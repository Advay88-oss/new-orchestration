# Vanna Internal Knowledge: Target Audiences

**Last Updated:** September 10, 2026  
**Status:** Approved by Founder  
**Scope:** Pre-Mainnet Testnet → Early Mainnet Roadmap

---

## 1. Audience Segmentation Matrix

| Segment | Who They Are | What They Care About (Job to be Done) | What They Hate / Fear | Where They Hang Out |
|---|---|---|---|---|
| **A1 · Stellar / Soroban DeFi Farmers & Traders** | Existing active users on Stellar Testnet & Mainnet using Blend, Aquarius, or Soroswap. | Maximizing yield on idle XLM/USDC; getting leverage on LP positions without manual looping. | Getting liquidated by 1-second price wicks; complex multi-transaction manual borrowing; high slippage. | Discord, Telegram (Stellar Global), X (@StellarOrg community). |
| **A2 · Cross-Chain Yield Seekers (EVM / Solana Migrants)** | Yield farmers looking for fresh yield frontiers with low gas fees and uncontested farming opportunities. | Capital efficiency (10x leverage); clear interest rate models; transparency on liquidation risk. | Hidden admin keys; opaque risk models; mercenary points programs that dump on them. | Crypto Twitter / X, DeFi debriefs, specialized alpha Telegram chats. |
| **A3 · Ecosystem Builders & Protocol Integrators** | Developers building dApps, vaults, or trading bots on Soroban looking for credit rails. | Programmable SmartAccount primitives; simple Soroban SDKs; composability with Blend/Aquarius. | Closed-source contracts; rigid pairwise lending pools; protocols that don't support contract-to-contract calls. | Stellar Developer Discord, GitHub, developer hackathons. |

---

## 2. Segment Deep-Dives

### Segment A1 · The Stellar Native Farmer
- **Context:** Stellar Soroban is a rising smart contract layer, but liquidity is fragmented across Blend (monolithic lending) and Aquarius (AMM pools).
- **The Core Problem:** To loop leverage, a user has to manually deposit, borrow, swap on Soroswap, deposit LP into Aquarius, and repeat. It costs time and risks slippage.
- **What Vanna Gives Them:** Dedicated on-chain **SmartAccount sandboxes** that execute up to 10x leveraged yield loops in an automated, isolated smart contract.
- **Tone to Use:** Practical, native, respectful of the Stellar community ethos (financial access, low transaction fees, speed).

### Segment A2 · The Cross-Chain Margin Trader
- **Context:** Experienced with Aave V3 on Arbitrum or Morpho Blue on Ethereum. They understand Health Factors, Loan-to-Value (LTV), and oracle latency.
- **The Core Problem:** They are tired of losing collateral to aggressive MEV liquidation bots the moment their Health Factor touches 0.999.
- **What Vanna Gives Them:** **1.10x RiskEngine Floor**. Vanna acts as the protective buffer—adjusting rates polynomially and warning the position before catastrophic 10% liquidation penalties hit.
- **Tone to Use:** Technical, mathematical, numbers-first, institutional. Never use hype words ("moon", "gem", "alpha").

### Segment A3 · The Soroban Developer / DAO Integrator
- **Context:** Building the next wave of Stellar fintech apps. They need credit primitives that don't force their users into separate custodial accounts.
- **What Vanna Gives Them:** Modular contract architecture (14 contracts across 4 layers). SmartAccounts are programmable endpoints that external apps can hook into.
- **Tone to Use:** Developer documentation style, architecture breakdowns, open-source transparency.

---

## 3. What We Do NOT Target (Exclusions)
- ❌ **Speculative Airdrop Hunters:** Users looking for points farming, quests, or token leaderboards. We do not have a token and will not run points gamification.
- ❌ **TradFi Non-Crypto Retail:** People who don't understand non-custodial wallets (Freighter). We are protocol infrastructure, not a neobank.
