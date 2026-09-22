---
type: Narrative Arc
title: Capital efficiency
description: Collateral sitting in one silo doing one job, when a unified margin account lets it do several.
tags: [arc, positioning, debate]
status: stable
arc_id: capital-efficiency
line: "Your collateral is doing one job. It should be doing six."
opposes: [/arcs/risk-relief.md, /arcs/agentic-credit.md]
assigned_to: /agents/strategist-capital-efficiency.md
verified:
  - by: human:advay
    at: 2026-08-10T00:00:00Z
---

# Capital efficiency

**"Your collateral is doing one job. It should be doing six."**

Isolated pools fragment collateral. The same capital, posted once into a unified
margin account, can support several positions at once. This arc argues the
waste is the story: not that borrowing is unavailable, but that it is
needlessly expensive in capital terms.

## What it may claim

The unified margin mechanism and the borrowing capacity it unlocks, stated at
the tier the ledger allows. Multiples such as "up to 10x" are illustrative and
must be labelled as such — see [/facts/tier-b-qualified.md](/facts/tier-b-qualified.md).

## Where it must not go

- No TVL, no user counts, no realised returns (`P1-tvl`, `P4-demo-as-result`).
- A capacity figure without an illustrative label trips `C-unlabelled-demo`.
- "10x" alongside credit or borrow language without testnet disclosure raises
  `A-missing-testnet`.

## How it argues against the others

Against [risk relief](/arcs/risk-relief.md): a floor that never gets tested is
insurance nobody needed. Most users are not being liquidated — they are
over-collateralised and under-deployed, and that cost is paid every single day
rather than on a bad one.

Against [agentic credit](/arcs/agentic-credit.md): agents are a small and
speculative audience today. Human capital is idle at scale right now, and a
positioning that leads with agents ignores the larger, present problem.
