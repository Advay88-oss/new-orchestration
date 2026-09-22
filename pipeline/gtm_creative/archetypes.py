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


def _fit(draw, text: str, weight: str, max_w: int, max_lines: int,
         start: int, minimum: int = 40):
    """Shrink the headline until it fits, rather than dropping words.

    Every archetype wrapped to a measure and then sliced `[:3]`, so a headline
    one line too long silently lost its ending — "One account defaults. The
    rest never" shipped without "know." A clipped sentence is worse than a
    smaller one, and worse still because nothing reports it.
    """
    size = start
    while size > minimum:
        f = font(weight, size)
        lines = _wrap(draw, text, f, max_w)
        if len(lines) <= max_lines:
            return f, lines, int(size * 1.18)
        size -= 3
    f = font(weight, minimum)
    return f, _wrap(draw, text, f, max_w)[:max_lines], int(minimum * 1.18)


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
    f_head = font("regular", 76)
    f_deck = font("regular", 23)
    f_label = font("semibold", 14)

    y = int(H * 0.085)
    _track(d, (m, y), "STELLAR SOROBAN · TESTNET", f_eyebrow, VIOLET_LIGHT, 2.2)

    y += 40
    f_head, _hl, _lh = _fit(d, headline, "regular", int(W * 0.52), 3,
                            f_head.size)
    for line in _hl:
        d.text((m, y), line, font=f_head, fill=INK_SOFT)
        y += _lh

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
    # The ledger was drawn on flat black with its own grid, which made it the
    # one asset that did not sit on the Vanna ground.
    img = refined_ground(size)
    d = ImageDraw.Draw(img)
    m = int(W * 0.082)

    f_eyebrow = font("semibold", 15)
    f_head = font("regular", 70)
    f_key = font("regular", 22)
    f_val = font("semibold", 26)
    f_verdict_k = font("semibold", 20)
    f_verdict_v = font("semibold", 44)
    f_foot = font("regular", 16)

    # Start lower and let the table run: the first draft put everything in the
    # top 55% and left the bottom half empty, which on a feed reads as a
    # cropped image rather than a composition.
    y = int(H * 0.155)
    _track(d, (m, y), "HEALTH FACTOR · WORKED", f_eyebrow, VIOLET_LIGHT, 2.2)

    y += 44
    f_head, _hl, _lh = _fit(d, headline, "regular", int(W * 0.74), 2,
                            f_head.size)
    for line in _hl:
        d.text((m, y), line, font=f_head, fill=INK_SOFT)
        y += _lh

    # The statement itself, as a table. Tabular figures, right aligned.
    y += 48
    right = W - m
    for i, (k, v) in enumerate(rows):
        d.text((m, y), k, font=f_key, fill=INK_MUTED)
        vw = d.textlength(v, font=f_val)
        d.text((right - vw, y - 3), v, font=f_val, fill=INK_SOFT)
        y += 82
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
# Refinement pass — the things that separate "correct" from "premium"
# --------------------------------------------------------------------------
#
# The assets were right and flat and on-brand, and still looked a tier below
# Arc, U-USDG and Robinhood Chain. Comparing them closely, the gap was never
# the subject matter. It was five things, none of which are about what the
# image depicts:
#
#   1. Type weight. The references set their largest line LIGHT, not bold. A
#      semibold headline at 58px reads as a slide; a regular headline at 80px
#      reads as a magazine. Weight down, size up.
#   2. Material. Arc's card is frosted, with one hairline edge catching light.
#      Nothing in our flat figures had any surface quality at all.
#   3. Tonality. The references sit close in value — subject barely brighter
#      than ground. Pure white on near-black is the cheapest contrast there is.
#   4. A second texture. Arc has a faint line field, U-USDG a ghosted mark.
#      One plain grid is a background; two layers at different scales is depth.
#   5. Vignette. All three darken at the edges, which is what holds the eye in
#      the middle. Ours were evenly lit corner to corner.

