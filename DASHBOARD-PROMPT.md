# Prompt — Mission Control dashboard

Paste everything below the line into a fresh frontend-generation session.

---

Build **Mission Control**, a local dashboard for watching an autonomous
multi-agent content pipeline run. Light theme, minimal, sleek. It is an
observability tool for one operator watching seven agents work — not a marketing
page, not a SaaS console.

## What the system being watched actually is

Seven AI agents with separate identities work in a shared chat channel on a
local relay. They research live trends, argue three competing narrative
positions in the open, judge the drafts, render a visual, pass a compliance
gate, and send the winner for human review. Everything they say to each other is
a signed message in one log.

The seven agents, and why each matters on screen:

| Agent | Role | Distinct because |
|---|---|---|
| `conductor` | Opens a run, dispatches, calls the bucket, closes | The only one who decides *whether* to post at all |
| `trend-scout` | Live research, why posts perform, keywords, competitor content | Produces evidence, never copy |
| `strategist-capital-efficiency` | Arc: "Your collateral is doing one job. It should be doing six." | Competes with the other two |
| `strategist-risk-relief` | Arc: "Leverage is easy. Not getting liquidated is the hard part." | Competes with the other two |
| `strategist-agentic-credit` | Arc: "Agents can pay. Agents can't borrow." | Competes with the other two |
| `editorial-judge` | Scores drafts, picks one or kills them all | Default posture is rejection |
| `visual-creator` | Winning brief → 1080×1080 card | Produces the only image artifact |

The three strategists are **rivals**. The single most important thing this UI
must convey is whether they actually argued with each other or just posted in
parallel. Design for that.

## The lifecycle, and the one thing missing

A run flows:

```
kickoff → research → bucket call → three pitches (parallel)
       → debate → ruling → visual → compliance gate → human review → shipped | killed
```

**Important gap you must design around:** there is currently no run identifier.
The channel is a flat message stream; runs are not delimited in the data. Do not
pretend otherwise. Either:

- derive run boundaries client-side from the conductor's run-open / run-close
  messages and show them as *inferred* (say so in the UI), or
- specify the small backend change you need (e.g. a `run_id` tag on each event)
  and build against that shape, clearly marked as a required change.

Pick one, state which, and be explicit. A dashboard that silently guesses run
boundaries and presents them as fact is worse than one that admits the seam.

## Data sources — real shapes, observed

**Messages** — `GET http://127.0.0.1:3000` relay, or shell out to
`buzz messages get --channel <uuid> --limit N`. Raw Nostr events:

```json
{"content":"...","created_at":1786129827,
 "id":"6463d24c...","kind":9,
 "pubkey":"0879a27506498637...",
 "tags":[["h","31098616-3d0b-4202-86b4-96bfd36680cd"]]}
```

`pubkey` is a 64-char hex identity. Map it to an agent name — never show raw
hex to a human. `created_at` is unix seconds. Threading, where present, is in
`tags`.

**Spend ledger** — `pipeline/state/spend-ledger.json`:

```json
{"spent_usd":0.033772,"calls":3,"input_tokens":62991,"output_tokens":1138,
 "started":"2026-08-08T16:28:05Z","cap_usd":10.0,"remaining_usd":9.9662}
```

**Per-call cost log** — `pipeline/logs/vertex-calls.jsonl`, one JSON per line:

```json
{"ts":"2026-08-08T15:57:10Z","model":"gemini-2.5-flash",
 "rewritten_from":"gemini-3.5-flash",
 "usage":{"promptTokenCount":8557,"candidatesTokenCount":1,
          "cachedContentTokenCount":8480},
 "cost_usd":0.004326,"spent_total":0.004326}
```

Note `cachedContentTokenCount` — a large share of input is cached. If you show a
token breakdown, show cached separately or the numbers mislead.

**Research payload** — posted by `trend-scout` into the channel as JSON:

```json
{"scanned_at":"...","trends":[{"id":"kebab-slug","headline":"...",
 "type":"crypto-native|mainstream-culture|competitor-move",
 "momentum":"rising|peaked|dead|evergreen","window_hours":36,
 "sources":[{"platform":"x","url":"...","engagement":{"likes":0,"replies":0}}],
 "why_it_works":{"hook_category":"contrarian","hook_text":"...",
   "format":"thread","virality_pattern":"counter-narrative",
   "stepps":{"social_currency":7,"triggers":9,"emotion":6,"public":8,
             "practical_value":4,"stories":5},
   "engagement_shape":"reply-heavy, low link clicks"},
 "vanna_hooks":["..."],"evidence":"a real quote"}],
 "competitor_content":[...],"keywords":[...],"notes":"what failed"}
```

`engagement` is often `null` — the scout refuses to invent numbers when a tool
is unavailable, and says so in `notes`. **Render null engagement as an explicit
"no data" state, never as zero.** Zero is a measurement; null is an absence, and
conflating them is how a dashboard starts lying.

**Draft payload** — posted by each strategist:

```json
{"arc":"risk-relief","trend_id":"...","rationale":"why this arc reads it best",
 "posts":[{"platform":"x|linkedin","template":"one of 9, by name",
   "hook":"first 7 words","body":"full copy","thread":["..."],
   "persona":"P1|P2|P3|P5",
   "claims":[{"text":"the claim","tier":"A","source":"which fact in file 08"}],
   "stepps_self_score":{...},
   "visual_brief":{"type":"infographic|quote-card|stat-card",
     "headline":"...","emphasis_phrase":"...","subhead":"...",
     "data":[{"label":"...","value":"...","note":"..."}],
     "disclaimer":"must mention testnet"}}]}
```

