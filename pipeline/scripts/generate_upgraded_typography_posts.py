#!/usr/bin/env python3
"""Generates 2 Upgraded Institutional Posts with dense, developer-grade typography.

Post 1: Automated Delta-Neutral Yield Harvester (10x Composable Leverage Loop)
Post 2: Continuous Polynomial RateModel (Dynamic Quantitative Dynamics)
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
STATE_DIR = REPO_ROOT / "pipeline" / "state"
STATE_DIR.mkdir(parents=True, exist_ok=True)

CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
if not os.path.exists(CHROME_PATH):
    for p in [
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe")
    ]:
        if os.path.exists(p):
            CHROME_PATH = p
            break

VANNA_MONOGRAM = """
<svg class="monogram-svg" viewBox="0 0 120 120" fill="none">
  <path d="M59.9886 16.0614C63.1147 13.6729 67.3757 13.3951 70.7757 15.3581C74.1757 17.3211 76.0413 21.1361 75.4986 25.0161L72.1417 49.0153L72.1454 49.0174L65.6912 95.1595L102.868 66.755L114.107 73.2444L68.4972 108.093C65.3711 110.481 61.11 110.759 57.7101 108.796C54.3101 106.833 52.4445 103.018 52.9872 99.138L56.3441 75.1388L56.3404 75.1367L62.7946 28.9947L25.6183 57.3991L14.3784 50.9098L59.9886 16.0614Z" fill="url(#p0)"/>
  <path d="M25.6183 57.3991L36.003 63.3948L33.9183 78.2994L45.9557 69.141L56.3404 75.1367L36.6411 90.1879C33.7348 92.4085 29.7734 92.6668 26.6125 90.8418C23.4545 89.0185 21.7201 85.4763 22.2206 81.872L25.6183 57.3991Z" fill="url(#p1)"/>
  <path d="M102.868 66.755L92.4828 60.7594L94.5675 45.8547L82.5301 55.0131L72.1454 49.0174L91.8447 33.9662C94.751 31.7457 98.7124 31.4874 101.873 33.3123C105.031 35.1356 106.766 38.6778 106.265 42.2822L102.868 66.755Z" fill="url(#p2)"/>
  <defs>
    <linearGradient id="p0" x1="44" y1="0" x2="128" y2="50" gradientUnits="userSpaceOnUse"><stop stop-color="#FC5457"/><stop offset="1" stop-color="#703AE6"/></defs>
    <linearGradient id="p1" x1="44" y1="0" x2="128" y2="50" gradientUnits="userSpaceOnUse"><stop stop-color="#FC5457"/><stop offset="1" stop-color="#703AE6"/></defs>
    <linearGradient id="p2" x1="44" y1="0" x2="128" y2="50" gradientUnits="userSpaceOnUse"><stop stop-color="#FC5457"/><stop offset="1" stop-color="#703AE6"/></defs>
  </defs>
