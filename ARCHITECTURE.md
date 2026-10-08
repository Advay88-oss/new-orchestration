# GTM Operating System — Architecture

How the engine actually works, as of 2026-10-08. This file describes the code; when the two
disagree, the code is right and this file is the bug. The roster below is declared in
`pipeline/gtm_os/agent_runtime.py` (`AGENT_ROLES`), which the dashboard reads, so a run's agent
list cannot drift from it.

The engine is tenant-agnostic (Vanna is tenant #1, Auri #2). Everything company-specific comes
from the tenant's brand brain: profile, arguments (the narrative arcs), facts, claims rules.

**It never publishes.** Every run ends at human review (Telegram and the dashboard).

---

## 1. One run

```
 founder directive / schedule / "make N posts"
        │
        ▼
 A01 Intelligence Scout ── parallel, no model: news RSS, Google News, GDELT, Reddit,
        │                  Telegram previews, DefiLlama, X (Apify, else Context.dev)
        ▼
 A02 Market Analyst + Opportunity Selector ── pick ONE subject (topic memory: no repeats)
        │
        ▼
 A03 GTM Strategists ── one per narrative arc, IN PARALLEL (the tenant's profile arguments)
        │                each argues only through its arc; they compete, not converge
        ▼
     Editorial judge (A15, sub-step "editorial") ── scores each /100, separate model call
        │   best ≥ 70 goes on; autonomous runs under 70 stop as NO_ACTION;
        │   a founder directive keeps its best angle (the subject was the founder's call)
        │   then planning: machine library + campaign vehicle (no model call)
        ▼
 A06 Copywriter ── X, LinkedIn, Reddit copy. If the model fails and the template
        │          stand-in is used, the run STOPS here (nothing paid for a stand-in)
        ▼
 A07 Creative Director (+ motion director) ── poster brief, layout, motion plan
        │
        ├──────────────► A08 Poster        ┐  in parallel
        └──────────────► A08 Meme          ┘
        │
        ▼
 A09 Video (Veo) ── made from the poster; skipped when the poster's own judge
        │           rejected every attempt
        ▼
 A15 Creative Judge ── judges what was actually made
        │
        ▼
 A10 Reviewer & Fact Checker ── channel review, slop check, and the fact check:
        │   every claim in every channel's copy AND the words on the poster against
        │   the brand brain + the deterministic claim-safety gate. Fails CLOSED:
        │   a model outage or a gate error blocks the run with that reason.
        ▼
 A11 Delivery ── Telegram review packet. A blocked run has no Approve button and
        │        cannot be approved anywhere (revise or kill). Dispatch never runs.
        ▼
 A13 Learning & Coach ── founder decisions + engagement (48 h later) → bandit,
                        learned rules, preferences. Per tenant.
```

Twelve agent ids, two of them judges (A10, A15) that never grade their own work. Former ids
(A04 machine library, A05 campaign engine, A12 Telegram, A14 motion director, A16 coach) were
merged into the agent that owns the job on 2026-09-26; old journals map through `MERGED`.

---

## 2. Models and spend

| Role | Default model | Override |
|---|---|---|
| reasoning (A02, A03, A06, A10, judges) | `gemini-3.8-flash` | `VANNA_GTM_MODEL_REASONING` |
| director (A07, A13) | `gemini-3.8-flash` | `VANNA_GTM_MODEL_DIRECTOR` |
| image (poster) | `gemini-3.1-flash-image` | `VANNA_GTM_MODEL_IMAGE` |
| meme | `gemini-3-pro-image` | `VANNA_GTM_MODEL_MEME` |
| video | `veo-3.1-generate-001` | `VANNA_GTM_MODEL_VIDEO` |

Calls go to the Generative Language API with the API key (Vertex/ADC is blocked for it).
Model calls retry 429 / 5xx / dropped connections twice with backoff; anything else fails at once.

Spend: `pipeline/ops/guard.py` wraps every paid HTTP call; `pipeline/ops/budget.py` holds daily
caps per service and in total (`config/budget.json`). Context.dev is counted too. It fails
closed: an unreadable ledger, or a guard that did not install, refuses paid calls.

---

## 3. Where it runs

- **Laptop (local mode):** the dashboard (`hermes-mission`, port 3000) keeps the scheduler daemon
  alive (`daemon_manager.py ensure`; one daemon per machine). The daemon runs every job on its own
  gap and renews a clock lease in the bucket.
- **GCP:** project `sales-agent-504607`. Cloud Run service `vanna-gtm-mission` (dashboard), Cloud
  Run Job `vanna-gtm-pipeline` (`pipeline/gtm_os/cloud_job.py`: `cycle`, `tick`, `sched <job>`),
  Cloud Scheduler, Cloud SQL brain (Postgres + pgvector, RLS per tenant), bucket
  `vanna-gtm-state-504607`.
- **One owner of the clock:** a cloud tick or cron that finds the laptop's fresh lease runs
  nothing. An unanswered GCP check keeps the last known owner.
- **State:** the bucket is the record in the cloud. A cloud run pulls with overwrite (the image's
  copies are build-time old); a push sends only files newer than the bucket's, with a generation
  precondition. Local writes are atomic with a last-good `.bak` (`pipeline/ops/atomic.py`).

---

## 4. Governance

- Facts: `files/08-facts-ledger-and-claim-safety.md` is the ledger. `registry/claims.jsonl` is
  generated from it (`python -m pipeline.scripts.build_claims_registry`); a test fails if they drift
  or if the gate blocks a fact the ledger calls safe.
- The deterministic gate: `pipeline/scripts/claim_safety_gate.py` (rules from the OKF bundle).
- Public dashboard: visitors read only, see only the public tenant's runs since their first visit
  (signed cookie), and the assistant refuses its action tools for them. The owner signs in on
  `/login`.

---

## 5. Run it

```bash
# one run, locally
python -m pipeline.gtm_os.autonomous_cycle --directive "explain health factor on Blend pools"

# the dashboard (and with it the scheduler daemon)
cd hermes-mission && npm run dev

# tests, network off (what CI runs)
python -m pipeline.tests.offline

# deploy everything to GCP
bash deploy_cloud.sh build jobs service
```

The earlier `core/` pipeline was removed on 2026-10-08; the model clients it had that the engine
still uses (LLM client, model routing, image generation, design rules, claim extraction) live in
`pipeline/genai/`. Video is Veo only (A09); the Remotion brand films are a separate tool.
