# 08 — Facts Ledger & Claim Safety

> **Read this before generating any external-facing content.** Vanna is pre-mainnet with no published audits. The gap between what the marketing site *depicts* and what the protocol *does today* is wide and deliberate — it is a vision site. An agent that treats depiction as fact will produce false marketing.

---

## 1. Confidence tiers

| Tier | Meaning | How to use it |
|---|---|---|
| **A — Verified** | In live technical docs or the live site as a statement of fact; or externally verifiable | State plainly. No hedging needed. |
| **B — Design / architecture** | Documented design intent that is shipped on testnet | State as how the protocol works. Add "on testnet" if the context implies live capital. |
| **C — Illustrative / demo** | Website mock, video scenario, worked example | **Must** be labelled as an example or scenario. Never presented as results. |
| **D — Roadmap / aspirational** | Planned, designed, or pitched but not built | Use future or conditional tense. Never present tense. |
| **E — Internal only** | Strategy, gaps, disagreements, unpublished numbers | **Never appears in external content.** |
| **F — Unverified / stale** | Number of unclear provenance, or a legacy-generation fact | Do not use until confirmed by a human. |

---

## 2. The facts ledger

### Tier A — Verified, safe to state

| Fact | Source |
|---|---|
| Vanna is composable, undercollateralized credit infrastructure for DeFi | Live site + GitHub org description |
| Maximum leverage is **10×** | Live docs (derived from the borrow guard) |
| Liquidation threshold / health-factor floor is **1.1×** | Live docs |
| Health factor = total collateral USD / total debt USD, never stored, derived on demand, WAD precision | Live docs |
| Protocol comprises **14 Soroban smart contracts** in five groups | Live docs |
| Every user gets their **own deployed SmartAccount contract** with its own storage; a bug in one cannot affect another | Live docs |
| Lending pools are separate contracts per asset; a problem in one cannot affect another | Live docs |
| Rate model is a **smooth polynomial with no kink point**: `APR = 3.5 × (u·0.1 + u³²·0.1 + u⁶⁴·0.3)` | Live docs |
| Approximate borrow APRs: ~9% at 25% util · ~18% at 50% · ~28% at 80% · ~33% at 90% · ~44% at 95% · ~115% at 99% | Live docs |
| Pool equilibrium typically settles at **70–85% utilization** | Live docs |
| No governance votes and no fixed rates — the rate responds to pool state in real time | Live docs |
| Oracle is a passthrough to **Reflector**, ~5-minute update cadence | Live docs |
| Registry-based address resolution; no hardcoded addresses in business logic | Live docs |
| All rounding uses floor division (`mul_wad_down`/`div_wad_down`) to prevent rounding in the protocol's favour | Live docs |
| Debt in health checks uses raw borrow shares, slightly understating true debt between pool operations; the 1.1× threshold is the buffer | Live docs |
| Liquidation clears **all** debt in one transaction — partial liquidation is not supported | Live docs |
| There is currently **no liquidation fee** | Live docs |
| `liquidate()` requires the account owner's authorization | Live docs (liquidation page) |
| `sweep_to()` transfers XLM and USDC balances; Blend b-tokens and Aquarius LP positions are **not unwound** — records cleared, assets remain in the external protocol | Live docs |
| Bad debt reduces the pool's `total_assets`, dropping the vToken exchange rate and distributing the shortfall proportionally across LPs | Live docs |
| Integrated external protocols on testnet: **Blend Capital, Aquarius, Soroswap** | Live docs (deployed contracts) |
| Assets on testnet: **XLM and USDC** (plus Aquarius USDC and Soroswap USDC variants) | Live docs |
| **All contracts are on Stellar Testnet. Mainnet addresses will be published at launch.** | Live docs |
| Four documented delta-neutral strategies with risk/complexity ratings | Live docs |
| Docs explicitly state strategies minimise price and liquidation risk, **not** protocol risk | Live docs |
| Events indexed via **Mercury** | Live docs |
| TypeScript SDK is `@vanna/sdk`; docs use the Stellar SDK and Freighter wallet | Live docs |
| Site displays: 15+ integrations · 6+ chains · 1,000+ users | Live site |
| Ecosystem logos: Stellar, Hyperliquid, Uniswap, Optimism (via Derive), Soroswap, ZeroDev, Katana, Avantis, Draper University, Morpho, Privy, Blend, Aerodrome, Derive, Gitcoin, Aquarius, Aster, Pivot Ventures | Live site |
| Site footer: "Built on Stellar · Base · Arbitrum · Optimism" | Live site |
| Site legal line: positions at outside venues remain subject to those venues' own margin and liquidation rules | Live site |
| Published tool taxonomy — READ: `get_account_state`, `estimate_capacity`, `simulate_position` · WRITE: `open_position`, `repay_debt`, `rebalance` · RISK: `protect_position`, `get_risk_alerts` | Live site |
| "Scoped session keys · Vanna never holds custody · the guardian runs beneath all three" | Live site |
| GitHub org has 4 public repos, all website-related; protocol contracts are not public | GitHub |
| `docs.vanna.finance/security/` reads "Coming Soon" | Live docs |
| x402 and MPP are both live on Stellar mainnet; SDF is a Premier member of the x402 Foundation | Stellar, 2026 |
| ~100M x402 payments on Base; $1+ transactions rose from 49% to 95% of volume in a year | Chainalysis, Jun 2026 |
| Galaxy Research estimates agentic commerce at $3–5T B2C revenue by 2030 | Galaxy, Jan 2026 |
| MPP launched with 100+ integrated services incl. Stripe, Anthropic, OpenAI, Shopify, Visa; spec submitted to IETF | Stellar, Apr 2026 |

