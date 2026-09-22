#!/usr/bin/env python3
"""Generates 3 crisp, native Twitter cards (1200x675, 2x Retina) and updates the preview HTML.
Renders via Headless Chrome with dense developer typography and Vanna brand tokens.
"""

from __future__ import annotations

import base64
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

# Base style wrapper
def wrap_card_html(badge: str, meta: str, main_content: str, footer_left: str, footer_right: str) -> str:
    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@500;600;700;800&family=JetBrains+Mono:wght@400;500;600;700&display=swap');
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
  .badge {{
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
  .meta {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
    color: #8C879E;
    letter-spacing: 0.05em;
  }}
  .monogram-svg {{
    width: 28px;
    height: 28px;
    opacity: 0.4;
  }}
  .main-stage {{
    position: relative;
    width: 100%;
    height: 420px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 24px;
    z-index: 2;
  }}
  .card-footer {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
    color: #6C687D;
    letter-spacing: 0.05em;
    border-top: 1px solid rgba(255, 255, 255, 0.08);
    padding-top: 14px;
    z-index: 2;
  }}
</style>
</head>
<body>
  <div class="card-header">
    <div class="header-left">
      <span class="badge">{badge}</span>
      <span class="meta">{meta}</span>
    </div>
    {VANNA_MONOGRAM}
  </div>

  <div class="main-stage">
    {main_content}
  </div>

  <div class="card-footer">
    <span>{footer_left}</span>
    <span>{footer_right}</span>
  </div>
</body>
</html>
"""

# -----------------------------------------------------------------------------
# CARD 1: Monolithic Shared Pool vs Modular Isolated Vaults
# -----------------------------------------------------------------------------
CONTENT_CARD1 = """
<div style="flex: 1; display: flex; flex-direction: column; gap: 16px;">
  <div style="font-size: 13px; font-family: 'JetBrains Mono', monospace; color: #FC5457; letter-spacing: 0.08em; text-transform: uppercase;">Aave v3 / Compound Monolithic Architecture</div>
  <div style="background: rgba(252, 84, 87, 0.06); border: 1px solid rgba(252, 84, 87, 0.25); border-radius: 12px; padding: 24px; display: flex; flex-direction: column; gap: 12px;">
    <div style="font-size: 20px; font-weight: 700; color: #FFF;">Shared Pool State</div>
    <div style="font-size: 14px; color: #9CA3AF; line-height: 1.5;">One exotic collateral depeg or oracle failure socializes bad debt across 100% of depositors.</div>
    <div style="display: flex; gap: 8px; margin-top: 8px;">
      <span style="font-family: 'JetBrains Mono', monospace; font-size: 11px; background: rgba(252, 84, 87, 0.15); color: #FC5457; padding: 4px 8px; border-radius: 4px;">Global Haircuts</span>
      <span style="font-family: 'JetBrains Mono', monospace; font-size: 11px; background: rgba(255, 255, 255, 0.05); color: #888; padding: 4px 8px; border-radius: 4px;">Contagion Risk: High</span>
    </div>
  </div>
</div>

<div style="width: 2px; height: 320px; background: rgba(255, 255, 255, 0.08);"></div>

<div style="flex: 1; display: flex; flex-direction: column; gap: 16px;">
  <div style="font-size: 13px; font-family: 'JetBrains Mono', monospace; color: #22D3C4; letter-spacing: 0.08em; text-transform: uppercase;">Modular Isolated Vaults (Morpho / Vanna)</div>
  <div style="background: rgba(34, 211, 196, 0.06); border: 1px solid rgba(34, 211, 196, 0.25); border-radius: 12px; padding: 24px; display: flex; flex-direction: column; gap: 12px;">
    <div style="font-size: 20px; font-weight: 700; color: #FFF;">Compartmentalized Risk</div>
    <div style="font-size: 14px; color: #9CA3AF; line-height: 1.5;">Isolated contract state per market. Deficits remain quarantined to the specific pair.</div>
    <div style="display: flex; gap: 8px; margin-top: 8px;">
      <span style="font-family: 'JetBrains Mono', monospace; font-size: 11px; background: rgba(34, 211, 196, 0.15); color: #22D3C4; padding: 4px 8px; border-radius: 4px;">0% Pool Contagion</span>
      <span style="font-family: 'JetBrains Mono', monospace; font-size: 11px; background: rgba(255, 255, 255, 0.05); color: #888; padding: 4px 8px; border-radius: 4px;">Contract-Level Isolation</span>
    </div>
  </div>
