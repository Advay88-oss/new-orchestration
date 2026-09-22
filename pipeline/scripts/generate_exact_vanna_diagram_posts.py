#!/usr/bin/env python3
"""Generates 2 new Vanna posts in the exact, approved style of post_01_capital_drag.html:
1. Generates 3-step DeFi architectural process flow diagrams with gemini-3.1-flash-image.
2. Creates standalone HTML files with .tweet-card layout, avatar, highlights, and stats.
3. Zero competitor naming. 100% Vanna Protocol on Stellar Soroban.
"""

from __future__ import annotations

import base64
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

STATE_DIR = REPO_ROOT / "pipeline" / "state"

from pipeline.scripts.gemini_flash_image import generate_gemini_image

# -----------------------------------------------------------------------------
# 1. GENERATE DIAGRAM A: Composable Credit Pipeline
# -----------------------------------------------------------------------------
out_diag_a = STATE_DIR / "vanna_diagram_composable_credit_pipeline.png"
prompt_a = (
    "A clean horizontal process flow DeFi architectural schematic diagram for Vanna Protocol on Stellar Soroban. "
    "Background: Deep space black / obsidian (#07020D) with soft ambient radial gradients in electric royal violet (#471485) "
    "in bottom-left and fuchsia-magenta (#5E0D46) in top-right, subtle fine digital film grain. "
    "A balanced, three-stage linear left-to-right transaction pipeline connected by glowing neon violet directional arrows: "
    "1. LEFT NODE (User Wallet Node): A semi-translucent frosted glass rounded-corner hexagon with a thin lavender border, "
    "labeled with clean white sans-serif text 'User Wallet Node' inside and beneath. "
    "2. CENTER NODE (Vanna Margin Account): A large isometric 3D modular cube in solid periwinkle/lavender with clean darker contour lines, "
    "featuring four small rectangular coral/salmon-pink mounting tabs on the visible edges. Labeled with bold white text 'Vanna Margin Account' "
    "and a muted subtitle 'Isolated SmartAccount Sandbox'. "
    "3. RIGHT NODE (Composable Liquidity Destination): A modular 3D isometric lattice cluster of interconnected dark purple blocks "
    "with vivid lavender edge highlights, representing external protocols. Hovering directly atop the central block is a glowing circular badge "
    "surrounded by an electric cyan aura, labeled with bold white text 'Blend & Aquarius'. Labeled beneath 'Composable Liquidity Pool'. "
    "Style: Modern Web3 Dark Mode UI, isometric 3D geometry combined with flat 2D vector elements, soft neon glows, "
    "high-contrast typography, razor-sharp line work, generous negative space. Zero generic crypto spheres with rings, zero typos."
)

print("▶ Generating Diagram A (Composable Credit Pipeline)...")
generate_gemini_image(prompt_a, out_diag_a, project="vanna-mcp", location="global", model="gemini-3.1-flash-image")
print(f"✅ Generated Diagram A: {out_diag_a.name} ({out_diag_a.stat().st_size:,} bytes)")

# -----------------------------------------------------------------------------
# 2. GENERATE DIAGRAM B: Sub-Second Telemetry & Solvency Rail
# -----------------------------------------------------------------------------
out_diag_b = STATE_DIR / "vanna_diagram_subsecond_solvency_rail.png"
prompt_b = (
    "A clean horizontal process flow DeFi architectural risk schematic diagram for Vanna Protocol on Stellar Soroban. "
    "Background: Deep space black / obsidian (#07020D) with soft ambient radial gradients in electric royal violet (#471485) "
    "in bottom-left and fuchsia-magenta (#5E0D46) in top-right, subtle fine digital film grain. "
    "A balanced, three-stage linear left-to-right risk defense pipeline connected by glowing directional vector arrows: "
    "1. LEFT NODE (Mercury Event Stream): A semi-translucent dark frosted glass squircle card with a luminous lavender border, "
    "displaying bold cyan text '~320ms' and labeled 'Mercury Event Stream' with a subtitle 'Sub-Second Ledger Ingestion'. "
    "2. CENTER NODE (Risk Guardian Sentinel): A stylized 3D isometric computer processor die in pale lavender with 16 coral/salmon-pink "
    "connector pins, glowing gently from within. Labeled with dark bold text 'Risk Guardian' and subheader '1.25x Proactive Rebalance'. "
    "3. RIGHT NODE (Protected Solvency Floor): A semi-translucent dark rounded card distinguished by an intense luminous neon coral "
    "outline and protective outer aura, labeled with bold white text '1.10x Health Factor' and subheader 'Protocol Liquidation Floor'. "
    "Below it, a small tag 'Fixed Gas: 0.00014 XLM'. "
    "Style: Modern Web3 Dark Mode UI, 3D isometric elements and frosted glass cards, soft neon glows, high-contrast typography, "
    "clean technical blueprint, generous negative space. Zero clutter, zero AI badges, zero typos."
)

