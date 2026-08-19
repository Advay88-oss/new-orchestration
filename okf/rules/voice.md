---
type: Claim Rule Set
title: Voice prohibitions
description: Brand-voice patterns that are rejected regardless of factual accuracy.
tags:
- voice
- style
status: stable
generated:
  by: process:okf_export_rules
  at: '2026-08-10T00:00:00Z'
sources:
- id: gate-builtin
  resource: /pipeline/scripts/claim_safety_gate.py
  title: claim_safety_gate.VOICE
rule_count: 5
rules:
- id: V-hype-register
  severity: BLOCK
  pattern: (?:^|[^\w])(?:moon(?:ing|shot)?|wen\b|WAGMI|LFG|gm\b|ape(?:d|ing)?\b|degen)(?:[^\w]|$)
  why: Crypto hype register is banned brand-wide.
  fix: Remove. The brand is professional, educational, confident — never hype.
  flags:
  - IGNORECASE
- id: V-banned-adjectives
  severity: BLOCK
  pattern: \b(?:revolutionary|game[- ]chang(?:er|ing)|next[- ]gen(?:eration)?|seamlessly)\b
  why: Explicitly banned word.
  fix: Delete the adjective and state the mechanism instead.
  flags:
  - IGNORECASE
- id: V-exclamation
  severity: BLOCK
  pattern: '!'
  why: Exclamation marks are banned — 'the brand does not shout.'
  fix: Replace with a period.
  flags: []
- id: V-leverage-as-verb
  severity: WARN
  pattern: \bleverage\s+(?:our|your|their|its|the)\s+\w+\s+to\b
  why: '''leverage'' as a verb meaning ''use'' is banned.'
  fix: Use 'use'. Reserve 'leverage' for the financial noun.
  flags:
  - IGNORECASE
- id: V-fomo
  severity: BLOCK
  pattern: \b(?:don'?t miss out|last chance|act now|limited time|only \d+ spots|before it'?s too late)\b
  why: FOMO or scarcity pressure is banned.
  fix: Remove.
  flags:
  - IGNORECASE
---

# Voice prohibitions

The most portable rule set in the bundle. Generic hype, hedging and filler read badly for almost any company, so most of these survive a re-branding unchanged. Review rather than rewrite.

## How these are applied

Each entry is a regular expression evaluated against the draft body. A match at severity `block` exits the gate non-zero and the draft never reaches a human reviewer. `warn` is recorded and does not stop the run.

`pattern` is the regex verbatim; `flags` are `re` module flag names. `why` is shown to the agent that wrote the draft, and `fix` tells it what to write instead — a rule without a usable `fix` produces a strategist that retries the same mistake.

## Editing

Change a pattern here and the gate picks it up on its next run; there is no build step. **Then prove it**: write a string that must be blocked and confirm it is.

```bash
python pipeline/scripts/claim_safety_gate.py --text "a claim that must block"
```
