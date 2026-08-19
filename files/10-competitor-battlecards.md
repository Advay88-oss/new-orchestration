# 10 — Competitive Landscape 2026 & Battlecards

**Research date:** 6 August 2026
**Method:** Live web research against every named competitor, cross-checked with Vanna's internal research library (dated Feb 2026 — now partly stale).

> ⚠️ **Read `11-competitive-strategy-and-repositioning.md` immediately after this file.** Two of Vanna's core differentiation claims were overtaken by events between April and June 2026. This file establishes the facts; `11` says what to do about them.

---

## 1. Market size — the denominators

| Market | Size | Date / source |
|---|---|---|
| DeFi lending deposits | **$54B across 380+ protocols** | DefiLlama, Apr 2026 |
| DeFi lending rank | **2nd-largest DeFi category** after liquid staking | DefiLlama, Apr 2026 |
| Aave V3 TVL | **~$14.6B**, 15+ chains | DefiLlama, Jun 2026 |
| Morpho Blue TVL | **~$11.8B** | DefiLlama, Jun 2026 |
| Compound V3 TVL | **~$2.7B** | DefiLlama, Jun 2026 |
| Gearbox TVL | **~$400M** | Jan 2026 |
| Hyperliquid 30-day perp volume | **~$196.3B**; cumulative ~$3.9T | 30 Jul 2026 |
| Hyperliquid open interest | **~$10.5B** — more than all other major perp DEXs combined; >70% of sector OI | Q2 2026 |
| Hyperliquid share of perp DEX volume | **~44%**, up from 36.4% in Jan 2026 | Mar 2026 |
| **Stellar total DeFi TVL** | **peak ~$200M (24 Apr 2026), $161.12M (27 May 2026)** — ~7× YoY | DefiLlama |
| Blend Capital TVL | **~$110M** (+25.9% QoQ through Q1) | Messari Q1 2026 |
| Aquarius TVL | **~$51.7M** | Apr 2026 |
| Stellar DEX TVL | ~$25.9M | Apr 2026 |
| Stellar stablecoin mcap | $404M (Apr) → $324M (May) | 2026 |
| Stellar RWA footprint | **$2.4B across 65 issuances — #8 globally**; $1.8B permissionless (#4 behind ETH, BNB, SOL) | RWA.xyz, 2026 |
| Stellar avg daily smart-contract volume | **$16M/day**, up from $2M/day a year earlier | SDF, Apr 2026 |
| Agentic AI market | **~$9.89B in 2026, >42% CAGR → $57B by 2031** | Mordor Intelligence |
| Agentic commerce forecast | **$3–5T by 2030** | Galaxy / McKinsey |
| Agent-controlled B2B purchasing | **$15T by 2028** | Gartner |
| Enterprise agent adoption | 40% of commercial applications embed autonomous agents (from <5% a year earlier); 80%+ of Fortune 500 deploying active agents | AWS; Microsoft Data Security Index 2026 |

### The number that reframes everything

**Stellar's entire DeFi ecosystem is ~$161M.** That is *less than half* of Gearbox alone, and roughly **0.3%** of DeFi lending deposits.

Two readings, both true:
- **Bad:** Vanna's addressable on-chain liquidity is tiny. There is not enough Stellar DeFi capital to build a $100M-TVL protocol without importing capital or expanding chains.
- **Good and actionable:** **$20–30M TVL would make Vanna a top-3 Stellar DeFi protocol.** In the Base or Ethereum lending market that number is invisible. On Stellar it is a headline. The big-fish-small-pond thesis holds — **but only as a launch strategy, not an endgame.**

---

## 2. The landscape map, updated

```
                        UNDERCOLLATERALIZED  ·  CREDIT EXCEEDS COLLATERAL
                                          ▲
                      Gearbox (RWA/instl)  │  ★ VANNA (target)
                      10× · $400M · audited│    10× · testnet
                      SEGREGATED/COMPLIANT │    DERIVATIVES + AGENTS
                                          │
  SINGLE VENUE ◄──────────────────────────┼──────────────────────► CROSS-VENUE
                                          │
                      Hyperliquid          │  Aave · Morpho · Compound
                      44% perp vol         │  $54B lending market
                      cross-margin WITHIN  │  Morpho Agents = MCP+CLI
                      one venue, all mkts  │  OVERCOLLATERALIZED
                                          │
                                          ▼
                        OVERCOLLATERALIZED  ·  CREDIT ≤ COLLATERAL
```

