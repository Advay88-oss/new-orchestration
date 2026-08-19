# Mission Control — port notes

Port of the bundled `Mission Control.html` component to Next.js (App Router,
TypeScript). Port, not redesign: no spacing, colour, copy, layout or component
changes.

## How fidelity was verified

Not by eye. Both versions were served side by side (original on `:3100`, port on
`:3000`), and a DOM walker captured every element's tag, own text, `title`,
bounding box (`x`/`w`/`h`) and 50 computed style properties, then diffed node by
node.

| View | Nodes (original / port) | Non-clock differences |
|---|---|---|
| Live debate | 210 / 210 | 0 |
| Lifecycles | 218 / 218 | 0 |
| Runs | 236 / 236 | 0 |
| Run detail | 951 / 951 | 0 |
| Posts | 471 / 471 | 0 |
| Agents | 260 / 260 | 0 |
| Cost | 222 / 222 | 0 |
| Backend note | 136 / 136 | 0 |

Repeated at 1440px and 1024px. The only diffs reported were values that depend on
wall-clock time and so differ between two tabs rendered seconds apart: the poll
countdown (`next in Ns`), elapsed times on the still-running R-08-05, and the
lifecycle segment `flex-grow` ratios, which differ in the sixth significant digit
because the running run's total duration keeps growing.

The fixture conversion was verified separately: the original `mission-data.js`
was evaluated in a VM, the compiled `lib/mission-data.ts` was required, and the
two were compared as JSON — **99,018 bytes, identical**; 5 runs, 50 messages,
total cost `3.64399` on both sides.

Other checks: no horizontal page scroll in any view at 1024px (`scrollWidth ===
clientWidth` everywhere); only the run table (860px in a 712px box) and the
claim-audit table (720px in a 654px box) scroll, each inside its own card; no
64-hex pubkey appears anywhere in the DOM in any view; `next build` and
`tsc --noEmit` pass clean; no `any` in the codebase; no console errors or
warnings.

Behaviour verified live: poll countdown ticks, Pause freezes it at `paused`,
Resume restarts it, 10s/15s/60s all switch; message/draft/post expand and
collapse; clicking a run row opens that run (row 3 → R-08-03, headline
`reject_all — nothing cleared 70`); post filters return All=14, Selected=3, Not
selected=6, Killed=3, Awaiting ruling=2 — identical to the original; the relay
probe flips `not connected` → `unreachable` without throwing. The three props
were exercised too: `capUsd={4}` gave `$3.6440 / $4.00 · approaching cap`,
`debateEdges="rail"` hid the matrix, and a grey `arcPalette` recoloured the arcs.

---

## (a) What could not be reproduced exactly

**1. The monospace font-family string.**
The original wrote `font-family: 'JetBrains Mono', monospace` literally.
`next/font/google` hashes the family name at build time
(`__JetBrains_Mono_05cb7b`), so that literal no longer resolves. Every
monospace element instead uses `var(--font-jetbrains-mono), monospace`, exported
once as `MONO` in `lib/colors.ts`. Same font, same weights, same rendering — only
the CSS string differs. The prompt required `next/font/google`, and there is no
way to keep the literal name with it.

**2. `adjustFontFallback` had to be turned off.**
With next/font's default, an auto-generated metric-adjusted fallback font is
inserted ahead of `monospace`/`sans-serif` in the stack. Glyphs outside the latin
subset — `●` (U+25CF) in the sidebar's live badge and `→` (U+2192) in the Runs
banner link — then rendered at different widths than the original, which fell
through to the plain generic families. Setting `adjustFontFallback: false` on
both fonts restores the original's stack and made those two nodes match exactly.
This is closer to the original, which loaded plain Google Fonts with no metric
adjustment.

**3. `sc-interp` wrapper spans are gone.**
The original's template runtime wrapped every `{{ }}` interpolation in an
unstyled `<span class="sc-interp">`. These are artifacts of that engine, carry no
styles, and have no layout effect. React renders the text directly. The node
counts above are measured with those wrappers normalised away; without that
normalisation the original reports 320 nodes on the Runs view to the port's 236,
all of the difference being empty spans.

**4. Hover states are JavaScript, not CSS.**
The original used a `style-hover="..."` attribute alongside the inline `style`.
Inline styles cannot express `:hover`, so `components/Hover.tsx` merges the hover
style on `onMouseEnter`/`onMouseLeave`. Same result, and it keeps the "everything
is an inline style object" constraint intact.

