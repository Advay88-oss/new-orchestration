"""Deterministic renderer: VisualSpec -> HTML -> Playwright -> PNG.

This module is the boundary the old system lost. Both deterministic renderers
(`render_visual.py`, `poster_compositor.py`) failed at import, the errors were
swallowed, and the only remaining path to pixels was a hardcoded prose paragraph
handed to a diffusion model asked to both illustrate and typeset. Everything the
founder disliked — misspelled words in-image, "TECHNICALARCHITECTURE" with no
letterspacing, the logo sitting on top of the headline, one layout with swapped
labels — follows from that.

Rules enforced here:
  1. Every readable element is laid out by the browser. The image model never
     touches text, and never touches the logo.
  2. Colours must be design tokens. A spec with an invented colour fails.
  3. The logo occupies a reserved band. Collision is structurally impossible.
  4. Given the same spec, the render is byte-stable — no randomness, no clocks.
"""
from __future__ import annotations

import html
import os
import time
from pathlib import Path

from .contracts import StageResult, VisualSpec, degraded, digest, ok
from .design import (
    CANVAS, CONTENT_MAX_HEIGHT, HAIRLINE, INK, LOGO_BAND_HEIGHT, LOGO_SIZE,
    MARGIN, PALETTE, RENDER_SCALE, SAFE_WIDTH, SPACE, TYPE, css_variables,
    validate_palette_slice,
)

REPO = Path(__file__).resolve().parents[1]
OUT_DIR = Path(os.environ.get("VANNA_RENDER_DIR", REPO / "state" / "renders"))


class RenderError(RuntimeError):
    pass


def _esc(text: str) -> str:
    return html.escape(text, quote=True)


def _block_html(spec: VisualSpec, idx: int) -> str:
    b = spec.blocks[idx]
    is_focal = spec.focal.block_index == idx
    cls = f"block block--{b.role} block--{b.emphasis}" + (" block--focal" if is_focal else "")
    if b.role == "stat":
        return f'<div class="{cls}"><span class="stat-value">{_esc(b.text)}</span></div>'
    if b.role == "label":
        return f'<div class="{cls}"><span class="label-text">{_esc(b.text)}</span></div>'
    if b.role == "step":
        return (f'<div class="{cls}"><span class="step-index">{idx + 1:02d}</span>'
                f'<span class="step-text">{_esc(b.text)}</span></div>')
    return f'<div class="{cls}">{_esc(b.text)}</div>'


def _layout_html(spec: VisualSpec) -> str:
    blocks = list(range(len(spec.blocks)))
    if spec.layout == "comparison":
        left = [i for i in blocks if spec.blocks[i].role == "compare_left"]
        right = [i for i in blocks if spec.blocks[i].role == "compare_right"]
        rest = [i for i in blocks if i not in left + right]
        return (
            '<div class="cmp">'
            f'<div class="cmp-col">{"".join(_block_html(spec, i) for i in left)}</div>'
            '<div class="cmp-rule"></div>'
            f'<div class="cmp-col">{"".join(_block_html(spec, i) for i in right)}</div>'
            '</div>'
            + "".join(_block_html(spec, i) for i in rest)
        )
    if spec.layout == "sequence":
        return f'<div class="seq">{"".join(_block_html(spec, i) for i in blocks)}</div>'
    return f'<div class="stack">{"".join(_block_html(spec, i) for i in blocks)}</div>'


