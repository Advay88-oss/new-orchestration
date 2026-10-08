# Vanna GTM Operating System — repo guide

Autonomous go-to-market engine for **Vanna Protocol** (composable credit
infrastructure on Stellar Soroban). It researches what is trending, argues
internally about what to say, renders the visual, checks every claim against a
facts ledger, and stops at human review. It never auto-publishes.

Authoritative spec: `ARCHITECTURE.md` (12 agents, two of them judges —
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
   | owner actions (signed session from /login): Launch Run, approve, Brand Brain, Notion invites
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

- Visitors to the public link see only this tenant's runs since their first visit
  (`vn_since` is HMAC-signed) and can change nothing: no runs, no schedule, and the
  assistant refuses its action tools for them. The owner signs in on `/login`
  (key in a POST body, 30-day signed session); `?key=` links only redirect there.
- File routes take bare names or validated run ids only (`hermes-mission/lib/safepath.ts`).
- Secrets live in Secret Manager (from `pipeline/.env` via `deploy_cloud.sh secrets`).
- Brain LLM: the generativelanguage API key (Vertex/ADC is blocked for it — do not reroute).
- The laptop still works as before (local Docker Postgres, `.venv`), but it is no longer
  the production brain: Cloud SQL is. Telegram is on the webhook; do not start the local
  polling listener, it would exit with 409.

---

## Repo map

| Path | What it is |
|---|---|
| `pipeline/` | **The engine.** ~160 modules in 12 `gtm_*` subsystems, agent prompts, state, logs |
| `pipeline/gtm_os/autonomous_cycle.py` | One content run (`run_cycle`), all 12 agents |
| `pipeline/gtm_os/cloud_job.py` | The Cloud Run Job entry: `cycle`, `tick`, `sched <job>` |
| `pipeline/gtm_os/state_sync.py` | GCS push/pull, job claims, the clock lease |
| `pipeline/gtm_os/editorial_judge.py` | Competing strategists per arc + the /100 judge |
| `pipeline/scripts/claim_safety_gate.py` | Deterministic compliance gate |
| `pipeline/companies/` | Tenant configs (`vanna.json`, `sample_saas.json`) |
| `.claude/agents/` | Agent definitions: trend-scout, content-strategist, editorial-judge, visual-creator |
| `.claude/skills/` | Skills incl. `vanna-content-pipeline` (the orchestrator skill) |
| `hermes-mission/` | Next.js dashboard (alternate; untouched since 2026-08-09) |
| `gtm/` | GTM strategy work — Phase 1 landscape, Phase 2.5 content audit |
| `knowledge/`, `registry/` | Campaign book; claims, discovered players, outcomes (`.jsonl`) |
| `marketing/`, `work/`, `exports/` | Brand/ads/competitive assets, campaigns, Notion exports |
| `okf-auri/`, `auri data/` | Second tenant (Auri) knowledge pack |
| `pipeline/gtm_creative/motion.py`, `pipeline/scripts/veo_broll.py` | Video (Veo, agent A09). Brand films: `D:/vanna-remotion` (crypto-video-style skill) |
| `open-design/`, `design references/` | Design systems and visual references |
| `Agent-Reach/`, `tools/` | Multi-platform scraping/research; utilities |

Root `*.md` files are specs and prompts — `ARCHITECTURE.md`, `GTM-ENGINE-SPEC.md`,
`GTM-BLUEPRINT-SPEC.md`, `CAMPAIGN-INTELLIGENCE-DOCTRINE.md`, `VALIDATION-HARNESS.md`,
`VIDEO-PRODUCTION-SPEC.md`, `HANDOFF.md`, `JOURNEY.md`, `OKRS.md`, `MAC_MINI_SETUP.md`.

---

## The content run (what the agents do)

`pipeline/gtm_os/autonomous_cycle.py`; the full picture is in `ARCHITECTURE.md`.

1. **A01 scout** — news, Google News, GDELT, Reddit, Telegram, DefiLlama and X in parallel. No model.
2. **A02** — picks ONE subject (topic memory: nothing repeats).
3. **A03 strategists, one per narrative arc, in parallel** — the arcs are the tenant's profile
   arguments (Vanna: capital efficiency, risk isolation). They **compete, not converge**.
4. **Editorial judge** — scores each /100 in a separate call; ships the best at ≥70, an autonomous
   run under 70 stops (default rejection). A founder directive keeps its best angle.
5. **A06 copy → A07 direction → A08 poster + meme in parallel → A09 video → A15 creative judge.**
6. **A10 fact check + claim-safety gate** — every channel and the poster text; fails closed.
7. **Telegram review** — founder approves (blocked runs cannot be). **Nothing publishes automatically.**

---

## Commands

```bash
# full run (local)
python -m pipeline.gtm_os.autonomous_cycle --directive "topic"

# the same on GCP (what the dashboard's Launch Run starts)
python -m pipeline.gtm_os.cloud_job cycle --directive "topic"

# GCS state
python -m pipeline.gtm_os.state_sync push-state|pull-state

# tests, network off (CI runs this)
python -m pipeline.tests.offline

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

# public watch: X, Reddit, news, blog, web summary -> brain with sources (scheduler: brain_watch, 6h)
# own channels are authority 3; everything others say is authority 5 (external: never proof for a post)
python -m pipeline.brand_brain.watch run [tenant] | status <tenant>

# Notion: OAuth per tenant (Connect Notion on Brand Brain; token encrypted), or NOTION_TOKEN
python -m pipeline.brand_brain.notion_sync all            # the daily scheduler job

# learning: record where a post went out; engagement is read back after 48h (scheduler: metrics_collect)
python -m pipeline.gtm_learning.metrics_collector published GTM-... https://x.com/<handle>/status/<id>
python -m pipeline.gtm_learning.metrics_collector collect

# Context.dev research agent: search, scrape, crawl, and brand intel on competitors
python -m pipeline.gtm_os.context_research_agent --competitor "Morpho Labs" --domain "morpho.org"
python -m pipeline.gtm_os.context_research_agent --topic "DeFi lending liquidation mechanisms"
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

## Known state (2026-10-07)

- `mission-control/` (the old dashboard's source) was **deleted from disk**; tracked
  copies remain in git history. `files/` (the 12-document Vanna knowledge base,
  including `files/08-facts-ledger-and-claim-safety.md`) is back on disk.
- `pipeline/scripts/autonomous_orchestrator.py`, `runner.py` and `gcs_sync.py` were
  removed in fe00f32. Production runs `pipeline/gtm_os/cloud_job.py` ->
  `autonomous_cycle.run_cycle`; bucket sync is `pipeline/gtm_os/state_sync.py`.
- The dashboard source is `hermes-mission/` (branded **Herald** since 2026-10-07):
  `/` is the front page, the app is `/app`, `/brief` is the share page.
  `.claude/launch.json` runs it (`hermes-mission`, port 3000).
- The live dashboard and pipeline are in `sales-agent-504607`; `deploy_cloud.sh` is the
  only deploy (the older dashboard-only scripts were removed: they reset env vars and
  disagreed on max instances).
- CI: `.github/workflows/ci.yml` runs ruff (`ruff.toml`), the claims-registry check,
  `python -m pipeline.tests.offline` (network blocked, no paid calls) and `tsc`.
- Python deps: edit `requirements.txt`, then recompile `requirements.lock` (command in
  its header); the image installs the lock with `--require-hashes` and runs as `app`.
- Runtime state (`pipeline/state/`, `state/`, generated images) is gitignored; it lives
  on disk and in the bucket. History still holds ~1.3 GB of old state.
- Scheduler: locally the dashboard server keeps `configurable_scheduler_daemon.py`
  alive (`daemon_manager.py ensure` every minute; `stop` from the Autopilot drawer
  is respected). When the GCP tick `vanna-gtm-tick` is ENABLED the laptop only
  mirrors the bucket's clock. "Make N posts" chains posts back to back (`_post_chain`).
  As of 2026-10-07 all four Cloud Scheduler jobs on GCP are PAUSED.
- Many untracked files are runtime state. Commit source you care about — that is how
  the above was lost. `.mcp.json` and `hermes-mission/.env.local` hold secrets.
