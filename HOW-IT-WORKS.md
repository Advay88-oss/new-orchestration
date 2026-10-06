# How the Vanna GTM system works

This is the current operating picture: what runs, where each piece lives, and how to read the brand brain from the backend. Counts below were read from this machine on 2026-10-03 with `python -m pipeline.brand_brain stats vanna`.

Nothing in this system publishes a post by itself. A run stops at human review.

`ARCHITECTURE.md` is the earlier 13-agent specification. This file is the one that matches the code that is running.

## Architecture

```
Dashboard (hermes-mission, Next.js)
  localhost:3000, and the last Cloud Run deploy
        |
        |  Launch Run, scheduler Run Now, /brief chat
        v
pipeline/gtm_os/autonomous_cycle.py
  one content run: scout, choose a signal, strategy, copy, poster, review
        |
        |  agents read the company only through the brain
        v
Brand brain (backend only)
  SQLite on this machine, or Cloud SQL Postgres + pgvector when
  BRAIN_DATABASE_URL is set and reachable
  text and images embedded with gemini-embedding-2 (768 dimensions)
```

| Piece | Where it lives |
|---|---|
| Dashboard | `hermes-mission/`. Home is Mission Control. `/brief` is the post-and-source page. |
| Content run | `python -m pipeline.gtm_os.autonomous_cycle`. The dashboard starts this same module. |
| Brand brain | `pipeline/brand_brain/`. Database, embeddings, profile, search. |
| Brain MCP | `python -m pipeline.brand_brain.mcp_server --tenant vanna`. Agents call this. They do not read the dashboard. |
| Scheduler | `config/scheduler.yaml` plus `pipeline/scheduler/configurable_scheduler_daemon.py`. |
| Run records | `pipeline/state/gtm_runs/GTM-*/summary.json`. |
| Remote dashboard | `https://vanna-gtm-mission-114262736718.us-central1.run.app` (GCP project `sales-agent-504607`, region `us-central1`). That URL is the last deploy. This working tree is not that deploy. |

The dashboard is a window. The brain is the database. Opening the dashboard does not scrape, embed, or write a post.

## What a content run does

1. Scout collects signals (news, Reddit, DefiLlama, and the other collectors the cycle already uses).
2. The selector chooses one signal. A typed request (`--directive`) becomes the subject instead.
3. The strategist accepts or declines that subject.
4. Accepted runs write channel copy (X, LinkedIn, Reddit), then a poster. Video is Veo, and `/brief` skips it with `--no-video`.
5. The claim check and the reviewer can block the run. Status `review_blocked` means a person still has to decide.
6. The run folder stores the chosen signal on `summary.json`: `signal`, `signal_source`, and, on new runs, `signal_url`, `signal_excerpt`, `signal_publisher`.

`/brief` reads that file. It shows the post and the source that run chose. A chat message there starts this same cycle and keeps the sources that were on screen.

## The brand brain is backend-only

The Brand Brain screen is no longer on the dashboard. Live Trace still opens the work, decisions, and agents for a run. The company knowledge itself stays in the database, with vectors.

On this machine the backend is **sqlite**. `stats` reports `"backend": "sqlite"`. Embeddings are created when a page is ingested or an image is captioned, not when the dashboard opens.

| Store | What was measured |
|---|---|
| Knowledge chunks | 1,766 (sections excluded) |
| Rows with a vector | 1,931. That is every live chunk, including 165 section headings. |
| Images with a vector | 22 of 22 |
| Profile | version 6, status `approved` |
| Last ingest | 2026-09-30T09:38:44Z |

Chunks by source: archive 325, docs 455, github 877, knowledge-pack 39, notion 16, profile 41, rulebook 13. 75 chunks are tombstoned. Competitor-pattern rows: 16 (that table also has a vector column). What's-new events: 0. Post outcomes: 0.

The model is `gemini-embedding-2`. Each vector is 768 floats, L2-normalised, stored as a blob on the chunk or image row. Search uses that vector. Keyword search still works if an embed call failed and the blob is empty.

These records sit beside the vectors. They are stored, and they are not embedding rows:

