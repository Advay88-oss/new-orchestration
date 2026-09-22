#!/usr/bin/env python3
"""Compiles the interactive HTML showcase for the 41-second Vanna Master Product Film:
- 41-second Full HD (1920x1080 @ 30fps) MP4 player.
- Follows the complete narrative pattern:
  PROBLEM -> VANNA INTRO -> SOLUTION -> REAL TELEMETRY -> CTA
- Master synchronized voiceover narration + 48kHz electronic sound design.
"""

from __future__ import annotations

import base64
from pathlib import Path

REPO_ROOT = Path("D:/new orchestration")
STATE_DIR = REPO_ROOT / "pipeline" / "state"

def get_b64(path: Path) -> str:
    if path.exists():
        return f"data:image/png;base64,{base64.b64encode(path.read_bytes()).decode('utf-8')}"
    return ""

img_s1 = get_b64(STATE_DIR / "frame_p41_act1_problem.png")
img_s2 = get_b64(STATE_DIR / "frame_p41_act2_intro.png")
img_s3 = get_b64(STATE_DIR / "frame_p41_act3_solution.png")
img_s4 = get_b64(STATE_DIR / "frame_p41_act4_telemetry.png")
img_s5 = get_b64(STATE_DIR / "frame_p41_act5_cta.png")

