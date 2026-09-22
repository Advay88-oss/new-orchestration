---
type: Content Topic
order: 1
title: Autonomous Risk Guardian
description: Vanna's 1.1x automated liquidation floor and policy-bounded risk management, saving users
  during volatile market cascades.
topic: risk-relief
angle: Autonomous Risk Guardian
tags:
- content
- taxonomy
status: stable
sources:
- id: marketing-config
  resource: /pipeline/config/marketing_config.json
  title: marketing_config.taxonomy
---

# Autonomous Risk Guardian

Vanna's 1.1x automated liquidation floor and policy-bounded risk management, saving users during volatile market cascades.

`topic` is the vocabulary the whole pipeline speaks: the scout must return one of
these values, the conductor selects from them, and `content_history.json` records
which was used so the anti-repetition logic can rotate.

**Renaming `topic` is a breaking change.** The permitted-value list is also
written into the scout prompt in the orchestrator; change one without the other
and runs silently carry an unrecognised topic.
