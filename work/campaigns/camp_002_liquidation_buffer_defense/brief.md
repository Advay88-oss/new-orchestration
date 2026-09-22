# Campaign Brief: Camp 002 Liquidation Buffer Defense

**Campaign ID:** `camp_002_liquidation_buffer_defense`
**Status:** READY_FOR_PRODUCTION · **Filter Policy:** `verdict__in=['OWN', 'ADAPT_STRUCTURE']`

## 1. Goal & Objective
* **Goal:** Position Vanna's 1.10x RiskEngine health factor floor as the mathematical defense against cascading liquidations on Stellar Soroban.

## 2. Target Audience (from knowledge/internal/audience.md)
* **Primary:** Segment A1 · Stellar / Soroban DeFi Farmers & Traders
* **Secondary:** Segment A3 · Ecosystem Builders & Protocol Integrators
* **Audience Pain Point:** Manual multi-transaction leverage looping across Blend/Aquarius and liquidation risk.

## 3. Approved Angle & Positioning (from knowledge/internal/positioning.md)
* **Pillar:** Pillar 1 ('The Composable Credit Primitive on Soroban') & Pillar 2 ('SmartAccount Sandboxes').
* **Rejected Framing Enforced:** Never call Vanna 'The Aave of Stellar'; never claim mainnet live or fake TVL.

## 4. Grounded Runnable Patterns (Filtered from Brain DB)
- **B2B Fintech Infrastructure Integration Hook** (`ADAPT_STRUCTURE`)
  - Target: Segment A3 · Ecosystem Builders & Protocol Integrators
  - Rebuts: Objection 1 · 'Why build on Stellar Soroban instead of Base/Arbitrum?'
  - Execution: Target: Segment A3. Pillar: Pillar 1. Answers Objection 1 using verified testnet SmartAccount capabilities.

- **The Round-Number Deposit Escalator** (`ADAPT_STRUCTURE`)
  - Target: Segment A1 · Stellar / Soroban DeFi Farmers & Traders
  - Rebuts: Objection 1 · 'Why build on Stellar Soroban instead of an established EVM L2?'
  - Execution: Target: Segment A1. Pillar: Pillar 1. Answers Objection 1 using verified testnet SmartAccount capabilities.

- **Crisis Solvency and Liquidation Stress Retrospective** (`OWN`)
  - Target: Segment A2 · Cross-Chain Margin Traders & Yield Seekers
  - Rebuts: Objection 3 · 'How is a 1.1x Health Factor floor actually different from standard liquidation?'
  - Execution: Target: Cross-chain margin traders (A2). Pillar: '1.10x RiskEngine Floor'. Rebuts Obj #3 by proving how Vanna's polynomial rate curve creates a protective buffer before sudden 10% liquidation penalties trigger.

## 5. Review Gates
* [ ] Writer drafts thread using only verified testnet claims.
* [ ] Critic asserts zero prohibited claims.
* [ ] Outcome logger records founder decision.