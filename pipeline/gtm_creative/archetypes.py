"""Archetype renderers — two ways to make a Vanna asset.

The generator had one path: describe a scene, hand it to an image model, paste a
logo on top. That is why every post looked the same, and why words came back
misspelt ("Volue" in a Veo frame) — the model was being asked to do a job it
cannot do.

There are really two jobs, and they need different machinery:

  **Geometry** — containment, a path that returns, a value near a floor. An
  image model is good at this, as long as it is asked for form only. It renders
  a textless canvas; every word is composited afterwards by PIL, with the exact
  strings we passed in, so nothing published can be misspelt.

  **Typography** — a ledger, a statement, a quoted rule. There is no image to
  generate. Sending these through a model is how you get invented labels and
  fake formulas. They are drawn deterministically, end to end.

Which archetype runs decides which path is taken. That is the whole anti-
monotony mechanism: two consecutive posts cannot share an archetype, and half
the archetypes never touch the image model at all.
"""
from __future__ import annotations

import textwrap
from pathlib import Path
from typing import Any, Optional

from PIL import Image, ImageDraw, ImageFont

REPO_ROOT = Path(__file__).resolve().parents[2]
FONTS = REPO_ROOT / "pipeline" / "assets" / "fonts"
OUT_DIR = REPO_ROOT / "pipeline" / "state"

# Tokens read from docs.vanna.finance computed styles, not invented.
GROUND = (8, 8, 10)
SURFACE = (19, 19, 23)
SURFACE_2 = (29, 29, 36)
LINE = (42, 42, 51)
INK = (242, 242, 244)
INK_MUTED = (138, 138, 147)
INK_FAINT = (95, 95, 106)
VIOLET = (124, 92, 255)
VIOLET_LIGHT = (163, 135, 255)
HEALTHY = (61, 220, 151)
DANGER = (255, 93, 93)


def font(weight: str, size: int) -> ImageFont.FreeTypeFont:
    path = FONTS / ("inter-" + weight + ".ttf")
    if not path.exists():
        path = FONTS / "inter-regular.ttf"
    return ImageFont.truetype(str(path), size)


def _track(draw: ImageDraw.ImageDraw, xy, text: str, f, fill, tracking: float = 0.0):
    """Draw text with letter-spacing. PIL has none, so step glyph by glyph."""
    x, y = xy
    for ch in text:
        draw.text((x, y), ch, font=f, fill=fill)
        x += draw.textlength(ch, font=f) + tracking
    return x