### Tier B — Design / architecture (shipped on testnet)

- The self-collateralization principle: borrowed capital cannot leave the margin account, so the borrow guard counts it on both sides.
- TrackingToken lets the RiskEngine value external Blend/Aquarius/Soroswap positions as collateral.
- Blend b-tokens are converted to underlying via `b_rate` then priced by the oracle; after conversion a Blend USDC position and a direct USDC deposit are treated identically.
- SmartAccount rejects all calls not originating from its registered AccountManager.
- Closed accounts are recycled into an inactive pool and reused to save deployment cost.
- Lite Mode executes deposit + borrow + deploy-to-yield in a single transaction.
- MCP server is zero-custody with a separate Sign Service as the only signer, using scoped session keys and spend caps.
- Analytics includes a Risk Explorer for stress simulations (crashes, depegs, liquidity shocks).
- A working end-to-end demo exists: natural language → agent computes constraints → multiple auto-signed transactions → health factor maintained.

### Tier C — Illustrative / demo (must be labelled)

| Content | Note |
|---|---|
| $10,000 collateral → ×3 credit → $30,000 working book; six market legs; Δ≈0; net +$302; HF 1.76 | Homepage mock. Values animate/change on load. |
| Isolated-margin panel numbers ($3,300/$3,300/$3,400, health 1.33, BTC live drift) | Homepage mock, animated |
| Copilot demo: 1,000 USDC → borrow $2,000 ETH → HF 1.43 | Homepage mock |
| Agent Score 742/850, Tier 4 Established, 100% on time, 47 saves, 1.8 avg HF, 214d/$1.2M, 7.0× line | Homepage mock — **no live Agent Score product** |
| Risk Guardian SOL story: 12% drop at 03:14, HF 2.4→1.3→2.1, liquidation at 1.10 | Homepage mock |
| Playbook figures: ≈12% funding capture, HF 2.4, HF 2.1 | Homepage mock |
| Video: $1,000 → $10,000 credit → ETH spot $4,000 / ETH short perp $4,000 / yield farm $2,000; funding fees +$150, yield +$200, borrow interest −$85, **net +$265, ROI 26%** | Marketing video — a modelled scenario, **not realised performance** |
| Video: utilization 58%, APY 11.5% | Marketing video mock |
| CLI/SDK example fees ("fee $0.004") and tx hashes | Illustrative |

