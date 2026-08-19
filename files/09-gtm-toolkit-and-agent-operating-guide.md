# 09 — GTM Toolkit Inventory & Agent Operating Guide

---

## PART A — THE MARKETING SKILL LIBRARY

`marketing.zip` contains **299 files / ~100 skills** across 11 domains. It is a **generic** marketing toolkit — there is **zero Vanna-specific content in it** (a grep for "vanna" returns nothing). Its `brand/brand-guidelines` reference describes **Anthropic's** brand identity, not Vanna's.

> **Wiring rule:** these skills are the *method*. This knowledge base is the *substance*. Every skill invocation must be fed the relevant KB file, and `04-brand-voice-and-message-library.md` overrides the pack's brand-guidelines skill entirely for anything Vanna.

### Full inventory by domain

| Domain | Skills |
|---|---|
| **competitive** (10) | competitive-intel · competitive-landscape · competitive-battlecard · competitor-alternatives · competitor-content-analysis · competitor-discovery · competitor-keyword-analysis · competitor-landscape · competitor-site-analysis · competitors-analysis |
| **strategy** (16) | acquisition-channel-advisor · beachhead-segment · blue-ocean-strategy · channel-discovery · contagious · crossing-the-chasm · hundred-million-offers · influence-psychology · intl-expansion · launch-strategy · ma-playbook · marketing-demand-acquisition · marketing-ideas · marketing-ops · marketing-psychology · marketing-strategy-pmm |
| **content** (7) | content-creator · content-humanizer · content-production · content-repurposer · content-strategy · copy-editing · copywriting |
| **social** (9) | community-discovery · influencer-discovery · referral-program · reply-writer · social-content · social-media-analyzer · social-media-manager · social-post-writer · x-twitter-growth |
| **seo** (19) | ai-seo · keyword-research · programmatic-seo · schema-markup · search-page-audit · seo-audit · site-architecture · seo-seo-{audit, competitor-pages, content, geo, hreflang, images, page, plan, programmatic, schema, sitemap, technical} |
| **cro** (11) | ab-test-analysis · ab-test-setup · conversion-audit · cro-methodology · form-cro · improve-retention · onboarding-cro · page-cro · paywall-upgrade-cro · popup-cro · signup-flow-cro |
| **ads** (5) | ad-angles · ad-campaign-analyzer · ad-creative · campaign-analytics · paid-ads |
| **reports** (15) | mktg-market-{ads, audit, brand, competitors, copy, emails, funnel, landing, launch, proposal, report, report-pdf, seo, social} · mktg-lead-magnets |
| **brand** (2) | brand-agency (HTML render templates for Instagram/Twitter/TikTok/Pinterest/YouTube + `render-templates.js`) · brand-guidelines |
| **email** (2) | cold-email · email-sequence |
| **analytics** (2) | analytics-tracking · cohort-analysis |

### High-leverage subset for Vanna right now (pre-mainnet)

| Priority | Skill | Feed it | Why |
|---|---|---|---|
| 1 | `competitive/competitive-intel` + `competitive-battlecard` | `06` + this file's battlecard schema | Next research pass; the battlecard template is already aligned |
| 2 | `strategy/beachhead-segment` | `05` | Formalise agent-builders as the beachhead |
| 3 | `strategy/crossing-the-chasm` | `05` + `08` | Correct framework for a pre-mainnet infra protocol |
| 4 | `social/x-twitter-growth` (incl. `competitor_analyzer.py`, `content_planner.py`, `tweet_composer.py`, `growth_tracker.py`, `profile_auditor.py`) | `04` + `08` | Building from ~348 followers; scripts are directly usable |
| 5 | `content/content-strategy` + `content/copywriting` | `04` + `02` | Technical education is Vanna's ownable channel |
| 6 | `seo/keyword-research` + `programmatic-seo` | `04` §13 | Own the agentic-credit and Stellar-DeFi clusters before anyone |
| 7 | `competitive/competitor-alternatives` (has `comparison_matrix_builder.py`) | `06` | "X vs Vanna" pages — but **jobs-to-be-done framing, never superiority** |
| 8 | `brand/brand-agency` | `04` Part B | Social templates — must be re-skinned to Vanna tokens, not Anthropic's |
| 9 | `content/content-humanizer` (has `ai-tells-checklist.md`) | `04` | Crypto audiences detect AI copy instantly and punish it |
| 10 | `email/cold-email` + `email-sequence` | `05` | 40K subscriber list is a real asset — reactivate it |
| 11 | `social/community-discovery` | `05` §5 | Find the agent-builder and Stellar communities |
| 12 | `analytics/analytics-tracking` + `cohort-analysis` | — | Instrument before scaling |

### Deprioritise until mainnet + audits
`ads/*` (don't pay to acquire users who can't deposit) · `cro/paywall-upgrade-cro` · `cro/signup-flow-cro` beyond testnet onboarding · `strategy/intl-expansion` · `strategy/ma-playbook` · institutional-outbound sequences.

---

## PART B — AGENT OPERATING GUIDE

## 1. Standing rules for the GTM agent

