---
type: Facts Ledger
title: Tier A - quotable
description: Verified LIVE in code (doc 06); may be stated plainly.
tags:
- facts
tier: A
status: stable
verified:
- by: human:advay
  at: '2026-08-11T00:00:00Z'
sources:
- id: auri-internal
  resource: /auri data/06-status-and-roadmap.md
  title: Auri internal status/roadmap (honest version)
---

# Tier A - quotable

Verified **live in code** against the internal status doc (06), 2026-08-11:

- **The money engine**: buy, sell, borrow, repay, withdraw - live (`/api/execute/*`).
- **Self-custody**: owner key in a TEE (Privy); Auri holds $0; session keys are owner-signed, scoped, spend-capped, expiring. A leaked key or backend compromise cannot exceed caps, reach another account, or move funds out.
- **The gold**: Tether Gold (XAUT), allocated London Good Delivery, Swiss vault, **quarterly BDO Italia attestation**; 22+ tonnes, 1,792 bars, 707,747 oz (point-in-time - re-verify).
- **Lending**: Morpho Blue, XAUT collateral / USDT loan, **3.75% APR**, no credit check.
- **Chain**: Ethereum mainnet (chain 1) - the only live chain.
- **Public REST API + scoped API keys + developer portal - LIVE (private beta, access-code gated).** Idempotent writes, `read`/`trade` scopes, session-secured. This is the real B2B/infrastructure surface.
- Gift, referral, auto-invest (SIP/DCA), notifications - built.
- Passwordless login, gasless (paymaster) - live.
