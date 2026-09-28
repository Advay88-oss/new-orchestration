"""A company's logo, from its own website, when the profile has none.

The analyzer used to take the logo only from an <img> whose alt or class says
"logo", and skipped inline SVG, which is how most sites draw it (Morpho's
profile came out with no logo, and every poster fell back to a template).

This opens the site in a real browser and screenshots the header's home link
or logo element itself (transparent background, at 3x), so an inline SVG
works too. Failing that, the site's apple-touch-icon. The result is kept in
the company's brain folder and in brain meta `visual:logo`; context.logo_path()
falls back to it while the profile has no logo of its own (an owner-set
profile logo always wins).

    python -m pipeline.brand_brain.logo <tenant> [website]
"""
from __future__ import annotations

import json
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36"

# The most logo-like element in the top-left of the page: the home link or an
# element named logo/brand, visible, of a plausible size.
_FIND_JS = r"""
() => {
  const vw = window.innerWidth;
  const sel = ['header a[href="/"]', 'nav a[href="/"]', 'a[href="/"]', 'a[aria-label*="home" i]',
               '[class*="logo" i]', '[id*="logo" i]', 'img[alt*="logo" i]', '[aria-label*="logo" i]',
               'header svg', 'nav svg'];
  const seen = new Set(); const out = [];
  for (const s of sel) {
    for (const el of document.querySelectorAll(s)) {
      if (seen.has(el)) continue; seen.add(el);
      const r = el.getBoundingClientRect();
      const cs = getComputedStyle(el);
      if (cs.visibility === 'hidden' || cs.display === 'none' || +cs.opacity === 0) continue;
      if (r.top > 160 || r.left > vw / 2 || r.width < 24 || r.height < 12 || r.width > 420 || r.height > 160) continue;
      if (!el.querySelector('svg, img') && !['svg', 'IMG'].includes(el.tagName)) continue;
      out.push({i: out.length, sel: s, top: r.top, left: r.left, w: r.width, h: r.height});
      el.setAttribute('data-vn-logo', String(out.length - 1));
    }
  }
  return out;
}
"""


def _clean(png: bytes) -> Optional[bytes]:
    """Trim transparent/flat edges; reject a blank capture."""
    from io import BytesIO
    from PIL import Image, ImageChops
    im = Image.open(BytesIO(png)).convert("RGBA")
    if im.getchannel("A").getextrema() == (255, 255):
        # An opaque capture (the site paints its header): key the corner colour
        # out to transparency, keeping anti-aliased edges as partial alpha.
        bg = im.getpixel((0, 0))[:3]
        rgb = im.convert("RGB")
        diff = ImageChops.difference(rgb, Image.new("RGB", im.size, bg)).convert("L")
        alpha = diff.point(lambda v: 0 if v < 12 else min(255, v * 3))
        im.putalpha(alpha)
    # A translucent overlay the CSS could not switch off (morpho.org paints
    # rgba(0,0,0,.6) behind its header): the one colour covering most of the
    # capture is background, not mark.
    from collections import Counter
    px = list(im.getdata())
    (dom, n), = Counter(px).most_common(1)
    if n > 0.35 * len(px) and dom[3] < 255:
        im.putdata([(0, 0, 0, 0) if (abs(p[0] - dom[0]) + abs(p[1] - dom[1]) + abs(p[2] - dom[2]) < 30
                                     and p[3] <= dom[3] + 10) else p for p in px])
    bbox = im.getchannel("A").getbbox()
    if bbox is None:
        return None
    im = im.crop(bbox)
    if im.width < 40 or im.height < 16:
        return None
    buf = BytesIO()
    im.save(buf, "PNG")
    return buf.getvalue()


def _from_header(website: str) -> Optional[tuple[bytes, dict]]:
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        b = p.chromium.launch()
        try:
            pg = b.new_page(viewport={"width": 1440, "height": 900}, device_scale_factor=3, user_agent=UA)
            # "load", not "networkidle": sites with analytics or live data
            # never go idle (morpho.org timed out at 45 s).
            pg.goto(website, wait_until="load", timeout=45000)
            pg.wait_for_timeout(2500)
            cands = pg.evaluate(_FIND_JS) or []
            # Every background off, so the capture is the mark alone on
            # transparency (omit_background only drops the page's white).
            pg.add_style_tag(content="*, *::before, *::after { background: transparent !important; "
                                     "background-color: transparent !important; box-shadow: none !important; "
                                     "backdrop-filter: none !important; }")
            pg.wait_for_timeout(200)
            # Prefer named logo elements and home links, then the top-left-most.
            rank = {s: i for i, s in enumerate(['[class*="logo" i]', 'img[alt*="logo" i]', '[id*="logo" i]',
                                                 'header a[href="/"]', 'nav a[href="/"]', 'a[href="/"]'])}
            cands.sort(key=lambda c: (rank.get(c["sel"], 9), c["top"] + c["left"] / 4))
            for c in cands[:6]:
                el = pg.query_selector('[data-vn-logo="' + str(c["i"]) + '"]')
                if not el:
                    continue
                shot = _clean(el.screenshot(omit_background=True))
                if shot:
                    return shot, {"source": "header", "selector": c["sel"], "css_px": [round(c["w"]), round(c["h"])]}
            icon = pg.evaluate("""() => { const l = [...document.querySelectorAll('link[rel*="apple-touch-icon"], link[rel="icon"]')]
                .map(x => ({href: x.href, s: parseInt((x.getAttribute('sizes') || '0').split('x')[0]) || 0}))
                .sort((a, b) => b.s - a.s); return l.length ? l[0].href : null }""")
        finally:
            b.close()
    if icon and not icon.lower().endswith((".ico", ".svg")):
        try:
            req = urllib.request.Request(icon, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=15) as r:
                shot = _clean(r.read())
            if shot:
                return shot, {"source": "icon", "url": icon}
        except Exception:                           # noqa: BLE001 — no logo found
            pass
    return None


def fetch_logo(tenant: str, website: Optional[str] = None) -> dict[str, Any]:
    """Find, save and remember the tenant's logo. Never raises."""
    from pipeline.brand_brain import store as S
    from pipeline.brand_brain.client import Brain
    b = Brain(tenant)
    site = website or ((b.get_brand_profile() or {}).get("company") or {}).get("website") or ""
    if not site:
        return {"ok": False, "error": "no website in the profile"}
    try:
        got = _from_header(site)
    except Exception as exc:                        # noqa: BLE001 — boundary
        return {"ok": False, "error": (type(exc).__name__ + ": " + str(exc))[:200]}
    if not got:
        return {"ok": False, "error": "no logo found on " + site}
    data, how = got
    d = S.tenant_dir(tenant) / "images"
    d.mkdir(parents=True, exist_ok=True)
    f = d / "logo.png"
    f.write_bytes(data)
    rel = f.resolve().relative_to(Path(__file__).resolve().parents[2]).as_posix()
    rec = {"path": rel, "website": site, "found_at": datetime.now(timezone.utc).isoformat(timespec="seconds"), **how}
    b.meta("visual:logo", json.dumps(rec))
    try:
        b.add_image("logo", rel, kind="logo", caption="The " + tenant + " logo, from " + site, source="website")
    except Exception:                               # noqa: BLE001 — the file and meta are what count
        pass
    return {"ok": True, **rec}


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    print(json.dumps(fetch_logo(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None), indent=2))
