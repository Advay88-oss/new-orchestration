# The journey

An engineering account of how the Vanna autonomous content pipeline was built:
what broke, what the wrong theory was before the right one, and what is still
broken. Not a changelog and not a success story.

Every incident below is sourced. Where a claim comes from prose written at the
time rather than from an artifact still on disk, it says so. Dates come from
file timestamps and `pipeline/state/content_history.json`; where no date was
recorded, none is given.

**Verification status of this document.** Version numbers, port bindings, route
behaviour, gate behaviour and run counts in this document were re-checked
against the machine on 2026-08-10. Incidents drawn from `HANDOFF.md` that
predate that check and left no artifact are marked *recorded, not reproducible*.

---

## Phase 1 — Standing up the environment

### Postgres rejected every connection with an SSL error

**Symptom.** `unexpected response from SSLRequest: 0x00` from every service
connecting to the Buzz Postgres container.

**What it looked like.** A TLS misconfiguration — the container requiring SSL,
or the client offering a protocol it would not accept. Every plausible fix at
that layer (`sslmode` variants, container config) was aimed at the wrong thing.

**Root cause.** `localhost` resolves to IPv6 `::1` on this machine, and
`wslrelay.exe` listens there. Docker's proxy listens on IPv4 `127.0.0.1`. The
connection was reaching a completely different process, whose reply was not
Postgres wire protocol at all — hence a byte sequence that looked like a broken
SSL handshake.

**Fix.** `127.0.0.1` in every service URL. Never `localhost`.

**Generalises to.** On Windows, a connection error from a Docker-published port
is a name-resolution question before it is a protocol question. The error text
will describe the wrong layer.

### Docker Desktop installed but would not launch

**Symptom.** Launch failed with `getting backend binary path: cannot find
registry key`.

**What it looked like.** A corrupt install or a missing WSL component.

**Root cause.** The installer had been given `--installation-dir` to keep the C:
drive free. It extracted every file to `D:\Docker` and silently skipped
registration — no `HKLM\SOFTWARE\Docker Inc.` key, no uninstall entry. The
install *looked* complete on disk.

**Fix.** Uninstall and reinstall without the flag. Docker Desktop 4.85 installs
per-user to `%LOCALAPPDATA%\Programs\DockerDesktop` with its uninstall entry
under HKCU, so looking for `C:\Program Files\Docker` or an HKLM key wastes time.
`--wsl-default-data-root=D:\DockerData` is safe and does keep image data off C:.

**Cost.** A full uninstall/reinstall cycle. The real install log is
`C:\ProgramData\DockerDesktop\install-cli-log-admin.txt`, not the stale one
under `%LOCALAPPDATA%\Docker`.

**Generalises to.** An installer flag that relocates files does not necessarily
relocate registration. "Files are present" is not "installed".

### `node -v` reported a version nvm did not manage

**Symptom.** `nvm use` failed with `'C:\Users\Advay' is not recognized`, and
`node -v` nonetheless answered — with a version nvm had never installed.

**What it looked like.** A stale shell, or nvm needing a reinstall.

**Root cause.** Two faults stacked. nvm4w 1.2.2 does not quote the space in the
profile path, so its own shim command was truncated at `C:\Users\Advay`. And
`C:\nvm4w\nodejs` — the link target nvm points PATH at — did not exist at all,
so PATH fell straight through to a stray `AppData\Local\hermes\node` install.
The reported version was real; it just came from a Node nobody was managing.

**Fix.** A junction (`mklink /J`) at the missing path. A junction needs no
admin, unlike the symlink nvm tries to create. **Re-run it after any nvm version
change.** Verified current on 2026-08-10: `node v24.19.0`, `npm 10.9.2`.

**Generalises to.** When a broken tool still returns a plausible answer,
find out where the answer came from before trusting it.

### The Buzz workspace does not build on Windows

**Symptom.** Three separate failures in one workspace: `sherpa-onnx` (voice)
failed outright, the `windows` crate crashed `rustc` with
`STATUS_STACK_BUFFER_OVERRUN`, and `buzz-test-client` panicked the compiler.

**What it looked like.** A broken toolchain or missing C++ build tools.

**Root cause.** Specific crates are incompatible with this build environment.
The toolchain was fine.

**Fix.** Stop building the workspace. Build only what the pipeline needs:
`buzz-relay`, `buzz-cli`, `buzz-agent`, `buzz-dev-mcp`, `buzz-acp`. Hermit
(`bin/activate-hermit`, `just bootstrap`) does not work here either; use the
system toolchain directly.

