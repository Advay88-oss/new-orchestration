---
type: Facts Ledger
title: Tier B - qualified
description: True, but false or misleading if stated without its qualifier.
tags:
- facts
- claims
tier: B
status: stable
verified:
- by: human:advay
  at: '2026-08-10T00:00:00Z'
sources:
- id: facts-08
  resource: /files/08-facts-ledger-and-claim-safety.md
  title: Facts ledger and claim safety
---

# Tier B - qualified

Claims that are accurate only with their conditions attached. Capacity multiples
such as "up to 10x" belong here: real as a mechanism, misleading as a headline
number without an illustrative label.

Dropping the qualifier is the most common way this pipeline nearly ships
something false, which is why `TIER_F` exists in
[/rules/tier-f-unsupported.md](/rules/tier-f-unsupported.md) and why
`C-unlabelled-demo` fires on an unlabelled demo figure.

**Test for this tier:** does the sentence stay true if a reader quotes only its
first half?
