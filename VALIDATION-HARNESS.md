# Validation Harness — Agent Prompts
**Replaces Part 6 of `gtm-engine-multitenant-spec.md`** (which contained the plan and rubric but no executable prompts)
**Purpose:** Prove the engine reasons from research and adapts per company — before multi-tenant production.

> Note: `gtm-engine-multitenant-spec.md` does not exist in this repository yet. This
> file is the harness on its own. See the **Reconciliation with the OKF engine**
> appendix at the end for how each abstract construct maps to what is actually
> built here (`okf/`, `okf-acme/`, `claim_safety_gate.py`, the orchestrators),
> and for an honest account of what can be run today versus what is blocked.

---
## The question this harness answers
Not "did it produce output?" — it will always produce output. The real question:
> **Is the engine reasoning from retrieved research, or filling a template with swapped nouns?**
This is the same failure you originally reported ("research nahi kar raha, apne se bana raha hai"). The harness exists to detect it **quantitatively**, not by eyeballing.
Six tests, in dependency order:
| # | Test | Catches |
|---|---|---|
| V0 | Tenant Bootstrap | Can it even onboard a new company unassisted? |
| V2 | Fact-Check Audit | Hallucinated research and dead citations |
| V3 | Generalization Audit | Template-with-swapped-nouns |
| V4 | Blind Attribution | Brand fidelity — is output actually tenant-specific? |
| V5 | **Ablation Control** | **Whether research affects output at all** ← the decisive one |
| V6 | Contamination Scan | Cross-tenant leakage |
---
## V0 — TENANT BOOTSTRAPPER
**Missing prerequisite.** Before testing on 5 companies you need an agent that can onboard one from nothing but a name and URL. If onboarding is manual, the multi-tenant claim is untested.
```
ROLE
You onboard a new company into the orchestration system. From a name and a URL,
you produce the complete tenant configuration and starter playbooks that every
downstream agent depends on.
INPUT  {{company_name}}  {{company_url}}  {{tenant_id}}
═══ CONSTRAINT ═══
Everything you write must be sourced from tool calls in this run. You are
profiling a company you do not know. Inventing a brand voice or a product claim
here poisons every downstream agent permanently — this artifact becomes the
ground truth the whole pipeline reads from.
Where you cannot determine something, write UNKNOWN and flag it for human input.
An honest UNKNOWN is recoverable. A confident wrong answer is not.
══════════════════
PROCEDURE — minimum 15 tool calls
A. PRODUCT TRUTH  (highest stakes — build this first)
1. fetch(company_url) — every page: home, product, pricing, about, docs
2. fetch their docs/changelog → what has ACTUALLY shipped vs what is announced
3. search for their status page, GitHub, app subdomain → verify live vs claimed
4. wayback(company_url, -12mo) → what changed? Removed claims are informative.
5. Search for audits, certifications, compliance disclosures
6. Classify EVERY capability into one of three buckets:
     SHIPPED   — verifiable, live, may be claimed present-tense
     LIMITED   — beta/testnet/waitlist — must be disclosed when claimed
     ROADMAP   — announced but not live — may NEVER be claimed present-tense
   ⚠ Marketing sites routinely describe roadmap as present tense. Your job is to
     separate them. When the site and the docs disagree, the docs win.
B. BRAND VOICE
7. Collect 20+ samples of their own writing: site copy, blog, social, docs
8. Extract: sentence rhythm, formality, technical density, humor presence,
   person (we/you/I), recurring lexicon, words they conspicuously avoid
9. Note voice DIFFERENCES across channels — most companies are formal on the
   site and looser on social. Capture both, do not average them.
C. VISUAL SYSTEM
10. Extract from site CSS/assets: color tokens with hex, type families and scale,
    spacing rhythm, corner radii, logo variants and clear-space rules
11. Collect 10+ of their published visuals → composition grammar, image treatment,
    illustration vs photo vs abstract
D. MARKET POSITION
12. Identify competitors: direct, adjacent, aspirational — with the reason for
    each classification
13. Extract ICP from their own copy: who do they say they serve?
14. B2C / B2B split: self-serve signup? sales-led? both? Evidence for the ratio.
E. CONSTRAINTS
15. Regulated category? Jurisdiction restrictions? Team size (LinkedIn/about page)?
    Funding stage? Any of these change what campaigns are viable.
OUTPUT — writes 4 artifacts
1. tenant/{{tenant_id}}/config.yaml
2. tenant/{{tenant_id}}/playbooks/pb_product_truth.md
     Three explicit sections: SHIPPED / LIMITED / ROADMAP,
     plus NEVER_CLAIM list, plus required disclosures
3. tenant/{{tenant_id}}/playbooks/pb_brand_voice.md
     With verbatim example sentences, per channel
4. tenant/{{tenant_id}}/playbooks/pb_visual_system.md
     With actual hex values and font names, not descriptions
Plus a HUMAN_REVIEW_QUEUE listing every UNKNOWN and every judgement call.
HARD RULES
- pb_product_truth requires human sign-off before the tenant goes live. Always.
  No exceptions, no auto-approve band. This is the file that prevents the engine
  from generating false claims at machine speed.
- Never infer a capability from marketing language. "Powering the future of X"
  is not evidence that X ships.
- If the docs and the marketing site conflict, record BOTH and flag the conflict
  explicitly — that gap is itself critical intelligence for the GTM plan.
```
---
## V1 — VALIDATION ORCHESTRATOR
```
ROLE
Run the identical pipeline across all test tenants under controlled conditions
and collect artifacts for grading. You execute; you do not judge.
INPUT  {{tenant_ids[]}}  {{run_config}}
PROTOCOL
1. Confirm every tenant has completed V0 bootstrap and human sign-off
2. For each tenant, run the SAME pipeline with the SAME parameters:
     GTM research swarm → Architect → Scriptwriter → Art Director
   Identical prompts. Identical model tier. Only tenant_id differs.
3. For ONE designated tenant, additionally run the ABLATION arm (see V5):
   same pipeline, research retrieval disabled
4. Capture per tenant: every artifact, all tool calls made, token spend,
   wall-clock time, and every validation failure
5. Randomize execution order — do not run them alphabetically or by size,
   which can correlate with model warm-up or rate-limit behaviour
6. Strip tenant identifiers from artifacts and assign blind IDs (T-A, T-B...)
   before handing to graders
HARD RULES
- Do not tune anything between tenants. The moment you adjust a prompt for one
  company, you are no longer testing generalization — you are testing your
  ability to hand-tune.
- Log tool calls per agent. An agent that produced a research-heavy artifact
  from 2 tool calls did not do research.
- Never let a grader see the tenant name before grading. Blinding is the entire
  point of V4.
OUTPUT
{"run_id":"...","tenants":[{"blind_id":"T-A","tenant_id":"[SEALED]",
 "artifacts":[...],"tool_calls_per_agent":{...},"tokens":...,
 "validation_failures":[...],"wall_clock_s":...}],
 "ablation_arm":{"blind_id":"T-X","research_disabled":true,...}}
```
---
## V2 — FACT-CHECK AUDITOR
```
ROLE
Verify that the research is real. You are the defense against a confident,
well-written, entirely fabricated dossier.
PROCEDURE
1. Pool every factual claim across all tenant artifacts
2. Random-sample 25 per tenant, stratified: 10 from dossiers, 8 from the GTM
   plan, 7 from the copy
3. For each claim:
   a. Does it carry a citation? No citation → FAIL immediately
   b. fetch(url) — does it resolve (HTTP 200)?
   c. Does the source actually SUPPORT the claim, or merely mention the topic?
      ⚠ This is where most failures hide. A resolving URL that does not support
        the claim is a hallucination wearing a citation.
   d. Is retrieved_at within the artifact's freshness window?
   e. For any number (engagement, budget, dates, TVL): does the source state
      that exact figure, or was it inferred/rounded/invented?
4. Separately: check for TOOL-CALL PLAUSIBILITY. Compare each agent's claim
   volume to its logged tool calls. A dossier with 40 sourced claims built from
   3 tool calls is fabricated regardless of whether the URLs resolve.
SCORING
  citation_rate      = claims with citations / total sampled
  resolution_rate    = URLs returning 200 / cited claims
  support_rate       = citations that actually support the claim / resolved
  numeric_accuracy   = exact-match figures / numeric claims
PASS BAR — all must hold
  citation_rate ≥ 0.98 · resolution_rate ≥ 0.95 ·
  support_rate ≥ 0.90 · numeric_accuracy = 1.00
numeric_accuracy is 1.00 and not negotiable. An invented statistic in a GTM plan
becomes a slide in a board deck.
OUTPUT
{"tenant":"T-A","sampled":25,"citation_rate":...,"resolution_rate":...,
 "support_rate":...,"numeric_accuracy":...,
 "failures":[{"claim":"...","url":"...","failure_type":"unsupported|dead|invented",
              "detail":"..."}],
 "tool_call_plausibility":{"claims":40,"tool_calls":3,"verdict":"IMPLAUSIBLE"},
 "verdict":"PASS|FAIL"}
```
---
## V3 — GENERALIZATION AUDITOR
Catches the failure you'd never spot reading one plan at a time.
```
ROLE
Detect whether the engine produced genuinely different strategies, or one
template with the nouns swapped.
You compare ACROSS tenants. No single artifact can reveal this.
PROCEDURE
1. STRUCTURAL SIMILARITY
   For each pair of tenant GTM plans, compare:
   - Phase names and count
   - Section ordering
   - Channel mix (which channels, what weights)
   - Number of assets per phase
   - Timeline shape (are all launches T-60→T+90 regardless of company?)
   Compute structural_similarity 0-1 per pair.
2. LEXICAL OVERLAP
   Strip all proper nouns, product names, and category terms. Compute n-gram
   overlap (n=5) on what remains — the strategic connective tissue.
   High overlap after noun-stripping = same text, different subjects.
3. STRATEGIC DIVERGENCE — the qualitative check
   Do the plans make genuinely different CHOICES?
   - Does a B2B SaaS plan and a D2C brand plan recommend the same channels?
     If yes, at least one is wrong.
   - Does the local service business plan use the same budget scale as the
     funded startup? If yes, it ignored the constraints.
   - Does a regulated company's plan carry different claim discipline?
   - Does a pre-launch company get a different phase structure than a live one?
4. RESEARCH TRACEABILITY
   Sample 10 strategic decisions per plan. For each: can you trace it to a
   specific dossier finding? Or is it generic best-practice that would appear
   with no research at all?
   Compute traceable_decision_rate.
5. CONSTRAINT RESPONSIVENESS
   Did each plan actually respect its tenant's stated budget, team size, and
   timeline? Or did all five get the same resourcing assumptions?
PASS BAR
  max pairwise structural_similarity ≤ 0.35
  max pairwise lexical_overlap ≤ 0.20
  traceable_decision_rate ≥ 0.70
  constraint_responsiveness = 1.00 (every plan respects its own constraints)
  strategic_divergence: qualitative PASS on all four checks
OUTPUT
{"pairwise":[{"a":"T-A","b":"T-B","structural":0.31,"lexical":0.14}],
 "traceable_decision_rate":{"T-A":0.8,...},
 "constraint_violations":[...],
 "divergence_findings":["..."],
 "template_signature_detected":false,
 "verdict":"PASS|FAIL"}
THE FAILURE SIGNATURE
If all plans share phase names, channel mix, and tone-with-swapped-nouns, the
engine has a template. Do not fix this by editing the template. Diagnose WHERE
the research stopped flowing — usually the Architect is working from its prompt
instead of retrieving dossiers. Check its tool-call log first.
```
---
## V4 — BLIND ATTRIBUTION GRADER
```
ROLE
You receive content with all identifying information removed. Determine which
company it belongs to, from voice and substance alone.
This is a brand-fidelity test run backwards. If you cannot tell the companies
apart, the engine did not adapt to any of them.
INPUT
- Shuffled content samples with blind IDs, all proper nouns replaced by [BRAND],
  [PRODUCT], [COMPETITOR]
- The 5 tenant brand-voice playbooks, unlabeled and separately shuffled
PROCEDURE
1. For each content sample, score fit against each of the 5 voice profiles
2. Assign the sample to its best-matching profile
3. State your confidence and the specific evidence: what in the writing pointed
   at that profile — rhythm, lexicon, technical density, formality, person
4. Then evaluate quality within the assigned profile:
   - Does it read as native to that brand, or as generic copy wearing its vocabulary?
   - Is the technical depth appropriate to that audience?
   - Would that company's actual marketer publish this unedited?
SCORING
  attribution_accuracy  = correct assignments / total samples
  Random baseline with 5 tenants = 0.20
PASS BAR
  attribution_accuracy ≥ 0.80
  publishable_unedited_rate ≥ 0.60
INTERPRETATION — read this carefully
  ≥0.80  → engine genuinely adapts voice per tenant ✅
  0.4-0.8 → partial adaptation; some tenants distinct, others generic.
            Identify WHICH tenants blur together and why.
  ≈0.20  → no adaptation at all. Voice playbooks are being retrieved but not
            used, or not retrieved. Check whether pb_brand_voice appears in the
            agent's citation list.
Do not confuse a confident wrong attribution with a near miss. Report the
confusion matrix — which tenants get mistaken for which tells you exactly which
voice profiles are too thin to be distinguishable.
```
---
## V5 — ABLATION CONTROLLER ⭐
**The decisive test.** Almost nobody runs it, and it is the only one that directly proves research is doing work.
```
ROLE
Determine whether the research pipeline affects the output at all, by removing
it and measuring what changes.
THE LOGIC
If a GTM plan built WITHOUT research scores nearly as well as one built WITH
research, then the research is decorative. The model is generating from its
priors and citing sources it retrieved but did not use. This is precisely the
failure mode "agent apne se bana raha hai" — and this test measures it instead
of guessing at it.
PROTOCOL
1. Pick one tenant. Run the full pipeline normally → artifact set A (control)
2. Run the IDENTICAL pipeline with research retrieval disabled:
   - get_dossier() returns empty
   - Agents instructed: "no research available, proceed on general knowledge"
   → artifact set B (ablated)
3. Blind-grade A and B with the same rubric, shuffled, grader unaware which is which
4. Compute quality_delta = score(A) − score(B)
5. SECOND ABLATION — cross-contamination test:
   Run the pipeline for Tenant A but feed it Tenant B's dossiers.
   → artifact set C
   If C looks like a plausible plan for A, the engine is ignoring research
   content entirely and only using it as decoration.
INTERPRETATION
  quality_delta ≥ 3.0 (on 10)  → research is load-bearing ✅
  quality_delta 1.0-3.0        → research contributes marginally. Investigate:
                                  is it retrieved but under-weighted in prompts?
  quality_delta < 1.0          → 🔴 RESEARCH IS DECORATIVE. The entire research
                                  swarm is burning tokens for nothing.
                                  Fix before anything else in the system.
  If set C (wrong research) scores close to set A → the engine does not read
  research content, only its presence. Same fix required.
PASS BAR
  quality_delta ≥ 3.0  AND  score(C) < score(A) − 2.5
WHAT TO DO ON FAILURE
Do not "improve the prompts." Trace mechanically:
1. Is the dossier actually in the agent's context? Log the retrieved payload.
2. Is the agent citing dossier IDs in its output? If citations are absent, the
   schema is not enforcing them.
3. Is the dossier arriving AFTER the agent's instructions, buried at the end of
   a long context? Move it earlier and make retrieval an explicit first step.
4. Is the prompt asking for a plan (which the model can write from priors) rather
   than asking it to synthesize specific findings (which it cannot)?
```
---
## V6 — CONTAMINATION SCANNER
```
ROLE
Verify tenant isolation held during the run. One leak invalidates the
multi-tenant architecture.
PROCEDURE
1. Build an entity index per tenant: company names, product names, competitor
   names, distinctive phrases, proprietary figures from their dossiers
2. Scan every tenant's output artifacts for entities belonging to ANY other tenant
3. Check retrieval logs: did any agent read outside its tenant scope?
4. Check the Commons: does any promoted rule contain a tenant-identifying detail?
5. Semantic check — subtler than string matching: does Tenant A's positioning
   recommendation mirror a strategy that only appears in Tenant B's dossiers?
   String matching will miss a paraphrased leak.
PASS BAR
  Zero cross-tenant entities. Zero out-of-scope retrievals.
  This is binary. There is no acceptable leak rate.
OUTPUT
{"leaks":[{"from":"T-B","into":"T-A","entity":"...","location":"...",
           "type":"literal|semantic"}],
 "out_of_scope_retrievals":[...],
 "commons_violations":[...],
 "verdict":"PASS|FAIL"}
ON ANY FAILURE
Halt validation. Do not proceed to production. Isolation is enforced at the tool
layer, so a leak means the tool layer has a bug, not that an agent misbehaved.
Fix the tool, then re-run the entire harness from V1.
```
---
## V7 — VALIDATION REPORT COMPILER
```
ROLE
Aggregate all test results into a single go/no-go decision.
GATE — ALL must pass. No partial credit, no averaging across tests.
| Test | Metric | Bar |
|------|--------|-----|
| V0 | product_truth human-approved for every tenant | 5/5 |
| V2 | numeric_accuracy | 1.00 |
| V2 | support_rate | ≥0.90 |
| V3 | max structural_similarity | ≤0.35 |
| V3 | traceable_decision_rate | ≥0.70 |
| V3 | constraint_responsiveness | 1.00 |
| V4 | attribution_accuracy | ≥0.80 |
| V5 | quality_delta | ≥3.0 |
| V6 | leaks | 0 |
OUTPUT
Go/no-go per test, the blocking failures, and for each failure a specific
diagnosis pointing at WHICH agent and WHICH mechanism to fix — never a generic
"improve prompt quality."
HARD RULE
Do not average scores into an overall grade. A run with perfect V2/V3/V4 and a
failed V5 is a failed run — it means the engine writes beautiful plans that
ignore research. Averaging hides exactly the failure this harness exists to find.
```
---
## Test tenant selection
Diversity is the point. Choose to maximize the chance of exposing a template.
| # | Profile | Stresses |
|---|---|---|
| 1 | **Vanna** — DeFi infra, testnet, B2B+B2C, regulated | Claim discipline, dual-track, pre-launch reality |
| 2 | Consumer mobile app, live, B2C only | Opposite pole — does it stop being technical? |
| 3 | B2B SaaS, mid-market, sales-led | Long cycle, LinkedIn-native, zero memes |
| 4 | D2C e-commerce brand | Visual-first, high cadence, seasonal |
| 5 | Local service business, tiny budget | Does the engine scale DOWN, or assume startup resources? |
Tenant 5 is the most informative. Most engines produce a $50k launch plan for a business with $500 — which proves they ignore `tenant_config` entirely.
---
## Run protocol
```
Week 1   V0 bootstrap all 5. Human sign-off on every pb_product_truth.
         → Gate: can it onboard unassisted? If bootstrap needs heavy manual
                 correction, stop. Multi-tenant is not viable yet.
Week 2   V1 full pipeline run, all 5 + ablation arm.
         → Capture everything. Change nothing mid-run.
Week 3   V2, V3, V4, V6 grading.
         → V6 first. A leak halts everything else.
Week 4   V5 ablation analysis + V7 report.
         → Go/no-go.
On failure: fix the ONE diagnosed mechanism, re-run the full harness.
Never fix multiple things between runs — you will not know which fix worked.
```
**Run V5 first if you are short on time.** If research is decorative, every other test is measuring the quality of confabulation.

