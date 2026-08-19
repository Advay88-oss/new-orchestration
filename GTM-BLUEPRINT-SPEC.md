# The AI GTM Department — Master Blueprint

The top-level spec. Everything else sits under this: the content pipeline
([ARCHITECTURE.md](ARCHITECTURE.md)), the multi-tenant substrate
([OKF-PACKS.md](OKF-PACKS.md)), the execution engine
([GTM-ENGINE-SPEC.md](GTM-ENGINE-SPEC.md)), the video arm
([VIDEO-PRODUCTION-SPEC.md](VIDEO-PRODUCTION-SPEC.md)), the learning loop
([learn.py](pipeline/scripts/learn.py)), and how any of it is trusted
([VALIDATION-HARNESS.md](VALIDATION-HARNESS.md)).

**What it is.** Not a content generator. An AI system that takes a product from
market research all the way to a measured, optimising launch — answering not
"what should we post?" but *"what should we launch, to whom, why, where, when,
with what message, creative, offer and budget, through which channels, executed
how, measured how, and what did we learn?"*

```
Market Research → Competitive Intelligence → Positioning → GTM Strategy →
Launch Strategy → Content Strategy → Creative Production → Campaign Execution →
Acquisition → Conversion → Analytics → Learning → Optimization
```

---

## Read this before the section map: the honest scale

This is a **multi-quarter build**, and most of it is **[NEW]**. That is not a
reason to shrink the vision — it is a reason to sequence it and to be precise
about what already exists so the new work compounds instead of restarting.

What is genuinely **built and proven this session**, that the rest stands on:

- **Per-tenant knowledge as data** — OKF bundles (Vanna, Auri) holding
  constraint, facts tiers, arcs, brand, ICP, competitors, positioning.
- **A deterministic claim-safety gate** — every asset gated per tenant; the thing
  that lets this run at machine speed without shipping false claims.
- **Competitor intelligence** — 21 cited Auri competitor dossiers + a threat
  radar; a JSON store; a tenant-aware trend scout pulling live market signals.
- **On-brand creative rendering** — per-tenant palette + logo → 1080² cards,
  deterministically (the model for all creative: code renders brand, AI renders
  texture).
- **A learning loop** — measure → analyse → INSIGHTS → injected back into
  generation, cross-company at the feature level, on a schedule.
- **A human review gate** — Telegram approval before anything ships.

What is **not yet real**, and gates large parts of this blueprint:

- **Publishing is the bottleneck.** Browser-automation posting to X is blocked by
  X (proven this session). Until a real publish path exists (platform APIs), the
  Execution → Acquisition → live-Analytics half of the loop cannot close.
- **The model backend** (Gemini/Vertex ADC) is down; the autonomous swarm runs
  only with Claude-as-brain today.
- **No live performance data** flows in yet (needs publishing + attribution +
  `run_id`).

Everything below is mapped against this reality, honestly.

---

## Section-by-section status (A–R)

Status: **[BUILT]** proven · **[PARTIAL]** substrate exists · **[NEW]** to build.
"Artifact" points at what already exists to build on.

