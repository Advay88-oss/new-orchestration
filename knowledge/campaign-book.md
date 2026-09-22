# Vanna Brand & Campaign Design Book

**Purpose:** Visual and structural constraints for content generation. "Constraint first, rendering second." All visual generators (Pillow cards, motion graphics, charts) must adhere strictly to these rules before rendering.

---

## 1. Color Palette & Canvas Rules
* **Background Canvas:** Dark Indigo / Obsidian (`#0b0e14` or `#0f172a`). Never pure black (`#000000`) or white.
* **Primary Brand Accent:** Electric Cyan / Protocol Blue (`#00f0ff` / `#38bdf8`) for active health factors, primary hooks, and highlight nodes.
* **Secondary / Warning Accent:** Amber Orange (`#f59e0b`) for the 1.10x RiskEngine warning buffer zone.
* **Danger / Liquidation Accent:** Crimson Red (`#ef4444`) for liquidation penalty zones (< 1.00x).
* **Text Hierarchy:**
  * Primary Headings: Pure White (`#ffffff`), Bold.
  * Secondary / Meta text: Slate Muted (`#94a3b8`).
  * Borders / Dividers: Subtle Slate (`#1e293b`).

---

## 2. Typography Rules
* **Primary Font:** **Plus Jakarta Sans** (Weights: SemiBold 600, Bold 700).
* **Monospace / Code:** JetBrains Mono for smart contract addresses, hashes, and formula parameters.
* **Strict Anti-Overlap Rule:**
  * When rendering two-column or multi-column data cards, use **strict 180px / 220px column splits**.
  * Never let status labels ("Standardizing", "Testnet Active") overlap with numeric values.

---

## 3. Approved Layout Archetypes

### Archetype A · The 4-Layer Contract Architecture Card
* **Use Case:** Technical breakdown threads explaining Vanna's Soroban architecture.
* **Structure:**
  1. Top Layer: Core Engine (Factory, Router)
  2. Second Layer: LendingPools (XLM, USDC vTokens)
  3. Third Layer: Dedicated SmartAccounts (User Sandboxes)
  4. Bottom Layer: External Composable Protocols (Blend, Aquarius, Soroswap)
* **Visual Anchor:** Logo (Interlocking icon + wordmark) anchored at top-right.

### Archetype B · The 1.10x Buffer Defense Card
* **Use Case:** Risk management and liquidation comparison posts.
* **Structure:**
  * Left: Competitor Cliff (Instant 10% penalty at HF 1.00x).
  * Right: Vanna 1.10x Buffer Zone (Polynomial rate defense buffer before liquidation).
* **Visual Anchor:** Horizontal health factor slider transitioning from Green (> 1.10x) $\rightarrow$ Amber (1.10x - 1.00x) $\rightarrow$ Red (< 1.00x).

### Archetype C · The Deal / Recipe Summary Card
* **Use Case:** Credit memos and Soroban leverage walkthroughs.
* **Structure:** Clean 3-row stat card:
  * Row 1: Initial Collateral ($1,000 USDC)
  * Row 2: Borrowed Leverage (up to 10x via SmartAccount)
  * Row 3: Target Liquidity Destination (Aquarius AQUA/USDC LP)

---

## 4. Visual Anti-Patterns (Forbidden)
* ❌ No cartoonish meme art, rockets, or generic AI astronaut graphics.
* ❌ No cluttered dashboards with unreadable microscopic labels.
* ❌ No generic templates that could belong to any arbitrary crypto project.