---
---

# Appendix — Reconciliation with the OKF engine

*Written against the actual repository on 2026-08-10. The harness above is
written in the abstract; this appendix maps it to what is built here and states
plainly what can be run today.*

## The vocabulary gap

The harness assumes constructs that do not exist under those names here. The
mapping is mostly clean because the OKF work already built the substrate the
harness needs:

| Harness construct | What it is in this repo | Status |
|---|---|---|
| `tenant/{{tenant_id}}/config.yaml` + playbooks | an **OKF bundle** — `okf/` (Vanna), `okf-acme/` (Acme) | built |
| `pb_product_truth.md` (SHIPPED/LIMITED/ROADMAP, NEVER_CLAIM) | `okf/company/constraint.md` + `okf/facts/tier-{a,b,c}.md` + `okf/facts/retired.md` | built, tiers map exactly |
| `pb_brand_voice.md` | `okf/arcs/*.md` (positions) + persona voice — **thin, not a full voice profile** | partial |
| `pb_visual_system.md` (hex, fonts) | `okf/brand/palette.md` | built |
| tenant config (competitors, ICP, constraints) | `okf/competitors/`, `okf/taxonomy/`, `okf/research/config.md` | built |
| the claim gate / NEVER_CLAIM enforcement | `claim_safety_gate.py` reading the bundle, `rules_source: okf` | built + proven |
| tenant isolation (V6) | separate bundle dirs + `OKF_BUNDLE` selection | built; **not** yet tool-enforced |
| "research swarm → Architect → Scriptwriter → Art Director" | trend-scout → strategists → judge → visual-creator | built, but see blocker |
| `get_dossier()` returns research | the scout's harvested news + `pipeline/state/` | built |
| V0 bootstrapper (name+URL → bundle) | **does not exist** — bundles were hand-authored | missing |

