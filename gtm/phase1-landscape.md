# Vanna GTM — Phase 1 Landscape + Phase 2 Terminology
**Research pass: 2026-08-20.** Produced through the agent orchestration (4 parallel research agents). Evidence discipline: named source + date per number; FOUND vs INFERRED separated; TradFi analogies are for terminology only, not regulatory equivalence. Canonical product truth = `docs.vanna.finance` (verified 2026-07-31): Stellar Soroban **testnet**, assets **XLM + USDC**, per-user SmartAccount, stateless RiskEngine, **health factor = risk-adjusted collateral ÷ total borrowed**, liquidation **1.1×**. NB: the `vanna.finance` marketing site contradicts the docs (multi-chain, perps/options, 15+ integrations) — docs win (a §8 known tension, now confirmed).

---

## 0. THE CONVERGENT FINDING (all four segments independently pointed here)

**No one cross-margins a mixed perps+options book across venues, enforced in-protocol.** Each adjacent category leaves exactly this lane open:
- **Composable-credit players** (Gearbox, Morpho, Euler, Fluid, Arcadia) margin **spot/lending** — none prices or cross-margins **derivative** positions.
- **Perp/options venues** (Hyperliquid, Derive, …) each run their **own** liquidation engine; risk is **not** netted across venues (the Oct-2025 crash proved every engine buckled independently).
- **CEX portfolio margin** (Binance/OKX/Bybit/Deribit) proves the demand + math but is **walled per-venue and gated** by high balance/VIP thresholds. No CEX nets your Deribit option against your Binance perp.
- **Risk-infra providers** (Gauntlet, Chaos Labs, …) **advise/rate/watch**; none **IS** a protocol's enforced risk engine.
- **Agentic finance** (Coinbase/Circle/Crossmint/Halliday) enforces **payment** guardrails at the wallet layer — not **derivatives margin**.

→ **The whitespace = "cross-margin / portfolio-margin aggregation + risk-bounded execution for on-chain derivatives, enforced in-protocol."** This sharpens the founder's "1inch for perps": the defensible wedge is **cross-venue risk/credit NETTING** (net a user's positions), *not* order-book liquidity aggregation (which faces venue hostility and needs their cooperation).

**Two hard dependencies (survivor vs failure lesson):**
1. **Ship the SDK / integration surface early.** Survivors (Morpho→Coinbase, Euler EVK/EVC, Gearbox integrations-v3) won *by becoming depended-on infra*; the three dead comparables (Prime, PrimeX, DeltaPrime) died *as destination apps that shipped no SDK*. This corrects Vanna's internal thesis: "never shipped an SDK" is TRUE only for the failures.
2. **Lead with risk-engine + security + mark integrity.** The reframe's strength (concentrated cross-margin + a live Track-Token mark) is exactly **DeltaPrime's fatal surface** (ops/security death). Make "our mark can't be gamed, our keys can't be stolen" a headline, not a footnote.

---

## 1. Composable credit / on-chain leverage (the contested ground)

| Entity | Positioning | Dev/SDK surface | TVL (DefiLlama, 2026-08-20) | Gap Vanna exploits |
|---|---|---|---|---|
| **Gearbox V3** | "The Onchain Credit Layer" — composable Credit Accounts | **Strong** (integrations-v3, permissionless markets) | **~$21M** (down ~90%+ from ~$410M peak) — owns the *words*, not the balance sheet | Leverages **spot**; does not cross-margin/mark **derivatives** |
| **Morpho** | "Open credit network" (purest infra-not-app) | **Very strong**; powers Coinbase Loans; $175M raise (Paradigm/a16z/Ribbit) | **~$8.99B** | Isolated-market lending; no derivatives cross-margin |
| **Euler v2** | "Credit layer for programmable finance" (EVK/EVC) | **Very strong** builder toolkit | **~$372M** | Cross-collateral of vaults/spot, not a derivatives margin engine |
| **Fluid (Instadapp)** | "Smart collateral / smart debt" liquidity layer | Strong | **~$905M** | Spot efficiency; no derivatives mark |
| **Arcadia** | **Closest structural analog** — composable cross-margin ERC-721 accounts | Open accounts-v2 | **~$5.56M** | Same *account* idea, but for **AMM-LP yield**, not perps+options |
| **Contango** | "Looping layer" (synthesizes cPerps via money markets) | App-first | **~$6.16M** | Manufactures single-leg exposure; no cross-venue margin |
| **Ethena** | Synthetic dollar (USDe), delta-neutral basis | Integrations | **~$4.39B** | A collateral/yield primitive — *what Vanna holds*, not a rival |
| **Aave v4** | "Unified liquidity" (Hub-and-Spoke) | Reference standard | multi-$B (v4 not fully live) | Unifies *lending liquidity*, not *derivatives margin* |

