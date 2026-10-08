# VANNA PROTOCOL — MASTER PRODUCTION FILM SCRIPT & STORYBOARD
**Document Version:** 2.4.0 (Production-Grade)  
**Target Duration:** 2 minutes 30 seconds (150 seconds / 4,500 frames @ 30fps)  
**Core Directive:** Grounded product storytelling using **real Vanna screen recordings** (`vanna-trade.mp4`, `vanna-farm.mp4`, `shot-risk2.png`, `shot-withdraw.png`), eliminating fake UI containers, generic 3D cubes, and uninformative cinematic diffusion shots.

---

## 1. NARRATIVE ARCHITECTURE OVERVIEW

```
[00:00 - 00:22] 01. THE PROBLEM: FRAGMENTED CAPITAL & CREDIT WALLS
[00:22 - 00:36] 02. INTRODUCING VANNA: THE COMPOSABLE CREDIT LAYER
[00:36 - 01:00] 03. HOW IT WORKS: ISOLATED SMARTACCOUNTS (THE SANDBOX)
[01:00 - 01:24] 04. PRODUCT DEMO: MARGIN DEPLOYMENT & LEVERAGE DISTRIBUTION
[01:24 - 01:46] 05. FEATURES IN ACTION: SUB-SECOND RISK & HF HEATMAP
[01:46 - 02:08] 06. STRATEGIES: COMPOUNDING YIELD & BLEND LP REBALANCING
[02:08 - 02:22] 07. THE AGENTIC MCP LAYER: FINANCIAL PRIMITIVES FOR AGENTS
[02:22 - 02:30] 08. SUMMARY, LIVE PRODUCT MONTAGE & FINAL CTA
```

---

## 2. SCENE-BY-SCENE PRODUCTION SPECIFICATION

---

### SCENE 01: THE TRAP OF STATIC CAPITAL
* **Timecode:** 00:00 – 00:12 (12 seconds)
* **Narrative Purpose:** Establish the fundamental friction in DeFi—capital and borrowing are locked inside isolated silos.
* **Voicemail / Audio Track:**
  > "In decentralized finance today, capital is trapped in isolated silos. When you pledge collateral to borrow, that credit is anchored to a single application. If you want to deploy leverage across another protocol, you have to unwind, bridge, and manually re-collateralize—incurring gas, slippage, and liquidation anxiety."
* **On-Screen Text:**  
  `THE PROBLEM: FRAGMENTED CREDIT`  
  `Collateral is locked in application silos.`
* **Visual Story:**  
  We open in a high-contrast dark space. Three distinct, separated glowing pools of capital sit in isolation. White capital filaments enter the first pool, but cannot pass the barrier to reach the yield opportunities in pools two and three. The capital remains trapped.
* **Actual Vanna Screen Required:**  
  None (Abstract structural problem setup).
* **Screen Recording Action:**  
  None.
* **Motion Graphics:**  
  Minimalist, elegant vector lines representing credit paths hitting an invisible barrier and stagnating. Micro-typography highlights `SLIPPAGE · CAPITAL DRAG · UNWINDING COSTS`.
* **Transition to Next Scene:**  
  Camera pushes forward directly between the two barrier walls into a centralized question.
* **Assets Required:** Vector motion canvas, sub-bass atmospheric drone.

---

### SCENE 02: THE NARRATIVE QUESTION & VANNA REVEAL
* **Timecode:** 00:12 – 00:24 (12 seconds)
* **Narrative Purpose:** Ask the core strategic question and introduce Vanna Protocol's canonical position.
* **Voicemail / Audio Track:**
  > "What if credit wasn't tied to an interface? What if borrowed liquidity could move directly with your strategy? Introducing Vanna: the decentralized composable credit infrastructure on Stellar Soroban."
* **On-Screen Text:**  
  `WHAT IF CREDIT COULD MOVE WITH THE STRATEGY?`  
  `VANNA // COMPOSABLE CREDIT INFRASTRUCTURE`
* **Visual Story:**  
  The barrier walls drop away as a clean, architectural vector lattice expands. In the center, the geometric Vanna monogram forms cleanly with coral and electric violet gradient lighting.