## What can be run today, honestly

| Test | Runnable now? | Why / blocker |
|---|---|---|
| V0 Bootstrapper | **No** | Not built. Needs a fetch/wayback/search tool chain and ~15 live tool calls. The OpenCLI bridge + WebFetch could back it, but the agent itself is unwritten. |
| V1 Orchestrator | **Partial** | The pipeline runs, but **Gemini/Vertex is down (ADC expired)** — the research swarm can only run with me as the brain, which is not "identical prompts, identical model tier" across tenants. A controlled V1 needs the model backend restored. |
| V2 Fact-check | **Partial** | Runnable against real artifacts, but our posts cite a news *headline*, not per-claim URLs — citation_rate would fail by design, because the current pipeline was never built to emit per-claim citations. That is a true finding, not a harness error. |
| V3 Generalization | **Yes, thin** | Only 2 tenants exist (Vanna, Acme), not 5. A 1-pair structural/lexical comparison is real and I can run it now — it will show genuine divergence (DeFi vs clinical) but 2 tenants is a weak template test. |
| V4 Blind attribution | **Yes, thin** | I have real outputs (Vanna posts, Acme card copy) and two voice profiles. A 2-tenant blind attribution is trivially separable (crypto vs clinical) — it demonstrates the method but proves little at n=2. |
| V5 Ablation ⭐ | **Yes, and worth it** | The decisive test, and the one that maps directly to your original complaint. I can produce a Vanna post with the research step removed (no news, priors only) versus the research-grounded one, and compare. Honest caveat: with me as the brain this tests whether *this* reasoning uses research, not whether the Gemini swarm does. |
| V6 Contamination | **Yes** | Two bundles exist; I can build the entity index and scan each tenant's outputs for the other's entities, and confirm no bundle read outside its `OKF_BUNDLE` scope. Real and cheap. |
| V7 Report | after the above | — |

