# Architecture

How the Vanna autonomous content pipeline works: every component, what it reads,
what it writes, and how to run it cold.

Written for an engineer who has never opened this folder. Everything here was
verified against the machine on **2026-08-10**; items that could not be verified
are marked `UNVERIFIED` with the reason. Where a document in this repository
disagrees with the code, the code is described and the disagreement is called
out.

Companion document: [JOURNEY.md](JOURNEY.md) — why things are the way they are,
and what is still broken.

---

## 1. What this is

A local, config-driven content engine for **Vanna**, a composable-credit DeFi
protocol on Stellar Soroban **testnet**. It researches live news, has three
agents argue three fixed narrative positions, judges the drafts adversarially,
renders a branded card, blocks anything that makes an unsafe product claim, and
sends the survivor to a human on Telegram before anything is published.

**There are two execution paths and they do not share code.** This is the single
most important thing to understand before reading further.

```
PATH A — direct orchestrator (currently ships content)

  Decrypt RSS ──► conductor ──► scout ──► 3 strategists ──► judge
   (last 24h)      (picks       (extracts   (compete on      (scores,
                    trend)       topic)      fixed arcs)      may kill all)
                                                                  │
                       ┌──────────────────────────────────────────┘
                       ▼
              claim_safety_gate.py ──BLOCK──► run ends, no human sees it
                       │ pass
                       ▼
              render_visual.py ──► 1080x1080 PNG (headless Chrome)
                       ▼
              telegram_review.py send ──► human ──► poll
                       │ approved
                       ▼
              opencli twitter post ──► content_history.json

  One Python process. Every agent is a Vertex call through the spend proxy.
  Does not use Buzz, does not use the relay, does not use agent identities.


PATH B — multi-process relay (architecturally complete, never finished a cycle)

  run_agents.py ──► 7 buzz-acp harnesses, one OS process each
                     │  each with its own Nostr keypair
                     ▼
                  Buzz relay (Rust, :3000) ──► channel `content-pipeline`
                     │  agents read and reply to each other by name
                     ▼
                  same gate / visual / Telegram tail as Path A
```

