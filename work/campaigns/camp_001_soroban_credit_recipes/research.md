# Campaign Research Grounding: Soroban Credit Recipes

**Campaign ID:** `camp_001_soroban_credit_recipes`  
**Source Knowledge:** Brain DB (`pipeline/gtm_engine/brain/db/` & `knowledge/`)

---

## 1. Relevant Competitor Patterns Extracted from Brain DB

### Pattern 1 · Credit Memo Format (`Credit Coop` — TVL $4.59M Outlier)
* **Brain DB Ref:** `patterns.jsonl` → `PAT_DEAL_CREDIT_MEMO` / `doc_10_uncollateralized_lending.md`
* **What They Do:** Publish open, step-by-step credit facility memos breaking down balance sheets and liquidation parameters.
* **How Vanna Adapts It:** Frame the campaign as a **"Sandbox Recipe"**—dissecting the exact math of a 10x leverage loop (e.g., $1,000 collateral commanding $10,000 credit) with exact liquidation price calculations.

### Pattern 2 · Role Decomposition Template (`Morpho` — Partner Embed)
* **Brain DB Ref:** `patterns.jsonl` → `PAT_B2B_FINTECH_HERO` / `morpho.md`
* **What They Do:** Always break an announcement down into clear roles: Underlying credit network (Morpho) $\rightarrow$ Risk curator (Steakhouse) $\rightarrow$ Settlement chain $\rightarrow$ Application.
* **How Vanna Adapts It:** Role decomposition for Soroban:
  * Margin Router: **Vanna SmartAccounts**
  * Lending Yield: **Blend Protocol (b-tokens)**
  * DEX Liquidity: **Aquarius (AQUA/USDC LPs)**
  * Risk Sentinel: **Vanna 1.1x RiskEngine**

### Pattern 3 · Double Yield Stacking (`Curve Finance` — cTokens Playbook)
* **Brain DB Ref:** `curve-finance.md` / `doc_01_pattern_matrix.md`
* **What They Do:** Stacking AMM swap fees directly on top of lending interest.
* **How Vanna Adapts It:** Explaining how Vanna SmartAccounts enable double-yield on Soroban without manual repositioning.

---

## 2. Anti-Patterns to Avoid (from `knowledge/internal/learnings.md`)
* ❌ Do NOT call Vanna "The Aave of Stellar" (Learnings L1).
* ❌ Do NOT use generic DeFi buzzwords without showing the 4 contract layers (Learnings L2).
* ❌ Do NOT mention simulated yields or future token rewards (Learnings L3 & L5).