**Separate trap, same session.** `CARGO_HOME` must be a Windows path.
`CARGO_HOME=/d/cargo-home` (a Git Bash path) stalls cargo with **zero output** —
no error, no progress. `D:\cargo-home` works.

**Generalises to.** A monorepo's build target is a choice, not an obligation. And
a tool that produces no output at all is more likely being handed a path it
cannot parse than doing slow work.

### C: reached zero bytes mid-build

**Symptom.** Builds failing for unrelated-looking reasons; C: at 0 bytes free.

**Root cause.** Accumulated package-manager caches across three ecosystems.

**Fix.** `npm cache clean --force`, `yarn cache clean`, `pip cache purge` —
about 8 GB. These refill over time and are the first place to look next time.

---

## Phase 2 — Getting agents to actually behave like agents

### Agents connected, went online, and ignored everyone

**Symptom.** Each agent process started, subscribed, and reported online. Not
one ever responded to a message.

**What it looked like.** A message-parsing failure, or the relay not delivering.
Debugging effort went into the event payloads.

**Root cause.** `buzz-acp` defaults to `--respond-to owner-only`. With no owner
set, that predicate matched nothing, so every event was dropped before the agent
ever saw it. A healthy-looking agent doing nothing.

**Fix.** Always pass `--respond-to anyone`.

**Generalises to.** Default-deny security postures in agent harnesses present as
silence, not as errors. When an agent does nothing, check what it was permitted
to hear before checking whether it can think.

### The scout's research quietly degraded to nothing

**Symptom.** The trend scout returned research with no engagement data, having
apparently used plain web search instead of the tools it was given.

**What it looked like.** The research tools rate-limiting or failing internally.

**Root cause.** The scout composed `export PATH=... && opencli ...`. That
compound string does not match `Bash(opencli:*)` in
`.claude/settings.local.json`. Permission mode was `dont-ask`, so the call was
denied — and the agent, behaving reasonably, fell back to a tool it *was*
allowed. Nothing errored. The output looked like research, and was worthless.

**Fix.** The launcher puts tools on PATH so agents never need a compound
command.

**Generalises to.** This is the most dangerous failure class in the whole
project: a permission boundary that degrades output quality instead of failing
loudly. An agent with a fallback will always hide your misconfiguration.

### Seven parallel Opus agents exhausted a subscription session limit

**Symptom.** A working Claude run died mid-execution, after the scout and
conductor had completed.

**Root cause.** Seven parallel Opus agents under
`@agentclientprotocol/claude-agent-acp` hit a subscription session limit in
roughly 28 minutes.

**Fix.** None. This is a live constraint on the Claude runtime for sustained
parallel work, and it is the direct reason the Gemini runtime was pursued.

*Recorded in `HANDOFF.md`; not reproducible from artifacts on disk.*

### Every Gemini turn died on a missing API key that was not missing

**Symptom.** `Gemini API key is missing or not configured` on every turn, with
ADC working fine outside the harness.

**What it looked like.** Expired or misconfigured application-default
credentials. Time was spent on `gcloud` auth that was never broken. (Git Bash's
`gcloud` shim reports a reauth error while `gcloud.cmd` mints tokens fine —
which made a working setup look broken.)

**Root cause.** A protocol disagreement, not a credential one. Gemini CLI's
`--acp` mode advertises `authMethods` and expects the client to call
`authenticate`. `buzz-acp` has no auth flag and never calls it. Neither side was
wrong on its own; they disagreed about whose job authentication was.

**Fix.** `gemini_acp_shim.js` sits between them, performs the handshake, and
hands `buzz-acp` an already-authenticated agent. Confirmed working:
`buzz-acp` now sees `authMethods: []`, which is how you verify this — an empty
list means "already authenticated", not "no auth available".

**Still open.** See *Still open*, item 1: the shim solved auth and did not
produce a completed turn.

### Assumed model ids that do not exist

**Symptom.** `400 INVALID_ARGUMENT` on model names that looked current.

**Root cause.** `gemini-3.5-flash` does not exist on project
`sales-agent-504607`, nor do 3-flash, 3-pro or flash-latest. Only the 2.5 family
answers (probed 2026-08-08).

**Fix.** `MODEL_REWRITE` in `vertex_spend_proxy.py:65` rewrites wrong model ids
at the proxy rather than trusting every caller to get it right.

**Generalises to.** Probe the model list on the actual project. A newer number
is not a guarantee of availability.

---

## Phase 3 — Design decisions that came out of a failure

### Three monologues, not a debate

**Symptom.** The three strategists produced three parallel pitches. None
referenced another. The judge was choosing between essays written in isolation.

**Root cause.** A coordinator relayed messages between subagents. No strategist
ever saw a rival's pitch as an addressable message, so there was nothing to
answer.