1. **Claim safety is a gate, not a filter.** Run `08`'s pre-publication checklist on every asset. If a claim can't be traced to Tier A or labelled as illustrative, it does not ship.
2. **Docs beat the marketing site on technical claims. The marketing site beats internal research on messaging.** When they conflict, resolve in that order.
3. **Named venues beat counts.** "Blend, Aquarius and Soroswap" is stronger and safer than "15+ integrations".
4. **Mechanism over adjective.** Vanna's advantage is that its mechanism is genuinely interesting. Explaining *why* 10× falls out of a 1.1× floor beats calling it powerful.
5. **One narrative arc per asset.** Capital efficiency, risk relief, or agentic credit. Never all three.
6. **Two-beat rhythm.** The brand's sentence shape is contrast + reveal. Match it.
7. **Push toward evidence, not ambition.** Testnet artefacts, working demos, published maths, open references. Vision statements do not move a pre-mainnet protocol.
8. **Cite external market data by source.** Galaxy, Chainalysis, Stellar. It borrows credibility Vanna hasn't earned yet.
9. **Escalate to a human** whenever: a claim sits in Tier F · a competitor's numbers are needed and unverified · anything touches security, audits, token, or regulation · a partnership or logo would be characterised as a customer.

## 2. Content patterns that work for this brand

**The contrast open.** Name the forced choice, then dissolve it. *"DeFi makes you choose. Vanna refuses."*

**The mechanism thread.** Pick one piece of the architecture and explain it properly. Candidates, each a strong standalone piece:
- Why 10× isn't a parameter — the self-collateralization maths
- Why kinked interest-rate curves are worse than smooth polynomials
- How you value a position that lives in another protocol as collateral
- Why 1.1× and not 1.0× — slippage, oracle lag, and the cost of a liquidation
- What a credit layer for agents actually has to do that a wallet doesn't
- Why three protocols with the same idea died, and the one thing the survivor had

**The 3am story.** The Risk Guardian narrative. Highest emotional resonance Vanna owns. Reusable as thread, video, ad, landing hero.

**The plug-in frame.** "You plug in collateral / a product / liquidity / autonomy." Elegant, scales to four audiences from one structure.

**The empty-layer diagram.** Identity ✅ · Communication ✅ · Wallets ✅ · Orchestration ✅ · Settlement ✅ · **Credit ⬜**. Single most persuasive visual Vanna has for the agentic thesis.

**The graveyard post.** Three protocols, three deaths, one survivor, one common factor. Genuinely useful to the whole category, positions Vanna as the party that did the homework, and is entirely defensible because it's about *others*.

## 3. Content patterns to avoid

- Generic "the future of finance is on-chain" thought leadership. Nobody reads it; it signals having nothing specific to say.
- Feature lists without a mechanism.
- Anything that reads like it was written by an AI without a point of view — run `content-humanizer`.
- Comparison content that punches at a bigger incumbent.
- Announcements of things that aren't shipped.
- Threads that end with a token tease.

## 4. Asset briefing template

When commissioning any asset, fill this in first:

```
ASSET: [type]
NARRATIVE ARC: capital efficiency | risk relief | agentic credit   (pick one)
PERSONA: P1 trader | P2 farmer | P3 agent builder | P4 business | P5 institution | P6 LP
FUNNEL STAGE: awareness | education | consideration | activation (testnet)
CORE CLAIM: [one sentence]
CLAIM TIER: A | B | C(labelled) | D(future tense)
PROOF POINT: [from 04 §10 proof bank]
CTA: Launch App | Read the docs | Join Discord | View Strategies | Start Earning
CHANNEL: X | blog | docs | landing | email | Discord | dev community
REQUIRED DISCLOSURES: [testnet status / illustrative label / protocol risk]
KB FILES TO LOAD: [list]
BRAND TOKENS: Plus Jakarta Sans; palette + spacing/radius from 04 Part B
```

## 5. Standing KPIs to instrument (pre-mainnet)

Because there is no TVL to report, the agent should optimise and report against **leading indicators**:

| Category | Metric |
|---|---|
| Developer pull | Docs sessions · unique visitors to `/developers/*` · SDK install attempts · MCP server registrations · GitHub org followers/stars |
| Testnet activity | Margin accounts created · testnet borrows · Farm/Lite Mode uses · distinct wallets |
| Attention | X followers, impressions, profile clicks · thread saves/bookmarks · Discord joins and active members |
| Content | Organic sessions on the agentic-credit and Stellar-DeFi keyword clusters · backlinks from ecosystem/research sites · mentions in agent-framework communities |
| Pipeline | Businesses/institutions in nurture · partner conversations · ecosystem co-marketing slots |
| List | 40K email list reactivation rate, open rate, click-through to docs |

**Explicitly not KPIs yet:** TVL, revenue, borrow volume, paid CAC.

## 6. First-90-days sequence (recommendation)

**Days 1–30 — Foundation**
Complete the competitor research pass (`06` §5 schema). Audit and rebuild the X profile and pinned content. Publish the first three mechanism threads. Fix the LP-content gap. Lock the keyword map and claim the agentic-credit cluster.

**Days 31–60 — Developer beachhead**
Ship a developer-facing quickstart narrative ("register mcp.vanna.finance, borrow on testnet in ten minutes"). Get listed in every MCP registry and directory. Publish the graveyard post. Begin Stellar-ecosystem co-marketing with Blend/Aquarius/Soroswap. Reactivate the email list with a technical, non-promotional sequence.

**Days 61–90 — Compounding**
Publish the "X vs Vanna" comparison set with jobs-to-be-done framing. Land the first third-party developer building on the SDK — this is the single most valuable milestone available pre-mainnet, because it is exactly what all three failed protocols never achieved. Stand up cohort tracking. Prepare the mainnet + audit announcement architecture so it's ready the moment security docs land.

## 7. The one-line brief the agent should never forget

> **Vanna is the credit layer for agentic finance — but it is pre-mainnet, unaudited, and running on Stellar testnet with Blend, Aquarius and Soroswap.** Sell the architecture and the thesis. Do not sell a product that isn't live. Everything else in this knowledge base is elaboration on that sentence.