**Vanna's quadrant (undercollateralized × cross-venue) has exactly one other serious occupant: Gearbox** — and Gearbox has moved to the RWA/institutional-compliance corner of it. **The derivatives-and-hedging position inside that quadrant is genuinely still open.** That part of the internal thesis survived the research.

---

# BATTLECARDS

---

## 🥇 BATTLECARD 1 — Gearbox Protocol

**Ring:** 1 (direct) · **Verdict: the benchmark — but it has moved away from Vanna's lane**

### 30-second summary
Gearbox is on-chain credit infrastructure built around the **Credit Account** primitive — a wallet with credit that can hold collateral, borrow from a pool, and execute approved actions while staying solvent. Live since 2021, through V1 → V2 → V3 → V3.1. **In 2026 it repositioned decisively to institutional RWA credit.** Its homepage now reads *"Tokenisation Lending Stack — Real-World Assets need Real-World Lending"* and sells *compliant on-chain credit infrastructure for tokenised assets: segregated accounts, margin, prime brokerage, portfolio loans.*

### Hard numbers
| Metric | Value |
|---|---|
| TVL | ~$400M (Jan 2026) |
| Transaction volume | **$12B+** all-time |
| Spent on security | **$3M+** |
| Audits | **30+ by leading firms** |
| Bug bounty | **Live on Immunefi** |
| Security incidents | **0 breaches since 2021**; $0 bad debt historically |
| Prime Brokerage product | **10× max leverage · 10K+ accounts opened · $1.5B all-time borrowed** |
| Savings product | up to **14% APY** · **$3.7B** cumulative supply · **80%** avg utilization |
| Token | GEAR (governance, Snapshot); staking/revenue-share under DAO discussion for 2026 |
| Curators | Re7 Labs, Chaos Labs, Tulipa Capital |
| Chains | Ethereum + L2s; 2026 expansion to Lisk, Monad and others |
| GTM motion | **Sales-led — "Request a Demo" form, named partner logos** |
| Partners | Pendle, Lido, Renzo, Convex, Ethena, Curve |
| Developer surface | Public GitHub (core-v3, sdk, integrations-v3, periphery-v3, liquidator-v2), SDK reference, permissionless bytecode repository |

### Their strengths — do not dismiss these
- **$3M+ on security, 30+ audits, five years, zero breaches.** This is the single hardest thing in DeFi to fake and the thing Vanna most lacks.
- **Permissionless market creation with institutional curators.** Others build markets *for* them — that's the infrastructure flywheel Vanna's own research says all three dead protocols never achieved.
- **Compliance built into the primitive:** per-account allowlists, role policies, jurisdiction filters, per-user risk limits, issuer-aware mechanics, modular legal enforcement (freezes, transfers, inheritance).
- **RWA timing.** They read tokenisation correctly and got there first.
- Fully public codebase and SDK.

### Their real weaknesses
- **They have vacated derivatives.** No options, no perps, no multi-leg hedging, no cross-venue delta-neutral tooling. Their integrations are yield: Curve, Convex, Lido, Pendle, Ethena.
- **No agent surface at all.** No MCP server, no agent tooling, no CLI-for-agents story. In a year where Morpho and Base both shipped MCP, Gearbox has nothing. **This is the clearest open flank.**
- **Compliance is a wedge and a cage.** KYC, allowlists, jurisdiction filters, "Apply for Account" — permissioned by design. A pseudonymous trader or an autonomous agent cannot use Gearbox Prime Brokerage.
- **Sales-led motion is slow.** Demo forms and approval gates don't serve self-serve retail or developers.
- Yield-strategy heritage means single-asset leverage loops, not portfolio margin across offsetting legs.

### Vanna's differentiated advantages
| Advantage | Proof point |
|---|---|
| Derivatives-and-hedging native | RiskEngine values external positions as collateral via TrackingToken; one solvency ratio across legs that intentionally offset |
| Agent-native | MCP + CLI + SDK converging on one `open_position`; zero-custody scoped session keys |
| Permissionless | No KYC, no allowlist, no application, no jurisdiction filter |
| No kink | Smooth polynomial rate curve vs the kinked utilization curves used across the entire lending category |