</div>
"""

# -----------------------------------------------------------------------------
# CARD 2: Mempool Gas War vs Deterministic Telemetry
# -----------------------------------------------------------------------------
CONTENT_CARD2 = """
<div style="flex: 1; display: flex; flex-direction: column; gap: 16px;">
  <div style="font-size: 13px; font-family: 'JetBrains Mono', monospace; color: #FC5457; letter-spacing: 0.08em; text-transform: uppercase;">EVM Priority Gas Auctions</div>
  <div style="background: rgba(252, 84, 87, 0.06); border: 1px solid rgba(252, 84, 87, 0.25); border-radius: 12px; padding: 24px; display: flex; flex-direction: column; gap: 12px;">
    <div style="font-size: 32px; font-weight: 800; font-family: 'JetBrains Mono', monospace; color: #FC5457;">150+ GWEI</div>
    <div style="font-size: 14px; color: #9CA3AF; line-height: 1.5;">Mempool congestion prices out borrower rebalances while MEV searchers front-run liquidations for a 10% fee cut.</div>
    <div style="font-family: 'JetBrains Mono', monospace; font-size: 11px; color: #FC5457;">Pending in Mempool -> Liquidated</div>
  </div>
</div>

<div style="width: 2px; height: 320px; background: rgba(255, 255, 255, 0.08);"></div>

<div style="flex: 1; display: flex; flex-direction: column; gap: 16px;">
  <div style="font-size: 13px; font-family: 'JetBrains Mono', monospace; color: #A387FF; letter-spacing: 0.08em; text-transform: uppercase;">Stellar Soroban Execution</div>
  <div style="background: rgba(163, 135, 255, 0.06); border: 1px solid rgba(163, 135, 255, 0.25); border-radius: 12px; padding: 24px; display: flex; flex-direction: column; gap: 12px;">
    <div style="font-size: 32px; font-weight: 800; font-family: 'JetBrains Mono', monospace; color: #A387FF;">0.00014 XLM</div>
    <div style="font-size: 14px; color: #9CA3AF; line-height: 1.5;">Deterministic transaction fees with ~320ms Mercury event streaming. Automated defense fires before liquidation floor.</div>
    <div style="font-family: 'JetBrains Mono', monospace; font-size: 11px; color: #22D3C4;">Zero Public Mempool Bidding Wars</div>
  </div>
</div>
"""

# -----------------------------------------------------------------------------
# CARD 3: Vanna Composable SmartAccount Sandbox
# -----------------------------------------------------------------------------
CONTENT_CARD3 = """
<div style="flex: 1; display: flex; flex-direction: column; justify-content: center; gap: 16px;">
  <div style="font-size: 13px; font-family: 'JetBrains Mono', monospace; color: #A387FF; letter-spacing: 0.08em;">STELLAR SOROBAN CONTRACT ARCHITECTURE</div>
  <h2 style="font-size: 32px; font-weight: 800; color: #FFFFFF; line-height: 1.25;">Dedicated SmartAccount Sandboxes. Zero Contagion.</h2>
  <p style="font-size: 15px; color: #9CA3AF; line-height: 1.6;">Borrowers execute within isolated SmartAccount instances. Deficits remain quarantined to the sandbox while capital deploys composably to Blend and Aquarius.</p>
</div>

<div style="width: 360px; background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 14px; padding: 24px; display: flex; flex-direction: column; gap: 18px;">
  <div style="display: flex; justify-content: space-between; align-items: baseline; border-bottom: 1px solid rgba(255,255,255,0.06); padding-bottom: 12px;">
    <span style="font-size: 12px; font-family: 'JetBrains Mono', monospace; color: #888;">PROACTIVE DEFENSE</span>
    <span style="font-size: 22px; font-weight: 700; font-family: 'JetBrains Mono', monospace; color: #22D3C4;">1.25x HF</span>
  </div>
  <div style="display: flex; justify-content: space-between; align-items: baseline; border-bottom: 1px solid rgba(255,255,255,0.06); padding-bottom: 12px;">
    <span style="font-size: 12px; font-family: 'JetBrains Mono', monospace; color: #888;">LIQUIDATION FLOOR</span>
    <span style="font-size: 22px; font-weight: 700; font-family: 'JetBrains Mono', monospace; color: #FC5457;">1.10x HF</span>
  </div>
  <div style="display: flex; justify-content: space-between; align-items: baseline;">
    <span style="font-size: 12px; font-family: 'JetBrains Mono', monospace; color: #888;">NETWORK GAS</span>
    <span style="font-size: 18px; font-weight: 700; font-family: 'JetBrains Mono', monospace; color: #A387FF;">0.00014 XLM</span>
  </div>
