---
type: Channel
title: Telegram human review
description: The blocking human gate. Nothing publishes without an explicit approval here.
tags:
- channel
- review
- safety
status: stable
reviewer: human:advay
chat_id: '5501720892'
bot: '@vanna0bot'
approve_words:
- ok
- approve
- haan
- 'yes'
- ship
- go
reject_words:
- 'no'
- reject
- nahi
- kill
- drop
timeout_seconds_default: 3600
timeout_seconds_actual: 120
---

# Telegram human review

The last gate before anything reaches a platform, and the product's safety
story. Any reply that is neither an approval nor a rejection is kept as revision
notes and the draft becomes `changes_requested`.

In OKF terms this is what produces a **human-reviewed** trust tier: an approval
here is the `verified: { by: human:<id> }` event on the resulting post.

**Known defect:** the orchestrator overrides the 3600s default down to 120s, and
7 of 13 recorded runs ended `timeout` as a result. The two-minute window encodes
an assumption nobody stated.