* **Actual Vanna Screen Required:**  
  Top navigation bar preview of `vanna.finance` (showing `Portfolio · Earn · Margin · Trade · Farm · Analytics`).
* **Screen Recording Action:**  
  Camera sweeps across the live top navigation bar of `vanna-trade.mp4` [00:01–00:05], highlighting the clean institutional UI and the `Pro` mode toggle.
* **Motion Graphics:**  
  Thin glowing lavender bracket indicators frame the top navigation bar, highlighting the `Margin` and `Farm` routes.
* **Transition to Next Scene:**  
  The `Margin` tab is clicked in the recording; camera zooms into the account activation state.
* **Assets Required:** `vanna-trade.mp4` [00:01–00:05], Vanna vector monogram.

---

### SCENE 03: HOW VANNA WORKS — THE SMARTACCOUNT SANDBOX
* **Timecode:** 00:24 – 00:44 (20 seconds)
* **Narrative Purpose:** Explain the core technical innovation—isolated SmartAccounts where credit executes without pool contagion.
* **Voicemail / Audio Track:**
  > "Unlike traditional monolithic money markets where a single exotic depeg can drain shared reserves, Vanna operates through dedicated SmartAccount sandboxes. When you deposit collateral, your credit position executes inside an isolated Soroban contract instance. You get amplified borrowing power, while the lending pool remains completely protected from bad debt contagion."
* **On-Screen Text:**  
  `DEDICATED SMARTACCOUNT SANDBOXES`  
  `Isolated execution. Zero cross-account contagion.`
* **Visual Story:**  
  We see an abstract diagram of the user's dedicated contract sandbox. A collateral deposit (XLM) enters. Instead of entering a communal bucket, it locks into a secure hexagonal perimeter. Surrounding protocol reserves remain completely separate.
* **Actual Vanna Screen Required:**  
  `vanna-trade.mp4` (or `shot-withdraw.png` modal).
* **Screen Recording Action:**  
  `shot-withdraw.png` modal overlay showing active smart contract interaction: `"Withdrawing 44.13 XLM from Blend"` with live animated progress bar and spinner, demonstrating on-chain execution with external protocols.
* **Motion Graphics:**  
  Laser incision line visually separates the user's SmartAccount sandbox from the background pool, with subtle text label `SOROBAN SMART CONTRACT INSTANCE`.
* **Transition to Next Scene:**  
  The contract modal completes; camera pans across to the live Analytics & Leverage dashboard.
* **Assets Required:** `shot-withdraw.png`, `vanna-trade.mp4`.

---

### SCENE 04: REAL PRODUCT WALKTHROUGH — LEVERAGE DISTRIBUTION
* **Timecode:** 00:44 – 01:08 (24 seconds)
* **Narrative Purpose:** Walk through the real product interface, showing real positions, leverage distribution, and margin parameters.
* **Voicemail / Audio Track:**
  > "Inside the Vanna Analytics console, users and allocators have real-time transparency. Here, the Leverage Distribution reveals active protocol positions across conservative, moderate, and high-risk tiers. Users access up to 10× undercollateralized margin—with the platform maintaining an average leverage of 1.32× and zero unhedged high-risk positions."
* **On-Screen Text:**  
  `REAL-TIME LEVERAGE DISTRIBUTION`  
  `Up to 10× Composable Margin · Max Allowed: 10×`
* **Visual Story:**  
  Direct, high-resolution capture of the live Vanna Analytics dashboard. The viewer sees the genuine interface, not a mock.
* **Actual Vanna Screen Required:**  
  `shot-risk2.png` / `vanna-trade.mp4` [00:15–00:35] — **Analytics > Positions > Leverage Distribution**.
* **Screen Recording Action:**  
  Mouse hovers over the Leverage Distribution panel:
  - Green bar highlighting `1-2x Conservative (55 positions, $37.3K)`.
  - Cursor tracks across `2-3x Moderate`, `3-5x Aggressive`, and `5-7x High Risk`.
  - Focuses on the summary footer: `Avg leverage: 1.32x | Max allowed: 10x | High-risk (>5x): 0`.
* **Motion Graphics:**  
  Slight 3D camera tilt (perspective: 1200px, rotateX: 4deg). A soft cyan halo highlights the `Max allowed: 10x` metric and the `Conservative` position volume.
