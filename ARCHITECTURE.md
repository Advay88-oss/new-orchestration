# Vanna Protocol GTM Operating System (System 2) — Architecture Spec

Authoritative technical specification of the production autonomous GTM Operating System for **Vanna Protocol** (composable credit infrastructure on Stellar Soroban).

---

## 1. Executive Summary & Top-Level Topology

The Vanna GTM Operating System (System 2) is a continuous, closed-loop autonomous growth and marketing engine. It integrates **13 specialized autonomous agents** arranged in a hybrid parallel/sequential topology across four operational tracks: **Intelligence**, **Creative**, **Governance**, and **Learning**.

```
┌───────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                       FOUNDER DIRECTIVE / CRON DAEMON                                 │
└───────────────────────────────────────────────────┬───────────────────────────────────────────────────┘
                                                    │
                                                    ▼
┌───────────────────────────────────────────────────────────────────────────────────────────────────────┐
│ TRACK 1: INTELLIGENCE & REASONING (01 ──► 05)                                                         │
│                                                                                                       │
│  [Agent 01: Intelligence Scout] ── (Parallel Ingestion: Horizon, Blend v2, Soroswap, X, Reddit, TG)  │
│                   │                                                                                   │
│                   ▼                                                                                   │
│  [Agent 02: Opportunity Selector] ── (7-Dimension Scoring Matrix + Bayesian UCB Exploration)          │
│                   │                                                                                   │
│                   ▼                                                                                   │
│  [Agent 03: GTM Strategist] ── (Gemini 3.8 Flash Brain + 4 Quality Gates + Tri-Arc Positioning)       │
│                   │                                                                                   │
│                   ▼                                                                                   │
│  [Agent 04: Machine Library] ── (Verifies against 10 Empirical GTM Machines)                          │
│                   │                                                                                   │
│                   ▼                                                                                   │
│  [Agent 05: Campaign & Series Engine] ── (Vehicle Classification & Recurrence Tiering)                │
└───────────────────────────────────────────────────┬───────────────────────────────────────────────────┘
                                                    │
                                                    ▼
┌───────────────────────────────────────────────────────────────────────────────────────────────────────┐
│ TRACK 2: CREATIVE SYNTHESIS & MEDIA COMPOSITION (06 ──► 09)                                           │
│                                                                                                       │
│  [Agent 06: Content Creator & Channel Adapter] ── (Gemini 3.8 Flash + Anti-Slop Thread Splitter)      │
│                   │                                                                                   │
│                   ▼                                                                                   │
│  [Agent 07: Creative Director System] ── (Rotates 5 Metaphor Families + Compiles 9-Point Blueprint)   │
│         │                                                           │                                 │
│         ▼ (Bespoke 1:1 Prompt)                                      ▼ (Queue Composition)             │
│  [Agent 08: Visual Synthesis Engine]                         [Agent 09: Video Production Engine]      │
│  • Model: gemini-3.1-flash-image (Model Garden)              • Remotion React 41s Product Film        │
│  • Style: Obsidian void (#07020D) + Dual Ambient Blooms      • Audio: EBU R128 (-14 LUFS) ducking     │
│  • Constraint: 100% textless geometric physical metaphors    • Veo 3.1 3D asset generation            │
└───────────────────────────────────────────────────┬───────────────────────────────────────────────────┘
                                                    │
                                                    ▼
┌───────────────────────────────────────────────────────────────────────────────────────────────────────┐
│ TRACK 3: GOVERNANCE & HUMAN APPROVAL GATE (10 ──► 12)                                                 │
│                                                                                                       │
│  [Agent 10: Pre-Delivery Reviewer Firewall]                                                           │
│  • Model: Gemini 3.8 Flash Brain (Adversarial CMO / Risk Officer / Art Director)                      │
│  • 100-Point Editorial Rubric: Claim (30), Hook (20), Arc (15), Voice (15), Trend (10), Viral (10)    │
│  • Output: Decision verdict (PASS / REVISE / KILL) & Score                                            │
│                   │                                                                                   │
│                   ▼                                                                                   │
│  [Agent 12: Telegram Gateway & Listener]                                                              │
│  • HALTS AT STATE: WAITING_FOR_HUMAN                                                                  │
│  • Delivers interactive approval packet to Advay Anand (TG: 5501720892) & Mission Control Cockpit     │
│                   │                                                                                   │
│                   ▼  [ FOUNDER APPROVES: Mission Control UI or Telegram Button Callback ]             │
│                                                                                                       │
│  [Agent 11: Approved Dispatch Worker]                                                                 │
│  • Executes multi-channel publishing to X, LinkedIn, and Reddit                                       │
│  • Protected by persistent DispatchRetryQueue with exponential backoff retry                         │
└───────────────────────────────────────────────────┬───────────────────────────────────────────────────┘
                                                    │
                                                    ▼
┌───────────────────────────────────────────────────────────────────────────────────────────────────────┐
│ TRACK 4: CLOSED-LOOP TELEMETRY & REINFORCEMENT LEARNING (13)                                          │
│                                                                                                       │
│  [Agent 13: Closed-Loop Learning Engine & RL Bandit]                                                  │
│  • Ingests verified conversion telemetry from canonical performance_records.jsonl (NULL != 0)         │
│  • Multi-Armed Bandit with Bayesian UCB smoothing (Dirichlet/Beta prior)                              │
│  • Dynamically updates pattern weights in canonical patterns.jsonl                                    │
└───────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Model Hierarchy & Spending Architecture

### 2.1 Model Assignment Mandate
To ensure maximum reasoning depth without exceeding latency or quota limits, models are strictly segregated:

| Task / Domain | Canonical Model | Provider / Location | Prohibitions |
| :--- | :--- | :--- | :--- |
| **Strategy & Ingestion** | `gemini-3.8-flash` | Google Cloud Vertex AI (`us-central1`) | Prohibited from using `gemini-2.5-pro` |
| **Channel Copywriting** | `gemini-3.8-flash` | Google Cloud Vertex AI (`us-central1`) | Zero em dashes, anti-AI buzzword check |
| **Reviewer Firewall** | `gemini-3.8-flash` | Google Cloud Vertex AI (`us-central1`) | Adversarial 100-point rubric enforcement |
| **Visual Asset Generation**| `gemini-3.1-flash-image`| Google Cloud Model Garden (`vanna-mcp`, `global`)| Pure textless 3D geometric metaphors |
| **Video Asset Synthesis** | `veo-3.1-generate-001` | Google Cloud Model Garden (`vanna-mcp`, `us-central1`) | Remotion 41s 1080p composition |

### 2.2 Hard Dollar Spend Accounting (`:8900`)
Every call is routed through or reconciled with the **Spend Proxy Watchdog** (`pipeline/scripts/vertex_spend_proxy.py`) running on `http://127.0.0.1:8900`:
* **Proxy Metering:** Automatically tracks input/output tokens and rewrites model requests to `gemini-3.8-flash`.
* **Modality Accounting (`POST /_charge`):** Direct accounting endpoint to charge:
  * Reasoning tokens ($0.30 / 1M in, $2.50 / 1M out)
  * Visual image synthesis ($+0.0300 per asset)
  * Video generation ($+0.0080 per second)