### Objection scripts
**"Gearbox already does on-chain credit and has $400M and 30 audits."**
> They do, and they're the reason the category exists. But look at what they sell now: compliant credit for tokenised assets, segregated accounts, KYC allowlists, an application form. That's a real business and it isn't ours. Gearbox extends credit to an identified institution to lever a yield position. Vanna extends credit to a pseudonymous trader or an autonomous agent to run a multi-leg hedged book across venues. Different customer, different primitive, different risk problem.

**"Why wouldn't Gearbox just add derivatives and agents?"**
> They could. They also spent five years and $3M building compliance infrastructure for tokenised securities, and every one of those design choices — allowlists, jurisdiction filters, issuer-aware mechanics — points away from permissionless agents. Roadmaps follow customers.

### Positioning rule
**Never claim superiority.** Gearbox is bigger, older, audited and unhacked. The frame is always *different job to be done*. Concede security and scale openly — it buys credibility for the differentiation claim that follows.

---

## 🥈 BATTLECARD 2 — Hyperliquid

**Ring:** 2 (substitute) · **Verdict: the real competitor for most traders, and the most under-appreciated threat**

### 30-second summary
A purpose-built L1 with a fully on-chain order book, sub-second finality and gasless order placement. In 2026 it is not just the dominant perp DEX — via **HIP-3** (permissionless market deployment, live Oct 2025) and **HIP-4** (outcome/prediction contracts) it is becoming a **single venue that hosts every market**: crypto perps, commodities, tokenized equities, FX, S&P 500, prediction markets. Raised **zero venture capital**; 31% of HYPE supply airdropped to ~94,000 users.

### Hard numbers
| Metric | Value |
|---|---|
| Share of perp DEX volume | **~44%** (Mar 2026), up from 36.4% (Jan 2026) |
| 30-day perp volume | ~$196.3B (Jul 2026); cumulative ~$3.9T |
| Open interest | **~$10.5B — more than all other major perp DEXs combined**; >70% of sector OI |
| RWA perp OI | record **$2.65B** (21 May 2026), doubled in ~2 months |
| Daily volume | frequently >$7B; peaks ~$21.8B |
| 2025 revenue | **>$650M — 4th-highest in all of crypto** |
| HYPE market cap | ~$10.5B–$15.5B through H1 2026 |
| Fees | 0.025% maker / 0.05% taker |
| Competitor collapse | dYdX, GMX, Vertex, Drift + long tail fell from 65% → 27% share in a year |

### Why this is the threat Vanna's internal research missed
Vanna's central pitch is: *isolated margin fragments your book across venues; unify it.* **Hyperliquid is solving the same problem from the opposite direction — by absorbing every market into one venue where margin is already unified.**

If a trader can hold BTC perps, silver, the S&P 500, tokenized equities and prediction contracts in **one Hyperliquid account under one margin system**, the fragmentation problem largely dissolves for them — without any credit protocol. And Hyperliquid has $10.5B of open interest and 44% market share, versus Vanna's testnet.

**Vanna's honest remaining edges over Hyperliquid:**
1. **Real assets, not synthetic exposure.** Vanna borrows actual tokens deployable anywhere. Hyperliquid gives synthetic exposure inside Hyperliquid.
2. **No funding rate on the credit.** You pay borrow interest, not perpetual funding.
3. **Credit that leaves.** Hyperliquid margin cannot be deployed to Blend, Aave, Pendle or an AMM. Vanna's can.
4. **Spot + yield + derivatives in one solvency ratio.** Hyperliquid unifies *derivatives*; it does not unify a yield-farming leg with a perp leg.
5. **Agents get credit, not just access.** An agent on Hyperliquid still needs its own capital.

### Objection script
**"I just use Hyperliquid. One account, every market, deepest book."**
> And for pure directional derivatives, that's the right answer — we're not going to out-liquidity Hyperliquid. The difference is what the collateral can *do*. On Hyperliquid your margin is synthetic exposure that lives inside Hyperliquid and pays funding. On Vanna the same collateral becomes real borrowed assets you can put into a lending pool, an AMM, or a perp — and all of it marks into one health factor. Most people running a carry trade are already doing both: perps on Hyperliquid, spot and yield somewhere else. Vanna is the credit line underneath that, not a replacement for the venue.

### Strategic note
**Do not position against Hyperliquid. Position as complementary.** Hyperliquid is on Vanna's own ecosystem logo wall. The best long-term outcome is Vanna credit funding Hyperliquid positions. The comparison that works is *funding source*, never *venue*.

