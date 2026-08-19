# 02 — Product & Technical Architecture

> Everything here is from the **live canonical docs** (`docs.vanna.finance`) and reflects the shipped Stellar Soroban implementation. If a piece of content makes a technical claim, it must be traceable to this file.

---

## 1. What Vanna is, mechanically

Vanna is a **dual-sided protocol**:

**Side A — Liquidity Providers (passive).** Deposit XLM or USDC into a Vanna lending pool. Receive **vTokens** (vXLM, vUSDC) representing a proportional claim on the pool. The vToken *exchange rate grows* as borrowers repay interest. No positions to manage, no impermanent loss.

**Side B — Traders / Borrowers (active).** Open a **Margin Account** (a per-user deployed smart contract). Deposit collateral. Borrow up to **10×** against it. Deploy that borrowed capital into external protocols — lending pools, AMMs, DEX swaps — all while the position stays inside the account under one health check.

**The connective tissue:** interest traders pay flows directly to LPs. Both sides are economically bound.

---

## 2. The Vanna Flywheel

This is the protocol's economic engine and a first-class marketing asset (it is scene 5 of the product video).

```
Traders borrow 10×
        ↓
Utilization ↑  →  Lender APY ↑
        ↓
More lenders join
        ↓
Borrow rate ↓  →  more borrowing
        ↓
   (back to top)
```

**The argument:** on Aave or Morpho every borrow must be overcollateralized, so pool utilization has a structural ceiling. Vanna removes that ceiling — up to 10× — which keeps **utilization structurally higher**. Higher utilization = higher LP yield = more capital = cheaper borrowing = more traders = higher utilization. The cycle is self-reinforcing.

*Video frame values (illustrative):* Utilization 58%, APY 11.5%.

---

## 3. Contract architecture — 14 Soroban contracts, 5 groups

| Group | Contracts | Role |
|---|---|---|
| **Entry** | `AccountManager`, `LendingPoolXLM`, `LendingPoolUSDC` | User-facing entry points |
| **Per-user state** | `SmartAccount` (one deployed per user) | Holds collateral, debt, external positions |
| **Risk** | `RiskEngine`, `RateModel` | Health checks and interest-rate computation |
| **Infrastructure** | `Registry`, `Oracle`, `TrackingToken`, `vXLM`, `vUSDC` | Address resolution, price feeds, position tokens |
| **Deployment** | `DeployerContract`, `DeployerLPoolContract` | Factories for new SmartAccount instances |

### Layer flow

```
                        USER
          ┌───────────────┼────────────────┐
    AccountManager   LendingPool XLM   LendingPool USDC
    (margin lifecycle)  (LP supply)      (LP supply)
          │                │                 │
      RiskEngine  ←────  RateModel  ←────────┘
    (health factor,     (borrow rate
     borrow/withdraw,    per second)
     liquidation gates)
          │
     SmartAccount  (per-user contract)
       collateral balances / borrowed tokens / external positions
          │
     ┌────┼─────────┐
   Blend  Aquarius  Soroswap
   Pool   AMM Pool  DEX Pair
```

### Contract-by-contract

**`AccountManager` — the single entry point.**
Users *never* call SmartAccount directly. Every operation goes through AccountManager, which: (1) authenticates the caller, (2) asks RiskEngine whether the operation is allowed, (3) calls the LendingPool to issue or collect debt, (4) calls SmartAccount to update balances and execute external calls, (5) emits events.
Key functions: `create_account`, `borrow`, `repay`, `deposit_collateral_tokens`, `withdraw_collateral_balance`, `liquidate`, `close_account`, `settle_account`, `execute`.

**`SmartAccount` — per-user isolated contract.**
Each margin-account user gets their **own deployed contract instance with its own storage**. This is the core risk-isolation property: *a bug in one account cannot affect another.* Deployed by AccountManager via DeployerContract using a deterministic salt. Closed accounts are recycled into an inactive pool and reused to save deployment cost.
Stores: `CollateralTokensList`, `CollateralBalanceWAD(symbol)`, `BorrowedTokensList`, `IsAccountActive`, `HasDebt`. External positions are tracked via TrackingTokens, not stored here.
External routing via `execute(target, action, ...)` → Blend, Aquarius, or Soroswap.

**`LendingPools` (XLM · USDC).**
One contract per asset. Accepts deposits, mints vTokens proportional to share. Tracks outstanding borrows using a **borrow-shares model**. Calls `update_state()` before every borrow/repay to accrue interest. Two privileged functions callable **only** by AccountManager: `lend_to()` and `collect_from()`. **Pool assets are fully isolated** — a problem in one pool cannot affect another.