* **$10.00 Hard Stop:** When cumulative spend reaches `$10.00`, the proxy returns `402 Payment Required`, halting all external model invocations to eliminate runaway API costs.

---

## 3. The 13 Specialized Autonomous Agents

### Track 1: Intelligence & Strategy
* **Agent 01 — Intelligence Scout & Parallel Stream Daemon:**
  * Runs a `ThreadPoolExecutor` querying 6 live data channels simultaneously: Stellar Horizon RPC, DeFiLlama Blend v2 API, Soroswap AMM API, Twitter protocol feeds, Reddit `r/defi`, and Telegram channels.
  * Applies hash-based deduplication against `pipeline/state/evidence.jsonl`.
* **Agent 02 — Multi-Track Opportunity Selector:**
  * Evaluates candidates across 7 dimensions (0.0 to 1.0) with diversity filtering.
  * Applies Bayesian Upper Confidence Bound (UCB) exploration bonus to discover high-alpha angles.
* **Agent 03 — GTM Strategist (Reasoning Engine):**
  * Powered by `gemini-3.8-flash`. Formulates core pain, narrative wedge, and proof points.
  * Evaluated across 4 Decision Quality Gates: *AudienceFitGate*, *ProductStageFitGate*, *ClaimConsistencyGate*, and *TriArcGate*.