**Fix.** Two changes, and both were needed. Agents became separate processes
with their own identities on a shared Buzz relay channel, so a strategist can
read a rival's pitch and answer it by name. And each strategist was **assigned**
one of the three narrative arcs from `files/04` — capital-efficiency,
risk-relief, agentic-credit — rather than choosing. Agents free to choose
converge on the same safe angle; agents locked to fixed positions have to argue.

**Measured, not assumed.** Cross-replies between two *different* strategists is
the metric the dashboard reports for exactly this reason, and a run with zero of
them is called out on screen. On the fixture data currently loaded, that count
is **0** — the dashboard's own headline reads "three parallel monologues, not a
debate". The architecture fix is in; the evidence that it worked at scale is
not yet on disk.

### AI image generation was tested for readable text, and rejected

**Symptom.** Generated cards contained illegible pseudo-glyph text where the
headline should be.

**What was actually tried.** FLUX, given a Vanna card prompt containing an exact
headline and an exact hex colour, returned a photorealistic portrait with
unreadable text. Given pure-abstract-texture prompts, it returned usable
backgrounds.

**Fix.** Split the job by what each tool is good at: AI makes the wallpaper, CSS
makes the poster. `render_visual.py` renders a brief to HTML and screenshots it
with headless Chrome (`--headless=new --screenshot`, 180s timeout,
`render_visual.py:218`). Every readable character is deterministic.

**Generalises to.** Test the specific capability you need, not the general one.
"Can it make an image" and "can it place these 9 characters exactly" are
different questions with different answers.

**Side effect worth recording.** The dark social theme was derived from
`design references/cl-11` and `cl-16`. `design references/theme.md` documents
the *light* app system — the dark social variant had no written spec before
this, and still has none beyond the renderer.

### A GCP budget was mistaken for a spending cap

**Symptom.** An unexplained ~$109 GCP bill a few days before 2026-08-08.

**What it looked like.** Nothing, until the bill arrived — which is the point.

**Root cause.** GCP budgets are *alerts*. A $10 budget emails you while the
meter keeps running. The only native hard stop is a Cloud Function that detaches
the billing account, which on project `sales-agent-504607` would also kill an
unrelated sales-agent workload — so it was off the table.

*The bill is recorded in `HANDOFF.md` as the most likely explanation, not as a
confirmed attribution.*

**Fix.** `vertex_spend_proxy.py`, a local proxy every agent call passes through.
Cap is `VERTEX_CAP_USD`, default `$10.00` (`vertex_spend_proxy.py:47`); it
returns HTTP 402 once reached.

**The bug inside the fix.** The first metering pass read `usageMetadata` only
from single-object responses. Streaming and SSE responses were missed, so those
calls were charged a flat pessimistic rate — burning the budget roughly 10×
too fast. A cap that trips at 10% of the real spend fails as surely as no cap.

**Deliberate design choice.** A corrupt ledger reads as **exhausted**, not as
fresh (`vertex_spend_proxy.py:172` returns `spent_usd = CAP_USD` on a parse
failure). Fail closed. Current ledger: `$3.3290` spent over 369 calls since
2026-08-08.

**Generalises to.** Read what a budget feature actually *does*, not what its
name implies. And when you write the meter yourself, the response shapes you
forgot to handle are the ones that cost money.

---

## Phase 4 — Content correctness

### The gate is a blocking gate, and that was the point

Agents optimising for engagement drift into claims that are retired or false
for a testnet-stage protocol. `claim_safety_gate.py` exits 1 and the draft never
reaches a human — it is not a warning surface.

**How the rules are actually stored, because this is easy to get wrong.** The
rules are hardcoded Python lists in the script: `HARD_PROHIBITIONS`
(`claim_safety_gate.py:54`), `TIER_F` (`:172`), `RETIRED` (`:204`), `VOICE`
(`:248`). The docstring at `:5` says they are derived *from*
`files/08-facts-ledger-and-claim-safety.md` — that describes where they came
from when they were written. **The gate does not read `files/08` at runtime.**
Editing the facts ledger does not change what the gate blocks. Anyone who
assumes otherwise will believe they have tightened a control that has not moved.

### `files/05` still carries a retired claim — and the gate does not catch it

**Symptom.** The editorial-judge agent flagged, unprompted, that `files/05` line
14 lists "MCP-native" in the Agents row, contradicting `files/11` §10.1, which
retired it after Morpho Agents shipped MCP + CLI on mainnet in April 2026.

**Verified 2026-08-10, and worse than recorded.** The contradiction is still
live, and there are **two** occurrences, not one:
- `files/05-audiences-personas-and-objections.md:14` — "MCP-native ·
  Policy-bounded · On-chain track record"