**`RiskEngine` — stateless.**
Reads position data from SmartAccount and LendingPools, prices everything via Oracle, returns allowed/not-allowed for every gated operation. Caches oracle prices within a single call to avoid duplicate cross-contract calls.
Three guards: `is_borrow_allowed`, `is_withdraw_allowed`, `is_account_healthy`.

**`RateModel` — smooth polynomial, no kink.** See §5.

**`Registry` — on-chain address book.**
Every contract resolves peer addresses through the Registry at runtime. No hardcoded addresses in business logic → **upgrades are safe: update the Registry entry, not every contract.** This is the one address an integrator hardcodes.

**`Oracle` — thin passthrough to Reflector.**
Exposes `get_price_latest(symbol)` returning `(price: u128, decimals: u32)`. RiskEngine converts to WAD for collateral valuation. Reflector updates on roughly a **5-minute cadence** — this oracle lag is one of the reasons the liquidation threshold sits at 1.1× rather than 1.0×.

**`TrackingToken` — synthetic position accounting.**
One contract tracking balances for position types:

| Symbol | Represents |
|---|---|
| `BLEND_XLM` | XLM deposited into Blend pool |
| `BLEND_USDC` | USDC deposited into Blend pool |
| `AQ_XLM_USDC` | Aquarius XLM/USDC LP position |
| `SS_XLM_USDC` | Soroswap XLM/USDC LP position |

When a SmartAccount deploys capital to Blend or Aquarius, AccountManager mints TrackingTokens on the SmartAccount. RiskEngine reads these to value the positions. **This is what makes external positions count as collateral** — and it is the mechanism behind the "credit that moves" claim.

**`vTokens` (vXLM · vUSDC).** Standard fungible tokens representing LP share. Exchange rate grows as borrowers repay interest. Holders earn yield passively by holding.

---

## 4. Health Factor — the single invariant

**Formula:**

```
Health Factor = Σ (collateral_i × price_i)  /  Σ (debt_j × price_j)
```

Both sums in USD at live oracle prices. Computed in WAD fixed-point (1e18). **Never stored** — always derived on demand. If debt is zero, the account is unconditionally solvent.

**On-chain check:**
```
(balance_wad × 10^18) / debt_wad  >  1.1 × 10^18      // BALANCE_TO_BORROW_THRESHOLD
```

### The three guard functions

| Guard | Formula | Note |
|---|---|---|
| **Borrow** | `(C + B) / (D + B) ≥ 1.1` | Borrow amount appears on **both sides** |
| **Withdraw** | `(C − W) / D ≥ 1.1` | Standard subtraction; skipped if no debt |
| **Liquidation** | `C / D ≤ 1.1` | Same function, inverse outcome |

**The self-collateralization principle — this is the most important technical idea in the protocol.**
The borrowed amount appears on both sides of the borrow guard because **capital borrowed from a Vanna lending pool cannot leave the margin account** — it is immediately available as deployed collateral within the same account. So the protocol treats the incoming borrow as simultaneously increasing *both* the asset base *and* the debt. Standard overcollateralized lending uses `C / (D + B)` because there the borrowed capital walks out the door.

**This asymmetry is exactly where 10× comes from:**
```
(C + B) / B ≥ 1.1   →   C + B ≥ 1.1B   →   C ≥ 0.1B   →   B ≤ 10C
```
A clean account with zero existing debt can borrow **up to 10× its deposited collateral**. With existing debt, remaining capacity is lower.

> **Marketing translation:** "10× isn't a parameter we dialled up. It falls out of the maths of credit that never leaves the protocol."

### Collateral valuation
- **Direct collateral (XLM, USDC):** balance × oracle price. One oracle call per unique symbol, cached for the transaction.
- **Blend yield positions (`BLEND_XLM`, `BLEND_USDC`):** b-tokens are not priced directly. First converted to underlying via Blend's `b_rate`: `underlying = (b_token_balance × b_rate) / 10^12`, then priced at the underlying's USD price. **After conversion, a Blend USDC position and a direct USDC deposit are treated identically for collateral purposes.**

### Debt valuation — a documented, deliberate trade-off
Debt is read as **raw borrow shares**, not the fully accrued token amount. Converting shares to the true amount owed requires a call chain across Registry → RateModel → LendingPool which, on Soroban, **exceeds the per-transaction compute budget** for accounts with borrows across multiple pools.