* **Transition to Next Scene:**  
  Camera slides right from the Leverage Distribution panel into the adjacent Health Factor Heatmap.
* **Assets Required:** `shot-risk2.png`, `vanna-trade.mp4`.

---

### SCENE 05: SUB-SECOND RISK TELEMETRY & HF HEATMAP
* **Timecode:** 01:08 – 01:30 (22 seconds)
* **Narrative Purpose:** Explain how Vanna manages liquidation risk using sub-second Mercury indexer telemetry and live HF monitoring.
* **Voicemail / Audio Track:**
  > "How does Vanna protect positions with 10× leverage? Through sub-second off-chain telemetry. Powered by Mercury, ledger events stream in approximately 320 milliseconds. The live Health Factor Heatmap clusters collateral density by risk band. When market volatility approaches the 1.25× proactive threshold, automated Risk Guardians rebalance the sandbox before ever touching the 1.10× liquidation floor."
* **On-Screen Text:**  
  `SUB-SECOND MERCURY TELEMETRY (~320ms)`  
  `1.25× Proactive Rebalance · 1.10× Hard Liquidation Floor`
* **Visual Story:**  
  The camera centers on the actual Vanna **HF Heatmap** table.
* **Actual Vanna Screen Required:**  
  `shot-risk2.png` / `vanna-trade.mp4` [00:35–00:55] — **HF Heatmap Panel**.
* **Screen Recording Action:**  
  - Cursor highlights the rows: `< 1.0` (1 position), `1.1–1.2` (1 position), `1.2–1.5` (9 positions), and the massive safe cluster at `> 2.0` (40 positions, $20.8K collateral).
  - Shows the gradient legend from Low to High risk.
* **Motion Graphics:**  
  A glowing lavender tracking line overlays the `1.2-1.5` row with a dynamic annotation: `PROACTIVE DEFENSIVE REBALANCE ZONE`. A green beacon illuminates `SAFE SOLVENT CLUSTER (>2.0 HF)`.
* **Transition to Next Scene:**  
  The user clicks the `Farm` tab in the top navigation bar; camera smoothly dollies into the Farm interface.
* **Assets Required:** `shot-risk2.png`, `vanna-trade.mp4`.

---

### SCENE 06: STRATEGIES IN ACTION — COMPOSABLE YIELD & DEFI FARMING
* **Timecode:** 01:30 – 01:54 (24 seconds)
* **Narrative Purpose:** Demonstrate what users actually DO with Vanna—deploying borrowed margin composably into external DeFi protocols like Blend and Aquarius.
* **Voicemail / Audio Track:**
  > "Credit is only as powerful as where it can go. Vanna’s Farm engine connects borrowed capital directly to external Soroban primitives. Users deposit collateral, access amplified liquidity, and deploy straight into Blend single-asset vaults or Aquarius liquidity pools—earning supply yield, trading fees, and protocol rewards in a single atomic flow."
* **On-Screen Text:**  
  `COMPOSABLE YIELD & FARMING`  
  `Atomic deployment to Blend Protocol & Aquarius DEX`
* **Visual Story:**  
  The full live Vanna Farm dashboard opens, showing user metrics and vault selection.
* **Actual Vanna Screen Required:**  
  `shot-farm2.png` / `vanna-farm.mp4` [00:08–00:30] — **Farm Dashboard**.
* **Screen Recording Action:**  
  - Cursor hovers over `Your Deposit TVL: $20.78` and `Net Farm APY`.
  - Toggles between `Vaults` and `Positions`.
  - Toggles between `LP/Multiple Assets` and `Lending/Single Assets`.
  - Scrolls to show the pool catalog: `Asset`, `Protocol (Blend / Aquarius)`, `Total Deposits`, `Supply APY`, `Borrow APY`.
* **Motion Graphics:**  
  Clean vector branching lines emanate from the `Deposit TVL` card, showing arrows routing into the `Protocol: Blend` and `Protocol: Aquarius` badges.
* **Transition to Next Scene:**  
  The camera pulls back into an architectural schematic perspective, bridging humans to automated agents.
* **Assets Required:** `shot-farm2.png`, `vanna-farm.mp4`.

---

