#!/usr/bin/env python3
"""Generates 2 institutional-grade posts using Gemini 3.1 Pro standards.

Post 1: Sub-Second Solvency Telemetry (Mercury Real-Time Indexer on Soroban)
Post 2: Dedicated SmartAccount Sandboxes vs Shared-Pool Contagion
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

# HTML Template for Pro Post 1: Mercury Real-Time Indexer & Sub-Second Solvency
HTML_PRO_POST1 = f"""<!DOCTYPE html>
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
    color: #22D3C4;
    background: rgba(34, 211, 196, 0.12);
    border: 1px solid rgba(34, 211, 196, 0.35);
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

  /* Pipeline Stage */
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

  /* Modular Cards */
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
  .card-c1 {{ width: 330px; }}
  .card-c2 {{
    width: 380px;
    border-color: rgba(34, 211, 196, 0.4);
    box-shadow: 0 0 35px rgba(34, 211, 196, 0.12), 0 16px 40px rgba(0, 0, 0, 0.6);
  }}
  .card-c3 {{ width: 350px; }}

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
  .card-eyebrow span {{ color: #22D3C4; }}
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
  .footer-left span {{ color: #22D3C4; }}
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
      <div class="protocol-badge">TELEMETRY // MERCURY INDEXER</div>
      <div class="telemetry-meta">SUB-SECOND OFF-CHAIN MONITORING · STELLAR SOROBAN PROTOCOL 20</div>
    </div>
    {VANNA_MONOGRAM}
  </div>

  <div class="stage-container">
    <svg class="flow-connector-svg" viewBox="0 0 1104 60">
      <line x1="330" y1="30" x2="380" y2="30" stroke="#22D3C4" stroke-width="2" stroke-dasharray="4 4" />
      <polygon points="380,26 388,30 380,34" fill="#22D3C4" />
      <line x1="760" y1="30" x2="810" y2="30" stroke="#A387FF" stroke-width="2" stroke-dasharray="4 4" />
      <polygon points="810,26 818,30 810,34" fill="#A387FF" />
    </svg>

    <!-- STAGE 01: MERCURY REAL-TIME STREAM -->
    <div class="arch-card card-c1">
      <div>
        <div class="card-eyebrow">STAGE 01 <span>EVENT STREAM</span></div>
        <div class="card-title">Mercury Real-Time Ingestion</div>
      </div>
      <div class="primary-metric-box">
        <div class="metric-label">STREAMING LATENCY</div>
        <div class="metric-val cyan">~320ms</div>
      </div>
      <div class="kv-list">
        <div class="kv-item"><span>Ingestion Layer:</span> <b>Mercury Indexer</b></div>
        <div class="kv-item"><span>Ledger Sync:</span> <b>Per Block (Continuous)</b></div>
        <div class="kv-item"><span>Monitored Accounts:</span> <b>100% On-Chain</b></div>
        <div class="kv-item"><span>Front-Run Vulnerability:</span> <b class="cyan">0.00% (No Mempool)</b></div>
      </div>
    </div>

    <!-- STAGE 02: RISK GUARDIAN STATE MACHINE -->
    <div class="arch-card card-c2">
      <div>
        <div class="card-eyebrow">STAGE 02 <span>DECISION CORE</span></div>
        <div class="card-title">Risk Guardian State Machine</div>
      </div>
      <div class="primary-metric-box">
        <div class="metric-label">AUTONOMOUS TRIGGER THRESHOLD</div>
        <div class="metric-val purple">HF ≤ 1.25×</div>
      </div>
      <div class="kv-list">
        <div class="kv-item"><span>Monitoring Variable:</span> <b class="purple">Net Health Factor</b></div>
        <div class="kv-item"><span>Threshold Action:</span> <b>Targeted Deleveraging</b></div>
        <div class="kv-item"><span>Immutable Floor:</span> <b>HF = 1.10× (Unreached)</b></div>
        <div class="kv-item"><span>Keeper Scope:</span> <b class="cyan">Session Key Only</b></div>
        <div class="kv-item"><span>Withdrawal Authority:</span> <b>Zero (Non-Custodial)</b></div>
      </div>
    </div>

    <!-- STAGE 03: DEFENSIVE EXECUTION -->
    <div class="arch-card card-c3">
      <div>
        <div class="card-eyebrow">STAGE 03 <span>ATOMIC CLEARANCE</span></div>
        <div class="card-title">SmartAccount Defense Clearance</div>
      </div>
      <div class="primary-metric-box" style="background: rgba(34, 211, 196, 0.06); border-color: rgba(34, 211, 196, 0.3);">
        <div class="metric-label">DEFENSE EXECUTION GAS</div>
        <div class="metric-val cyan">0.00014 XLM</div>
      </div>
      <div class="kv-list">
        <div class="kv-item"><span>Gas Cost in USD:</span> <b class="cyan">&lt; $0.0001</b></div>
        <div class="kv-item"><span>Settlement Velocity:</span> <b>1 Ledger (~4s Finality)</b></div>
        <div class="kv-item"><span>Penalty Incurred:</span> <b class="cyan">0.00% (No Auction)</b></div>
        <div class="kv-item"><span>Position Outcome:</span> <b class="cyan">Secured at 1.85× HF</b></div>
      </div>
    </div>
  </div>

  <div class="card-footer">
    <div class="footer-left">
      <div>ARCHITECTURE: <span>MERCURY + SOROBAN VM</span></div>
      <div>DEFENSE TRIGGER: <span>SUB-SECOND TICK</span></div>
      <div>LIQUIDATION PENALTY: <span>0.0% SAVED</span></div>
    </div>
    <div class="footer-right">test.stellar.vanna.finance</div>
  </div>
</body>
</html>
"""

# HTML Template for Pro Post 2: Compartmentalized Sandboxes vs Shared Pool Contagion
HTML_PRO_POST2 = f"""<!DOCTYPE html>
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

  /* Comparative Stage Grid */
  .comp-stage {{
    position: relative;
    width: 100%;
    height: 420px;
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 28px;
    align-items: center;
    z-index: 2;
  }}

  /* Architecture Box */
  .arch-box {{
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
  .arch-box.competitor {{
    border-color: rgba(252, 84, 87, 0.35);
    box-shadow: 0 0 35px rgba(252, 84, 87, 0.08), 0 16px 40px rgba(0, 0, 0, 0.6);
  }}
  .arch-box.vanna {{
    border-color: rgba(34, 211, 196, 0.4);
    box-shadow: 0 0 35px rgba(34, 211, 196, 0.12), 0 16px 40px rgba(0, 0, 0, 0.6);
  }}

  .box-header {{
    display: flex;
    justify-content: space-between;
    align-items: center;
  }}
  .box-tag {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 10px;
    font-weight: 700;
    padding: 3px 10px;
    border-radius: 4px;
    letter-spacing: 0.08em;
  }}
  .box-tag.red {{
    background: rgba(252, 84, 87, 0.15);
    border: 1px solid rgba(252, 84, 87, 0.4);
    color: #FC5457;
  }}
  .box-tag.cyan {{
    background: rgba(34, 211, 196, 0.15);
    border: 1px solid rgba(34, 211, 196, 0.4);
    color: #22D3C4;
  }}
  .box-title {{
    font-size: 17px;
    font-weight: 700;
    color: #FFFFFF;
    margin-top: 10px;
  }}

  /* Diagram Visual Canvas Inside Box */
  .box-canvas {{
    background: rgba(0, 0, 0, 0.3);
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-radius: 12px;
    height: 180px;
    display: flex;
    align-items: center;
    justify-content: center;
    position: relative;
    padding: 10px;
  }}

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
  .kv-item b.red {{ color: #FC5457; }}
  .kv-item b.cyan {{ color: #22D3C4; }}

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
      <div class="protocol-badge">ARCHITECTURE // SOLVENCY TOPOLOGY</div>
      <div class="telemetry-meta">CONTAGION MITIGATION ANALYSIS · SOROBAN DEDICATED SANDBOXES</div>
    </div>
    {VANNA_MONOGRAM}
  </div>

  <div class="comp-stage">
    <!-- LEFT: SHARED POOL CONTAGION -->
    <div class="arch-box competitor">
      <div>
        <div class="box-header">
          <div class="box-tag red">TRADITIONAL LENDING (SHARED POOL)</div>
          <div style="font-family:'JetBrains Mono'; font-size:10px; color:#FC5457;">SOCIALIZED BAD DEBT</div>
        </div>
        <div class="box-title">Monolithic Liquidity Pool</div>
      </div>

      <div class="box-canvas">
        <svg viewBox="0 0 480 160" style="width: 100%; height: 100%;">
          <!-- Single Large Pool Box with Fracture -->
          <rect x="40" y="25" width="400" height="110" rx="12" fill="rgba(252,84,87,0.08)" stroke="#FC5457" stroke-width="1.5" stroke-dasharray="6 4" />
          <text x="240" y="52" text-anchor="middle" fill="#FFFFFF" font-family="JetBrains Mono" font-size="12" font-weight="700">SHARED RESERVE VAULT ($50M)</text>
          
          <!-- Contagion Fracture Line Across All Users -->
          <path d="M 40,80 L 140,95 L 240,75 L 340,90 L 440,80" fill="none" stroke="#FC5457" stroke-width="2.5" />
          
          <!-- 3 User Balances Inside Broken Vault -->
          <rect x="60" y="95" width="100" height="30" rx="6" fill="rgba(252,84,87,0.2)" stroke="#FC5457" stroke-width="1" />
          <text x="110" y="115" text-anchor="middle" fill="#FC5457" font-family="JetBrains Mono" font-size="10">USER A (HAIRCUT)</text>

          <rect x="190" y="95" width="100" height="30" rx="6" fill="rgba(252,84,87,0.2)" stroke="#FC5457" stroke-width="1" />
          <text x="240" y="115" text-anchor="middle" fill="#FC5457" font-family="JetBrains Mono" font-size="10">USER B (HAIRCUT)</text>

          <rect x="320" y="95" width="100" height="30" rx="6" fill="rgba(252,84,87,0.2)" stroke="#FC5457" stroke-width="1" />
          <text x="370" y="115" text-anchor="middle" fill="#FC5457" font-family="JetBrains Mono" font-size="10">EXOTIC DEPEG</text>
        </svg>
      </div>

      <div class="kv-list">
        <div class="kv-item"><span>Risk Containment:</span> <b class="red">Zero (Global Pool Contagion)</b></div>
        <div class="kv-item"><span>Depeg Impact:</span> <b class="red">Haircut on 100% of Depositors</b></div>
        <div class="kv-item"><span>Borrower Isolation:</span> <b>None (Shared Storage State)</b></div>
      </div>
    </div>

    <!-- RIGHT: VANNA COMPARTMENTALIZED SANDBOXES -->
    <div class="arch-box vanna">
      <div>
        <div class="box-header">
          <div class="box-tag cyan">VANNA PROTOCOL (STELLAR SOROBAN)</div>
          <div style="font-family:'JetBrains Mono'; font-size:10px; color:#22D3C4;">ZERO CROSS-ACCOUNT RISK</div>
        </div>
        <div class="box-title">Compartmentalized SmartAccounts</div>
      </div>

      <div class="box-canvas">
        <svg viewBox="0 0 480 160" style="width: 100%; height: 100%;">
          <!-- Core Lending Pool at Top -->
          <rect x="140" y="15" width="200" height="32" rx="6" fill="rgba(34,211,196,0.12)" stroke="#22D3C4" stroke-width="1" />
          <text x="240" y="35" text-anchor="middle" fill="#22D3C4" font-family="JetBrains Mono" font-size="11" font-weight="700">CORE LENDING POOL</text>

          <!-- 3 Dedicated Isolated Sandbox Contracts Below -->
          <line x1="170" y1="47" x2="100" y2="85" stroke="#22D3C4" stroke-width="1.5" stroke-dasharray="3 3" />
          <line x1="240" y1="47" x2="240" y2="85" stroke="#22D3C4" stroke-width="1.5" stroke-dasharray="3 3" />
          <line x1="310" y1="47" x2="380" y2="85" stroke="#FC5457" stroke-width="1.5" stroke-dasharray="3 3" />

          <!-- Sandbox 1 -->
          <rect x="40" y="85" width="120" height="55" rx="8" fill="rgba(14,10,24,0.9)" stroke="#22D3C4" stroke-width="1.2" />
          <text x="100" y="108" text-anchor="middle" fill="#FFFFFF" font-family="JetBrains Mono" font-size="10" font-weight="700">SANDBOX #01</text>
          <text x="100" y="126" text-anchor="middle" fill="#22D3C4" font-family="JetBrains Mono" font-size="9">100% PROTECTED</text>

          <!-- Sandbox 2 -->
          <rect x="180" y="85" width="120" height="55" rx="8" fill="rgba(14,10,24,0.9)" stroke="#22D3C4" stroke-width="1.2" />
          <text x="240" y="108" text-anchor="middle" fill="#FFFFFF" font-family="JetBrains Mono" font-size="10" font-weight="700">SANDBOX #02</text>
          <text x="240" y="126" text-anchor="middle" fill="#22D3C4" font-family="JetBrains Mono" font-size="9">100% PROTECTED</text>

          <!-- Sandbox 3 (Isolated Deficit Containment) -->
          <rect x="320" y="85" width="120" height="55" rx="8" fill="rgba(30,8,16,0.8)" stroke="#FC5457" stroke-width="1.2" />
          <text x="380" y="108" text-anchor="middle" fill="#FC5457" font-family="JetBrains Mono" font-size="10" font-weight="700">SANDBOX #03</text>
          <text x="380" y="126" text-anchor="middle" fill="#FC5457" font-family="JetBrains Mono" font-size="9">QUARANTINED DEFICIT</text>
        </svg>
      </div>

      <div class="kv-list">
        <div class="kv-item"><span>Risk Containment:</span> <b class="cyan">Strict Sandbox Compartmentalization</b></div>
        <div class="kv-item"><span>Depeg Impact:</span> <b class="cyan">0.00% Leakage to Other Accounts</b></div>
        <div class="kv-item"><span>Borrower Isolation:</span> <b>Individual SmartContract Instances</b></div>
      </div>
    </div>
  </div>

  <div class="card-footer">
    <div class="footer-left">
      <div>ISOLATION MODEL: <span>DEDICATED INSTANCES</span></div>
      <div>CORE RESERVES: <span>IMMUTABLE PROTECTION</span></div>
      <div>CONTAGION VECTOR: <span>0.0% LEAKAGE</span></div>
    </div>
    <div class="footer-right">docs.vanna.finance</div>
  </div>
</body>
</html>
"""

def render_pro_posts():
    # Render Pro Post 1
    p1_html = STATE_DIR / "temp_pro_p1.html"
    p1_png = STATE_DIR / "vanna_pro_post1_mercury_telemetry.png"
    p1_html.write_text(HTML_PRO_POST1, encoding="utf-8")
    
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
    print(f"✅ Generated Pro Post 1: {p1_png.name} ({p1_png.stat().st_size:,} bytes)")

    # Render Pro Post 2
    p2_html = STATE_DIR / "temp_pro_p2.html"
    p2_png = STATE_DIR / "vanna_pro_post2_isolated_sandboxes.png"
    p2_html.write_text(HTML_PRO_POST2, encoding="utf-8")
    
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
    print(f"✅ Generated Pro Post 2: {p2_png.name} ({p2_png.stat().st_size:,} bytes)")

if __name__ == "__main__":
    render_pro_posts()