Consequence: the debt value in a health check reflects principal + interest settled *as of the last pool interaction*, excluding interest accrued since. This slightly **understates** true debt between pool operations. The 1.1× threshold is the buffer that absorbs it. Any pool-touching operation (borrow, repay, deposit, withdrawal) fully settles interest into shares and the next health check is accurate.

> **Honesty note for content:** Vanna documents this trade-off openly in its own docs. That transparency is a trust asset — use it. Do not hide it.

### Why 1.1× and not 1.0×
At 1.0× an account is liquidatable exactly when collateral equals debt — zero surplus. A liquidation at zero surplus has no cover for:
- **Slippage** — selling collateral on-chain has market impact; bigger position = more slippage
- **Oracle lag** — Reflector updates ~every 5 minutes; on-chain price may lag true market

The 1.1× floor (10% minimum overcollateralization) provides a fixed surplus at trigger. In extreme conditions where collateral collapses faster than liquidations clear, the surplus may be insufficient and **bad debt arises** — the affected pool's `total_assets` decreases, reducing the vToken exchange rate, distributing the shortfall proportionally across LP positions.

---

## 5. Interest Rate Model — smooth polynomial, no kink

**Input: utilization only.**
```
utilization = total_borrows / (total_borrows + available_liquidity)
```

**Rate:**
```
Borrow APR = C₃ × ( u·C₁ + u³²·C₁ + u⁶⁴·C₂ )

C₁ = 0.1   (linear and 32nd-power weight)
C₂ = 0.3   (64th-power weight)
C₃ = 3.5   (overall scaling)

rate_per_sec = APR / SECS_PER_YEAR
```

**Why it matters:** most money markets use a **kinked two-slope** model with an arbitrary breakpoint where the rate suddenly jumps. Vanna has **no kink**. The high-exponent terms are ≈0 at low utilization and rapidly dominate near 100%, so acceleration is organic.

| Utilization | Approx Borrow APR |
|---|---|
| 25% | ~9% |
| 50% | ~18% |
| 75% | ~26% |
| 80% | ~28% |
| 90% | ~33% |
| 95% | ~44% |
| 99% | ~115% |

Term behaviour:

| Term | 50% util | 90% util | 99% util |
|---|---|---|---|
| `u × C₁` | 0.050 | 0.090 | 0.099 |
| `u³² × C₁` | ≈0 | 0.003 | 0.073 |
| `u⁶⁴ × C₂` | ≈0 | 0.001 | 0.158 |
| **× C₃ = APR** | **~18%** | **~33%** | **~115%** |

**Utilization states:** 0% idle · 50% half deployed · 80% tightening, rate climbing · 95%+ near-fully lent, expensive · 100% all borrowed, **withdrawals blocked**.

**Self-correcting loop:** utilization rises → borrowing gets expensive → marginal strategies stop being profitable → borrowers repay → utilization falls → rate drops. Equilibrium typically settles in the **70–85%** range. No governance votes, no manual updates, no fixed rates.

---

## 6. Liquidation

**Trigger:** health factor falls to or below **1.1×**.

**Authorization — important and unusual.** `liquidate()` calls `trader_address.require_auth()`. It is **not permissionless** in the current implementation — it requires the account owner's authorization (direct participation or pre-signed delegation). The rationale: collateral is swept back **to the owner**, not to an external liquidator.

> ⚠️ Note the internal inconsistency to be aware of: the architecture doc's authorization table says "Anyone — AccountManager.liquidate() — no auth required," while the liquidation doc shows `require_auth()` on the trader. **Treat the liquidation page as authoritative** (it quotes the Rust source) and do not make public claims about permissionless liquidation without engineering confirmation.

**Mechanics:**
1. RiskEngine confirms account is unhealthy (call panics if healthy — it is an emergency exit only)
2. For each borrowed token: read full outstanding balance via `get_borrow_balance()` (includes all accrued interest, unlike the health check which uses raw shares), then `collect_from()` to clear pool-side debt, then `remove_borrowed_token_balance()` on the SmartAccount
3. **All debt closed in a single transaction — partial liquidation is not supported**
4. `sweep_to(trader_address)` returns all remaining collateral to the owner

**Sweep coverage caveat:** `sweep_to()` transfers actual balances for **XLM and USDC**. For Blend positions (`BLEND_XLM`, `BLEND_USDC`) and Aquarius LP positions (`AQ_XLM_USDC`), the internal collateral balance is zeroed and the token removed from the list, **but no token transfer occurs** — the underlying b-tokens in Blend and LP positions in Aquarius are **not unwound**. Their tracking records are cleared; the assets remain in the external protocols.