**5. A global stylesheet exists.**
`app/globals.css` carries the original `<helmet>` block verbatim — the box-sizing
reset, body font, `a:hover`, `::selection`, and the scrollbar rules. These are
pseudo-element and pseudo-class selectors that inline styles cannot express. It
is a plain stylesheet, not CSS modules.

---

## (b) Believed bugs, left untouched

1. **Draft expand state leaks across runs.** Draft bodies key their expand state
   on `"draft:" + arc`, with no run in the key (`lib/viewmodel.ts`, `draftsVM`).
   Posts do it correctly (`"post:" + runKey + ":" + arc`). Expand a
   `risk-relief` draft in one run, switch runs, and the same arc's draft is
   already expanded there.

2. **Latent crash in the artifact panel.** `artifactVM` reads
   `run.ruling.winner.arc` whenever a ruling exists, but a `reject_all` ruling
   has `winner: null` (R-08-03). It does not fire today only because a rejected
   run never has an artifact, so the function returns early. Preserved with a
   non-null assertion and a comment at the call site.

3. **Overlapping stage spans double-count the timeline.** In R-08-01 and R-08-03,
   `debate` is `skipped` and `ruling` is `done` over the *same* interval
   (R1_START+358→604, R3_START+470→812). The Lifecycles timeline sizes segments
   by real elapsed seconds, so that period is counted twice and those runs' bars
   sum past their own duration.

4. **`Math.max` on an empty score list.** `rulingVM`'s non-ship branch calls
   `Math.max.apply(null, v.scores.map(...))`, which returns `-Infinity` and
   renders "Highest was -Infinity" if a ruling ever arrives with no scores.

5. **Singular "pitch" regardless of count.** `draftsVM` builds
   `broken + " pitch could not be parsed"` — reads wrong the moment two pitches
   in one run fail to parse.

6. **"Revise" verdicts get reject_all wording.** `rulingVM.verdictNote` has only
   two branches: ship, and everything else says "Nothing cleared 70." A `revise`
   verdict would be described as a rejection. `verdictLabel` handles all three.

7. **Blind-research tone fires on no research.** In `researchVM`,
   `blind = nulls === srcs.length` is `true` when `srcs` is empty, so a payload
   with zero trends would be labelled "Research was blind" rather than "no data".

8. **Current stage is picked by array order, not time.** `live.stageLabel` takes
   `.filter(active || done).slice(-1)[0]`. With the overlapping spans in item 3,
   or any out-of-order stage, this reports the last stage in the array rather
   than the most recent one.

9. **`cachedPct` divides without guarding zero.** Cost view renders
   `Math.round(cachedTok / inTok * 100)` — `NaN%` if a window has no input
   tokens.

---

## (c) Backend endpoint contracts coded against

All read-only, all local, all JSON. Nothing writes. Wired in `lib/api.ts` behind
`USE_FIXTURE`; flip it to `false` to read the real backend. Routes are built by
`ROUTES` and match the Backend note view verbatim.

| Route | Returns | Notes |
|---|---|---|
| `GET /api/messages?channel=<uuid>&since=<unix>&limit=500` | `NostrEvent[]` | Raw Nostr events, unchanged, so the client parses defensively. `since` makes polling cheap. |
| `GET /api/identities` | `Record<pubkey, agentName>` | Sent once. The client never renders hex and never guesses who spoke. |
| `GET /api/spend` | `{ cap_usd: number, remaining_usd: number, started: string }` | `spend-ledger.json` verbatim. |
| `GET /api/calls?since=<iso>` | `VertexCall[]` | `vertex-calls.jsonl` as an array. **Must** keep `cachedContentTokenCount` and `rewritten_from` — both change what the numbers mean. |
| `GET /api/agents/status` | `Agent[]` | Per-agent log tail with the last `subscribed`, `agent_returned` and error line parsed out. Without it, live status is a guess from silence. |
| `GET /api/artifacts/<name>.png` | `image/png` | Serves `pipeline/state/*.png`. Until it exists the artifact panel can only compose the `visual_brief`, not show the render. |
| `GET /api/review/<draft_id>` | `Review` | The `drafts \| approved \| rejected` JSON for one draft, with status and the reviewer's reply. |

Exact response types are in `lib/types.ts` (`NostrEvent`, `VertexCall`, `Agent`,
`Review`, plus `SpendLedger` in `lib/api.ts`).

**One thing the endpoint list does not solve.** None of these carry a run
identity, so `loadMissionData()` still has to infer run boundaries from conductor
prose. That inference is isolated in `lib/api.ts` rather than spread through the
views, so when the conductor starts stamping a `run` tag the change lands in one
place and the "inferred" chips come out.