**Failed comparables (causal death mechanism):**
- **DeltaPrime** — **ops/security death**: Sept-2024 single-key ProxyAdmin compromise (~$6M) + Nov-2024 valuation-logic bug in reward/swap path (~$4.75M). Two drains in two months killed "trust us with your whole portfolio." **← the death Vanna most structurally risks** (concentrated cross-margin + live mark).
- **Prime Protocol** — **adoption death**: "first cross-chain prime brokerage," now ~$353K TVL. No builder ever depended on it → nothing held TVL when incentives lapsed.
- **PrimeX V1** — **adoption death**: funded, real tech, token sale, now ~$11.5K TVL. Product-that-never-became-infra.

**Strategic call:** **Reframe, don't contest "onchain credit layer."** Sit **on top of / adjacent to** the credit layers (Morpho/Euler/Aave supply credit; Vanna is the **margin brain + real-time derivatives valuation** that plugs in). Yes-and, not versus.

---

## 2. Perp/derivatives venues + CEX portfolio margin

**Per-venue (who would want a credit-aggregation layer above them):**
- **Structurally hostile** (their moat *is* their book): **Hyperliquid** (builder codes/HIP-3 pull flow INTO its shared book), **Lighter** (verifiable zk book), **Aster**.
- **Natural complements** (vault/synthetic or differentiated exposure): **Derive** (options — the flagship pairing leg; its PM only nets *within* Derive), **Ostium** (RWA/macro perps), **Avantis** (Base synthetic).
- **Ambivalent** (run internal cross/portfolio margin, want captive flow): **Drift**, **Aevo**, **Paradex**.

**CEX portfolio margin** = proven precedent, but walled + gated: **Binance** PM (needs 100k–10M USDT), **Bybit** UTA 2.0, **OKX** Unified Account, **Deribit** PME (SPAN-style scenario margin — closest technical analog, confined within Deribit).

**Aggregation verdict (2026-08-20):** **No one aggregates order-book perp liquidity across rival independent books.** Routers (MUX, Vooi) route to *vault* venues or one chosen venue; **Orderly** is a *single shared CLOB* (shared liquidity ≠ aggregation). Founder's "order-book venues won't aggregate" holds — **but** Vanna's real wedge is cross-venue **risk/credit netting** (Hyperliquid perp ↔ Derive option under one margin layer), which needs no venue cooperation. Competitive caveat: perps may consolidate onto *one* book (Hyperliquid), weakening the "aggregate many books" framing — another reason to lead with **netting**, not liquidity aggregation.

---

## 3. Risk infrastructure + TradFi margin terminology (→ Phase 2 ruling)

**Risk-infra providers** — all advisory/rating/monitoring, none IS the enforced engine:
Gauntlet (sim + curation), Chaos Labs (Risk Oracles push params), Credora/RedStone (ratings), Block Analitica (Maker/curator), LlamaRisk (frameworks/stewards), Steakhouse (advisory + largest Morpho stablecoin curator), Hypernative (security watchdog). **Their vocabulary — "economic security, solvency, capital efficiency" — is the buyer's language; speak it, but don't claim to BE a Gauntlet.** Vanna is the enforced surface they would advise *on*.

### ⚖️ PHASE 2 TERMINOLOGY RULING
Against real TradFi regimes (Reg T; FINRA 4210(g) portfolio margin; CME SPAN 2; OCC STANS/TIMS; PB cross-margining; Basel SA-CCR netting) — "portfolio margin" specifically means **scenario-based risk-netting of offsetting positions** (revalue portfolio under stress, let P&L cancel).

**Vanna = cross-collateralised composable credit, NOT portfolio margining.** It nets **value** (collateral ÷ debt), not **risk**; with only XLM+USDC there are no offsetting legs; no scenario/pricing engine; static 1.1 HF = the Reg-T/haircut family, same primitive as Aave.

| Bucket | Terms |
|---|---|
| **OWN** | cross-margin · cross-collateralised · **risk-bounded execution surface** · portfolio-level exposure limits *enforced in-protocol* |
| **EDUCATE** | cross-venue delta-neutral · derivatives cross-margin · real-time position mark (Track Token) |
| **USE-DON'T-OWN** | composable credit · composable leverage (crowded; for comprehension) |
| **AVOID** | **portfolio margin** · **risk-based netting** (indefensible on a 2-asset testnet; a Credora/Gauntlet-literate allocator will catch it) · "Greeks Dashboard" (retired) · flat 10x/900% LTV |

Roadmap note: if Vanna later adds offsetting instruments (perps/options) **and** a scenario-revaluation engine, "portfolio margin" becomes defensible. Not today.

---

## 4. Agentic / MCP finance (enforcement-tier classification)

Frame: (1) talk-about · (2) read-only · (3) move-capital-under-ENFORCED-constraints. Most market markets (3) while doing (1)/(2).

