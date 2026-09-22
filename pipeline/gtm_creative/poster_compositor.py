"""Phase 5.2: Production Poster Compositor Engine (poster_compositor.py).

Implements the critical separation of information design from image generation:
  AI Image Model -> Pure textless, material-rich visual metaphor asset
        ↓
  HTML/CSS Compositor -> Typography + copy hierarchy + layout + data chips + branding + Double-Bezel
        ↓
  Headless Chrome (2x Retina) -> $150k agency-tier product marketing creative
"""

from __future__ import annotations

import base64
import os
import subprocess
from pathlib import Path
from typing import Any, Dict, Optional

from pipeline.gtm_creative.visual_creative_director import CreativeBlueprint

CHROME_CANDIDATES = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
    "google-chrome",
    "chromium",
]

VANNA_MONOGRAM_SVG = """
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


class PosterCompositor:
    """Takes a CreativeBlueprint and a raw textless AI image asset to composite a publication-grade creative."""

    def __init__(self):
        self.chrome_path = self._find_chrome()

    def _find_chrome(self) -> str:
        for p in CHROME_CANDIDATES:
            if os.path.exists(p):
                return p
        raise RuntimeError("Google Chrome not found for headless compositing.")

    def composite_poster(
        self,
        blueprint: CreativeBlueprint,
        visual_asset_path: Path,
        output_png_path: Path
    ) -> Path:
        """Compose HTML/CSS layout with embedded visual asset and render 2x Retina PNG."""
        output_png_path = Path(output_png_path).resolve()
        output_png_path.parent.mkdir(parents=True, exist_ok=True)

        img_b64 = ""
        if visual_asset_path.exists():
            img_b64 = base64.b64encode(visual_asset_path.read_bytes()).decode("utf-8")

        # Compile layout based on archetype
        if blueprint.layout_archetype == "EDITORIAL_SPLIT":
            html_content = self._render_editorial_split(blueprint, img_b64)
        else:
            html_content = self._render_architectural_viewport(blueprint, img_b64)

        tmp_html = output_png_path.parent / f"temp_{output_png_path.stem}.html"
        tmp_html.write_text(html_content, encoding="utf-8")

        # Render with Headless Chrome 2x
        cmd = [
            self.chrome_path,
            "--headless=new",
            "--disable-gpu",
            "--hide-scrollbars",
            "--force-device-scale-factor=2",
            "--window-size=1200,675",
            f"--screenshot={output_png_path}",
            str(tmp_html.resolve())
        ]
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if tmp_html.exists():
            tmp_html.unlink()

        return output_png_path

    def _render_editorial_split(self, bp: CreativeBlueprint, img_b64: str) -> str:
        """Archetype A: Asymmetrical Editorial Split Layout."""
        telemetry_chips = "".join([
            f'<div class="chip"><span class="chip-key">{k}</span> <span class="chip-val">{v}</span></div>'
            for k, v in bp.telemetry_metadata.items()
        ])
        proof_items = "".join([
            f'<div class="proof-row"><span class="proof-bullet"></span><span>{p}</span></div>'
            for p in bp.proof_points[:3]
        ])

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
    background-color: {bp.color_palette['bg_void']};
    background-image:
      radial-gradient(ellipse 65% 55% at 95% 15%, rgba(94, 13, 70, 0.45) 0%, rgba(7, 2, 13, 0) 75%),
      radial-gradient(ellipse 70% 60% at 5% 90%, rgba(71, 20, 133, 0.55) 0%, rgba(7, 2, 13, 0) 80%);
    color: #FFFFFF;
    font-family: 'Plus Jakarta Sans', sans-serif;
    position: relative;
    padding: 32px 40px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
  }}
  .film-grain {{
    position: absolute;
    top: 0; left: 0; width: 100%; height: 100%;
    opacity: {bp.film_grain_opacity};
    pointer-events: none;
    background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noiseFilter'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.8' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noiseFilter)'/%3E%3C/svg%3E");
    z-index: 1;
  }}
  .top-bar {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    z-index: 2;
  }}
  .eyebrow-badge {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
    font-weight: 700;
    color: {bp.color_palette['accent_violet']};
    background: rgba(163, 135, 255, 0.1);
    border: 1px solid rgba(163, 135, 255, 0.25);
    padding: 5px 12px;
    border-radius: 999px;
    letter-spacing: 0.1em;
    text-transform: uppercase;
  }}
  .monogram-svg {{ width: 26px; height: 26px; opacity: 0.6; }}
  
  .stage-grid {{
    display: grid;
    grid-template-columns: 1.15fr 1fr;
    gap: 36px;
    align-items: center;
    z-index: 2;
    height: 480px;
  }}
  .info-col {{
    display: flex;
    flex-direction: column;
    justify-content: center;
    gap: 16px;
    padding-right: 12px;
  }}
  h1 {{
    font-size: 34px;
    font-weight: 800;
    line-height: 1.2;
    letter-spacing: -0.02em;
    color: #FFFFFF;
  }}
  .supporting-copy {{
    font-size: 14px;
    line-height: 1.6;
    color: #A2A1A8;
    max-width: 520px;
  }}
  .proof-stack {{
    display: flex;
    flex-direction: column;
    gap: 8px;
    margin-top: 4px;
  }}
  .proof-row {{
    display: flex;
    align-items: center;
    gap: 10px;
    font-size: 13px;
    color: #E2E1E6;
  }}
  .proof-bullet {{
    width: 5px;
    height: 5px;
    border-radius: 50%;
    background: {bp.color_palette['accent_cyan']};
    box-shadow: 0 0 8px {bp.color_palette['accent_cyan']};
  }}
  
  /* Double-Bezel Hardware Frame for Visual Asset */
  .double-bezel-outer {{
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 20px;
    padding: 6px;
    box-shadow: 0 20px 50px rgba(0, 0, 0, 0.7);
    height: 100%;
    display: flex;
  }}
  .double-bezel-inner {{
    background: #000000;
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-radius: 14px;
    overflow: hidden;
    width: 100%;
    height: 100%;
    position: relative;
    display: flex;
    align-items: center;
    justify-content: center;
  }}
  .double-bezel-inner img {{
    width: 100%;
    height: 100%;
    object-fit: cover;
    display: block;
  }}

  .footer-bar {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
    color: #716D80;
    border-top: 1px solid rgba(255, 255, 255, 0.06);
    padding-top: 12px;
    z-index: 2;
  }}
  .chips-container {{
    display: flex;
    gap: 10px;
  }}
  .chip {{
    background: rgba(255, 255, 255, 0.04);
    border: 1px solid rgba(255, 255, 255, 0.07);
    padding: 3px 8px;
    border-radius: 4px;
  }}
  .chip-key {{ color: #8A8598; }}
  .chip-val {{ color: #D1CFDA; font-weight: 600; }}
  .cta-link {{ color: {bp.color_palette['accent_violet']}; font-weight: 600; }}
</style>
</head>
<body>
  <div class="film-grain"></div>
  <div class="top-bar">
    <span class="eyebrow-badge">{bp.eyebrow}</span>
    {VANNA_MONOGRAM_SVG}
  </div>

  <div class="stage-grid">
    <div class="info-col">
      <h1>{bp.headline}</h1>
      <p class="supporting-copy">{bp.supporting_copy}</p>
      <div class="proof-stack">
        {proof_items}
      </div>
    </div>
    <div class="double-bezel-outer">
      <div class="double-bezel-inner">
        <img src="data:image/png;base64,{img_b64}" alt="Visual Metaphor">
      </div>
    </div>
  </div>

  <div class="footer-bar">
    <div class="chips-container">
      {telemetry_chips}
    </div>
    <span class="cta-link">{bp.call_to_action}</span>
  </div>
</body>
</html>"""

    def _render_architectural_viewport(self, bp: CreativeBlueprint, img_b64: str) -> str:
        """Archetype B: Architectural Viewport Layout with Hero Card Enclosure."""
        telemetry_chips = "".join([
            f'<div class="chip"><span class="chip-key">{k}</span> <span class="chip-val">{v}</span></div>'
            for k, v in bp.telemetry_metadata.items()
        ])

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
    background-color: {bp.color_palette['bg_void']};
    background-image:
      radial-gradient(ellipse 65% 55% at 95% 15%, rgba(94, 13, 70, 0.45) 0%, rgba(7, 2, 13, 0) 75%),
      radial-gradient(ellipse 70% 60% at 5% 90%, rgba(71, 20, 133, 0.55) 0%, rgba(7, 2, 13, 0) 80%);
    color: #FFFFFF;
    font-family: 'Plus Jakarta Sans', sans-serif;
    position: relative;
    padding: 32px 40px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
  }}
  .film-grain {{
    position: absolute;
    top: 0; left: 0; width: 100%; height: 100%;
    opacity: {bp.film_grain_opacity};
    pointer-events: none;
    background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noiseFilter'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.8' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noiseFilter)'/%3E%3C/svg%3E");
    z-index: 1;
  }}
  .top-bar {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    z-index: 2;
  }}
  .eyebrow-badge {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
    font-weight: 700;
    color: {bp.color_palette['accent_cyan']};
    background: rgba(34, 211, 196, 0.1);
    border: 1px solid rgba(34, 211, 196, 0.25);
    padding: 5px 12px;
    border-radius: 999px;
    letter-spacing: 0.1em;
    text-transform: uppercase;
  }}
  .monogram-svg {{ width: 26px; height: 26px; opacity: 0.6; }}

  /* Central Floating Hardware Stage */
  .viewport-stage {{
    position: relative;
    width: 100%;
    height: 480px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    z-index: 2;
    gap: 36px;
  }}
  .hero-text-block {{
    flex: 1.1;
    display: flex;
    flex-direction: column;
    gap: 14px;
  }}
  h1 {{
    font-size: 34px;
    font-weight: 800;
    line-height: 1.22;
    letter-spacing: -0.02em;
    color: #FFFFFF;
  }}
  .body-lead {{
    font-size: 14px;
    line-height: 1.6;
    color: #A2A1A8;
  }}
  .solvency-spec-card {{
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 12px;
    padding: 16px 20px;
    display: flex;
    gap: 24px;
    align-items: center;
    margin-top: 8px;
  }}
  .metric-slot {{ display: flex; flex-direction: column; }}
  .metric-label {{ font-family: 'JetBrains Mono', monospace; font-size: 10px; color: #7F7B8F; text-transform: uppercase; }}
  .metric-val {{ font-family: 'JetBrains Mono', monospace; font-size: 20px; font-weight: 700; color: #FFFFFF; }}
  .metric-val.cyan {{ color: {bp.color_palette['accent_cyan']}; }}
  .metric-val.coral {{ color: {bp.color_palette['accent_coral']}; }}

  /* Right Viewport Window */
  .image-window-outer {{
    flex: 1;
    height: 100%;
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 20px;
    padding: 6px;
    box-shadow: 0 20px 50px rgba(0, 0, 0, 0.7);
    display: flex;
  }}
  .image-window-inner {{
    width: 100%;
    height: 100%;
    border-radius: 14px;
    overflow: hidden;
    background: #000;
    border: 1px solid rgba(255, 255, 255, 0.06);
  }}
  .image-window-inner img {{
    width: 100%;
    height: 100%;
    object-fit: cover;
    display: block;
  }}

  .footer-bar {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
    color: #716D80;
    border-top: 1px solid rgba(255, 255, 255, 0.06);
    padding-top: 12px;
    z-index: 2;
  }}
  .chips-container {{ display: flex; gap: 10px; }}
  .chip {{
    background: rgba(255, 255, 255, 0.04);
    border: 1px solid rgba(255, 255, 255, 0.07);
    padding: 3px 8px;
    border-radius: 4px;
  }}
  .chip-key {{ color: #8A8598; }}
  .chip-val {{ color: #D1CFDA; font-weight: 600; }}
  .cta-link {{ color: {bp.color_palette['accent_cyan']}; font-weight: 600; }}
</style>
</head>
<body>
  <div class="film-grain"></div>
  <div class="top-bar">
    <span class="eyebrow-badge">{bp.eyebrow}</span>
    {VANNA_MONOGRAM_SVG}
  </div>

  <div class="viewport-stage">
    <div class="hero-text-block">
      <h1>{bp.headline}</h1>
      <p class="body-lead">{bp.supporting_copy}</p>
      <div class="solvency-spec-card">
        <div class="metric-slot">
          <span class="metric-label">Proactive Check</span>
          <span class="metric-val cyan">1.25x HF</span>
        </div>
        <div style="width: 1px; height: 32px; background: rgba(255,255,255,0.08);"></div>
        <div class="metric-slot">
          <span class="metric-label">Protocol Floor</span>
          <span class="metric-val coral">1.10x HF</span>
        </div>
        <div style="width: 1px; height: 32px; background: rgba(255,255,255,0.08);"></div>
        <div class="metric-slot">
          <span class="metric-label">Execution Gas</span>
          <span class="metric-val">0.00014 XLM</span>
        </div>
      </div>
    </div>
    <div class="image-window-outer">
      <div class="image-window-inner">
        <img src="data:image/png;base64,{img_b64}" alt="Sub-Second Telemetry Deflection">
      </div>
    </div>
  </div>

  <div class="footer-bar">
    <div class="chips-container">
      {telemetry_chips}
    </div>
    <span class="cta-link">{bp.call_to_action}</span>
  </div>
</body>
</html>"""