| § | Capability | Status | Artifact to build on |
|---|---|---|---|
| **A** | Competitor market intelligence (per-competitor profiles) | **[PARTIAL]** | 21 Auri dossiers in `okf-auri/competitors/`; `competitors.json` |
| A | Launch **timeline** reconstruction (T-30 → post-launch) | **[NEW]** | dossiers hold the facts; the timeline agent is new |
| **B** | Competitor content intelligence across platforms | **[PARTIAL]** | trend scout (X/Reddit/News); other platforms new |
| **C** | Acquisition & conversion intelligence (funnel map) | **[NEW]** | dossiers note incentives; funnel-mapping is new |
| **D** | Competitive **creative** intelligence (video teardowns) | **[NEW]** | [VIDEO-PRODUCTION-SPEC.md](VIDEO-PRODUCTION-SPEC.md) Stage 1 |
| **E** | Market & audience intelligence + ICP | **[PARTIAL]** | ICP lives in OKF bundles; live market research new |
| **F** | Positioning engine (white-space finder) | **[PARTIAL]** | arcs + positioning directives in bundles; auto white-space new |
| **G** | Full GTM strategy generation | **[NEW]** | [GTM-ENGINE-SPEC.md](GTM-ENGINE-SPEC.md) Stage 3 |
| **H** | Full launch campaign (pre/launch/post) | **[NEW]** | GTM-ENGINE Stage 5 |
| **I** | Platform-native content engine | **[PARTIAL]** | X proven end-to-end; other platforms new formats |
| **J** | Automated script writing (all formats) | **[PARTIAL]** | 3-arc debate + gate writes copy; per-format new |
| **K** | Premium creative & visual generation | **[PARTIAL]** | cards [BUILT]; video [NEW] per VIDEO spec |
| **L** | Incentive & promotion intelligence + impact estimate | **[NEW]** | GTM-ENGINE Stage 4 (incentive designer) |
| **M** | Campaign implementation plan (the 12-field table) | **[NEW]** | — |
| **N** | Execution through connectors | **[PARTIAL]** | Telegram [BUILT]; publishing **blocked** (see bottleneck) |
| **O** | Performance & attribution engine | **[PARTIAL]** | `performance_tracker.py` exists; needs live data + `run_id` |
| **P** | Automatic experimentation (A/B) | **[NEW]** | learning loop is the substrate |
| **Q** | Self-improving GTM knowledge base | **[PARTIAL]** | `learn.py` + `INSIGHTS.md` (feature-level, cross-company) |
| **R** | The 33-part GTM blueprint (final output) | **[NEW]** | assembles A–Q |

**The pattern:** intelligence and creative substrate is largely built; the
*strategy synthesis*, *cross-platform expansion*, *video*, and *closed-loop
execution* are the new work — and execution is gated on publishing.

---

## The final output (R): the 33-part blueprint as a real artifact

Not a document that lives in a chat. Per tenant, per launch, an OKF-native
folder — versioned, gated, reviewable — so it is data the engine reads and
improves, not prose it forgets:

```
okf-{tenant}/launches/{launch-id}/
  00-blueprint.md          index of all 33 parts, with status per part
  01-market-research.md         09-channel-strategy.md
  02-competitor-intel.md        10-launch-timeline.md
  03-competitor-launches.md     11..13 pre/launch/post strategy
  04-customer-research.md        14-content-calendar.md
  05-icp.md                      15-scripts/ (per platform, per funnel stage)
  06-positioning.md              16-creative-concepts/  17-video-scripts/
  07-messaging.md                18-storyboards/  19-visual-production/
  08-gtm-strategy.md             20-paid  21-incentive  22-influencer …
  …                              27-funnel 28-budget 29-experiments
                                 30-measurement 31-analysis 32-optimisation 33-learnings
```

Every content/creative artifact carries the same tag — **Audience + Funnel Stage
+ Campaign Objective + CTA** — so nothing is "random content" (§J's requirement),
and so §O attribution and §Q learning can group by those dimensions. Every claim
in it traces to the tenant's facts ledger and passes the gate (§sign-off on
`pb_product_truth` stays mandatory, same hard rule as the tenant bootstrapper).

---

## The closed loop (N → O → P → Q) — where this becomes a system, not a report

```
 Research → Claude (intel+strategy) → Content/Creative → Publish → Analytics
     ▲                                                                  │
     └──────────────── Optimisation ◄── Learning ◄── Claude analysis ◄──┘
```

This is the part already partially real: `learn.py` aggregates performance +
market signal into `INSIGHTS.md`, which is injected into the next generation.
Extending it to the full GTM loop means:

- **§O attribution**: tag every artifact with campaign/objective/audience/funnel;
  pull platform metrics (impressions → CAC → LTV where data allows); join to
  outcomes. Needs a `run_id`/campaign_id (the top instrumentation gap in
  [OKRS.md](OKRS.md)) and **working publishing** to have anything to measure.
