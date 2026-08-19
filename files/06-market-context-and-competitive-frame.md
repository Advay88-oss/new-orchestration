# 06 — Market Context & Competitive Frame

> Deep competitor profiles are a **separate research pass**. This file establishes the frame, the categories, the named field, and the graveyard lessons — so the next pass has somewhere to land.

---

## 1. Category definition — "composable credit"

**The definition Vanna operates under:**
Credit is *composable* when the borrowed capital can be **moved, redeployed and reused across protocols and markets** while remaining under a single risk framework, instead of being locked to the venue that issued it.

**The four/six properties named in internal research:** portability · interoperability · programmability · reusability (extended sets add composability and policy-boundedness).

**The analogy that makes it click:** a normal DeFi loan is cash you withdraw from one bank and physically carry to another. Composable credit is a **prime-brokerage margin line** — the broker extends credit, you trade it anywhere on the platform, and the broker marks your whole book to one solvency number.

**The liquidity-multiplication thesis:** because one unit of pool liquidity backs up to 10× of working capital, composable credit produces roughly a **10× liquidity expansion** for the venues that receive the deployed capital. This is Vanna's argument to *other protocols*: integrating Vanna brings them multiplied order flow, not just users.

---

## 2. The competitive taxonomy — four rings

The GTM agent should never say "our competitors" without specifying which ring.

### Ring 1 — Direct: composable credit / DeFi prime brokerage
Same job to be done: undercollateralized credit that moves across protocols under one risk account.
- **Gearbox Protocol (V3)** — the **surviving benchmark**. ~$300M+ TVL, universal leverage up to ~10×, has an SDK, permissionless V3, zero hacks. Scored **59/70** on the internal seven-dimension scorecard vs Vanna's ~35/70 (much of Vanna's score being design-dependent rather than proven).
- **Arcadia Finance** — margin/credit accounts, named in internal landscape research.
- **PrimeX Finance V2** — the pivot survivor of a V1 that failed on product-market fit.
- **Contango, Fluid, and similar leverage-loop products** — adjacent; verify in the next pass.

### Ring 2 — Substitutes: where the demand goes today
Not the same architecture, but where a trader's money actually is.
- **Perp DEXs:** Hyperliquid (dominant), Aster, Avantis, GMX, dYdX, Drift
- **Options:** Derive (formerly Lyra), Premia, Aevo
- **Money markets:** Aave, Morpho, Euler, Compound, Spark, and on Stellar, **Blend Capital**
- **Yield/leverage loops:** Pendle, Ethena, Gearbox strategies, various LRT loopers

> **The uncomfortable truth for positioning:** for most traders, the *real* competitor is not another credit protocol — it's **just using Hyperliquid with isolated margin and accepting the inefficiency.** The isolated-vs-unified section of the site is aimed squarely at this. The next research pass should quantify that inefficiency.

### Ring 3 — The agentic stack: partners more than rivals
Vanna's claim is that this stack has a **credit-shaped hole**.

| Layer | Players | Vanna's relationship |
|---|---|---|
| Identity | Skyfire | Complementary |
| Communication | Google A2A | Complementary |
| Wallets / signing | Privy, Turnkey, Crossmint, Coinbase AgentKit, ZeroDev | **Partner** (Privy already integrated) |
| Orchestration / liquidity routing | Eco, L2 ecosystem layers | Complementary |
| Settlement | x402 (Coinbase/Linux Foundation), MPP (Stripe/Tempo) | **Rail Vanna sits on** |
| Agent DeFi access | Base MCP and similar MCP servers | **Nearest analogue — watch closely** |
| **Credit** | **— empty —** | **Vanna's claim** |

Watch item: **Base MCP** demonstrated demand for AI clients (ChatGPT, Claude, Cursor, Codex) to interact directly with wallets and DeFi protocols. If a major chain or wallet ships a credit-enabled MCP server, that is the first true direct competitor to Vanna's agentic wedge.

### Ring 4 — The graveyard: negative benchmarks
Three studied failures. These are **argumentative assets**, not just cautionary tales — Vanna can credibly say "we studied the three deaths."