### SCENE 07: THE AGENTIC MCP LAYER (FINANCIAL PRIMITIVES FOR AI)
* **Timecode:** 01:54 – 02:14 (20 seconds)
* **Narrative Purpose:** Introduce Vanna's programmatic SDK and Model Context Protocol (MCP) access for autonomous AI agents.
* **Voicemail / Audio Track:**
  > "As financial workflows automate, autonomous agents need access to balance sheets. Vanna exposes its entire credit architecture programmatically through SDKs and the Model Context Protocol. AI agents can autonomously open SmartAccounts, monitor health factors, rebalance collateral, and route liquidity across Soroban—with deterministic smart-contract execution."
* **On-Screen Text:**  
  `PROGRAMMATIC & AGENTIC ACCESS`  
  `Model Context Protocol (MCP) · Automated Credit Management`
* **Visual Story:**  
  Split screen: on the left, an autonomous terminal / code execution window showing clean MCP tool calls (`vanna_open_account`, `vanna_get_health_factor`, `vanna_rebalance`). On the right, the live Vanna dashboard updating in real-time as the agent executes.
* **Actual Vanna Screen Required:**  
  `vanna-trade.mp4` (Analytics position update) paired with actual MCP schema code (`pipeline/companies/vanna.json`).
* **Screen Recording Action:**  
  Terminal shows MCP tool call response `status: "SOLVENT", health_factor: 1.45, gas_paid: "0.00014 XLM"`. The dashboard counter updates instantaneously.
* **Motion Graphics:**  
  Subtle terminal code highlights. Glowing cyan connector wire connects the agent terminal to the Vanna SmartAccount icon.
* **Current vs. Future Note:**  
  *Current capability:* SDK, smart contract calls, and Hermes MCP server integration.  
  *Roadmap:* Multi-agent automated rebalancing swarms.
* **Transition to Next Scene:**  
  Camera accelerates forward through the code window into a fast-paced live UI montage.
* **Assets Required:** Terminal screen recording of MCP call, `vanna-trade.mp4`.

---

### SCENE 08: LIVE PRODUCT MONTAGE & CALL TO ACTION
* **Timecode:** 02:14 – 02:30 (16 seconds)
* **Narrative Purpose:** Final high-energy montage of the real product screens, reinforcing institutional reliability and driving testnet action.
* **Voicemail / Audio Track:**
  > "Isolated SmartAccounts. Sub-second risk telemetry. Composable credit across Stellar Soroban. The infrastructure is live on testnet. Connect your wallet and experience sovereign credit today at test.stellar.vanna.finance."
* **On-Screen Text:**  
  `VANNA PROTOCOL`  
  `Credit Infrastructure for Stellar Soroban`  
  `test.stellar.vanna.finance`
* **Visual Story:**  
  Rhythmic 1-second cuts of genuine product footage:
  1. `02:14`: Mode toggle switching to `Pro`.
  2. `02:16`: Wallet `GC2D5Z...PY6X` connected.
  3. `02:18`: Leverage Distribution green conservative bar.
  4. `02:20`: Live transaction modal completing on Blend.
  5. `02:22`: Resolves into the full obsidian brand screen with Vanna monogram and glowing testnet URL.
* **Actual Vanna Screen Required:**  
  Montage clips from `vanna-trade.mp4`, `vanna-farm.mp4`, and `shot-withdraw.png`.
* **Motion Graphics:**  
  Sleek ambient violet & magenta radial gradient bloom, subtle film grain, and prominent typography.
* **Final Sound Cue:**  
  Full 48kHz resonant electronic chord resolve.
* **Assets Required:** `vanna-trade.mp4`, `vanna-farm.mp4`, `vanna-logo.png`, `vanna_sfx_soundtrack.wav`.

---

## 3. COMPLETE SCENE-BY-SCENE STORYBOARD TABLE