- **§P experimentation**: the loop already biases toward what performs; formalise
  it into controlled A/B (hook, creative, offer, audience, format) with holdouts.
- **§Q knowledge base**: `learn.py`'s feature-level patterns are exactly this —
  cross-company, isolation-safe (V6). Extend the feature set to campaign/offer/
  funnel dimensions so it learns "for this audience, demo videos beat brand
  videos" rather than only hook/theme.

**Isolation caveat (V6):** the knowledge base shares *patterns* across companies
("B2B responds to ROI-led over feature-led"), never a tenant's proprietary
facts. This is enforced by keeping the knowledge base feature-level, as the
learning loop already does.

---

## What gates the whole thing (fix these first, in order)

1. **Publishing.** No execution, no acquisition, no live analytics until content
   can actually go live. Browser automation is confirmed blocked by X — the path
   is platform APIs (X, LinkedIn, YouTube, Meta) or manual. **This is the single
   biggest blocker; it gates §N, §O, §P, §Q's live half.**
2. **Model backend.** Restore Gemini/Vertex ADC, or formalise Claude-as-brain, so
   the intelligence/strategy agents run at scale, controlled and repeatable.
3. **Instrumentation (`run_id` / campaign_id).** Without it, "did it work / why"
   (§O) is unanswerable. Cheapest high-leverage fix.
4. **Attribution connectors.** Platform analytics APIs feed §O; without them
   performance is guesswork.

Until 1–3 exist, this engine can produce world-class **plans** (A–M, R) but cannot
**close the loop** (N–Q). That is the honest ceiling of the current state, and it
is worth stating before anyone builds on top.

---

## Build sequence (dependency-ordered, reusing what exists)

Each step compounds on the last; none restarts.

1. **Unblock publishing** (platform APIs) + **`run_id`** + **backend**. Nothing
   downstream is real without these.
2. **Competitor intelligence, deepened** (§A–D): the launch-timeline agent, the
   funnel-map agent, and video teardowns — on the 21 Auri dossiers already stored.
   Cited by construction so [VALIDATION-HARNESS.md](VALIDATION-HARNESS.md) V2 can
   grade them.
3. **Strategy synthesis** (§E–H, L): market/ICP → positioning/white-space →
   GTM strategy → launch campaign → incentives, scaled to the tenant's real
   budget/constraints (V3 constraint-responsiveness is the test).
4. **Platform-native content + scripts** (§I, J): fan the proven content pipeline
   across LinkedIn/Reddit/PH/email/blog; every asset tagged
   audience+funnel+objective+CTA.
5. **Creative + video** (§K, D): the Remotion branded-overlay renderer first
   (reuses the card wiring), then AI B-roll — per [VIDEO-PRODUCTION-SPEC.md](VIDEO-PRODUCTION-SPEC.md).
6. **Blueprint assembler** (§M, R): the 33-part per-launch artifact.
7. **Closed loop** (§N–Q): execute → attribute → experiment → learn, on the
   learning loop already running.
8. **Validate** (V0–V6) before trusting any of it in production.

**Smallest real slice that proves the whole shape:** for **Auri**, one launch
blueprint for **one channel (X)** — competitor launch-timeline teardown (§A) →
positioning + white-space (§F) → a 2-week campaign plan scaled to a real budget
(§H, M) → tagged scripts + cards (§I–K) → *manual* publish (until APIs) →
measure + learn (§O, Q). That is a genuine end-to-end GTM blueprint on real
research, using almost entirely what is already built — the honest MVP of the AI
GTM Department.

---

## One-line summary

> The intelligence, the safety gate, the per-tenant brand system, the creative
> renderer, and the learning loop are built. The strategy brain, the
> cross-platform expansion, the video arm, and closed-loop execution are the
> build ahead — and closed-loop execution waits on a working publish path, which
> is the one thing to fix first.