| Protocol | Peak TVL | Status | Failure mode | Root cause |
|---|---|---|---|---|
| **Prime Protocol** | $13M | Dead | **Adoption failure** | Cross-chain across too many chains → fragmented liquidity; wrong ecosystem; no integration strategy; founder lost conviction; underfunded for ambition |
| **PrimeX Finance V1** | ~$3M | Pivoted to V2 | **Product-market-fit failure** | Credit restricted to **spot margin only** — non-composable; missed perps (the dominant volume); too long in beta; oracle constraints limited assets; no SDK so no developers |
| **DeltaPrime** | $42.9M | Severely diminished | **Security failure** | **$10.8M lost to two hacks in two months.** Single EOA admin key, insufficient auditing, 828 contracts = unmanageable attack surface, security budget didn't scale with TVL |
| **Gearbox V3** | $300M+ | **Active** | — survived | Had an SDK → became infrastructure others depend on; zero hacks; earned high leverage over years of mainnet operation |

**The pattern that matters most (and the sharpest content angle available):**

> All three failures had **no SDK. Zero third-party building. None became infrastructure.** Gearbox had one, and it did.
> *Without an SDK, a DeFi protocol is an application. Applications die when attention moves. Infrastructure persists because other people depend on it.*

Vanna's MCP + CLI + SDK trio is a direct response to this pattern. **Say so.**

**Second pattern: revenue never reached sustainability.** Internal modelling puts Vanna's break-even around **$100M+ TVL** (est. revenue $950K–$2.3M/yr vs costs $1.5M–$3M/yr at that level; borderline at $50M). Below that, the protocol burns funding — the exact pattern across all three failures. *Internal only.*

**Third pattern: founder retention.** Prime Protocol's founder losing conviction was fatal. Founder-led, visible, consistent public presence is therefore a GTM requirement, not a nice-to-have.

---

## 3. Vanna's honest scorecard (internal only — never publish)

Seven dimensions a DeFi prime brokerage must clear simultaneously; failing any one is fatal.

| # | Dimension | Prime Protocol | PrimeX V1 | DeltaPrime | Gearbox V3 | **Vanna** |
|---|---|---|---|---|---|---|
| 1 | Product-market fit | 2/10 | 2/10 | 7/10 | 9/10 | **10/10 (design)** |
| 2 | Security | 5/10 | 6/10 | 2/10 | 9/10 | **? unproven** |
| 3 | Composability | 1/10 | 2/10 | 6/10 | 9/10 | **10/10 (planned)** |
| 4 | Liquidity depth | 2/10 | 2/10 | 7/10 | 9/10 | **0/10 (pre-launch)** |
| 5 | SDK / developer ecosystem | 0/10 | 0/10 | 0/10 | 7/10 | **10/10 (planned)** |
| 6 | Token / economic model | 0/10 | 2/10 | 5/10 | 7/10 | **? undefined** |
| 7 | Integration ecosystem | 1/10 | 3/10 | 7/10 | 9/10 | **10/10 (planned)** |
| | **Total** | **11/70** | **17/70** | **34/70** | **59/70** | **~35/70** |

**The verdict, stated plainly (internal):**
> Vanna has the **best theoretical design** of any composable credit protocol attempted to date. It is also **pre-launch with zero battle-tested security, no mainnet TVL, and unproven risk models.** Vanna scores strongly on **design-dependent** dimensions and unknown on **execution-dependent** ones. *Design without execution is a whitepaper, not a protocol. The gap between Vanna's vision and Vanna's proven capability is the single largest risk.*

**GTM implication:** every piece of content should push toward *evidence*, not toward *ambition*. Testnet metrics, working demos, published maths, open contract references, third-party integrations — these are the currency. Vision statements are not.

---

## 4. Market tailwinds worth citing publicly

