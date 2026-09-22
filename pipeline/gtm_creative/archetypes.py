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