- GitHub commit list (`github_sync latest`)
- Inspiration brands and their campaign notes (`inspiration list`)
- Chat threads and the audit log

### How to see what the Brand Brain screen used to show

Run these from the repo root. On Windows, set `PYTHONPATH` to the repo root first, and use `.venv\Scripts\python.exe`.

One command prints the whole former screen: profile, chunk counts, GitHub, images, competitors, outcomes, scrape record, Notion, and the public watch.

```bash
python -m pipeline.brand_brain.dashboard overview vanna
```

| What the screen showed | Backend command |
|---|---|
| Company, profile version, approved or draft | `python -m pipeline.brand_brain profile vanna` |
| Approve a draft | `python -m pipeline.brand_brain approve vanna VERSION` |
| Chunk counts, images, last ingest | `python -m pipeline.brand_brain stats vanna` |
| Search the knowledge the agents retrieve | `python -m pipeline.brand_brain search vanna "health factor"` |
| Same search, with the passages | `python -m pipeline.brand_brain.dashboard search "health factor" vanna` |
| Visual references for a topic | `python -m pipeline.brand_brain refs vanna "isolated margin"` |
| GitHub files in the brain, and how many are embedded | `python -m pipeline.brand_brain.github_sync status --tenant vanna` |
| Newest commits (stored as records, not as vectors) | `python -m pipeline.brand_brain.github_sync latest --tenant vanna` |
| Brands and the five strategy fields | `python -m pipeline.brand_brain.inspiration list vanna` |
| Public watch (X, Reddit, news, blog) | `python -m pipeline.brand_brain.watch status vanna` |
| Re-embed or refill after new docs | `python -m pipeline.brand_brain ingest vanna` and `python -m pipeline.brand_brain images vanna` |

`search` returns the passages the agents get: source, authority, section, and text. Authority 1 is founder-confirmed. External pages are stored at a lower authority and are not treated as proof for a claim.

The approved profile on this machine is still the Stellar Soroban profile (version 6). GitHub Solana pages are stored next to it as knowledge chunks. Approving a new version is the `approve` command above. The dashboard no longer has a button for it.

## What the dashboard still shows

| Page | What it is |
|---|---|
| Assistant | Chat over the brain. Answers come from the database. The brain itself is not drawn here. |
| Live Trace | Where the current run is, and what it decided. "See how it was done" opens the work, the decisions, and the agents. |
| 24/7 Scheduler | Job list. Run Now starts that job. The clock runs only while the scheduler daemon process is open. |
| Crypto Memes | Meme panel. |
| Post History | One card per finished run. |
| Scraped Intelligence | Signals the scout collected. |
| What Vanna Can Do | Campaign notes for brands added in the inspiration store. Empty until a brand is added. |
| Learning | What later engagement changed. |
| References | Visual references. |
| `/brief` | One generated post, the source that run recorded, and a box that asks the existing cycle for another post. |

## Scheduler

The daemon is a separate process. `npm run dev` does not start it.

```bash
python pipeline/scheduler/configurable_scheduler_daemon.py --daemon
```

Jobs in `config/scheduler.yaml`: `gtm_cycle` 6h, `research_collect` 12h, `trend_scan` 12h, `ideas_panel` 12h, `memes_panel` 12h, `brain_watch` 6h, `github_commits` 1h, `notion_sync` 24h, `metrics_collect` 6h, `ops_watch` 1h. A model-heavy job cannot be set below 60 minutes. `trend_scan` can be 2 minutes. Changing the dropdown does not start the clock.

On Cloud Run the default tick is the lighter jobs (`notion_sync`, `metrics_collect`, `ops_watch`, `brain_watch`, `github_commits`). The full cycle is opt-in.

## Deploy

`deploy_cloud.sh` builds the dashboard service `vanna-gtm-mission` and the pipeline job `vanna-gtm-pipeline` in `sales-agent-504607`. Do not run it against an uncommitted tree if the live service should stay as it is. Secrets stay in Secret Manager and in `pipeline/.env`. They are not written into the dashboard.
