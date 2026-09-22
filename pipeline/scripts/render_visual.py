#!/usr/bin/env python3
"""Vanna Visual Engine v2 — With Brand Device & Material Depth.

Deterministic, geometric brand device generated entirely in SVG code:
1. Proprietary device: Hairline isometric geometry derived from Vanna's logo mark.
   - dense: statement/thesis cards (surrounds center well)
   - cropped: single_stat cards (radiates along edges, center void)
   - structural: architecture cards (serves as the perspective pipeline grid)
2. Material: subtle fractal noise film grain overlay.
3. Gradient rule refined: Coral->Violet gradient allowed in brand-mark; zero gradient on text.
4. Support for both Lavender accent (#A387FF) and Pure Monochrome (text-shadow glow).
5. Aspect ratio support: 1080x1080 (square) and 1500x500 (wide banner).
"""

from __future__ import annotations

import argparse
import html
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, Optional

# Import art director
sys.path.insert(0, str(Path(__file__).resolve().parent))
from art_director import compile_art_direction, ARCHETYPE_RULES

CHROME_CANDIDATES = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    "google-chrome",
    "chromium",
]

# Locked Design Tokens
TOKENS = {
    "bg_void": "#07020D",
    "text_hero": "#FFFFFF",
    "text_body": "rgba(255, 255, 255, 0.75)",
    "text_muted": "rgba(255, 255, 255, 0.55)",
    "text_dim": "rgba(255, 255, 255, 0.35)",
    "accent": "#a387ff",           # Vanna Lavender
    "border_hairline": "rgba(255, 255, 255, 0.08)",
}

LAYOUT = {
    "canvas": 1080,
    "margin": 120,
    "content_max_height": 400,     # 680px stays empty. Strict whitespace rule.
    "hero_size": 180,
    "headline_size": 52,
    "support_size": 28,
    "accent_colors_max": 1,
    "text_colors": ["#FFFFFF", "rgba(255, 255, 255, 0.55)"],
    "background": "#07020D",
    "logo": {"size": 32},
}

TEMPLATE_MAP = {
    "TRUST_RISK": "data_visualization",
    "METRICS_PROOF": "data_visualization",
    "EDUCATION": "technical_architecture",
    "PRODUCT": "technical_architecture",
    "NARRATIVE_THESIS": "editorial_manifesto",
    "ECOSYSTEM": "editorial_manifesto",
}

_TEMPLATE_ALIAS = {
    "single_stat": "data_visualization",
    "architecture": "technical_architecture",
    "statement": "editorial_manifesto",
}

TEXT_KEYS = ("headline", "subhead", "support", "footer", "hero", "tag", "source")

ACCENT_HEXES = {
    "#703ae6", "#5a3ecc", "#a387ff", "#c4b0f6",
    "#fc5457", "#22d3c4", "#10b981", "#f59e0b", "#ef4444",
}

OFFICIAL_SVG_PATH = Path(__file__).resolve().parents[1] / "state" / "vanna_logo_official.svg"


def find_chrome() -> str:
    for candidate in CHROME_CANDIDATES:
        if Path(candidate).exists():
            return candidate
        found = shutil.which(candidate)
        if found:
            return found
    sys.exit("Chrome not found. Install Chrome or set a path in CHROME_CANDIDATES.")


def _escape(text: Any) -> str:
    return html.escape(str(text or ""))


