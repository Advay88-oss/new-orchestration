# GTM Engine — Full Launch Campaign Planning & Execution

**One feature.** Point it at a company (an OKF tenant), and it researches how the
competition actually launched and grew, then produces a complete,
platform-by-platform launch campaign — strategy, content scripts, premium
on-brand visuals and video, and incentive campaigns — every claim gated for
safety, ending in a human-reviewed, executable plan.

Status legend used throughout: **[BUILT]** exists and is proven this session ·
**[PARTIAL]** substrate exists, needs extension · **[NEW]** to build.

This spec sits on top of everything already built:
[OKF-PACKS.md](OKF-PACKS.md) (per-tenant brand/facts/rules),
[ARCHITECTURE.md](ARCHITECTURE.md) (the content pipeline),
[VALIDATION-HARNESS.md](VALIDATION-HARNESS.md) (how its output is graded),
[VIDEO-PIPELINE research](#) (the video layer), and the OKRs in
[OKRS.md](OKRS.md).

---

## The one command

```
/gtm-launch  --tenant auri  --budget 25000  --launch-date 2026-10-01
             --platforms x,linkedin,reddit,producthunt,instagram,email
```

Produces `tenant/{id}/launch/` — a dated, versioned campaign folder containing
the strategy, the per-platform plans, the content library (copy + visuals +
video), the incentive-campaign designs, the calendar, and the measurement plan.
Nothing in it is published until a human approves it on Telegram.

Everything is **grounded in two sources and nothing else**: the tenant's OKF
bundle (who they are, what they may claim) and live competitor research (what
actually worked). No step invents a fact — the same discipline that made the
Auri post fully source-traceable.

---

## A-to-Z flow

```
 ┌─ 0. GROUND ────────────────────────────────────────────────────────────┐
 │  Load OKF bundle: constraint, facts tiers, arcs, brand, ICP, competitors │  [BUILT]
 └────────────────────────────────────┬────────────────────────────────────┘
                                       ▼
 ┌─ 1. COMPETITOR GTM INTELLIGENCE (research swarm, one agent per competitor)┐
 │  How they launched · their posts & formats · what performed · paid/organic│  [PARTIAL]
 │  · PR & partnerships · funnel: how they ATTRACTED and CONVERTED · their    │
 │  incentive/referral mechanics · site evolution (wayback)                   │
 │  → per-competitor GTM dossier, every claim cited                           │
 └────────────────────────────────────┬────────────────────────────────────┘
                                       ▼
 ┌─ 2. TEARDOWN / PATTERN SYNTHESIS ──────────────────────────────────────┐
 │  Across competitors: the launch grammar, the channels that converted,    │  [NEW]
 │  the incentive mechanics that drove growth, what to copy vs avoid         │
 └────────────────────────────────────┬────────────────────────────────────┘
                                       ▼
 ┌─ 3. GTM STRATEGY ARCHITECT ────────────────────────────────────────────┐
 │  Positioning (from arcs) · ICP & segments · channel mix w/ rationale ·   │  [NEW]
 │  phase structure (pre → launch → post) · timeline & budget SCALED to     │
 │  this tenant's real resources · KPIs per phase                            │
 └────────────────────────────────────┬────────────────────────────────────┘
                                       ▼
 ┌─ 4. INCENTIVE CAMPAIGN DESIGNER ───────────────────────────────────────┐
 │  Referral / waitlist / points / ambassador / discount / gift mechanics,  │  [NEW]
 │  chosen from what competitors did AND what is legal for this tenant's     │
 │  category (Auri=financial, Acme=clinical, Vanna=testnet-no-token)         │
 └────────────────────────────────────┬────────────────────────────────────┘
                                       ▼
 ┌─ 5. PER-PLATFORM CONTENT ENGINE (the existing pipeline, fanned per platform)┐
 │  For each platform: strategy → calendar → scripts (3-arc debate → judge)  │  [PARTIAL]
 │  → premium visuals (render_visual, per aspect ratio) → video (Remotion)   │
 └────────────────────────────────────┬────────────────────────────────────┘
                                       ▼
 ┌─ 6. CLAIM-SAFETY GATE (every asset, per-tenant OKF rules) ──────────────┐  [BUILT]
 └────────────────────────────────────┬────────────────────────────────────┘
                                       ▼
 ┌─ 7. ASSEMBLE LAUNCH PLAN ──────────────────────────────────────────────┐
 │  One executable doc + asset library + calendar + owners + measurement     │  [NEW]
 └────────────────────────────────────┬────────────────────────────────────┘
                                       ▼
 ┌─ 8. HUMAN REVIEW (Telegram) → EXECUTE (OpenCLI per platform) → MEASURE ──┐  [PARTIAL]
 └──────────────────────────────────────────────────────────────────────────┘
```

---

## Stage detail

### 0. Ground — from the OKF bundle  [BUILT]

Reads `okf-{tenant}/`: the overriding constraint, facts tiers (A/B/C/retired),
the three narrative arcs, brand palette, ICP, competitor list, research config.
This is the tenant's identity and its claim boundaries. Already working for
Vanna, Acme, Auri.

### 1. Competitor GTM Intelligence  [PARTIAL — connectors exist, the swarm is new]

One research agent per competitor (from `okf/competitors/`), each producing a
**GTM dossier** with every claim carrying a citation (so V2 fact-check can grade
it). What each dossier must answer:

| Question | How | Connector |
|---|---|---|
| How did they launch? sequence, date, channel | site + wayback + press + Product Hunt | WebFetch, `wayback`, `opencli producthunt` |
| What do they post? formats, cadence, hooks | scrape their socials | `opencli twitter/linkedin/reddit`, Agent-Reach |
| What actually performed? | engagement per post | `opencli twitter search` (likes/RT/replies) |
| Paid vs organic vs PR? | ads library, mentions | WebSearch, ad libraries |
| How did they ATTRACT? (top of funnel) | channel mix, content themes | synthesis of above |
| How did they CONVERT? (activation) | onboarding, offers, funnels | site walk-through (browser), pricing pages |
| Incentives that drove growth | referral/waitlist/points programs | site, docs, community |
| Site & positioning evolution | what claims they added/removed | `wayback` diff |

**Honest note:** the connectors are [BUILT] and proven (OpenCLI twitter/reddit/
producthunt, WebFetch, the in-app browser). The **research agent that runs 15+
tool calls per competitor and assembles a cited dossier is [NEW]** — this is the
V0-bootstrapper's sibling and the single biggest new build.

**Guardrail:** collect competitors' *strategy and format*, never copy their
actual creative assets — that is a copyright/impersonation line. The engine
learns the grammar and the quality bar, then expresses it in the tenant's own
brand.

### 2. Teardown / Pattern Synthesis  [NEW]

Cross-competitor analysis — the part no single dossier reveals (this is exactly
what V3 Generalization guards): the shared **launch grammar**, the channel mix
that actually converted, the incentive mechanics that moved the needle, and an
explicit **copy / adapt / avoid** table. Output is a synthesis brief that feeds
the strategy architect.

### 3. GTM Strategy Architect  [NEW]

Turns dossiers + synthesis + OKF into the strategy:

- **Positioning** — from the tenant's arcs, not generic.
- **ICP & segments** — from the OKF bundle's audience + competitor overlap.
- **Channel mix with rationale** — B2B tenant ≠ D2C tenant ≠ local business. A
  plan that recommends the same channels for Auri (D2C fintech) and a B2B SaaS
  is a template failure (V3 catches it).
- **Phase structure** — pre-launch (waitlist/teaser) → launch (burst) →
  post-launch (retention/referral).
- **Timeline & budget SCALED to the tenant's real resources** — the `--budget`
  and the OKF constraints are hard inputs. A $500 local business must not get a
  $50k plan (V3 constraint-responsiveness = the decisive scaling test).
- **KPIs per phase** — tied to [OKRS.md](OKRS.md); every phase gets a
  measurable target.

### 4. Incentive Campaign Designer  [NEW]

A dedicated stage because incentives are where growth and legal risk collide.

- **Research input:** what incentive mechanics competitors used (from stage 1) —
  referral bonuses, waitlist priority, points, ambassador programs, cashback,
  gifting, early-access.
- **Design:** per-platform incentive campaigns matched to the tenant.
- **Legal/claim discipline (via the OKF gate):**
  - **Auri** (financial, gold + borrowing): no "guaranteed" rewards, no
    return-implying incentives, referral terms must disclose risk — the Auri
    rule set already blocks the dangerous framings.
  - **Vanna** (testnet): **no token/airdrop/points incentives** — the gate hard-
    blocks these (`P3-token`). Incentives must be non-financial (early access,
    status, community).
  - **Acme** (clinical): no patient inducements; incentives target clinics, not
    care decisions.
- Every incentive design passes the gate before it reaches the plan.

### 5. Per-Platform Content Engine  [PARTIAL — pipeline built, per-platform fan-out new]

The existing content pipeline (trend-scout → 3-arc strategist debate →
editorial-judge → visual) **[BUILT]**, run once per platform with
platform-specific parameters:

| Platform | Format focus | Visual | Notes |
|---|---|---|---|
| X / Twitter | thread + single hooks | 1080² card + short video | [BUILT] end-to-end (published this session) |
| LinkedIn | long-form, professional | doc-style carousel | [NEW] format |
| Reddit | native, non-promo, value-first | minimal | [NEW] — tone discipline critical |
| Product Hunt | launch-day kit: tagline, gallery, first comment | gallery images | [NEW] |
| Instagram / TikTok | vertical video, hooks | 9:16 video (Remotion) | [NEW] video |
| YouTube | launch/intro video | 16:9 video (Remotion + Veo B-roll) | [NEW] video |
| Email | sequence (teaser→launch→follow-up) | header images | [NEW] |
| Blog / SEO | pillar + launch post | og-images | [NEW] |

- **Scripts** — the 3-arc debate writes copy per platform, editorial-judge picks,
  the gate clears it. Same mechanism, per-platform prompts.
- **Premium visuals** — `render_visual.py` **[BUILT]**, extended to per-platform
  aspect ratios (1:1, 9:16, 16:9) **[NEW]**, always in the tenant's OKF palette.
- **Video** — Remotion (branded spine) + Veo 3.1 via the existing Vertex proxy
  (B-roll) + ElevenLabs (VO) **[NEW]** — see the video-pipeline research; reuses
  headless Chrome and the spend proxy you already run.

### 6. Claim-Safety Gate  [BUILT]

Every asset — every post, script, incentive, email — passes
`claim_safety_gate.py` against the tenant's OKF rules. Proven this session:
`rules_source: okf`, per-tenant (32 Vanna rules, 6 Auri rules, 6 Acme rules).

### 7. Assemble Launch Plan  [NEW]

One executable deliverable:
- **The plan** — strategy, phases, timeline, budget, channel-by-channel.
- **The content library** — every script + visual + video, gated, ready.
- **The calendar** — dated, per platform, with the incentive campaigns slotted.
- **Owners & dependencies** — what a human does vs what the engine auto-runs.
- **The measurement plan** — KPIs, instrumentation, attribution per channel.

### 8. Human Review → Execute → Measure  [PARTIAL]

- **Review** — the plan goes to Telegram for approval **[BUILT]** (the gate you
  just used). Big plans get section-by-section sign-off.
- **Execute** — on approval, publish per platform via OpenCLI connectors
  **[PARTIAL]** — Twitter proven; other platforms per connector availability.
- **Measure** — pull engagement/conversion per channel, feed
  [OKRS.md](OKRS.md). Needs the `run_id` instrumentation (the open gap).

---

## How the Validation Harness fits

This engine is precisely the "engine" that [VALIDATION-HARNESS.md](VALIDATION-HARNESS.md)
grades. Before any launch plan is trusted:

- **V2** — every competitor-dossier claim must cite a resolving, supporting source.
- **V3** — plans for different tenants must genuinely diverge (no template).
- **V4** — content must be attributable to the right brand voice.
- **V5** — the decisive one: a plan built *without* the competitor research must
  score materially worse than one *with* it — proving the research is
  load-bearing, not decorative. This is your original concern, measured.
- **V6** — no competitor's or other tenant's data leaks across.

A launch plan that fails V5 is a beautiful plan that ignored the research — the
exact failure this whole system is built to prevent.

---

## Implementation plan

Ordered by dependency. Effort is rough, for one engineer + the model backend.

| Phase | Build | Status leaned on | New work |
|---|---|---|---|
| **P0. Restore backend** | Gemini ADC or a formal Claude-as-brain protocol | — | nothing runs controlled without this |
| **P1. Competitor dossier agent** | the 15+ tool-call researcher, one per competitor, cited output | connectors [BUILT] | the agent + citation schema [NEW] |
| **P2. Teardown + Strategy architect** | synthesis + the plan generator | OKF [BUILT] | two agents [NEW] |
| **P3. Incentive designer** | per-platform incentive campaigns, gate-checked | gate [BUILT] | one agent + legal-discipline rules per tenant [NEW] |
| **P4. Per-platform fan-out** | LinkedIn/Reddit/PH/email/blog formats | pipeline [BUILT] | per-platform prompts + aspect ratios [NEW] |
| **P5. Video layer** | Remotion spine + Veo B-roll + ElevenLabs VO | Chrome, Vertex proxy [BUILT] | Remotion project reading OKF palette [NEW] |
| **P6. Plan assembler + calendar** | the single executable deliverable | — | [NEW] |
| **P7. Execute connectors** | publish per platform | Twitter [BUILT] | per-platform OpenCLI [PARTIAL] |
| **P8. Measurement** | KPI pull + attribution | — | needs `run_id` [NEW] |
| **P9. Validate** | run V2–V6 on the output | harness spec [BUILT] | wire the graders [NEW] |

**Fastest first vertical (recommended):** P0 → P1 (competitors for ONE tenant,
e.g. Auri) → P2 → P4 for **one platform** (X, already proven) → P6 → P8. That is
a real, end-to-end, single-platform launch plan grounded in real competitor
research — the smallest thing that proves the whole loop. Then widen to more
platforms and the video layer.

---

## Honest prerequisites and gaps

1. **Model backend is down.** Gemini/Vertex ADC expired; the research swarm needs
   it (or a formalized Claude-as-brain protocol). Nothing at scale runs first.
2. **The competitor-research agent is the core new build** — everything
   downstream depends on real, cited dossiers. If this hallucinates, V2 catches
   it, but it must be built to cite by construction.
3. **Per-claim citations** are not yet emitted by the content pipeline — required
   for V2 and for trust. Schema change needed.
4. **Video layer is researched, not built.** Remotion + Veo + ElevenLabs is the
   plan; it reuses your Chrome + Vertex proxy but the Remotion project is new.
5. **Incentive legality needs a human.** The engine designs and gates incentives,
   but a financial (Auri) or clinical (Acme) incentive must have human/legal
   sign-off before running — same hard rule as `pb_product_truth`.
6. **Isolation is by convention.** For multi-tenant GTM at scale, isolation must
   move to the tool layer (V6's requirement).
7. **Measurement needs `run_id`.** Without it, "did the launch work?" can't be
   answered per channel — the top instrumentation gap in [OKRS.md](OKRS.md).

---

## What this becomes, in one line

> A tenant's competitors, reverse-engineered into a launch playbook, expressed in
> the tenant's own brand across every platform, with the visuals and video to
> ship it — and a gate that guarantees none of it says something the company
> can't stand behind.