**No liquidation fee** in the current implementation. `collect_from()` transfers exactly what's needed; `sweep_to()` transfers the full remainder to the trader. No percentage deducted for any party.

**State after liquidation:** borrowed tokens removed, `has_debt` false, collateral balances zeroed, SmartAccount **remains active** in the registry. `liquidate()` is a *position clear*, not an account closure.

**`settle_account()` — the voluntary alternative:**

| | `liquidate()` | `settle_account()` |
|---|---|---|
| Health check | Must be unhealthy | No check |
| Debt cleared | All borrowed tokens | All borrowed tokens |
| Collateral returned | Swept to owner immediately | Stays in Smart Account |
| Account deactivated | No | No |

---

## 7. Product surfaces (the four sections of the app)

| Section | What it does |
|---|---|
| **Earn** | LP side. Supply XLM/USDC to Vanna lending pools, receive vTokens, earn borrower interest. Withdraw = redeem vTokens for deposit + accrued yield. |
| **Margin** | Open Margin Account, deposit collateral, borrow up to 10×, transfer collateral, repay, monitor health factor. |
| **Trade** | Spot swap using borrowed margin (via Soroswap). |
| **Farm** | Deploy margin-account assets into external yield: **single-asset pools** (Blend → b-Tokens) and **LP pools** (AMM two-asset, earn swap fees). Includes **Lite Mode** — one-click leveraged yield: deposit collateral, borrow, and deploy into a yield pool in a **single transaction**. |
| **Analytics** | Protocol-wide risk dashboard: positions, HF distribution, leverage analytics, live borrow rates, liquidation events, wallets eligible for liquidation, and a **Risk Explorer** for stress simulations (market crashes, depegs, liquidity shocks). |

**Lite Mode vs Pro Mode** is the documented user split: Lite Mode for simplicity, Pro Mode for full control.

---

## 8. Documented strategies (highest-value content assets)

These are real, documented, delta-neutral strategies. They are the best proof that "composable credit" is not an abstraction.

| Strategy | Sections used | Delta exposure | Risk | Complexity |
|---|---|---|---|---|
| **Cross-Pool Rate Carry** | Margin · Farm | None (XLM-neutral) | Low–Medium | Medium |
| **Dual Yield Stack** | Earn · Margin · Farm | None | Low–Medium | Medium |
| **Earn + Borrow Hedge** | Earn · Margin · Trade | None (XLM-neutral) | Medium | Medium |
| **Parallel Rate Carry** | Margin · Farm | None | Medium–High | High |

