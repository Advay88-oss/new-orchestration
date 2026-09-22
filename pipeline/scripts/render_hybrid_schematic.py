#!/usr/bin/env python3
"""Vanna Hybrid Vector Renderer (Test Mode Only).

Combines:
  1. Exact Vanna dual-point ambient gradient canvas (#07020D + #471485 + #5E0D46)
  2. Ultra-crisp vector SVG diagram elements and connectors
  3. Native 2x Retina typography (Plus Jakarta Sans + JetBrains Mono)
  4. Micro-telemetry metadata tags (Network, Contract, Latency, Protocol)
  5. Discrete Vanna monogram in upper-right corner

Renders to pristine 2x Retina PNGs via headless Chrome.
"""

from __future__ import annotations

import os
import subprocess
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

COMMON_STYLES = """
  @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600;700&display=swap');
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    width: 1200px;
    height: 675px;
    overflow: hidden;
    background-color: #080310;
    background-image:
      radial-gradient(ellipse 75% 65% at 92% 12%, rgba(225, 48, 128, 0.85) 0%, rgba(180, 28, 110, 0.52) 35%, rgba(120, 15, 80, 0.22) 60%, rgba(8, 3, 16, 0) 80%),
      radial-gradient(ellipse 80% 70% at 8% 90%, rgba(142, 58, 245, 0.90) 0%, rgba(98, 35, 215, 0.58) 38%, rgba(60, 18, 145, 0.25) 65%, rgba(8, 3, 16, 0) 85%),
      radial-gradient(circle at 55% 45%, rgba(210, 45, 140, 0.20) 0%, rgba(8, 3, 16, 0) 65%);
    color: #FFFFFF;
    font-family: 'Plus Jakarta Sans', sans-serif;
    position: relative;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    padding: 36px 48px;
  }
  .film-grain {
    position: absolute;
    top: 0; left: 0; width: 100%; height: 100%;
    opacity: 0.035;
    pointer-events: none;
    background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noiseFilter'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.8' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noiseFilter)'/%3E%3C/svg%3E");
    z-index: 1;
  }
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    z-index: 2;
  }
  .header-left {
    display: flex;
    align-items: center;
    gap: 12px;
  }
  .protocol-badge {
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
    font-weight: 700;
    color: #A387FF;
    background: rgba(163, 135, 255, 0.12);
    border: 1px solid rgba(163, 135, 255, 0.3);
    padding: 4px 10px;
    border-radius: 4px;
    letter-spacing: 0.08em;
  }
  .telemetry-meta {
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
    color: #7A758D;
    letter-spacing: 0.05em;
  }
  .monogram-svg {
    width: 28px;
    height: 28px;
    opacity: 0.35;
  }
  .card-footer {
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-top: 1px solid rgba(255, 255, 255, 0.08);
    padding-top: 16px;
    z-index: 2;
  }
  .footer-left {
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
    color: #8C889E;
    display: flex;
    gap: 18px;
  }
  .footer-left span { color: #A387FF; }
  .footer-right {
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
    color: #4A4658;
  }
  .diagram-stage {
    display: flex;
    align-items: center;
    justify-content: space-between;
    position: relative;
    z-index: 2;
    margin: auto 0;
    padding: 0 20px;
  }
"""