print("\n▶ Generating Diagram B (Sub-Second Telemetry & Solvency Rail)...")
generate_gemini_image(prompt_b, out_diag_b, project="vanna-mcp", location="global", model="gemini-3.1-flash-image")
print(f"✅ Generated Diagram B: {out_diag_b.name} ({out_diag_b.stat().st_size:,} bytes)")

# -----------------------------------------------------------------------------
# 3. COMPILE HTML FILES (Exact post_01_capital_drag.html template)
# -----------------------------------------------------------------------------
b64_a = base64.b64encode(out_diag_a.read_bytes()).decode("utf-8")
b64_b = base64.b64encode(out_diag_b.read_bytes()).decode("utf-8")

monogram_svg = """<svg class="vanna-logo-svg" viewBox="0 0 120 120" fill="none">
  <path d="M59.9886 16.0614C63.1147 13.6729 67.3757 13.3951 70.7757 15.3581C74.1757 17.3211 76.0413 21.1361 75.4986 25.0161L72.1417 49.0153L72.1454 49.0174L65.6912 95.1595L102.868 66.755L114.107 73.2444L68.4972 108.093C65.3711 110.481 61.11 110.759 57.7101 108.796C54.3101 106.833 52.4445 103.018 52.9872 99.138L56.3441 75.1388L56.3404 75.1367L62.7946 28.9947L25.6183 57.3991L14.3784 50.9098L59.9886 16.0614Z" fill="url(#p0)"/>
  <path d="M25.6183 57.3991L36.003 63.3948L33.9183 78.2994L45.9557 69.141L56.3404 75.1367L36.6411 90.1879C33.7348 92.4085 29.7734 92.6668 26.6125 90.8418C23.4545 89.0185 21.7201 85.4763 22.2206 81.872L25.6183 57.3991Z" fill="url(#p1)"/>
  <path d="M102.868 66.755L92.4828 60.7594L94.5675 45.8547L82.5301 55.0131L72.1454 49.0174L91.8447 33.9662C94.751 31.7457 98.7124 31.4874 101.873 33.3123C105.031 35.1356 106.766 38.6778 106.265 42.2822L102.868 66.755Z" fill="url(#p2)"/>
  <defs>
    <linearGradient id="p0" x1="44" y1="0" x2="128" y2="50" gradientUnits="userSpaceOnUse"><stop stop-color="#FC5457"/><stop offset="1" stop-color="#703AE6"/></linearGradient>
    <linearGradient id="p1" x1="44" y1="0" x2="128" y2="50" gradientUnits="userSpaceOnUse"><stop stop-color="#FC5457"/><stop offset="1" stop-color="#703AE6"/></linearGradient>
    <linearGradient id="p2" x1="44" y1="0" x2="128" y2="50" gradientUnits="userSpaceOnUse"><stop stop-color="#FC5457"/><stop offset="1" stop-color="#703AE6"/></linearGradient>
  </defs>
</svg>"""

