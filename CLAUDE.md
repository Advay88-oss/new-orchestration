# Vanna GTM Operating System — repo guide

Autonomous go-to-market engine for **Vanna Protocol** (composable credit
infrastructure on Stellar Soroban). It researches what is trending, argues
internally about what to say, renders the visual, checks every claim against a
facts ledger, and stops at human review. It never auto-publishes.

Authoritative spec: `ARCHITECTURE.md` (13 agents across 4 tracks —
Intelligence, Creative, Governance, Learning).

The engine is **tenant-agnostic**. Vanna is the primary tenant; Auri is the
second (`okf-auri/`), driven by OKF knowledge packs. See `WHITE-LABEL-SETUP.md`
and `OKF-PACKS.md` before adding a company.

---

## Architecture — all on GCP (2026-09-26)

Scraping uses only free public feeds and APIs (news RSS, Google News, GDELT,
Reddit, Telegram channel previews, DefiLlama) plus X via Apify (APIFY_TOKEN),
so it runs anywhere. Everything runs in GCP project **`sales-agent-504607`**
(number 114262736718), region `us-central1`, from one image (`Dockerfile`,
two roles). `deploy_cloud.sh` builds and deploys all of it.

```
Dashboard  vanna-gtm-mission (Cloud Run service, public link)
   | owner actions (OWNER_KEY cookie): Launch Run, approve, Brand Brain, Notion invites
   v
Cloud Run Job vanna-gtm-pipeline  ---- cycle: all 12 agents; they reach the brain only
   ^        |                           through the Brain MCP server (stdio child process)
   |        v
Cloud Scheduler vanna-gtm-tick (hourly: notion_sync, metrics_collect; the cycle is opt-in)
            |
   Cloud SQL brand-brain (Postgres 17 + pgvector, RLS per tenant)   GCS vanna-gtm-state-504607
   the brand brain of every tenant                                   runs, assets, learned state
            |
   Telegram review (webhook -> /api/telegram/webhook). Nothing publishes automatically.
```

- Visitors to the public link see only runs since their first visit and can
  change nothing; the owner opens it once with `?key=<OWNER_KEY>`.
- Secrets live in Secret Manager (from `pipeline/.env` via `deploy_cloud.sh secrets`).
- Brain LLM: the generativelanguage API key (Vertex/ADC is blocked for it — do not reroute).
- The laptop still works as before (local Docker Postgres, `.venv`), but it is no longer
  the production brain: Cloud SQL is. Telegram is on the webhook; do not start the local
  polling listener, it would exit with 409.

---

## Repo map

| Path | What it is |
|---|---|
| `pipeline/` | **The engine.** 108 scripts, 30 subsystems (`gtm_*`), agent prompts, state, drafts, logs |
| `pipeline/scripts/autonomous_orchestrator.py` | End-to-end content run |
| `pipeline/scripts/runner.py` | Bridges GCS requests → local pipeline → live trace |
| `pipeline/scripts/gcs_sync.py` | GCS push/pull/claim |
| `pipeline/scripts/claim_safety_gate.py` | Deterministic compliance gate |
| `pipeline/companies/` | Tenant configs (`vanna.json`, `sample_saas.json`) |
| `.claude/agents/` | Agent definitions: trend-scout, content-strategist, editorial-judge, visual-creator |
| `.claude/skills/` | Skills incl. `vanna-content-pipeline` (the orchestrator skill) |
| `hermes-mission/` | Next.js dashboard (alternate; untouched since 2026-08-09) |
| `gtm/` | GTM strategy work — Phase 1 landscape, Phase 2.5 content audit |
| `knowledge/`, `registry/` | Campaign book; claims, discovered players, outcomes (`.jsonl`) |
| `marketing/`, `work/`, `exports/` | Brand/ads/competitive assets, campaigns, Notion exports |
| `okf-auri/`, `auri data/` | Second tenant (Auri) knowledge pack |
| `remotion-video/`, `claude-video/`, `pipeline/video_*` | Video production stack |
| `open-design/`, `design references/` | Design systems and visual references |
| `Agent-Reach/`, `tools/` | Multi-platform scraping/research; utilities |