def build_html(spec: VisualSpec, *, wordmark: str = "VANNA",
               texture_data_uri: str | None = None) -> str:
    """Compose the page. Pure function of the spec — no time, no randomness."""
    problems = validate_palette_slice(spec.palette.ink, spec.palette.ground, spec.palette.accent)
    if problems:
        raise RenderError("; ".join(problems))

    bg_layer = ""
    if spec.background == "gradient":
        bg_layer = (
            f'<div class="bg bg--gradient" style="background:'
            f'radial-gradient(120% 90% at 18% 8%, {PALETTE["violet_bloom"]}38 0%, transparent 58%),'
            f'radial-gradient(90% 70% at 88% 92%, {PALETTE["fuchsia_bloom"]}30 0%, transparent 60%)'
            f'"></div>'
        )
    elif spec.background == "texture" and texture_data_uri:
        # The ONLY place a generated image is permitted: a background plate,
        # behind everything, carrying no text and no brand mark.
        bg_layer = (f'<div class="bg bg--texture" style="background-image:url({texture_data_uri})">'
                    f'</div><div class="bg bg--scrim"></div>')

    subhead = (f'<p class="subhead">{_esc(spec.subhead)}</p>' if spec.subhead else "")
    disclaimer = (f'<p class="disclaimer">{_esc(spec.disclaimer)}</p>' if spec.disclaimer else "")

    return f"""<!doctype html>
<html><head><meta charset="utf-8">
<style>
{css_variables()}
* {{ margin:0; padding:0; box-sizing:border-box; }}
html,body {{ width:{CANVAS}px; height:{CANVAS}px; }}
body {{
  background:{spec.palette.ground};
  color:{spec.palette.ink};
  font-family:var(--font-sans);
  -webkit-font-smoothing:antialiased;
  position:relative; overflow:hidden;
}}
.bg {{ position:absolute; inset:0; }}
.bg--texture {{ background-size:cover; background-position:center; opacity:0.55; }}
.bg--scrim {{ background:linear-gradient(180deg,{spec.palette.ground}CC 0%,{spec.palette.ground}F2 100%); }}

/* Reserved logo band. Content can never enter it, so collision is impossible. */
.logo-band {{
  position:absolute; top:var(--margin); left:var(--margin);
  height:{LOGO_SIZE}px; display:flex; align-items:center; gap:10px; z-index:2;
}}
.logo-mark {{ width:{LOGO_SIZE}px; height:{LOGO_SIZE}px; border-radius:8px;
  background:{spec.palette.accent}; display:block; }}
.logo-word {{ font-size:15px; font-weight:700; letter-spacing:0.18em;
  color:var(--ink-muted); text-transform:uppercase; }}

.frame {{
  position:absolute; left:var(--margin); right:var(--margin);
  top:calc(var(--margin) + {LOGO_BAND_HEIGHT}px);
  width:var(--safe-width); max-height:{CONTENT_MAX_HEIGHT}px;
  display:flex; flex-direction:column; gap:var(--space-md); z-index:2;
}}
.headline {{
  font-size:var(--type-headline-size); font-weight:var(--type-headline-weight);
  letter-spacing:var(--type-headline-tracking); line-height:var(--type-headline-leading);
  color:var(--ink-hero); text-wrap:balance;
}}
.subhead {{
  font-size:var(--type-subhead-size); font-weight:var(--type-subhead-weight);
  letter-spacing:var(--type-subhead-tracking); line-height:var(--type-subhead-leading);
  color:var(--ink-body); max-width:calc(var(--safe-width) * 0.88);
}}
.stack {{ display:flex; flex-direction:column; gap:var(--space-sm); }}
.seq {{ display:flex; flex-direction:column; gap:var(--space-sm);
  border-left:2px solid {spec.palette.accent}; padding-left:var(--space-md); }}
.cmp {{ display:grid; grid-template-columns:1fr 1px 1fr; gap:var(--space-md); align-items:start; }}
.cmp-rule {{ background:var(--hairline); height:100%; min-height:96px; }}
.cmp-col {{ display:flex; flex-direction:column; gap:var(--space-sm); }}

.block {{ font-size:var(--type-body-size); line-height:var(--type-body-leading); color:var(--ink-body); }}
.block--muted {{ color:var(--ink-dim); }}
.block--primary {{ color:var(--ink-hero); }}
.block--focal .stat-value {{ color:{spec.palette.accent}; }}
.stat-value {{
  font-family:var(--font-mono); font-size:var(--type-hero-size);
  font-weight:var(--type-hero-weight); letter-spacing:var(--type-hero-tracking);
  line-height:var(--type-hero-leading); color:var(--ink-hero); display:block;
}}
.label-text {{
  font-size:var(--type-label-size); font-weight:var(--type-label-weight);
  letter-spacing:var(--track-upper);   /* the fix for TECHNICALARCHITECTURE */
  text-transform:uppercase; color:var(--ink-muted);
}}
.block--step {{ display:flex; gap:var(--space-sm); align-items:baseline; }}
.step-index {{ font-family:var(--font-mono); font-size:var(--type-caption-size);
  color:{spec.palette.accent}; letter-spacing:0.08em; }}
.disclaimer {{
  position:absolute; left:var(--margin); bottom:var(--margin);
  font-size:var(--type-caption-size); letter-spacing:var(--type-caption-tracking);
  color:var(--ink-dim); max-width:var(--safe-width); z-index:2;
}}
</style></head>
<body>
{bg_layer}
<div class="logo-band"><span class="logo-mark"></span><span class="logo-word">{_esc(wordmark)}</span></div>
<div class="frame">
  <h1 class="headline">{_esc(spec.headline)}</h1>
  {subhead}
  {_layout_html(spec)}
</div>
{disclaimer}
</body></html>"""


def render_png(spec: VisualSpec, out_path: Path, *,
               texture_data_uri: str | None = None) -> Path:
    """Rasterise with a headless browser. Raises rather than returning None —
    the old path swallowed the ImportError and shipped runs with no visual."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:              # loud, not swallowed
        raise RenderError(
            "playwright is not installed in this interpreter; deterministic "
            "rendering is unavailable"
        ) from exc

    markup = build_html(spec, texture_data_uri=texture_data_uri)
    out_path = out_path.resolve()          # file:// URIs require an absolute path
    out_path.parent.mkdir(parents=True, exist_ok=True)
    html_path = out_path.with_suffix(".html")
    html_path.write_text(markup, encoding="utf-8")

    with sync_playwright() as p:
        browser = p.chromium.launch(args=["--force-color-profile=srgb",
                                          "--disable-lcd-text"])
        try:
            page = browser.new_page(
                viewport={"width": CANVAS, "height": CANVAS},
                device_scale_factor=RENDER_SCALE,
            )
            page.goto(html_path.as_uri(), wait_until="load")
            page.wait_for_timeout(120)       # fonts settle; fixed, not random
            page.screenshot(path=str(out_path), type="png")
        finally:
            browser.close()
    return out_path


def render_stage(spec: VisualSpec, run_id: str, *, attempt: int = 1,
                 texture_data_uri: str | None = None) -> StageResult[dict]:
    started = time.time()
    ih = digest(spec.model_dump())
    out = OUT_DIR / f"{run_id}_v{attempt}.png"
    try:
        path = render_png(spec, out, texture_data_uri=texture_data_uri)
    except RenderError as exc:
        return degraded("render", None, started, f"render failed: {exc}", input_hash=ih)
    return ok("render", {"path": str(path), "bytes": path.stat().st_size,
                         "width": CANVAS * RENDER_SCALE, "height": CANVAS * RENDER_SCALE,
                         "attempt": attempt},
              started, input_hash=ih, tool_calls=["playwright.screenshot"])
