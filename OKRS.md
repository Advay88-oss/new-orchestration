# OKRs — turning this pipeline into a product

Short-term and long-term objectives for taking the Vanna content pipeline from a
single-company installation to something that can be set up for any company.

Baselines measured on **2026-08-10**. Short term means the next ~90 days
(through early November 2026); long term means the next 12 months (through
August 2027).

Companion documents: [ARCHITECTURE.md](ARCHITECTURE.md) for how it works,
[JOURNEY.md](JOURNEY.md) for what broke, [WHITE-LABEL-SETUP.md](WHITE-LABEL-SETUP.md)
for the per-company setup surface this plan is trying to shrink.

---

## Where we actually are

Every number below is measured, not estimated. Where no measurement exists, it
says so — that absence is itself a finding, and §5 deals with it.

| Metric | Value | Source |
|---|---|---|
| Companies served | 1 (Vanna) | — |
| Runs recorded | 13, over ~20 hours | `content_history.json`, 2026-08-09 08:50 → 2026-08-10 04:44 |
| Runs ending `timeout` | **7 of 13 (54%)** | same |
| Runs ending `shipped` | 4 | same |
| Runs ending `approved` | 2 | same |
| Posts confirmed published to X | **1** | account timeline, 2026-08-09 17:53 |
| Approved but unpublished | 1 (`dfda50d2`) | blocked on the OpenCLI bridge |
| Model cost of one complete run | **$0.0597**, 9 Vertex calls, ~2m15s | `vertex-calls.jsonl`, 04:34:30–04:36:45 |
| Total spend | $3.3290 over 369 calls since 2026-08-08 | `spend-ledger.json` |
| Average cost per Vertex call | $0.0090 | derived |
| Cost per *published* post | **no metric exists** | see §5 |
| Time to onboard a company | **never measured** | only one company has ever been set up |
| Full autonomous cycles on the relay path | **0** | [JOURNEY.md](JOURNEY.md#still-open) item 9 |

**The honest summary.** The system produces good content cheaply and has
published once. Slightly over half of all runs die waiting for a human, the
publishing path is currently broken, and the second company has never been
attempted. Nothing here is a scale problem yet; everything is a reliability and
repeatability problem.

---

## The product thesis

Worth stating explicitly, because the OKRs only make sense against it.

What is being sold is **not** "AI writes your social posts" — that market is
crowded and undifferentiated. Two things here are genuinely hard to copy:

1. **Content that provably cannot make a claim the company can't support.** The
   claim-safety gate is deterministic, blocking, and sits upstream of any human.
   For a company that is pre-launch, pre-revenue, in a regulated category, or
   otherwise constrained in what it may assert, this is the whole product. The
   tier system in `files/08` — quotable / state carefully / future tense only —
   is the portable asset.
2. **Content that argues rather than averages.** Three strategists locked to
   opposing narrative arcs, judged adversarially by a critic whose default is
   rejection. Generic tools converge on the safe post; this one is built to stop
   that.

Everything else — the scout, the renderer, the dashboards — is table stakes.
The OKRs below prioritise accordingly: the gate and the debate get invested in,
the surrounding machinery gets made boring and reliable.

---

## Short term — next 90 days

**Theme: make one company reliable, and make the second company cheap.**

Do not pursue multi-tenancy this quarter. The system has not yet proven it can
run one company unattended, and a multi-tenant version of an unreliable pipeline
is just an unreliable pipeline with more surface area.

### O1 — The pipeline ships without being babysat

*Right now a run has a roughly even chance of producing nothing, and the reasons
are all known and all fixable.*

| KR | Baseline | Target |
|---|---|---|
| KR1.1 Runs ending `timeout` | 54% (7/13) | **< 10%** |
| KR1.2 Approved drafts that reach the platform | 0 of 1 currently | **100%** |
| KR1.3 Runs lost to an unretried transient failure | 1 known occurrence | **0** |
| KR1.4 Consecutive scheduled runs completing unattended | never attempted | **10** |

The named work behind these, each already diagnosed:

- The review poll gives a human **120 seconds** (`trendjack_news_orchestrator.py:445`)
  while the script's own default is 3600. This alone explains most of KR1.1.
- The Telegram dispatch parses subprocess stdout with **no retry and no
  empty-string guard** (`:430`). One transient failure destroys a run that has
  already passed the gate and rendered its card.
- The OpenCLI Chrome bridge is the only publishing path and it is currently
  returning `No SW`. KR1.2 cannot move until this is either repaired or replaced
  with an API-based path.
- The RSS fetch **fabricates a fallback news item** when the feed is unreachable,
  so a network failure silently produces a run built on invented input. This
  should fail loudly instead.

### O2 — We know what a published post costs and what it is worth

*One measured run is not unit economics. Nothing currently connects spend to
output.*

| KR | Baseline | Target |
|---|---|---|
| KR2.1 Cost per **published** post, instrumented end to end | no metric | **reported automatically every run** |
| KR2.2 Model cost per completed run | $0.0597 (measured once) | **median over ≥30 runs, ±20% band known** |
| KR2.3 Human minutes per published post | never measured | **measured, then < 5** |
| KR2.4 Engagement captured per published post | not captured | **recorded for every post** |

KR2.4 is the one that turns this from a cost centre into something with a
demonstrable return, and it is currently the largest measurement gap — the
pipeline publishes and then forgets. Note the existing display invariant when
building it: **`null` is not `0`**. A post whose engagement could not be
retrieved must not be recorded as zero engagement.

### O3 — A second company can be set up in a known, repeatable time

*The setup surface is documented ([WHITE-LABEL-SETUP.md](WHITE-LABEL-SETUP.md));
it has never been walked.*

| KR | Baseline | Target |
|---|---|---|
| KR3.1 Gate rule sets loaded from per-company data files, not Python | rules hardcoded, 32 across 4 sets | **shipped** |
| KR3.2 Absolute paths in dashboard routes | 14 files hardcode `D:/new orchestration` | **1 env var, 0 hardcoded** |
| KR3.3 Vertex project id honoured from env on the live path | hardcoded in 2 orchestrator URLs | **env var honoured everywhere** |
| KR3.4 End-to-end onboarding of a real second company | never done | **done once, elapsed time recorded** |
| KR3.5 Must-block / must-pass gate test suite per company | none | **exists, runs in CI** |

**KR3.1 is the highest-leverage item in this document.** Externalising the rule
sets does three things at once: it makes each new company a data change instead
of a code change, it removes the most dangerous manual step in onboarding, and
it fixes the existing decoupling where editing `files/08` does not change what
the gate blocks. Do this before attempting company number two.

**KR3.5 exists because of a real defect.** `R-mcp-differentiator` was found to
pass the exact retired phrasing sitting in `files/05` — a rule that looked
correct and had never been tested against the string it was written for. Every
company's rule set needs a suite that proves at least one rule blocks something.

### O4 — Content quality is defended, not assumed

*The debate architecture is the differentiator and there is currently no
evidence it is working at scale.*

| KR | Baseline | Target |
|---|---|---|
| KR4.1 Runs with ≥1 cross-reply between two *different* strategists | 0 in the loaded fixture | **> 80% of runs** |
| KR4.2 Judge rejection rate | not tracked | **tracked; a rate near 0% means the judge is not working** |
| KR4.3 Drafts blocked by the gate | 0 of the runs inspected | **tracked, with the rule that fired** |
| KR4.4 Source-document contradictions outstanding | 2 known (`files/05:14`, `:47`) | **0** |

KR4.2 deserves a note: a judge that never rejects is indistinguishable from no
judge. The target is not "low rejections" — it is a rejection rate that is
tracked and defensible.

---

## Long term — 12 months

**Theme: one installation, many companies, provable safety.**

### O5 — One installation serves many companies

| KR | Baseline | Target |
|---|---|---|
| KR5.1 Companies served from a single deployment | 1 (fork-per-company only) | **5+** |
| KR5.2 Tenant id present in drafts, history, ledger, logs | absent everywhere | **present everywhere** |
| KR5.3 Per-tenant spend caps and ledgers | one global ledger, one port | **per tenant, isolated** |
| KR5.4 Per-tenant reviewer routing | `REVIEWER_CHAT_ID` is a module constant | **configured per tenant** |

The six specific blockers are enumerated in
[WHITE-LABEL-SETUP.md §10](WHITE-LABEL-SETUP.md#10-what-blocks-real-multi-tenancy).
KR5.3 matters more than it looks: a shared ledger means one company's runaway
run exhausts another company's budget.

### O6 — Onboarding is a workflow, not an engineering project

| KR | Baseline | Target |
|---|---|---|
| KR6.1 Time to onboard a new company | unmeasured, currently days of writing | **< 1 day** |
| KR6.2 Onboarding steps requiring a code change | most of tiers 3–6 | **0** |
| KR6.3 Companies onboarded by someone who did not build the system | 0 | **≥ 2** |

KR6.3 is the real test. Documentation that only its author can follow has not
been validated.

### O7 — Safety is provable to a buyer

*This is what justifies the price, so it has to be demonstrable rather than
asserted.*

| KR | Baseline | Target |
|---|---|---|
| KR7.1 False or unsupportable claims published | 0 known, but **not systematically audited** | **0, with an audit trail** |
| KR7.2 Every published post traceable to its gate verdict and approver | not linked | **linked, queryable** |
| KR7.3 Claim-audit view comparing `strategist_said` vs `you_found` | type exists, view does not | **shipped** |
| KR7.4 Independent review of the rule sets per company | none | **signed off before first publish** |

KR7.3 is called out in the dashboard's own notes as the highest-value thing to
build next, and the reasoning holds: a claim where what the strategist said
differs from what the scout actually found is the most dangerous failure mode in
the system, and nothing currently surfaces it.

### O8 — The autonomous architecture either ships or is retired

*Two execution paths exist. One works and is not the design; the other is the
design and has never completed a run.*

| KR | Baseline | Target |
|---|---|---|
| KR8.1 Full cycles completed on the multi-process relay path | **0** | **decision made and executed** |

This is a fork in the road, not a feature. Either the relay path completes a
cycle and becomes the product, or it is retired and the direct orchestrator
becomes the product officially. Carrying both indefinitely costs maintenance on
a path nobody uses and keeps the dashboards coded against a message contract
that does not match reality. Make the call inside 90 days; execute within 12
months.

---

## The instrumentation gap

**Most KRs above cannot currently be measured.** This is the first work item, not
a footnote — an OKR you cannot track is a wish.

What exists: `content_history.json` (per-run outcome, topic, hook),
`spend-ledger.json` (cumulative), `vertex-calls.jsonl` (per-call cost with
timestamps), per-agent logs.

What is missing, in the order it should be built:

1. **A run id joining everything.** Runs are not delimited in the data at all;
   the dashboards infer boundaries from the conductor's prose and label them
   "inferred". Until the conductor stamps a real `run_id`, no per-run metric can
   be computed reliably. **This single change unblocks KR2.1, KR2.2, KR4.1 and
   KR7.2.**
2. **Publish outcome recorded by the pipeline.** `publish_outcome` currently
   exists on exactly one history entry because a human wrote it there. KR1.2 is
   unmeasurable until the publish step writes its own result.
3. **Engagement retrieval after publish.** Nothing reads back. KR2.4 needs a job
   that fetches metrics per published post on a delay.
4. **Gate verdict persisted per draft.** The gate prints JSON to stdout and it is
   discarded. KR4.3 and KR7.2 need it stored alongside the draft.
5. **Cross-reply counting on real runs.** The metric is implemented in the
   dashboard against fixture data. It needs to run against live runs.

---

## Non-goals

Stated so they do not quietly become work.

- **More platforms.** Twitter is not yet reliable; LinkedIn and Farcaster before
  KR1.2 is met would multiply an unsolved problem.
- **More agents.** Seven is enough. The constraint is reliability, not capacity.
- **A second dashboard.** There are already two, unreconciled. Pick one before
  building anything new.
- **Self-serve signup.** Nothing in the short term needs it, and it forces
  multi-tenancy prematurely.
- **Replacing the human review gate.** It is the product's safety story. Making
  it faster is O1; removing it is not on the roadmap.

---

## Risks that would invalidate this plan

- **Publishing depends on a browser extension.** The current path drives Chrome
  through a local daemon and it has already failed once with reads and writes
  both dead. This is a fragile foundation for a paid product; an API-based path
  may be a prerequisite rather than an optimisation.
- **The publishing account is personal.** Posts go to `@AnandAdvay91289`, not a
  brand handle. For a product serving other companies, per-tenant account
  ownership and access is an unsolved question with legal as well as technical
  parts.
- **The safety differentiator is only as good as the rules**, which are written
  by hand per company. KR3.1 and KR3.5 reduce this risk; they do not remove it.
  An un-rewritten gate for a new company is inert *and looks like it is working*.
- **Single-model dependency.** Everything runs on `gemini-2.5-flash` through one
  proxy against one GCP project. No fallback exists.
- **The relay path may be unrecoverable cheaply.** If O8 resolves toward
  retirement, the dashboards' entire endpoint contract needs rewriting, and that
  cost is not currently budgeted anywhere.

---

## What to do first

If only three things happen this quarter, these are the three, in order:

1. **Stamp a `run_id`.** Everything measurable depends on it.
2. **Fix the two reliability leaks** — the 120-second poll and the unretried
   dispatch. Together they account for eight of thirteen recorded runs producing
   nothing.
3. **Externalise the gate rule sets to data files.** It is the gate between "we
   fork the repo per company" and "this is a product".
