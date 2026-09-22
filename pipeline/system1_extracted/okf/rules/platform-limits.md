---
type: Claim Rule Set
title: Platform limits
description: Per-channel length and format constraints.
tags:
- platform
- format
status: stable
rule_count: 0
rules: []
limits:
  x:
    max_chars: 280
---

# Platform limits

Length and format constraints per channel. Held as `limits` rather than regex
rules because they are numeric, and enforced at composition time rather than by
pattern matching.

`rules` is intentionally empty — it exists so the loader treats this document
uniformly with the other rule sets. A consumer that iterates rule sets will find
nothing here to evaluate, which is correct.
