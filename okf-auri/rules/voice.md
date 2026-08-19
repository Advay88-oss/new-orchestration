---
type: Claim Rule Set
title: Voice
description: Tone patterns rejected regardless of accuracy.
tags:
- voice
status: stable
rule_count: 2
rules:
- id: AUV1-cryptohype
  severity: BLOCK
  pattern: \b(?:to the moon|ape in|number go up|diamond hands|WAGMI|get rich|lambo)\b
  why: Auri is serious money, deliberately anti crypto-bro. This tone breaks the brand.
  fix: Plain, concrete, sensory language.
  flags:
  - IGNORECASE
- id: AUV2-hype
  severity: BLOCK
  pattern: \b(?:revolutionary|game[-\s]?chang\w+|world[-\s]?class|cutting[-\s]?edge|disrupt(?:ive|ing)?)\b
  why: Generic hype; Auri earns trust with specifics, not adjectives.
  fix: Use a concrete, checkable fact.
  flags:
  - IGNORECASE
---

# Voice

Auri is anti-hype and anti crypto-bro. Trust comes from specifics.