VANNA_MONOGRAM = """
<svg class="monogram-svg" viewBox="0 0 120 120" fill="none">
  <path d="M59.9886 16.0614C63.1147 13.6729 67.3757 13.3951 70.7757 15.3581C74.1757 17.3211 76.0413 21.1361 75.4986 25.0161L72.1417 49.0153L72.1454 49.0174L65.6912 95.1595L102.868 66.755L114.107 73.2444L68.4972 108.093C65.3711 110.481 61.11 110.759 57.7101 108.796C54.3101 106.833 52.4445 103.018 52.9872 99.138L56.3441 75.1388L56.3404 75.1367L62.7946 28.9947L25.6183 57.3991L14.3784 50.9098L59.9886 16.0614Z" fill="url(#p0)"/>
  <path d="M25.6183 57.3991L36.003 63.3948L33.9183 78.2994L45.9557 69.141L56.3404 75.1367L36.6411 90.1879C33.7348 92.4085 29.7734 92.6668 26.6125 90.8418C23.4545 89.0185 21.7201 85.4763 22.2206 81.872L25.6183 57.3991Z" fill="url(#p1)"/>
  <path d="M102.868 66.755L92.4828 60.7594L94.5675 45.8547L82.5301 55.0131L72.1454 49.0174L91.8447 33.9662C94.751 31.7457 98.7124 31.4874 101.873 33.3123C105.031 35.1356 106.766 38.6778 106.265 42.2822L102.868 66.755Z" fill="url(#p2)"/>
  <defs>
    <linearGradient id="p0" x1="44" y1="0" x2="128" y2="50" gradientUnits="userSpaceOnUse"><stop stop-color="#FC5457"/><stop offset="1" stop-color="#703AE6"/></linearGradient>
    <linearGradient id="p1" x1="44" y1="0" x2="128" y2="50" gradientUnits="userSpaceOnUse"><stop stop-color="#FC5457"/><stop offset="1" stop-color="#703AE6"/></linearGradient>
    <linearGradient id="p2" x1="44" y1="0" x2="128" y2="50" gradientUnits="userSpaceOnUse"><stop stop-color="#FC5457"/><stop offset="1" stop-color="#703AE6"/></linearGradient>
  </defs>
</svg>
"""

# HTML Card 1: 10x Leverage Multiplier
CARD_1_HTML = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
{COMMON_STYLES}
  .node-box {{
    width: 280px;
    height: 200px;
    background: rgba(14, 10, 24, 0.7);
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 16px;
    backdrop-filter: blur(12px);
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    position: relative;
    box-shadow: 0 16px 32px rgba(0, 0, 0, 0.5);
  }}
  .node-box.output {{
    border: 1px solid rgba(163, 135, 255, 0.4);
    box-shadow: 0 0 40px rgba(163, 135, 255, 0.15), 0 16px 32px rgba(0, 0, 0, 0.5);
  }}
  .node-amount {{
    font-size: 38px;
    font-weight: 800;
    color: #FFFFFF;
    letter-spacing: -0.02em;
    margin-bottom: 4px;
  }}
  .node-asset {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 15px;
    font-weight: 600;
    color: #A387FF;
    letter-spacing: 0.1em;
    margin-bottom: 14px;
  }}
  .node-label {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
    font-weight: 700;
    color: #7A758D;
    text-transform: uppercase;
    letter-spacing: 0.12em;
  }}
  .engine-module {{
    width: 220px;
    height: 190px;
    background: linear-gradient(135deg, #7C3AED 0%, #4C1D95 100%);
    border: 1px solid rgba(255, 255, 255, 0.25);
    border-radius: 20px;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    position: relative;
    box-shadow: 0 0 50px rgba(124, 58, 237, 0.35);
  }}
  .engine-multiplier {{
    font-size: 52px;
    font-weight: 900;
    color: #FFFFFF;
    line-height: 1;
    letter-spacing: -0.03em;
  }}
  .engine-tag {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 12px;
    font-weight: 700;
    color: #E9D5FF;
    letter-spacing: 0.1em;
    margin-top: 6px;
    text-transform: uppercase;
  }}
  .engine-sub {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 9px;
    color: rgba(255, 255, 255, 0.6);
    margin-top: 4px;
  }}
  .pins-col {{
    position: absolute;
    display: flex;
    flex-direction: column;
    gap: 12px;
  }}
  .pins-col.left {{ left: -8px; }}
  .pins-col.right {{ right: -8px; }}
  .pin {{
    width: 8px;
    height: 12px;
    background: #FC5457;
    border-radius: 2px;
    box-shadow: 0 0 8px rgba(252, 84, 87, 0.8);
  }}
  .conduit-svg {{
    width: 130px;
    height: 50px;
  }}