INK_SOFT = (228, 228, 234)          # not pure white; #FFFFFF is the tell


def _vignette(img: Image.Image, strength: float = 0.42) -> Image.Image:
    """Darken the corners. Even edge-to-edge lighting is what makes a
    composition read as a screenshot rather than as a photograph."""
    from PIL import ImageFilter

    W, H = img.size
    mask = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(mask)
    inset_x, inset_y = int(W * 0.17), int(H * 0.17)
    d.ellipse([(-inset_x, -inset_y), (W + inset_x, H + inset_y)], fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(int(min(W, H) * 0.13)))
    mask = mask.point(lambda v: int(255 - (255 - v) * strength))
    dark = Image.new("RGB", (W, H), (4, 3, 7))
    return Image.composite(img.convert("RGB"), dark, mask)


def _hairlines(img: Image.Image, opacity: int = 7) -> Image.Image:
    """A second, finer texture at a different scale from the grid.

    One grid alone reads as a background. Two layers at different frequencies
    read as depth — it is the faint line field behind the Arc card and the
    ghosted grid under the U-USDG badges.
    """
    W, H = img.size
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    step = 11
    for x in range(-H, W, step):
        d.line([(x, 0), (x + H, H)], fill=(190, 175, 255, opacity), width=1)
    return Image.alpha_composite(img.convert("RGBA"), layer).convert("RGB")


def refined_ground(size: tuple[int, int] = (1600, 900)) -> Image.Image:
    """The Vanna ground with the depth pass applied."""
    return _vignette(_hairlines(vanna_ground(size)))


def premium(img: Image.Image) -> Image.Image:
    """Apply the depth pass to a composited asset."""
    return _vignette(_hairlines(img))


# The clause that asks nano banana pro for material rather than shape alone.
# Without it the figures come back as flat silhouettes: correct, and lifeless.
MATERIAL_CLAUSE = (
    "MATERIAL AND LIGHT, restrained: every shape is a softly translucent "
    "frosted surface, not a flat cut-out. Each carries ONE hairline lighter "
    "edge along a single side where light grazes it, and a faint interior "
    "luminance that falls away toward the opposite side. Edges are crisp and "
    "true. "
    "TONALITY: keep everything close in value. The subject sits only slightly "
    "brighter than the background — a quiet, tonal, low-contrast image. Never "
    "pure white, never a hard black silhouette; high contrast reads as cheap. "
    "This is the restraint of a premium product launch graphic, not the "
    "contrast of an infographic."
)


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
    "Fine 35mm grain. " + MATERIAL_CLAUSE + " "
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

    base = premium(left_scrim(on_ground(Image.open(raw), size), 0.56, 0.82))
    d = ImageDraw.Draw(base)
    W, H = size
    m = int(W * 0.082)

    f_eyebrow = font("semibold", 15)
    f_head = font("regular", 80)
    f_deck = font("regular", 23)
    f_ann = font("semibold", 15)
    f_foot = font("regular", 15)

    y = int(H * 0.115)
    _track(d, (m, y), "HEALTH FACTOR · STELLAR SOROBAN TESTNET", f_eyebrow,
           VIOLET_LIGHT, 2.2)

    y += 44
    f_head, _hl, _lh = _fit(d, headline, "regular", int(W * 0.40), 3,
                            f_head.size)
    for line in _hl:
        d.text((m, y), line, font=f_head, fill=INK_SOFT)
        y += _lh

    y += 10
    for line in _wrap(d, deck, f_deck, int(W * 0.36))[:2]:
        d.text((m, y), line, font=f_deck, fill=INK_MUTED)
        y += 32

    # Two callouts, tied to the column by short rules so they read as
    # annotations rather than as a floating legend.
    # Callouts sit to the LEFT of the column, right-aligned into their rule.
    # Placed on the right they ran straight across the machined face.
    rule_end = int(W * 0.625)
    # Never above the text block: with a three-line headline the first callout
    # landed on top of the last line. The rule still meets the column, so a
    # nudged callout reads as an annotation rather than a collision.
    first_y = max(int(H * 0.38), y + 34)
    second_y = max(int(H * 0.70), first_y + int(H * 0.28))
    for label, ay, col in ((value_label, first_y, HEALTHY),
                           (floor_label, second_y, DANGER)):
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
    "Fine 35mm grain. " + MATERIAL_CLAUSE + " "
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

    base = premium(left_scrim(on_ground(Image.open(raw), size), 0.54, 0.84))
    d = ImageDraw.Draw(base)
    W, H = size
    m = int(W * 0.082)

    f_eyebrow = font("semibold", 15)
    f_head = font("regular", 78)
    f_deck = font("regular", 23)
    f_stat = font("regular", 104)
    f_statlab = font("semibold", 15)
    f_foot = font("regular", 15)

    y = int(H * 0.115)
    _track(d, (m, y), "SMARTACCOUNT ISOLATION · TESTNET", f_eyebrow,
           VIOLET_LIGHT, 2.2)

    y += 44
    f_head, _hl, _lh = _fit(d, headline, "regular", int(W * 0.38), 3,
                            f_head.size)
    for line in _hl:
        d.text((m, y), line, font=f_head, fill=INK_SOFT)
        y += _lh

    y += 10
    for line in _wrap(d, deck, f_deck, int(W * 0.34))[:2]:
        d.text((m, y), line, font=f_deck, fill=INK_MUTED)
        y += 32

    # One figure, once, at scale — the Robinhood lesson. It sits in the empty
    # lower-left quadrant the prompt deliberately reserved.
    sy = int(H * 0.68)
    d.text((m, sy), stat_value, font=f_stat, fill=INK_SOFT)
    _track(d, (m + 4, sy + 96), stat_label.upper(), f_statlab, INK_MUTED, 1.8)

    d.text((m, int(H * 0.905)), footnote, font=f_foot, fill=INK_FAINT)
    base.save(out, quality=96)
    return out


