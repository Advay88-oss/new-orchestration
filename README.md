# Vanna GTM Operating System

An autonomous go-to-market engine. It finds what the market is talking about,
runs an internal debate about what to say, renders the visual, verifies every
claim against a facts ledger, and hands the result to a human for approval.

Built for **Vanna Protocol** — composable credit infrastructure on Stellar
Soroban — and designed to be re-pointed at any company via knowledge packs.

> **Nothing publishes automatically.** Every run terminates at human review.

---

## How a run works

```
trend research  ->  competitor scraping  ->  three strategists debate
      ->  editorial judge rules  ->  visual rendered  ->  claim-safety gate
      ->  Telegram review  ->  founder decides
```

Three strategists are invoked in parallel, each locked to a different narrative
arc, so the drafts **compete instead of converging**. The judge's default
posture is rejection — drafts ship only at 70/100 or better. The final gate is
deterministic: no overclaims, no invented numbers.

## Where it runs

The dashboard is public on Google Cloud Run. The pipeline runs locally, because
scraping goes through a local Chrome bridge. A GCS bucket is the seam: the
dashboard writes a run request, the local runner claims it, and the execution
trace streams back to the browser live.

| | |
|---|---|
| Brain | `gemini-3.5-flash` |
| Cloud | GCP `video-506009`, `us-central1` |
| State | `gs://vanna-pipeline-state-506009` |
| Review | Telegram |

## Quick start

```bash
# one full run
python pipeline/scripts/autonomous_orchestrator.py --focus "your topic"

# serve runs triggered from the dashboard
python pipeline/scripts/runner.py --interval 30
```

Needs `google-cloud-storage`, a `GEMINI_API_KEY` in `pipeline/.env`, and
`gcloud auth application-default login`.

## Reading order

| Document | For |
|---|---|
| `CLAUDE.md` | Repo map, commands, conventions, current state — **start here** |
| `ARCHITECTURE.md` | The full 13-agent system specification |
| `JOURNEY.md` | How this was built |
| `HANDOFF.md` | Operating handoff notes |
| `WHITE-LABEL-SETUP.md`, `OKF-PACKS.md` | Running it for another company |
| `OKRS.md` | Turning the pipeline into a product |

## Multi-tenant

Tenant knowledge lives in packs, not in code. `pipeline/companies/` holds tenant
configs; `okf-auri/` is a complete second tenant. Adding a company means
authoring a pack, not editing agents.

## Ground rules

- Dated sources; FOUND vs INFERRED marked; never invent a number
- One narrative arc per asset — no mixing
- Secrets (`pipeline/.env`, `pipeline/keys/`) never leave the machine
- Human review is the terminus — do not add auto-publish