def generate_brand_device_svg(intensity: str = "dense", w: int = 1080, h: int = 1080, monochrome: bool = False) -> str:
    """Generates the proprietary hairline isometric interlocking geometry.
    Zero external assets, zero model calls, deterministic.
    """
    stroke_col = "rgba(255, 255, 255, 0.22)" if monochrome else "rgba(163, 135, 255, 0.26)"
    faint_col = "rgba(255, 255, 255, 0.08)"
    paths = []

    if intensity == "dense":
        # Concentric nested isometric chevrons and diamonds radiating from center,
        # with an empty center-well for clear text readability.
        cx, cy = w // 2, h // 2
        for r in range(160, max(w, h), 48):
            dx = int(r * 1.35)
            dy = int(r * 0.78)
            paths.append(
                f'<polygon points="{cx},{cy-dy} {cx+dx},{cy} {cx},{cy+dy} {cx-dx},{cy}" '
                f'fill="none" stroke="{stroke_col}" stroke-width="1.2" stroke-dasharray="3 6" />'
            )
            paths.append(f'<line x1="{cx-dx}" y1="{cy}" x2="{cx-dx}" y2="{cy+140}" stroke="{faint_col}" stroke-width="1.2" />')
            paths.append(f'<line x1="{cx+dx}" y1="{cy}" x2="{cx+dx}" y2="{cy+140}" stroke="{faint_col}" stroke-width="1.2" />')

        # Radiating perspective isometric rays
        step = 160 if w > 1200 else 110
        for offset in range(-400, w + 600, step):
            paths.append(f'<line x1="{offset}" y1="0" x2="{offset+450}" y2="{h}" stroke="{faint_col}" stroke-width="0.8" />')
            paths.append(f'<line x1="{offset+450}" y1="0" x2="{offset}" y2="{h}" stroke="{faint_col}" stroke-width="0.8" />')

    elif intensity == "cropped":
        # Edge-anchored isometric chevrons: top-right and bottom-right edges only,
        # leaving 80%+ center canvas entirely void.
        for i, r in enumerate(range(80, 750, 48)):
            opacity = max(0.02, 0.16 - (i * 0.012))
            col = f"rgba(255, 255, 255, {opacity})" if monochrome else f"rgba(163, 135, 255, {opacity})"
            # Top-right radiating isometric chevrons
            paths.append(f'<path d="M {w-int(r*1.4)} 0 L {w} {int(r*0.8)} L {w} {int(r*0.8)+70}" fill="none" stroke="{col}" stroke-width="1.2" />')
            # Bottom-right interlocking chevrons
            paths.append(f'<path d="M {w} {h-int(r*0.8)} L {w-int(r*1.2)} {h} L {w-int(r*1.2)-90} {h}" fill="none" stroke="{col}" stroke-width="1.2" />')
        # Left subtle baseline coordinates
        paths.append(f'<line x1="{w//9}" y1="{h//5}" x2="{w//9}" y2="{h*4//5}" stroke="{faint_col}" stroke-width="1.2" stroke-dasharray="2 8" />')

    elif intensity == "structural":
        # Isometric diagrammatic foundation: 3-tier perspective stage
        base_y = int(h * 0.62)
        span_x = int(w * 0.42)
        cx = w // 2
        for layer_idx, dy in enumerate([0, 48, 96]):
            alpha = 0.14 - (layer_idx * 0.03)
            col = f"rgba(255, 255, 255, {alpha})" if monochrome else f"rgba(163, 135, 255, {alpha})"
            paths.append(f'<polygon points="{cx-span_x},{base_y+dy} {cx},{base_y+dy-70} {cx+span_x},{base_y+dy} {cx},{base_y+dy+70}" fill="none" stroke="{col}" stroke-width="1.2" />')
            paths.append(f'<line x1="{cx-span_x}" y1="{base_y+dy}" x2="{cx-span_x}" y2="{base_y+dy+48}" stroke="{faint_col}" stroke-width="1.2" />')
            paths.append(f'<line x1="{cx}" y1="{base_y+dy+70}" x2="{cx}" y2="{base_y+dy+118}" stroke="{faint_col}" stroke-width="1.2" />')
            paths.append(f'<line x1="{cx+span_x}" y1="{base_y+dy}" x2="{cx+span_x}" y2="{base_y+dy+48}" stroke="{faint_col}" stroke-width="1.2" />')

    return (
        f'<svg class="brand-device device-{intensity}" viewBox="0 0 {w} {h}" width="{w}" height="{h}" '
        f'xmlns="http://www.w3.org/2000/svg" style="position:absolute;inset:0;pointer-events:none;z-index:1;">'
        f'{" ".join(paths)}'
        f'</svg>'
    )