# --------------------------------------------------------------------------
# Flat archetypes — no 3D, no lighting, no photorealism
# --------------------------------------------------------------------------
#
# The 3D renders read as product photography: machined columns, lit cubes,
# cast shadows. Handsome, but wrong register — none of the reference posts
# are photographed, and Vanna's own documentation explains itself with flat
# figures and interface, never with rendered objects.
#
# These two are orthographic figures. The clause below is what does the work:
# an image model's default for "architecture" is an isometric hero render, so
# flatness has to be stated repeatedly and in several vocabularies at once.

FLAT_CLAUSE = (
    "STRICTLY FLAT 2D VECTOR ILLUSTRATION, drawn as a figure in technical "
    "documentation. Orthographic and face-on. "
    "ABSOLUTELY NO: three-dimensional forms, isometric or axonometric "
    "projection, perspective, depth, extrusion, thickness, bevels, rounded "
    "solids, lighting, key light, ambient occlusion, cast shadows, drop "
    "shadows, reflections, specular highlights, material shading, gloss, "
    "metal, glass, plastic, texture, photorealism, product photography, "
    "render, raytracing, floor plane, horizon, vanishing point. "
    "Use solid flat fills and thin uniform strokes only. Every shape is a "
    "silhouette with no interior shading whatsoever. Think a diagram in a "
    "technical manual or an SVG schematic, not an object in a room."
)

NEVER_CLAUSE = (
    "NEVER: glowing edges, neon, cyan, teal, holographic surfaces, gradients "
    "inside shapes, network-node constellations, circuit-board texture, coins "
    "or currency glyphs, vaults, shields, padlocks, lens flare, light streaks, "
    "haze, particles, starfields, cyberpunk or gaming aesthetics, any logo or "
    "brand mark, three evenly spaced equal objects in a row."
)

NO_TEXT_CLAUSE = (
    "RENDER NO TEXT: no words, letters, numerals, labels, axis ticks, "
    "gradations, formulas, percentages or captions anywhere on the canvas. "
    "Express every quantity and relationship through shape, proportion and "
    "position only."
)