- `files/05-audiences-personas-and-objections.md:47` — "MCP-native from day one"

`HANDOFF.md` records only line 14.

**The part nobody had checked.** The gate was tested against these exact
phrasings on 2026-08-10:

| Input | Result |
|---|---|
| `Vanna is MCP-native. Policy-bounded. On-chain track record.` | **PASS** |
| `MCP-native from day one, typed policy-bounded tools.` | **PASS** |
| `Vanna is the only protocol with MCP support.` | BLOCK `R-mcp-differentiator` |
| `Nobody else is building agent credit scores.` | BLOCK `R-category-claim` |

`R-mcp-differentiator` matches superlative and possessive framings — "first/only
… MCP", "MCP-native is our differentiator", "MCP is our moat". Bare "MCP-native"
as a feature bullet matches none of them. So a strategist that copies the phrase
straight out of `files/05` — a file it is instructed to treat as a source —
produces a draft the gate passes.

**Impact.** This is not a stale-doc nit. It is a source document contradicting
current positioning, in a form the automated control is blind to, in a file
agents read. The two defects only matter together, which is why neither was
caught alone.

**Status.** Unfixed. No code was changed while writing this document.

---

## Phase 5 — Running it, and what running it revealed

### The human review window is too short, and the history says so

**Symptom.** Runs completing, drafts dispatched, and nothing shipping.

**Evidence.** `content_history.json`, 13 runs recorded between 2026-08-09T08:50
and 2026-08-10T04:44:

| Outcome | Runs |
|---|---|
| `timeout` | 7 |
| `shipped` | 4 |
| `approved` | 2 |

Seven of those timeouts are consecutive, between 16:22 and 17:41 on 2026-08-09.

**Root cause.** `trendjack_news_orchestrator.py:445` hardcodes
`--timeout 120` on the review poll. `telegram_review.py` itself defaults to
3600s; the orchestrator overrides it down to two minutes. A human who steps away
for three minutes produces a `timeout`, and the run is recorded as if the
content failed.

**Generalises to.** When a machine waits on a human, the timeout is a product
decision, not a technical default. Two minutes encodes an assumption nobody
stated.

### A transient Telegram send killed a run that had already done all the work

**Symptom.** `trendjack_news_orchestrator.py` aborted at step 9 with
`json.decoder.JSONDecodeError: Expecting value: line 1 column 1 (char 0)` at
`trendjack_news_orchestrator.py:430`.

**What it looked like.** A malformed draft, or a bug in `telegram_review.py`.

**Root cause.** `telegram_review.py send` returned empty stdout. The orchestrator
calls `json.loads(tg_send_res.stdout)` with no retry and no guard for the empty
string. The identical command succeeded on a manual retry seconds later, so the
underlying fault was transient — the defect is the missing retry, not the send.

**Why it hurt more than it should have.** The crash landed *after* the safety
gate had passed and the visual had rendered. The run had completed every
expensive stage. It then died before step 12, so the script never wrote the run
to `content_history.json`. The record was reconstructed by hand afterwards; run
`dfda50d2` is in the history and in `pipeline/state/approved/` because a human
put it there, not because the pipeline did.

**Generalises to.** Cheap, transient, late-pipeline calls destroy expensive
completed work when they are not retried. Rank retry effort by what is upstream
of the call, not by how likely the call is to fail.

### The publishing bridge failed, then took the read path with it

**Symptom.** `opencli twitter post` returned `TIMEOUT` after 60s. Every
subsequent OpenCLI call — including read-only ones like `twitter whoami` —
returned `No SW`.

**What it looked like.** A rate limit or a session expiry on the Twitter side.

**Root cause.** Neither. `opencli auth status` still reported twitter
`logged_in: true`, and the bridge daemon on port 19825 was alive and answering
(`opencli browser twitter tab list` returned `[]` rather than failing). `No SW`
is the daemon reporting that no extension service worker is attached. The fault
is on the Chrome-extension side of the bridge; nothing in the pipeline was
involved.

**Verification that mattered.** Before retrying a post, the account timeline was
read to confirm no duplicate had been published. It had not — the newest tweet
was still the previous day's run. A publish step that times out is not a publish
step that failed; check before retrying.

**Status.** Unresolved. Draft `dfda50d2` is approved and unpublished.

### Dev servers that vanished with their shell

**Symptom.** `npm run dev` reported starting; nothing ever answered on the port,
and no `node.exe` process existed.

**Root cause.** The server was launched as a background job from a shell that
then exited, taking the process with it. The log file ended at the banner,
before Next had compiled anything — which is the tell.

