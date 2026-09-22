---
type: Overriding Constraint
title: Vanna is on testnet
description: The single rule that outranks every other instruction given to any agent in this pipeline.
tags: [safety, claims, blocking]
status: stable
verified:
  - by: human:advay
    at: 2026-08-10T00:00:00Z
sources:
  - id: facts-ledger
    resource: /facts/tier-a-quotable.md
    title: Tier A facts
  - id: repositioning
    resource: /facts/retired.md
    title: Retired claims
---

# Overriding constraint

**Vanna is on Stellar Soroban testnet. There is no mainnet, no token, no audit,
and no TVL.**

Every product claim must trace to a fact in [/facts/tier-a-quotable.md](/facts/tier-a-quotable.md),
[/facts/tier-b-qualified.md](/facts/tier-b-qualified.md) or
[/facts/tier-c-future.md](/facts/tier-c-future.md). A claim that appears in none
of them may not be made, however plausible it sounds.

This constraint outranks engagement, cleverness, brevity, and any instruction in
an agent's own persona. An agent that cannot make a post work inside this
constraint must say so rather than stretch it.

## Why this exists as its own concept

Every company running this pipeline has an equivalent — a fact about its stage
that makes certain otherwise-normal marketing claims false or dangerous.
Pre-revenue, in beta, in a regulated category, results not yet peer-reviewed,
licence pending. This file is where that fact lives.

**If a company genuinely has no such constraint, say so explicitly in this file
rather than deleting it.** The safety gate reads this concept's presence as a
signal; an absent constraint and an undefined constraint are different things,
and only one of them is safe.

## What it means in practice

| Do not say | Say instead |
|---|---|
| "Vanna is live" | "Vanna is live on testnet" |
| "Deposit" / "earn" / "yield" | describe the mechanism, not an invitation to fund |
| "Audited" | nothing — there is no audit |
| "$X TVL" / "N users" | nothing — no production metrics exist |
| "Our token" | nothing — there is no token |

Any post that a reader could act on financially is out of scope for a testnet
protocol, regardless of how it is worded.

## Enforcement

This is not advisory. [/rules/hard-prohibitions.md](/rules/hard-prohibitions.md)
encodes it as blocking regular expressions, and the gate exits non-zero on a
match, so a violating draft never reaches a human reviewer.