def top_scrim(img: Image.Image, height_pct: float = 0.44,
              strength: float = 0.80) -> Image.Image:
    """Darken the top edge with a soft falloff, for type set across the width.

    `left_scrim`'s sibling. Pasting a flat darker rectangle instead, as the
    first version did, drew a hard horizontal seam across the whole image that
    read as a compositing mistake.
    """
    W, H = img.size
    mask = Image.new("L", (1, H), 0)
    px = mask.load()
    edge = int(H * height_pct)
    for y in range(H):
        px[0, y] = int(255 * strength * (1 - y / edge) ** 1.5) if y < edge else 0
    mask = mask.resize((W, H))
    dark = Image.new("RGB", (W, H), GROUND_BASE)
    return Image.composite(dark, img.convert("RGB"), mask)

# --------------------------------------------------------------------------
# A13 — Containment Figure. Nesting drawn flat.
# --------------------------------------------------------------------------

A13_PROMPT = (
    "A flat schematic figure occupying the right half of a plain very dark "
    "canvas, the left half completely empty. "
    "The figure is a set of four concentric rounded-rectangle outlines, nested "
    "one inside the next with even margins between them, like a plan view of "
    "boxes within boxes. The outermost three outlines are thin and mid-grey. "
    "The innermost rectangle is the only filled shape: a solid muted violet "
    "block. A single thin grey line runs from the innermost violet block "
    "straight out through a small gap in each surrounding outline to the "
    "figure's right edge, then turns once and returns into the same innermost "
    "block through a second gap, forming one closed circuit. "
    + FLAT_CLAUSE + " " + MATERIAL_CLAUSE + " "
    "Palette: near-black background, three greys for the outlines, exactly one "
    "muted violet for the filled block and the returning line. No other colour. "
    "Generous empty space around the figure. "
    + NO_TEXT_CLAUSE + " " + NEVER_CLAUSE
)


def render_a13_containment(headline: str, deck: str, notes: list[tuple[str, str]],
                           footnote: str, *,
                           out: Optional[Path] = None,
                           model: str = "gemini-3-pro-image",
                           reuse_raw: bool = False,
                           size: tuple[int, int] = (1600, 900)) -> Path:
    """Flat nesting figure from nano banana pro; all type composited."""
    from pipeline.scripts.gemini_flash_image import generate_gemini_image

    out = Path(out or (OUT_DIR / "demo_a13_containment.png"))
    raw = out.with_name(out.stem + "_raw.png")
    if not (reuse_raw and raw.exists()):
        generate_gemini_image(prompt=A13_PROMPT, output_path=raw,
                              project="vanna-mcp", location="global",
                              model=model, temperature=0.45)

    base = premium(left_scrim(on_ground(Image.open(raw), size), 0.54, 0.84))
    d = ImageDraw.Draw(base)
    W, H = size
    m = int(W * 0.082)

    f_eyebrow = font("semibold", 15)
    f_head = font("regular", 78)
    f_deck = font("regular", 23)
    f_note_k = font("semibold", 15)
    f_note_v = font("regular", 15)
    f_foot = font("regular", 15)

    y = int(H * 0.115)
    _track(d, (m, y), "COMPOSABILITY · STELLAR SOROBAN TESTNET", f_eyebrow,
           VIOLET_LIGHT, 2.2)

    y += 44
    f_head, _hl, _lh = _fit(d, headline, "regular", int(W * 0.37), 3,
                            f_head.size)
    for line in _hl:
        d.text((m, y), line, font=f_head, fill=INK_SOFT)
        y += _lh

    y += 12
    for line in _wrap(d, deck, f_deck, int(W * 0.34))[:2]:
        d.text((m, y), line, font=f_deck, fill=INK_MUTED)
        y += 32

    # A short key, stacked, each row a thin rule then label and value. Reads
    # as an annotation set rather than as a legend floating over the figure.
    y = int(H * 0.615)
    for label, value in notes[:3]:
        d.line([(m, y), (m + 26, y)], fill=VIOLET, width=2)
        _track(d, (m + 40, y - 9), label.upper(), f_note_k, INK, 1.4)
        d.text((m + 40, y + 12), value, font=f_note_v, fill=INK_MUTED)
        y += 62

    d.text((m, int(H * 0.905)), footnote, font=f_foot, fill=INK_FAINT)
    base.save(out, quality=96)
    return out


