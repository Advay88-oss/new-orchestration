# 11 — Competitive Strategy & Repositioning

**Version 1.0 · Compiled 7 Aug 2026 · Read immediately after `10-competitor-battlecards.md`**

File 10 established the facts. This file says what to do about them.

> **Tier discipline.** Sections marked **[PUBLISHABLE]** may inform external content
> subject to the usual `08-facts-ledger-and-claim-safety.md` gate. Sections marked
> **[INTERNAL — TIER E]** must never appear in external content in any form, including
> paraphrase. The substitution table in §7 is the part the content pipeline consumes.

---

## 1. What changed, and what it costs

File 10 retired two claims that Vanna's positioning had been resting on.

| Retired claim | What killed it | Cost |
|---|---|---|
| **"Vanna is MCP-native — agents can call DeFi through MCP"** | Morpho Agents shipped MCP + CLI on mainnet, April 2026, ~$11.8B TVL, audited, working with Claude/Cursor/Codex/Windsurf + 30 clients. Base MCP shipped May 2026. | The entire agent-layer differentiation as previously written. MCP is now table stakes. |
| **"Nobody else is building agent credit scores — high-quality credit history is an unforkable data moat"** | Kojiru's ACS (300–850, FICO-matched, recursive Bayesian, identified the identical deadlock). Plus ERC-8004, Visa TAP, WEF KYA, an IETF Internet-Draft on agent trust scoring, Alchemy, Kite AI. | The "unforkable moat" framing. Standards are converging on a credit-bureau model for machines. |

**What survived intact.** The quadrant thesis. Undercollateralized × cross-venue has
exactly one other serious occupant — Gearbox — and Gearbox has moved to the
RWA/institutional-compliance corner of it. **The derivatives-and-hedging position
inside that quadrant is genuinely still open.**

**The strategic error to avoid now:** defending the retired claims. They are gone.
Content that keeps asserting MCP-native leadership is describing a competitor's
shipped product, and a technical prospect will know that within one search.

---

## 2. The replacement position **[PUBLISHABLE]**

### 2.1 The one-line reframe

> **Morpho gives agents access to a lending market. Vanna gives them a balance sheet.**

Everything downstream follows from that sentence. Morpho lets an agent borrow
*against collateral it already has*. Vanna lets an agent borrow capital *it does not
have*. That is the whole difference and it is now the lead, not a footnote.

### 2.2 The new claim hierarchy

Lead with tier 1. Support with tier 2. **Never lead with tier 3.**

| Tier | Claim | Why it holds |
|---|---|---|
| **1 — Lead** | Undercollateralized credit for agents and pseudonymous traders. Borrow what you don't have, up to 10×. | No named competitor does this with an agent surface. Gearbox does undercollateralized but is KYC-gated and has no agent tooling. Morpho has the agent tooling and is overcollateralized. |
| **1 — Lead** | One solvency ratio across legs that intentionally offset. | Hyperliquid unifies derivatives but not a yield leg with a perp leg. Morpho has no portfolio margin. |
| **2 — Support** | Credit that leaves. Real borrowed assets deployable to any venue, not synthetic exposure locked in one. | The honest edge over Hyperliquid. |
| **2 — Support** | No kink. Smooth polynomial rate curve. | Genuinely category-wide differentiation, confirmed against the whole overcollateralized pole. |
| **3 — Table stakes, never the headline** | MCP server, CLI, SDK, simulate-before-execute, zero-custody session keys. | Morpho and Base both shipped this. State it as competence, never as advantage. |

### 2.3 The Agent Score, repositioned

**Stop claiming to have invented the category. Claim the underwriting layer.**

The distinction that survives scrutiny:

- Everyone else is building **reputation for payments** — *this agent is who it claims
  and pays its bills.*
- Vanna is building **underwriting for credit** — *this agent can be trusted with 10×
  leverage and will not blow up the pool.*

Only the second requires a live margin account to generate. That is the defensible
claim, and it is narrow: *a credit score derived from an agent's behaviour inside a
live undercollateralized margin account, where the score determines the credit line.*

**Align publicly with ERC-8004 and KYA rather than competing with them.** Vanna
consumes agent identity and produces a credit decision. In a standardising market
that is a better, more defensible and more partnership-friendly position than a
proprietary score. It also converts three standards bodies from competitors into
distribution.

---

## 3. The blocker nobody has addressed **[INTERNAL — TIER E until fixed]**

File 10 §Battlecard 7 Q2 identifies a direct, unaddressed vulnerability:

> A 742-score, 214-day, $1.2M-volume, 47-liquidations-avoided profile is farmable by
> an adversary willing to spend time and capital. Vanna's docs and site say nothing
> about sybil resistance, cost-to-fake, or capital-weighting.

