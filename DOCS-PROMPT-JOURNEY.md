# Prompt — "The journey" documentation

Paste everything below the line into a fresh Hermes session opened at
`D:\new orchestration`.

---

Write **`JOURNEY.md`** at the root of `D:\new orchestration`: an honest
engineering account of how this system was built — what broke, what the wrong
theory was before the right one, what is still unsolved.

This is the document that saves the next person a week. It is not a changelog
and it is not a success story. A reader should come away knowing which parts of
this system are dangerous to touch and why.

## Ground rules — these outrank the section list

1. **Every incident must have evidence.** A file, a log line, a document that
   records it. If you cannot find the evidence, leave the incident out. An
   unsourced war story is worse than no war story.
2. **Never invent a timeline, a duration, a cost, or an error string.** Quote
   error messages exactly as they appear in the logs. If you know an incident
   happened but not when, say "date not recorded" rather than guessing.
3. **Write the wrong hypothesis, not just the fix.** The value here is in the
   detour. "Postgres was failing" is worthless; "Postgres appeared to be
   rejecting SSL, and the actual cause was that `localhost` resolves to IPv6
   `::1` where a different process listens" is the whole point.
4. **Unresolved counts as content.** Open blockers get the same treatment as
   solved ones, in their own section. Do not quietly convert an open item into a
   solved one because a workaround exists — name the workaround as a workaround.
5. **No heroics, no blame, no drama.** Plain past tense. "This cost roughly a
   day" is fine if recorded; "we heroically battled" is not.
6. **Do not fix anything.** If you find a live bug while researching, add it to
   the open-items section. Change no code.

## Where the evidence lives

**Primary — written down at the time**
- `HANDOFF.md` — richest single source. Its "Windows gotchas, all paid for in
  real time", "Spend control", "Runtimes" and "Open items" sections are each a
  seed list. Verify each entry still holds before you write it up.
- `hermes-mission/PORT-NOTES.md` — sections (a) "what could not be reproduced
  exactly" and (b) "believed bugs, left untouched" are a complete, well-sourced
  incident log for the frontend port. Section (a) item 2 (`adjustFontFallback`)
  is a good model for the level of detail wanted throughout.
- `MAC_MINI_SETUP.md` — read as evidence of what the target topology was
  *supposed* to be, and diff that against what actually runs on Windows. The gap
  is itself a finding.
- `DASHBOARD-PROMPT.md` — what the dashboard was asked to be, against what the
  two apps became.

**Primary — machine-written**
- `pipeline/logs/agents/*.log`, `pipeline/logs/vertex-calls.jsonl`,
  `pipeline/logs/trendjack-run.log`, `pipeline/logs/spend-proxy.log`
- `pipeline/state/content_history.json` — every recorded run with its verdict
  outcome. The `verdict_outcome` field distinguishes `approved` from `timeout`,
  which tells you how often the human gate actually closed.
- `pipeline/state/drafts|approved|rejected/` — the drafts that survived and the
  drafts that did not.
- `pipeline/logs/gate-in.json` / `gate-out.json` — claim-safety gate fixtures.

