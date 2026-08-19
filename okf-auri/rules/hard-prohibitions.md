---
type: Claim Rule Set
title: Hard prohibitions
description: Claims that are false or reckless for a gold + borrowing product.
tags:
- safety
- blocking
status: stable
rule_count: 5
rules:
- id: AU1-returns
  severity: BLOCK
  pattern: \b(?:guaranteed|risk-?free|can'?t lose|no downside|assured returns|will (?:grow|earn)|guaranteed
    (?:yield|return))\b
  why: Gold can fall and leverage amplifies losses. Never promise or imply a return or safety.
  fix: State value conditionally; keep the risk.
  flags:
  - IGNORECASE
- id: AU2-advice
  severity: BLOCK
  pattern: \byou should (?:buy|invest|borrow|leverage)\b|\b(?:financial|investment) advice\b|\bgood investment\b
  why: Constitutes financial/investment advice.
  fix: Describe the product, not a recommendation.
  flags:
  - IGNORECASE
- id: AU3-safe-leverage
  severity: BLOCK
  pattern: \b(?:safe|risk-?free|no risk|worry-?free)\b[^.]{0,20}\b(?:leverage|borrow|loan)\b|\b(?:leverage|borrow(?:ing)?|loan)\b[^.]{0,20}\b(?:is
    safe|risk-?free|no risk)\b
  why: Borrowing and leverage carry real liquidation risk. Never frame them as safe.
  fix: State the liquidation risk alongside.
  flags:
  - IGNORECASE
- id: AU4-custody-overclaim
  severity: BLOCK
  pattern: \b(?:FDIC|CDIC)[- ]?insured\b|\bbank[- ]?guaranteed\b|\bfully insured\b
  why: Auri is non-custodial gold, not an insured deposit. Do not borrow bank-deposit trust language.
  fix: Speak to allocated gold, attestation, and self-custody instead.
  flags:
  - IGNORECASE
- id: AU5-infra-overclaim
  severity: BLOCK
  pattern: \b(?:production-?grade|enterprise-?grade|battle-?tested|proven at scale|(?:99\.?\d*)\s*%?\s*uptime|SLA-?backed|bank-?grade)\b
  why: Infrastructure is a campaign lead, but Auri's API/scale is unverified (Tier C). Do not claim proven
    production reliability or scale.
  fix: Frame the rails as designed for B2B and B2C, not as proven at scale.
  flags:
  - IGNORECASE
---

# Hard prohibitions

Every rule descends from [/company/constraint.md](/company/constraint.md).
