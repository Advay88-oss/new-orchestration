#!/usr/bin/env python3
"""Renders corrected 1.10x Net Health Factor Solvency Rail.

Fixes all 4 issues:
  1. Removes internal prompt leakage in header.
  2. Smooth parabolic deflection curve that never clips through card borders.
  3. Clean trajectory rebound without line collisions.
  4. Symmetrical alignment across all 3 solvency zones.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
STATE_DIR = REPO_ROOT / "pipeline" / "state"

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
    <linearGradient id="p0" x1="44" y1="0" x2="128" y2="50" gradientUnits="userSpaceOnUse"><stop stop-color="#FC5457"/><stop offset="1" stop-color="#703AE6"/></linearGradient>
    <linearGradient id="p1" x1="44" y1="0" x2="128" y2="50" gradientUnits="userSpaceOnUse"><stop stop-color="#FC5457"/><stop offset="1" stop-color="#703AE6"/></linearGradient>
    <linearGradient id="p2" x1="44" y1="0" x2="128" y2="50" gradientUnits="userSpaceOnUse"><stop stop-color="#FC5457"/><stop offset="1" stop-color="#703AE6"/></linearGradient>
  </defs>
</svg>
"""

HTML_CONTENT = f"""<!DOCTYPE html>
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
  
  /* Telemetry Visual Area */
  .telemetry-stage {{
    position: relative;
    width: 100%;
    height: 380px;
    display: flex;
    flex-direction: column;
    justify-content: flex-end;
    z-index: 2;
    margin: auto 0;
  }}

  /* SVG Trajectory Overlay */
  .trajectory-svg {{
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 240px;
    z-index: 5;
    pointer-events: none;
  }}

  /* The 3 Solvency Rail Cards */
  .rail-container {{
    display: grid;
    grid-template-columns: 1fr 1fr 1fr;
    gap: 20px;
    width: 100%;
    z-index: 2;
  }}
  .zone-card {{
    background: rgba(14, 10, 24, 0.7);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 16px;
    backdrop-filter: blur(12px);
    padding: 24px 20px;
    display: flex;
    flex-direction: column;
    align-items: center;
    position: relative;
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
  }}
  .zone-card.healthy {{
    border-color: rgba(34, 211, 196, 0.3);
    box-shadow: 0 0 25px rgba(34, 211, 196, 0.08), 0 10px 30px rgba(0, 0, 0, 0.5);
  }}
  .zone-card.trigger {{
    border-color: rgba(163, 135, 255, 0.4);
    box-shadow: 0 0 35px rgba(163, 135, 255, 0.15), 0 10px 30px rgba(0, 0, 0, 0.5);
  }}
  .zone-card.floor {{
    border: 1.5px dashed #FC5457;
    background: rgba(30, 8, 16, 0.4);
    box-shadow: 0 0 30px rgba(252, 84, 87, 0.15), 0 10px 30px rgba(0, 0, 0, 0.5);
  }}
  .zone-badge {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 10px;
    font-weight: 700;
    padding: 4px 12px;
    border-radius: 20px;
    margin-bottom: 12px;
    letter-spacing: 0.08em;
  }}
  .zone-badge.cyan {{
    background: rgba(34, 211, 196, 0.12);
    border: 1px solid rgba(34, 211, 196, 0.4);
    color: #22D3C4;
  }}
  .zone-badge.purple {{
    background: rgba(163, 135, 255, 0.15);
    border: 1px solid rgba(163, 135, 255, 0.4);
    color: #A387FF;
  }}
  .zone-badge.red {{
    background: rgba(252, 84, 87, 0.15);
    border: 1px solid rgba(252, 84, 87, 0.5);
    color: #FC5457;
  }}
  .zone-number {{
    font-size: 42px;
    font-weight: 800;
    color: #FFFFFF;
    letter-spacing: -0.02em;
    line-height: 1;
    margin-bottom: 8px;
  }}
  .zone-number.red {{ color: #FC5457; }}
  .zone-label {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
    font-weight: 700;
    color: #8C879E;
    letter-spacing: 0.05em;
    text-transform: uppercase;
  }}
  .rail-subtext {{
    text-align: center;
    font-family: 'JetBrains Mono', monospace;
    font-size: 10px;
    color: #5A566A;
    margin-top: 14px;
    letter-spacing: 0.15em;
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
      <div class="protocol-badge">RISK ENGINE // NET HEALTH FACTOR</div>
      <div class="telemetry-meta">CONTINUOUS ON-CHAIN SOLVENCY MONITORING · STELLAR SOROBAN</div>
    </div>
    {VANNA_MONOGRAM}
  </div>

  <div class="telemetry-stage">
    <!-- SVG Vector Trajectory: Bounces safely off 1.25x trigger and stays above 1.10x floor -->
    <svg class="trajectory-svg" viewBox="0 0 1104 240">
      <defs>
        <linearGradient id="lineGrad" x1="0" y1="0" x2="1" y2="0">
          <stop offset="0%" stop-color="#22D3C4" />
          <stop offset="45%" stop-color="#A387FF" />
          <stop offset="100%" stop-color="#22D3C4" />
        </linearGradient>
        <filter id="glow">
          <feGaussianBlur stdDeviation="3" result="coloredBlur"/>
          <feMerge>
            <feMergeNode in="coloredBlur"/>
            <feMergeNode in="SourceGraphic"/>
          </feMerge>
        </filter>
      </defs>

      <!-- Trajectory path: starts high left (2.50x), dips toward 1.25x trigger (center), rebounds up right -->
      <path d="M 80,40 C 260,40 450,165 552,165 C 654,165 820,50 1024,50" 
            fill="none" stroke="url(#lineGrad)" stroke-width="3" filter="url(#glow)" />
      
      <!-- Ghost downward danger trajectory that NEVER happens -->
      <path d="M 552,165 C 620,165 680,210 736,210" 
            fill="none" stroke="#FC5457" stroke-width="1.5" stroke-dasharray="4 4" opacity="0.35" />

      <!-- Origin Node: 2.50x Normal Position -->
      <circle cx="80" cy="40" r="5" fill="#22D3C4" />
      <text x="94" y="44" fill="#22D3C4" font-family="JetBrains Mono" font-size="11" font-weight="700">ORIGINAL STATE (2.50x)</text>

      <!-- Inflection Node: 1.25x Defense Rebalance Trigger -->
      <circle cx="552" cy="165" r="7" fill="#A387FF" filter="url(#glow)" />
      <circle cx="552" cy="165" r="3" fill="#FFFFFF" />
      <text x="552" y="145" text-anchor="middle" fill="#FFFFFF" font-family="JetBrains Mono" font-size="11" font-weight="700">
        AUTONOMOUS DEFENSE TRIGGER (1.25x)
      </text>
      <text x="552" y="195" text-anchor="middle" fill="#A387FF" font-family="JetBrains Mono" font-size="10">
        REBALANCE EXECUTED
      </text>

      <!-- Rebound Apex Node: Position Secured (2.10x) -->
      <circle cx="1024" cy="50" r="6" fill="#22D3C4" filter="url(#glow)" />
      <text x="1000" y="32" text-anchor="end" fill="#22D3C4" font-family="JetBrains Mono" font-size="11" font-weight="700">
        POSITION SECURED (2.10x)
      </text>
    </svg>

    <!-- The 3 Aligned Solvency Rail Cards -->
    <div class="rail-container">
      <!-- ZONE 1: HEALTHY -->
      <div class="zone-card healthy">
        <div class="zone-badge cyan">HEALTHY</div>
        <div class="zone-number">2.50×</div>
        <div class="zone-label">HEALTH FACTOR</div>
      </div>

      <!-- ZONE 2: DEFENSE TRIGGER -->
      <div class="zone-card trigger">
        <div class="zone-badge purple">DEFENSE TRIGGER</div>
        <div class="zone-number">1.25×</div>
        <div class="zone-label">AUTOMATED REBALANCE</div>
      </div>

      <!-- ZONE 3: LIQUIDATION FLOOR -->
      <div class="zone-card floor">
        <div class="zone-badge red">IMMUTABLE</div>
        <div class="zone-number red">1.10×</div>
        <div class="zone-label" style="color:#FC5457">LIQUIDATION FLOOR (UNREACHED)</div>
      </div>
    </div>
    
    <div class="rail-subtext">SOLVENCY STATUS RAIL // AUTOMATED THRESHOLD DEFENSE</div>
  </div>

  <div class="card-footer">
    <div class="footer-left">
      <div>SOLVENCY METRIC: <span>COLLATERAL / DEBT</span></div>
      <div>DEFENSE: <span>SUB-SECOND KEEPER</span></div>
      <div>CUSTODY: <span>NON-CUSTODIAL</span></div>
    </div>
    <div class="footer-right">test.stellar.vanna.finance</div>
  </div>
</body>
</html>
"""

def render():
    out_png = STATE_DIR / "vanna_flash_post1_health_factor.png"
    tmp_html = STATE_DIR / "temp_fix_health_factor.html"
    tmp_html.write_text(HTML_CONTENT, encoding="utf-8")
    
    cmd = [
        CHROME_PATH,
        "--headless=new",
        "--disable-gpu",
        "--hide-scrollbars",
        "--force-device-scale-factor=2",
        "--window-size=1200,675",
        f"--screenshot={out_png.resolve()}",
        str(tmp_html.resolve())
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if tmp_html.exists():
        tmp_html.unlink()
    print(f"✅ Rendered perfectly: {out_png.name} ({out_png.stat().st_size:,} bytes)")

if __name__ == "__main__":
    render()