**Secondary — point-in-time notes, verify before quoting**
- `C:\Users\Advay Anand\.claude\projects\D--\memory\` — particularly
  `vanna-content-pipeline.md`, `buzz-agent-runtime.md`, `agent-reach-setup.md`,
  `vanna-product-reality.md`. These were written during the build and carry
  detail that exists nowhere else. They are observations from a moment, not live
  state — check each against the current code before repeating it.

## Incident seed list

These are known to have happened and are recorded somewhere in the sources
above. **Verify each one before writing it up, and drop any you cannot source.**
This list is not exhaustive — find the ones it misses.

*Environment and platform*
- `localhost` resolving to IPv6 `::1` (where `wslrelay.exe` listens) instead of
  Docker's proxy, surfacing as a misleading Postgres SSL error.
- Docker Desktop installed with `--installation-dir`: files extracted,
  registration silently skipped, launch failed on a missing registry key.
- nvm4w failing on the space in the profile path, PATH silently falling through
  to an unmanaged Node install; resolved with a junction rather than a symlink.
- The Buzz workspace not building on Windows — which crates fail and how, and
  why the fix was to build a subset rather than fix the build.
- `CARGO_HOME` needing a Windows path; a Git Bash path stalling cargo silently.
- C: filling to zero bytes mid-build, and what reclaimed the space.

*Agent runtime*
- `buzz-acp` defaulting to `--respond-to owner-only`, so agents connected, went
  online, and silently ignored every message.
- `--agent-args` requiring the equals form.
- Compound shell commands defeating the permission allowlist, which silently
  downgraded the scout's research to plain web search with no engagement data.
  Note the failure mode: it degraded quietly instead of erroring.
- Seven parallel Opus agents exhausting a subscription session limit mid-run.
- The Gemini ACP auth handshake, the shim written to solve it, and the fact that
  turn completion was never verified afterwards.
- Which model ids actually exist on the project versus which were assumed to.

*Design decisions that came from a failure*
- The coordinator-relay architecture producing three parallel monologues instead
  of a debate, and the move to separate identities in a shared channel. Explain
  why assigning narrative arcs beats letting agents choose one.
- AI image generation being tested and rejected for anything readable, and the
  resulting split: generated texture for background, deterministic CSS for every
  readable element. This was tested, not assumed — say what the test returned.
- GCP budgets being alerts rather than caps, and the local proxy written because
  the only native hard stop would have killed an unrelated workload. Include
  what streaming/SSE metering got wrong on the first attempt and what that error
  would have cost.

*Content correctness*
- Claims retired in August 2026 ("MCP-native", sole ownership of agent credit
  scoring) and what forced the retirement. The claim-safety gate encodes these —
  explain the gate as a response to a real risk, not a formality.
- The `files/05` line 14 contradiction against `files/11` §10.1, found by the
  editorial-judge agent unprompted. Check whether it is still live.

*Operational failures seen in running the pipeline*
- `trendjack_news_orchestrator.py` aborting at the Telegram dispatch step when
  `telegram_review.py send` returned empty stdout — `json.loads` on `""`, no
  retry, and the run dying after the gate had already passed and the card had
  already rendered. The same send succeeded on a manual retry, so the underlying
  cause was transient and the real defect is the missing retry. Consequence: the
  run never reached step 12, so `content_history.json` was not updated by the
  script.
- The OpenCLI Chrome bridge failing publishing with `TIMEOUT` after 60s and then
  `No SW` on every subsequent call, reads included, while the daemon on port
  19825 stayed alive and answering. Root cause sits on the browser-extension
  side, not in the pipeline.
- Dev servers started as background jobs from a shell that then exited, leaving
  nothing listening on the port.

## Structure

**One entry per incident**, grouped into the phases the project actually went
through (work the phases out from the evidence; do not force it into a template
that does not fit). Each entry:

- **Symptom** — what was observed, quoted exactly where a log exists.
- **What it looked like** — the plausible wrong diagnosis. Required. If there
  was no wrong turn, say the cause was immediately obvious; that is rare enough
  to be worth stating.
- **Root cause** — the actual mechanism, in enough detail to recognise it again.
- **Fix** — what changed, at which path.
- **Cost** — only if recorded.
- **Generalises to** — one line. What class of future bug this teaches. Skip it
  if the incident is genuinely one-off; a forced lesson is noise.

Then, as separate closing sections:

- **Still open** — every unresolved blocker, each with what is known, what was
  ruled out, and the concrete next step. Draw from `HANDOFF.md` "Open items" and
  anything you found that is not recorded there.
- **Decisions that would be worth revisiting** — choices made under time
  pressure that a reader should know were choices, not conclusions.
- **The five things most likely to bite the next person** — ranked, each one
  line, each linking to its full entry above.

## Format

Markdown. Past tense. Exact error strings in inline code. File references as
clickable relative paths with line numbers where useful. No emoji. Do not
reproduce any secret, token, private key, or the contents of `pipeline/keys/`.

If a section of this brief turns out to be unsupported by the evidence, write
that in a short note at the end of the document rather than filling it with
plausible-sounding text.
