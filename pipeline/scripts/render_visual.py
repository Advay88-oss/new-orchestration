#!/usr/bin/env python3
"""Vanna social visual renderer — JSON brief in, on-brand PNG out.

Builds HTML from the Vanna dark social theme (derived from design references
cl-11 / cl-16) and rasterises it with headless Chrome. No AI image generation
touches anything that must be read.

Usage:
    python render_visual.py brief.json -o out.png
    echo '{...}' | python render_visual.py --stdin -o out.png

Brief schema:
    {
      "type": "infographic" | "stat-card" | "quote-card",
      "headline": "Leverage is easy. Not getting liquidated is the hard part.",
      "emphasis_phrase": "Not getting liquidated",   # gets the gradient
      "subhead": "One health factor across your whole book.",
      "data": [{"label": "Healthy", "value": "above 2.0",
                 "note": "Room to move.", "color": "blue"}],
      "stat": {"value": "1.1x", "caption": "liquidation threshold"},
      "quote": "Credit that composes. Leverage that holds.",
      "disclaimer": "Illustrative example. Stellar testnet only; leverage carries risk of loss.",
      "background": "path/to/optional/ai-texture.jpg"
    }
"""

from __future__ import annotations

import argparse
import base64
import html
import json
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

# Vanna palette — files/04 + design references/theme.md
PALETTE = {
    "violet": "#703AE6",
    "violet_light": "#9F7BEE",
    "rose": "#FF007A",
    "rose_light": "#FF54A6",
    "red": "#FC5457",
    "blue": "#32EEE2",
    "gray": "#A9A9A9",
    "gray_dim": "#949494",
}
ACCENT = {"red": "#FC5457", "rose": "#FF54A6", "violet": "#9F7BEE", "blue": "#32EEE2"}
BACKGROUND = "#0D0616"
LOGO_PATH = Path(__file__).resolve().parents[1] / "state" / "logo.png"


def _apply_okf_brand() -> None:
    """Override the palette from the OKF bundle's Brand Palette concept.

    Falls back silently to the hardcoded defaults above whenever the bundle is
    absent, unreadable, or carries no palette — the renderer must never crash on
    a missing knowledge pack, exactly like the safety gate. When a company
    swaps its bundle, its colours come with it.
    """
    global PALETTE, ACCENT, BACKGROUND, LOGO_PATH
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from okf_loader import Bundle, default_bundle_path

        root = default_bundle_path()
        brand = Bundle.load(root).brand()
        if not brand:
            return
        colors = brand.get("colors") or {}
        if colors:
            PALETTE = {**PALETTE, **colors}
        names = brand.get("accent") or []
        if names:
            ACCENT = {n: PALETTE.get(n, PALETTE["violet_light"]) for n in names}
        if brand.get("background"):
            BACKGROUND = str(brand["background"])
        # Per-tenant logo. A bundle-relative path ("/assets/logo.png") resolves
        # against the bundle root; a repo-relative one ("/pipeline/state/...")
        # against the repo. Fall back to the built-in state/logo.png.
        raw = brand.get("logo")
        if raw:
            rel = str(raw).lstrip("/")
            repo = Path(__file__).resolve().parents[2]
            for cand in (Path(root) / rel, repo / rel):
                if cand.exists():
                    LOGO_PATH = cand
                    break
    except Exception:
        # Any bundle problem keeps the built-in Vanna palette and logo.
        return


_apply_okf_brand()


def _rgba(hex_color: str, alpha: float) -> str:
    """#RRGGBB -> rgba(r,g,b,alpha). Used for the decorative glow blobs so they
    follow the tenant palette instead of being hardcoded. Falls back to the hex
    as-is if it is not a 6-digit hex."""
    h = (hex_color or "").lstrip("#")
    if len(h) != 6:
        return hex_color
    try:
        r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    except ValueError:
        return hex_color
    return f"rgba({r},{g},{b},{alpha})"


def find_chrome() -> str:
    for candidate in CHROME_CANDIDATES:
        if Path(candidate).exists():
            return candidate
        found = shutil.which(candidate)
        if found:
            return found
    sys.exit("Chrome not found. Install Chrome or set a path in CHROME_CANDIDATES.")


