# Vanna Internal Knowledge: Approved vs Rejected Positioning

**Governing Rule:** Every piece of copy, campaign brief, and strategic brief must align with the approved positioning pillars. Any draft using rejected framing is immediately rejected by the Critic agent.

---

## 1. Approved Positioning Pillars

### Pillar 1 · "The Composable Credit Primitive on Stellar Soroban"
* **The Positioning:** Vanna is not an isolated consumer lending app; it is the **credit layer** that connects Stellar's DeFi primitives (Blend b-tokens, Aquarius LP shares, Soroswap DEX trades).
* **The Metaphor:** Vanna is the "programmable margin router" for Soroban.
* **Why It Works:** Positions Vanna as foundational infrastructure that others build on top of, rather than a competing front-end.

### Pillar 2 · "Dedicated SmartAccount Sandboxes (Isolated Execution)"
* **The Positioning:** Every borrower commands their own on-chain SmartAccount contract. Up to 10x leverage is executed inside a personal sandbox, preventing cross-account risk contagion.
* **The Contrast:** Aave pools all risk into monolithic contracts; Morpho isolates only 2-token pairs. Vanna isolates the *execution sandbox*, allowing multi-protocol composability.

### Pillar 3 · "Mathematical Defense: The 1.10x RiskEngine Floor"
* **The Positioning:** Liquidation should not be a surprise ambush. Vanna's polynomial rate model creates an active 1.10x defense buffer before irreversible liquidation penalties hit.
* **The Contrast:** Incumbents liquidate immediately at 1.00x or LLTV, triggering predator bot liquidations.

---

## 2. Explicitly Rejected Positioning (Do Not Use)

| Rejected Framing | Why It Was Rejected | Founder Guidance |
|---|---|---|
| ❌ **"The Next Aave on Stellar"** | Derivative and lazy. Makes Vanna look like an unoriginal fork of Ethereum lending rather than a native Soroban primitive. | *"Never call ourselves the Aave of Stellar. We have SmartAccounts; Aave is a monolithic shared pool."* |
| ❌ **"Algorithmic High-Yield Savings"** | Evokes toxic memories of Anchor Protocol (Terra) and Celsius. Attracts unsophisticated retail expecting guaranteed 20% APY. | *"We are institutional credit infrastructure, not a retail high-yield bank."* |
| ❌ **"Zero-Risk / Guaranteed Margin"** | Factually false and legally toxic. In extreme black-swan market drops, positions can and will be liquidated. | *"If we claim zero risk, the Critic agent must immediately fail the draft."* |
| ❌ **"Points / Airdrop Season 1"** | Attracts sybil bots and mercenary farmers who dump the moment rewards stop. Destroys credit risk modeling. | *"No points. Both lending leaders (Aave, Morpho) abstained from points programs."* |
| ❌ **"Mainnet Live / Audited Security"** | Violates the pre-mainnet testnet claim gate. Destroys technical credibility with sophisticated developers. | *"We are on testnet. Be loud and proud about testnet stress-testing."* |

---

## 3. Approved Taglines & Boilerplates

* **Primary Tagline:**  
  *"Composable Credit Infrastructure for Stellar Soroban."*
* **Functional Description:**  
  *"Vanna Protocol enables isolated SmartAccount execution sandboxes with up to 10x leverage, composable across Blend, Aquarius, and Soroswap, defended by an automated 1.10x RiskEngine floor."*
* **Developer Boilerplate:**  
  *"14 smart contracts in 4 modular layers on Stellar Testnet, engineered for native cross-protocol composability via Freighter."*
