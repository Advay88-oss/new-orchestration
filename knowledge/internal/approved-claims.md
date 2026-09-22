# Vanna Internal Knowledge: Approved Claims Registry

**Governing Policy:** Only claims explicitly listed with status `VERIFIED` may be stated as fact in external communications. All claims must carry their verified source references.

---

## 1. Verified Protocol Claims (Claim Tier: VERIFIED)

| Claim ID | Approved Text / Capability | Permitted Scope | Verified Source File |
|---|---|---|---|
| `CLM-001` | Vanna protocol consists of 14 smart contracts organized across 4 functional layers (Core, LendingPools, SmartAccount Sandboxes, RiskEngine). | Testnet & Architectural documentation | `registry/vanna_knowledge.json` |
| `CLM-002` | Dedicated SmartAccount contracts are deployed per user, providing isolated execution sandboxes for margin borrowing. | Testnet & Architecture | `registry/vanna_knowledge.json` |
| `CLM-003` | SmartAccounts support up to 10x leverage for capital deployment into external Soroban DeFi primitives. | Testnet execution capability | `registry/vanna_knowledge.json` |
| `CLM-004` | Composable integration architecture hooks directly into Blend (b-tokens), Aquarius (LP shares), and Soroswap (DEX swaps). | Testnet integrations | `registry/vanna_knowledge.json` |
| `CLM-005` | Vanna RiskEngine enforces a strict 1.10x Health Factor floor with polynomial interest rate adjustments. | Testnet risk modeling | `registry/vanna_knowledge.json` |
| `CLM-006` | Vanna operates on Stellar Soroban Testnet and connects via the Freighter non-custodial wallet. | Current live state | `registry/vanna_knowledge.json` |
| `CLM-007` | Dual-sided liquidity pool model: LPs deposit XLM/USDC to receive interest-bearing vTokens (vXLM / vUSDC). | Protocol mechanism | `registry/vanna_knowledge.json` |

---

## 2. Forbidden Claims (Claim Tier: PROHIBITED)

| Prohibited Claim | Reason for Prohibition | Enforcement Action |
|---|---|---|
| ❌ "Vanna is live on Stellar Mainnet" | False. Active on Testnet only. | Instant rejection by Critic agent. |
| ❌ "Vanna has $X million TVL" | False. Testnet liquidity is for testing only. | Instant rejection by Critic agent. |
| ❌ "Audit completed by [Firm]" | False. Formal audits pending pre-mainnet. | Instant rejection by Critic agent. |
| ❌ "Zero liquidation risk / Guaranteed yield" | Mathematically and legally false. | Instant rejection by Critic agent. |
| ❌ "Token / Airdrop / Points launch" | False. Vanna has no token or points system. | Instant rejection by Critic agent. |