| Tailwind | Data point | Source |
|---|---|---|
| Agentic commerce TAM | $3–5 trillion in B2C revenue by 2030 | Galaxy Research, Jan 2026 |
| Agent payments are real volume now | ~100M x402 payments on Base; $1+ transactions went 49% → 95% of volume in a year; tester-to-payer conversion up 4× in six months | Chainalysis, Jun 2026 |
| Payment standardisation | MPP spec submitted to **IETF** as the official HTTP payment standard; launched with 100+ services incl. Stripe, Anthropic, OpenAI, Shopify, Visa | Stellar dev meeting, Apr 2026 |
| Stellar is an agentic hub | x402 **and** MPP both live on Stellar mainnet; SDF is a Premier member of the x402 Foundation (Linux Foundation) | Stellar, 2026 |
| Non-crypto adoption | Cloudflare pay-per-crawl; Nous Research per-inference billing for Hermes 4 | Stellar blog, Mar 2026 |
| Big-tech rails | x402 became the first stablecoin facilitator on Google's Agentic Payments Protocol (A2A) | RZLT, 2026 |
| Multi-chain settlement is solved | x402 live on Base, Solana, Stellar, Arbitrum, Polygon, Ethereum mainnet | RZLT, 2026 |
| Derivatives are where volume is | Perps are the dominant share of DeFi derivatives volume; internal research cites ~78% | Internal research — **verify before publishing** |

**The synthesis line (strongest single argument Vanna has):**
> Agents got identity, communication, wallets, orchestration and settlement in about eighteen months. Six chains can settle an agent's payment. **Not one of them can extend an agent credit.** That's the layer we're building.

---

## 5. Scaffolding for the next competitor research pass

When the deep competitor pass runs, produce **one battlecard per competitor** using this schema (aligned to the `competitive-intel` skill's battlecard template already in the marketing toolkit):

```
COMPETITOR: [name]
Ring: 1 direct / 2 substitute / 3 agentic stack / 4 graveyard
Last updated: [date] | Owner: [name]

30-SECOND SUMMARY
  Who they are · who they target · why they win · what they're known for

HARD NUMBERS
  TVL (current + peak, w/ date + source) · chains · max leverage · assets supported
  Funding raised + investors · team size · token (yes/no, mcap, FDV)
  Audits (firms + dates) · bug bounty (platform + max payout) · incident history
  Revenue model + estimated annual revenue

ARCHITECTURE
  Credit model (over/undercollateralized, LTV, liquidation threshold)
  Account primitive · risk engine design · oracle
  Composability: which venues can borrowed capital reach?
  SDK / API / MCP: does an agent surface exist?

GTM TEARDOWN
  Positioning line · homepage hero copy · ICP · voice
  Channels: X followers + posting cadence · Discord size · docs quality
  Content engine: blog cadence, best-performing content, SEO footprint
  Partnerships + ecosystem programme
  Community incentives: points, airdrop, campaigns

THEIR STRENGTHS  (do not dismiss — prospects have heard their pitch)
THEIR REAL WEAKNESSES  (evidence only, no wishful thinking)

VANNA'S DIFFERENTIATED ADVANTAGES  (each needs a proof point from 04's proof bank)
WHERE VANNA IS BEHIND  (honest; internal only)

OBJECTION SCRIPTS
  "They have X and you don't" → acknowledge, reframe, redirect
  "They're bigger / more established" → reframe tenure
  "They're cheaper" → TCO / capital-efficiency reframe

MESSAGING ANGLES THIS UNLOCKS
  Comparison-page angle · content angle · keyword angle
```

**Priority order for the deep pass:**
1. **Gearbox V3** — the benchmark; determines the entire positioning frame
2. **Hyperliquid** — where the demand actually is; the real substitute
3. **Aave + Morpho** — the "credit that moves but never exceeds collateral" pole
4. **Blend Capital** — same chain, adjacent, and already an integration partner: **frenemy analysis needed**
5. **Base MCP / any credit-enabled agent DeFi server** — the agentic wedge threat
6. **Derive, Avantis, Aster** — venue partners that could vertically integrate credit
7. **Arcadia, PrimeX V2, Contango** — direct-ring completeness
8. **Ethena, Pendle** — delta-neutral yield substitutes competing for the same "structured yield" mindshare

**Questions the pass must answer:**
- What is the actual, measurable capital inefficiency of running a multi-leg book on isolated margin? (Quantifies the entire pitch.)
- Which competitor is closest to shipping an agent credit surface, and how long is Vanna's lead?
- Does any competitor have a behavioural credit score? (If not, the Agent Score moat is real.)
- What did Gearbox's SDK adoption curve actually look like, and how long from launch to first third-party build?
- How large is Stellar DeFi TVL vs Base/Arbitrum, and does big-fish-small-pond hold?
- Which venues on the logo wall are genuinely reachable, and what would each integration cost?
