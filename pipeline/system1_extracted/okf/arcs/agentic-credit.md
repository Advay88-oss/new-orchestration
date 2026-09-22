---
type: Narrative Arc
title: Agentic credit
description: Autonomous agents can spend but cannot borrow; a balance sheet is the missing primitive.
tags: [arc, positioning, debate]
status: stable
arc_id: agentic-credit
line: "Agents can pay. Agents can't borrow."
opposes: [/arcs/capital-efficiency.md, /arcs/risk-relief.md]
assigned_to: /agents/strategist-agentic-credit.md
verified:
  - by: human:advay
    at: 2026-08-10T00:00:00Z
---

# Agentic credit

**"Agents can pay. Agents can't borrow."**

Payment rails for autonomous agents exist and are maturing. Credit does not. An
agent with a wallet can spend what it has; it cannot take a position it will
settle later, which is what a balance sheet is for. This arc argues the missing
primitive is credit, not payments.

## What it may claim

The lead framing is the one that survived the August 2026 repositioning:
**"Morpho gives agents access to a lending market. Vanna gives them a balance
sheet."**

The Agent Score stays **future tense only** until sybil resistance is designed.
See [/facts/tier-c-future.md](/facts/tier-c-future.md).

## Where it must not go

This arc sits closest to the retired claims and needs the most care.

- **Never lead with "MCP-native."** Morpho Agents shipped MCP and CLI on mainnet
  in April 2026, so it describes a competitor's shipped product.
  `R-mcp-differentiator` in [/rules/retired-claims.md](/rules/retired-claims.md)
  blocks the superlative forms.
- **Never claim the company owns agent credit scoring.** Kojiru, ERC-8004, Visa
  TAP, WEF KYA and Agentics Credit are all in that space. `R-category-claim`
  blocks the explicit version.
- **Known gap:** the bare phrase "MCP-native" as a feature bullet is *not*
  currently blocked, and it still appears in the legacy source at
  `files/05-audiences-personas-and-objections.md` lines 14 and 47. Until both are
  fixed, a strategist copying from that file can produce a passing draft with a
  retired claim in it. See [/facts/retired.md](/facts/retired.md).

## How it argues against the others

Against [capital efficiency](/arcs/capital-efficiency.md): optimising human
collateral is an incremental gain in a market that already has many options.
Agents that can hold a balance sheet is a new category, and categories are worth
more than percentages.

Against [risk relief](/arcs/risk-relief.md): risk controls are table stakes that
every lender claims. They do not answer why an autonomous agent should exist as
a borrower at all, which is the question that decides whether any of this
matters in five years.