</style>
</head>
<body>
  <div class="film-grain"></div>
  <div class="card-header">
    <div class="header-left">
      <div class="protocol-badge">ARCH // 10X MULTIPLIER</div>
      <div class="telemetry-meta">NETWORK: STELLAR SOROBAN TESTNET · WASM v21</div>
    </div>
    {VANNA_MONOGRAM}
  </div>

  <div class="diagram-stage">
    <!-- STAGE 1: COLLATERAL -->
    <div class="node-box">
      <div class="node-amount">1,000</div>
      <div class="node-asset">XLM</div>
      <div class="node-label">COLLATERAL DEPOSIT</div>
    </div>

    <!-- CONDUIT 1 -->
    <svg class="conduit-svg" viewBox="0 0 130 50">
      <line x1="0" y1="15" x2="115" y2="15" stroke="rgba(255,255,255,0.2)" stroke-width="1.5" />
      <line x1="0" y1="25" x2="115" y2="25" stroke="#A387FF" stroke-width="2.5" stroke-dasharray="8 4" />
      <polygon points="115,20 128,25 115,30" fill="#A387FF" />
      <line x1="0" y1="35" x2="115" y2="35" stroke="rgba(255,255,255,0.2)" stroke-width="1.5" />
    </svg>

    <!-- STAGE 2: 10X ENGINE -->
    <div class="engine-module">
      <div class="pins-col left">
        <div class="pin"></div>
        <div class="pin"></div>
        <div class="pin"></div>
      </div>
      <div class="engine-multiplier">10×</div>
      <div class="engine-tag">LEVERAGE ENGINE</div>
      <div class="engine-sub">SMART CONTRACT CORE</div>
      <div class="pins-col right">
        <div class="pin"></div>
        <div class="pin"></div>
        <div class="pin"></div>
      </div>
    </div>

    <!-- CONDUIT 2 -->
    <svg class="conduit-svg" viewBox="0 0 130 50">
      <line x1="0" y1="15" x2="115" y2="15" stroke="rgba(255,255,255,0.2)" stroke-width="1.5" />
      <line x1="0" y1="25" x2="115" y2="25" stroke="#FC5457" stroke-width="2.5" />
      <polygon points="115,20 128,25 115,30" fill="#FC5457" />
      <line x1="0" y1="35" x2="115" y2="35" stroke="rgba(255,255,255,0.2)" stroke-width="1.5" />
    </svg>

    <!-- STAGE 3: OUTPUT -->
    <div class="node-box output">
      <div class="node-amount">10,000</div>
      <div class="node-asset">USDC</div>
      <div class="node-label">TRADING POWER</div>
    </div>
  </div>

  <div class="card-footer">
    <div class="footer-left">
      <div>ISOLATION: <span>SMARTACCOUNT SANDBOX</span></div>
      <div>SOLVENCY FLOOR: <span>1.10X HEALTH FACTOR</span></div>
      <div>CUSTODY: <span>NON-CUSTODIAL</span></div>
    </div>
    <div class="footer-right">test.stellar.vanna.finance</div>
  </div>
