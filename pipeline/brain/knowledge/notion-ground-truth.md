# Vanna — ground truth from the Notion workspace

Extracted 2026-09-24 from the founder's Notion, via the connected Notion MCP.
Source pages are listed at the bottom. **Confidence tags are the source's own
and must not be upgraded here.** Where this file disagrees with an older
document, the disagreement is recorded rather than resolved — resolving it is
a founder decision, not a pipeline one.

---

## 1. Product (CONFIRMED)

Vanna is a **composable credit / unified margin protocol for DeFi**. Users
deposit collateral into a smart-contract margin account (**ERC-4337 account
abstraction**) and borrow credit against it. The borrowed credit is
*composable*: it can be deployed across integrated venues — perps, options,
spot/AMM, yield, lending — rather than being trapped in one protocol.

**Deployment (CONFIRMED — this constrains every claim):** live on **Stellar,
testnet**. Not mainnet. Any positioning, campaign or metric that assumes live
mainnet capital is invalid. **All EVM-chain references are roadmap, not
current state.**

### Mechanism

| Thing | What it is |
|---|---|
| **Track Token** | The most original primitive. Perp and options positions emit no standard receipt token (unlike aTokens or LP tokens), so no lending protocol can value them inside a margin account in real time. The Track Token is a synthetic per-account receipt token whose value is oracle-read from the live derivative position. This is what makes derivatives-inclusive composable credit possible at all. |
| **Health factor** | `(aToken + LP Token + Track Token + cash) / total borrowed`, with a **1.1 liquidation threshold**. |
| **Asset-tiered leverage** | Blue-chip collateral (USDC, ETH, BTC) up to **~7x**; volatile assets capped lower. Risk-aware, not a flat cap. |
| **Risk engine** | Portfolio-level exposure monitoring aggregated across venues, scenario analysis, threshold alerting, liquidation management — evaluated on the whole margin account, not position by position. |
| **LP side** | Single-sided lending pool. Yield from borrow interest + liquidation fee share + revenue share. No impermanent loss. |

---

## 2. Canonical integration list (CONFIRMED)

**This is the whole list.** Do not add a protocol to it from memory, from an
older Vanna document, or by inference. A partnership post about anything not
on this list is fabricating a relationship.

| Partner | Role in the stack |
|---|---|
| Stellar | Chain — current deployment |
| Soroswap | Spot / AMM (Stellar) |
| Aquarius | Spot / AMM (Stellar) |
| Blend | Lending (Stellar) |
| Hyperliquid | Perps |
| Aster | Perps |
| Avantis | Perps |
| Derive | Options (via Optimism) |
| Optimism | Chain — accessed via Derive |
| Uniswap | Spot / AMM |
| Aerodrome | Spot / AMM |
| Morpho | Lending |
| Katana | Yield |
| Privy | Wallet / auth infrastructure |
| ZeroDev | Account abstraction infrastructure |
| Draper University | Backer |
| Pivot Ventures | Backer |
| Gitcoin | Backer / ecosystem |

The *shape* of that list is the defensible story: **Stellar-native venue
coverage (Soroswap, Aquarius, Blend) plus cross-chain derivatives
(Hyperliquid, Aster, Avantis, Derive), with Privy and ZeroDev as the account
layer.** Tell that story rather than the larger multi-chain story Vanna has
not yet earned.

---

## 3. The four access surfaces (BUILT — CONFIRMED BY FOUNDER)

All four exist. They are the substance of the infrastructure claim: Vanna is
not promising an infrastructure future, it has built the access layers.

- **Vanna MCP** — Vanna's own MCP server. Intent: anything doable in the Vanna
  UI becomes doable through MCP, from a cloud environment or an AI agent.
- **AI Copilot** — in-product natural-language execution. Intent → action, plus
  templates (risk report, strategy design, liquidation management, portfolio
  risk, trading strategy, DeFi execution, monitoring).
- **API / SDK** — surface includes `createCreditAccount`, `borrow`, `allocate`,
  `getHealthFactor`, `getTrackTokenValue`, `executeStrategy`, `rebalance`.
  Internally framed as "the Stripe of DeFi liquidity."

**Built is not the same as publicly consumable.** Before any copy ships about
these, establish per surface: publicly accessible? documented? has anyone
outside the team used it? testnet-only? The failure mode is no longer
overclaiming a roadmap item — it is inviting developers to something real
they then cannot reach. *A built-but-undocumented SDK converts worse than an
honest waitlist.*