**Required labelling patterns:** "illustrative example" · "a worked scenario" · "in this example" · "hypothetical". **Never:** "our users earned" · "returns of" · "we delivered".

### Tier D — Roadmap / aspirational (future tense only)

- **Markets:** perps, options, prediction markets, tokenized stocks (NVDAx), AI-compute/GPU-hours markets. **None are live on Stellar testnet.** The site presents them as the product; today they are the target.
- **Agent Score** as a live, queryable product.
- **x402 Financial Data API** — `/account-state/{address}`, `/simulate-position`, `/agent-score/{address}`, `/yield-rates`, `/risk-alerts/{address}`.
- **Agent Credit Layer** — agents accessing undercollateralized credit on behavioural record.
- **Intent-Based Prime Brokerage.**
- **DePIN / GPU financing credit agent** — internally flagged as *not* near-term absent a clear oracle and legal/collateral path.
- **Businesses / white-label** offering: "offer undercollateralized credit inside your own app."
- **Institutions:** segregated accounts, prime-broker experience.
- Base / Arbitrum / Optimism deployments.
- Mainnet.

### Tier E — Internal only, never publish

- Break-even TVL estimate (~$100M+); revenue modelling ($475K–$1.15M at $50M TVL vs $1M–$2M costs).
- Funding-gap assessment ($350K raised vs $5M+ minimum needed).
- The ten launch blockers (multi-sig, timelock, 2+ audits, bug bounty, formal verification, input validation, identity verification, incident response, monitoring partner, insurance fund).
- The internal recommendation to **remove Stellar** and launch on a single EVM L2.
- The recommendation to cut launch integrations from 16 to 5–7.
- The seven-dimension scorecard and Vanna's ~35/70.
- The verdict: "design without execution is a whitepaper, not a protocol."
- Staged leverage rollout plan (3×→5×→7×).
- Token prerequisites.
- The internal MCP server's 43-tool count (unconfirmed publicly).
- Any competitor's confidential detail.

### Tier F — Unverified / stale, do not use

| Item | Why |
|---|---|
| "**1000× leverage**" (ETHGlobal listing) | Legacy, almost certainly a typo or hackathon-era framing. **Never repeat.** |
| "5× base / 7× blue-chip asset-tiered leverage" | Legacy EVM-era design. Current canonical is 10×. |
| **ERC-4337 / EIP-4337** account abstraction | Legacy. Current is native Soroban per-user contracts. |
| **Greeks Dashboard**, **Prop Dashboard** | Legacy vocabulary. Not in the current product or docs. |
| "Live on Optimism with Perp Protocol and Uniswap" | Legacy EVM deployment. |
| "**2M+ users**" | Aggregate reach of integrated protocols, **not Vanna users.** Never state as a user count. |
| "**40,000+ subscribers**" | Internal figure; confirm before external use. |
| "78% of derivatives volume is perps" | Internal research figure; verify against a current source before publishing. |
| Perps/options/prediction/AI-compute as **live** integrations | Not live. Tier D. |
| Audits, bug bounty, multi-sig, insurance | **None published.** Never claim. |
| Any TVL figure | Pre-mainnet. There is no TVL. |
| Any token, airdrop, points or reward | Does not exist. |

---

## 3. Hard prohibitions

Absolute. No context, campaign, or channel makes any of these acceptable.