**Ruling** — posted by `editorial-judge`:

```json
{"verdict":"ship|revise|reject_all",
 "winner":{"arc":"...","platform":"x","final_hook":"...","final_body":"...",
           "final_thread":["..."],"visual_brief":{...}},
 "scores":[{"arc":"capital-efficiency","total":78,
   "breakdown":{"claim_integrity":27,"hook":12,"arc_coherence":15,
                "voice":13,"trend_fit":5,"virality":6},
   "killer_issue":"the single biggest problem"}],
 "graft":{"took":"the closing line","from":"agentic-credit","why":"..."},
 "claim_audit":[{"claim":"...","strategist_said":"A","you_found":"A",
                 "verified_against":"file 08 line ref"}],
 "send_back_notes":"exactly what must change"}
```

Scoring is out of 100 across six dimensions; **ship threshold is 70**.

**Visuals** — PNGs at `pipeline/state/*.png`, named `<date>-<arc>-<type>.png`.

**Review state** — `pipeline/state/drafts|approved|rejected/<draft_id>.json`,
each with `status` (`awaiting_review` / `changes_requested` / `approved` /
`rejected`) and the reviewer's reply.

**Agent process logs** — `pipeline/logs/agents/<agent>.log`. Useful signals:
`subscribed to channel` (agent is live), `agent_returned ... outcome="error"`
(a turn failed), and the error text.

## Views to build

**1. Run list.** Every lifecycle as a row: when, what triggered it, which bucket
the conductor called, the outcome (shipped / killed / died mid-run), duration,
total cost. Runs that died mid-way are as informative as ones that shipped —
give them equal visual weight, not an error styling that hides them.

**2. Run detail — the main screen.** For one lifecycle:

- **Stage rail**: the pipeline stages with the current one marked, showing
  elapsed time per stage. Stages that were skipped or never reached must read as
  *not reached*, distinct from *failed*.
- **The debate**: the message thread, grouped by agent, showing who replied to
  whom. This is the centrepiece. A reader should be able to tell at a glance
  whether the three strategists engaged each other's arguments or posted three
  monologues. Consider showing reply edges explicitly.
- **Research panel**: trends with momentum, the why-it-works breakdown, STEPPS
  as a small radar or bar set, keywords, and prominently the `notes` field about
  what failed. A run where research was blind is a run whose conclusions are
  weaker, and the UI should make that unmissable.
- **Draft comparison**: the three arcs side by side, each with its hook, claims
  (with tier badges — A / B / C), and self-scored STEPPS. The judge's score
  overlays this once it lands.
- **Ruling**: verdict, per-arc score breakdown, the killer issue for each, what
  was grafted from whom, and the claim audit. Highlight any claim where
  `strategist_said` differs from `you_found` — that is a tier inflation and the
  most dangerous failure mode in this pipeline.
- **Artifact**: the rendered PNG with its disclaimer legible.
- **Gate + review**: pass/fail with violations, then the Telegram review state.

**3. Agent roster.** Seven agents, live status (connected / thinking / idle /
errored), what each is working on, turns taken this run, tokens and cost
attributed to each. Show each strategist's arc line under its name — the arcs
are the point of the design.

**4. Cost.** Spend against the $10 cap as the headline number, then per-run,
per-agent, and per-stage breakdowns. Cached vs fresh input tokens separated. A
clear, calm indication when the cap is approaching — this exists because an
uncapped run once produced a surprise bill, so the number should be legible at a
glance without being alarmist.

## Design direction

- **Light, minimal, generous whitespace.** Content is dense and text-heavy;
  the layout's job is to make long agent messages readable, not to decorate.
- **Type does the work.** A clear hierarchy beats borders and cards everywhere.
  Long-form agent prose needs a comfortable measure (~70ch) and real line height.
- **One restrained accent.** Use colour to encode meaning — agent identity,
  claim tier, verdict — not for ornament. The three arcs each get a stable hue
  used consistently everywhere they appear.
- **Monospace for data**, proportional for prose. Token counts, costs, hashes
  and IDs align in tabular numerals.
- **No fake liveliness.** No spinners implying progress you cannot measure, no
  animated counters, no gradient hero. This is an instrument panel.
- **Empty and unknown states are first-class.** "No data" ≠ "zero". "Not
  reached" ≠ "failed". "Still running" ≠ "stalled". Design all three.
- Responsive down to a laptop screen; this is not a mobile product.

## Technical

- Single-page app, runs locally, reads from the local relay and the JSON/JSONL
  files above. Assume a thin read-only backend can be added to serve them —
  specify the endpoints you want.
- Polling is fine; live push is not required. Make the refresh interval visible
  and let the operator pause it.
- Handle a message body of several thousand characters gracefully — collapse
  with expand, never truncate silently.
- JSON payloads arrive embedded in message text and are sometimes malformed or
  partial. Parse defensively and show the raw text when parsing fails, rather
  than dropping the message.
- Timestamps are unix seconds (messages) and ISO-8601 Z (logs). Show local time,
  keep UTC in a tooltip.

## Do not

- Do not invent metrics the data cannot support — no "agent efficiency score",
  no sentiment gauge, no productivity index.
- Do not show raw pubkeys, private keys, or token values anywhere.
- Do not render zero when the value is null.
- Do not present inferred run boundaries as if they were recorded.

## Deliver

A working frontend plus a short note listing: the endpoints you need from the
backend, any data the current sources cannot provide, and the run-id decision
you made and why.
