---
type: Claim Rule Set
title: Hard prohibitions
description: Claims that are false at this company's stage and must never be published.
tags:
- safety
- blocking
- stage
status: stable
generated:
  by: process:okf_export_rules
  at: '2026-08-10T00:00:00Z'
sources:
- id: gate-builtin
  resource: /pipeline/scripts/claim_safety_gate.py
  title: claim_safety_gate.HARD_PROHIBITIONS
rule_count: 14
rules:
- id: P1-mainnet-live
  severity: BLOCK
  pattern: \b(?:live on mainnet|now live|mainnet is live|launched on mainnet|trading live|funds are (?:live|deployed)|our
    mainnet|launch(?:ing)? soon|going live|(?:is|are|we'?re)\s+live(?!\s+on\s+(?:Stellar\s+)?testnet))\b
  why: Implies mainnet is live or imminent. Vanna is pre-mainnet, Stellar testnet only.
  fix: Say 'Currently on Stellar testnet. Mainnet addresses will be published at launch.'
  flags:
  - IGNORECASE
- id: P1-tvl
  severity: BLOCK
  pattern: \b(?:TVL|total value locked)\b
  why: There is no TVL. Vanna is pre-mainnet.
  fix: Remove entirely. No TVL figure of any kind may be published.
  flags:
  - IGNORECASE
- id: P2-security-claims
  severity: BLOCK
  pattern: \b(?:audited|audit(?:s)?\b|bug bount(?:y|ies)|multi-?sig|timelock(?:s|ed)?|formal(?:ly)? verif(?:ied|ication)|insur(?:ed|ance))\b
  why: No audits, bug bounty, multi-sig, timelocks, formal verification or insurance exist.
  fix: Say 'Security documentation is being published ahead of mainnet.'
  flags:
  - IGNORECASE
- id: P3-token
  severity: BLOCK
  pattern: \b(?:airdrop|token(?:omics)?\b|\$VANNA|points? program(?:me)?|early users will be remembered|retro(?:active)?
    reward|farming points)\b
  why: No token, airdrop, points or rewards exist. This is an absolute rule — including jokes, emoji and
    winks.
  fix: Remove entirely. Never hint otherwise, in any channel, ever.
  flags:
  - IGNORECASE
- id: P4-demo-as-result
  severity: BLOCK
  pattern: \b(?:our users earned|users earned|returns of|we delivered|traders earn(?:ed)?|generated returns)\b
  why: Presents demo/mock figures as realised results.
  fix: Label as 'illustrative example' / 'a worked scenario' / 'in this example'.
  flags:
  - IGNORECASE
- id: P5-returns-promise
  severity: BLOCK
  pattern: \b(?:guaranteed|risk-?free|can'?t lose|no downside|assured returns|promised? (?:returns|yield)|will
    earn)\b
  why: Promises or implies returns.
  fix: Remove. Use conditional framing and state that risk remains.
  flags:
  - IGNORECASE
- id: P6-financial-advice
  severity: BLOCK
  pattern: \b(?:you should (?:buy|invest|deposit|allocate)|we recommend (?:buying|investing)|financial
    advice|investment advice|(?:this|it) is a good investment)\b
  why: Constitutes financial, investment, legal or tax advice.
  fix: Remove. Describe mechanisms, never recommend allocation.
  flags:
  - IGNORECASE
- id: P7-competitor-superiority
  severity: BLOCK
  pattern: \b(?:better than|superior to|beats|outperforms|kills|destroys|replaces)\s+(?:Gearbox|Hyperliquid|Morpho|Aave|Blend|Compound|dYdX|GMX|Euler|Spark)\b
  why: Claims superiority over a named competitor. Explicitly forbidden.
  fix: 'Compare jobs-to-be-done instead: ''Gearbox is universal leverage. Vanna is built for derivatives
    and hedging.'' Use ''X vs Vanna'' framing, never superiority.'
  flags:
  - IGNORECASE
- id: P8-internal-leak
  severity: BLOCK
  pattern: \b(?:break-?even TVL|launch blocker|funding gap|scorecard|35/70|remove Stellar|single EVM L2|cut
    integrations|staged leverage rollout|43[- ]tool|design without execution)\b
  why: Tier E internal-only material. Never appears in external content.
  fix: Remove entirely.
  flags:
  - IGNORECASE
- id: P10-live-integrations
  severity: BLOCK
  pattern: \b(?:live|now|today|currently)\s+(?:\w+\s+){0,2}(?:perps?|options|prediction market|tokeni[sz]ed
    stock|AI[- ]compute)\s+(?:integration|support|trading|market)
  why: Claims live perps/options/prediction/tokenized-stock/AI-compute integrations. Only Blend, Aquarius
    and Soroswap are integrated, on testnet.
  fix: 'Use future tense: ''built for'' / ''designed for''. Name only Blend, Aquarius, Soroswap as live.'
  flags:
  - IGNORECASE
- id: P11-agent-autonomy
  severity: BLOCK
  pattern: \b(?:(?:our|the) AI trades for you|trades? on your behalf|fully autonomous trading|it trades
    while you sleep|bot trades your)\b
  why: Overstates the agent layer's autonomy. It is policy-bounded, human-approved, zero-custody.
  fix: Say 'You state the intent. The copilot compiles it into a guarded position and hands it back —
    nothing signs without you.'
  flags:
  - IGNORECASE
- id: P12-regulatory
  severity: BLOCK
  pattern: \b(?:compliant|licen[sc]ed|regulated|KYC-?ready|SEC[- ]approved|MiCA[- ]compliant|registered
    with)\b
  why: Makes a regulatory or compliance claim. None exist.
  fix: Remove entirely.
  flags:
  - IGNORECASE
- id: P14-fabricated-proof
  severity: BLOCK
  pattern: \b(?:our customer|our client|case study|testimonial|trusted by \d|\d+ companies use|as used
    by)\b
  why: Fabricates a customer, testimonial, case study or partnership. Ecosystem logos may not be described
    as customers.
  fix: Remove. Ecosystem logos can be shown as ecosystem only.
  flags:
  - IGNORECASE
- id: P13-infra-overclaim
  severity: BLOCK
  pattern: \b(?:production-?grade|enterprise-?grade|bank-?grade|military-?grade|carrier-?grade|battle-?tested|proven
    at scale|(?:99\.?\d*)\s*%?\s*uptime|SLA-?backed|five nines)\b
  why: Infrastructure emphasis is the campaign lead, but Vanna is on testnet — there is no production,
    so proven-reliability or proven-scale language is false.
  fix: Frame as architecture and design intent, e.g. 'built for B2B and B2C from one system' or 'designed
    to scale', not as proven production performance.
  flags:
  - IGNORECASE
---

# Hard prohibitions

Derived from the company's overriding constraint. Every rule here descends from [/company/constraint.md](/company/constraint.md) — if that constraint changes, this file is the first thing to rewrite.

For another company, replace these wholesale. A rule that names a concept the new company does not have is dead weight, and worse, it creates the impression the gate is configured when it is not.

## How these are applied

Each entry is a regular expression evaluated against the draft body. A match at severity `block` exits the gate non-zero and the draft never reaches a human reviewer. `warn` is recorded and does not stop the run.

`pattern` is the regex verbatim; `flags` are `re` module flag names. `why` is shown to the agent that wrote the draft, and `fix` tells it what to write instead — a rule without a usable `fix` produces a strategist that retries the same mistake.

## Editing

Change a pattern here and the gate picks it up on its next run; there is no build step. **Then prove it**: write a string that must be blocked and confirm it is.

```bash
python pipeline/scripts/claim_safety_gate.py --text "a claim that must block"
```