def _get_logo_html(monochrome: bool = False) -> str:
    """Official Vanna logo from docs.vanna.finance with signature gradient mark,
    or monochrome white version for pure black-and-white cards.
    """
    if monochrome:
        return (
            '<div class="brand-mark brand-mark-mono">'
            '<svg width="120" height="34" viewBox="0 0 120 34" fill="none" xmlns="http://www.w3.org/2000/svg">'
            '<path d="M18 4 L28 10 L26 22 L16 28 L6 22 L8 10 Z" stroke="white" stroke-width="2" fill="none" />'
            '<text x="36" y="24" fill="white" font-family="Plus Jakarta Sans, sans-serif" font-size="20" font-weight="800" letter-spacing="-0.04em">vanna</text>'
            '</svg>'
            '</div>'
        )
    if OFFICIAL_SVG_PATH.exists():
        svg_content = OFFICIAL_SVG_PATH.read_text(encoding="utf-8")
        return f'<div class="brand-mark">{svg_content}</div>'
    return '<div class="brand-mark"><span class="brand-wordmark">vanna</span></div>'


def validate_brief(b: dict, is_spec: bool = False) -> dict:
    """Pre-render assertion gate on brief and spec."""
    if not is_spec and not b.get("content_category"):
        raise ValueError("Brief missing content_category.")

    if "data" in b and isinstance(b["data"], list) and len(b["data"]) > 1:
        raise ValueError(f"{len(b['data'])} data points. One asset = one idea.")

    present = [k for k in TEXT_KEYS if b.get(k)]
    if len(present) > 4:
        raise ValueError(f"{len(present)} text blocks: {present}. Max 4.")

    # Narrowed gradient check: text fields must be solid
    for k in ("headline", "support", "footer", "hero", "subhead", "tag"):
        val = b.get(k)
        if isinstance(val, dict):
            val_str = json.dumps(val).lower()
        else:
            val_str = str(val or "").lower()
        if "gradient" in val_str:
            raise ValueError(f"Gradient on text field '{k}'. Text must be solid.")

    return b


def validate_markup(markup: str) -> str:
    """Post-render assertion gate on raw HTML markup before screenshot.
    Allows brand mark gradient; strictly bans gradients on layout/text content.
    """
    # Strip the brand mark before checking — its gradient is the signature
    body = re.sub(r'<(svg|div)[^>]*class="[^"]*brand-mark[^"]*".*?</\1>', "", markup, flags=re.S)
    low_body = body.lower()

    if "gradient" in low_body:
        raise ValueError("Gradient outside the brand mark.")

    used = {h for h in ACCENT_HEXES if h in low_body}
    if len(used) > 1:
        raise ValueError(f"{len(used)} accent colours in markup: {sorted(used)}. Max 1.")

    if f"max-height: {LAYOUT['content_max_height']}px" not in markup:
        raise ValueError("build_html() is not applying LAYOUT.content_max_height")

    return markup


# ─────────────────────────────────────────────────────────────────────────────
# 1. STATEMENT PRIMITIVE (editorial_manifesto)
# ─────────────────────────────────────────────────────────────────────────────

def render_editorial_manifesto(spec: dict, monochrome: bool = False) -> str:
    raw_headline = spec.get("headline", "")
    words = raw_headline.split(" ")
    if len(words) >= 4:
        accent_part = " ".join(words[-2:])
        main_part = " ".join(words[:-2])
        accent_class = "emphasis" if monochrome else "text-accent"
        headline = f'{_escape(main_part)} <span class="{accent_class}">{_escape(accent_part)}</span>'.replace("\n", "<br>")
    else:
        headline = _escape(raw_headline).replace("\n", "<br>")

    support = _escape(spec.get("support", spec.get("subhead", "")))
    footer = _escape(spec.get("footer", ""))
    logo_html = _get_logo_html(monochrome=monochrome)

    chip_class = "category-chip mono-chip" if monochrome else "category-chip"

    return f"""
    <div class="card-frame">
      <header class="card-header">
        {logo_html}
      </header>
      <main class="content-block">
        <div class="{chip_class}">NARRATIVE THESIS</div>
        <h1 class="manifesto-headline">{headline}</h1>
        {f'<p class="manifesto-support">{support}</p>' if support else ''}
      </main>
      <footer class="card-footer">
        <span>{footer}</span>
      </footer>
    </div>
    """