| Entity | Tier | Enforcement location |
|---|---|---|
| **Coinbase AgentKit + x402** | **3** (qualified) | CDP Wallet Policies at the TEE signing layer — but **off by default** in bare AgentKit (dev must attach policies) |
| **Circle Agent Stack** | **3** | Policies "enforced at the wallet layer" (mechanism publicly vaguer); natively supports x402; ships a first-party MCP server |
| **Crossmint + GOAT** | **3** (external) | Enforcement in the Crossmint smart wallet (spend caps/allowlists, key in TEE); GOAT itself is an unenforcing tool-catalog — **repo now archived** |
| **Halliday** | **3** | Immutable, on-chain workflow guardrails ("zero-trust delegation"); a16z $20M Series A (Mar-2025) |

**Full cohort now covered (16 entities):** + Enso, Definitive, Almanak, Giza/ARMA, Axal, Olas, Theoriq, Virtuals, HeyAnon, Wayfinder, Griffain, **Brahma ConsoleKit** (strongest — SAFE smart-account policy engine). Enforcement in this cohort is either **custody** (non-custodial: agent can trade, only user withdraws) or **spend-scope** (session keys, per-tx caps, allowlists — ERC-4337/smart-account). Insight the field agrees on (thirdweb/Openfort/Fystack): *checks in the agent's code can be bypassed by a bug or prompt injection — enforcement must sit BELOW the agent, at the signer/contract.*

**MCP spec (primary, rev 2025-06-18 + the 2026-03-16 annotations blog):** MCP **explicitly does NOT standardize permissioning or capital limits.** Human-in-the-loop is a **SHOULD, not MUST**; tool annotations (`readOnlyHint`/`destructiveHint`) are **"untrusted hints"** — *"a server can claim readOnlyHint:true and delete your files anyway."* "The spec itself tells you not to rely on the spec for safety." Finance MCP servers (Coinbase Payments MCP, deBridge, WAIaaS, Kukapay) inherit wallet/human-confirm safety; **none enforce a capital-risk policy.**

**Adjacent copilots:** **Mercury Command is the model** — *"the AI is read-only; any real-money action requires a separate deterministic approval."* Sardine tiers HITL-vs-autonomous by design; Ramp/Brex push autonomy wrapped in **policy they own**. Nobody credible lets the model be final authority over capital.

### 🎯 THE SHARP FINDING (answers §3.3 — the strongest positioning insight in the whole research)
The market enforces **custody** ("the agent can't steal it") and **spend scope** ("can't spend >$X / off-allowlist") — **but almost nobody enforces SOLVENCY.** An agent can stay perfectly inside a $10k/day cap and a blue-chip allowlist and *still* lever into a liquidatable position and lose everything "very efficiently." The market's implicit answer to *"what stops an agent destroying a user's capital?"* is **"a liquidation/margin engine in the protocol contract"** — which is exactly what **no agent framework, MCP server, or copilot in the survey provides** (Brahma's policy engine enforces *action permissions*, not *portfolio solvency*).

**→ Vanna's bulletproof wedge:** *An LLM's promise not to over-lever is not a risk control; a cross-margin liquidation engine enforced at the contract is.* Vanna answers the one question the rest of the agentic stack markets around rather than solves. This is the spine of the Agentic + Risk-infrastructure narratives.

---

## 5. Market: BELIEVES vs DOES-NOT-YET-UNDERSTAND (category-creation raw material)

**Already believes (don't re-argue):** on-chain credit is an *infra/layer* business (Morpho's $175M validates it); modular/permissionless/composable accounts are table stakes; capital efficiency via shared collateral is desirable on the *spot/lending* side; agents need enforced spend guardrails (Coinbase/Circle shipped them).

**Does NOT yet understand / has no language for (Vanna's whitespace):**
- Portfolio/cross margin across **derivatives** (perps+options) on-chain, **across venues**.
- A **tokenized real-time mark** of a margin account's derivative positions (Track Token) — genuinely novel primitive *and* its largest risk surface.
- Risk **enforced in-protocol** as the product (vs advised by Gauntlet / voted by a DAO / trusted to an agent).
- **Honest sizing caveat:** the *demand* for on-chain derivatives portfolio-margin is **modelled/inferred**, not observed — on-chain options liquidity is thin. Do not present as observed demand.

---

## GATE STATUS
- **Phase 1 gate — PASSED.** ~35 named entities, dated sources (composable-credit 11 · perp/CEX 13 · risk-infra 7 + 6 TradFi regimes · agentic 4).
- **Phase 2 gate — PASSED.** One primary term recommended (**cross-margin / risk-bounded execution surface**), counter-case written, "portfolio margin" ruled AVOID with the accuracy determination.
- **Next:** Phase 3 (category) needs the founder inputs (§F) + the 10x-vs-7x and app-vs-infra sign-offs before committing one category.