</body>
</html>
"""

# HTML Card 2: Composability Pipeline
CARD_2_HTML = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
{COMMON_STYLES}
  .pipeline-node {{
    display: flex;
    flex-direction: column;
    align-items: center;
    position: relative;
  }}
  .wallet-hex {{
    width: 140px;
    height: 150px;
    background: rgba(14, 10, 24, 0.7);
    border: 1px solid rgba(255, 255, 255, 0.15);
    clip-path: polygon(50% 0%, 100% 25%, 100% 75%, 50% 100%, 0% 75%, 0% 25%);
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    box-shadow: 0 10px 30px rgba(0,0,0,0.6);
  }}
  .wallet-title {{
    font-size: 13px;
    font-weight: 700;
    color: #FFF;
    margin-top: 14px;
    letter-spacing: -0.01em;
  }}
  .wallet-sub {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 10px;
    color: #7A758D;
    margin-top: 4px;
  }}
  .account-cube {{
    width: 240px;
    height: 180px;
    background: linear-gradient(135deg, rgba(163, 135, 255, 0.18) 0%, rgba(94, 13, 70, 0.25) 100%);
    border: 1px solid rgba(163, 135, 255, 0.4);
    border-radius: 16px;
    backdrop-filter: blur(12px);
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    padding: 20px;
    box-shadow: 0 0 40px rgba(163, 135, 255, 0.15);
    position: relative;
  }}
  .account-title {{
    font-size: 16px;
    font-weight: 800;
    color: #FFFFFF;
    margin-bottom: 6px;
  }}
  .account-sub {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 10px;
    color: #A387FF;
    letter-spacing: 0.05em;
    margin-bottom: 12px;
  }}
  .account-badge {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 9px;
    color: #22D3C4;
    background: rgba(34, 211, 196, 0.1);
    border: 1px solid rgba(34, 211, 196, 0.3);
    padding: 3px 8px;
    border-radius: 4px;
  }}
  .ports-left, .ports-right {{
    position: absolute;
    display: flex;
    flex-direction: column;
    gap: 12px;
  }}
  .ports-left {{ left: -6px; }}
  .ports-right {{ right: -6px; }}
  .port-dot {{
    width: 12px;
    height: 12px;
    background: #FC5457;
    border-radius: 3px;
    box-shadow: 0 0 10px #FC5457;
  }}
  .pool-matrix {{
    width: 250px;
    display: flex;
    flex-direction: column;
    align-items: center;
    position: relative;
  }}
  .blusdc-badge {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 12px;
    font-weight: 700;
    color: #FFFFFF;
    background: #2563EB;
    border: 1px solid #60A5FA;
    padding: 6px 14px;
    border-radius: 20px;
    display: flex;
    align-items: center;
    gap: 6px;
    box-shadow: 0 0 20px rgba(37, 99, 235, 0.6);
    margin-bottom: 18px;
  }}
  .pool-grid {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 10px;
    width: 100%;
  }}
  .pool-cube {{
    height: 65px;
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(163, 135, 255, 0.25);
    border-radius: 8px;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    font-family: 'JetBrains Mono', monospace;
    font-size: 10px;
    color: #C4B5FD;
  }}
  .pool-title {{
    font-size: 13px;
    font-weight: 700;
    color: #FFF;
    margin-top: 14px;
  }}
  .pool-sub {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 10px;
    color: #7A758D;
    margin-top: 4px;
  }}
  .conduit-line {{
    width: 100px;
    height: 40px;
  }}
</style>
</head>
<body>
  <div class="film-grain"></div>
  <div class="card-header">
    <div class="header-left">
      <div class="protocol-badge">INTEGRATION // BLEND PROTOCOL</div>
      <div class="telemetry-meta">EXECUTION: ATOMIC SINGLE-TRANSACTION · SOROBAN WASM</div>
    </div>
    {VANNA_MONOGRAM}
  </div>

  <div class="diagram-stage">
    <!-- NODE 1: USER WALLET -->
    <div class="pipeline-node">
      <div class="wallet-hex">
        <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="#A387FF" stroke-width="1.8">
          <rect x="2" y="5" width="20" height="14" rx="3"/>
          <path d="M16 12h.01"/>
          <path d="M2 10h20"/>
        </svg>
      </div>
      <div class="wallet-title">User Wallet Node</div>
      <div class="wallet-sub">KEYPAIR SIGNER</div>
    </div>

    <!-- CONDUIT 1 -->
    <svg class="conduit-line" viewBox="0 0 100 40">
      <line x1="0" y1="20" x2="85" y2="20" stroke="#A387FF" stroke-width="2.5" />
      <polygon points="85,15 98,20 85,25" fill="#A387FF" />
    </svg>

    <!-- NODE 2: VANNA MARGIN ACCOUNT -->
    <div class="pipeline-node">
      <div class="account-cube">
        <div class="ports-left">
          <div class="port-dot"></div>
          <div class="port-dot"></div>
        </div>
        <div class="account-title">Vanna Margin Account</div>
        <div class="account-sub">ISOLATED SMARTACCOUNT</div>
        <div class="account-badge">ZERO RISK CONTAGION</div>
        <div class="ports-right">
          <div class="port-dot"></div>
          <div class="port-dot"></div>
        </div>
      </div>
      <div class="wallet-title">SmartAccount Sandbox</div>
      <div class="wallet-sub">AUTOMATED RISK SHIELD</div>
    </div>

    <!-- CONDUIT 2 -->
    <svg class="conduit-line" viewBox="0 0 100 40">
      <line x1="0" y1="20" x2="85" y2="20" stroke="#FC5457" stroke-width="2.5" stroke-dasharray="6 3" />
      <polygon points="85,15 98,20 85,25" fill="#FC5457" />
    </svg>

    <!-- NODE 3: BLEND PROTOCOL -->
    <div class="pipeline-node">
      <div class="pool-matrix">
        <div class="blusdc-badge">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><circle cx="12" cy="12" r="10"/></svg>
          BLUSDC YIELD TOKEN
        </div>
        <div class="pool-grid">
          <div class="pool-cube">POOL A<br><span style="font-size:8px;color:#7A758D">LIQUIDITY</span></div>
          <div class="pool-cube">POOL B<br><span style="font-size:8px;color:#7A758D">LIQUIDITY</span></div>
          <div class="pool-cube">POOL C<br><span style="font-size:8px;color:#7A758D">LIQUIDITY</span></div>
          <div class="pool-cube">POOL D<br><span style="font-size:8px;color:#7A758D">LIQUIDITY</span></div>
        </div>
      </div>
      <div class="pool-title">Blend Protocol Lending Pool</div>
      <div class="pool-sub">STELLAR SOROBAN MARKET</div>
    </div>
  </div>

  <div class="card-footer">
    <div class="footer-left">
      <div>ROUTING: <span>DIRECT ATOMIC</span></div>
      <div>BORROW ASSET: <span>BLUSDC</span></div>
      <div>NETWORK: <span>STELLAR SOROBAN</span></div>
    </div>
    <div class="footer-right">test.stellar.vanna.finance</div>
  </div>
</body>
</html>
"""

