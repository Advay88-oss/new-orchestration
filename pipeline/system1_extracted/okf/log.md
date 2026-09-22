# Log

Chronological history of this bundle, newest first. OKF §9.

## 2026-08-10

**Update** — Bundle wired into the renderer and the orchestrator config, not
just the gate. `render_visual.py` now reads [/brand/palette.md](/brand/palette.md)
(fallback to its built-in palette), and `marketing_config.json` is generated
from the bundle's taxonomy, competitors and new
[/research/config.md](/research/config.md) by `okf_sync_config.py`. The generated
config is identical by value to the hand-written one it replaced. `order` fields
were added to the taxonomy and competitor concepts so the generated config
preserves the original ordering.

**Creation** — Bundle created at OKF v0.2. Everything company-specific that was
previously scattered across `files/`, `pipeline/buzz-pack/`,
`pipeline/config/marketing_config.json` and `pipeline/scripts/claim_safety_gate.py`
was moved or mirrored here so the pipeline can be pointed at another company by
swapping this directory.

**Creation** — 32 safety rules exported verbatim from the gate's Python literals
into [/rules/hard-prohibitions.md](/rules/hard-prohibitions.md),
[/rules/tier-f-unsupported.md](/rules/tier-f-unsupported.md),
[/rules/retired-claims.md](/rules/retired-claims.md) and
[/rules/voice.md](/rules/voice.md). Patterns were exported by script, not
transcribed. Parity with the built-ins is asserted by
`pipeline/scripts/okf_parity_test.py`: identical rule ids, verbatim patterns and
flags, and identical verdicts across a must-block / must-pass corpus.

**Update** — The claim-safety gate now loads rules from this bundle and falls
back to its built-in literals if the bundle is absent, unreadable or empty. Its
verdict carries `rules_source` so a run that silently used the wrong company's
rules is visible rather than invisible.

**Creation** — [/company/constraint.md](/company/constraint.md) records the one
rule that outranks every other instruction. For this company it is testnet
status; every company running this pipeline needs its own.

**Deprecation** — [/facts/retired.md](/facts/retired.md) marked
`status: deprecated` and given `stale_after: 2026-11-01`. It records two claims
retired in 2026 — MCP as a differentiator, and sole ownership of agent credit
scoring — plus a live defect: the legacy source `files/05` still carries the
retired phrasing at lines 14 and 47, and `R-mcp-differentiator` does not match
that bare form. Verified by test on this date. Unfixed.