**Fix.** Run it under a supervisor that outlives the shell. A `.claude/launch.json`
entry now defines `mission-control`, so it does not depend on a shell staying
alive.

---

## Phase 6 — The frontend port

This phase is unusually well documented: `hermes-mission/PORT-NOTES.md` was
written during the work and is the primary source for everything below.

### Fidelity was proved by diffing the DOM, not by looking

The port of `Mission Control.html` to Next.js was verified by serving both
versions side by side and walking the DOM — every element's tag, own text,
`title`, bounding box and 50 computed style properties, diffed node by node,
across eight views at 1440px and 1024px. Result: **0 non-clock differences**;
the only diffs were values that depend on wall-clock time. The fixture
conversion was checked separately by evaluating the original `mission-data.js`
in a VM and comparing to the compiled TypeScript as JSON — 99,018 bytes,
identical.

**Generalises to.** "Looks the same" is not a verification method for a port.
This is the right amount of rigour for work whose entire acceptance criterion is
*nothing changed*.

### Four things could not be reproduced exactly, and each has a reason

1. **The literal font-family string.** The original wrote
   `font-family: 'JetBrains Mono', monospace`. `next/font/google` hashes the
   family name at build time, so that literal no longer resolves; every
   monospace element uses `var(--font-jetbrains-mono), monospace` instead. The
   prompt required `next/font/google`, so this was unavoidable.
2. **`adjustFontFallback` had to be disabled.** next/font inserts a
   metric-adjusted fallback ahead of the generic family. Glyphs outside the
   latin subset — `●` (U+25CF) in the live badge, `→` (U+2192) in the Runs
   banner — then rendered at different widths than the original, which fell
   through to plain `monospace`. Turning it off restored an exact match. *This
   is the model for the level of detail worth capturing: a two-glyph
   discrepancy, traced to a font-loading default.*
3. **`sc-interp` wrapper spans are gone.** The original template runtime wrapped
   every interpolation in an unstyled span. They carry no styles and no layout
   effect, but they inflate node counts — 320 vs 236 on the Runs view — so the
   diff had to normalise them away or report 84 false differences.
4. **Hover states became JavaScript.** Inline styles cannot express `:hover`, so
   `components/Hover.tsx` merges hover styles on mouse enter/leave, preserving
   the "everything is an inline style object" constraint.

### Nine bugs were found and deliberately left in

`PORT-NOTES.md` section (b) records nine defects found during the port and left
untouched, because the brief was *port, not redesign*. Recording them instead of
fixing them was the right call for that task and the wrong thing to leave
undocumented — so they are carried forward here and in `ARCHITECTURE.md`. The
two that will bite first:

- **Draft expand state leaks across runs.** Draft bodies key expand state on
  `"draft:" + arc` with no run in the key (`lib/viewmodel.ts`, `draftsVM`).
  Posts do it correctly (`"post:" + runKey + ":" + arc`). Expand a `risk-relief`
  draft in one run, switch runs, and it is already expanded there.
- **A latent crash in the artifact panel.** `artifactVM` reads
  `run.ruling.winner.arc` whenever a ruling exists, but a `reject_all` ruling has
  `winner: null`. It does not fire today only because a rejected run never has an
  artifact, so the function returns early. It is preserved behind a non-null
  assertion with a comment at the call site — a tripwire, not a fix.

The remaining seven — double-counted timeline segments from overlapping stage
spans, `Math.max` on an empty score list rendering `-Infinity`, a hardcoded
singular "pitch", `revise` verdicts described with `reject_all` wording, a
blind-research label firing on zero research, current-stage picked by array
order rather than time, and `cachedPct` dividing without a zero guard — are
listed in full in `PORT-NOTES.md` section (b).

### The two dashboards diverged, and nothing on disk says which one wins

**Symptom.** Two Next.js apps, both named "mission control", both with a
seven-route `app/api/**` tree.

**Verified 2026-08-10:**

| | `mission-control/` | `hermes-mission/` |
|---|---|---|
| Next / React | 15.1.6 / 19.0.0 | 14.2.15 / 18.3.1 |
| Port | 3100 (`next dev -p 3100`) | 3000 (`next dev`) |
| Data seam | `source = 'fixture'` | `USE_FIXTURE = false` |
| Components | 3 | 12 + 8 views |

The route sets have the same seven names. `spend` and `calls` are byte-identical
between the two apps; `messages` and `identities` differ. This is a fork that
was never reconciled, and neither app declares itself canonical.

**Two findings that only appear when you read the routes.**