def headline_size(text: str) -> int:
    """Scale the headline so it never orphans a word on its own line.

    Fixes the wrap problem seen in the first prototype, where a 3-line headline
    left 'part.' stranded.
    """
    n = len(text)
    if n <= 42:
        return 62
    if n <= 60:
        return 54
    if n <= 80:
        return 46
    return 40


def emphasise(headline: str, phrase: str | None) -> str:
    """Wrap the emphasis phrase in the brand gradient span."""
    safe = html.escape(headline)
    if not phrase:
        return safe
    safe_phrase = html.escape(phrase)
    if safe_phrase not in safe:
        return safe
    return safe.replace(safe_phrase, f"<em>{safe_phrase}</em>", 1)


def build_rows(data: list[dict]) -> str:
    if not data:
        return ""
    rows = []
    for item in data:
        colour = ACCENT.get(item.get("color", "violet"), PALETTE["violet_light"])
        rows.append(
            f"""
      <div class="row">
        <span class="dot" style="background:{colour}"></span>
        <span class="rval" style="color:{colour}">{html.escape(str(item.get('value','')))}</span>
        <span class="rlbl">{html.escape(str(item.get('label','')))}</span>
        <span class="rnote">{html.escape(str(item.get('note','')))}</span>
      </div>"""
        )
    return f'<div class="rows">{"".join(rows)}</div>'


def build_stat(stat: dict | None) -> str:
    if not stat:
        return ""
    return f"""
    <div class="stat">
      <div class="statval">{html.escape(str(stat.get('value','')))}</div>
      <div class="statcap">{html.escape(str(stat.get('caption','')))}</div>
    </div>"""


def build_quote(quote: str | None) -> str:
    if not quote:
        return ""
    return f'<div class="quote">{html.escape(quote)}</div>'


