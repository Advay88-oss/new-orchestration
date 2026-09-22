#!/usr/bin/env python3
"""Vanna Pure Visual Engine — Zero-Text Visual Metaphors.

Translates the post's core technical thesis into pure geometry, topology, and light:
1. risk_threshold: Mathematical threshold dividing volatile space from calm solvent space.
2. isolated_sandboxes: 3D floating isometric crystalline vaults compartmentalizing capital.
3. composability_network: Topological routing graph with branching liquidity vectors.

Zero typography. Zero labels. Zero digits. Pure visual artifact.
"""

from __future__ import annotations

import argparse
import html
import json
import math
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

CHROME_CANDIDATES = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    "google-chrome",
    "chromium",
]

def find_chrome() -> str:
    for candidate in CHROME_CANDIDATES:
        if Path(candidate).exists():
            return candidate
        found = shutil.which(candidate)
        if found:
            return found
    sys.exit("Chrome not found. Install Chrome or set a path in CHROME_CANDIDATES.")


def build_pure_visual_html(metaphor: str = "risk_threshold", w: int = 1080, h: int = 1080) -> str:
    """Builds completely text-free visual metaphor in high-contrast SVG and CSS."""
    cx, cy = w // 2, h // 2

    svg_elements = []

    if metaphor == "risk_threshold":
        # Mathematical threshold dividing high-entropy/danger space from protected solvent space.
        # Concentric contour curves with a glowing 1.10x protective boundary ridge.
        base_y = int(h * 0.58)
        
        # 1. Background isometric terrain / grid
        for i in range(-200, w + 400, 40):
            svg_elements.append(f'<line x1="{i}" y1="0" x2="{i+300}" y2="{h}" stroke="rgba(255, 255, 255, 0.03)" stroke-width="1" />')
            svg_elements.append(f'<line x1="{i+300}" y1="0" x2="{i}" y2="{h}" stroke="rgba(255, 255, 255, 0.03)" stroke-width="1" />')

        # 2. Mathematical risk curves (hyperbolic decay lines approaching threshold)
        for offset in range(-6, 7):
            d_parts = []
            for step in range(0, w + 20, 20):
                # Sigmoid / barrier curve formula
                x = step
                norm_x = (x - cx) / 180
                # Steep drop on left (volatility), flat asymptote on right (solvency)
                y = base_y + int(120 / (1 + math.exp(-norm_x))) + (offset * 14)
                d_parts.append(f"{'M' if step == 0 else 'L'} {x} {y}")
            
            is_threshold = (offset == 0)
            if is_threshold:
                # The Glowing Threshold Line
                svg_elements.append(f'<path d="{" ".join(d_parts)}" fill="none" stroke="#a387ff" stroke-width="2.5" filter="url(#glow)" />')
                svg_elements.append(f'<path d="{" ".join(d_parts)}" fill="none" stroke="#ffffff" stroke-width="1" />')
            else:
                alpha = max(0.04, 0.22 - abs(offset) * 0.03)
                stroke_col = f"rgba(163, 135, 255, {alpha})" if offset > 0 else f"rgba(255, 255, 255, {alpha})"
                svg_elements.append(f'<path d="{" ".join(d_parts)}" fill="none" stroke="{stroke_col}" stroke-width="1" stroke-dasharray="{"3 5" if offset % 2 == 0 else "none"}" />')

        # 3. Protective vertical sentinel markers (the 10% barrier)
        tx = cx + 60
        svg_elements.append(f'<line x1="{tx}" y1="180" x2="{tx}" y2="{h-180}" stroke="#a387ff" stroke-width="1.5" stroke-dasharray="4 8" />')
        svg_elements.append(f'<circle cx="{tx}" cy="{base_y+60}" r="6" fill="#a387ff" filter="url(#glow)" />')
        svg_elements.append(f'<circle cx="{tx}" cy="{base_y+60}" r="2" fill="#ffffff" />')

    elif metaphor == "isolated_sandboxes":
        # 3D floating isometric crystalline vaults compartmentalized in space.
        # Central user SmartAccounts isolated from each other.
        def draw_isometric_cube(x, y, size, active=False):
            dx = int(size * 0.866)
            dy = int(size * 0.5)
            h_cube = int(size * 1.1)

            p_top = f"{x},{y-h_cube-dy} {x+dx},{y-h_cube} {x},{y-h_cube+dy} {x-dx},{y-h_cube}"
            p_left = f"{x-dx},{y-h_cube} {x},{y-h_cube+dy} {x},{y+dy} {x-dx},{y}"
            p_right = f"{x},{y-h_cube+dy} {x+dx},{y-h_cube} {x+dx},{y} {x},{y+dy}"

            stroke = "#a387ff" if active else "rgba(255, 255, 255, 0.2)"
            fill_top = "rgba(163, 135, 255, 0.12)" if active else "rgba(255, 255, 255, 0.02)"
            fill_side = "rgba(163, 135, 255, 0.06)" if active else "rgba(255, 255, 255, 0.01)"

            return (
                f'<polygon points="{p_top}" fill="{fill_top}" stroke="{stroke}" stroke-width="1.2" />'
                f'<polygon points="{p_left}" fill="{fill_side}" stroke="{stroke}" stroke-width="1.2" />'
                f'<polygon points="{p_right}" fill="{fill_side}" stroke="{stroke}" stroke-width="1.2" />'
            )

        # Baseline perspective plane
        svg_elements.append(f'<polygon points="180,{cy+220} {cx},{cy+100} {w-180},{cy+220} {cx},{cy+340}" fill="none" stroke="rgba(255,255,255,0.08)" stroke-width="1" stroke-dasharray="4 6" />')
        
        # Floating isolated cubes (sandboxes)
        svg_elements.append(draw_isometric_cube(cx, cy - 20, 110, active=True))
        svg_elements.append(draw_isometric_cube(cx - 240, cy + 80, 75, active=False))
        svg_elements.append(draw_isometric_cube(cx + 240, cy + 80, 75, active=False))
        svg_elements.append(draw_isometric_cube(cx - 160, cy - 160, 65, active=False))
        svg_elements.append(draw_isometric_cube(cx + 160, cy - 160, 65, active=False))

        # Thin non-touching coordinate projection rays
        svg_elements.append(f'<line x1="{cx}" y1="{cy+140}" x2="{cx}" y2="{cy+220}" stroke="#a387ff" stroke-width="1" stroke-dasharray="2 4" />')
        svg_elements.append(f'<circle cx="{cx}" cy="{cy+220}" r="4" fill="#a387ff" filter="url(#glow)" />')

    else:  # composability_network
        # Topological liquidity routing network: branching geometric vectors
        radii = [120, 240, 360, 480]
        for r in radii:
            svg_elements.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="rgba(255, 255, 255, 0.04)" stroke-width="1" />')

        # Star-burst isometric vectors
        nodes = []
        for i in range(12):
            angle = i * (math.pi / 6)
            dist = 220 if i % 2 == 0 else 340
            nx = cx + int(math.cos(angle) * dist)
            ny = cy + int(math.sin(angle) * dist)
            nodes.append((nx, ny))
            
            # Line to center
            stroke = "rgba(163, 135, 255, 0.22)" if i % 3 == 0 else "rgba(255, 255, 255, 0.06)"
            svg_elements.append(f'<line x1="{cx}" y1="{cy}" x2="{nx}" y2="{ny}" stroke="{stroke}" stroke-width="1.2" />')

        # Inter-node cross rails
        for i in range(len(nodes)):
            n1 = nodes[i]
            n2 = nodes[(i + 1) % len(nodes)]
            svg_elements.append(f'<line x1="{n1[0]}" y1="{n1[1]}" x2="{n2[0]}" y2="{n2[1]}" stroke="rgba(255,255,255,0.08)" stroke-width="1" stroke-dasharray="3 5" />')

        # Node points
        for idx, (nx, ny) in enumerate(nodes):
            active = (idx % 3 == 0)
            col = "#a387ff" if active else "#ffffff"
            r_node = 5 if active else 3
            glow_attr = 'filter="url(#glow)"' if active else ""
            if active:
                svg_elements.append(f'<circle cx="{nx}" cy="{ny}" r="{r_node+4}" fill="none" stroke="#a387ff" stroke-width="1" opacity="0.4" />')
            svg_elements.append(f'<circle cx="{nx}" cy="{ny}" r="{r_node}" fill="{col}" {glow_attr} />')

        # Center core origin
        svg_elements.append(f'<circle cx="{cx}" cy="{cy}" r="12" fill="none" stroke="#a387ff" stroke-width="2" filter="url(#glow)" />')
        svg_elements.append(f'<circle cx="{cx}" cy="{cy}" r="4" fill="#ffffff" />')

    svg_content = "\n".join(svg_elements)

    return f"""<!doctype html>
<html>
<head>
<meta charset="utf-8">
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{
  width: {w}px;
  height: {h}px;
  overflow: hidden;
  background: #08070C;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
}}

/* Tactile film grain */
.grain {{
  position: absolute;
  inset: 0;
  opacity: 0.045;
  pointer-events: none;
  z-index: 2;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='3'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E");
}}

.visual-canvas {{
  position: absolute;
  inset: 0;
  width: {w}px;
  height: {h}px;
  z-index: 1;
}}
</style>
</head>
<body>
  <div class="grain"></div>
  <svg class="visual-canvas" viewBox="0 0 {w} {h}" width="{w}" height="{h}" xmlns="http://www.w3.org/2000/svg">
    <defs>
      <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
        <feGaussianBlur stdDeviation="8" result="blur" />
        <feMerge>
          <feMergeNode in="blur" />
          <feMergeNode in="SourceGraphic" />
        </feMerge>
      </filter>
    </defs>
    {svg_content}
  </svg>
</body>
</html>"""


