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

## Architecture — hybrid cloud/local

Scraping runs through a local Chrome bridge (OpenCLI), so it cannot run in the
cloud. The dashboard is public on Cloud Run; the pipeline executes locally;
**GCS is the seam between them**.

```
Dashboard (Cloud Run, public)  --run request-->  GCS bucket  --polls-->  Local runner
        ^                                     requests/ traces/                |
        |                                     runs/ drafts/ cards/             | runs
        +------------ SSE live trace ---------------+                          v
                                                          autonomous_orchestrator.py
                                                          brain: gemini-3.5-flash
                                                                 |
                                                                 v
                                                        Telegram (human review)
```

- Bucket: `gs://vanna-pipeline-state-506009` · GCP project `video-506009` · region `us-central1`
- Brain: `gemini-3.5-flash` via the generativelanguage API key in `pipeline/.env`
  (Vertex/ADC is blocked for this key — do not reroute to Vertex)
- Dashboard auth: service account. Local runner auth: ADC. These are separate
  and the org enforces periodic reauth, so the runner's ADC expires often.

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
- `deploy_gcp.sh` targets project `sales-agent-504607`, **not** the `video-506009`
  project the live dashboard runs in. Check before using it.
- ~537 untracked files. Commit work you care about — that is how the above was lost.