1. **Neither app reads the Buzz relay.** `PORT-NOTES.md` section (c) specifies
   `GET /api/messages` as returning raw Nostr events from the relay. The
   implementation reads `pipeline/state/drafts/*.json` off the filesystem and
   synthesises message objects from them. No route contains a relay URL, a
   WebSocket, or a `buzz` invocation. The endpoint contract and the
   implementation describe different systems.
2. **All fourteen route files hardcode `D:/new orchestration`.** Every route in
   both apps resolves absolute Windows paths. This directly blocks the migration
   described in `MAC_MINI_SETUP.md` — the dashboards cannot start on the Mac
   Mini without editing every route file.

### The run-boundary problem, and why it was left alone

Runs are not delimited in the data. The channel is a flat message stream with no
run identifier, so boundaries are derived client-side from the conductor's
run-open and run-close prose. Every run carries an `inferred` flag that the UI
renders as "boundaries inferred".

This was the right call: the inference is isolated in one file rather than
spread through the views, and nothing presents a guessed boundary as recorded
fact. The durable fix is a `run_id` tag written by the conductor when it opens a
run, after which the inference and the flag both come out.

**Generalises to.** When you must guess, isolate the guess in one place and
label it in the UI. Both halves matter.

---

## Phase 7 — The video arm: brand films

The GTM engine grew a video arm — launch films for Vanna and Auri, rendered with
Remotion (`D:/vanna-remotion/`) on a machine with no GPU. The through-line of this
phase is the same as Phase 3's: the failures were not in the rendering, they were in
mistaking a methodology for a source, and an alpha channel for transparency.

### npm and every render died on a "file" argument that was undefined

**Symptom.** `npm install` and `remotion render` both failed with
`ERR_INVALID_ARG_TYPE: The "file" argument must be of type string. Received
undefined`.

**What it looked like.** A corrupt package tree, or the space in
`D:\new orchestration` breaking a path — a project relocation to `D:/vanna-remotion`
was tried first and did not fix it.

**Root cause.** Node 24's promise-spawn reads `process.env.ComSpec` to find
`cmd.exe`; on this shell `ComSpec` was unset, so the "file" it tried to spawn was
`undefined`. Nothing to do with packages or the path.

**Fix.** Export `ComSpec="C:\\Windows\\System32\\cmd.exe"` (and `COMSPEC`) before any
npm/remotion call. This is now in every render command in the skill doc.

**Generalises to.** A spawn error naming an `undefined` *file* argument is a missing
shell-path env var, not your dependency tree. Read which argument was undefined before
reinstalling anything.

### Building the wrong brand, well

**Symptom.** After a full rebuild to a "premium video" spec — computed contour
substrate, held-frame reveal, disciplined motion — the user's reply was blunt: *not
using vanna logo, not using vanna colours.*

**What it looked like.** A quality problem. It was not; the craft was fine.

**Root cause.** A supplied visual-system spec document carried an example palette
(bone `#E9E6DF`, orange `#FF5C2B`, teal). I built to that palette as though it were
Vanna's brand. It was a *methodology* doc illustrating a method, not a brand ledger.
Vanna's real brand — dark `#0D0616`, violet `#703AE6`, rose `#FF007A` — was sitting in
`okf/brand/palette.md` the whole time, with the logo and font beside it.

**Fix.** Rebuild from the tenant's brand ledger: `okf/brand/palette.md` +
`okf-auri/brand/palette.md` give palette, logo path, and font (Plus Jakarta Sans for
Vanna, Geist for Auri). Two brand-film compositions (`VannaBrand`, `AuriBrand`) and a
combined one (`VannaAuriFilm`) now read from those values.

**Generalises to.** A design spec's illustrative palette is not the brand. When a doc
shows you a method, do not copy its example as if it were the client's identity —
read the identity from where the identity lives. This is Phase 3's "test the specific
capability" rule wearing a different hat: I answered "is this premium?" when the
question was "is this *Vanna*?"

### An alpha channel that was fully opaque

**Symptom.** The Vanna logo sat on the dark cards fine but showed a visible dark
rectangle once placed over the film's colored glow.

**What it looked like.** A blend-mode issue.

**Root cause.** `logo.png` was RGBA — so "has transparency" seemed safe — but every
pixel's alpha was 255, with a solid near-black box (`#131020`) painted behind the mark.
On a matching dark card it blended invisibly; over a gradient it did not.

**Fix.** Key it out: a PIL pass sets alpha from `max(r,g,b)` brightness, ramping 0→255
above the box. Auri's logo, checked the same way, was genuinely alpha-transparent and
needed nothing.

**Generalises to.** "Has an alpha channel" is not "is transparent." Sample the corner
pixels before trusting a PNG over a non-matching background.

