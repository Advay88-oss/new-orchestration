# Vanna Internal Knowledge: Customer Objections & Approved Answers

**Purpose:** Equip the Writer and Critic agents with the real counter-arguments and approved rebuttals. If a draft cannot answer these objections, it fails review.

---

## Objection 1 · "Why build on Stellar Soroban instead of an established EVM L2 like Base or Arbitrum?"
* **The Skeptic's Voice:** *"Base and Arbitrum have billions in liquidity and thousands of users. Stellar is just for cross-border payments. Nobody trades DeFi there."*
* **The Approved Answer:**
  * Stellar Soroban has sub-second finality, negligible fees, and native anchor rails for fiat on/off-ramps (MoneyGram, Circle USDC).
  * However, Soroban lacks **composable credit infrastructure**. While EVM has 50 competing lending forks cannibalizing the same TVL, Stellar has zero dedicated margin execution sandboxes. Vanna captures an uncontested ecosystem with native distribution.
* **Forbidden Answer:** Never claim Stellar has more DeFi TVL than Arbitrum. Acknowledge scale honestly.

---

## Objection 2 · "You're only on testnet with no audit — why should I take you seriously?"
* **The Skeptic's Voice:** *"Testnet means nothing. Talk to me when you're live on mainnet with real TVL and multiple audits."*
* **The Approved Answer:**
  * Testnet is where architecture is stress-tested. Vanna has deployed 14 smart contracts in 4 modular layers on Stellar Testnet, with real contract execution via the Freighter wallet.
  * We openly declare our testnet status. We do not invent mock yields or pretend to be battle-tested. Our code, contract telemetry, and mathematical rate models are public for technical inspection before mainnet capital is risked.
* **Forbidden Answer:** Never say "audits coming next week" or "mainnet is right around the corner". State current reality: **Testnet active, mainnet gated on formal verification**.

---

## Objection 3 · "How is a 1.1x Health Factor floor actually different from standard lending liquidation?"
* **The Skeptic's Voice:** *"Every protocol has a liquidation threshold. 1.1x is just a higher threshold where I get liquidated earlier!"*
* **The Approved Answer:**
  * In incumbent protocols (Aave/Morpho), when Health Factor touches 0.999 (or Borrow/Collateral touches LLTV), a third-party liquidator or MEV bot seizes 5%–10% of your collateral instantly.
  * In Vanna's RiskEngine, the **1.10x floor is a programmatic buffer zone**. Between 1.10x and 1.00x, polynomial rate adjustments kick in to incentivize partial debt rebalancing and position protection *before* catastrophic liquidation execution penalties destroy the borrower's principal.
* **Forbidden Answer:** Never claim "Vanna positions can never be liquidated" or "Zero liquidation risk". Liquidations still occur if collateral continues to crash through the buffer.

---

## Objection 4 · "What happens if Blend or Aquarius goes down or depegs?"
* **The Skeptic's Voice:** *"You are composable with external protocols. If Blend gets exploited, does my Vanna account get wiped?"*
* **The Approved Answer:**
  * Vanna uses **isolated SmartAccount sandboxes per user**. Unlike monolithic pools where one bad collateral asset can drain the entire liquidity pool, risk in Vanna is strictly ring-fenced inside the individual user's contract.
  * If an external integration fails, the loss is contained within that specific SmartAccount's composable leg—it cannot drain other users' deposits or the core Vanna LendingPools.
* **Forbidden Answer:** Do not claim third-party protocols are 100% safe. Always emphasize **isolation over systemic contagion**.

---

## Objection 5 · "Is there a token, points, or a whitelist airdrop?"
* **The Skeptic's Voice:** *"Where do I sign up for the points leaderboard? When is TGE?"*
* **The Approved Answer:**
  * Vanna has **no token, no points system, and no airdrop campaigns**.
  * Incentivized deposits in credit markets distort risk curves and attract mercenary capital that leaves the second yields decline. Vanna is building sustainable infrastructure that survives without token inflation.
* **Forbidden Answer:** Never hint at a "future governance token" or "early adopter rewards".