1. **Never imply mainnet is live**, or that user funds are deployed, or that TVL exists.
2. **Never claim audits, a bug bounty, multi-sig, timelocks, formal verification, or insurance.**
3. **Never mention or hint at a token, airdrop, points programme, or rewards** — including jokes, emoji, "no token 👀", or "early users will be remembered".
4. **Never present demo numbers as results.** The 26% ROI, the 742 score, the +$302 book, the 47 saves — all mocks.
5. **Never promise or imply returns.** No APY projections presented as expectations. No "guaranteed", "risk-free", "can't lose".
6. **Never give financial, investment, legal or tax advice.**
7. **Never claim superiority over a named competitor.** Compare jobs-to-be-done. Especially: no "better than Gearbox", no "better than Hyperliquid".
8. **Never publish Tier E internal material** — the gap analyses, the launch blockers, the internal disagreements, the break-even maths.
9. **Never use legacy vocabulary** (see Tier F) as current.
10. **Never claim live perps, options, prediction-market, tokenized-stock or AI-compute integrations.**
11. **Never overstate the agent layer's autonomy.** It is policy-bounded, human-approved, zero-custody. Never "our AI trades for you".
12. **Never make regulatory or compliance claims** — no "compliant", "licensed", "regulated", "KYC-ready" — none exist.
13. **Never disclose the private repos, internal env var conventions, contract source, or infrastructure details** from internal engineering context.
14. **Never fabricate a customer, testimonial, case study, partnership, or logo.** If a logo is on the site it can be shown as ecosystem; it cannot be described as a customer.

---

## 4. Safe reframes — the substitution table

| Instead of ❌ | Say ✅ |
|---|---|
| "Vanna offers up to 10× leverage across perps and options today" | "Vanna is built for up to 10× credit across spot, perps, options, prediction and AI-compute markets. Live on Stellar testnet today with Blend, Aquarius and Soroswap." |
| "Traders earn 26% ROI" | "In this illustrative example, a $1,000 collateral position nets $265 — a 26% return on collateral before protocol risk." |
| "Our Agent Score gives agents credit" | "Vanna is building an Agent Score that turns an agent's on-chain behaviour into an undercollateralized credit line, queryable by third parties over x402." |
| "Audited and secure" | "Every margin account is a separately deployed contract; each lending pool is isolated; every write is gated by a stateless risk engine. Security documentation is being published ahead of mainnet." |
| "We have 15+ integrations" | "Deep integrations with Blend, Aquarius and Soroswap today, with a broader venue roadmap." |
| "2M+ users" | "Ecosystem reach across integrated protocols." (or omit) |
| "Better than Gearbox" | "Gearbox is universal leverage. Vanna is built for derivatives and hedging — one solvency ratio across legs that intentionally offset." |
| "The AI trades for you" | "You state the intent. The copilot compiles it into a guarded position and hands it back — nothing signs without you." |
| "Never get liquidated" | "Set a health-factor floor and the guardian defends it within your policy. Liquidation remains possible in extreme conditions." |
| "No risk" | "These strategies are designed to eliminate price and liquidation risk. Protocol risk remains." |
| "Launching soon" | "Currently on Stellar testnet. Mainnet addresses will be published at launch." |

---

## 5. Pre-publication checklist

Run this on every asset before it ships.

```
□ Every number traced to Tier A, or explicitly labelled as illustrative
□ No implication of mainnet, live TVL, or deployed user funds
□ No audit / bug bounty / multi-sig / insurance claim
□ No token, airdrop, points, or reward reference of any kind
□ No named-competitor superiority claim
□ No return promise, projection-as-expectation, or "risk-free"
□ Perps / options / prediction / AI-compute stated as target, not live
□ Agent autonomy framed as policy-bounded + human-approved + zero-custody
□ Risk disclosure present wherever a strategy or yield is described
□ No Tier E internal material
□ No legacy vocabulary (Greeks Dashboard, ERC-4337, 5x/7x, 1000x, Prop Dashboard)
□ Brand compliance: Plus Jakarta Sans, palette tokens, spacing/radius scale
□ Voice check: no hype register, no exclamation marks, no FOMO
□ Named venues preferred over integration counts
□ Human review flagged if any claim sits in Tier F
```