```
┌───────┬─────────────┬────────────────────────────────────┬─────────────────────────────┬────────────────────────────────────────────────────────┐
│ SCENE │ TIMECODE    │ NARRATIVE CONCEPT                  │ REAL PRODUCT FOOTAGE        │ VISUAL METAPHOR & MOTION                               │
├───────┼─────────────┼────────────────────────────────────┼─────────────────────────────┼────────────────────────────────────────────────────────┤
│ 01    │ 00:00–00:12 │ Fragmented capital & credit walls   │ None (Problem space)        │ Isolated capital pools behind impermeable barrier walls│
│ 02    │ 00:12–00:24 │ Vanna reveal & core question       │ vanna-trade.mp4 (Nav bar)   │ Barriers fall, Vanna monogram forms, live navbar sweep │
│ 03    │ 00:24–00:44 │ Isolated SmartAccount sandboxes    │ shot-withdraw.png (Modal)   │ User deposit enters isolated hexagonal contract cell   │
│ 04    │ 00:44–01:08 │ Live Leverage Distribution console │ shot-risk2.png (Analytics)  │ Cursor inspects 1-2x conservative tier, avg 1.32x lev  │
│ 05    │ 01:08–01:30 │ Sub-second telemetry & HF Heatmap  │ shot-risk2.png (HF table)   │ Collateral density heatmap & ~320ms rebalance trigger  │
│ 06    │ 01:30–01:54 │ Farm & composable Blend/Aquarius   │ shot-farm2.png (Farm UI)    │ Deposit TVL routes directly into external DeFi pools   │
│ 07    │ 01:54–02:14 │ Programmatic Model Context Protocol│ Terminal MCP execution      │ Split screen: autonomous agent call → live UI rebalance│
│ 08    │ 02:14–02:30 │ High-energy montage & testnet CTA  │ Rapid 1s cuts of real UI    │ Real cuts resolve into Vanna monogram & testnet URL    │
└───────┴─────────────┴────────────────────────────────────┴─────────────────────────────┴────────────────────────────────────────────────────────┘
```

---

## 4. REQUIRED PRODUCT SCREEN RECORDINGS PLAN

```
┌────────────────────┬─────────────────────────┬──────────────────────────┬─────────────────────────────────────┬──────────────────────────┬──────────┐
│ FILE NAME          │ EXACT SCREEN/TAB        │ START STATE              │ REQUIRED USER ACTION                │ END STATE                │ DURATION │
├────────────────────┼─────────────────────────┼──────────────────────────┼─────────────────────────────────────┼──────────────────────────┼──────────┤
│ vanna-trade.mp4    │ Analytics > Positions   │ Analytics overview open  │ Hover over Leverage Distribution &  │ Cursor on Avg leverage   │ 25 sec   │
│                    │                         │                          │ move across HF Heatmap risk rows    │ (1.32x) and Max (10x)    │          │
├────────────────────┼─────────────────────────┼──────────────────────────┼─────────────────────────────────────┼──────────────────────────┼──────────┤
│ vanna-farm.mp4     │ Farm > Vaults & Pools   │ Farm dashboard loaded    │ Toggle Vaults/Positions & Lending/  │ Hover over Deposit TVL   │ 24 sec   │
│                    │                         │                          │ LP; scroll to Blend/Aquarius pools  │ ($20.78) and Net APY     │          │
├────────────────────┼─────────────────────────┼──────────────────────────┼─────────────────────────────────────┼──────────────────────────┼──────────┤
│ shot-withdraw.png  │ On-Chain Contract Modal │ Modal pop-up centered    │ Transaction in progress:            │ 50% filled purple bar    │ 6 sec    │
│                    │                         │                          │ "Withdrawing 44.13 XLM from Blend"  │ with active spinner      │          │
├────────────────────┼─────────────────────────┼──────────────────────────┼─────────────────────────────────────┼──────────────────────────┼──────────┤
│ [RECORDING_MCP]    │ Developer CLI Terminal  │ Bash/Python prompt open  │ Execute `hermes tool call` to Vanna │ Returns health_factor    │ 8 sec    │
│                    │                         │                          │ MCP endpoint requesting account state│ 1.45 and 0.00014 XLM gas │          │
└────────────────────┴─────────────────────────┴──────────────────────────┴─────────────────────────────────────┴──────────────────────────┴──────────┘
```

---

## 5. CURRENT vs. FUTURE PRODUCT CLAIMS