* **Agent 04 — GTM Machine Library Engine:**
  * Maps strategies against an authoritative catalog of 10 empirical GTM machines (e.g., *MACH_04: Technical Telemetry Series*). Enforces prerequisite evidence rules.
* **Agent 05 — Campaign & Series Engine:**
  * Classifies content into structural vehicles: `ONE_OFF`, `RECURRING_SERIES`, or `CAMPAIGN`. Enforces recurrence tiering (`RECURRING_SYSTEM`).

### Track 2: Creative & Media Synthesis
* **Agent 06 — Content Creator & Channel Adapter:**
  * Powered by `gemini-3.8-flash`. Produces bespoke, platform-native copy for X (Twitter), LinkedIn, and Reddit.
  * Integrates a Smart Thread Splitter enforcing character limits (<280) without mid-sentence truncation and formatting with `[1/N]` numbering.
* **Agent 07 — Creative Director System:**
  * Enforces visual variety by rotating across 5 physical concept families: *Optical Refraction*, *Hydraulic Circuitry*, *Electromagnetic Dynamics*, *Monolithic Balance*, and *Structural Crystallization*.
  * Compiles a comprehensive 9-point visual blueprint.
* **Agent 08 — Visual Synthesis Engine:**
  * Powered by `gemini-3.1-flash-image` on Google Model Garden.
  * Strictly enforces Vanna brand tokens: deep obsidian canvas (`#07020D`), electric violet (`#471485`) bottom-left bloom, fuchsia-magenta (`#5E0D46`) top-right bloom, subtle analog film grain, $\ge 75\%$ negative space, and **zero text/numbers/letters**.
* **Agent 09 — Video Production Engine:**
  * Background rendering engine built on Remotion React and Google Veo 3.1.
  * Delivers 5-act studio-grade 41s product films with EBU R128 audio normalization (-14 LUFS) and -12dB dynamic voice ducking.

### Track 3: Governance & Distribution
* **Agent 10 — Pre-Delivery Reviewer Firewall:**
  * Adversarial quality gate enforcing the canonical **100-point editorial rubric**:
    * Claim Integrity (30 pts)
    * Hook Strength (20 pts)
    * Arc Coherence (15 pts)
    * Voice Fidelity (15 pts)
    * Trend Fit (10 pts)
    * Virality Mechanics (10 pts)
* **Agent 11 — Approved Dispatch Worker:**
  * Executes multi-channel distribution across X, LinkedIn, and Reddit **only after human approval is received**.
  * Supported by a persistent `DispatchRetryQueue` handling rate limits and transient network timeouts.
* **Agent 12 — Telegram Gateway & Listener:**
  * Interacts with founder Advay Anand (Telegram User ID `5501720892`).
  * Presents interactive mobile review cards with inline action buttons (`APPROVE`, `REVISE`, `KILL`).

### Track 4: Learning & Optimization
* **Agent 13 — Closed-Loop Learning Engine & RL Bandit:**
  * Evaluates post-distribution conversion telemetry (impressions, clicks, SmartAccount testnet sandbox deployments).
  * Uses a Multi-Armed Bandit with Bayesian UCB smoothing to adjust pattern weights in canonical `patterns.jsonl` once minimum sample thresholds ($N \ge 3$) are satisfied.

---

## 4. UI & Mission Control Observability (`hermes-mission`)

The Next.js 14 Mission Control Cockpit (`http://127.0.0.1:3000`) provides real-time observability and operational control:

