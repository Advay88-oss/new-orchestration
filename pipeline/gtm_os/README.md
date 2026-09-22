# The 13 GTM agents

Written from the code. Where this disagrees with `ARCHITECTURE.md`, the code is
what runs.

---

## Entry points

```bash
# terminal
python -m pipeline.gtm_os.autonomous_cycle                 # autonomous: A02 picks
python -m pipeline.gtm_os.autonomous_cycle --directive "…" # founder directive
python -m pipeline.gtm_os.autonomous_cycle --no-video      # skip Veo (faster)

# scheduler, every 6h, no directive
python pipeline/scheduler/configurable_scheduler_daemon.py --run-now gtm_cycle
```

The dashboard's **Launch Run** posts to `/api/run`, which spawns the same module
detached. A cycle takes two to four minutes, so the run appears in the
Observatory when it finishes, not when the button is pressed.

---

## The pass

`autonomous_cycle.py` calls the agents in sequence. No agent decides when
another runs.

| | Agent | Model | ~time |
|---|---|---|---|
| A01 | Intelligence Scout — live HTTP scrape | — | 15–45s |
| A02 | Opportunity Selector — picks the topic | gemini-3.8-flash | 5–7s |
| A03 | GTM Strategist — forms the strategy | gemini-3.8-flash | 5–10s |
| A04 | Machine Library — verifies the play | — | <1s |
| A05 | Campaign Engine — picks the vehicle | — | <1s |
| A06 | Channel Adapter — writes the posts | gemini-3.8-flash | 9–18s |
| A07 | Creative Director — picks an archetype | gemini-3.8-flash | 8–14s |
| A08 | Visual Synthesis — post visual | gemini-3.1-flash-image | 15–25s |
| A08 | Visual Synthesis — meme | gemini-3-pro-image | 25–52s |
| A09 | Video Production | veo-3.1-generate-001 | 75–98s |
| A07 | Creative Director — **judges the assets** | gemini-3.8-flash | 15–23s |
| A10 | Reviewer Firewall — claim + slop gates | — | <1s |
| A11 | Dispatch Worker | *always skipped* | — |
| A12 | Telegram Gateway — builds the packet | — | <1s |
| A13 | Learning Engine — reads outcomes back | gemini-3.8-flash | 3–5s |

A03 returning `NO_ACTION` or `KILL` ends the run and says why. A07's second pass
returning `REJECT` blocks it.

**A healthy cycle reports 12/13, not 13/13.** A11 dispatches only what a human
has approved, and no human has seen the run at that point. That is the design.

---

## The runtime

Every agent reaches its model through `agent_runtime.py`. Before it existed each
agent had a private `call_gemini_brain` with its own silent `except: return
None`, and a failed call fell through to canned output while the run still
reported success.

```python
brain(prompt, agent=, role=, system=, json_out=)   # raises BrainError
brain_json(...)                                     # parses, raises on bad JSON
brain_vision(prompt, images=[...])                  # the judge's eyes
```

Routing is by **role**, not URL — one table instead of thirteen hardcoded
strings. Failure is **raised, not returned**, so a caller has to decide in
writing what a missing answer means.

Journal, written by the same module:

```
record(AgentCall)  -> calls.jsonl    every model call, including failures
record_stage(...)  -> stages.jsonl   every agent, including the six with no model
```

---

## Models

| Role | Model | Transport | Used by |
|---|---|---|---|
| `reasoning` | `gemini-3.8-flash` | API key from `pipeline/.env`, falling back to a local Vertex proxy on :8900 | A02, A03, A06, A07, A13 |
| `image` | `gemini-3.1-flash-image` | Vertex Model Garden (ADC) | A08 post visual |
| `meme` | `gemini-3-pro-image` | Vertex Model Garden (ADC) | A08 meme, flat archetypes |
| `video` | `veo-3.1-generate-001` | Vertex `predictLongRunning` + poll (ADC) | A09 |

Override with `VANNA_GTM_MODEL_REASONING` / `_IMAGE` / `_MEME` / `_VIDEO`.

> **"nano banana pro" is not a model id.** `nano-banana-pro-preview` 404s on
> Model Garden. The id the publisher serves is `gemini-3-pro-image`.

Reasoning runs on an API key; image and video run on ADC. An expired
`gcloud auth application-default login` therefore takes out A08 and A09 and
leaves everything else working — a partial failure the journal reports correctly.

---

## Per-agent notes

