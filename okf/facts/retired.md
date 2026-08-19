---
type: Facts Ledger
title: Retired claims
description: Claims that were safe to make and stopped being safe when the market moved.
tags: [facts, claims, competitive]
tier: RETIRED
status: deprecated
stale_after: 2026-11-01
verified:
  - by: human:advay
    at: 2026-08-10T00:00:00Z
sources:
  - id: repositioning
    resource: /files/11-competitive-strategy-and-repositioning.md
    title: Competitive strategy and repositioning
  - id: gate
    resource: /rules/retired-claims.md
    title: Retired positioning rules
---

# Retired claims

A claim retires when a competitor ships something that makes it false, not when
someone decides it sounds stale. Each entry records what changed and when, so
the decision can be re-examined rather than re-argued.

`status: deprecated` on this document is deliberate: an OKF consumer that
surfaces concepts by lifecycle will not present these as current positioning.

## MCP-native as a differentiator

**Retired April 2026.** Morpho Agents shipped MCP plus CLI on mainnet with
roughly $11.8B TVL; Base MCP followed in May 2026. Leading with MCP now
describes a competitor's shipped product rather than a distinguishing feature.

**Replacement line:** "Morpho gives agents access to a lending market. Vanna
gives them a balance sheet."

Enforced by `R-mcp-differentiator`.

## Sole ownership of agent credit scoring

**Retired 2026.** Kojiru ACS, ERC-8004, Visa TAP, WEF KYA and Agentics Credit
are all working in this space. Any claim that nobody else is building it is
false.

Enforced by `R-category-claim`.

## Two live defects in the legacy source

Both verified present on 2026-08-10, and they are only dangerous together.

1. **`files/05-audiences-personas-and-objections.md` still carries the retired
   claim at two lines** — line 14 ("MCP-native · Policy-bounded · On-chain track
   record") and line 47 ("MCP-native from day one"). The earlier handoff note
   recorded only line 14.

2. **The gate does not catch that phrasing.** `R-mcp-differentiator` matches
   superlative and possessive forms — "the only protocol with MCP", "MCP is our
   moat" — but not a bare feature bullet. Tested:

   | Input | Result |
   |---|---|
   | `Vanna is MCP-native. Policy-bounded. On-chain track record.` | **passes** |
   | `Vanna is the only protocol with MCP support.` | blocks |

So a strategist that copies the phrase out of a file it was told to treat as a
source produces a draft the gate approves. Fixing either one alone leaves the
hazard in place.

## Watch triggers

Agentics Credit (Base, 90-day track-record agent credit scoring) trips the watch
condition in `files/11` §9. The agentic-credit strategist correctly refused to
adjust positioning on its own authority and escalated; that escalation is still
open. An agent declining to move positioning unilaterally is the intended
behaviour, not a failure.
