---
type: Claim Rule Set
title: Retired positioning
description: Claims that were once safe and became false when the market moved.
tags:
- safety
- blocking
- competitive
status: stable
generated:
  by: process:okf_export_rules
  at: '2026-08-10T00:00:00Z'
sources:
- id: gate-builtin
  resource: /pipeline/scripts/claim_safety_gate.py
  title: claim_safety_gate.RETIRED
rule_count: 6
rules:
- id: R-mcp-differentiator
  severity: BLOCK
  pattern: \b(?:first|only|unique(?:ly)?)\s+(?:\w+\s+){0,3}MCP\b|\bMCP-native\s+(?:is|as)\s+(?:our|the)\s+(?:differentiator|advantage|edge)\b|\bMCP\s+(?:is\s+)?(?:our|the)\s+(?:differentiator|moat|advantage)\b
  why: MCP is table stakes since Morpho Agents (Apr 2026, mainnet, ~$11.8B TVL) and Base MCP (May 2026).
    Leading with it describes a competitor's shipped product.
  fix: 'Lead with undercollateralized credit: ''Morpho gives agents access to a lending market. Vanna
    gives them a balance sheet.'''
  flags:
  - IGNORECASE
- id: R-category-claim
  severity: BLOCK
  pattern: \bnobody else is building\b|\bno one else is building\b|\b(?:first|only) (?:protocol|company|team)
    to (?:build|offer)\b
  why: Category-invention claim. Kojiru ships an Agent Credit Score; ERC-8004, Visa TAP, WEF KYA and an
    IETF draft are standardising agent reputation.
  fix: Claim the underwriting layer, not the category. See file 11 §2.3.
  flags:
  - IGNORECASE
- id: R-unforkable-moat
  severity: BLOCK
  pattern: \bunforkable\b|\bcannot be forked\b|\bcan'?t be forked\b
  why: The 'unforkable data moat' framing was retired by file 11 §1.
  fix: Say 'a credit decision needs a margin account to generate — that's the part that can't be copied
    from outside.'
  flags:
  - IGNORECASE
- id: R-agent-score-present-tense
  severity: BLOCK
  pattern: \b(?:our|the) Agent Score (?:gives|provides|underwrites|determines|scores|powers)\b|\bAgent
    Score (?:is|does) (?:live|working|underwriting)\b
  why: The Agent Score has no documented sybil resistance (file 11 §3). It must stay in future tense until
    that design ships.
  fix: Say 'Vanna is building an Agent Score that turns on-chain behaviour into a credit line.'
  flags:
  - IGNORECASE
- id: R-logo-wall-as-live
  severity: BLOCK
  pattern: \b1[0-9]\+?\s*integrations\b|\b6\+?\s*chains\b|\b(?:live|integrated) (?:with|on) (?:\w+\s+){0,2}(?:Hyperliquid|Uniswap|Morpho|Aerodrome|Avantis|Derive|Aster|Katana)\b
  why: Only Blend, Aquarius and Soroswap are live, all on Stellar testnet. The logo wall is ecosystem,
    not integrations (file 11 §6).
  fix: Say 'Deep integrations with Blend, Aquarius and Soroswap today, with a broader venue roadmap.'
  flags:
  - IGNORECASE
- id: R-stellar-liquidity
  severity: WARN
  pattern: \bStellar (?:is where|has) (?:\w+\s+){0,2}(?:DeFi )?liquidity\b
  why: Stellar's entire DeFi TVL is ~$161M. The liquidity framing does not survive scrutiny.
  fix: Say 'Stellar has $2.4B in RWAs, institutions and live agentic payment rails — and no credit layer.'
  flags:
  - IGNORECASE
---

# Retired positioning

The most perishable rule set, and the one most likely to be wrong for another company. These exist because a competitor shipped something that invalidated a claim this company used to make; see [/facts/retired.md](/facts/retired.md) for the underlying facts and when each was retired.

**For a new company this set is almost certainly empty at first.** That is correct. It fills up as the market moves.

## How these are applied

Each entry is a regular expression evaluated against the draft body. A match at severity `block` exits the gate non-zero and the draft never reaches a human reviewer. `warn` is recorded and does not stop the run.

`pattern` is the regex verbatim; `flags` are `re` module flag names. `why` is shown to the agent that wrote the draft, and `fix` tells it what to write instead — a rule without a usable `fix` produces a strategist that retries the same mistake.

## Editing

Change a pattern here and the gate picks it up on its next run; there is no build step. **Then prove it**: write a string that must be blocked and confirm it is.

```bash
python pipeline/scripts/claim_safety_gate.py --text "a claim that must block"
```