* **CURRENT (VERIFIED IN CODE & SCREENS):**
  - Stellar Soroban Protocol 20 smart contracts.
  - Dedicated isolated SmartAccount contracts per user.
  - Composable leverage up to 10×.
  - Live Analytics console showing Leverage Distribution and HF Heatmap.
  - External integration with Blend Protocol single-asset vaults.
  - External integration with Aquarius AMM pools.
  - Fixed 0.00014 XLM transaction fee.
  - Sub-second ledger event streaming via Mercury indexer (~320ms).
  - Programmatic tool calling via Model Context Protocol (MCP) / SDK.

* **ROADMAP / FUTURE (DO NOT PRESENT AS LIVE PRODUCT):**
  - Cross-chain bridge integrations outside Stellar.
  - Fully autonomous multi-agent high-frequency hedge-fund swarms.
  - Instant one-click fiat onboarding.

---

## 6. REQUIRED AUDIO & MOTION ASSETS

1. **Audio:** `D:/vanna-remotion/public/vanna_sfx_soundtrack.wav` (48kHz stereo, sub-bass impacts, modular latches, harmonic risers, ~320ms telemetry pings, resolving pad chord).
2. **Video Captures:**
   - `D:/vanna-remotion/public/vanna-trade.mp4`
   - `D:/vanna-remotion/public/vanna-farm.mp4`
   - `D:/vanna-remotion/public/shot-risk2.png`
   - `D:/vanna-remotion/public/shot-farm2.png`
   - `D:/vanna-remotion/public/shot-withdraw.png`
3. **Logos & Vector Art:**
   - `D:/vanna-remotion/public/vanna-logo.png`
   - Vanna precise SVG geometric monogram with `#FC5457` $\rightarrow$ `#703AE6` linear gradient.
4. **Missing Assets:**
   - `[RECORDING_MCP]`: 8-second clean capture of an automated terminal calling the Vanna MCP tool interface. (Can be rendered programmatically in Remotion via terminal syntax component).

---

## 7. FINAL VOICEOVER SCRIPT (CONTINUOUS READ)

> "In decentralized finance today, capital is trapped in isolated silos. When you pledge collateral to borrow, that credit is anchored to a single application. If you want to deploy leverage across another protocol, you have to unwind, bridge, and manually re-collateralize—incurring gas, slippage, and liquidation anxiety.
>
> What if credit wasn't tied to an interface? What if borrowed liquidity could move directly with your strategy?
>
> Introducing Vanna: the decentralized composable credit infrastructure on Stellar Soroban.
>
> Unlike traditional monolithic money markets where a single exotic depeg can drain shared reserves, Vanna operates through dedicated SmartAccount sandboxes. When you deposit collateral, your credit position executes inside an isolated Soroban contract instance. You get amplified borrowing power, while the lending pool remains completely protected from bad debt contagion.
>
> Inside the Vanna Analytics console, users and allocators have real-time transparency. Here, the Leverage Distribution reveals active protocol positions across conservative, moderate, and high-risk tiers. Users access up to 10× undercollateralized margin—with the platform maintaining an average leverage of 1.32× and zero unhedged high-risk positions.
>
> How does Vanna protect positions with 10× leverage? Through sub-second off-chain telemetry. Powered by Mercury, ledger events stream in approximately 320 milliseconds. The live Health Factor Heatmap clusters collateral density by risk band. When market volatility approaches the 1.25× proactive threshold, automated Risk Guardians rebalance the sandbox before ever touching the 1.10× liquidation floor.
>
> Credit is only as powerful as where it can go. Vanna’s Farm engine connects borrowed capital directly to external Soroban primitives. Users deposit collateral, access amplified liquidity, and deploy straight into Blend single-asset vaults or Aquarius liquidity pools—earning supply yield, trading fees, and protocol rewards in a single atomic flow.
>
> As financial workflows automate, autonomous agents need access to balance sheets. Vanna exposes its entire credit architecture programmatically through SDKs and the Model Context Protocol. AI agents can autonomously open SmartAccounts, monitor health factors, rebalance collateral, and route liquidity across Soroban—with deterministic smart-contract execution.
>
> Isolated SmartAccounts. Sub-second risk telemetry. Composable credit across Stellar Soroban. 
>
> The infrastructure is live on testnet. Connect your wallet and experience sovereign credit today at test.stellar.vanna.finance."
