#!/usr/bin/env python3
"""Builds an interactive Twitter feed preview pairing punchy 2-4 line posts with pure textless geometric visuals."""

from __future__ import annotations

import base64
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
STATE_DIR = REPO_ROOT / "pipeline" / "state"

img1_path = STATE_DIR / "vanna_pure_design_post1_isolation.png"
img2_path = STATE_DIR / "vanna_pure_design_post2_deflection.png"
img3_path = STATE_DIR / "vanna_pure_design_post3_sandbox.png"

b64_1 = base64.b64encode(img1_path.read_bytes()).decode("utf-8") if img1_path.exists() else ""
b64_2 = base64.b64encode(img2_path.read_bytes()).decode("utf-8") if img2_path.exists() else ""
b64_3 = base64.b64encode(img3_path.read_bytes()).decode("utf-8") if img3_path.exists() else ""

t1_text = """In Aave v3, when one exotic collateral depegs, all depositors take the haircut.

Morpho and Euler proved the alternative: isolate markets to discrete pairs.

DeFi credit is moving from pooled risk to compartmentalized risk."""

t2_text = """Most liquidations don't fail on the math. They fail in the mempool.

When gas jumps to 150 gwei, MEV bots front-run your rebalance and pocket a 10% fee.

Leverage without predictable execution is just queued liquidation."""

t3_text = """Isolated SmartAccounts on Stellar Soroban.

Your debt stays in your own sandbox. Core reserves never absorb cross-account losses.

Automated rebalances fire at 1.25x Net Health Factor before the 1.10x floor at 0.00014 XLM fixed gas.

Testnet live: test.stellar.vanna.finance"""

preview_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Vanna Twitter Posts & Textless Design Previews</title>
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
    background-image: 
      radial-gradient(circle at 10% 20%, rgba(71, 20, 133, 0.25) 0%, transparent 40%),
      radial-gradient(circle at 90% 80%, rgba(94, 13, 70, 0.2) 0%, transparent 40%);
    color: #F3F4F6;
    font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
    padding: 32px 20px;
    display: flex;
    justify-content: center;
    min-height: 100vh;
  }}
  .container {{
    max-width: 680px;
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
  h1 {{ font-size: 26px; font-weight: 800; color: #FFF; margin-bottom: 6px; }}
  .subtitle {{ font-size: 14px; color: #9CA3AF; margin-bottom: 16px; }}
  .tweet-card {{
    background: var(--card-bg);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 24px;
    display: flex;
    flex-direction: column;
    gap: 16px;
    backdrop-filter: blur(20px);
    transition: all 0.2s ease;
  }}
  .tweet-card:hover {{
    border-color: var(--border-hover);
    box-shadow: 0 12px 36px rgba(71, 20, 133, 0.25);
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
    width: 38px;
    height: 38px;
    border-radius: 50%;
    background: linear-gradient(135deg, #471485, #5E0D46);
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 800;
    font-size: 14px;
    color: #FFF;
    border: 1px solid rgba(255, 255, 255, 0.15);
  }}
  .author-text {{ display: flex; flex-direction: column; }}
  .name {{ font-weight: 700; font-size: 14px; color: #FFF; }}
  .handle {{ font-size: 12px; color: #6B7280; }}
  .tag {{ font-family: 'JetBrains Mono', monospace; font-size: 11px; padding: 4px 8px; border-radius: 4px; background: rgba(255,255,255,0.05); color: #9CA3AF; border: 1px solid rgba(255,255,255,0.08); }}
  .tweet-text {{
    font-size: 15px;
    line-height: 1.6;
    color: #E5E7EB;
    white-space: pre-wrap;
  }}
  .tweet-image {{
    width: 100%;
    border-radius: 12px;
    overflow: hidden;
    border: 1px solid rgba(255, 255, 255, 0.1);
    background: #000;
  }}
  .tweet-image img {{
    width: 100%;
    height: auto;
    display: block;
    transition: transform 0.3s ease;
  }}
  .tweet-image:hover img {{
    transform: scale(1.01);
  }}
  .tweet-footer {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
    color: #6B7280;
    padding-top: 10px;
    border-top: 1px solid rgba(255, 255, 255, 0.05);
  }}
  .copy-btn {{
    background: rgba(255, 255, 255, 0.06);
    border: 1px solid rgba(255, 255, 255, 0.12);
    color: #F3F4F6;
    padding: 6px 14px;
    border-radius: 6px;
    font-size: 12px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s;
  }}
  .copy-btn:hover {{ background: var(--accent-violet); color: #000; border-color: var(--accent-violet); }}
</style>
</head>
<body>
<div class="container">
  <div>
    <span class="header-badge">VANNA GTM TWITTER PRODUCTION</span>
    <h1>Punchy Posts & 100% Textless Visuals</h1>
    <p class="subtitle">Short Twitter copy paired with abstract geometric design metaphors.</p>
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
    <div class="tweet-text" id="t1">{t1_text}</div>
    <div class="tweet-image">
      <img src="data:image/png;base64,{b64_1}" alt="Textless Geometric Isolation Visual">
    </div>
    <div class="tweet-footer">
      <span>160 chars · Pure Textless Design Metaphor</span>
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
    <div class="tweet-text" id="t2">{t2_text}</div>
    <div class="tweet-image">
      <img src="data:image/png;base64,{b64_2}" alt="Textless Sub-Second Deflection Visual">
    </div>
    <div class="tweet-footer">
      <span>180 chars · Pure Textless Velocity Metaphor</span>
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
      <span class="tag" style="color: #22D3C4; border-color: rgba(34,211,196,0.3);">Product // Testnet</span>
    </div>
    <div class="tweet-text" id="t3">{t3_text}</div>
    <div class="tweet-image">
      <img src="data:image/png;base64,{b64_3}" alt="Textless SmartAccount Sandbox Visual">
    </div>
    <div class="tweet-footer">
      <span>245 chars · Pure Textless Architecture Metaphor</span>
      <button class="copy-btn" onclick="navigator.clipboard.writeText(document.getElementById('t3').innerText); this.innerText='Copied!'; setTimeout(()=>this.innerText='Copy', 2000);">Copy</button>
    </div>
  </div>

</div>
</body>
</html>"""

out_file = STATE_DIR / "vanna_posts_preview.html"
out_file.write_text(preview_html, encoding="utf-8")
print(f"✅ Updated preview HTML with textless designs: {out_file.name} ({out_file.stat().st_size:,} bytes)")
