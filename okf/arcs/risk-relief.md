---
type: Narrative Arc
title: Risk relief
description: Leverage is easy to get and hard to survive; the product is survival, not access.
tags: [arc, positioning, debate]
status: stable
arc_id: risk-relief
line: "Leverage is easy. Not getting liquidated is the hard part."
opposes: [/arcs/capital-efficiency.md, /arcs/agentic-credit.md]
assigned_to: /agents/strategist-risk-relief.md
verified:
  - by: human:advay
    at: 2026-08-10T00:00:00Z
---

# Risk relief

**"Leverage is easy. Not getting liquidated is the hard part."**

The reader already has access to leverage from a dozen places. What they do not
have is a mechanism that keeps them solvent while they sleep. This arc argues
that the scarce thing is survival, not access.

## What it may claim

Only what the facts ledger supports. The concrete, quotable mechanisms are the
1.1x health-factor floor rather than 1.0x, the oracle cadence, and per-account
contract isolation. See [/facts/tier-a-quotable.md](/facts/tier-a-quotable.md).

## Where it must not go

- It may not promise that liquidation is prevented. It is reduced within a
  policy the user sets. `P5-returns-promise` in
  [/rules/hard-prohibitions.md](/rules/hard-prohibitions.md) blocks the stronger
  framing.
- It may not present a demo figure as a realised outcome (`P4-demo-as-result`).
- Any post touching leverage or credit must disclose testnet status, per
  [/company/constraint.md](/company/constraint.md).

## How it argues against the others

Against [capital efficiency](/arcs/capital-efficiency.md): more efficient
collateral is more collateral at risk in one place. Efficiency without a floor
is a faster route to liquidation, so the floor is the prior concern.

Against [agentic credit](/arcs/agentic-credit.md): giving an autonomous agent a
balance sheet is only responsible if the downside is bounded first. Risk
controls are a precondition for agent credit, not a feature alongside it.

**This disagreement is the point.** The three arcs are assigned to three
strategists precisely so that they must argue about *which problem matters
most*, rather than converging on "we are better". An arc that could be swapped
for another without changing the argument is not doing its job.
