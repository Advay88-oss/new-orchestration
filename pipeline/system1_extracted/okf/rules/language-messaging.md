---
type: Claim Rule Set
title: Language and messaging prohibitions
description: Phrases the founder's Language & Messaging page rules out, because each is false or invites the wrong reading.
tags:
- voice
- positioning
status: stable
sources:
- id: notion-language-messaging
  resource: https://app.notion.com/p/3e0846d6f5598115a3c3c779091b3756
  title: Notion › Vanna — Current Thesis › Vanna — Language & Messaging (19 Sep 2026)
rule_count: 6
rules:
- id: L-prime-broker-identity
  severity: BLOCK
  pattern: \b(?:we\s+are|vanna\s+is)\s+(?:a|an|the)\s+(?:on-?chain\s+)?prime\s+broker\b
  why: Vanna is a protocol; prime brokerage is an analogy only. A prime broker is a custodial intermediary and invites "which bank licenses you".
  fix: Say "composable credit infrastructure" or "prime-broker-style".
  flags:
  - IGNORECASE
- id: L-prevent-liquidation
  severity: BLOCK
  pattern: \b(?:we|vanna)\s+(?:prevents?|stops?|eliminates?)\s+liquidations?\b
  why: Vanna acts on the account; the venue controls its own liquidation.
  fix: Say the guardian defends a health-factor floor; liquidation remains possible.
  flags:
  - IGNORECASE
- id: L-buffer-recourse
  severity: BLOCK
  pattern: \bbuffer\s+is\s+(?:our|the)\s+recourse\b
  why: The buffer is prevention; the reserve is the recourse.
  fix: '"The buffer makes bad debt rare; the reserve covers it when it happens."'
  flags:
  - IGNORECASE
- id: L-deposit-once
  severity: BLOCK
  pattern: \b(?:deposit|post)\s+(?:collateral\s+)?once\b
  why: Factually wrong — pooled collateral, repeated deposits.
  fix: Say "borrow against deposited collateral, then deploy".
  flags:
  - IGNORECASE
- id: L-borrow-against-markets
  severity: BLOCK
  pattern: \bborrow(?:ing)?\s+against\s+markets\b
  why: Credit is borrowed against deposited collateral, then deployed into markets.
  fix: Say "borrow against deposited collateral, then deploy".
  flags:
  - IGNORECASE
- id: L-absolutes
  severity: BLOCK
  pattern: \b(?:nobody\s+(?:else\s+)?can\s+do\s+this|battle-?tested|provably\s+safe)\b
  why: Absolutes the founder rules out ("I haven't found…" instead of "nobody can").
  fix: Remove the absolute; state the mechanism.
  flags:
  - IGNORECASE
---

# Language and messaging prohibitions

From the founder's single source of truth for how Vanna describes itself
(Notion › Vanna — Current Thesis › Vanna — Language & Messaging, settled Sept 2026
across the Monad Studio, Superteam Canada and Cyber Fund applications).
