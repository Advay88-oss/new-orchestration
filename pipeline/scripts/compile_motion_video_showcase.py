#!/usr/bin/env python3
"""Compiles the comprehensive Motion Graphics Showcase:
OLD VIDEO ANALYSIS -> REDESIGN PLAN -> NEW VIDEO RENDER -> CRITIC COMPARISON
"""

from __future__ import annotations

import base64
import json
from pathlib import Path

REPO_ROOT = Path("D:/new orchestration")
STATE_DIR = REPO_ROOT / "pipeline" / "state"

critic_file = STATE_DIR / "vanna_motion_critic_evaluation.json"
plan_file = STATE_DIR / "vanna_motion_redesign_plan.json"

critic_data = json.loads(critic_file.read_text(encoding="utf-8"))
plan_data = json.loads(plan_file.read_text(encoding="utf-8"))

def get_b64(path: Path) -> str:
    if path.exists():
        return f"data:image/png;base64,{base64.b64encode(path.read_bytes()).decode('utf-8')}"
    return ""

img_s1 = get_b64(STATE_DIR / "frame_s1_capital_drag.png")
img_s2 = get_b64(STATE_DIR / "frame_s2_smartaccount.png")
img_s3 = get_b64(STATE_DIR / "frame_s3_leverage.png")
img_s4 = get_b64(STATE_DIR / "frame_s4_telemetry.png")
img_s5 = get_b64(STATE_DIR / "frame_s5_outro.png")