**This is the highest-priority item in this document, ahead of all messaging work.**

An agent credit score with no stated sybil resistance is not an underwriting product
— it is a leaderboard. The first serious technical reviewer will ask how it is faked,
and there is currently no answer. Worse: the agent-builder persona (P3) is described
in `05-audiences-personas-and-objections.md` as the highest-strategic ICP, and the
thing that kills the deal for them is vaporware. They will read the docs and check
GitHub.

**Sequence:** design the sybil resistance → document it → *then* make the design the
marketing. Cost-to-fake, capital-weighting and time-weighting are all legitimately
interesting content once they exist. Until they do, the Agent Score should be
described in future tense only and should not carry the strategic weight of the
positioning.

Two adjacent unresolved items from the same battlecard:

- **Liability when an agent causes a loss.** No jurisdiction has moved. The Risk
  Guardian executes defensive actions autonomously. **Legal review is required before
  any mainnet autonomy claim.**
- **Governance of agents that outgrow their operators.** Open across the field. Not
  Vanna's to solve, but do not claim to have solved it.

---

## 4. Per-competitor strategic posture **[PUBLISHABLE unless marked]**

| Competitor | Posture | The rule |
|---|---|---|
| **Gearbox** | Different job to be done | Never claim superiority. Concede security and scale openly — it buys credibility for the differentiation that follows. They extend credit to an identified institution to lever a yield position; Vanna extends credit to a pseudonymous trader or an agent to run a multi-leg hedged book. **Their clearest open flank is having no agent surface at all.** |
| **Hyperliquid** | Complementary, never opposed | The comparison that works is *funding source*, never *venue*. "We're not going to out-liquidity Hyperliquid" is the correct opening concession. Best long-term outcome is Vanna credit funding Hyperliquid positions. They are on Vanna's own logo wall. |
| **Morpho** | Adjacent primitive, honest concession | Concede the MCP work is good and the pattern is right. Then move immediately to what an agent can *do* with it: supply collateral, borrow less than it supplied. Useful, and not credit. **Monthly roadmap monitoring — highest-priority watch item.** |
| **Base MCP** | Distribution channel, not rival | It is plumbing, not credit — no lending book, no risk engine, no health factor. An agent using it must arrive funded. **Become a skill plugin inside it.** Plugins are writable from published markdown specs. This is the single cheapest distribution move available. |
| **Blend Capital** | Frenemy and partner | ~68% of Stellar DeFi, integrated on testnet. The Feb 2026 YieldBlox oracle-manipulation exploit (~$10.8M) is Vanna's most important risk data point — **use it to explain design choices, never to attack a partner. Engineering sign-off required before referencing it externally.** |
| **Aave and the overcollateralized pole** | Reference point, not rival | Confirms the no-kink rate curve as genuine category-wide differentiation. Safe to cite as a category baseline. |
| **Kojiru / Kite AI** | Direct on agent credit | Do not claim the category. Claim the underwriting layer. Watch whether Kojiru moves from scoring into lending. |

---

## 5. The Stellar reframe **[PUBLISHABLE]**

The old framing — *Stellar has DeFi liquidity* — does not survive contact with the
numbers. Stellar's entire DeFi TVL is ~$161M, less than half of Gearbox alone and
roughly 0.3% of DeFi lending deposits.

**The correct framing:**

> Stellar has RWAs, institutions and agentic payment rails — and no credit layer.

