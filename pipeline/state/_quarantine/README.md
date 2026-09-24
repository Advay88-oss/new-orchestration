# Quarantined learning state (2026-09-24)

Moved, not deleted — they are evidence of why A13 never learned.

- `performance_records.test_fixture.jsonl` — 44 rows, every one the same test
  fixture (`C-E2E-01`, dated 2026-09-16), every metric `NOT_MEASURED`. No real
  post has ever been measured.
- `learned_pattern_adjustments.fixture.jsonl` — 157 adjustments, 151 of them the
  identical first step `PAT_01 1.0 -> 1.15`: weights were never persisted, so
  each run started from 1.0. Written by tests whose weighting engine ignored
  the temporary store and used the production path.

Learning restarts from founder feedback (`pipeline/state/feedback.jsonl`).