**A01 — `gtm_os/live_scout.py`.** Five sources in a thread pool, 45s each:
Google News, docs/blogs, Reddit RSS, Telegram mirrors, the X bridge. A source
that fails contributes **nothing** — the old Reddit fallback invented a post with
a fake permalink and a fabricated loss figure. Archive rows are re-stamped
`ARCHIVE` so nothing mistakes a fortnight-old record for today's news.

**A02 — `autonomous_cycle._select_signal`.** Returns the pick *and why not each
of the others*. The rejections were being discarded; they are what make the
choice inspectable. Skipped when a directive is supplied.

**A03 — `gtm_orchestration/gtm_strategist.py`.** Deterministic kill check first,
then one reasoning call. On model failure returns `HUMAN_REVIEW_REQUIRED`, never
a canned strategy. Was a three-branch `if/else` with every field a literal.

**A04 — `gtm_machines/machine_library.py`.** Three incompatible id schemes
existed for the same plays, so every lookup missed the DB and fell through to a
hardcoded whitelist with invented counts. Normalised; 8 of 10 verify on evidence.

**A06 — `gtm_content/channel_adapter.py`.** X, LinkedIn and Reddit in one pass.
On failure falls back to deterministic synthesis but records **degraded**.
`ContentCreator` used to return posts as string literals; it now delegates here.

**A07 — `gtm_creative/archetype_director.py` + `gtm_os/creative_judge.py`.**
Runs twice. Directs, then judges the actual pixels — grading a brief grades your
intentions. A `REJECT` blocks the run. The last two archetypes are **removed from
the candidate list** before it chooses (`state/recent_archetypes.json`), not
discouraged in a prompt.

**A08 — `gtm_creative/archetypes.py`.** Ten archetypes; **four never reach an
image model** because a ledger and a proportional bar are arithmetic. The model
draws shapes only; every word is composited with PIL using the exact strings
passed in. The docs.vanna.finance hero gradient is hardcoded — the model never
decides the background.

**A09 — `autonomous_cycle.render_video`.** Superseded. See
`pipeline/brain/knowledge/motion-direction.md`, prototyped in
`gtm_creative/motion.py` and `film.py`.

**A10 — `channel_reviewer.py` + `creative_validator.py`.** Deterministic on
purpose: a gate that can reason can be reasoned out of blocking.

**A13 — `gtm_learning/learning_engine.py`.** The engine alone is a group-by and
a weight nudge. The model audits its own adjustment for sample size, which is
what makes the "model-backed" label honest.

---

## State

```
pipeline/state/gtm_runs/<RUN-ID>/
  calls.jsonl    one row per model call — failures included
  stages.jsonl   one row per agent — including the six with no model
  summary.json   signal, selection + rejections, strategy reasoning, posts,
                 archetype, creative review, artifact paths, token totals
```

| Path | What |
|---|---|
| `pipeline/brain/db/` | Brain DB. One `VANNA_BRAIN_ROOT` override replaced ~20 hardcoded absolute paths. |
| `pipeline/brain/knowledge/` | Approved claims, positioning, audience, objections, motion direction. |
| `pipeline/brain/docs/` | 40 mechanism pages cached from docs.vanna.finance, refreshed daily. |
| `state/recent_archetypes.json` | Drives the anti-repeat rule. |
| `state/panels/` | Ideas and Memes feeds, written by the cycle. |
| `state/.render/` | Video frame scratch. On D: deliberately — the system temp dir is on C:, which hit 100%. |

---

## Dashboard

`hermes-mission/`. Every surface reads the run journal; nothing is fixtured.

```
GET  /api/gtm/agents                  all 13, live status, model, tokens
GET  /api/gtm/runs                    run history
GET  /api/gtm/run/[id]                full detail; serves a run IN FLIGHT
GET  /api/gtm/artifact/[id]/[kind]    visual | meme | video
POST /api/run                         spawns a detached cycle
```

---

## Autonomy

`gtm_cycle` in `config/scheduler.yaml`, every 6h, **no directive** — which is
what makes it autonomous rather than merely scheduled.

Registration is a manual step, from an elevated shell:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\install-scheduler.ps1
```

---

## Open

- **A09 renders the wrong genre** — still cinematic Veo on every cycle, ~80s and
  the cost, against a rejected direction. Replacement designed, not wired in.
- **Cost is unpriced.** Tokens are measured and real; no rate table is wired, so
  the dashboard says "cost unpriced" rather than showing an invented figure. The
  Runs table used to price a run as `0.008 + duration_s * 0.0006`.
- **A05 and A10 are thin** — both work, neither examined as closely as the rest.
- **The C: volume is full** (777MB free at last check). Anything defaulting to
  the system temp dir will fail.