# --------------------------------------------------------------------------
# A14 — Comparison Figure. One variable changed, drawn flat.
# --------------------------------------------------------------------------

A14_PROMPT = (
    "A flat schematic comparison figure on a plain very dark canvas, occupying "
    "the lower two-thirds, with the top third completely empty. "
    "LEFT SIDE: one single large plain rectangle outline, undivided, SPLIT "
    "APART by a jagged break: an irregular zigzag crack with sharp angular "
    "turns running diagonally from the top edge to the bottom edge, cutting "
    "the rectangle into two separated pieces that have visibly shifted away "
    "from each other, like a broken pane. The crack is muted dull red. "
    "It must read as a FRACTURE, not as a graph: it is NOT a line chart, NOT a "
    "trend line, NOT a data series, NOT a rising or falling plot, and it must "
    "not run left-to-right along the lower half. "
    "RIGHT SIDE: twelve small separate square outlines in an even grid, each "
    "one clearly detached from its neighbours with visible gaps, none touching "
    "and none connected by any line. Exactly one of the twelve squares is "
    "filled solid muted dull red; the other eleven are plain grey outlines, "
    "unmarked and intact. "
    "A single thin vertical grey rule separates the left and right halves. "
    + FLAT_CLAUSE + " " + MATERIAL_CLAUSE + " "
    "Palette: near-black background, mid-grey outlines, exactly one muted dull "
    "red. No violet, no other colour. Even weight to both halves. "
    + NO_TEXT_CLAUSE + " " + NEVER_CLAUSE
)


def render_a14_comparison(headline: str, deck: str,
                          left_label: str, right_label: str,
                          footnote: str, *,
                          out: Optional[Path] = None,
                          model: str = "gemini-3-pro-image",
                          reuse_raw: bool = False,
                          size: tuple[int, int] = (1600, 900)) -> Path:
    """Flat split comparison. Type runs across the reserved top third."""
    from pipeline.scripts.gemini_flash_image import generate_gemini_image

    out = Path(out or (OUT_DIR / "demo_a14_comparison.png"))
    raw = out.with_name(out.stem + "_raw.png")
    if not (reuse_raw and raw.exists()):
        generate_gemini_image(prompt=A14_PROMPT, output_path=raw,
                              project="vanna-mcp", location="global",
                              model=model, temperature=0.45)

    # No left scrim here: this archetype reserves the TOP, not the left, so a
    # left falloff would darken half the comparison it is meant to show.
    base = premium(top_scrim(on_ground(Image.open(raw), size), 0.46, 0.86))
    W, H = size
    d = ImageDraw.Draw(base)
    m = int(W * 0.082)

    f_eyebrow = font("semibold", 15)
    f_head = font("regular", 76)
    f_deck = font("regular", 23)
    f_col = font("semibold", 15)
    f_foot = font("regular", 15)

    y = int(H * 0.085)
    _track(d, (m, y), "RISK CONTAINMENT · STELLAR SOROBAN TESTNET", f_eyebrow,
           VIOLET_LIGHT, 2.2)

    y += 42
    f_head, _hl, _lh = _fit(d, headline, "regular", int(W * 0.70), 2,
                            f_head.size)
    for line in _hl:
        d.text((m, y), line, font=f_head, fill=INK_SOFT)
        y += _lh

    y += 6
    d.text((m, y), deck, font=f_deck, fill=INK_MUTED)

    # Column headings sit inside the scrimmed band, above the figure, each on
    # its own short rule. Placed lower they landed on top of the halves they
    # were meant to name.
    cy = int(H * 0.355)
    for lx, label, col in ((m, left_label, DANGER),
                           (int(W * 0.525), right_label, HEALTHY)):
        d.line([(lx, cy - 14), (lx + 30, cy - 14)], fill=col, width=2)
        _track(d, (lx, cy), label.upper(), f_col, col, 1.8)

    # The footnote joins the top block: the figure bleeds to the bottom edge,
    # so anything set down there is buried under it.
    d.text((m, int(H * 0.262)), footnote, font=f_foot, fill=INK_FAINT)
    base.save(out, quality=96)
    return out