def make_html_card(tag: str, tag_color: str, text: str, highlight_text: str, img_src: str, views: str, retweets: str, likes: str) -> str:
    full_text = text.replace(highlight_text, f'<span class="highlight" style="color: {tag_color};">{highlight_text}</span>')
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Vanna Protocol — {tag}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@500;600;700&display=swap" rel="stylesheet">
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    background: #07020D;
    color: #F3F1F8;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 40px 20px;
    min-height: 100vh;
  }}
  .tweet-card {{
    width: 100%;
    max-width: 620px;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 16px;
    background: #0C0C10;
    padding: 24px;
    box-shadow: 0 16px 48px rgba(0, 0, 0, 0.85);
  }}
  .post-tag {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
    font-weight: 700;
    color: {tag_color};
    margin-bottom: 12px;
    display: inline-block;
    letter-spacing: 0.05em;
  }}
  .tweet-header {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 16px;
  }}
  .author-meta {{
    display: flex;
    align-items: center;
    gap: 12px;
  }}
  .avatar {{
    width: 48px;
    height: 48px;
    border-radius: 50%;
    background: #110E1B;
    border: 1px solid rgba(163, 135, 255, 0.3);
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 8px;
  }}
  .vanna-logo-svg {{ width: 100%; height: 100%; }}
  .names {{ display: flex; flex-direction: column; }}
  .display-name {{
    font-size: 16px;
    font-weight: 700;
    color: #F3F1F8;
    display: flex;
    align-items: center;
    gap: 4px;
  }}
  .verified-badge {{ color: {tag_color}; width: 18px; height: 18px; }}
  .handle {{ font-size: 14px; color: #A2A1A6; }}
  .tweet-text {{
    font-size: 16px;
    line-height: 1.55;
    color: #E2E1E6;
    margin-bottom: 18px;
    white-space: pre-line;
  }}
  .tweet-text .highlight {{ font-weight: 600; }}
  .media-attachment {{
    border-radius: 14px;
    overflow: hidden;
    border: 1px solid rgba(255, 255, 255, 0.08);
    margin-bottom: 16px;
    background: #07020D;
  }}
  .media-attachment img {{ width: 100%; height: auto; display: block; }}
  .tweet-stats {{
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 13px;
    color: #A2A1A6;
    padding-bottom: 14px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.08);
    margin-bottom: 12px;
  }}
  .actions-row {{
    display: flex;
    justify-content: space-between;
    color: #A2A1A6;
    font-size: 13px;
    padding: 0 10px;
  }}
  .action-btn {{ display: flex; align-items: center; gap: 8px; cursor: pointer; }}
  .action-btn:hover {{ color: {tag_color}; }}
</style>
</head>
<body>

<div class="tweet-card">
  <div class="post-tag">{tag}</div>
  <div class="tweet-header">
    <div class="author-meta">
      <div class="avatar">
        {monogram_svg}
      </div>
      <div class="names">
        <div class="display-name">Vanna <svg class="verified-badge" viewBox="0 0 24 24" fill="currentColor"><path d="M22.5 12.5c0-1.58-.875-2.95-2.148-3.6.154-.435.238-.905.238-1.4 0-2.21-1.79-4-4-4-.495 0-.965.084-1.4.238C14.55 2.475 13.18 1.6 11.6 1.6c-1.58 0-2.95.875-3.6 2.148-.435-.154-.905-.238-1.4-.238-2.21 0-4 1.79-4 4 0 .495.084.965.238 1.4C1.475 10.55.6 11.92.6 13.5c0 1.58.875 2.95 2.148 3.6-.154.435-.238.905-.238 1.4 0 2.21 1.79 4 4 4 .495 0 .965-.084 1.4-.238 1.05 1.273 2.42 2.148 4 2.148 1.58 0 2.95-.875 3.6-2.148.435.154.905.238 1.4.238 2.21 0 4-1.79 4-4 0-.495-.084-.965-.238-1.4 1.273-1.05 2.148-2.42 2.148-4zM10.2 16.6l-3.8-3.8 1.4-1.4 2.4 2.4 6.4-6.4 1.4 1.4-7.8 7.8z"/></svg></div>
        <div class="handle">@VannaProtocol</div>
      </div>
    </div>
    <div class="x-logo"><svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor"><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/></svg></div>
  </div>

  <div class="tweet-text">{full_text}</div>

  <div class="media-attachment">
    <img src="{img_src}" alt="Vanna Architecture Schematic">
  </div>

  <div class="tweet-stats">
    <span>11:20 AM · Sep 17, 2026</span> · <span><strong>{views}</strong> Views</span>
  </div>

  <div class="actions-row">
    <div class="action-btn"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"/></svg> 340</div>
    <div class="action-btn"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 1l4 4-4 4"/><path d="M3 11V9a4 4 0 0 1 4-4h14"/><path d="M7 23l-4-4 4-4"/><path d="M21 13v2a4 4 0 0 1-4 4H3"/></svg> {retweets}</div>
    <div class="action-btn"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/></svg> {likes}</div>
    <div class="action-btn"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"/></svg> 610</div>
  </div>
</div>

</body>
</html>"""

# Post A text
t_a = """Most credit protocols lock liquidity inside their own closed ecosystem.

Vanna routes capital composably through isolated SmartAccount sandboxes on Stellar Soroban.

Deposit collateral once, access up to 10× margin, and deploy directly across Blend and Aquarius in a single atomic transaction.

test.stellar.vanna.finance"""
hl_a = "Vanna routes capital composably through isolated SmartAccount sandboxes on Stellar Soroban."

# Post B text
t_b = """Traditional on-chain liquidations fail when keeper transactions get stuck in volatile network queues.

Vanna integrates sub-second Mercury event telemetry directly on Stellar Soroban.

Ledger events stream in ~320ms. When an account nears 1.25× Net Health Factor, our Risk Guardian rebalances directly inside the user's sandbox—protecting positions before ever touching the 1.10× liquidation floor.

test.stellar.vanna.finance"""
hl_b = "Vanna integrates sub-second Mercury event telemetry directly on Stellar Soroban."

html_a = make_html_card(
    tag="POST #08 // COMPOSABLE CREDIT PIPELINE",
    tag_color="#A387FF",
    text=t_a,
    highlight_text=hl_a,
    img_src=f"data:image/png;base64,{b64_a}",
    views="88.4K",
    retweets="1.2K",
    likes="5.4K"
)
(STATE_DIR / "post_08_composable_credit.html").write_text(html_a, encoding="utf-8")
print("✅ Wrote post_08_composable_credit.html")

html_b = make_html_card(
    tag="POST #09 // SUB-SECOND RISK TELEMETRY",
    tag_color="#22D3C4",
    text=t_b,
    highlight_text=hl_b,
    img_src=f"data:image/png;base64,{b64_b}",
    views="96.1K",
    retweets="1.5K",
    likes="6.8K"
)
(STATE_DIR / "post_09_subsecond_solvency.html").write_text(html_b, encoding="utf-8")
print("✅ Wrote post_09_subsecond_solvency.html")

# Combined master showcase
showcase_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Vanna Architecture Showcase — Exact Style</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@500;600;700&display=swap" rel="stylesheet">
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    background: #07020D;
    background-image: 
      radial-gradient(circle at 10% 20%, rgba(71, 20, 133, 0.3) 0%, transparent 40%),
      radial-gradient(circle at 90% 80%, rgba(94, 13, 70, 0.25) 0%, transparent 40%);
    color: #F3F1F8;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 40px 20px;
    gap: 40px;
    min-height: 100vh;
  }}
  .showcase-header {{
    width: 100%;
    max-width: 620px;
    text-align: left;
    border-bottom: 1px solid rgba(255, 255, 255, 0.08);
    padding-bottom: 20px;
  }}
  .brand-badge {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
    font-weight: 700;
    color: #A387FF;
    background: rgba(163, 135, 255, 0.12);
    border: 1px solid rgba(163, 135, 255, 0.3);
    padding: 4px 10px;
    border-radius: 4px;
    letter-spacing: 0.08em;
    display: inline-block;
    margin-bottom: 12px;
  }}
  h1 {{ font-size: 24px; font-weight: 800; color: #FFF; margin-bottom: 6px; }}
  .subtitle {{ font-size: 13px; color: #A2A1A6; line-height: 1.5; }}
  .tweet-card {{
    width: 100%;
    max-width: 620px;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 16px;
    background: #0C0C10;
    padding: 24px;
    box-shadow: 0 16px 48px rgba(0, 0, 0, 0.85);
  }}
  .post-tag {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
    font-weight: 700;
    margin-bottom: 12px;
    display: inline-block;
    letter-spacing: 0.05em;
  }}
  .tweet-header {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 16px;
  }}
  .author-meta {{ display: flex; align-items: center; gap: 12px; }}
  .avatar {{
    width: 48px; height: 48px; border-radius: 50%;
    background: #110E1B; border: 1px solid rgba(163, 135, 255, 0.3);
    display: flex; align-items: center; justify-content: center; padding: 8px;
  }}
  .vanna-logo-svg {{ width: 100%; height: 100%; }}
  .names {{ display: flex; flex-direction: column; }}
  .display-name {{
    font-size: 16px; font-weight: 700; color: #F3F1F8; display: flex; align-items: center; gap: 4px;
  }}
  .verified-badge {{ width: 18px; height: 18px; }}
  .handle {{ font-size: 14px; color: #A2A1A6; }}
  .tweet-text {{
    font-size: 16px; line-height: 1.55; color: #E2E1E6; margin-bottom: 18px; white-space: pre-line;
  }}
  .tweet-text .highlight {{ font-weight: 600; }}
  .media-attachment {{
    border-radius: 14px; overflow: hidden; border: 1px solid rgba(255, 255, 255, 0.08);
    margin-bottom: 16px; background: #07020D;
  }}
  .media-attachment img {{ width: 100%; height: auto; display: block; }}
  .tweet-stats {{
    display: flex; align-items: center; gap: 6px; font-size: 13px; color: #A2A1A6;
    padding-bottom: 14px; border-bottom: 1px solid rgba(255, 255, 255, 0.08); margin-bottom: 12px;
  }}
  .actions-row {{
    display: flex; justify-content: space-between; color: #A2A1A6; font-size: 13px; padding: 0 10px;
  }}
  .action-btn {{ display: flex; align-items: center; gap: 8px; cursor: pointer; }}
  .action-btn:hover {{ color: #A387FF; }}
</style>
</head>
<body>

<div class="showcase-header">
  <span class="brand-badge">VANNA PURE ARCHITECTURE SHOWCASE</span>
  <h1>Exact post_01_capital_drag.html Format</h1>
  <p class="subtitle">Pure Vanna protocol mechanics on Stellar Soroban. Zero competitor naming. Clean 3-step process flow architectural schematics.</p>
</div>

<!-- POST 08 -->
<div class="tweet-card">
  <div class="post-tag" style="color: #A387FF;">POST #08 // COMPOSABLE CREDIT PIPELINE</div>
  <div class="tweet-header">
    <div class="author-meta">
      <div class="avatar">{monogram_svg}</div>
      <div class="names">
        <div class="display-name">Vanna <svg class="verified-badge" viewBox="0 0 24 24" fill="#A387FF"><path d="M22.5 12.5c0-1.58-.875-2.95-2.148-3.6.154-.435.238-.905.238-1.4 0-2.21-1.79-4-4-4-.495 0-.965.084-1.4.238C14.55 2.475 13.18 1.6 11.6 1.6c-1.58 0-2.95.875-3.6 2.148-.435-.154-.905-.238-1.4-.238-2.21 0-4 1.79-4 4 0 .495.084.965.238 1.4C1.475 10.55.6 11.92.6 13.5c0 1.58.875 2.95 2.148 3.6-.154.435-.238.905-.238 1.4 0 2.21 1.79 4 4 4 .495 0 .965-.084 1.4-.238 1.05 1.273 2.42 2.148 4 2.148 1.58 0 2.95-.875 3.6-2.148.435.154.905.238 1.4.238 2.21 0 4-1.79 4-4 0-.495-.084-.965-.238-1.4 1.273-1.05 2.148-2.42 2.148-4zM10.2 16.6l-3.8-3.8 1.4-1.4 2.4 2.4 6.4-6.4 1.4 1.4-7.8 7.8z"/></svg></div>
        <div class="handle">@VannaProtocol</div>
      </div>
    </div>
    <div class="x-logo"><svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor"><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/></svg></div>
  </div>

  <div class="tweet-text">{t_a.replace(hl_a, f'<span class="highlight" style="color: #A387FF;">{hl_a}</span>')}</div>

  <div class="media-attachment">
    <img src="data:image/png;base64,{b64_a}" alt="Vanna Composable Credit Pipeline Diagram">
  </div>

  <div class="tweet-stats">
    <span>11:20 AM · Sep 17, 2026</span> · <span><strong>88.4K</strong> Views</span>
  </div>

  <div class="actions-row">
    <div class="action-btn"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"/></svg> 340</div>
    <div class="action-btn"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 1l4 4-4 4"/><path d="M3 11V9a4 4 0 0 1 4-4h14"/><path d="M7 23l-4-4 4-4"/><path d="M21 13v2a4 4 0 0 1-4 4H3"/></svg> 1.2K</div>
    <div class="action-btn"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/></svg> 5.4K</div>
    <div class="action-btn"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"/></svg> 610</div>
  </div>
</div>

<!-- POST 09 -->
<div class="tweet-card">
  <div class="post-tag" style="color: #22D3C4;">POST #09 // SUB-SECOND RISK TELEMETRY</div>
  <div class="tweet-header">
    <div class="author-meta">
      <div class="avatar">{monogram_svg}</div>
      <div class="names">
        <div class="display-name">Vanna <svg class="verified-badge" viewBox="0 0 24 24" fill="#22D3C4"><path d="M22.5 12.5c0-1.58-.875-2.95-2.148-3.6.154-.435.238-.905.238-1.4 0-2.21-1.79-4-4-4-.495 0-.965.084-1.4.238C14.55 2.475 13.18 1.6 11.6 1.6c-1.58 0-2.95.875-3.6 2.148-.435-.154-.905-.238-1.4-.238-2.21 0-4 1.79-4 4 0 .495.084.965.238 1.4C1.475 10.55.6 11.92.6 13.5c0 1.58.875 2.95 2.148 3.6-.154.435-.238.905-.238 1.4 0 2.21 1.79 4 4 4 .495 0 .965-.084 1.4-.238 1.05 1.273 2.42 2.148 4 2.148 1.58 0 2.95-.875 3.6-2.148.435.154.905.238 1.4.238 2.21 0 4-1.79 4-4 0-.495-.084-.965-.238-1.4 1.273-1.05 2.148-2.42 2.148-4zM10.2 16.6l-3.8-3.8 1.4-1.4 2.4 2.4 6.4-6.4 1.4 1.4-7.8 7.8z"/></svg></div>
        <div class="handle">@VannaProtocol</div>
      </div>
    </div>
    <div class="x-logo"><svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor"><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/></svg></div>
  </div>

  <div class="tweet-text">{t_b.replace(hl_b, f'<span class="highlight" style="color: #22D3C4;">{hl_b}</span>')}</div>

  <div class="media-attachment">
    <img src="data:image/png;base64,{b64_b}" alt="Vanna Sub-Second Telemetry & Solvency Rail Schematic">
  </div>

  <div class="tweet-stats">
    <span>2:30 PM · Sep 17, 2026</span> · <span><strong>96.1K</strong> Views</span>
  </div>

  <div class="actions-row">
    <div class="action-btn"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"/></svg> 412</div>
    <div class="action-btn"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 1l4 4-4 4"/><path d="M3 11V9a4 4 0 0 1 4-4h14"/><path d="M7 23l-4-4 4-4"/><path d="M21 13v2a4 4 0 0 1-4 4H3"/></svg> 1.5K</div>
    <div class="action-btn"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/></svg> 6.8K</div>
    <div class="action-btn"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"/></svg> 890</div>
  </div>
</div>

</body>
</html>"""

out_showcase = STATE_DIR / "vanna_exact_style_preview.html"
out_showcase.write_text(showcase_html, encoding="utf-8")
print(f"✅ Wrote Master Showcase: {out_showcase.name} ({out_showcase.stat().st_size:,} bytes)")