html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Vanna Motion Graphics Redesign — Studio Product Film</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@500;600;700&display=swap" rel="stylesheet">
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    background: #05020A;
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
    max-width: 1120px;
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
    color: #32EEE2;
    background: rgba(50, 238, 226, 0.12);
    border: 1px solid rgba(50, 238, 226, 0.35);
    padding: 4px 10px;
    border-radius: 4px;
    letter-spacing: 0.08em;
    display: inline-block;
    margin-bottom: 12px;
  }}
  h1 {{ font-size: 32px; font-weight: 800; color: #FFF; margin-bottom: 8px; letter-spacing: -0.02em; }}
  .subtitle {{ font-size: 15px; color: #A2A1A6; line-height: 1.6; max-width: 860px; }}

  /* Player Card */
  .player-card {{
    background: #090412;
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
  .player-meta {{ font-family: 'JetBrains Mono', monospace; font-size: 12px; color: #32EEE2; }}
  .video-wrapper {{
    width: 100%;
    border-radius: 14px;
    overflow: hidden;
    background: #000;
    border: 1px solid rgba(255, 255, 255, 0.12);
  }}
  video {{ width: 100%; height: auto; display: block; }}

  /* Comparison Banner */
  .score-banner {{
    background: linear-gradient(135deg, rgba(112, 58, 230, 0.2), rgba(50, 238, 226, 0.15));
    border: 1px solid rgba(50, 238, 226, 0.4);
    border-radius: 16px;
    padding: 24px 32px;
    display: grid;
    grid-template-columns: 1fr 1fr 1fr;
    gap: 20px;
    text-align: center;
  }}
  .score-metric {{ display: flex; flex-direction: column; gap: 4px; }}
  .metric-label {{ font-family: 'JetBrains Mono', monospace; font-size: 12px; color: #A2A1A6; text-transform: uppercase; }}
  .metric-val {{ font-size: 38px; font-weight: 800; color: #FFF; }}

  /* Storyboard Grid */
  .storyboard-grid {{
    display: flex;
    flex-direction: column;
    gap: 24px;
  }}
  .scene-card {{
    background: #0A0514;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 16px;
    overflow: hidden;
    display: grid;
    grid-template-columns: 420px 1fr;
    transition: transform 0.2s, border-color 0.2s;
  }}
  .scene-card:hover {{
    border-color: rgba(50, 238, 226, 0.4);
    transform: translateY(-2px);
  }}
  .scene-media img {{
    width: 100%;
    height: 100%;
    object-fit: cover;
    display: block;
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
    color: #32EEE2;
    margin-bottom: 6px;
  }}
  .scene-heading {{ font-size: 20px; font-weight: 800; color: #FFF; margin-bottom: 10px; }}
  .scene-concept {{ font-size: 14px; color: #E2E1E6; line-height: 1.55; margin-bottom: 12px; }}
  .scene-metaphor {{ font-size: 13px; color: #A2A1A6; line-height: 1.5; }}
  .meta-pill {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
    color: #A387FF;
    background: rgba(163, 135, 255, 0.12);
    border: 1px solid rgba(163, 135, 255, 0.3);
    padding: 4px 10px;
    border-radius: 4px;
    display: inline-block;
    margin-top: 14px;
    width: fit-content;
  }}

  /* Dimension Evaluation Table */
  .table-card {{
    background: #090412;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 18px;
    padding: 28px;
  }}
  table {{
    width: 100%;
    border-collapse: collapse;
    font-size: 13px;
    margin-top: 16px;
  }}
  th, td {{
    padding: 14px 16px;
    text-align: left;
    border-bottom: 1px solid rgba(255, 255, 255, 0.06);
    vertical-align: top;
  }}
  th {{ font-family: 'JetBrains Mono', monospace; color: #A2A1A6; font-size: 12px; font-weight: 700; }}
  .old-val {{ color: #FC5457; font-weight: 700; }}
  .new-val {{ color: #32EEE2; font-weight: 800; }}
</style>
</head>
<body>

<div class="container">
  <div class="header">
    <span class="brand-badge">VANNA MOTION ENGINE // ARCHITECTURAL REDESIGN</span>
    <h1>Studio Product Film: The Architecture of Sovereign Credit</h1>
    <p class="subtitle">Complete overhaul from an animated slide deck into a tier-one motion graphics product film. Zero UI cards, zero container boxes, continuous morphological scene flow, dynamic SVG laser networks, and synchronized 48kHz audio design.</p>
  </div>

  <!-- SCORE BANNER -->
  <div class="score-banner">
    <div class="score-metric">
      <span class="metric-label">Old Video (Slide Deck)</span>
      <span class="metric-val" style="color: #FC5457;">{critic_data['old_video_overall_score']} <span style="font-size: 20px; color: #A2A1A6;">/100</span></span>
    </div>
    <div class="score-metric">
      <span class="metric-label">Redesigned Product Film</span>
      <span class="metric-val" style="color: #32EEE2;">{critic_data['new_video_overall_score']} <span style="font-size: 20px; color: #A2A1A6;">/100</span></span>
    </div>
    <div class="score-metric">
      <span class="metric-label">Verified Uplift</span>
      <span class="metric-val" style="color: #41D99B;">{critic_data['score_improvement']}</span>
    </div>
  </div>

  <!-- PLAYER -->
  <div class="player-card">
    <div class="player-header">
      <div class="player-title">Vanna Composable Credit Architecture (Rendered MP4)</div>
      <div class="player-meta">1920×1080 @ 30fps · 720 Frames · 24.04s · 8.9 MB · 48kHz Stereo SFX</div>
    </div>
    <div class="video-wrapper">
      <video controls autoplay loop muted>
        <source src="vanna_motion_graphics_reference.mp4" type="video/mp4">
        Your browser does not support the video tag.
      </video>
    </div>
  </div>

  <!-- STORYBOARD -->
  <div class="header" style="border-bottom: none; padding-bottom: 0;">
    <span class="brand-badge" style="color: #A387FF; background: rgba(163,135,255,0.12); border-color: rgba(163,135,255,0.35);">5-ARC VISUAL METAPHOR BREAKTHROUGH</span>
    <h2 style="font-size: 24px; font-weight: 800; color: #FFF;">Physical Transformations Replacing UI Cards</h2>
  </div>

  <div class="storyboard-grid">
    <!-- Arc 1 -->
    <div class="scene-card">
      <div class="scene-media"><img src="{img_s1}" alt="Arc 1 Shared Contagion"></div>
      <div class="scene-info">
        <div>
          <div class="scene-tag">ARC 01 // FRAMES 000–135 (4.5s)</div>
          <div class="scene-heading">The Trap of Shared Contagion</div>
          <div class="scene-concept">Replaces static cards with an interconnected credit lattice. A toxic depeg shockwave hits the center node; bright red dashed contagion lines vibrate under physical mechanical strain as typography shakes.</div>
          <div class="scene-metaphor"><strong>Visual Metaphor:</strong> Contagion in pooled lending physically warping a shared network.</div>
        </div>
        <div class="meta-pill">CONTINUITY: MACRO PLUNGE INTO DISTRESSED JOINT</div>
      </div>
    </div>

    <!-- Arc 2 -->
    <div class="scene-card">
      <div class="scene-media"><img src="{img_s2}" alt="Arc 2 Autonomous Isolation"></div>
      <div class="scene-info">
        <div>
          <div class="scene-tag">ARC 02 // FRAMES 125–285 (5.0s)</div>
          <div class="scene-heading">Autonomous Laser Incision & Quarantine</div>
          <div class="scene-concept">Two neon coral laser slashes sever the distressed connections. An obsidian hexagonal quarantine barrier snaps shut around 0xLOCK, and the surrounding nodes instantly re-stabilize into calm cyan/violet equilibrium.</div>
          <div class="scene-metaphor"><strong>Visual Metaphor:</strong> SmartAccount sandbox containing bad debt with zero pool contagion.</div>
        </div>
        <div class="meta-pill">CONTINUITY: QUARANTINE CORE TRANSFORMS TO APERTURE</div>
      </div>
    </div>

    <!-- Arc 3 -->
    <div class="scene-card">
      <div class="scene-media"><img src="{img_s3}" alt="Arc 3 Capital Multiplexer"></div>
      <div class="scene-info">
        <div>
          <div class="scene-tag">ARC 03 // FRAMES 275–435 (5.0s)</div>
          <div class="scene-heading">Kinetic Multiplication (10× Leverage)</div>
          <div class="scene-concept">A single 1x origin node erupts into 10 smooth, fiber-like curved laser waveforms with traveling white photon pulse packets. A massive typographic 10× scales forward dynamically in 3D Z-space.</div>
          <div class="scene-metaphor"><strong>Visual Metaphor:</strong> Composable multiplexing amplifying capital efficiency.</div>
        </div>
        <div class="meta-pill">CONTINUITY: 10 STREAMS TIGHTEN INTO HORIZON TRAJECTORY</div>
      </div>
    </div>

    <!-- Arc 4 -->
    <div class="scene-card">
      <div class="scene-media"><img src="{img_s4}" alt="Arc 4 Sub-Second Deflection"></div>
      <div class="scene-info">
        <div>
          <div class="scene-tag">ARC 04 // FRAMES 425–585 (5.0s)</div>
          <div class="scene-heading">Sub-Second Parabolic Deflection</div>
          <div class="scene-concept">Trajectory dives toward the rising crimson 1.10x liquidation floor. At the exact 1.25x trigger line, a ~320ms Mercury telemetry pulse whips the trajectory into an asymptotic parabolic climb into Safe Orbit (1.45x).</div>
          <div class="scene-metaphor"><strong>Visual Metaphor:</strong> Automated keepers rescuing positions before forced liquidation.</div>
        </div>
        <div class="meta-pill">CONTINUITY: ORBITAL CURVE LOOPS INTO MONOGRAM SHAPE</div>
      </div>
    </div>

    <!-- Arc 5 -->
    <div class="scene-card">
      <div class="scene-media"><img src="{img_s5}" alt="Arc 5 Ecosystem Resolution"></div>
      <div class="scene-info">
        <div>
          <div class="scene-tag">ARC 05 // FRAMES 575–720 (4.8s)</div>
          <div class="scene-heading">Ecosystem Crystallization & Call to Action</div>
          <div class="scene-concept">The vector paths fold seamlessly into the geometric Vanna Monogram with dual-point ambient light blooms, flanked by Blend and Aquarius integration anchors and the live testnet URL.</div>
          <div class="scene-metaphor"><strong>Visual Metaphor:</strong> Sovereign credit infrastructure resolving into a complete platform.</div>
        </div>
        <div class="meta-pill">CONTINUITY: FINAL RESONANT 48kHz CHORD HOLD</div>
      </div>
    </div>
  </div>

  <!-- MOTION CRITIC 12-DIMENSION TABLE -->
  <div class="table-card">
    <div class="header" style="border-bottom: none; padding-bottom: 0;">
      <span class="brand-badge">MOTION CRITIC COMPREHENSIVE AUDIT</span>
      <h3 style="font-size: 22px; font-weight: 800; color: #FFF;">12-Dimension Evaluation: Old Video vs. Redesigned Product Film</h3>
    </div>
    <table>
      <thead>
        <tr>
          <th>Dimension</th>
          <th>Old Video (Deck)</th>
          <th>New Video (Film)</th>
          <th>Critical Breakdown</th>
        </tr>
      </thead>
      <tbody>
        { "".join(f'''
        <tr>
          <td><strong>{d["dimension"]}</strong></td>
          <td class="old-val">{d["old_score"]} / 10</td>
          <td class="new-val">{d["new_score"]} / 10</td>
          <td>
            <div style="color: #A2A1A6; margin-bottom: 4px;"><strong>Old Defect:</strong> {d["old_critique"]}</div>
            <div style="color: #F3F1F8;"><strong>New Architectural Solution:</strong> {d["new_breakthrough"]}</div>
          </td>
        </tr>
        ''' for d in critic_data["dimensions"]) }
      </tbody>
    </table>
  </div>
</div>

</body>
</html>"""

out_html = STATE_DIR / "vanna_motion_video_showcase.html"
out_html.write_text(html_content, encoding="utf-8")
print(f"✅ Generated Comprehensive Motion Showcase HTML: {out_html.name} ({out_html.stat().st_size:,} bytes)")