### The contour field read as a ripple, i.e. as decoration

**Symptom.** The computed "solvency field" substrate rendered as concentric rings —
exactly the ripple-graphic look its own spec named as the thing to avoid.

**Root cause.** Two near-equal Gaussian wells produce level sets that are concentric
circles. Contours only read as *data* when a trend deforms them.

**Fix.** A dominant directional slope plus opposite-sign, anisotropic wells — the level
sets became swept, irregular bands that tighten near the wells. A per-scene `seed`
varies the field so no two beats share one.

**Generalises to.** A contour is information only if something directional dominates it;
symmetric sources read as ornament. (This film was later set aside anyway, for the
"wrong brand" reason above — but the lesson stands for any computed substrate.)

### OmniVoice cannot run on this machine, and CPU-fallback is a trap

**Symptom.** The user asked to clone a voice with OmniVoice locally.

**What it looked like.** Feasible — the repo advertises a CPU fallback.

**Root cause.** OmniVoice is a 613M-parameter diffusion TTS. Float32 weights are
~2.5 GB before PyTorch's own ~1.5 GB, on a 7.3 GB machine already spending 3–4 GB on
Windows. It supports CUDA / Apple MPS / Intel XPU — none of which is this box's AMD
iGPU. The CPU fallback exists but the RAM ceiling is the wall, not the clock.

**Fix.** Clone on a free Colab T4 (`pipeline/scripts/omnivoice_colab.md`), download the
wav, and mux locally with ffmpeg (`add_voice.py`) — the only part that fits here.

**Generalises to.** Local-ML feasibility is gated by RAM ceiling and accelerator
support *before* raw speed. "It falls back to CPU" answers the wrong question when the
model does not fit in memory.

### A verification gotcha worth recording

Spot-checking a `@remotion/transitions` render by plucking a frame at a sequence's
declared boundary lands *inside* the dissolve — content half-gone, apparently clipped.
Transitions consume frames by overlapping the two sequences. Pick interior frames, not
boundary frames, when reading a render for correctness.

### What the films are, and honestly are not

Three films render and are on brand: `vanna-brand.mp4`, `auri-brand.mp4`, and the
combined `vanna-auri-film.mp4`, each from its tenant's real logo/palette/font, with
distinct-topic scenes (variance from structure, not restated copy) and
`@remotion/transitions` between them. Auri's copy is held to `okf-auri/facts/tier-a.md`
and its claim rules — no card, no fiat on-ramp, Ethereum-only, borrowing always shows
liquidation risk. What they are *not* yet: they ship **silent**, and the honest read is
that audio (a real bed or a cloned VO) is the largest remaining premium lever — a low
placeholder hum reads worse than silence, so nothing was faked in.

---

## Still open

1. **Gemini turn completion.** With the shim in place the scout connects,
   subscribes, and consumes real tokens — 3 calls, ~63k input tokens, $0.034
   metered, no errors — but no turn completion was ever logged and it never
   posted. Whether the turn is slow or completing silently was never determined.
   `steering_supported=false` for gemini-cli where Claude reports `true`; that
   difference is unexplored and may be the answer. **Next step:** run one Gemini
   agent, tail its log and `pipeline/logs/vertex-calls.jsonl` together, and
   compare against a Claude agent on the identical prompt.
2. **`files/05` carries a retired claim at two lines, and the gate passes it.**
   See Phase 4. Two fixes needed, not one: correct the file, and extend
   `R-mcp-differentiator` to match bare "MCP-native".
3. **Twitter publishing is down.** Draft `dfda50d2` is approved and unpublished.
   The OpenCLI Chrome bridge returns `No SW`; the daemon is alive, the extension
   service worker is not attached. **Next step:** reload the OpenCLI extension in
   Chrome on the `advayanand87@gmail.com` profile, confirm with
   `opencli twitter whoami`, then re-run the post.
4. **The review poll window is 120s.** See Phase 5. Seven of thirteen recorded
   runs died on it.
5. **No retry on the Telegram dispatch.** `trendjack_news_orchestrator.py:430`.
   A one-line guard prevents the loss of a complete run.
6. **The two dashboards are an unreconciled fork**, neither reads the relay, and
   all fourteen route files hardcode `D:/new orchestration`.
7. **Agentics Credit escalation.** Base, 90-day track-record agent credit
   scoring, trips the `files/11` §9 watch trigger. The agentic-credit strategist
   correctly refused to adjust positioning on its own authority and escalated.
   Unresolved — and worth noting the agent behaved correctly here.