---

## 🔴 BATTLECARD 3 — Morpho (and Morpho Agents)

**Ring:** 2 (substitute) escalating to **Ring 1 threat** · **Verdict: this is the finding that most changes Vanna's story**

### 30-second summary
Morpho Blue is a minimal, permissionless lending primitive with curated vaults on top — **~$11.8B TVL**, second-largest DeFi lending protocol behind Aave. Overcollateralized. **And in April 2026 it launched Morpho Agents (beta): an MCP server and CLI giving any AI agent full read, simulate and write access to Morpho across Ethereum and Base.**

### What Morpho Agents actually shipped
- **MCP server + CLI**, working with **Claude, Cursor, Codex, Windsurf and 30+ other agent clients**
- **Full read, simulate and write** access
- **Machine-readable protocol knowledge layer** (`AGENTS.md`)
- Works with **any wallet infrastructure** — Coinbase, Safe, Fireblocks, local keystore
- **Every write operation runs through simulation before execution**
- Two products: **User Agent** and **Builder Agent**
- Stated use cases: enterprises adding lending infra, agent developers building portfolio agents / yield optimizers / risk monitors, app builders shipping earn and borrow products
- Their framing: *"Can an AI agent one-shot a Morpho integration?"* — a week of SDK wrangling reduced to minutes

**This is architecturally near-identical to Vanna's MCP + CLI + SDK pitch — from a protocol with roughly 70× Gearbox's TVL, full audits, and a live mainnet.**

### The honest read
| Claim | Vanna | Morpho Agents |
|---|---|---|
| MCP server for agents | ✅ | ✅ |
| CLI for agents | ✅ | ✅ |
| Simulate before execute | ✅ (`simulate_position`) | ✅ |
| Non-custodial | ✅ | ✅ |
| Mainnet | ❌ testnet | ✅ |
| Audited | ❌ | ✅ |
| TVL | $0 | ~$11.8B |
| **Undercollateralized credit** | **✅ up to 10×** | **❌ overcollateralized** |
| **Cross-venue deployment of borrowed capital** | **✅** | **❌** |
| **Unified portfolio margin across markets** | **✅** | **❌** |
| **Derivatives / multi-leg hedging** | **✅ (target)** | **❌** |
| **Behavioural credit score for agents** | **✅ (designed)** | **❌** |

### What this means
**"MCP-native" is no longer a differentiator. It is table stakes.** Any Vanna content whose central claim is *"agents can call DeFi through MCP"* is now describing something Morpho shipped in April on mainnet at $11.8B TVL.

**The surviving differentiator is narrower and sharper: Morpho lets an agent lend and borrow *against collateral it already has.* Vanna lets an agent borrow capital *it does not have.*** That is the whole difference, and all agent-facing messaging must now lead with it.

### Objection script
**"Morpho already has an MCP server and it's on mainnet with $11.8B."**
> They do, and it's good work — genuinely the right pattern, simulate-then-write, wallet-agnostic. But notice what an agent can actually do with it: supply collateral and borrow less than it supplied. That's useful and it's not credit. Every agent that needs Morpho already has capital. Vanna is for the agent that doesn't — undercollateralized credit up to 10×, deployable across venues, under one health factor, with the agent's own track record deepening the line over time. Morpho gives agents access to a lending market. We give them a balance sheet.

### Threat watch
If Morpho ships a leveraged or looping product with an agent surface, the differentiation narrows sharply. **Monitor Morpho's roadmap monthly. This is the highest-priority competitive watch item Vanna has.**

---

## 🟠 BATTLECARD 4 — Base MCP (Coinbase)

**Ring:** 3 (agentic stack) · **Verdict: aggregator, not credit — but it is eating the "agent front door" position**

### What it is
Launched **26 May 2026**. An MCP gateway letting AI agents such as Claude execute on-chain DeFi on Base. Integrates six ecosystem protocols via **skill plugins**:

| Function | Protocols |
|---|---|
| Lending | **Morpho**, Moonwell |
| Swaps / LP | **Uniswap**, **Aerodrome** |
| Perpetuals | **Avantis** |
| Token launches / agent tokens | Bankr, Virtuals |