def render_pure_visual(
    metaphor: str = "risk_threshold",
    out_path: Path | str = "pipeline/state/pure_visual.png",
    w: int = 1080,
    h: int = 1080
) -> Path:
    """Renders a 100% textless visual asset inspired by protocol mechanics."""
    out = Path(out_path).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)

    markup = build_pure_visual_html(metaphor=metaphor, w=w, h=h)

    tmp_dir = Path(tempfile.mkdtemp(prefix="vanna-pure-visual-"))
    html_path = tmp_dir / "pure_visual.html"
    html_path.write_text(markup, encoding="utf-8")

    cmd = [
        find_chrome(),
        "--headless=new",
        "--disable-gpu",
        "--hide-scrollbars",
        "--virtual-time-budget=8000",
        f"--window-size={w},{h}",
        f"--screenshot={out}",
        html_path.as_uri(),
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return out


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Render 100% text-free visual metaphors.")
    parser.add_argument("--metaphor", choices=["risk_threshold", "isolated_sandboxes", "composability_network"], default="risk_threshold")
    parser.add_argument("-o", "--out", default="pipeline/state/pure_visual.png")
    parser.add_argument("--width", type=int, default=1080)
    parser.add_argument("--height", type=int, default=1080)
    args = parser.parse_args()

    res = render_pure_visual(metaphor=args.metaphor, out_path=args.out, w=args.width, h=args.height)
    print(f"Rendered textless visual: {res} ({res.stat().st_size} bytes)")