# ─────────────────────────────────────────────────────────────────────────────
# 2. ARCHITECTURE PRIMITIVE (technical_architecture)
# ─────────────────────────────────────────────────────────────────────────────

def render_technical_architecture(spec: dict, monochrome: bool = False) -> str:
    headline = _escape(spec.get("headline", "")).replace("\n", "<br>")
    support = _escape(spec.get("support", spec.get("subhead", "")))
    footer = _escape(spec.get("footer", ""))
    logo_html = _get_logo_html(monochrome=monochrome)

    chip_class = "category-chip mono-chip" if monochrome else "category-chip"
    highlight_class = "arch-node highlight-mono" if monochrome else "arch-node highlight"

    return f"""
    <div class="card-frame">
      <header class="card-header">
        {logo_html}
      </header>
      <main class="content-block">
        <div class="{chip_class}">SYSTEM TOPOLOGY</div>
        <h1 class="arch-headline">{headline}</h1>
        <div class="arch-pipeline">
          <div class="arch-node">LENDERS</div>
          <div class="arch-arrow">→</div>
          <div class="{highlight_class}">MARGIN ACCOUNT</div>
          <div class="arch-arrow">→</div>
          <div class="arch-node">DERIVATIVES</div>
        </div>
        {f'<p class="arch-support">{support}</p>' if support else ''}
      </main>
      <footer class="card-footer">
        <span>{footer}</span>
      </footer>
    </div>
    """


# ─────────────────────────────────────────────────────────────────────────────
# 3. SINGLE STAT PRIMITIVE (data_visualization)
# ─────────────────────────────────────────────────────────────────────────────

def render_data_visualization(spec: dict, monochrome: bool = False) -> str:
    headline = _escape(spec.get("headline", "")).replace("\n", "<br>")
    support = _escape(spec.get("support", spec.get("subhead", "")))
    footer = _escape(spec.get("footer", ""))

    hero_obj = spec.get("hero", {})
    if isinstance(hero_obj, dict):
        hero_val = _escape(hero_obj.get("value", ""))
        hero_lbl = _escape(hero_obj.get("label", ""))
    else:
        hero_val = _escape(str(hero_obj))
        hero_lbl = ""

    logo_html = _get_logo_html(monochrome=monochrome)
    chip_class = "category-chip mono-chip" if monochrome else "category-chip"
    stat_class = "stat-val stat-val-mono emphasis" if monochrome else "stat-val"

    return f"""
    <div class="card-frame">
      <header class="card-header">
        {logo_html}
      </header>
      <main class="content-block">
        <div class="{chip_class}">QUANTITATIVE RISK</div>
        <h1 class="data-headline">{headline}</h1>
        <div class="stat-unit">
          <span class="{stat_class}">{hero_val}</span>
          {f'<span class="stat-lbl">{hero_lbl}</span>' if hero_lbl else ''}
        </div>
        {f'<p class="stat-support">{support}</p>' if support else ''}
      </main>
      <footer class="card-footer">
        <span>{footer}</span>
      </footer>
    </div>
    """