</svg>
"""

# HTML Template for Post 1: Delta-Neutral Composable Architecture
HTML_POST1 = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600;700&display=swap');
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    width: 1200px;
    height: 675px;
    overflow: hidden;
    background-color: #07020D;
    background-image:
      radial-gradient(ellipse 65% 55% at 95% 15%, rgba(94, 13, 70, 0.75) 0%, rgba(62, 8, 49, 0.45) 40%, rgba(7, 2, 13, 0) 75%),
      radial-gradient(ellipse 70% 60% at 8% 90%, rgba(71, 20, 133, 0.85) 0%, rgba(42, 11, 82, 0.5) 45%, rgba(7, 2, 13, 0) 80%);
    color: #FFFFFF;
    font-family: 'Plus Jakarta Sans', sans-serif;
    position: relative;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    padding: 36px 48px;
  }}
  .film-grain {{
    position: absolute;
    top: 0; left: 0; width: 100%; height: 100%;
    opacity: 0.035;
    pointer-events: none;
    background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noiseFilter'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.8' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noiseFilter)'/%3E%3C/svg%3E");
    z-index: 1;
  }}
  .card-header {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    z-index: 2;
  }}
  .header-left {{
    display: flex;
    align-items: center;
    gap: 12px;
  }}
  .protocol-badge {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
    font-weight: 700;
    color: #A387FF;
    background: rgba(163, 135, 255, 0.12);
    border: 1px solid rgba(163, 135, 255, 0.3);
    padding: 4px 10px;
    border-radius: 4px;
    letter-spacing: 0.08em;
  }}
  .telemetry-meta {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
    color: #8C879E;
    letter-spacing: 0.05em;
  }}
  .monogram-svg {{
    width: 28px;
    height: 28px;
    opacity: 0.35;
  }}
  
  /* Main Architecture Stage */
  .stage-container {{
    position: relative;
    width: 100%;
    height: 420px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 20px;
    z-index: 2;
  }}

  /* Connector SVG */
  .flow-connector-svg {{
    position: absolute;
    top: 50%;
    left: 0;
    width: 100%;
    height: 60px;
    transform: translateY(-50%);
    z-index: 1;
    pointer-events: none;
  }}

  /* Individual Stage Cards */
  .arch-card {{
    background: rgba(14, 10, 24, 0.75);
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 16px;
    backdrop-filter: blur(14px);
    padding: 24px 22px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    height: 380px;
    z-index: 3;
    box-shadow: 0 16px 40px rgba(0, 0, 0, 0.6);
  }}
  .card-c1 {{ width: 280px; }}
  .card-c2 {{
    width: 380px;
    border-color: rgba(163, 135, 255, 0.4);
    box-shadow: 0 0 35px rgba(163, 135, 255, 0.15), 0 16px 40px rgba(0, 0, 0, 0.6);
  }}
  .card-c3 {{ width: 420px; }}

  .card-eyebrow {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 10px;
    font-weight: 700;
    color: #8C879E;
    letter-spacing: 0.1em;
    margin-bottom: 8px;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }}
  .card-eyebrow span {{
    color: #A387FF;
  }}
  .card-title {{
    font-size: 16px;
    font-weight: 700;
    color: #FFFFFF;
    margin-bottom: 16px;
    line-height: 1.3;
  }}
  .primary-metric-box {{
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 10px;
    padding: 14px 16px;
    margin-bottom: 14px;
  }}
  .metric-label {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 10px;
    color: #8C879E;
    letter-spacing: 0.08em;
    margin-bottom: 4px;
  }}
  .metric-val {{
    font-size: 32px;
    font-weight: 800;
    letter-spacing: -0.02em;
    color: #FFFFFF;
    line-height: 1.1;
  }}
  .metric-val.cyan {{ color: #22D3C4; }}
  .metric-val.purple {{ color: #A387FF; }}
  .metric-val.coral {{ color: #FC5457; }}

  /* Metric Key-Value List */
  .kv-list {{
    display: flex;
    flex-direction: column;
    gap: 8px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
    color: #A2A1A6;
  }}
  .kv-item {{
    display: flex;
    justify-content: space-between;
    border-bottom: 1px solid rgba(255, 255, 255, 0.05);
    padding-bottom: 6px;
  }}
  .kv-item b {{ color: #FFFFFF; font-weight: 600; }}
  .kv-item b.cyan {{ color: #22D3C4; }}
  .kv-item b.purple {{ color: #A387FF; }}

  /* Dual Allocation Split Inside Card 3 */
  .split-grid {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 10px;
    margin-bottom: 14px;
  }}
  .split-cell {{
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 8px;
    padding: 10px 12px;
  }}
  .split-cell-title {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 9px;
    color: #8C879E;
    letter-spacing: 0.08em;
    margin-bottom: 4px;
  }}
  .split-cell-apy {{
    font-size: 20px;
    font-weight: 800;
    color: #22D3C4;
  }}

  /* Footer */
  .card-footer {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-top: 1px solid rgba(255, 255, 255, 0.08);
    padding-top: 16px;
    z-index: 2;
  }}
  .footer-left {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
    color: #8C889E;
    display: flex;
    gap: 20px;
  }}
  .footer-left span {{ color: #A387FF; }}
  .footer-right {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
    color: #4A4658;
  }}
</style>
</head>
<body>
  <div class="film-grain"></div>
  
  <div class="card-header">
    <div class="header-left">
      <div class="protocol-badge">STRATEGY SUITE // DELTA-NEUTRAL HARVESTER</div>
      <div class="telemetry-meta">CONTRACT: 0x7c9a...b412 · STATUS: ACTIVE [BLOCK #48,291,044]</div>
    </div>
    {VANNA_MONOGRAM}
  </div>

  <div class="stage-container">
    <!-- Connector Arrow SVG -->
    <svg class="flow-connector-svg" viewBox="0 0 1104 60">
      <line x1="280" y1="30" x2="330" y2="30" stroke="#A387FF" stroke-width="2" stroke-dasharray="4 4" />
      <polygon points="330,26 338,30 330,34" fill="#A387FF" />
      <line x1="720" y1="30" x2="770" y2="30" stroke="#22D3C4" stroke-width="2" stroke-dasharray="4 4" />
      <polygon points="770,26 778,30 770,34" fill="#22D3C4" />
    </svg>

    <!-- CARD 1: INPUT COLLATERAL -->
    <div class="arch-card card-c1">
      <div>
        <div class="card-eyebrow">STAGE 01 <span>ISOLATED</span></div>
        <div class="card-title">Initial Capital Commitment</div>
      </div>
      <div class="primary-metric-box">
        <div class="metric-label">DEPOSITED COLLATERAL</div>
        <div class="metric-val">$10,000</div>
      </div>
      <div class="kv-list">
        <div class="kv-item"><span>Asset:</span> <b>USDC (Stellar)</b></div>
        <div class="kv-item"><span>Custody Layer:</span> <b>Isolated Sandbox</b></div>
        <div class="kv-item"><span>Wallet Auth:</span> <b>Non-Custodial</b></div>
        <div class="kv-item"><span>Entry Cost:</span> <b class="cyan">0.00014 XLM</b></div>
      </div>
    </div>

    <!-- CARD 2: SMARTACCOUNT MULTIPLIER -->
    <div class="arch-card card-c2">
      <div>
        <div class="card-eyebrow">STAGE 02 <span>COMPOSABLE CORE</span></div>
        <div class="card-title">SmartAccount Leverage Engine</div>
      </div>
      <div class="primary-metric-box">
        <div class="metric-label">TOTAL POSITION NOTIONAL</div>
        <div class="metric-val purple">$100,000</div>
      </div>
      <div class="kv-list">
        <div class="kv-item"><span>Multiplier Applied:</span> <b class="purple">10.00× LEVERAGE</b></div>
        <div class="kv-item"><span>Underwritten Debt:</span> <b>$90,000 BLUSDC</b></div>
        <div class="kv-item"><span>Delta Exposure:</span> <b class="cyan">Δ = 0.00 (HEDGED)</b></div>
        <div class="kv-item"><span>Net Health Factor:</span> <b>1.38× [MIN: 1.10×]</b></div>
        <div class="kv-item"><span>Rebalance Latency:</span> <b>~320ms Soroban VM</b></div>
      </div>
    </div>

    <!-- CARD 3: COMPOSABLE DUAL YIELD -->
    <div class="arch-card card-c3">
      <div>
        <div class="card-eyebrow">STAGE 03 <span>EXTERNAL ROUTING</span></div>
        <div class="card-title">Dual On-Chain Yield Harvest</div>
      </div>
      <div class="split-grid">
        <div class="split-cell">
          <div class="split-cell-title">AQUARIUS AMM LP</div>
          <div class="split-cell-apy">18.4%</div>
          <div class="metric-label" style="margin-top:4px;">USDC / XLM POOL</div>
        </div>
        <div class="split-cell">
          <div class="split-cell-title">BLEND PROTOCOL</div>
          <div class="split-cell-apy">8.2%</div>
          <div class="metric-label" style="margin-top:4px;">LENDING INCENTIVES</div>
        </div>
      </div>
      <div class="primary-metric-box" style="margin-bottom:0; background: rgba(34, 211, 196, 0.06); border-color: rgba(34, 211, 196, 0.3);">
        <div class="metric-label">NET POSITION APY (LEVERAGED)</div>
        <div class="metric-val cyan">26.6% APY</div>
      </div>
      <div class="kv-list" style="margin-top: 10px;">
        <div class="kv-item"><span>Harvest Frequency:</span> <b>Per Block (Continuous)</b></div>
        <div class="kv-item"><span>Liquidation Risk:</span> <b class="cyan">Zero (Delta Hedged)</b></div>
      </div>
    </div>
  </div>

  <div class="card-footer">
    <div class="footer-left">
      <div>COLLATERAL RATIO: <span>10.0%</span></div>
      <div>SETTLEMENT: <span>ATOMIC SOROBAN TX</span></div>
      <div>CAPITAL EFFICIENCY: <span>1000% BOOST</span></div>
    </div>
    <div class="footer-right">test.stellar.vanna.finance</div>
  </div>
</body>
</html>
"""