- **Cross-Pool Rate Carry** — borrow XLM from Vanna, deploy into an external Blend XLM pool, earn the rate spread with zero net XLM price exposure.
- **Earn + Borrow Hedge** — supply XLM to Earn for yield, borrow an equal value of XLM and swap to USDC. The two legs cancel; zero net XLM exposure, earning on both sides.
- **Parallel Rate Carry** — from a single USDC collateral base, borrow XLM and split across two yield venues (Blend's XLM pool + Aquarius XLM/USDC), stacking two independent rate spreads with no net XLM price exposure.
- **Dual Yield Stack** — supply USDC to Earn *while* running an XLM rate carry in Margin: two independent yield streams, zero directional exposure.

**Required risk framing (from the docs, use it):**
> No DeFi strategy is entirely risk-free. All positions carry smart contract risk. These strategies are designed to eliminate or minimise **price risk** and **liquidation risk** — not protocol risk.

### The marketing-side strategy playbooks (site + video)
Named on the homepage carousel: **LP + Lending Spread · Delta-Hedged Vol Carry · Funding-Rate Harvest · Compute Yield, Hedged**.

*Funding-Rate Harvest* (shown expanded): Δ-neutral · perps · ≈12% funding capture — (1) buy BTC spot with the credit line, (2) short the same size in BTC perps, (3) collect funding and rebalance the drift. Agent runs it end-to-end under your policy. HF 2.4.

*Delta-Hedged Vol Carry*: θ carry · premium capture — (1) sell a 30-day ETH strangle, (2) hedge the delta with perps, (3) roll or close at 21 days out. HF 2.1.

> ⚠️ These perps/options playbooks describe the **target multi-venue product**, not what is wired on Stellar testnet today (where Blend/Aquarius/Soroswap are the live venues). See claim safety.

### The product video's worked example (illustrative, marketing-owned)
Scene sequence, 800×800 social video:
1. **$10,000 undercollateralized credit · 10× leverage** (from $1,000 collateral)
2. **Composable Leverage** — $10,000 borrowed splits into: ETH Spot $4,000 (no funding rate) · ETH Short Perp $4,000 (hedge position, "leverage over leverage") · Yield Farm $2,000 (extra APY)
3. **Hedge Strategy** — Long Spot $4,000 vs Short Perp $4,000 = **zero directional risk**; directional risk 0%, no funding rate, funding-fee arbitrage, health factor safe
4. **Profit Breakdown** (on $1,000 collateral) — Funding Fees +$150 · Yield Farming APY +$200 · **Total income +$350** · Borrow Interest −$85 · **Net Profit +$265** · **ROI 26%**
5. **Protocol Flywheel** — utilization 58%, APY 11.5%
6. **Outro** — "Leverage Anywhere, Without Getting Liquidated · Composable Credit Infrastructure"

**Always label this as an illustrative example.** The 26% ROI is a modelled scenario, not realised performance.

---

## 9. Engineering details worth knowing

**Fixed-point arithmetic.** All balances, prices and rates in **WAD (1e18 = 1.0)**. Conversion at protocol boundaries:
```
WAD ← native:  wad = native_amount × 10^18 / 10^decimals
native ← WAD:  native = wad × 10^decimals / 10^18
```
All intermediate math uses `mul_wad_down` / `div_wad_down` (floor division) **to prevent rounding in the protocol's favour**. Good trust signal.

**Authorization model.**

| Caller | Can call |
|---|---|
| User wallet | AccountManager, LendingPool (deposit/redeem) |
| AccountManager | SmartAccount (all writes), LendingPool (`lend_to`, `collect_from`) |
| SmartAccount | TrackingToken (mint/burn), external protocols (Blend, Aquarius, Soroswap) |

SmartAccount **rejects all calls that don't originate from its registered AccountManager.** Users cannot call SmartAccount functions directly.

**Indexing.** Contract events are indexed via **Mercury** (Stellar indexer). Docs cover XDR event schemas, Mercury integration patterns, and real-time streaming. Liquidation-bot guide covers account discovery, HF monitoring and trigger.

**Origination fee** exists — the borrow flow transfers an `origination_fee` to treasury before transferring the borrowed amount to the SmartAccount.

**Deployment (Stellar Testnet):**
- Network passphrase: `Test SDF Network ; September 2015`
- Soroban RPC: `https://soroban-testnet.stellar.org`
- Horizon: `https://horizon-testnet.stellar.org`
- Registry: `CC35XWCH7SCQROTNW7PA6HZKP4JMNSVV2K7CX3HY2PSI2MI2ZQQH73ID`
- Account Manager: `CAK2IJIO2SKZWUODY4G7ZRIUUIIMJUUAIXE3I5YTQ5QYNSS2RYJ3P4CV`
- Risk Engine: `CBL7RCG5H4VIZCNF7BRM2FQFXK7N5KRQKW7ZVEQZJKNXHA6FEU4OXK5I`
- Pools: XLM, USDC, Aquarius USDC, Soroswap USDC
- vTokens: vXLM, vUSDC, vAQUSDC, vSOUSDC
- External: Blend Pool TestnetV2, Blend Backstop V2, Blend Emitter, BLND; Aquarius Router + XLM/USDC, XLM/AQUA, XLM/USDT pools; Soroswap Router, Factory, XLM/USDC pair

**Smart Account addresses are per-user**, determined at creation. Find via `Registry.get_accounts(user_address)` or by listening for `AccountCreationEvent`.

**Security documentation status:** `docs.vanna.finance/security/` currently reads **"Coming Soon."** No published audits, no bug bounty, no multi-sig disclosure. This is the single biggest credibility gap. See claim safety.

---

## 10. Developer surface

**TypeScript SDK** — `@vanna/sdk`, documented flow: set up environment, call contracts from TypeScript using the Stellar SDK and **Freighter** wallet; build → simulate → sign with Freighter → submit a Soroban transaction.

**Integration guides that exist:** Integrate Lending (supply, read pool state, redeem vTokens) · Integrate Margin Accounts (create, deposit, borrow, deploy to external protocols, repay, close) · Liquidation Bots · Events & Indexing · Math Reference.

**Docs audience split:** Liquidity Providers · Traders & Borrowers · Developers & Integrators. Developer docs say "on Stellar and Base."