def build_html(spec: dict, w: int = 1080, h: int = 1080, monochrome: bool = False) -> str:
    archetype = spec.get("archetype", "data_visualization")

    # Intensity mapping
    if archetype == "editorial_manifesto":
        intensity = "dense"
        inner_html = render_editorial_manifesto(spec, monochrome=monochrome)
    elif archetype == "technical_architecture":
        intensity = "structural"
        inner_html = render_technical_architecture(spec, monochrome=monochrome)
    else:
        intensity = "cropped"
        inner_html = render_data_visualization(spec, monochrome=monochrome)

    device_svg = generate_brand_device_svg(intensity=intensity, w=w, h=h, monochrome=monochrome)

    # Accent styles depending on monochrome test
    accent_color = "#FFFFFF" if monochrome else TOKENS["accent"]
    chip_color = "rgba(255, 255, 255, 0.7)" if monochrome else TOKENS["accent"]

    return f"""<!doctype html>
<html>
<head>
<meta charset="utf-8">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700;800&family=JetBrains+Mono:wght@600;700&display=swap" rel="stylesheet">
<style>
* {{
  margin: 0;
  padding: 0;
  box-sizing: border-box;
  -webkit-font-smoothing: antialiased;
}}

body {{
  width: {w}px;
  height: {h}px;
  overflow: hidden;
  background-color: #07020D;
  background-image:
    radial-gradient(ellipse 65% 55% at 95% 15%, rgba(94, 13, 70, 0.75) 0%, rgba(62, 8, 49, 0.45) 40%, rgba(7, 2, 13, 0) 75%),
    radial-gradient(ellipse 70% 60% at 8% 90%, rgba(71, 20, 133, 0.85) 0%, rgba(42, 11, 82, 0.5) 45%, rgba(7, 2, 13, 0) 80%);
  background-repeat: no-repeat;
  color: {TOKENS['text_hero']};
  font-family: 'Plus Jakarta Sans', sans-serif;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
}}

/* Material: Film Grain */
.grain {{
  position: absolute;
  inset: 0;
  opacity: 0.045;
  pointer-events: none;
  z-index: 2;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='3'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E");
}}

.card-frame {{
  width: {w}px;
  height: {h}px;
  padding: {int(LAYOUT['margin'] * (h / 1080))}px {int(LAYOUT['margin'] * (w / 1080))}px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  position: relative;
  z-index: 3;
}}

.card-header {{
  display: flex;
  align-items: center;
}}

.brand-mark svg {{
  height: {LAYOUT['logo']['size']}px;
  width: auto;
  display: block;
}}

.content-block {{
  max-height: {LAYOUT['content_max_height']}px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: {int(18 * (h / 1080))}px;
}}

.category-chip {{
  font-family: 'JetBrains Mono', monospace;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.12em;
  color: {chip_color};
  text-transform: uppercase;
}}

.manifesto-headline {{
  font-size: {int(LAYOUT['headline_size'] * (h / 1080))}px;
  font-weight: 800;
  line-height: 1.14;
  letter-spacing: -0.03em;
  color: {TOKENS['text_hero']};
}}

.text-accent {{
  color: {accent_color};
}}

.emphasis {{
  color: #FFFFFF;
  text-shadow: 0 0 24px rgba(255, 255, 255, 0.45),
               0 0 48px rgba(255, 255, 255, 0.2);
}}

.manifesto-support {{
  font-size: {int(LAYOUT['support_size'] * (h / 1080))}px;
  line-height: 1.4;
  color: {TOKENS['text_muted']};
}}

.arch-headline {{
  font-size: {int(42 * (h / 1080))}px;
  font-weight: 800;
  line-height: 1.15;
  letter-spacing: -0.02em;
  color: {TOKENS['text_hero']};
}}

.arch-pipeline {{
  display: flex;
  align-items: center;
  gap: 14px;
  margin: 6px 0;
}}

.arch-node {{
  font-family: 'JetBrains Mono', monospace;
  font-size: 13px;
  font-weight: 700;
  padding: 10px 18px;
  border: 1px solid {TOKENS['border_hairline']};
  border-radius: 8px;
  color: {TOKENS['text_hero']};
  background: rgba(255, 255, 255, 0.02);
}}

.arch-node.highlight {{
  border-color: {TOKENS['accent']};
  color: {TOKENS['accent']};
  background: rgba(163, 135, 255, 0.08);
}}

.arch-node.highlight-mono {{
  border-color: rgba(255, 255, 255, 0.6);
  color: #FFFFFF;
  text-shadow: 0 0 16px rgba(255, 255, 255, 0.4);
  background: rgba(255, 255, 255, 0.06);
}}

.arch-arrow {{
  color: {TOKENS['text_dim']};
  font-size: 16px;
}}

.arch-support {{
  font-size: {int(LAYOUT['support_size'] * (h / 1080))}px;
  color: {TOKENS['text_muted']};
  line-height: 1.4;
}}

.data-headline {{
  font-size: {int(40 * (h / 1080))}px;
  font-weight: 700;
  line-height: 1.2;
  letter-spacing: -0.02em;
  color: {TOKENS['text_hero']};
}}

.stat-unit {{
  display: flex;
  align-items: baseline;
  gap: 20px;
}}

.stat-val {{
  font-family: 'JetBrains Mono', monospace;
  font-size: {int(LAYOUT['hero_size'] * (h / 1080))}px;
  font-weight: 800;
  line-height: 0.85;
  letter-spacing: -0.06em;
  color: {TOKENS['accent']};
}}

.stat-val-mono {{
  color: #FFFFFF;
}}

.stat-lbl {{
  font-family: 'JetBrains Mono', monospace;
  font-size: 13px;
  font-weight: 700;
  letter-spacing: 0.08em;
  color: {TOKENS['text_muted']};
  text-transform: uppercase;
}}

.stat-support {{
  font-size: {int(LAYOUT['support_size'] * (h / 1080))}px;
  color: {TOKENS['text_muted']};
  line-height: 1.4;
}}

.card-footer {{
  font-family: 'JetBrains Mono', monospace;
  font-size: 13px;
  color: {TOKENS['text_dim']};
  border-top: 1px solid {TOKENS['border_hairline']};
  padding-top: 24px;
}}
</style>
</head>
<body>
  {device_svg}
  <div class="grain"></div>
  {inner_html}
</body>
</html>"""