---

## 4. Traction figures — TREAT AS UNVERIFIED

$350k+ raised (Pivot Ventures, Draper University, Gitcoin) · 40k+ email
subscribers · "2M+ users via integrated protocols" · integration counts from
older materials.

Vanna is on testnet, so **any figure implying live economic activity — TVL,
volume, active traders, capital deployed — cannot be real usage.** The
"2M+ users via integrated protocols" figure describes *other protocols'*
users, not Vanna's.

---

## 5. Narrative currently in market

- Category claim in use: "Composable Credit Infrastructure for DeFi"
- Taglines: "Composable Credit for DeFi" · "Leverage Anything & Anywhere in
  DeFi" · "Borrow 10x Credit Upfront. Allocate Across DeFi" · "Stop Gambling.
  Start Strategizing." · "TradFi Precision. DeFi Freedom."
- Framing devices: "Leverage 1.0 vs Leverage 2.0", the "DeFi credit card"
  analogy
- Current content tone: high-energy, emoji-dense, retail-degen adjacent — and
  it **conflicts** with the infrastructure audience the repositioning targets
- Brand system: Plus Jakarta Sans; violet `#703AE6` and rose `#FF007A`
  primaries; near-black `#111111` base

---

## 6. Retired and prohibited framings

- **Never write "Greeks Dashboard."** That framing has been retired. Describe
  the capability at the infrastructure level, not as a trader-facing dashboard.
- No hype vocabulary: revolutionary, game-changing, unparalleled, seamless,
  cutting-edge, next-gen, "the future of X."
- No competitor smears — grant competitors their genuine strengths.
- No implied guarantees of returns or safety.
- **Do not present TradFi analogies as regulatory equivalence.** On-chain
  portfolio margining is not an OCC-approved margin methodology.
- On "portfolio margin" specifically: it carries a precise regulatory meaning
  in TradFi. Whether Vanna's health-factor model genuinely constitutes
  portfolio margining (risk-based netting across offsetting positions), or is
  better described as cross-collateralised composable credit, is **unresolved**.
  Using the term loosely is the error a sophisticated allocator catches.

---

## 7. Unresolved tensions — do not smooth these over

1. **10x vs ~7x.** Public materials say "10x / 900% LTV". The internal risk
   architecture says asset-tiered, ~7x blue-chip, lower for volatile assets,
   HF floor 1.1. *The source calls these "different products."*
   **This repo's `approved-claims.md` currently carries `CLM-003` — "up to 10x
   leverage" — as a VERIFIED claim.** That is the higher of the two numbers and
   it is not reconciled. Flagged, not changed: the claims registry is the
   founder's to amend.
2. **"2M+ users via integrated protocols"** — not Vanna's users.
3. **Testnet stage vs infrastructure claims.** Infrastructure positioning
   invites scrutiny that application positioning does not. Testnet is not a
   weakness if stated plainly; it is fatal if obscured and later discovered.
4. **Track Token: lead with it or protect it?** Simultaneously the strongest
   technical differentiator and the largest novel attack surface with no
   battle-tested precedent.
5. **Voice conflict.** Emoji-dense retail energy vs infrastructure credibility.
6. **Category collision.** Gearbox already runs on "The Onchain Credit Layer"
   with meaningful TVL.
7. **Agentic timing.** Is the market ready for agent-executed DeFi, or is
   Vanna early?

---

## 8. The sharpest question, and the product story

> What stops an agent with Vanna access from destroying a user's capital very
> efficiently?

The candidate answer, per the source: Vanna's differentiator is **not** agent
access — access is commoditising — it is that Vanna is a **risk-bounded
execution surface**, where the constraints (health factor, tiered leverage,
liquidation logic, portfolio-level exposure limits) are **enforced by the
protocol** rather than trusted to the agent's judgement.

> An LLM's promise not to over-lever is not a risk control. A liquidation
> engine is.

---

## Sources

| Notion page | Path | Last edited |
|---|---|---|
| "Vanna — Positioning, Category, GTM & Content Strategy / Master Prompt (v1)" (page titled "New note") | Notes | 2026-08-21 |
| VANNA-AI-Agents-MASTER-DOC | workspace root | 2026-07-31 |

The link the founder supplied — `app.notion.com/p/Vanna-Protocol-358846d6…` —
returns 404 to this integration. It is in a workspace the connector is not
authorised for, or has not been shared with it. Everything here comes from the
workspace the connector *can* reach.