</div>
"""

def render_cards():
    cards = [
        ("vanna_card1_isolation.png", wrap_card_html("RESEARCH // RISK ARCHITECTURE", "MONOLITHIC VS ISOLATED", CONTENT_CARD1, "vanna.finance / research", "AAVE V3 vs MORPHO BLUE")),
        ("vanna_card2_mempool.png", wrap_card_html("RESEARCH // EXECUTION QUEUE", "MEMPOOL MEV & LATENCY", CONTENT_CARD2, "vanna.finance / research", "ETHEREUM vs SOROBAN")),
        ("vanna_card3_sandbox.png", wrap_card_html("PRODUCT // STELLAR TESTNET", "SMARTACCOUNT SANDBOXES", CONTENT_CARD3, "test.stellar.vanna.finance", "1.10x HEALTH FACTOR FLOOR"))
    ]

    rendered_paths = []
    for filename, html_data in cards:
        tmp_html = STATE_DIR / f"temp_{filename}.html"
        tmp_html.write_text(html_data, encoding="utf-8")
        out_png = STATE_DIR / filename

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
        if tmp_html.exists(): tmp_html.unlink()
        print(f"✅ Rendered Twitter Card: {out_png.name} ({out_png.stat().st_size:,} bytes)")
        rendered_paths.append(out_png)

    # Now update preview HTML with base64 encoded versions
    b64_1 = base64.b64encode(rendered_paths[0].read_bytes()).decode("utf-8")
    b64_2 = base64.b64encode(rendered_paths[1].read_bytes()).decode("utf-8")
    b64_3 = base64.b64encode(rendered_paths[2].read_bytes()).decode("utf-8")

    preview_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Vanna Twitter Posts & Developer Cards</title>
<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@500;600;700;800&family=JetBrains+Mono:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
  :root {{
    --bg: #07020D;
    --card-bg: rgba(255, 255, 255, 0.03);
    --border: rgba(255, 255, 255, 0.08);
    --border-hover: rgba(163, 135, 255, 0.3);
    --accent-violet: #A387FF;
    --accent-coral: #FC5457;
    --accent-cyan: #22D3C4;
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    background: var(--bg);
    color: #F3F4F6;
    font-family: 'Plus Jakarta Sans', sans-serif;
    padding: 32px 20px;
    display: flex;
    justify-content: center;
  }}
  .container {{
    max-width: 720px;
    width: 100%;
    display: flex;
    flex-direction: column;
    gap: 32px;
  }}
  .header-badge {{
    display: inline-flex;
    align-items: center;
    gap: 8px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
    color: var(--accent-violet);
    background: rgba(163, 135, 255, 0.1);
    padding: 4px 10px;
    border-radius: 6px;
    border: 1px solid rgba(163, 135, 255, 0.25);
    margin-bottom: 12px;
  }}
  h1 {{ font-size: 24px; font-weight: 800; color: #FFF; }}
  .tweet-card {{
    background: var(--card-bg);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 20px;
    display: flex;
    flex-direction: column;
    gap: 16px;
  }}
  .tweet-meta {{
    display: flex;
    justify-content: space-between;
    align-items: center;
  }}
  .author {{
    display: flex;
    align-items: center;
    gap: 10px;
  }}
  .avatar {{
    width: 36px;
    height: 36px;
    border-radius: 50%;
    background: linear-gradient(135deg, #471485, #5E0D46);
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 800;
    font-size: 13px;
    color: #FFF;
  }}
  .author-text {{ display: flex; flex-direction: column; }}
  .name {{ font-weight: 700; font-size: 14px; color: #FFF; }}
  .handle {{ font-size: 12px; color: #6B7280; }}
  .tag {{ font-family: 'JetBrains Mono', monospace; font-size: 11px; padding: 3px 8px; border-radius: 4px; background: rgba(255,255,255,0.05); color: #9CA3AF; }}
  .tweet-text {{
    font-size: 15px;
    line-height: 1.6;
    color: #E5E7EB;
    white-space: pre-wrap;
  }}
  .tweet-image {{
    width: 100%;
    border-radius: 10px;
    overflow: hidden;
    border: 1px solid rgba(255, 255, 255, 0.1);
  }}
  .tweet-image img {{
    width: 100%;
    height: auto;
    display: block;
  }}
  .tweet-footer {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
    color: #6B7280;
    padding-top: 8px;
    border-top: 1px solid rgba(255, 255, 255, 0.05);
  }}
  .copy-btn {{
    background: rgba(255, 255, 255, 0.06);
    border: 1px solid rgba(255, 255, 255, 0.12);
    color: #F3F4F6;
    padding: 5px 12px;
    border-radius: 6px;
    font-size: 12px;
    font-weight: 600;
    cursor: pointer;
  }}
  .copy-btn:hover {{ background: var(--accent-violet); color: #000; }}
</style>
</head>
<body>
<div class="container">
  <div>
    <span class="header-badge">VANNA GTM TWITTER PRODUCTION</span>
    <h1>Punchy Twitter Posts & Technical Cards</h1>
  </div>

  <!-- POST 1 -->
  <div class="tweet-card">
    <div class="tweet-meta">
      <div class="author">
        <div class="avatar">V</div>
        <div class="author-text">
          <span class="name">Vanna Research</span>
          <span class="handle">@vanna_fi</span>
        </div>
      </div>
      <span class="tag">Research 1 // Isolation</span>
    </div>
    <div class="tweet-text" id="t1">In Aave v3, when one exotic collateral depegs, all depositors take the haircut.

Morpho and Euler proved the alternative: isolate markets to discrete pairs.

DeFi credit is moving from pooled risk to compartmentalized risk.</div>
    <div class="tweet-image">
      <img src="data:image/png;base64,{b64_1}" alt="Card 1">
    </div>
    <div class="tweet-footer">
      <span>160 characters · 2x Retina Developer Card</span>
      <button class="copy-btn" onclick="navigator.clipboard.writeText(document.getElementById('t1').innerText); this.innerText='Copied!'; setTimeout(()=>this.innerText='Copy', 2000);">Copy</button>
    </div>
  </div>

  <!-- POST 2 -->
  <div class="tweet-card">
    <div class="tweet-meta">
      <div class="author">
        <div class="avatar">V</div>
        <div class="author-text">
          <span class="name">Vanna Research</span>
          <span class="handle">@vanna_fi</span>
        </div>
      </div>
      <span class="tag">Research 2 // Mempool MEV</span>
    </div>
    <div class="tweet-text" id="t2">Most liquidations don't fail on the math. They fail in the mempool.

When gas jumps to 150 gwei, MEV bots front-run your rebalance and pocket a 10% fee.

Leverage without predictable execution is just queued liquidation.</div>
    <div class="tweet-image">
      <img src="data:image/png;base64,{b64_2}" alt="Card 2">
    </div>
    <div class="tweet-footer">
      <span>180 characters · 2x Retina Developer Card</span>
      <button class="copy-btn" onclick="navigator.clipboard.writeText(document.getElementById('t2').innerText); this.innerText='Copied!'; setTimeout(()=>this.innerText='Copy', 2000);">Copy</button>
    </div>
  </div>

  <!-- POST 3 -->
  <div class="tweet-card">
    <div class="tweet-meta">
      <div class="author">
        <div class="avatar" style="background: linear-gradient(135deg, #FC5457, #5E0D46);">V</div>
        <div class="author-text">
          <span class="name">Vanna Protocol</span>
          <span class="handle">@vanna_fi</span>
        </div>
      </div>
      <span class="tag" style="color: #22D3C4;">Vanna Product // Testnet</span>
    </div>
    <div class="tweet-text" id="t3">Isolated SmartAccounts on Stellar Soroban.

Your debt stays in your own sandbox. Core reserves never absorb cross-account losses.

Automated rebalances fire at 1.25x Net Health Factor before the 1.10x floor at 0.00014 XLM fixed gas.

Testnet live: test.stellar.vanna.finance</div>
    <div class="tweet-image">
      <img src="data:image/png;base64,{b64_3}" alt="Card 3">
    </div>
    <div class="tweet-footer">
      <span>245 characters · 2x Retina Developer Card</span>
      <button class="copy-btn" onclick="navigator.clipboard.writeText(document.getElementById('t3').innerText); this.innerText='Copied!'; setTimeout(()=>this.innerText='Copy', 2000);">Copy</button>
    </div>
  </div>

</div>
</body>
</html>
"""
    out_preview = STATE_DIR / "vanna_posts_preview.html"
    out_preview.write_text(preview_html, encoding="utf-8")
    print(f"✅ Updated preview HTML: {out_preview.name} ({out_preview.stat().st_size:,} bytes)")

if __name__ == "__main__":
    render_cards()
