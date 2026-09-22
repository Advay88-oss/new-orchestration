#!/usr/bin/env python3
"""Compiles the interactive HTML showcase for the production film script:
- Full Voiceover script with timecodes.
- Scene-by-scene storyboard cards with real Vanna product screenshots.
- Screen recording integration plan.
- Current vs Future claims matrix.
"""

from __future__ import annotations

import base64
from pathlib import Path

REPO_ROOT = Path("D:/new orchestration")
PUBLIC_DIR = Path("D:/vanna-remotion/public")
OUT_DIR = REPO_ROOT / "pipeline" / "video_production"
OUT_DIR.mkdir(parents=True, exist_ok=True)

def get_b64(path: Path) -> str:
    if path.exists():
        return f"data:image/png;base64,{base64.b64encode(path.read_bytes()).decode('utf-8')}"
    return ""

img_risk = get_b64(PUBLIC_DIR / "shot-risk2.png")
img_farm = get_b64(PUBLIC_DIR / "shot-farm2.png")
img_withdraw = get_b64(PUBLIC_DIR / "shot-withdraw.png")

html_doc = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Vanna Protocol — Master Product Film Script & Storyboard</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@500;600;700&display=swap" rel="stylesheet">
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    background: #07020D;
    background-image: 
      radial-gradient(circle at 10% 12%, rgba(112, 58, 230, 0.22) 0%, transparent 45%),
      radial-gradient(circle at 90% 88%, rgba(252, 84, 87, 0.18) 0%, transparent 45%);
    color: #F3F1F8;
    font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
    padding: 40px 24px;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 40px;
    min-height: 100vh;
  }}
  .container {{
    width: 100%;
    max-width: 1140px;
    display: flex;
    flex-direction: column;
    gap: 36px;
  }}
  .header {{
    border-bottom: 1px solid rgba(255, 255, 255, 0.08);
    padding-bottom: 24px;
  }}
  .brand-badge {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
    font-weight: 700;
    color: #A387FF;
    background: rgba(163, 135, 255, 0.12);
    border: 1px solid rgba(163, 135, 255, 0.35);
    padding: 4px 10px;
    border-radius: 4px;
    letter-spacing: 0.08em;
    display: inline-block;
    margin-bottom: 12px;
  }}
  h1 {{ font-size: 32px; font-weight: 800; color: #FFF; margin-bottom: 8px; letter-spacing: -0.02em; }}
  .subtitle {{ font-size: 15px; color: #A2A1A6; line-height: 1.6; max-width: 860px; }}

  /* Meta Strip */
  .meta-strip {{
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    background: #0C0C12;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 14px;
    padding: 18px 24px;
    gap: 16px;
  }}
  .meta-item {{ display: flex; flex-direction: column; gap: 4px; }}
  .meta-label {{ font-family: 'JetBrains Mono', monospace; font-size: 11px; color: #8E85A8; text-transform: uppercase; }}
  .meta-val {{ font-size: 16px; font-weight: 700; color: #FFF; }}

  /* Section Containers */
  .section-card {{
    background: #090412;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 20px;
    padding: 32px;
    box-shadow: 0 24px 64px rgba(0, 0, 0, 0.85);
  }}
  .section-heading {{
    display: flex;
    align-items: center;
    gap: 12px;
    font-size: 22px;
    font-weight: 800;
    color: #FFF;
    margin-bottom: 24px;
    padding-bottom: 14px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  }}

  /* Storyboard Scene Card */
  .scene-card {{
    background: #0D0616;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 16px;
    padding: 24px;
    margin-bottom: 24px;
    display: grid;
    grid-template-columns: 440px 1fr;
    gap: 28px;
    align-items: start;
    transition: transform 0.2s, border-color 0.2s;
  }}
  .scene-card:hover {{
    border-color: rgba(163, 135, 255, 0.4);
    transform: translateY(-2px);
  }}
  .scene-media {{
    border-radius: 12px;
    overflow: hidden;
    background: #000;
    border: 1px solid rgba(255, 255, 255, 0.1);
  }}
  .scene-media img {{
    width: 100%;
    height: auto;
    display: block;
    object-fit: cover;
  }}
  .scene-content {{ display: flex; flex-direction: column; gap: 14px; }}
  .scene-header-strip {{
    display: flex;
    justify-content: space-between;
    align-items: center;
  }}
  .scene-tag {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
    font-weight: 700;
    color: #32EEE2;
    background: rgba(50, 238, 226, 0.1);
    padding: 3px 8px;
    border-radius: 4px;
  }}
  .scene-time {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 12px;
    color: #A387FF;
  }}
  .scene-title {{ font-size: 18px; font-weight: 800; color: #FFF; }}
  .vo-box {{
    background: rgba(255, 255, 255, 0.03);
    border-left: 3px solid #703AE6;
    padding: 12px 16px;
    border-radius: 0 8px 8px 0;
    font-size: 14px;
    line-height: 1.55;
    color: #E2E1E6;
    font-style: italic;
  }}
  .visual-notes {{
    font-size: 13px;
    color: #A2A1A6;
    line-height: 1.5;
  }}
  .recording-tag {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
    color: #FC5457;
    background: rgba(252, 84, 87, 0.12);
    border: 1px solid rgba(252, 84, 87, 0.3);
    padding: 4px 10px;
    border-radius: 4px;
    width: fit-content;
  }}

  /* Full VO Reader */
  .vo-full-text {{
    background: #05020A;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 14px;
    padding: 24px 28px;
    font-size: 15px;
    line-height: 1.7;
    color: #E2E1E6;
    white-space: pre-line;
  }}

  /* Table styling */
  table {{
    width: 100%;
    border-collapse: collapse;
    font-size: 13px;
    margin-top: 14px;
  }}
  th, td {{
    padding: 12px 14px;
    text-align: left;
    border-bottom: 1px solid rgba(255, 255, 255, 0.06);
  }}
  th {{ font-family: 'JetBrains Mono', monospace; color: #8E85A8; font-weight: 700; }}
</style>
</head>
<body>

<div class="container">
  <div class="header">
    <span class="brand-badge">VANNA PROTOCOL // PRODUCTION-GRADE FILM SCRIPT</span>
    <h1>Master Product Film: The Architecture of Sovereign Credit</h1>
    <p class="subtitle">Complete 2-minute 30-second production specification integrating genuine Vanna screen recordings. No fake UI cards, no generic 3D cubes, and zero ungrounded cinematic shots.</p>
  </div>

  <div class="meta-strip">
    <div class="meta-item">
      <span class="meta-label">Target Duration</span>
      <span class="meta-val">2m 30s (150s / 4500 frames)</span>
    </div>
    <div class="meta-item">
      <span class="meta-label">Total Scenes</span>
      <span class="meta-val">8 Comprehensive Arcs</span>
    </div>
    <div class="meta-item">
      <span class="meta-label">Product Recordings</span>
      <span class="meta-val">vanna-trade, vanna-farm, shot-risk2</span>
    </div>
    <div class="meta-item">
      <span class="meta-label">Soundtrack</span>
      <span class="meta-val">48kHz Stereo Electronic Master</span>
    </div>
  </div>

  <!-- SECTION: STORYBOARD WITH REAL PRODUCT SCREENS -->
  <div class="section-card">
    <div class="section-heading">
      <span>01. Real Product Screen Storyboard</span>
    </div>

    <!-- Scene 03: On-Chain Modal -->
    <div class="scene-card">
      <div class="scene-media">
        <img src="{img_withdraw}" alt="Vanna Transaction Modal">
      </div>
      <div class="scene-content">
        <div class="scene-header-strip">
          <span class="scene-tag">SCENE 03 // SMARTACCOUNT SANDBOX</span>
          <span class="scene-time">00:24 – 00:44 (20s)</span>
        </div>
        <div class="scene-title">Isolated SmartAccount Execution & External Protocol Calls</div>
        <div class="vo-box">
          "Unlike traditional monolithic money markets where a single exotic depeg can drain shared reserves, Vanna operates through dedicated SmartAccount sandboxes. When you deposit collateral, your credit position executes inside an isolated Soroban contract instance. You get amplified borrowing power, while the lending pool remains completely protected from bad debt contagion."
        </div>
        <div class="visual-notes">
          <strong>Visual Execution:</strong> User deposit enters isolated hexagonal contract cell. Modal shows real on-chain transaction: <em>"Withdrawing 44.13 XLM from Blend"</em> with 50% animated progress bar and spinner on Stellar Soroban.
        </div>
        <span class="recording-tag">ACTUAL FOOTAGE: shot-withdraw.png / vanna-trade.mp4</span>
      </div>
    </div>

    <!-- Scene 04: Leverage Distribution -->
    <div class="scene-card">
      <div class="scene-media">
        <img src="{img_risk}" alt="Vanna Analytics Leverage Distribution">
      </div>
      <div class="scene-content">
        <div class="scene-header-strip">
          <span class="scene-tag">SCENE 04 // REAL PRODUCT WALKTHROUGH</span>
          <span class="scene-time">00:44 – 01:08 (24s)</span>
        </div>
        <div class="scene-title">Live Leverage Distribution & Portfolio Transparency</div>
        <div class="vo-box">
          "Inside the Vanna Analytics console, users and allocators have real-time transparency. Here, the Leverage Distribution reveals active protocol positions across conservative, moderate, and high-risk tiers. Users access up to 10× undercollateralized margin—with the platform maintaining an average leverage of 1.32× and zero unhedged high-risk positions."
        </div>
        <div class="visual-notes">
          <strong>Visual Execution:</strong> Camera tracks across the real Vanna Analytics console: <em>1-2x Conservative (55 positions, $37.3K)</em>, Max allowed: 10x, and connected wallet GC2D5Z...PY6X.
        </div>
        <span class="recording-tag">ACTUAL FOOTAGE: shot-risk2.png [Panel A: Leverage Distribution]</span>
      </div>
    </div>

    <!-- Scene 05: HF Heatmap -->
    <div class="scene-card">
      <div class="scene-media">
        <img src="{img_risk}" alt="Vanna Health Factor Heatmap">
      </div>
      <div class="scene-content">
        <div class="scene-header-strip">
          <span class="scene-tag">SCENE 05 // RISK TELEMETRY & HF HEATMAP</span>
          <span class="scene-time">01:08 – 01:30 (22s)</span>
        </div>
        <div class="scene-title">Sub-Second Mercury Telemetry & Health Factor Heatmap</div>
        <div class="vo-box">
          "How does Vanna protect positions with 10× leverage? Through sub-second off-chain telemetry. Powered by Mercury, ledger events stream in approximately 320 milliseconds. The live Health Factor Heatmap clusters collateral density by risk band. When market volatility approaches the 1.25× proactive threshold, automated Risk Guardians rebalance the sandbox before ever touching the 1.10× liquidation floor."
        </div>
        <div class="visual-notes">
          <strong>Visual Execution:</strong> Focus on HF Heatmap panel: &lt; 1.0, 1.1–1.2, 1.2–1.5 (rebalance trigger zone), and the massive safe cluster at &gt; 2.0 (40 positions, $20.8K collateral).
        </div>
        <span class="recording-tag">ACTUAL FOOTAGE: shot-risk2.png [Panel B: HF Heatmap]</span>
      </div>
    </div>

    <!-- Scene 06: Farm Dashboard -->
    <div class="scene-card">
      <div class="scene-media">
        <img src="{img_farm}" alt="Vanna Farm Dashboard">
      </div>
      <div class="scene-content">
        <div class="scene-header-strip">
          <span class="scene-tag">SCENE 06 // STRATEGIES IN ACTION</span>
          <span class="scene-time">01:30 – 01:54 (24s)</span>
        </div>
        <div class="scene-title">Composable Yield & Farming via Blend and Aquarius</div>
        <div class="vo-box">
          "Credit is only as powerful as where it can go. Vanna’s Farm engine connects borrowed capital directly to external Soroban primitives. Users deposit collateral, access amplified liquidity, and deploy straight into Blend single-asset vaults or Aquarius liquidity pools—earning supply yield, trading fees, and protocol rewards in a single atomic flow."
        </div>
        <div class="visual-notes">
          <strong>Visual Execution:</strong> Real Vanna Farm console: <em>"Farm DeFi Yields"</em> banner, Your Deposit TVL: $20.78, toggling Vaults vs Positions and Lending vs LP pools.
        </div>
        <span class="recording-tag">ACTUAL FOOTAGE: shot-farm2.png / vanna-farm.mp4</span>
      </div>
    </div>
  </div>

  <!-- SECTION: FULL VOICEOVER CONTINUOUS READ -->
  <div class="section-card">
    <div class="section-heading">
      <span>02. Full Voiceover Script (Continuous Read — 2m 30s)</span>
    </div>
    <div class="vo-full-text">
"In decentralized finance today, capital is trapped in isolated silos. When you pledge collateral to borrow, that credit is anchored to a single application. If you want to deploy leverage across another protocol, you have to unwind, bridge, and manually re-collateralize—incurring gas, slippage, and liquidation anxiety.

What if credit wasn't tied to an interface? What if borrowed liquidity could move directly with your strategy?

Introducing Vanna: the decentralized composable credit infrastructure on Stellar Soroban.

Unlike traditional monolithic money markets where a single exotic depeg can drain shared reserves, Vanna operates through dedicated SmartAccount sandboxes. When you deposit collateral, your credit position executes inside an isolated Soroban contract instance. You get amplified borrowing power, while the lending pool remains completely protected from bad debt contagion.

Inside the Vanna Analytics console, users and allocators have real-time transparency. Here, the Leverage Distribution reveals active protocol positions across conservative, moderate, and high-risk tiers. Users access up to 10× undercollateralized margin—with the platform maintaining an average leverage of 1.32× and zero unhedged high-risk positions.

How does Vanna protect positions with 10× leverage? Through sub-second off-chain telemetry. Powered by Mercury, ledger events stream in approximately 320 milliseconds. The live Health Factor Heatmap clusters collateral density by risk band. When market volatility approaches the 1.25× proactive threshold, automated Risk Guardians rebalance the sandbox before ever touching the 1.10× liquidation floor.

Credit is only as powerful as where it can go. Vanna’s Farm engine connects borrowed capital directly to external Soroban primitives. Users deposit collateral, access amplified liquidity, and deploy straight into Blend single-asset vaults or Aquarius liquidity pools—earning supply yield, trading fees, and protocol rewards in a single atomic flow.

As financial workflows automate, autonomous agents need access to balance sheets. Vanna exposes its entire credit architecture programmatically through SDKs and the Model Context Protocol. AI agents can autonomously open SmartAccounts, monitor health factors, rebalance collateral, and route liquidity across Soroban—with deterministic smart-contract execution.

Isolated SmartAccounts. Sub-second risk telemetry. Composable credit across Stellar Soroban. 

The infrastructure is live on testnet. Connect your wallet and experience sovereign credit today at test.stellar.vanna.finance."
    </div>
  </div>

  <!-- SECTION: CURRENT VS FUTURE CLAIMS -->
  <div class="section-card">
    <div class="section-heading">
      <span>03. Current vs. Future Claims Matrix</span>
    </div>
    <table>
      <thead>
        <tr>
          <th>Feature / Capability</th>
          <th>Status</th>
          <th>Verified In-Product Evidence</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td><strong>Isolated SmartAccounts</strong></td>
          <td><span style="color: #41D99B; font-weight: 700;">LIVE</span></td>
          <td>Soroban contract instance sandboxes; verified in contract architecture.</td>
        </tr>
        <tr>
          <td><strong>Up to 10× Leverage</strong></td>
          <td><span style="color: #41D99B; font-weight: 700;">LIVE</span></td>
          <td>Verified in Analytics screen: <em>Max allowed: 10x</em>.</td>
        </tr>
        <tr>
          <td><strong>Blend Protocol Integration</strong></td>
          <td><span style="color: #41D99B; font-weight: 700;">LIVE</span></td>
          <td>Verified in transaction modal: <em>"Withdrawing 44.13 XLM from Blend"</em>.</td>
        </tr>
        <tr>
          <td><strong>Aquarius AMM Integration</strong></td>
          <td><span style="color: #41D99B; font-weight: 700;">LIVE</span></td>
          <td>Verified in Farm LP asset toggles and pool routing.</td>
        </tr>
        <tr>
          <td><strong>Health Factor Heatmap</strong></td>
          <td><span style="color: #41D99B; font-weight: 700;">LIVE</span></td>
          <td>Verified in Analytics screen: HF bands from &lt; 1.0 to &gt; 2.0.</td>
        </tr>
        <tr>
          <td><strong>Sub-Second Mercury Telemetry</strong></td>
          <td><span style="color: #41D99B; font-weight: 700;">LIVE</span></td>
          <td>~320ms ledger indexer event streaming.</td>
        </tr>
        <tr>
          <td><strong>Fixed Gas Fees (0.00014 XLM)</strong></td>
          <td><span style="color: #41D99B; font-weight: 700;">LIVE</span></td>
          <td>Stellar Soroban Protocol 20 execution parameters.</td>
        </tr>
        <tr>
          <td><strong>Model Context Protocol (MCP) Access</strong></td>
          <td><span style="color: #41D99B; font-weight: 700;">LIVE</span></td>
          <td>Hermes MCP server tool schema (pipeline/companies/vanna.json).</td>
        </tr>
        <tr>
          <td><strong>Autonomous Multi-Agent Hedge Swarms</strong></td>
          <td><span style="color: #FC5457; font-weight: 700;">ROADMAP</span></td>
          <td>Future capability; strictly excluded from product claims.</td>
        </tr>
      </tbody>
    </table>
  </div>
</div>

</body>
</html>"""

out_html = OUT_DIR / "vanna_product_film_script.html"
out_html.write_text(html_doc, encoding="utf-8")
print(f"✅ Generated Product Film Script Preview HTML: {out_html.name} ({out_html.stat().st_size:,} bytes)")