Root `*.md` files are specs and prompts — `ARCHITECTURE.md`, `GTM-ENGINE-SPEC.md`,
`GTM-BLUEPRINT-SPEC.md`, `CAMPAIGN-INTELLIGENCE-DOCTRINE.md`, `VALIDATION-HARNESS.md`,
`VIDEO-PRODUCTION-SPEC.md`, `HANDOFF.md`, `JOURNEY.md`, `OKRS.md`, `MAC_MINI_SETUP.md`.

---

## The content run (what the agents do)

1. **trend-scout** — scans X, Reddit, HN, ProductHunt, DefiLlama, Exa in parallel;
   scores with STEPPS and the 5 virality patterns. Returns evidence, never copy.
2. **live scouter** — scrapes competitor tweets + Reddit posts (local Chrome bridge).
3. **content-strategist ×3 in parallel** — one per narrative arc
   (capital-efficiency / risk-relief / third arc). They **compete, not converge**.
4. **editorial-judge** — scores all three out of 100, re-verifies every claim,
   ships at ≥70. Default posture is rejection.
5. **visual-creator** — renders the winner's brief to a 1080×1080 PNG.
6. **claim-safety gate** — deterministic PASS/FAIL. No overclaims, no invented numbers.
7. **Telegram review** — founder approves. **Nothing publishes automatically.**

---

## Commands

```bash
# full run (local)
python pipeline/scripts/autonomous_orchestrator.py --focus "topic" --visual static

# serve dashboard-triggered runs from GCS
python pipeline/scripts/runner.py --interval 30

# GCS state
python pipeline/scripts/gcs_sync.py requests|runs|push|claim

# brand brain (per tenant): build, search, serve over MCP
python -m pipeline.brand_brain init vanna
python -m pipeline.brand_brain search vanna "health factor"
python -m pipeline.brand_brain.mcp_server --tenant vanna            # stdio (.mcp.json)
python -m pipeline.brand_brain.mcp_server --tenant vanna --http 8765  # local HTTP; other hosts need BRAIN_MCP_TOKEN

# brain database: Postgres + pgvector (Docker, 127.0.0.1:5433), row-level security per tenant
python -m pipeline.brand_brain.pg setup             # container, role, schema; URLs go to pipeline/.env
python -m pipeline.brand_brain.pg migrate           # SQLite brains -> Postgres, then switch over
python -m pipeline.brand_brain.pg status | check-isolation | use-sqlite

# competitors (web search + their website and X posts -> pattern summaries only)
python -m pipeline.brand_brain.analyzer competitors --tenant vanna [--suggest]

# Notion: OAuth per tenant (Connect Notion on Brand Brain; token encrypted), or NOTION_TOKEN
python -m pipeline.brand_brain.notion_sync all            # the daily scheduler job

# learning: record where a post went out; engagement is read back after 48h (scheduler: metrics_collect)
python -m pipeline.gtm_learning.metrics_collector published GTM-... https://x.com/<handle>/status/<id>
python -m pipeline.gtm_learning.metrics_collector collect
```

Requires `google-cloud-storage` and valid ADC (`gcloud auth application-default login`).

---

## Conventions

- **Evidence discipline.** Dated sources; mark FOUND vs INFERRED; never invent a
  number. Claims are checked against the facts ledger and `registry/claims.jsonl`.
- **One narrative arc per asset.** Mixing arcs is forbidden.
- **Never commit secrets.** `pipeline/.env` and `pipeline/keys/` stay local.
- **Human review is the terminus.** Do not add auto-publish to any channel.

---

## Known state (2026-09-20)

- `mission-control/` (the deployed dashboard's source) and `files/` (the 12-document
  Vanna knowledge base) were **deleted from disk**. Tracked copies remain in git
  history; the SSE/scraped-card work was untracked and is gone. The deployed
  Cloud Run revision still serves normally.
- `pipeline/README.md` and the claim gate reference `files/08-facts-ledger-and-claim-safety.md`
  — that path is currently missing, so claim verification may degrade.
- `.claude/launch.json` still points at the missing `mission-control/`.
- The live dashboard and pipeline are in `sales-agent-504607` (deploy with
  `deploy_cloud.sh`). `deploy_gcp.sh` / `deploy_dashboard.sh` are the older,
  dashboard-only deploys.
- ~537 untracked files. Commit work you care about — that is how the above was lost.
