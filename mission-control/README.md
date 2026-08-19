# Mission Control

Observability for the seven-agent content pipeline. Next.js 15, App Router,
TypeScript. Light, monospace, minimal — an instrument panel, not a landing page.

```bash
npm install
npm run dev      # http://localhost:3100
```

## Where the data comes from

`lib/data.ts` is the only seam. Today it reads `lib/fixture.json` — a captured
fixture whose shapes match the real sources exactly. Flip `source` to `'live'`
and implement three fetches:

| What | Source | Shape |
|---|---|---|
| Messages | Buzz relay, `GET /` (proxied at `/api/relay/*`) | Nostr kind-9 events |
| Cost | `pipeline/logs/vertex-calls.jsonl` | one JSON per line |
| Ledger | `pipeline/state/spend-ledger.json` | single object |

Research, draft and ruling payloads are not separate sources — they arrive as
JSON embedded in message text and are parsed client-side by `parsePayload`.

### Endpoints still needed from the backend

The relay serves messages, but the two file-backed sources need a thin
read-only server (a Next route handler is enough):

- `GET /api/calls` → contents of `vertex-calls.jsonl`, parsed to an array
- `GET /api/ledger` → contents of `spend-ledger.json`
- `GET /api/artifact/[name]` → serve PNGs out of `pipeline/state/`

## The run-id decision

**Runs are not delimited in the data.** The channel is a flat message stream
with no run identifier. This build derives boundaries client-side from the
conductor's run-open and run-close messages, and every run carries an
`inferred` flag that the UI shows as "boundaries inferred". Nothing presents a
guessed boundary as a recorded fact.

The durable fix is a `run_id` tag on each event, written by the conductor when
it opens a run. Once that exists, drop the inference and the flag.

## Decisions worth keeping

**`null` is not `0`.** The scout leaves engagement counts null when a research
tool is unavailable, and says so in `notes`. Rendering that as zero would turn
"we could not measure" into "we measured nothing", which is a different and
false claim. The `NoData` component exists so this can never happen by accident.

**Cached input tokens are shown separately.** Most input on every call is
cached; folding it into one total makes runs look far more expensive than they
are.

**Five stage states, not two.** `done`, `running`, `failed`, `skipped`,
`never reached`. A run that never got to the gate did not fail the gate.

**Cross-replies are a headline metric.** The three strategists are meant to
argue. Counting replies between two *different* strategists is the cheapest
honest test of whether a debate happened or three monologues did, and a run
with zero gets called out.

**Unparseable messages are shown raw, never dropped.** Payloads arrive embedded
in prose and are sometimes malformed. The message is still evidence.

## Not built yet

- Live polling (the seam is there; the fetches are not)
- Artifact image rendering (needs the file endpoint)
- Claim-audit tier-inflation highlighting — the type exists (`ClaimAuditRow`),
  the view does not. This is the highest-value thing to add next: a claim where
  `strategist_said` differs from `you_found` is the most dangerous failure mode
  in the pipeline.