8. **Draft `a4cb2c02`.** `HANDOFF.md` records it as `changes_requested` with the
   reviewer's "send notes" never resolved. **No artifact for this id exists
   anywhere on disk** — `drafts/`, `approved/` and `rejected/` do not contain it,
   and the id appears only in `HANDOFF.md`. Either the draft was cleaned up (the
   lifecycle scripts do clear draft directories at startup) or the id was
   mis-recorded. Treat as unverifiable rather than open.
9. **A full autonomous cycle has never completed end to end on the Buzz
   substrate.** The Claude run died on a session limit; the Gemini run never
   posted. What *has* been proven is that agents wake, reason from their
   personas, research, correct each other, and post autonomously. The runs that
   produced shipped content used the direct-orchestrator path
   (`trendjack_news_orchestrator.py`), not the multi-process relay.
10. **The brand films are silent.** `vanna-brand.mp4`, `auri-brand.mp4` and
    `vanna-auri-film.mp4` render on brand but ship with no audio, which is the largest
    gap between them and the reference set. The voiceover path exists but is
    user-gated: a 15–30s reference clip run through `omnivoice_colab.md` on a free GPU,
    then `add_voice.py` muxes locally. Until a clip or a licensed bed arrives, silent is
    the honest default.

---

## Decisions worth revisiting

**Rendering the pipeline as a single Python orchestrator while the relay
architecture was still being debugged.** `trendjack_news_orchestrator.py` calls
Vertex directly in sequence — it does not use Buzz at all. This is why content
shipped at all, and it is also why the relay path has never completed a cycle:
the pragmatic path removed the pressure to finish the architectural one. Both
now exist and only one works. Decide which is the product.

**Building the Buzz relay from Rust source on Windows.** The build friction —
failing crates, `CARGO_HOME` path format, a partial build that must be
remembered — is permanent overhead on every machine. Prebuilt binaries or a
fully containerised relay would remove it, and would remove most of Phase 1 from
this document for the next person.

**Hardcoding absolute paths in the dashboard routes.** Expedient during a port
where the data source was a fixture. It is now the single largest blocker to the
`MAC_MINI_SETUP.md` migration, and it is in fourteen files.

**Letting the endpoint contract in `PORT-NOTES.md` §(c) drift from the
implementation.** The contract is well written and now describes a system that
does not exist. A contract nobody re-checks is worse than no contract, because
the next person will code against it.

---

## The five things most likely to bite the next person

1. **A GCP budget does not stop spend.** Route every call through
   `vertex_spend_proxy.py` and check `/_spend`. Trusting the Google dashboard is
   how the ~$109 bill happened. → [A GCP budget was mistaken for a spending cap](#a-gcp-budget-was-mistaken-for-a-spending-cap)
2. **Editing `files/08` does not change what the gate blocks.** The rules are
   hardcoded lists in `claim_safety_gate.py`. And the gate currently passes the
   exact retired phrasing sitting in `files/05`. → [`files/05` still carries a retired claim](#files05-still-carries-a-retired-claim--and-the-gate-does-not-catch-it)
3. **`localhost` is IPv6 `::1` here, and the error will blame the wrong layer.**
   Use `127.0.0.1` for every Docker-published port. → [Postgres rejected every connection with an SSL error](#postgres-rejected-every-connection-with-an-ssl-error)
4. **Silent degradation beats loud failure to your detriment.** A denied
   permission made the scout produce plausible, worthless research; an unset
   `--respond-to` made agents look healthy while ignoring everything. When
   output looks thin, check permissions before checking prompts. → [The scout's research quietly degraded to nothing](#the-scouts-research-quietly-degraded-to-nothing)
5. **The pipeline loses completed work to transient failures at the end.** The
   Telegram dispatch has no retry, and the review poll gives a human 120
   seconds. Together they account for eight of thirteen recorded runs producing
   nothing. → [A transient Telegram send killed a run](#a-transient-telegram-send-killed-a-run-that-had-already-done-all-the-work)

---

## Notes on sourcing

Incidents in Phases 1 and 2 come primarily from `HANDOFF.md`, written at the
time; where an artifact still exists it was re-checked, and where it does not
the entry is marked *recorded, not reproducible*. Phase 6 comes from
`hermes-mission/PORT-NOTES.md`. Phase 4's gate behaviour, Phase 5's run
statistics, and every version number and route claim in Phase 6 were verified
directly against the machine on 2026-08-10.

Two items in `HANDOFF.md` did not survive verification and are corrected above:
the `files/05` contradiction occurs at two lines rather than one, and draft
`a4cb2c02` has no artifact on disk.

No secrets, tokens, or key material appear in this document, and none were read
from `pipeline/keys/` to write it.
