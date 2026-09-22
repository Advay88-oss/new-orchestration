---
type: Content Topic
order: 0
title: Unified Margin Accounts
description: How Vanna unifies collateral across disparate positions to unlock up to 10x borrowing capacity,
  contrasted with siloed liquidity pools.
topic: capital-efficiency
angle: Unified Margin Accounts
tags:
- content
- taxonomy
status: stable
sources:
- id: marketing-config
  resource: /pipeline/config/marketing_config.json
  title: marketing_config.taxonomy
---

# Unified Margin Accounts

How Vanna unifies collateral across disparate positions to unlock up to 10x borrowing capacity, contrasted with siloed liquidity pools.

`topic` is the vocabulary the whole pipeline speaks: the scout must return one of
these values, the conductor selects from them, and `content_history.json` records
which was used so the anti-repetition logic can rotate.

**Renaming `topic` is a breaking change.** The permitted-value list is also
written into the scout prompt in the orchestrator; change one without the other
and runs silently carry an unrecognised topic.