Path A is what produced every shipped post. Path B is the design the project is
actually aiming at — agents that answer each other rather than being polled in
sequence — and it has never completed a full run. See
[JOURNEY.md](JOURNEY.md#still-open) item 9.

---

## 2. The seven agents

Personas live in `pipeline/buzz-pack/agents/*.persona.md`; the contract they
share is `pipeline/buzz-pack/instructions.md`. Path A composes
`persona + instructions` into a Vertex `systemInstruction`; Path B gives each
one its own process and keypair.

| Agent | Persona file | Decides | May never |
|---|---|---|---|
| Conductor | `conductor.persona.md` | Which trend to jack, and whether to post at all | Write copy or research |
| Trend scout | `trend-scout.persona.md` | What is live, which competitor is referenced, why posts perform | Write copy or make product claims |
| Strategist — capital efficiency | `strategist-capital-efficiency.persona.md` | The pitch for "your collateral is doing one job; it should be doing six" | Borrow another arc's theme |
| Strategist — risk relief | `strategist-risk-relief.persona.md` | The pitch for "leverage is easy; not getting liquidated is hard" | Borrow another arc's theme |
| Strategist — agentic credit | `strategist-agentic-credit.persona.md` | The pitch for "agents can pay; agents can't borrow" | Borrow another arc's theme |
| Editorial judge | `editorial-judge.persona.md` | Scores drafts, ships one or kills all | Write copy |
| Visual creator | `visual-creator.persona.md` | Turns the winning brief into a card | Use AI for any readable text |

**Why the arcs are assigned, not chosen.** `files/04-brand-voice-and-message-library.md`
requires one narrative arc per asset and forbids mixing. Assigning a fixed arc
to each strategist is what makes them compete: agents free to choose converge on
the same safe angle and produce three versions of one post. Locked to fixed
positions, they have to argue for their own ground. The dashboard's headline
metric — cross-replies between two *different* strategists — exists to measure
whether that actually happened.

---

## 3. Runtime and dependency inventory

Versions observed on this machine on 2026-08-10.

| Dependency | Version | Where / notes |
|---|---|---|
| Python (pipeline venv) | **3.13.1** | `C:\Users\Advay Anand\.agent-reach-venv\Scripts\python.exe` — this is the interpreter the pipeline actually runs under |
| Python (project venv) | **3.11.15** | `.venv\Scripts\python.exe` — present, older, not what recent runs used |
| Python (system) | 3.13.1 | `C:\Python313` |
| Node.js | **v24.19.0** | npm 10.9.2. Note: a stray `AppData\Local\hermes\node` install once shadowed this — see [JOURNEY.md](JOURNEY.md) |
| Next.js / React (`mission-control`) | **15.1.6 / 19.0.0** | `mission-control/package.json` |
| Next.js / React (`hermes-mission`) | **14.2.15 / 18.3.1** | `hermes-mission/package.json` |
| Docker | **29.6.2** | `docker --version` |
| Docker Compose | **v5.3.1** | `docker compose version` |
| Postgres / Redis | via Docker Compose | `D:\buzz\docker-compose.yml`. No host `psql`/`redis-cli` on PATH; reach them with `docker exec` |
| Buzz relay | built from source | `D:\buzz\target\debug\buzz-relay.exe`. Rust workspace, partial build only — see §12 |
| Vertex AI model | **`gemini-2.5-flash`** | `trendjack_news_orchestrator.py:57`. The 3.x family does not exist on project `sales-agent-504607` |
| Chrome (headless) | installed | `C:\Program Files\Google\Chrome\Application\chrome.exe`, used by `render_visual.py:229` |
| Playwright | installed | `PLAYWRIGHT_BROWSERS_PATH=D:/ms-playwright`, used only by `twitter_tester.py` — not on the main path |
| OpenCLI | **1.8.6** | `opencli --version`. Publishing and research |
| Telegram Bot API | n/a | stdlib `urllib` against `api.telegram.org`, bot `@vanna0bot` |
| `@agentclientprotocol/claude-agent-acp` | `UNVERIFIED` | Path B only; not exercised in the runs recorded on disk |

---

## 4. Backend, in execution order

Path A, as implemented in `pipeline/scripts/trendjack_news_orchestrator.py`.
This is the newest orchestrator (modified 2026-08-09 23:37) and the one behind
every run in `content_history.json` whose source is `Decrypt Global RSS Feed`.

**The other orchestrators.** `autonomous_orchestrator.py` is the predecessor —
same shape, but it scrapes competitor Twitter and Reddit and picks a topic by
least-recently-used from `marketing_config.json` instead of jacking a news
story. Runs sourced from `MorphoLabs tweets`, `r/defi posts` and `scout scraper`
came from it. `run_twitter_lifecycle.py`, `run_campaign_lifecycle.py` and
`run_two_consecutive_runs.py` are thin drivers that call an orchestrator with
preset campaign copy. `slack_review.py` is a Slack-shaped alternative to the
Telegram gate and is not wired into either orchestrator.

**Step 0 — spend check.** `GET http://127.0.0.1:8900/_spend`. If the proxy is
unreachable, or under $0.05 remains, the run refuses to start. **Fatal.**

**Step 1 — harvest.** Fetches `https://decrypt.co/feed`, parses the newest 10
items (title, `pubDate`, description, HTML stripped). On failure it substitutes a
single hardcoded fallback item so the run continues — **watch for this**: a
network failure produces a plausible-looking run built on invented news.

**Step 2 — conductor.** Picks the strongest story, bridges it to one product
angle, and is explicitly blacklisted from repeating the last three
`hook_shipped` values in `content_history.json`.

**Step 3 — scout synthesis.** Extracts `selected_topic` (one of the five
taxonomy topics) and `competitor_referenced` as JSON.

**Steps 4–5 — strategist drafting and debate.** Three strategists draft, then
respond to each other's pitches in sequence.

**Step 6 — editorial judge.** Returns `ship` or a rejection, plus the winning
body, hook and `visual_brief`. Winner is written to
`pipeline/state/drafts/temp_winner.json`.

**Step 7 — claim safety gate.** See §4a. **Fatal on block.**

**Step 8 — visual render.** See §4b. Failure is non-fatal: `image_path` becomes
`None` and the run continues text-only.

**Step 9 — Telegram dispatch.** `telegram_review.py send`. **Fatal, and
fragile** — the orchestrator does `json.loads(tg_send_res.stdout)` at
`trendjack_news_orchestrator.py:430` with no retry and no empty-string guard. A
transient failure here destroys a run that has already passed the gate and
rendered its card.

**Step 10 — review poll.** `telegram_review.py poll --timeout 120`
(`:445`). `--auto-approve` skips the human entirely — do not use it for anything
that will actually be published.

**Step 11 — publish.** `opencli twitter post <text> --images <png>`, via
`subprocess.run(..., shell=True)`. Runs only on `status == "approved"`.

**Step 12 — history.** Appends the run to `content_history.json`. Reached only
if step 9 succeeded, which is why a step-9 crash silently loses the record.

### 4a. The claim-safety gate

`pipeline/scripts/claim_safety_gate.py` — the reason this project has a review
pipeline at all rather than a posting script.

```bash
python pipeline/scripts/claim_safety_gate.py --file draft.json --platform x
```

Accepts `--text`, `--file` or `--stdin`; `--no-testnet-check` disables the
testnet-disclosure requirement. Emits a JSON verdict on stdout and **exits 1 on
a block**, at which point the draft never reaches a human.

Four rule sets, evaluated together at `:291`:

| Set | Line | Covers |
|---|---|---|
| `HARD_PROHIBITIONS` | `:54` | Claims that are false at testnet stage — mainnet, token, audit, TVL |
| `TIER_F` | `:172` | Facts not in the ledger, or stated at the wrong confidence tier |
| `RETIRED` | `:204` | Claims retired by `files/11` — MCP as a differentiator, category ownership |
| `VOICE` | `:248` | Brand-voice prohibitions from `files/04` |

**These lists are hardcoded in the script.** The docstring at `:5` says they are
derived *from* `files/08-facts-ledger-and-claim-safety.md` — that records where
they came from when they were written. **The gate does not read `files/08` at
runtime, and editing the facts ledger will not change what it blocks.** Rules are
changed by editing the Python.

**A verified gap.** `R-mcp-differentiator` matches superlative and possessive
framings but not a bare feature bullet. Tested 2026-08-10:

| Input | Result |
|---|---|
| `Vanna is MCP-native. Policy-bounded. On-chain track record.` | **PASS** |
| `Vanna is the only protocol with MCP support.` | BLOCK `R-mcp-differentiator` |

The first string is the phrasing that sits in `files/05` at lines 14 and 47 — a
file the strategists read as a source. See §11.

### 4b. Visual rendering

`pipeline/scripts/render_visual.py`. Takes the winner's `visual_brief` JSON,
builds an HTML document at exactly 1080×1080 (`:155`), and screenshots it with
Chrome: `--headless=new --window-size=1080,1080 --screenshot=<out>`, 180s
timeout (`:229`–`:238`). Output lands in `pipeline/state/`.

**Every readable character is CSS, never AI.** This was tested, not assumed —
see [JOURNEY.md](JOURNEY.md#ai-image-generation-was-tested-for-readable-text-and-rejected).
The dark social theme derives from `design references/cl-11` and `cl-16`; note
that `design references/theme.md` documents the *light* app system, so the
renderer is the only specification of the dark variant.

---

## 5. The spend cap

`pipeline/scripts/vertex_spend_proxy.py`, serving `:8900`. Every Vertex call in
Path A goes through it. It exists because **GCP budgets are alerts, not caps** —
a budget emails you while the meter runs, and the only native hard stop would
have detached billing for an unrelated workload.

- **Cap:** `VERTEX_CAP_USD`, default `$10.00` (`:47`). Returns **HTTP 402** once
  reached (`:254`).
- **Metering:** `extract_usage` (`:100`) reads `usageMetadata`, handling
  streaming and SSE responses as well as single objects. This matters — the first
  version handled only single objects and charged everything else a flat
  pessimistic rate, burning the budget about 10× too fast.
- **Prices:** `PRICES` (`:54`), set deliberately high so the cap trips early.
  **Re-check these against current Vertex rates**; a wrong-but-low rate is how
  surprise bills happen.
- **Model rewriting:** `MODEL_REWRITE` (`:65`) rewrites non-existent model ids
  and strips unsupported fields, so a caller asking for `gemini-3.5-flash` does
  not get a 400.
- **Ledger:** `pipeline/state/spend-ledger.json`, so a restart does not reset the
  budget. **A corrupt ledger reads as exhausted, never as fresh** (`:172` returns
  `spent_usd = CAP_USD` on a parse failure). Fail closed, deliberately.
- `run_agents.py` refuses to start the gemini runtime if the proxy is down
  (`:115`).

```bash
curl http://127.0.0.1:8900/_spend
```

```bash
python pipeline/scripts/vertex_spend_proxy.py --reset
```

State as of 2026-08-10: `$3.3290` spent across 369 calls since 2026-08-08;
`pipeline/logs/vertex-calls.jsonl` holds 374 call records.

---

## 6. The human review gate

`pipeline/scripts/telegram_review.py`. Nothing reaches a social platform without
this returning an explicit approval.

```bash
python pipeline/scripts/telegram_review.py send --draft draft.json --image card.png
```

```bash
python pipeline/scripts/telegram_review.py poll --draft-id <id> --timeout 3600
```

```bash
python pipeline/scripts/telegram_review.py status --draft-id <id>
```

Reviewer chat is `5501720892`; the bot is `@vanna0bot`.

**Reply protocol** (reply to the draft message in Telegram):

| Reply | Status |
|---|---|
| `ok` `okay` `approve` `haan` `yes` `y` `ship` `go` | `approved` |
| `no` `nope` `reject` `nahi` `n` `kill` `drop` | `rejected` |
| anything else | `changes_requested`, reply kept as revision notes |

**State** is persisted per draft in `pipeline/state/drafts/<id>.json`, and moved
to `approved/` or `rejected/` on verdict.

**Token** is read from `TELEGRAM_BOT_TOKEN`, falling back to the first `.env`
found among `%LOCALAPPDATA%\hermes\.env`,
`~/.agent-reach/tools/telegram-bot/.env`, `~/.agent-reach/.env`, and
`D:/new orchestration/Agent-Reach/.env`. It is never printed.

**The default timeout is 3600s; the orchestrator overrides it to 120s.** Seven
of thirteen recorded runs died on that window.

---

## 7. Publishing

Twitter only, via OpenCLI's Chrome bridge:

```bash
opencli twitter post "<text>" --images "<path/to/card.png>"
```

- **Account:** the bridge is authenticated as **`@AnandAdvay91289`** — a personal
  account, not a Vanna brand handle. Confirm with `opencli twitter whoami`
  before assuming otherwise.
- **Mechanism:** a daemon on `127.0.0.1:19825` driving a Chrome extension on the
  `advayanand87@gmail.com` profile. It reuses that profile's logged-in session;
  no API keys or cookie export.
- **Failure modes.** `TIMEOUT` after 60s (raise with
  `OPENCLI_BROWSER_COMMAND_TIMEOUT`; there is no `--timeout` flag on `post`), and
  `No SW` — the daemon is alive but no extension service worker is attached, which
  breaks reads as well as writes. **A timeout is not proof the post failed:**
  check the account timeline before retrying, or you will double-post.
- Publishing anywhere other than Twitter is not built. Postiz was considered and
  deliberately dropped.

---

## 8. Frontend

**There are two Next.js apps and neither declares itself canonical.**

| | `mission-control/` | `hermes-mission/` |
|---|---|---|
| Next / React | 15.1.6 / 19.0.0 | 14.2.15 / 18.3.1 |
| Dev port | **3100** (`next dev -p 3100`) | **3000** (`next dev`) |
| Data seam | `lib/data.ts`, `source = 'fixture'` | `lib/api.ts`, `USE_FIXTURE = false` |
| Components | 3 | 12 components + 8 views |
| API routes | 7 | 7 (same names) |

`spend` and `calls` are byte-identical between the apps; `messages` and
`identities` differ. Treat this as an unreconciled fork.

### Route contract vs implementation

`hermes-mission/PORT-NOTES.md` §(c) specifies these seven read-only routes:

| Route | Contract says | Implementation actually does |
|---|---|---|
| `GET /api/messages?channel&since&limit` | raw Nostr events from the relay | **reads `pipeline/state/drafts/*.json` and synthesises messages** |
| `GET /api/identities` | pubkey → agent name | reads `pipeline/keys/agent-pubkeys.json` |
| `GET /api/spend` | `spend-ledger.json` verbatim | as specified |
| `GET /api/calls?since` | `vertex-calls.jsonl` as an array | as specified |
| `GET /api/agents/status` | per-agent log tail | reads `pipeline/logs/agents/*.log` + personas |
| `GET /api/artifacts/<name>.png` | serves `pipeline/state/*.png` | as specified |
| `GET /api/review/<draft_id>` | draft status + reviewer reply | as specified |

**Two things to know before trusting either app.**

1. **Neither app talks to the Buzz relay.** No route contains a relay URL, a
   WebSocket, or a `buzz` invocation. The messages route reconstructs a message
   stream from draft files on disk. The contract above describes a system that
   does not exist yet.
2. **All fourteen route files hardcode `D:/new orchestration`.** Both apps. This
   blocks the `MAC_MINI_SETUP.md` migration until every route is parameterised.

### Run boundaries are inferred

Runs are not delimited in the data — the channel is a flat message stream with no
run identifier. Boundaries are derived client-side from the conductor's run-open
and run-close prose, and every run carries an `inferred` flag the UI renders as
"boundaries inferred". The inference is isolated in one file so that adding a
`run_id` tag later removes it in one place.

### Three display invariants

These are deliberate and easy to break:

1. **`null` is not `0`.** The scout leaves engagement counts null when a research
   tool is unavailable. Rendering that as zero turns "we could not measure" into
   "we measured nothing" — a different and false claim. The `NoData` component
   exists so it cannot happen by accident.
2. **Cached input tokens are shown separately.** Most input on every call is
   cached; folding it into one total makes runs look far more expensive than
   they are.
3. **Five stage states, not two:** `done`, `running`, `failed`, `skipped`,
   `never reached`. A run that never reached the gate did not fail the gate.

---

## 9. How to run it, cold

### Path A — the one that ships content

Only two things need to be up: the spend proxy and the run itself.

```bash
export PYTHONIOENCODING=utf-8
```

```bash
"/c/Users/Advay Anand/.agent-reach-venv/Scripts/python.exe" pipeline/scripts/vertex_spend_proxy.py --port 8900
```

Confirm it before continuing — the orchestrator aborts at step 0 without it:

```bash
curl http://127.0.0.1:8900/_spend
```

```bash
"/c/Users/Advay Anand/.agent-reach-venv/Scripts/python.exe" pipeline/scripts/trendjack_news_orchestrator.py
```

The run prints each step. Approve or reject in Telegram when it reaches step 10.

### The dashboard

```bash
npm run dev --prefix mission-control
```

Serves on `http://localhost:3100`. A `.claude/launch.json` entry named
`mission-control` exists so the server survives the shell that started it —
starting it as a bare background job leaves nothing listening.

### Path B — the multi-process relay

Docker Desktop must be running first.

```bash
cd /d/buzz && docker compose up -d
```

```bash
DATABASE_URL="postgres://buzz:buzz_dev@127.0.0.1:5432/buzz?sslmode=disable" REDIS_URL="redis://127.0.0.1:6379" BUZZ_BIND_ADDR="0.0.0.0:3000" D:/buzz/target/debug/buzz-relay.exe
```

`127.0.0.1`, never `localhost` — see [JOURNEY.md](JOURNEY.md#postgres-rejected-every-connection-with-an-ssl-error).

```bash
curl http://127.0.0.1:3000/health
```

The WebSocket comes up *after* `/health` does; agents started immediately get
`404` on connect. `run_agents.py` staggers starts by 6s (`:232`) and some still
need an individual restart.

```bash
"/c/Users/Advay Anand/.agent-reach-venv/Scripts/python.exe" pipeline/scripts/run_agents.py --runtime claude
```

`--runtime` defaults to **gemini** (`:105`); `claude` is the proven path. Agents
ignore their own messages, so the conductor cannot self-start — kick a run off
by posting to the channel as the operator identity.

Channel `content-pipeline` = `31098616-3d0b-4202-86b4-96bfd36680cd`.

```bash
"/c/Users/Advay Anand/.agent-reach-venv/Scripts/python.exe" pipeline/scripts/watch_channel.py --limit 30
```

---

## 10. Configuration and secrets

All values redacted; none are printed by any script.

| Name | Read by | Without it |
|---|---|---|
| `TELEGRAM_BOT_TOKEN` | `telegram_review.py` (env, then four `.env` locations) | No human review; step 9 fails |
| `VERTEX_CAP_USD` | `vertex_spend_proxy.py:47` | Defaults to `$10.00` |
| `VERTEX_PROXY_URL` | `run_agents.py:52` | Defaults to `http://127.0.0.1:8900` |
| `PYTHONIOENCODING=utf-8` | every script | Emoji and non-latin output crash with a cp1252 `UnicodeEncodeError` |
| `OPENCLI_BROWSER_COMMAND_TIMEOUT` | OpenCLI | Publishing gives up after 60s |
| `PLAYWRIGHT_BROWSERS_PATH` | `twitter_tester.py` | Playwright looks on C: |
| `SLACK_BOT_TOKEN` | `slack_review.py` | Slack review path unavailable (not on the main path) |
| Google ADC | spend proxy → Vertex | `gcloud.cmd` mints tokens; Git Bash's `gcloud` shim reports a spurious reauth error |

**Files that are secrets:** `pipeline/keys/agent-keys.json` (private keys),
`pipeline/keys/operator-key.json`. Gitignored. Never print them.
`pipeline/keys/agent-pubkeys.json` is public and is what the dashboard reads.

**`.claude/settings.local.json`** is the allowlist bounding what agents may
execute, and it is a real security boundary. It is also matched as literal
prefixes: a compound command (`export PATH=... && opencli ...`) does not match
`Bash(opencli:*)` and is denied — silently, under `dont-ask`.

**Quote any `.env` value containing a space.** Several bash scripts `source .env`
and an unquoted Windows path executes as a command.

---

## 11. Known defects

Verified present on 2026-08-10 unless noted.

**Content correctness**

1. **`files/05` carries a retired claim at two lines**, contradicting
   `files/11` §10.1: `files/05-audiences-personas-and-objections.md:14`
   ("MCP-native · Policy-bounded · On-chain track record") and `:47`
   ("MCP-native from day one"). `HANDOFF.md` records only line 14.
2. **The gate does not catch that phrasing.** Bare "MCP-native" passes
   `R-mcp-differentiator` (tested, §4a). Defects 1 and 2 are only dangerous
   together: a source file agents read contains a claim the automated control is
   blind to.

**Pipeline**

3. **No retry on the Telegram dispatch.** `trendjack_news_orchestrator.py:430`
   parses subprocess stdout as JSON with no guard. A transient send failure
   discards a run that already passed the gate and rendered its card, and skips
   the history write.
4. **The review poll allows a human 120 seconds.** `:445`, overriding the
   script's own 3600s default. 7 of 13 recorded runs ended `timeout`.
5. **RSS failure fabricates news.** `fetch_latest_defi_news` substitutes a
   hardcoded fallback story when the feed is unreachable, so a network failure
   produces a confident run built on an invented item.

**Frontend** — from `hermes-mission/PORT-NOTES.md` §(b), found during the port
and deliberately left in scope-limited work:

6. **Draft expand state leaks across runs.** `lib/viewmodel.ts` `draftsVM` keys
   on `"draft:" + arc` with no run id; posts key correctly.
7. **Latent crash in the artifact panel.** `artifactVM` reads
   `run.ruling.winner.arc` when a `reject_all` ruling has `winner: null`. Does
   not fire only because rejected runs have no artifact.
8. **Overlapping stage spans double-count the timeline**, so some runs' bars sum
   past their own duration.
9. **`Math.max` on an empty score list** renders "Highest was -Infinity".
10. **Hardcoded singular "pitch"** in `draftsVM`.
11. **`revise` verdicts get `reject_all` wording** in `rulingVM.verdictNote`.
12. **Blind-research tone fires on zero research** — empty sources are labelled
    "Research was blind" rather than "no data".
13. **Current stage picked by array order, not time.**
14. **`cachedPct` divides without a zero guard** — `NaN%` when a window has no
    input tokens.

**Structural**

15. **All fourteen dashboard route files hardcode `D:/new orchestration`.**
16. **Neither dashboard reads the Buzz relay**, though `PORT-NOTES.md` §(c)
    specifies that it does.

**Recorded but not reproducible**

17. **Gemini turn completion.** Agents connect and consume tokens; no turn
    completion is ever logged. See [JOURNEY.md](JOURNEY.md#still-open).
18. **Draft `a4cb2c02`**, described in `HANDOFF.md` as unresolved
    `changes_requested`, has no artifact anywhere on disk. Unverifiable.

---

## 12. What is not built

- **Path B has never completed a cycle.** The relay, identities, personas and
  harnesses all exist and agents demonstrably wake, reason, research, correct
  each other and post — but no full run has finished on it.
- **Publishing beyond Twitter.** No LinkedIn, no Farcaster, no scheduling.
  Postiz was dropped deliberately.
- **The Hermes Multi-Platform Gateway** (Telegram + Slack) described in
  `MAC_MINI_SETUP.md` §6 does not exist on this machine. `hermes gateway start`
  is macOS setup documentation, not a running component here.
- **Live polling in the dashboards.** The seam exists; `mission-control` is
  fixture-only, and `hermes-mission`'s routes read files rather than the relay.
- **Claim-audit tier-inflation highlighting.** The `ClaimAuditRow` type exists;
  the view does not. This is the highest-value addition — a claim where
  `strategist_said` differs from `you_found` is the most dangerous failure mode
  in the pipeline.
- **Buzz workflow approval gates.** Buzz's own `request_approval` does not
  persist the approval token or suspend execution (its `VISION.md`, WF-08), so
  the human gate stays on Telegram.
- **A full Windows build of Buzz.** Only `buzz-relay`, `buzz-cli`, `buzz-agent`,
  `buzz-dev-mcp` and `buzz-acp` compile here.

---

## Appendix — knowledge base and assets

Not code, but the pipeline reads these and the gate encodes them.

| Path | Role |
|---|---|
| `files/00-INDEX.md` | Map of the knowledge base — start here |
| `files/04` | Brand voice, message library, the three narrative arcs |
| `files/05` | Audiences, personas, objections — **contains defect 1** |
| `files/08` | Facts ledger and claim safety: Tier A quotable, Tier B state carefully, Tier C future tense only |
| `files/10`, `files/11` | Competitor battlecards; current positioning and retired claims. **File 11 wins any conflict** |
| `marketing/` | 11 subdirectories of research — `seo` (19), `strategy` (16), `reports` (15), `cro` (11), `competitive` (10), `social` (9), `content` (7), `ads` (5), `analytics`/`brand`/`email` (2 each) |
| `design references/` | `theme.md` (light app system) plus `cl-*.png` product cards. The dark social theme has no written spec — `render_visual.py` is its only definition |
| `pipeline/config/marketing_config.json` | Competitor list and topic taxonomy |
| `pipeline/state/content_history.json` | Every run, with `verdict_outcome` and `hook_shipped`. Drives the anti-repetition blacklist |
| `Agent-Reach/` | Research tooling — OpenCLI, Exa, Jina Reader, yt-dlp, RSS |

**The rule that outranks everything:** Vanna is on testnet. No mainnet, no token,
no audit, no TVL. Every product claim must trace to `files/08`, and `files/11`
retires claims that used to be safe.
