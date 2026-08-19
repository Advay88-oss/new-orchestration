---
type: Claim Rule Set
title: Unsupported and tier-inflated facts
description: Facts stated at a higher confidence than the facts ledger supports.
tags:
- safety
- blocking
- facts
status: stable
generated:
  by: process:okf_export_rules
  at: '2026-08-10T00:00:00Z'
sources:
- id: gate-builtin
  resource: /pipeline/scripts/claim_safety_gate.py
  title: claim_safety_gate.TIER_F
rule_count: 8
rules:
- id: F-1000x
  severity: BLOCK
  pattern: \b1000\s*[x×]\b|\b1,?000\s*[x×]\s*leverage\b
  why: '''1000× leverage'' is a legacy/hackathon-era error. Canonical max is 10×.'
  fix: Use 10×.
  flags:
  - IGNORECASE
- id: F-tiered-leverage
  severity: BLOCK
  pattern: \b5\s*[x×]\s*base\b|\b7\s*[x×]\s*blue-?chip\b
  why: Legacy EVM-era tiered leverage design. Current canonical is a flat 10×.
  fix: Use 10×.
  flags:
  - IGNORECASE
- id: F-erc4337
  severity: BLOCK
  pattern: \b(?:ERC|EIP)-?4337\b|\baccount abstraction\b
  why: Legacy. Current architecture is native Soroban per-user contracts.
  fix: Say 'each user gets their own deployed SmartAccount contract on Soroban'.
  flags:
  - IGNORECASE
- id: F-legacy-dashboards
  severity: BLOCK
  pattern: \b(?:Greeks Dashboard|Prop Dashboard)\b
  why: Legacy vocabulary. Not in the current product or docs.
  fix: Remove.
  flags:
  - IGNORECASE
- id: F-optimism-legacy
  severity: BLOCK
  pattern: \blive on Optimism\b|\bPerp Protocol\b
  why: Legacy EVM deployment. Current is Stellar Soroban testnet.
  fix: Say 'Stellar testnet'.
  flags:
  - IGNORECASE
- id: F-2m-users
  severity: BLOCK
  pattern: \b2\s*M\+?\s*users\b|\b2 million users\b
  why: '''2M+ users'' is aggregate reach of integrated protocols, not Vanna users.'
  fix: Say 'ecosystem reach across integrated protocols', or omit.
  flags:
  - IGNORECASE
- id: F-subscribers
  severity: WARN
  pattern: \b40,?000\+?\s*subscribers\b
  why: Unconfirmed internal figure.
  fix: Confirm with a human before external use.
  flags:
  - IGNORECASE
- id: F-perps-78
  severity: WARN
  pattern: \b78%\s*of\s*derivatives\b
  why: Unverified internal research figure.
  fix: Verify against a current public source before publishing.
  flags:
  - IGNORECASE
---

# Unsupported and tier-inflated facts

These catch a claim that exists in the ledger but is being stated more strongly than its tier allows — a Tier C roadmap item written in the present tense, or a Tier B fact stated without its qualifier. See [/facts/tier-b-qualified.md](/facts/tier-b-qualified.md) and [/facts/tier-c-future.md](/facts/tier-c-future.md).

## How these are applied

Each entry is a regular expression evaluated against the draft body. A match at severity `block` exits the gate non-zero and the draft never reaches a human reviewer. `warn` is recorded and does not stop the run.

`pattern` is the regex verbatim; `flags` are `re` module flag names. `why` is shown to the agent that wrote the draft, and `fix` tells it what to write instead — a rule without a usable `fix` produces a strategist that retries the same mistake.

## Editing

Change a pattern here and the gate picks it up on its next run; there is no build step. **Then prove it**: write a string that must be blocked and confirm it is.

```bash
python pipeline/scripts/claim_safety_gate.py --text "a claim that must block"
```