- Developers can write additional skill plugins from published markdown specs
- Supports **x402 micropayments**
- **Hands unsigned transactions to users for approval** — the same "nothing signs without you" pattern Vanna markets
- Builds on Coinbase AgentKit, embedded wallets, onramp
- Reads balances and transaction histories across EVM chains
- A separate **Payments MCP** covers agent payments on Base, Polygon and Solana

### Why Vanna should pay attention
**Uniswap, Aerodrome and Avantis are all on Vanna's own ecosystem logo wall — and all three are already reachable by agents through Base MCP.** The "one MCP endpoint, many venues" position is being claimed by Coinbase with Coinbase's distribution.

### What Base MCP does not do
It is **plumbing, not credit.** No lending book, no risk engine, no health factor, no unified margin, no undercollateralized borrowing, no behavioural underwriting. An agent using Base MCP must arrive funded.

### The strategic opportunity, not just the threat
**Base MCP is plugin-extensible from published markdown specs.** The correct move is not to compete with Base MCP — it is to **become a skill plugin inside it.** Vanna as the credit plugin in an ecosystem that already has lending, swaps and perps plugins is a far better position than Vanna as a rival gateway nobody has heard of.

> ⚠️ This would require a Base deployment. Base is already in Vanna's footer and developer docs. **Flag as a strategic decision for the team, not a marketing claim.**

---

## 🟡 BATTLECARD 5 — Blend Capital

**Ring:** 2 (substitute) **AND integration partner** · **Verdict: frenemy — and the source of the most important risk lesson available to Vanna**

### The facts
- **Stellar's dominant lending protocol: ~$110M TVL**, +25.9% QoQ through Q1 2026 (crossed $80M early 2026)
- Non-custodial; users create **isolated or shared liquidity pools**
- **Vanna's primary external yield destination.** Blend b-tokens are tracked as `BLEND_XLM` / `BLEND_USDC` and valued as collateral by Vanna's RiskEngine
- Roughly **68% of all Stellar DeFi TVL** sits in Blend

### 🚨 The February 2026 exploit — read this carefully
On **22 February 2026**, Blend's **community-managed YieldBlox DAO Pool** was drained of approximately **$10.8M via an oracle manipulation attack**. The attacked collateral was **USTRY**, a yield-bearing treasury-bond token issued by Etherfuse, and the manipulation ran through Blend's interaction with the Stellar DEX (SDEX). **The core Blend protocol was not broken** — the failure was in economic risk modelling of a permissioned-pool collateral asset.

**Why this matters more to Vanna than any other single data point in this research:**

1. **It happened on Vanna's chain, in Vanna's year, to Vanna's main integration partner.** Vanna cannot tell a story about learning from DeltaPrime's $10.8M hack without acknowledging that a $10.8M hack just happened on Stellar too.
2. **It was an oracle attack.** Vanna's entire solvency model rests on Reflector with a **~5-minute cadence**, and Vanna's docs already name oracle lag as one of two reasons the threshold is 1.1×. An adversary who can move a thin Stellar market inside that window is attacking the same surface.
3. **Vanna's exposure is direct.** Blend positions are *counted as collateral* inside Vanna margin accounts via b-token → `b_rate` → underlying → oracle price. A compromised or mispriced Blend position propagates into Vanna's health factor.
4. **The named root cause was collateral-asset risk modelling in a permissioned pool** — precisely the discipline Vanna needs to demonstrate before mainnet.

**Recommended posture:** do not hide from this, and do not exploit it against a partner. Address it *technically and specifically* — which collateral assets Vanna accepts, why the accepted set is deliberately narrow (XLM, USDC), what the oracle-deviation guards are, and what happens if a Blend position is mispriced. **A published "how Vanna would have survived February 22nd" analysis would be one of the highest-trust content assets available pre-mainnet.** Get engineering sign-off before publishing anything on this.

### Competitive relationship
Blend is where a Stellar LP puts USDC today. Vanna's Earn product competes for the same deposit. The honest differentiation: **Vanna's borrowers can take up to 10× rather than overcollateralizing, so utilization — and therefore LP yield — runs structurally higher.** That is a real, mechanical argument. It is also an argument that Blend's LPs will only believe after Vanna is audited.

---

## 🟡 BATTLECARD 6 — Aave (and the overcollateralized pole)

**Ring:** 2 (substitute) · **Verdict: the reference point, not a rival**