def build_html(brief: dict) -> str:
    headline = brief.get("headline", "")
    hsize = headline_size(headline)
    bg_layer = ""
    if brief.get("background"):
        bg_path = Path(brief["background"])
        if bg_path.exists():
            b64 = base64.b64encode(bg_path.read_bytes()).decode()
            mime = "image/png" if bg_path.suffix.lower() == ".png" else "image/jpeg"
            bg_layer = (
                f'<div class="aitex" style="background-image:url(data:{mime};base64,{b64})"></div>'
            )

    # Load and Base64 encode the official Vanna logo
    logo_b64 = ""
    if LOGO_PATH.exists():
        logo_b64 = base64.b64encode(LOGO_PATH.read_bytes()).decode()

    return f"""<!doctype html>
<html><head><meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700&display=swap" rel="stylesheet">
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{width:1080px;height:1080px;overflow:hidden;background:{BACKGROUND};color:#fff;
     font-family:'Plus Jakarta Sans',system-ui,sans-serif;position:relative}}
.aitex{{position:absolute;inset:0;background-size:cover;background-position:center;
       opacity:.30;z-index:0}}
.glow{{position:absolute;border-radius:50%;filter:blur(95px);z-index:1}}
.g1{{width:780px;height:640px;left:-190px;bottom:-210px;background:{_rgba(PALETTE['violet'],0.52)}}}
.g2{{width:640px;height:580px;right:-170px;top:140px;background:{_rgba(PALETTE['rose'],0.26)}}}
.g3{{width:430px;height:390px;left:43%;top:-150px;background:{_rgba(PALETTE['violet'],0.20)}}}
.wrap{{position:relative;z-index:2;height:100%;display:flex;flex-direction:column;
      align-items:center;padding:56px 76px 42px}}
.brand{{display:flex;align-items:center;gap:14px;margin-bottom:40px}}
.cube{{width:34px;height:34px;border-radius:8px;
      background:linear-gradient(135deg,{PALETTE['rose_light']} 0%,{PALETTE['violet']} 100%);
      box-shadow:0 6px 18px rgba(112,58,230,.5)}}
.brand span{{font-size:30px;font-weight:600;letter-spacing:-.01em}}
h1{{font-size:{hsize}px;line-height:1.16;font-weight:700;text-align:center;
   letter-spacing:-.02em;text-wrap:balance;max-width:920px}}
h1 em{{font-style:normal;
      background:linear-gradient(135deg,{PALETTE['red']} 10%,{PALETTE['violet']} 80%);
      -webkit-background-clip:text;background-clip:text;color:transparent}}
.sub{{margin-top:18px;font-size:20px;color:{PALETTE['gray']};text-align:center;
     font-weight:400;max-width:820px}}
.rows{{margin-top:54px;width:860px;display:flex;flex-direction:column;gap:12px}}
.row{{display:flex;align-items:center;gap:18px;height:74px;padding:0 26px;
     border-radius:16px;background:rgba(255,255,255,.045);
     border:1px solid rgba(255,255,255,.09)}}
.dot{{width:11px;height:11px;border-radius:50%;flex:none}}
.rval{{font-size:21px;font-weight:700;width:180px;flex:none;
      font-variant-numeric:tabular-nums}}
.rlbl{{font-size:19px;font-weight:600;width:220px;flex:none}}
.rnote{{font-size:16px;color:{PALETTE['gray']};font-weight:400;flex:1;line-height:1.4}}
.stat{{margin-top:70px;text-align:center}}
.statval{{font-size:150px;font-weight:700;letter-spacing:-.04em;line-height:1;
         background:linear-gradient(135deg,{PALETTE['red']} 10%,{PALETTE['violet']} 80%);
         -webkit-background-clip:text;background-clip:text;color:transparent}}
.statcap{{margin-top:14px;font-size:22px;color:{PALETTE['gray']};font-weight:400}}
.quote{{margin-top:90px;font-size:46px;font-weight:700;text-align:center;
       line-height:1.25;max-width:880px;text-wrap:balance}}
.foot{{margin-top:44px;margin-bottom:auto;text-align:center;font-size:17px;
      color:{PALETTE['gray']};line-height:1.55;max-width:840px}}
/* Keep the footer attached to the content it qualifies, then centre the whole
   block: the auto margins above the content and below the footer split the
   leftover space evenly. Previously .foot was pinned to the bottom edge, which
   dumped every spare pixel into one gap on sparse cards. Auto margins only
   absorb free space, so denser cards are unaffected. Child 2 is the first
   content element after .brand, whatever the card type. */
.wrap > :nth-child(2){{margin-top:auto}}
</style></head>
<body>
{bg_layer}
<div class="glow g1"></div><div class="glow g2"></div><div class="glow g3"></div>
<div class="wrap">
  <div class="brand"><img src="data:image/png;base64,{logo_b64}" style="height:44px;display:block;" /></div>
  <h1>{emphasise(headline, brief.get('emphasis_phrase'))}</h1>
  {f'<div class="sub">{html.escape(brief["subhead"])}</div>' if brief.get('subhead') else ''}
  {build_quote(brief.get('quote'))}
  {build_stat(brief.get('stat'))}
  {build_rows(brief.get('data', []))}
  <div class="foot">{html.escape(brief.get('disclaimer',''))}</div>
</div>
</body></html>"""


def render(brief: dict, out: Path, keep_html: Path | None = None) -> Path:
    out = out.resolve()
    markup = build_html(brief)
    tmp_dir = Path(tempfile.mkdtemp(prefix="vanna-visual-"))
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
        "--window-size=1080,1080",
        f"--screenshot={out}",
        html_path.as_uri(),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
    if not out.exists():
        sys.exit(f"Render failed.\nstdout: {result.stdout}\nstderr: {result.stderr}")
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="Render a Vanna social visual")
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("brief", nargs="?", type=Path)
    src.add_argument("--stdin", action="store_true")
    ap.add_argument("-o", "--out", type=Path, required=True)
    ap.add_argument("--keep-html", type=Path, help="also write the generated HTML")
    args = ap.parse_args()

    raw = sys.stdin.read() if args.stdin else args.brief.read_text(encoding="utf-8")
    brief = json.loads(raw)

    path = render(brief, args.out, args.keep_html)
    print(json.dumps({"ok": True, "png": str(path), "bytes": path.stat().st_size}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
