---
type: Content Topic
order: 2
title: Agentic Credit & Balance Sheets
description: Vanna's core feature enabling autonomous agents to have their own onchain financial identity,
  borrow capital, and build credit scores.
topic: agentic-credit
angle: Agentic Credit & Balance Sheets
tags:
- content
- taxonomy
status: stable
sources:
- id: marketing-config
  resource: /pipeline/config/marketing_config.json
  title: marketing_config.taxonomy
---

# Agentic Credit & Balance Sheets

Vanna's core feature enabling autonomous agents to have their own onchain financial identity, borrow capital, and build credit scores.

`topic` is the vocabulary the whole pipeline speaks: the scout must return one of
these values, the conductor selects from them, and `content_history.json` records
which was used so the anti-repetition logic can rotate.

**Renaming `topic` is a breaking change.** The permitted-value list is also
written into the scout prompt in the orchestrator; change one without the other
and runs silently carry an unrecognised topic.