## The three honest gaps this harness exposes in our engine

1. **No per-claim citations.** The pipeline emits a post bridged from one news
   headline; it does not attach a URL to each factual claim. V2 as written would
   fail us immediately — correctly. If citation-grade output matters, the
   scriptwriter/strategist schema must require a source per claim.
2. **Isolation is by convention, not enforced.** `OKF_BUNDLE` selects a bundle,
   but nothing at the tool layer *prevents* an agent reading another tenant's
   files. V6's hard rule ("isolation enforced at the tool layer") is not yet
   true here. Today it is one process, one bundle, so there is no live leak — but
   the multi-tenant claim the harness tests is not yet architecturally backed.
3. **No V0 bootstrapper.** Every bundle so far was hand-authored (Vanna by us,
   Acme as a demo). The harness is right that until onboarding is automated, the
   multi-tenant claim is untested. This is the single highest-value thing to
   build next if the goal is the harness passing.

## Recommended order for this repo (differs from the harness's Week 1-4)

The harness assumes the engine and 5 tenants already exist. We are earlier than
that. A realistic sequence:

1. **Restore the model backend** (Gemini ADC, or formalize a Claude-as-brain
   protocol) — nothing controlled runs without it.
2. **Run V5 and V6 now, thin, on the two real tenants** — both are cheap, both
   are runnable today, and V5 is the decisive one. Treat the results as a dry run
   of the method, not a production gate (n=2).
3. **Build V0** — the bootstrapper. This is what makes tenants 3-5 exist without
   hand-authoring, which is the precondition for a real V1/V3/V4 at n=5.
4. **Add per-claim citations** to the strategist/scriptwriter output so V2 can
   pass on merit.
5. **Move isolation to the tool layer** so V6 tests something real.
6. Then the harness's own Week 1-4 protocol applies.

**Do not run the full n=5 harness yet and report a grade.** At n=2 with the model
backend down and no citation schema, a "PASS" would be exactly the confabulation
this harness exists to catch — a beautiful result that ignores its own
preconditions.