def render(
    brief: dict,
    out: Path,
    keep_html: Path | None = None,
    forced_layout: Optional[str] = None,
    w: int = 1080,
    h: int = 1080,
    monochrome: bool = False,
) -> Path:
    out = out.resolve()
    # 1. Validate brief input
    validate_brief(brief, is_spec=False)

    # 2. Strict category validation
    cat = brief.get("content_category")
    if not cat:
        raise ValueError("Brief missing content_category. No default — it selects the template.")
    if cat not in TEMPLATE_MAP:
        raise ValueError(f"Unknown content_category: {cat!r}. Must be one of {sorted(TEMPLATE_MAP)}")

    layout_target = _TEMPLATE_ALIAS.get(forced_layout, forced_layout) if forced_layout else TEMPLATE_MAP[cat]

    # 3. Compile art direction (strict, zero defaults)
    spec = compile_art_direction(brief, forced_archetype=layout_target)

    # 4. Validate compiled spec
    validate_brief(spec, is_spec=True)

    # 5. Build and validate markup
    markup = build_html(spec, w=w, h=h, monochrome=monochrome)
    validate_markup(markup)

    tmp_dir = Path(tempfile.mkdtemp(prefix="vanna-visual-v2-"))
    html_path = tmp_dir / "card.html"
    html_path.write_text(markup, encoding="utf-8")
    if keep_html:
        keep_html.write_text(markup, encoding="utf-8")

    out.parent.mkdir(parents=True, exist_ok=True)
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
    parser = argparse.ArgumentParser(description="Vanna Visual Engine v2.")
    parser.add_argument("brief", nargs="?", type=Path, help="Path to brief JSON file")
    parser.add_argument("--stdin", action="store_true", help="Read JSON brief from stdin")
    parser.add_argument("-o", "--out", required=True, type=Path, help="Output PNG path")
    parser.add_argument("--keep-html", type=Path, help="Optional path to save generated HTML markup")
    parser.add_argument("--layout", type=str, help="Force layout archetype")
    parser.add_argument("--width", type=int, default=1080, help="Canvas width")
    parser.add_argument("--height", type=int, default=1080, help="Canvas height")
    parser.add_argument("--monochrome", action="store_true", help="Render monochrome B&W version")
    args = parser.parse_args()

    if args.stdin:
        brief_data = json.loads(sys.stdin.read())
    elif args.brief:
        brief_data = json.loads(args.brief.read_text(encoding="utf-8"))
    else:
        sys.exit("Error: Must provide brief path or --stdin")

    out_path = render(
        brief_data,
        args.out,
        keep_html=args.keep_html,
        forced_layout=args.layout,
        w=args.width,
        h=args.height,
        monochrome=args.monochrome,
    )