# HTML Template for Post 2: Continuous Polynomial RateModel
HTML_POST2 = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600;700&display=swap');
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    width: 1200px;
    height: 675px;
    overflow: hidden;
    background-color: #07020D;
    background-image:
      radial-gradient(ellipse 65% 55% at 95% 15%, rgba(94, 13, 70, 0.75) 0%, rgba(62, 8, 49, 0.45) 40%, rgba(7, 2, 13, 0) 75%),
      radial-gradient(ellipse 70% 60% at 8% 90%, rgba(71, 20, 133, 0.85) 0%, rgba(42, 11, 82, 0.5) 45%, rgba(7, 2, 13, 0) 80%);
    color: #FFFFFF;
    font-family: 'Plus Jakarta Sans', sans-serif;
    position: relative;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    padding: 36px 48px;
  }}
  .film-grain {{
    position: absolute;
    top: 0; left: 0; width: 100%; height: 100%;
    opacity: 0.035;
    pointer-events: none;
    background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noiseFilter'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.8' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noiseFilter)'/%3E%3C/svg%3E");
    z-index: 1;
  }}
  .card-header {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    z-index: 2;
  }}
  .header-left {{
    display: flex;
    align-items: center;
    gap: 12px;
  }}
  .protocol-badge {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
    font-weight: 700;
    color: #A387FF;
    background: rgba(163, 135, 255, 0.12);
    border: 1px solid rgba(163, 135, 255, 0.3);
    padding: 4px 10px;
    border-radius: 4px;
    letter-spacing: 0.08em;
  }}
  .telemetry-meta {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
    color: #8C879E;
    letter-spacing: 0.05em;
  }}
  .monogram-svg {{
    width: 28px;
    height: 28px;
    opacity: 0.35;
  }}
  
  /* Layout: Left Coordinate Chart, Right Quantitative Specs */
  .quant-stage {{
    position: relative;
    width: 100%;
    height: 420px;
    display: grid;
    grid-template-columns: 700px 380px;
    gap: 24px;
    align-items: center;
    z-index: 2;
  }}

  /* Chart Container */
  .chart-box {{
    background: rgba(14, 10, 24, 0.75);
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 16px;
    backdrop-filter: blur(14px);
    padding: 24px;
    height: 390px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    box-shadow: 0 16px 40px rgba(0, 0, 0, 0.6);
  }}
  .chart-header-row {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 12px;
  }}
  .chart-title {{
    font-size: 15px;
    font-weight: 700;
    color: #FFFFFF;
  }}
  .formula-pill {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 10px;
    background: rgba(163, 135, 255, 0.15);
    border: 1px solid rgba(163, 135, 255, 0.4);
    color: #A387FF;
    padding: 3px 10px;
    border-radius: 4px;
  }}
  .chart-svg-wrap {{
    position: relative;
    width: 100%;
    height: 280px;
  }}

  /* Quantitative Metrics Sidebar */
  .quant-sidebar {{
    display: flex;
    flex-direction: column;
    gap: 12px;
    height: 390px;
    justify-content: space-between;
  }}
  .spec-card {{
    background: rgba(14, 10, 24, 0.75);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 14px;
    backdrop-filter: blur(12px);
    padding: 16px 18px;
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
  }}
  .spec-card.highlight {{
    border-color: rgba(34, 211, 196, 0.4);
    background: rgba(34, 211, 196, 0.04);
  }}
  .spec-label {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 10px;
    color: #8C879E;
    letter-spacing: 0.08em;
    margin-bottom: 4px;
    text-transform: uppercase;
  }}
  .spec-value {{
    font-size: 24px;
    font-weight: 800;
    color: #FFFFFF;
    letter-spacing: -0.01em;
  }}
  .spec-value.purple {{ color: #A387FF; }}
  .spec-value.cyan {{ color: #22D3C4; }}
  .spec-value.coral {{ color: #FC5457; }}
  .spec-desc {{
    font-size: 11px;
    color: #A2A1A6;
    margin-top: 4px;
    line-height: 1.4;
  }}

  /* Footer */
  .card-footer {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-top: 1px solid rgba(255, 255, 255, 0.08);
    padding-top: 16px;
    z-index: 2;
  }}
  .footer-left {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
    color: #8C889E;
    display: flex;
    gap: 20px;
  }}
  .footer-left span {{ color: #A387FF; }}
  .footer-right {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
    color: #4A4658;
  }}
</style>
</head>
<body>
  <div class="film-grain"></div>
  
  <div class="card-header">
    <div class="header-left">
      <div class="protocol-badge">QUANTITATIVE DYNAMICS // RATEMODEL</div>
      <div class="telemetry-meta">GOVERNING EQUATION: R(U) = R₀ + α·U + β·U² · STELLAR SOROBAN VM</div>
    </div>
    {VANNA_MONOGRAM}
  </div>

  <div class="quant-stage">
    <!-- LEFT: PRECISE COORDINATE CHART -->
    <div class="chart-box">
      <div class="chart-header-row">
        <div class="chart-title">Borrow APY Response vs Pool Utilization</div>
        <div class="formula-pill">R(U) = 4.0% + 12.0%·U + 48.0%·U²</div>
      </div>

      <div class="chart-svg-wrap">
        <svg viewBox="0 0 650 280" style="width: 100%; height: 100%;">
          <defs>
            <linearGradient id="vannaCurveGrad" x1="0" y1="1" x2="1" y2="0">
              <stop offset="0%" stop-color="#A387FF" />
              <stop offset="60%" stop-color="#C084FC" />
              <stop offset="100%" stop-color="#22D3C4" />
            </linearGradient>
            <filter id="glowLine">
              <feGaussianBlur stdDeviation="2.5" result="coloredBlur"/>
              <feMerge>
                <feMergeNode in="coloredBlur"/>
                <feMergeNode in="SourceGraphic"/>
              </feMerge>
            </filter>
          </defs>

          <!-- Grid Lines -->
          <line x1="60" y1="30" x2="620" y2="30" stroke="rgba(255,255,255,0.06)" stroke-width="1" />
          <line x1="60" y1="95" x2="620" y2="95" stroke="rgba(255,255,255,0.06)" stroke-width="1" />
          <line x1="60" y1="160" x2="620" y2="160" stroke="rgba(255,255,255,0.06)" stroke-width="1" />
          <line x1="60" y1="225" x2="620" y2="225" stroke="rgba(255,255,255,0.06)" stroke-width="1" />

          <!-- Axes -->
          <line x1="60" y1="225" x2="620" y2="225" stroke="rgba(255,255,255,0.2)" stroke-width="1.5" />
          <line x1="60" y1="20" x2="60" y2="225" stroke="rgba(255,255,255,0.2)" stroke-width="1.5" />

          <!-- Y-Axis Ticks & Labels -->
          <text x="50" y="228" text-anchor="end" fill="#8C879E" font-family="JetBrains Mono" font-size="10">0%</text>
          <text x="50" y="163" text-anchor="end" fill="#8C879E" font-family="JetBrains Mono" font-size="10">20%</text>
          <text x="50" y="98" text-anchor="end" fill="#8C879E" font-family="JetBrains Mono" font-size="10">40%</text>
          <text x="50" y="33" text-anchor="end" fill="#8C879E" font-family="JetBrains Mono" font-size="10">64%</text>
          <text x="25" y="125" text-anchor="middle" fill="#A2A1A6" font-family="JetBrains Mono" font-size="10" transform="rotate(-90 25 125)">BORROW APY</text>

          <!-- X-Axis Ticks & Labels -->
          <text x="60" y="245" text-anchor="middle" fill="#8C879E" font-family="JetBrains Mono" font-size="10">0%</text>
          <text x="200" y="245" text-anchor="middle" fill="#8C879E" font-family="JetBrains Mono" font-size="10">25%</text>
          <text x="340" y="245" text-anchor="middle" fill="#8C879E" font-family="JetBrains Mono" font-size="10">50%</text>
          <text x="508" y="245" text-anchor="middle" fill="#A387FF" font-family="JetBrains Mono" font-size="10" font-weight="700">80% [KINK]</text>
          <text x="620" y="245" text-anchor="middle" fill="#8C879E" font-family="JetBrains Mono" font-size="10">100%</text>
          <text x="340" y="268" text-anchor="middle" fill="#A2A1A6" font-family="JetBrains Mono" font-size="10">POOL UTILIZATION RATIO (U)</text>

          <!-- Target Kink Guide Line at 80% -->
          <line x1="508" y1="20" x2="508" y2="225" stroke="rgba(252, 84, 87, 0.25)" stroke-width="1" stroke-dasharray="3 3" />

          <!-- CURVE 1: TRADITIONAL PIECEWISE LINEAR KINK (Aave/Compound) -->
          <!-- Sluggish 4% to 12% until 80%, then brutal spike to 60% -->
          <path d="M 60,213 L 508,189 L 620,42" 
                fill="none" stroke="#FC5457" stroke-width="2" stroke-dasharray="5 4" opacity="0.85" />
          <text x="495" y="178" text-anchor="end" fill="#FC5457" font-family="JetBrains Mono" font-size="10">PIECEWISE JUMP KINK</text>

          <!-- CURVE 2: VANNA CONTINUOUS POLYNOMIAL CURVE -->
          <!-- R(U) = 4% + 12%*U + 48%*U^2 -> smooth, continuous acceleration -->
          <path d="M 60,213 Q 320,185 508,135 T 620,30" 
                fill="none" stroke="url(#vannaCurveGrad)" stroke-width="3.5" filter="url(#glowLine)" />
          <text x="440" y="115" text-anchor="end" fill="#22D3C4" font-family="JetBrains Mono" font-size="11" font-weight="700">
            VANNA POLYNOMIAL R(U)
          </text>

          <!-- Dynamic Pricing Indicator Node -->
          <circle cx="508" cy="135" r="5" fill="#22D3C4" />
          <circle cx="508" cy="135" r="8" fill="none" stroke="#22D3C4" stroke-width="1" opacity="0.6" />
        </svg>
      </div>
    </div>

    <!-- RIGHT: QUANTITATIVE SPECIFICATIONS SIDEBAR -->
    <div class="quant-sidebar">
      <div class="spec-card">
        <div class="spec-label">BASE BORROW RATE (R₀)</div>
        <div class="spec-value purple">4.00%</div>
        <div class="spec-desc">Guarantees base yield floor for passive depositors at zero utilization.</div>
      </div>

      <div class="spec-card highlight">
        <div class="spec-label">OPTIMAL TARGET EQUILIBRIUM</div>
        <div class="spec-value cyan">U* = 80.0%</div>
        <div class="spec-desc">Smooth polynomial inflection replaces the abrupt non-differentiable jump shock.</div>
      </div>

      <div class="spec-card">
        <div class="spec-label">TERMINAL APY SPREAD (100% U)</div>
        <div class="spec-value coral">64.00%</div>
        <div class="spec-desc">Instant mathematical incentive driving emergency debt repayments.</div>
      </div>
    </div>
  </div>

  <div class="card-footer">
    <div class="footer-left">
      <div>CALCULATION FREQUENCY: <span>PER-SECOND TICK</span></div>
      <div>SMART CONTRACT: <span>RateModel.soroban</span></div>
      <div>EXHAUSTION RISK: <span>0.00% (PROVEN)</span></div>
    </div>
    <div class="footer-right">docs.vanna.finance</div>
  </div>
</body>
</html>
"""

def render_posts():
    # Render Post 1
    p1_html = STATE_DIR / "temp_p1_upgraded.html"
    p1_png = STATE_DIR / "vanna_upgraded_post1_delta_neutral.png"
    p1_html.write_text(HTML_POST1, encoding="utf-8")
    
    cmd1 = [
        CHROME_PATH,
        "--headless=new",
        "--disable-gpu",
        "--hide-scrollbars",
        "--force-device-scale-factor=2",
        "--window-size=1200,675",
        f"--screenshot={p1_png.resolve()}",
        str(p1_html.resolve())
    ]
    subprocess.run(cmd1, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if p1_html.exists(): p1_html.unlink()
    print(f"✅ Generated Post 1: {p1_png.name} ({p1_png.stat().st_size:,} bytes)")

    # Render Post 2
    p2_html = STATE_DIR / "temp_p2_upgraded.html"
    p2_png = STATE_DIR / "vanna_upgraded_post2_polynomial_dynamics.png"
    p2_html.write_text(HTML_POST2, encoding="utf-8")
    
    cmd2 = [
        CHROME_PATH,
        "--headless=new",
        "--disable-gpu",
        "--hide-scrollbars",
        "--force-device-scale-factor=2",
        "--window-size=1200,675",
        f"--screenshot={p2_png.resolve()}",
        str(p2_html.resolve())
    ]
    subprocess.run(cmd2, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if p2_html.exists(): p2_html.unlink()
    print(f"✅ Generated Post 2: {p2_png.name} ({p2_png.stat().st_size:,} bytes)")

if __name__ == "__main__":
    render_posts()