# --------------------------------------------------------------------------
# A7 — Composition. What something is made of, drawn not generated.
# --------------------------------------------------------------------------

def render_a7_composition(headline: str, deck: str,
                          segments: list[tuple[str, float, tuple[int, int, int]]],
                          total_label: str, footnote: str, *,
                          out: Optional[Path] = None,
                          size: tuple[int, int] = (1600, 900)) -> Path:
    """A proportional bar. No model: a bar is arithmetic, and arithmetic
    rendered by an image model is arithmetic you cannot trust.

    `segments` is (label, weight, colour); weights are normalised, so the bar
    always sums to the width and the drawing cannot disagree with the numbers
    that sit beside it.
    """
    out = Path(out or (OUT_DIR / "demo_a7_composition.png"))
    W, H = size
    base = refined_ground(size)
    d = ImageDraw.Draw(base)
    m = int(W * 0.082)

    f_eyebrow = font("semibold", 15)
    f_head = font("regular", 76)
    f_deck = font("regular", 23)
    f_seg = font("semibold", 16)
    f_pct = font("semibold", 32)
    f_total = font("semibold", 15)
    f_foot = font("regular", 15)

    y = int(H * 0.115)
    _track(d, (m, y), "RECOGNISED COLLATERAL · STELLAR SOROBAN TESTNET",
           f_eyebrow, VIOLET_LIGHT, 2.2)

    y += 44
    f_head, _hl, _lh = _fit(d, headline, "regular", int(W * 0.52), 2,
                            f_head.size)
    for line in _hl:
        d.text((m, y), line, font=f_head, fill=INK_SOFT)
        y += _lh

    y += 8
    for line in _wrap(d, deck, f_deck, int(W * 0.56))[:2]:
        d.text((m, y), line, font=f_deck, fill=INK_MUTED)
        y += 32

    # One horizontal bar, full measure. Segments are separated by a gap rather
    # than a stroke, so nothing needs a border and the proportions stay honest.
    total = sum(max(0.0, s[1]) for s in segments) or 1.0
    bar_y = int(H * 0.545)
    bar_h = 74
    gap = 6
    usable = (W - 2 * m) - gap * (len(segments) - 1)
    x = m
    for label, weight, col in segments:
        w = int(usable * (max(0.0, weight) / total))
        d.rectangle([(x, bar_y), (x + w, bar_y + bar_h)], fill=col)
        x += w + gap

    # Labels sit under their own segment, left-aligned to it — a key off to
    # the side makes the reader match colours instead of reading the bar.
    x = m
    ly = bar_y + bar_h + 26
    for label, weight, col in segments:
        w = int(usable * (max(0.0, weight) / total))
        pct = str(int(round(weight / total * 100))) + "%"
        d.text((x, ly), pct, font=f_pct, fill=col)
        for i, line in enumerate(_wrap(d, label, f_seg, max(w, 150))[:2]):
            d.text((x, ly + 42 + i * 22), line, font=f_seg, fill=INK_MUTED)
        x += w + gap

    _track(d, (m, bar_y - 30), total_label.upper(), f_total, INK_FAINT, 1.8)
    d.text((m, int(H * 0.905)), footnote, font=f_foot, fill=INK_FAINT)

    base.save(out, quality=96)
    return out