def _wrap(draw, text: str, f, max_w: int) -> list[str]:
    words, lines, cur = text.split(), [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if draw.textlength(trial, font=f) <= max_w:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


# --------------------------------------------------------------------------
# A5 — Round Trip. Generated geometry + composited type.
# --------------------------------------------------------------------------

A5_PROMPT = (
    "A single dark matte-graphite chamber, rectangular and sealed, resting "
    "slightly left of centre on an expansive near-black floor (#08080A). "
    "One continuous thin conduit leaves the chamber's right face, travels "
    "rightward, passes through a smaller neutral grey module, curves and "
    "RETURNS to re-enter the same chamber's lower right face, forming one "
    "closed loop. Inside the chamber's open front, a solid fill level sits "
    "visibly higher than a faint horizontal reference line beneath it. "
    "Two further identical chambers sit far behind in shadow, unlit, sealed "
    "and entirely unconnected. "
    "Lighting: clinical, restrained, a single soft key from upper left. Matte "
    "surfaces only. One muted violet (#7C5CFF) appears solely as the fill of "
    "the returning conduit; everything else is neutral graphite and near-black. "
    "Flat orthographic framing, wide horizontal composition, 70% empty space, "
    "the top 22% of the canvas completely clear and dark. "
    "Fine 35mm film grain. Photorealistic architectural product rendering, "
    "quiet institutional restraint. "
    "RENDER NO TEXT: no words, letters, numerals, labels, axis ticks, formulas, "
    "percentages or captions anywhere. Express every quantity through geometry, "
    "proportion and position only. "
    "NEVER: glowing edges, neon outlines, cyan or teal of any kind, holographic "
    "surfaces, floating cubes, network-node constellations, circuit textures, "
    "coins or currency glyphs, vaults, shields, padlocks, lens flare, light "
    "streaks, volumetric haze, particle drift, starfields, cyberpunk or gaming "
    "aesthetics, any logo or brand mark, three evenly spaced equal objects in a row."
)


def render_a5_round_trip(
    headline: str,
    deck: str,
    labels: list[str],
    *,
    out: Optional[Path] = None,
    model: str = "gemini-3.1-flash-image",
    size: tuple[int, int] = (1600, 900),
) -> Path:
    """Generate the geometry, then composite every word."""
    from pipeline.scripts.gemini_flash_image import generate_gemini_image

    out = Path(out or (OUT_DIR / "demo_a5_round_trip.png"))
    raw = out.with_name(out.stem + "_raw.png")
    generate_gemini_image(prompt=A5_PROMPT, output_path=raw,
                          project="vanna-mcp", location="global",
                          model=model, temperature=0.55)

    base = Image.open(raw).convert("RGB").resize(size, Image.Resampling.LANCZOS)
    d = ImageDraw.Draw(base)
    W, H = size
    m = int(W * 0.055)

    # Darken the top band so composited type always has its own ground rather
    # than fighting whatever the model happened to render there.
    band = Image.new("RGB", (W, int(H * 0.30)), GROUND)
    base.paste(Image.blend(base.crop((0, 0, W, int(H * 0.30))), band, 0.82), (0, 0))

    f_eyebrow = font("semibold", 15)
    f_head = font("semibold", 58)
    f_deck = font("regular", 23)
    f_label = font("semibold", 14)

    y = int(H * 0.085)
    _track(d, (m, y), "STELLAR SOROBAN · TESTNET", f_eyebrow, VIOLET_LIGHT, 2.2)

    y += 40
    for line in _wrap(d, headline, f_head, int(W * 0.62))[:3]:
        d.text((m, y), line, font=f_head, fill=INK)
        y += 68

    y += 8
    d.text((m, y), deck, font=f_deck, fill=INK_MUTED)

    # Labels along the bottom rule — six maximum, per the diagram rules.
    ly = int(H * 0.905)
    d.line([(m, ly - 22), (W - m, ly - 22)], fill=LINE, width=1)
    lx = m
    for i, lab in enumerate(labels[:3]):
        col = VIOLET_LIGHT if i == 1 else INK_FAINT
        end = _track(d, (lx, ly), lab.upper(), f_label, col, 1.8)
        lx = end + 56

    base.save(out, quality=96)
    return out


# --------------------------------------------------------------------------
# A6 — Ledger. No image model at all.
# --------------------------------------------------------------------------

def render_a6_ledger(
    headline: str,
    rows: list[tuple[str, str]],
    verdict: tuple[str, str],
    footnote: str,
    *,
    out: Optional[Path] = None,
    size: tuple[int, int] = (1600, 900),
) -> Path:
    """A worked calculation, typeset. Nothing here is generated.

    The figures must be correct, and a model cannot be trusted with a figure,
    so this archetype never reaches one. It is also the cheapest asset the
    system can produce, which matters when most posts are not architecture.
    """
    out = Path(out or (OUT_DIR / "demo_a6_ledger.png"))
    W, H = size
    img = Image.new("RGB", size, GROUND)
    d = ImageDraw.Draw(img)
    m = int(W * 0.075)

    # Documentation ground: a faint grid, nothing more.
    for x in range(0, W, 48):
        d.line([(x, 0), (x, H)], fill=(14, 14, 17), width=1)
    for y in range(0, H, 48):
        d.line([(0, y), (W, y)], fill=(14, 14, 17), width=1)

    f_eyebrow = font("semibold", 15)
    f_head = font("semibold", 52)
    f_key = font("regular", 22)
    f_val = font("semibold", 26)
    f_verdict_k = font("semibold", 20)
    f_verdict_v = font("bold", 40)
    f_foot = font("regular", 16)

    # Start lower and let the table run: the first draft put everything in the
    # top 55% and left the bottom half empty, which on a feed reads as a
    # cropped image rather than a composition.
    y = int(H * 0.155)
    _track(d, (m, y), "HEALTH FACTOR · WORKED", f_eyebrow, VIOLET_LIGHT, 2.2)

    y += 44
    for line in _wrap(d, headline, f_head, int(W * 0.74))[:2]:
        d.text((m, y), line, font=f_head, fill=INK)
        y += 62

    # The statement itself, as a table. Tabular figures, right aligned.
    y += 48
    right = W - m
    for i, (k, v) in enumerate(rows):
        d.text((m, y), k, font=f_key, fill=INK_MUTED)
        vw = d.textlength(v, font=f_val)
        d.text((right - vw, y - 3), v, font=f_val, fill=INK)
        y += 62
        if i < len(rows) - 1:
            d.line([(m, y - 10), (right, y - 10)], fill=(22, 22, 27), width=1)

    # The one violet row: the line under discussion.
    y += 16
    d.rectangle([(m - 18, y - 14), (right + 18, y + 58)], fill=(21, 17, 38))
    d.line([(m - 18, y - 14), (m - 18, y + 58)], fill=VIOLET, width=3)
    d.text((m, y + 6), verdict[0], font=f_verdict_k, fill=VIOLET_LIGHT)
    vw = d.textlength(verdict[1], font=f_verdict_v)
    d.text((right - vw, y - 2), verdict[1], font=f_verdict_v, fill=HEALTHY)

    d.text((m, int(H * 0.885)), footnote, font=f_foot, fill=INK_FAINT)

    img.save(out, quality=96)
    return out


# --------------------------------------------------------------------------
# The Vanna ground — one background, every post
# --------------------------------------------------------------------------
#
# Taken from docs.vanna.finance's own hero, read off its computed styles
# rather than eyeballed:
#
#   radial-gradient(circle, rgba(112,58,230,.50) 0%, rgba(112,58,230,.18) 32%,
#                           rgba(112,58,230,0) 65%)      <- violet
#   radial-gradient(circle, rgba(255,0,122,.45) 0%, rgba(255,0,122,.18) 30%,
#                           rgba(255,0,122,0) 65%)       <- pink
#
# The earlier design note proposed six interchangeable grounds. The founder
# overruled that: the docs hero IS the Vanna ground, and every post uses it.
# That is the correct call — the background is the one element that should not
# vary, because it is what makes ten different layouts read as one brand.
# Variety now comes from archetype, composition and subject, never from the
# backdrop.

GROUND_BASE = (9, 7, 13)
VIOLET_BLOOM = (112, 58, 230)
PINK_BLOOM = (255, 0, 122)


def _radial(size: tuple[int, int], centre: tuple[float, float],
            radius_px: float, rgb: tuple[int, int, int],
            peak: float, mid: float) -> Image.Image:
    """One docs-style radial bloom as an RGBA layer.

    Three stops, matching the CSS: `peak` at the centre, `mid` at ~31% of the
    radius, fully transparent at 65%. A plain linear falloff reads as a flat
    disc; these stops are what give the docs hero its soft shoulder.
    """
    w, h = size
    cx, cy = centre
    layer = Image.new("L", size, 0)
    px = layer.load()
    r_out = radius_px
    r_mid = radius_px * 0.31 / 0.65
    for y in range(h):
        dy2 = (y - cy) ** 2
        for x in range(0, w, 2):          # every other column, then smooth
            dist = (dy2 + (x - cx) ** 2) ** 0.5
            if dist >= r_out:
                continue
            if dist <= r_mid:
                t = dist / r_mid
                a = peak + (mid - peak) * t
            else:
                t = (dist - r_mid) / (r_out - r_mid)
                a = mid * (1 - t)
            v = int(max(0.0, min(1.0, a)) * 255)
            px[x, y] = v
            if x + 1 < w:
                px[x + 1, y] = v
    layer = layer.filter(__import__("PIL.ImageFilter", fromlist=["ImageFilter"]).GaussianBlur(6))
    out = Image.new("RGBA", size, rgb + (0,))
    out.putalpha(layer)
    return out


def vanna_ground(size: tuple[int, int] = (1600, 900), *, grid: bool = True) -> Image.Image:
    """The background. Identical on every asset, by design."""
    w, h = size
    img = Image.new("RGB", size, GROUND_BASE)

    if grid:
        d = ImageDraw.Draw(img)
        step = max(40, w // 34)
        for x in range(0, w, step):
            d.line([(x, 0), (x, h)], fill=(15, 12, 21), width=1)
        for y in range(0, h, step):
            d.line([(0, y), (w, y)], fill=(15, 12, 21), width=1)

    # Pink upper-right, violet lower centre-left — the docs hero arrangement.
    pink = _radial(size, (w * 0.78, h * 0.22), w * 0.46, PINK_BLOOM, 0.38, 0.15)
    violet = _radial(size, (w * 0.44, h * 0.86), w * 0.50, VIOLET_BLOOM, 0.42, 0.15)

    img = img.convert("RGBA")
    img = Image.alpha_composite(img, violet)
    img = Image.alpha_composite(img, pink)
    return img.convert("RGB")


def on_ground(generated: Image.Image, size: tuple[int, int] = (1600, 900)) -> Image.Image:
    """Place a model-rendered subject onto the Vanna ground.

    The subject is generated on near-black, so a per-channel lighten drops the
    ground in behind it wherever the render is dark and keeps the object
    wherever it is light. This is what guarantees the background is byte-identical
    across posts: the model never gets to decide it.
    """
    from PIL import ImageChops

    g = generated.convert("RGB").resize(size, Image.Resampling.LANCZOS)
    return ImageChops.lighter(vanna_ground(size), g)


def left_scrim(img: Image.Image, width_pct: float = 0.52,
               strength: float = 0.72) -> Image.Image:
    """Darken the left edge so composited type always has contrast.

    Every archetype sets its headline against the left margin, but what the
    model renders there varies run to run — the isolation grid spread further
    left than its prompt asked and the footnote ended up sitting on a cube.
    Rather than tune each prompt until the space happens to be clear, guarantee
    it: a soft horizontal falloff, invisible where it ends, under all
    left-aligned text.
    """
    W, H = img.size
    mask = Image.new("L", (W, 1), 0)
    px = mask.load()
    edge = int(W * width_pct)
    for x in range(W):
        px[x, 0] = int(255 * strength * (1 - x / edge) ** 1.6) if x < edge else 0
    mask = mask.resize((W, H))
    dark = Image.new("RGB", (W, H), GROUND_BASE)
    return Image.composite(dark, img.convert("RGB"), mask)

# --------------------------------------------------------------------------
# A3 — Threshold. A value held above a floor.
# --------------------------------------------------------------------------

A3_PROMPT = (
    "A single tall vertical measuring column standing on the right third of an "
    "empty dark floor. The column is dark matte graphite, precision-machined, "
    "with a narrow open channel running its full height. Inside the channel a "
    "solid pale bar sits in the UPPER portion, clearly and comfortably above a "
    "single thin horizontal reference groove cut across the lower third of the "
    "column. The space between the bar and the groove is open and visible. "
    "Everything else on the canvas is empty dark floor. "
    "Lighting: one soft key from the upper left, clinical and restrained, a "
    "long soft shadow falling left. Matte machined surfaces, no reflections. "
    "Colour: neutral graphite and near-black only. The bar is pale warm grey. "
    "NOTHING glows. "
    "Composition: flat near-orthographic, the column occupying only the right "
    "third, the left two-thirds completely empty dark floor, the top 25 percent "
    "entirely clear. "
    "Fine 35mm grain. Photorealistic precision-instrument product photography. "
    "RENDER NO TEXT: no words, letters, numerals, tick labels, scale markings, "
    "gradations, formulas or captions anywhere. "
    "NEVER: glowing edges, neon, cyan, teal, holographic surfaces, floating "
    "cubes, network nodes, circuit textures, coins, currency glyphs, vaults, "
    "shields, dial gauges, lens flare, light streaks, haze, particles, "
    "cyberpunk or gaming aesthetics, any logo or brand mark."
)


def render_a3_threshold(headline: str, deck: str, floor_label: str,
                        value_label: str, footnote: str, *,
                        out: Optional[Path] = None,
                        model: str = "gemini-3.1-flash-image",
                        reuse_raw: bool = False,
                        size: tuple[int, int] = (1600, 900)) -> Path:
    """Generated column, composited callouts, hardcoded ground."""
    from pipeline.scripts.gemini_flash_image import generate_gemini_image

    out = Path(out or (OUT_DIR / "demo_a3_threshold.png"))
    raw = out.with_name(out.stem + "_raw.png")
    if not (reuse_raw and raw.exists()):
        generate_gemini_image(prompt=A3_PROMPT, output_path=raw,
                              project="vanna-mcp", location="global",
                              model=model, temperature=0.5)

    base = left_scrim(on_ground(Image.open(raw), size))
    d = ImageDraw.Draw(base)
    W, H = size
    m = int(W * 0.065)

    f_eyebrow = font("semibold", 15)
    f_head = font("semibold", 62)
    f_deck = font("regular", 23)
    f_ann = font("semibold", 15)
    f_foot = font("regular", 15)

    y = int(H * 0.115)
    _track(d, (m, y), "HEALTH FACTOR · STELLAR SOROBAN TESTNET", f_eyebrow,
           VIOLET_LIGHT, 2.2)

    y += 44
    for line in _wrap(d, headline, f_head, int(W * 0.50))[:3]:
        d.text((m, y), line, font=f_head, fill=INK)
        y += 74

    y += 10
    for line in _wrap(d, deck, f_deck, int(W * 0.44))[:2]:
        d.text((m, y), line, font=f_deck, fill=INK_MUTED)
        y += 32

    # Two callouts, tied to the column by short rules so they read as
    # annotations rather than as a floating legend.
    # Callouts sit to the LEFT of the column, right-aligned into their rule.
    # Placed on the right they ran straight across the machined face.
    rule_end = int(W * 0.625)
    for label, ay, col in ((value_label, int(H * 0.38), HEALTHY),
                           (floor_label, int(H * 0.70), DANGER)):
        txt = label.upper()
        tw = sum(d.textlength(c, font=f_ann) + 1.6 for c in txt)
        d.line([(rule_end - 44, ay), (rule_end, ay)], fill=col, width=2)
        _track(d, (rule_end - 60 - tw, ay - 9), txt, f_ann, col, 1.6)

    d.text((m, int(H * 0.895)), footnote, font=f_foot, fill=INK_FAINT)
    base.save(out, quality=96)
    return out


# --------------------------------------------------------------------------
# A4 — Isolation Grid. Containment, as repetition with one exception.
# --------------------------------------------------------------------------

A4_PROMPT = (
    "A precise grid of sixteen identical small sealed cubes, four by four, "
    "evenly spaced with clear gaps between every unit, resting on an empty "
    "dark floor. Each cube is dark matte graphite with clean machined edges. "
    "ONE single cube, off-centre and not in the middle, is filled with a solid "
    "dull warm-red interior visible through its open face. That one cube is "
    "otherwise identical in size and shape to the rest and is NOT connected to "
    "any of them. Every other cube is closed, uniform and untouched. The gaps "
    "between units are wide and obvious. "
    "Lighting: one soft overhead key, clinical, even across the whole grid, "
    "short soft shadows. Matte surfaces, no reflections, nothing glows. "
    "Colour: neutral graphite, near-black floor, one dull warm red. No other "
    "colour anywhere. "
    "Composition: the grid occupying the lower right two-thirds at a low "
    "three-quarter angle, the upper left and the top 25 percent of the canvas "
    "completely empty dark floor. "
    "Fine 35mm grain. Photorealistic architectural product rendering, quiet "
    "institutional restraint. "
    "RENDER NO TEXT: no words, letters, numerals, labels, formulas or captions "
    "anywhere. "
    "NEVER: glowing edges, neon, cyan, teal, holographic surfaces, connecting "
    "lines or cables between units, network-node constellations, circuit "
    "textures, coins, currency glyphs, vaults, shields, padlocks, cracks "
    "spreading between units, lens flare, light streaks, haze, particles, "
    "cyberpunk or gaming aesthetics, any logo or brand mark."
)


def render_a4_isolation(headline: str, deck: str, stat_value: str,
                        stat_label: str, footnote: str, *,
                        out: Optional[Path] = None,
                        model: str = "gemini-3.1-flash-image",
                        reuse_raw: bool = False,
                        size: tuple[int, int] = (1600, 900)) -> Path:
    """Generated grid, one composited figure, hardcoded ground."""
    from pipeline.scripts.gemini_flash_image import generate_gemini_image

    out = Path(out or (OUT_DIR / "demo_a4_isolation.png"))
    raw = out.with_name(out.stem + "_raw.png")
    if not (reuse_raw and raw.exists()):
        generate_gemini_image(prompt=A4_PROMPT, output_path=raw,
                              project="vanna-mcp", location="global",
                              model=model, temperature=0.5)

    base = left_scrim(on_ground(Image.open(raw), size), 0.46, 0.66)
    d = ImageDraw.Draw(base)
    W, H = size
    m = int(W * 0.065)

    f_eyebrow = font("semibold", 15)
    f_head = font("semibold", 60)
    f_deck = font("regular", 23)
    f_stat = font("bold", 78)
    f_statlab = font("semibold", 15)
    f_foot = font("regular", 15)

    y = int(H * 0.115)
    _track(d, (m, y), "SMARTACCOUNT ISOLATION · TESTNET", f_eyebrow,
           VIOLET_LIGHT, 2.2)

    y += 44
    for line in _wrap(d, headline, f_head, int(W * 0.46))[:3]:
        d.text((m, y), line, font=f_head, fill=INK)
        y += 72

    y += 10
    for line in _wrap(d, deck, f_deck, int(W * 0.40))[:2]:
        d.text((m, y), line, font=f_deck, fill=INK_MUTED)
        y += 32

    # One figure, once, at scale — the Robinhood lesson. It sits in the empty
    # lower-left quadrant the prompt deliberately reserved.
    sy = int(H * 0.68)
    d.text((m, sy), stat_value, font=f_stat, fill=INK)
    _track(d, (m + 4, sy + 96), stat_label.upper(), f_statlab, INK_MUTED, 1.8)

    d.text((m, int(H * 0.905)), footnote, font=f_foot, fill=INK_FAINT)
    base.save(out, quality=96)
    return out