- **Aave V3: ~$14.6B TVL across 15+ chains.** Compound V3 ~$2.7B. Spark, Fluid, Euler occupy the same pole.
- Aave's depth caps utilization, which caps APY — the exact mechanism Vanna's flywheel argument exploits.
- **Confirmed and useful:** every major lending protocol (Aave, Morpho, Spark, Compound, Fluid, Euler) sets rates on a **kinked utilization curve** where rates jump sharply near 100%. **Vanna's smooth no-kink polynomial is therefore a genuine, verifiable technical differentiator across the entire category.** This was worth confirming and it holds.
- Agent surface: community MCP servers exist for Aave data (e.g. `graph-aave-mcp`, 14 tools via The Graph; `defi-rates-mcp` covering 14+ protocols across 6 chains, some x402-paid with built-in spend caps) — but these are **read-only data servers**, not first-party write access. Aave itself has not shipped a Morpho-Agents equivalent.

**Use Aave as the illustrative pole in the "forced choice" argument — never as an attack target.** Morpho and Aave are both on Vanna's ecosystem logo wall.

---

## 🔵 BATTLECARD 7 — The Agent Credit Score field

**Ring:** 1 (direct threat to Vanna's claimed moat) · **Verdict: the "unforkable data moat" is contested, and standards are forming fast**

Vanna's internal position is: *"Smart contracts can be forked, but high-quality credit history cannot be forked. This is one of Vanna's strongest possible data moats."* **That claim needs immediate qualification.**

### Who else is in this space (2026)

| Player | What they have |
|---|---|
| **Kojiru — Agent Credit Score (ACS)** | A **300–850 scale deliberately matched to FICO**, powered by a recursive Bayesian model built for machines, updating continuously after every task. **Identified the identical deadlock Vanna identified:** lenders won't extend credit without a track record; agents can't build a track record without working capital; the loop never closes. |
| **Ethereum ERC-8004** | Agent **identity standard** |
| **Visa Trusted Agent Protocol (TAP)** | Agent trust/authentication at payment-network scale |
| **World Economic Forum — Know Your Agent (KYA)** | Emerging governance framework |
| **IETF (March 2026 Internet-Draft)** | **Trust scoring for autonomous agent payments** — standardisation in progress |
| **Alchemy (Feb 2026)** | Shipped autonomous agent purchase of compute credits and blockchain data via on-chain wallets and USDC on Base — widely reported as agents getting on-chain credit |
| **Kite AI** | Agent-native trustless payment infrastructure |

**Emerging consensus across IETF / WEF KYA / Visa TAP / ERC-8004: agent reputation should capture seven dimensions** — effectively a credit-bureau model adapted for machine actors.

### The three unanswered questions in the field — and Vanna's exposure to each

1. **Who is liable when an agent causes a loss?** No jurisdiction has moved. Vanna's Risk Guardian executes defensive actions autonomously — liability is genuinely unresolved. **Legal review needed before any mainnet autonomy claim.**
2. **Can on-chain reputation be trusted, given how quickly it can be manufactured?** **This is a direct, unaddressed vulnerability in Vanna's Agent Score design.** A 742-score, 214-day, $1.2M-volume, 47-liquidations-avoided profile is farmable by an adversary willing to spend time and capital. Vanna's docs and site say nothing about sybil resistance, cost-to-fake, or capital-weighting. **Fix the design and then make the fix the marketing.**
3. **Who governs agents that have outgrown their operators?** Open.

### Revised strategic read on the moat
- ❌ **"Nobody else is building agent credit scores"** — false. Kojiru is directly competitive; standards bodies are converging.
- ✅ **"Nobody else is building a credit score derived from an agent's behaviour inside a live undercollateralized margin account, where the score determines the credit line"** — this remains true and defensible.

The distinction is that everyone else is building **reputation for payments**. Vanna is building **underwriting for credit**. A payment reputation says *this agent is who it claims and pays its bills*. An underwriting score says *this agent can be trusted with 10× leverage and will not blow up the pool*. Those are different products, and only Vanna's requires a margin account to generate.

**Recommended repositioning:** stop claiming to invent the category. Claim the **underwriting layer** on top of the emerging identity standards. Align publicly with **ERC-8004 / KYA** rather than competing with them — Vanna consumes agent identity and produces a credit decision. That is a better, more defensible, and more partnership-friendly position than a proprietary score in a standardising market.

---

## 🟢 BATTLECARD 8 — Ecosystem watch (lower priority)

| Player | Note |
|---|---|
| **Aster** | Fast-rising perp DEX: multi-chain, high leverage, retail-friendly UX, incentive-driven. Proved perp DEX share rotates quickly. On Vanna's logo wall. |
| **Avantis** | Perps on Base. On Vanna's logo wall **and** a Base MCP skill plugin. |
| **Derive** | Options. On Vanna's logo wall; the "Optimism via Derive" reference. Vanna's stated options path. |
| **Lighter** | Dark-horse perp DEX, late-2025 TGE. |
| **dYdX, GMX, Vertex, Drift** | Collectively collapsed from 65% → 27% of perp share in a year. Cautionary, not competitive. |
| **Arcadia Finance** | Margin accounts, asset-management focus, narrow integrations. Still Ring 1 but small. |
| **PrimeX Finance V2** | The pivot survivor of a V1 that failed on PMF. Worth a check-in. |
| **Ethena, Pendle** | Compete for the *"structured delta-neutral yield"* mindshare Vanna's strategy pages target. **Both are Gearbox partners.** |
| **Moonwell, Bankr, Virtuals** | Base MCP plugin ecosystem. |
| **Kojiru, Kite AI** | Agent credit / agent-native payment infrastructure. See Battlecard 7. |

---

## 3. Answers to the six questions the research pass had to settle

**Q1 — What is the measurable capital inefficiency of a multi-leg book on isolated margin?**
Still not cleanly quantified in public data, and it remains the single most valuable missing number in Vanna's arsenal. **Recommendation: build it internally.** Take a real delta-neutral carry (BTC spot long + BTC perp short + idle stablecoin), price it on Hyperliquid + a spot DEX + a lending market, and compute the capital required versus the same book on unified portfolio margin. A credible, reproducible number here would carry more weight than any messaging work.

**Q2 — Who is closest to an agent credit surface, and how long is Vanna's lead?**
**Vanna's lead on "MCP-native DeFi" is gone** — Morpho shipped April 2026, Base shipped May 2026. **Vanna's lead on "MCP-native *undercollateralized credit*" is real but likely 6–12 months**, and it closes the moment Morpho or Base MCP adds a leverage product or a Gearbox plugin.

**Q3 — Does any competitor have a behavioural credit score?**
Yes — Kojiru's ACS is directly competitive, and IETF/WEF/Visa/ERC-8004 are standardising agent reputation. **Vanna's narrower claim (underwriting inside a live margin account, score determines the line) survives. The broad claim does not.**

**Q4 — What did Gearbox's SDK-to-first-third-party-build curve look like?**
Not precisely datable from public sources, but the trajectory is clear and instructive: **2021 launch → V2 → V3 → V3.1, and only by 2026 does it have institutional curators (Re7, Chaos Labs, Tulipa) deploying markets.** That is a **~5-year** arc from protocol to infrastructure-others-build-on. Vanna's internal roadmap targets a first third-party SDK integration at month 12 post-launch. **That is aggressive by a factor of several.** Plan accordingly and do not treat it as a slam dunk.

**Q5 — Stellar DeFi TVL vs Base/Arbitrum: does big-fish-small-pond hold?**
**Yes as a launch strategy, no as an endgame.** Stellar DeFi is ~$161M total — Vanna could be top-3 on Stellar with $20–30M. But Stellar's real strength is elsewhere and it is genuinely strong: **$2.4B in RWAs (#8 globally, #4 in permissionless), $16M/day smart-contract volume (8× YoY), and both x402 and MPP live on mainnet with SDF as an x402 Foundation Premier member.** SDF's 2026 plan targets $1B in network asset value growth, 15 new enterprise partners with 5+ deployed. **The correct framing is not "Stellar has DeFi liquidity" — it's "Stellar has RWAs, institutions and agentic payment rails, and no credit layer."**

**Q6 — Which logo-wall venues are genuinely reachable, and at what cost?**
Live today: **Blend, Aquarius, Soroswap** (all Stellar). Everything else — Hyperliquid, Uniswap, Morpho, Aerodrome, Avantis, Derive, Aster, Katana — is **on a different chain** and requires either a Base/Arbitrum deployment or a cross-chain path Vanna has not built. **This is the largest single gap between Vanna's marketing and Vanna's product**, and it directly determines whether the "every market at once" claim can survive scrutiny from a technical prospect.