# --------------------------------------------------------------------------
# A8 — Sequence. Something that happens in order, drawn flat.
# --------------------------------------------------------------------------

A8_PROMPT = (
    "A flat schematic timeline figure across the lower half of a plain very "
    "dark canvas, with the top half completely empty. "
    "One long thin horizontal grey baseline runs most of the width. Four small "
    "square markers sit ON the baseline at UNEVEN intervals — the first two "
    "close together near the left, the third after a wider gap, the fourth "
    "after a wider gap still. The first three markers are plain grey outlines. "
    "The fourth and final marker is a solid filled muted violet square. "
    "Below the baseline, a second thin line traces a shallow descent from left "
    "to right that levels off flat before reaching the right edge, staying "
    "clearly above a short dashed horizontal grey rule drawn near the bottom. "
    "The descent line never touches the dashed rule. "
    + FLAT_CLAUSE + " " + MATERIAL_CLAUSE + " "
    "Palette: near-black background, mid-grey lines and outlines, exactly one "
    "muted violet for the final marker. No other colour. "
    + NO_TEXT_CLAUSE + " " + NEVER_CLAUSE
)


def render_a8_sequence(headline: str, deck: str, steps: list[tuple[str, str]],
                       footnote: str, *,
                       out: Optional[Path] = None,
                       model: str = "gemini-3-pro-image",
                       reuse_raw: bool = False,
                       size: tuple[int, int] = (1600, 900)) -> Path:
    """Flat timeline from nano banana pro; steps composited along the top."""
    from pipeline.scripts.gemini_flash_image import generate_gemini_image

    out = Path(out or (OUT_DIR / "demo_a8_sequence.png"))
    raw = out.with_name(out.stem + "_raw.png")
    if not (reuse_raw and raw.exists()):
        generate_gemini_image(prompt=A8_PROMPT, output_path=raw,
                              project="vanna-mcp", location="global",
                              model=model, temperature=0.45)

    base = premium(top_scrim(on_ground(Image.open(raw), size), 0.58, 0.86))
    W, H = size
    d = ImageDraw.Draw(base)
    m = int(W * 0.082)

    f_eyebrow = font("semibold", 15)
    f_head = font("regular", 76)
    f_deck = font("regular", 23)
    f_step_n = font("bold", 15)
    f_step_k = font("semibold", 16)
    f_step_v = font("regular", 15)
    f_foot = font("regular", 15)

    y = int(H * 0.105)
    _track(d, (m, y), "DEFENSIVE REBALANCING · STELLAR SOROBAN TESTNET",
           f_eyebrow, VIOLET_LIGHT, 2.2)

    y += 42
    f_head, _hl, _lh = _fit(d, headline, "regular", int(W * 0.70), 2,
                            f_head.size)
    for line in _hl:
        d.text((m, y), line, font=f_head, fill=INK_SOFT)
        y += _lh

    y += 6
    d.text((m, y), deck, font=f_deck, fill=INK_MUTED)

    # Four steps as columns in the scrimmed band, so the figure beneath reads
    # as the same sequence rather than as a separate chart.
    cols = 4
    col_w = (W - 2 * m) // cols
    sy = int(H * 0.365)
    for i, (title, sub) in enumerate(steps[:cols]):
        cx = m + i * col_w
        col = VIOLET_LIGHT if i == cols - 1 else INK_FAINT
        d.line([(cx, sy - 16), (cx + 26, sy - 16)], fill=col, width=2)
        _track(d, (cx, sy), ("0" + str(i + 1)), f_step_n, col, 1.4)
        for j, line in enumerate(_wrap(d, title, f_step_k, col_w - 40)[:2]):
            d.text((cx, sy + 26 + j * 22), line, font=f_step_k,
                   fill=INK if i == cols - 1 else INK_MUTED)
        d.text((cx, sy + 74), sub, font=f_step_v, fill=INK_FAINT)

    d.text((m, int(H * 0.925)), footnote, font=f_foot, fill=INK_FAINT)
    base.save(out, quality=96)
    return out