# HTML Card 3: Gas Comparison
CARD_3_HTML = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
{COMMON_STYLES}
  .compare-container {{
    display: flex;
    flex-direction: column;
    gap: 20px;
    width: 100%;
    margin: auto 0;
  }}
  .compare-row {{
    background: rgba(14, 10, 24, 0.7);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 16px;
    padding: 20px 28px;
    display: grid;
    grid-template-columns: 240px 160px 1fr 240px;
    align-items: center;
    gap: 24px;
    box-shadow: 0 10px 30px rgba(0,0,0,0.4);
  }}
  .compare-row.evm {{
    border-left: 4px solid #FC5457;
  }}
  .compare-row.vanna {{
    border-left: 4px solid #22D3C4;
    background: rgba(22, 14, 38, 0.75);
    border-color: rgba(163, 135, 255, 0.25);
    box-shadow: 0 0 30px rgba(34, 211, 196, 0.08);
  }}
  .row-title {{
    font-size: 16px;
    font-weight: 800;
    color: #FFF;
    display: flex;
    flex-direction: column;
    gap: 4px;
  }}
  .row-sub {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 10px;
    color: #7A758D;
  }}
  .fee-block {{
    display: flex;
    flex-direction: column;
  }}
  .fee-value {{
    font-size: 26px;
    font-weight: 800;
  }}
  .fee-value.red {{ color: #FC5457; }}
  .fee-value.green {{ color: #22D3C4; }}
  .fee-label {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 9px;
    color: #7A758D;
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }}
  .conduit-block {{
    display: flex;
    align-items: center;
    gap: 12px;
  }}
  .conduit-bar {{
    flex: 1;
    height: 8px;
    border-radius: 4px;
    position: relative;
    overflow: hidden;
  }}
  .conduit-bar.red {{ background: rgba(252, 84, 87, 0.2); }}
  .conduit-bar.red::after {{
    content: '';
    position: absolute;
    left: 20%; width: 40%; height: 100%;
    background: #FC5457;
    border-radius: 4px;
  }}
  .conduit-bar.green {{ background: rgba(34, 211, 196, 0.2); }}
  .conduit-bar.green::after {{
    content: '';
    position: absolute;
    left: 0; width: 100%; height: 100%;
    background: linear-gradient(90deg, #A387FF 0%, #22D3C4 100%);
    border-radius: 4px;
  }}
  .status-badge-box {{
    padding: 10px 16px;
    border-radius: 8px;
    text-align: center;
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.05em;
  }}
  .status-badge-box.red {{
    background: rgba(252, 84, 87, 0.12);
    border: 1px solid rgba(252, 84, 87, 0.35);
    color: #FC5457;
  }}
  .status-badge-box.green {{
    background: rgba(34, 211, 196, 0.12);
    border: 1px solid rgba(34, 211, 196, 0.4);
    color: #22D3C4;
    box-shadow: 0 0 20px rgba(34, 211, 196, 0.2);
  }}
</style>
</head>
<body>
  <div class="film-grain"></div>
  <div class="card-header">
    <div class="header-left">
      <div class="protocol-badge">ANALYSIS // GAS VOLATILITY &amp; DEFENSE</div>
      <div class="telemetry-meta">STRESS SIMULATION: -15% HIGH-VOLATILITY SHOCK</div>
    </div>
    {VANNA_MONOGRAM}
  </div>

  <div class="compare-container">
    <!-- ROW 1: EVM -->
    <div class="compare-row evm">
      <div class="row-title">
        Traditional EVM Lending
        <div class="row-sub">ETHEREUM &amp; OPTIMISTIC L2s</div>
      </div>
      <div class="fee-block">
        <div class="fee-value red">$42.50</div>
        <div class="fee-label">GAS SPIKE ON DROP</div>
      </div>
      <div class="conduit-block">
        <div class="conduit-bar red"></div>
        <div style="font-family:'JetBrains Mono',monospace;font-size:10px;color:#FC5457;white-space:nowrap;">CONGESTED MEMPOOL</div>
      </div>
      <div class="status-badge-box red">
        TRANSACTION DELAYED<br><span style="font-size:9px;opacity:0.8">LIQUIDATION RISK</span>
      </div>
    </div>

    <!-- ROW 2: VANNA ON STELLAR -->
    <div class="compare-row vanna">
      <div class="row-title">
        Vanna on Stellar
        <div class="row-sub">SOROBAN WASM RUNTIME</div>
      </div>
      <div class="fee-block">
        <div class="fee-value green">&lt; $0.001</div>
        <div class="fee-label">PREDICTABLE SUB-CENT FEE</div>
      </div>
      <div class="conduit-block">
        <div class="conduit-bar green"></div>
        <div style="font-family:'JetBrains Mono',monospace;font-size:10px;color:#22D3C4;white-space:nowrap;">INSTANT ATOMIC FINALITY</div>
      </div>
      <div class="status-badge-box green">
        POSITION SECURED<br><span style="font-size:9px;opacity:0.8">AUTONOMOUS REBALANCE</span>
      </div>
    </div>
  </div>

  <div class="card-footer">
    <div class="footer-left">
      <div>LEDGER CLOSURE: <span>3.5 SECONDS</span></div>
      <div>BASE INCLUSION FEE: <span>100 STROOPS</span></div>
      <div>PROTECTION: <span>24/7 SESSION KEYS</span></div>
    </div>
    <div class="footer-right">test.stellar.vanna.finance</div>
  </div>
</body>
</html>
"""


def render_card_with_chrome(html_content: str, output_png_path: Path):
    tmp_html = output_png_path.with_suffix(".tmp.html")
    tmp_html.write_text(html_content, encoding="utf-8")
    
    cmd = [
        CHROME_PATH,
        "--headless=new",
        "--disable-gpu",
        "--hide-scrollbars",
        "--force-device-scale-factor=2",
        "--window-size=1200,675",
        f"--screenshot={output_png_path.resolve()}",
        str(tmp_html.resolve())
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if tmp_html.exists():
        tmp_html.unlink()
    print(f"✅ Rendered: {output_png_path.name} ({output_png_path.stat().st_size:,} bytes)")


if __name__ == "__main__":
    print("🚀 Generating Hybrid Vector Schematic Cards via Headless Chrome...")
    render_card_with_chrome(CARD_1_HTML, STATE_DIR / "vanna_hybrid_post1_multiplier.png")
    render_card_with_chrome(CARD_2_HTML, STATE_DIR / "vanna_hybrid_post2_composability.png")
    render_card_with_chrome(CARD_3_HTML, STATE_DIR / "vanna_hybrid_post4_gas_comparison.png")
    print("All hybrid cards successfully rendered.")