That is defensible and it is interesting: **$2.4B in RWAs across 65 issuances (#8
globally, #4 permissionless), $16M/day smart-contract volume (8× YoY), and both x402
and MPP live on mainnet with SDF a Premier member of the x402 Foundation.**

**[INTERNAL — TIER E]** Big-fish-small-pond holds as a launch strategy and fails as an
endgame. $20–30M TVL makes Vanna top-3 on Stellar; the same number is invisible on
Base. Plan the chain-expansion path now, and do not let external content imply that
Stellar is the permanent home.

---

## 6. The credibility gap that outranks messaging **[INTERNAL — TIER E]**

File 10 Q6 names it plainly: of the logo wall, only **Blend, Aquarius and Soroswap**
are live, all on Stellar. Hyperliquid, Uniswap, Morpho, Aerodrome, Avantis, Derive,
Aster and Katana are all on other chains and require either a Base/Arbitrum
deployment or a cross-chain path that does not exist.

> This is the largest single gap between Vanna's marketing and Vanna's product.

It directly determines whether "every market at once" survives scrutiny from a
technical prospect — and P3, the highest-strategic persona, is exactly the prospect
who checks. No amount of repositioning fixes this; only shipping does. Until then,
external content must use the approved reframe: *"Deep integrations with Blend,
Aquarius and Soroswap today, with a broader venue roadmap."*

Related and equally sobering: Gearbox took roughly **five years** to go from protocol
to infrastructure-others-build-on. Vanna's internal roadmap targets a first
third-party SDK integration at month 12. That is aggressive by a factor of several.

---

## 7. Messaging substitution table — what the pipeline consumes **[PUBLISHABLE]**

This extends the table in `08-facts-ledger-and-claim-safety.md` §4 with the
repositioning from this file. Content agents should treat both as one list.

| Stop saying ❌ | Start saying ✅ |
|---|---|
| "Vanna is MCP-native — the first protocol agents can call" | "Agents can pay. Agents can't borrow. Vanna is the credit line underneath." |
| "Our MCP server is the differentiator" | "MCP, CLI and SDK are how you reach it. Undercollateralized credit is what you reach." |
| "Nobody else is building agent credit scores" | "Everyone is building reputation for payments. We're building underwriting for credit — the score comes from behaviour inside a live margin account and it sets the line." |
| "Our unforkable data moat" | "A credit decision needs a margin account to generate. That's the part that can't be copied from outside." |
| "Better than Morpho for agents" | "Morpho gives agents access to a lending market. We give them a balance sheet." |
| "We compete with ERC-8004 / identity standards" | "We consume agent identity and produce a credit decision. Identity standards are upstream of us, not against us." |
| "Vanna replaces Hyperliquid" | "We're not going to out-liquidity Hyperliquid. Vanna is the funding source underneath the position." |
| "Stellar is where DeFi liquidity is going" | "Stellar has $2.4B in RWAs, institutions and live agentic payment rails — and no credit layer." |
| "15+ integrations across 6+ chains" | "Deep integrations with Blend, Aquarius and Soroswap today, with a broader venue roadmap." |
| "Our Agent Score underwrites agents" | "Vanna is building an Agent Score that turns on-chain behaviour into a credit line." (future tense — mandatory until §3 is fixed) |

---

## 8. Priority sequence

Ordered by what unblocks the most. Messaging work is **fourth**, deliberately.

1. **Sybil resistance for the Agent Score** — design, then document, then market.
   Until this exists the agent-credit narrative cannot carry weight, and §3 keeps the
   whole positioning in future tense.
2. **Build the capital-inefficiency number.** File 10 Q1 calls it "the single most
   valuable missing number in Vanna's arsenal." Take a real delta-neutral carry (BTC
   spot long + BTC perp short + idle stablecoin), price it on Hyperliquid + a spot DEX
   + a lending market, and compute capital required versus the same book on unified
   portfolio margin. **A credible reproducible number here carries more weight than
   any messaging work in this document.**
3. **Become a Base MCP skill plugin.** Cheapest distribution available; plugins are
   writable from published markdown specs. Converts the strongest agent-front-door
   competitor into a channel.
4. **Reposition all agent-facing content** per §2 and §7.
5. **Open an ERC-8004 / KYA alignment conversation.** Converts standards bodies from
   competitors into distribution.
6. **Legal review on Risk Guardian autonomy and liability** before any mainnet
   autonomy claim.

---

## 9. Watch triggers — what forces a re-plan

Re-open this file if any of these occur:

| Trigger | Consequence |
|---|---|
| **Morpho ships a leveraged or looping product with an agent surface** | The core differentiation narrows sharply. Highest-probability threat. Monitor monthly. |
| **Base MCP adds a Gearbox plugin or any leverage plugin** | The agent front door gains credit without Vanna. |
| **Kojiru moves from scoring into lending** | Direct collision on the underwriting claim. |
| **Gearbox ships an MCP server or agent tooling** | Closes the clearest open flank, from a position of 30+ audits and $400M TVL. |
| **A named competitor announces undercollateralized credit for agents** | The tier-1 claim in §2.2 is gone. Escalate immediately. |
| **Any Stellar-native protocol ships portfolio margin** | Home-turf advantage lost. |

---

## 10. Standing rules for content agents

1. **Never lead with MCP.** It is competence, not advantage.
2. **Never claim the agent-credit-score category.** Claim the underwriting layer.
3. **Agent Score stays in future tense** until sybil resistance is designed and
   documented.
4. **Never claim superiority over any named competitor** — this predates and outranks
   this file (`08` §3.7).
5. **Never position against Hyperliquid.** Funding source, never venue.
6. **Never attack Blend.** Partner on Stellar. The exploit explains design choices; it
   is not ammunition.
7. **Never imply the logo wall is live integrations.** Three are live: Blend, Aquarius,
   Soroswap.
8. **Never publish §3, §5 (marked block), or §6.** Tier E.