```
┌─────────────────────────────────┐
│ 🔴 MISSION CONTROL              │
│ SYSTEM 2: 13-AGENT GTM OS       │
├─────────────────────────────────┤
│ 💬 Live debate            [●]   │ ──▶ Real-time deliberation across Capital Efficiency, Risk Relief & Agentic Credit
│ 📋 Runs Observatory        [N]  │ ──▶ Live telemetry streaming from pipeline/state/runs/*.meta.json
│ 🔍 Run Detail                   │ ──▶ Interactive inspection of copy, media, review scores & Founder Approval buttons
│ 🤖 13 GTM Agents          [13]  │ ──▶ Live status cards with 4-part telemetry (Inputs, Mechanism, Output, Verification)
│ ⚡ 13-Stage Matrix              │ ──▶ Execution profiler measuring exact latencies and parallel track throughput
│ 📡 Multi-Channel Feed      [N]  │ ──▶ Performance feed bound to performance_records.jsonl (NULL != 0)
│ 💰 Cost & Cap                   │ ──▶ Live spend dial and modality breakdown polling http://127.0.0.1:8900
│ 📝 Backend Topology             │ ──▶ Subsystem ping diagnostic verifying latency across Cockpit, Proxy, and Storage
└─────────────────────────────────┘
```

---

## 5. Directory Structure & Invariants

```
D:\new orchestration\
├── hermes-mission\                  # Next.js 14 Production Mission Control Dashboard (:3000)
│   ├── app\                         # Route handlers (api/run, api/runs, api/spend, api/scout)
│   ├── components\views\            # Runs, RunDetail, LiveDebate, Agents, Posts, Cost, Lifecycles
│   └── lib\                         # Viewmodel (viewmodel.ts) & type contracts
├── pipeline\
│   ├── gtm_orchestration\           # Strategist, Opportunity Selector, Machine Library, Schemas
│   ├── gtm_content\                 # Channel Adapter, Thread Splitter, Copywriting Engine
│   ├── gtm_publish\                 # Dispatch Worker, Social Publishers, Retry Queue
│   ├── gtm_storage\                 # AtomicJsonlStore, State DBs
│   ├── reviewer\                    # Pre-Delivery Reviewer Firewall & 100-point rubric
│   ├── video_pipeline\              # Remotion React Queue & Veo 3.1 video engine
│   ├── scripts\
│   │   ├── run_autonomous_gtm_master.py  # Master 13-Agent Autonomous Orchestrator
│   │   ├── vertex_spend_proxy.py         # Port 8900 Spend Proxy with /_charge
│   │   └── gemini_flash_image.py         # Gemini 3.1 Flash Image synthesis wrapper
│   ├── system1_extracted\           # Extracted System 1 IP (Tri-Arc personas, OKF bundle, doctrine)
│   │   ├── buzz-pack\               # 7 Agent personas, instructions.md, campaign-doctrine.md
│   │   └── okf\                     # 39 concepts, 33 rules, 4 fact tiers, 5 competitor battlecards
│   └── state\                       # Real-time JSON/JSONL persistence (runs, spend, receipts)
│       ├── runs\                    # Run metadata (*.meta.json)
│       ├── spend-ledger.json        # Live dollar spend accounting
│       └── posts_published.jsonl    # Social distribution receipts
```

---

## 6. How to Run System 2 Cold

1. **Start the Spend Proxy Watchdog:**
   ```bash
   python pipeline/scripts/vertex_spend_proxy.py --port 8900 --cap 10.0
   ```
2. **Start Mission Control Dashboard:**
   ```bash
   cd hermes-mission && npm run dev
   ```
3. **Execute an Autonomous Directives Run:**
   ```bash
   python pipeline/scripts/run_autonomous_gtm_master.py --directive "explain 10x composable margin on Blend v2 pools"
   ```
4. **Run the 24/7 Continuous Autonomous Daemon:**
   ```bash
   python pipeline/scripts/run_autonomous_gtm_master.py --continuous --interval 1800
   ```
5. **Run the Verification Test Suite:**
   ```bash
   python -m unittest discover pipeline/tests
   ```
