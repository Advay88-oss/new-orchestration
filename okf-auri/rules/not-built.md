---
type: Claim Rule Set
title: Not-built guardrails
description: Features described publicly that do NOT exist in code. Never claim them as live.
tags:
- safety
- blocking
- roadmap
status: stable
verified:
- by: human:advay
  at: '2026-08-11T00:00:00Z'
sources:
- id: auri-internal
  resource: /auri data/06-status-and-roadmap.md
  title: Auri internal status/roadmap (honest version)
rule_count: 5
rules:
- id: AUNB1-fiat
  severity: BLOCK
  pattern: \b(?:fund(?:ed|ing)?|deposit|top[- ]?up)\b[^.]{0,20}\b(?:Interac|ACH|e-?Transfer|bank|debit)\b|\bInterac
    e-?Transfer\b
  why: Fiat on-ramp (ACH/Interac) is NOT built (doc 06). The landing site's 'fund by Interac' is a destination,
    not live.
  fix: Do not claim fiat funding. Speak to the money engine, self-custody, or the API instead.
  flags:
  - IGNORECASE
- id: AUNB2-card
  severity: BLOCK
  pattern: \bAuri card\b|\btap (?:your |the )?card\b|\bcard[- ]spends?\b|\bspend (?:straight )?from (?:your
    )?gold\b
  why: The Auri card is NOT built - no issuer selected, no code (doc 06).
  fix: Remove any card claim. Spending via card is roadmap, not live.
  flags:
  - IGNORECASE
- id: AUNB3-devtools
  severity: BLOCK
  pattern: \bMCP server\b|\bAuri CLI\b|\bauri binary\b|\bcommand[- ]line tool\b
  why: MCP server and CLI are documented but are placeholder package names - NOT built (doc 06). The REST
    API is the live developer surface.
  fix: Claim the live REST API + scoped keys, not MCP or CLI.
  flags:
  - IGNORECASE
- id: AUNB4-chain
  severity: BLOCK
  pattern: \bArbitrum\b|\bon Base\b|\bBase chain\b
  why: Ethereum mainnet (chain 1) is the only live chain. Arbitrum is partially wired but not live; Base
    has no XAUT (doc 02, 06).
  fix: Say Ethereum mainnet, or omit the chain.
  flags:
  - IGNORECASE
- id: AUNB5-kyc-remit
  severity: BLOCK
  pattern: \bremittance\b|\bsend (?:gold )?to India\b|\bINR payout\b|\bKYC[- ]?(?:verified|compliant|approved)\b|\bfully
    KYC\b
  why: Remittance corridors are NOT built; KYC has no real provider and auto-approves outside production
    (doc 06).
  fix: Do not claim remittance or KYC. These are roadmap.
  flags:
  - IGNORECASE
---

# Not-built guardrails

From the internal honest status ([06-status-and-roadmap.md](/auri data/06-status-and-roadmap.md)). The landing site markets the destination; these features are **not in code**. Claiming them live destroys trust with partners and users.

**Not built:** fiat on-ramp (ACH/Interac), the Auri card, MCP server, CLI, Arbitrum path, real KYC, remittance corridors, no-account claim links, on-chain Boost leverage, mobile apps.

**Live instead (claim these):** the money engine (buy/sell/borrow/repay), self-custody + session keys, XAUT/Morpho, and the **public REST API + scoped keys + developer portal** (private beta).