html_doc = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Vanna Protocol — Master Product Film (41s Full Arc)</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@500;600;700&display=swap" rel="stylesheet">
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    background: #07020D;
    background-image: 
      radial-gradient(circle at 10% 12%, rgba(112, 58, 230, 0.25) 0%, transparent 45%),
      radial-gradient(circle at 90% 88%, rgba(252, 84, 87, 0.2) 0%, transparent 45%);
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
    color: #38EF7D;
    background: rgba(56, 239, 125, 0.12);
    border: 1px solid rgba(56, 239, 125, 0.35);
    padding: 4px 10px;
    border-radius: 4px;
    letter-spacing: 0.08em;
    display: inline-block;
    margin-bottom: 12px;
  }}
  h1 {{ font-size: 32px; font-weight: 800; color: #FFF; margin-bottom: 8px; letter-spacing: -0.02em; }}
  .subtitle {{ font-size: 15px; color: #A2A1A6; line-height: 1.6; max-width: 880px; }}

  /* Player Card */
  .player-card {{
    background: #0A0612;
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 20px;
    padding: 26px;
    box-shadow: 0 30px 80px rgba(0, 0, 0, 0.9);
  }}
  .player-header {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 18px;
  }}
  .player-title {{ font-size: 18px; font-weight: 700; color: #FFF; }}
  .player-meta {{ font-family: 'JetBrains Mono', monospace; font-size: 12px; color: #38EF7D; }}
  .video-wrapper {{
    width: 100%;
    border-radius: 14px;
    overflow: hidden;
    background: #000;
    border: 1px solid rgba(255, 255, 255, 0.12);
  }}
  video {{ width: 100%; height: auto; display: block; }}

  /* 5-Act Pattern Strip */
  .pattern-strip {{
    display: grid;
    grid-template-columns: repeat(5, 1fr);
    gap: 12px;
  }}
  .pattern-box {{
    background: #0D0818;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 12px;
    padding: 16px;
    display: flex;
    flex-direction: column;
    gap: 4px;
  }}
  .pattern-num {{ font-family: 'JetBrains Mono', monospace; font-size: 10px; font-weight: 700; color: #A387FF; text-transform: uppercase; }}
  .pattern-name {{ font-size: 13px; font-weight: 800; color: #FFF; }}
  .pattern-desc {{ font-size: 11px; color: #8E85A8; line-height: 1.4; }}

  /* Storyboard Grid */
  .storyboard-grid {{
    display: flex;
    flex-direction: column;
    gap: 24px;
  }}
  .scene-card {{
    background: #0A0612;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 16px;
    overflow: hidden;
    display: grid;
    grid-template-columns: 460px 1fr;
    transition: transform 0.2s, border-color 0.2s;
  }}
  .scene-card:hover {{
    border-color: rgba(56, 239, 125, 0.4);
    transform: translateY(-2px);
  }}
  .scene-media img {{
    width: 100%;
    height: auto;
    display: block;
    object-fit: cover;
    border-right: 1px solid rgba(255, 255, 255, 0.08);
  }}
  .scene-info {{
    padding: 24px 28px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
  }}
  .scene-tag {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
    font-weight: 700;
    color: #38EF7D;
    margin-bottom: 6px;
  }}
  .scene-heading {{ font-size: 20px; font-weight: 800; color: #FFF; margin-bottom: 8px; }}
  .vo-quote {{
    background: rgba(255, 255, 255, 0.04);
    border-left: 3px solid #703AE6;
    padding: 10px 14px;
    font-size: 13px;
    color: #32EEE2;
    font-style: italic;
    margin-bottom: 10px;
    border-radius: 0 8px 8px 0;
  }}
  .scene-desc {{ font-size: 13px; color: #E2E1E6; line-height: 1.5; margin-bottom: 10px; }}
  .scene-notes {{ font-size: 12px; color: #8E85A8; line-height: 1.4; }}
</style>
</head>
<body>

<div class="container">
  <div class="header">
    <span class="brand-badge">MASTER FILM // COMPLETE 5-ACT NARRATIVE PATTERN</span>
    <h1>Vanna Protocol: 41s Master Product Film</h1>
    <p class="subtitle">Structured strictly around the classic high-converting product film pattern: Problem → Vanna Intro → Solution → Real Telemetry → CTA. Featuring the 3D rotating Veo 3.1 coin, streamlined Remotion spring physics, clean Vanna background, and synchronized voiceover.</p>
  </div>

  <!-- VIDEO PLAYER -->
  <div class="player-card">
    <div class="player-header">
      <div class="player-title">Vanna Master Product Film (Rendered MP4)</div>
      <div class="player-meta">1920×1080 @ 30fps · 1,230 Frames · 41.00s · 8.7 MB · Master Audio with Voiceover</div>
    </div>
    <div class="video-wrapper">
      <video controls autoplay loop muted>
        <source src="vanna_product_film_41s.mp4" type="video/mp4">
        Your browser does not support the video tag.
      </video>
    </div>
  </div>

  <!-- 5-ACT PATTERN STRIP -->
  <div class="pattern-strip">
    <div class="pattern-box">
      <span class="pattern-num">ACT 01 // 0.0s – 8.0s</span>
      <span class="pattern-name">THE PROBLEM</span>
      <span class="pattern-desc">Trapped capital in silos & pooled contagion risk.</span>
    </div>
    <div class="pattern-box">
      <span class="pattern-num">ACT 02 // 8.0s – 16.0s</span>
      <span class="pattern-name">VANNA INTRO</span>
      <span class="pattern-desc">3D rotating coin & Stellar Soroban lockup.</span>
    </div>
    <div class="pattern-box">
      <span class="pattern-num">ACT 03 // 16.0s – 25.0s</span>
      <span class="pattern-name">THE SOLUTION</span>
      <span class="pattern-desc">SmartAccounts & 10× margin pipeline.</span>
    </div>
    <div class="pattern-box">
      <span class="pattern-num">ACT 04 // 25.0s – 33.5s</span>
      <span class="pattern-name">REAL TELEMETRY</span>
      <span class="pattern-desc">Sub-second Mercury HUD with 1.45× HF.</span>
    </div>
    <div class="pattern-box">
      <span class="pattern-num">ACT 05 // 33.5s – 41.0s</span>
      <span class="pattern-name">RESOLUTION / CTA</span>
      <span class="pattern-desc">The future of DeFi & testnet URL resolve.</span>
    </div>
  </div>

  <!-- 5-ACT STORYBOARD -->
  <div class="header" style="border-bottom: none; padding-bottom: 0;">
    <h2 style="font-size: 24px; font-weight: 800; color: #FFF;">5-Act Narrative Storyboard (Computer Vision Verified)</h2>
  </div>

  <div class="storyboard-grid">
    <!-- Act 1 -->
    <div class="scene-card">
      <div class="scene-media"><img src="{img_s1}" alt="Act 1 Problem"></div>
      <div class="scene-info">
        <div>
          <div class="scene-tag">ACT 01 // 00:00–00:08.0 (FRAMES 000–240)</div>
          <div class="scene-heading">Capital is Trapped. Pooled Risk Threatens Everyone.</div>
          <div class="vo-quote">"In traditional DeFi, capital is trapped in isolated silos, and pooled risk threatens everyone."</div>
          <div class="scene-desc">Frames the core architectural flaw of legacy money markets: 150% capital drag, pooled shared contagion, and fragmented credit walls.</div>
          <div class="scene-notes"><strong>Transition:</strong> Camera pushes into the center as sub-bass impact triggers the brand reveal.</div>
        </div>
      </div>
    </div>

    <!-- Act 2 -->
    <div class="scene-card">
      <div class="scene-media"><img src="{img_s2}" alt="Act 2 Vanna Intro"></div>
      <div class="scene-info">
        <div>
          <div class="scene-tag">ACT 02 // 00:08.0–00:16.0 (FRAMES 240–480)</div>
          <div class="scene-heading">Introducing Vanna Protocol on Stellar Soroban</div>
          <div class="vo-quote">"Introducing Vanna: the decentralized composable credit infrastructure on Stellar Soroban."</div>
          <div class="scene-desc">Symmetrical partnership lockup: Stellar Soroban on the left, photorealistic 3D rotating physical copper/rose-gold Vanna 10X coin (Veo 3.1) in the center, and Vanna Protocol on the right.</div>
          <div class="scene-notes"><strong>Transition:</strong> 3D coin scales smoothly into the center of the 1-click margin engine.</div>
        </div>
      </div>
    </div>

    <!-- Act 3 -->
    <div class="scene-card">
      <div class="scene-media"><img src="{img_s3}" alt="Act 3 Solution"></div>
      <div class="scene-info">
        <div>
          <div class="scene-tag">ACT 03 // 00:16.0–00:25.0 (FRAMES 480–750)</div>
          <div class="scene-heading">Dedicated SmartAccounts. 10× Composable Leverage.</div>
          <div class="vo-quote">"Vanna isolates credit inside dedicated SmartAccounts, unlocking up to 10x composable leverage."</div>
          <div class="scene-desc">3-step process pipeline: Deposit Collateral (1,000 XLM) → 10× Credit Engine ($9,000 Borrowed Credit) → Deploy Anywhere ($10,000 USDC across Blend & Aquarius).</div>
          <div class="scene-notes"><strong>Transition:</strong> Camera dollies right into the live product risk telemetry console.</div>
        </div>
      </div>
    </div>

    <!-- Act 4 -->
    <div class="scene-card">
      <div class="scene-media"><img src="{img_s4}" alt="Act 4 Telemetry HUD"></div>
      <div class="scene-info">
        <div>
          <div class="scene-tag">ACT 04 // 00:25.0–00:33.5 (FRAMES 750–1005)</div>
          <div class="scene-heading">Sub-Second Telemetry & Solvency Defense</div>
          <div class="vo-quote">"Sub-second Mercury telemetry streams ledger state in roughly 320 milliseconds, protecting positions before liquidation can ever occur."</div>
          <div class="scene-desc">Floating dark-glass HUD card with NET HEALTH FACTOR (1.45× HF) in glowing mint green, ~320ms Mercury Telemetry, and the horizontal slider with the 1.00× floor and 1.20× threshold marker.</div>
          <div class="scene-notes"><strong>Audio:</strong> Synchronized ~320ms digital telemetry radar pings.</div>
        </div>
      </div>
    </div>

    <!-- Act 5 -->
    <div class="scene-card">
      <div class="scene-media"><img src="{img_s5}" alt="Act 5 Outro"></div>
      <div class="scene-info">
        <div>
          <div class="scene-tag">ACT 05 // 00:33.5–00:41.0 (FRAMES 1005–1230)</div>
          <div class="scene-heading">The Future of DeFi is Composable</div>
          <div class="vo-quote">"The future of DeFi is composable. Experience sovereign credit today at test.stellar.vanna.finance."</div>
          <div class="scene-desc">3D glowing geometric ribbon logo with ambient volumetric halo, headline from vanna.finance, glowing testnet capsule button (test.stellar.vanna.finance), and ecosystem footer.</div>
          <div class="scene-notes"><strong>Audio Resolve:</strong> Full 48kHz resonant electronic chord resolve.</div>
        </div>
      </div>
    </div>
  </div>
</div>

</body>
</html>"""

out_html = STATE_DIR / "vanna_product_film_41s_showcase.html"
out_html.write_text(html_doc, encoding="utf-8")
print(f"✅ Generated 41s Product Film Showcase HTML: {out_html.name} ({out_html.stat().st_size:,} bytes)")
