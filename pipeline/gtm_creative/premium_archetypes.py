"""Brand posters, not engineering diagrams.

The existing archetypes render schematics: a figure on the left, a diagram on
the right, a footnote underneath. They are honest and they are legible, and
they read like a slide from an internals deck. Held next to what good crypto
brands actually post — a Robinhood Chain metric card, a Uniswap token
announcement, an Arc Portal product shot — the difference is not polish, it is
*kind*. Those are posters. One idea, enormous, with brand furniture around it.

Three patterns worth having, taken from those references rather than invented:

  **Hero Metric** — one number at enormous scale, a two-line descriptor, and a
  decorative corner motif. Robinhood's "$20B / Volume on Uniswap Protocol".
  The number is the whole composition.

  **Announcement** — a bordered partner pill, a large term set as a wordmark,
  and a subhead with exactly one accent-coloured keyword. Uniswap's "U-USDG /
  LIVE ON ROBINHOOD CHAIN NOW". Status, not explanation.

  **Product Card** — a question as the headline and a glass UI card carrying a
  real value below it. Arc Portal's "Want cirBTC on Arc?" over a transfer
  card. It shows the product doing the thing.

The division of labour is the one that already works here: the image model
renders only the field — gradient bloom, soft glass plate, ornament — with no
text at all, and every word, rule, pill and chip is composited afterwards by
PIL with the exact strings passed in. That is why the references have perfect
type and why these can too.
"""
from __future__ import annotations

import math
import re
from pathlib import Path
from typing import Optional

from PIL import Image, ImageChops, ImageDraw, ImageFilter

from pipeline.gtm_creative.brand import logo as _logo, paste_logo
from pipeline.gtm_creative.archetypes import (
    DANGER, GROUND, HEALTHY, INK, INK_FAINT, INK_MUTED, LINE, OUT_DIR,
    SURFACE, SURFACE_2, VIOLET, VIOLET_LIGHT, _fit, _track, font, premium,
    vanna_ground,
)

# The field prompts ask for atmosphere only. No shapes that carry meaning, so
# the model cannot contradict the argument the type is making.
FIELD_METRIC = (
    "A plain very dark near-black field, empty, with one soft wide bloom of "
    "deep violet light low and slightly left of centre, and a fainter cooler "
    "bloom near the upper right corner. The centre of the frame is clean and "
    "unobstructed. Very fine even film grain across the whole image.\n\n"
    "RENDER NO TEXT and NO OBJECTS: no words, letters, numerals, shapes, "
    "icons, diagrams, lines, grids, logos or figures of any kind. This is a "
    "background wash only.\n\n"
    "NEVER: three-dimensional rendering, isometric views, photorealism, "
    "product shots, glowing edges, neon, cyan, teal, holograms, network "
    "nodes, circuit textures, coins, currency glyphs, vaults, shields, lens "
    "flare, light streaks, particles, starfields, cyberpunk aesthetics."
)

FIELD_ANNOUNCE = (
    "A plain very dark field with one broad warm bloom sweeping from the "
    "lower right corner toward the centre, fading to near-black at the left "
    "edge. A second cooler violet bloom sits behind it at the top right. The "
    "left half of the frame is dark, clean and unobstructed. Very fine even "
    "film grain.\n\n"
    "RENDER NO TEXT and NO OBJECTS: no words, letters, numerals, shapes, "
    "icons, diagrams, lines, grids, logos or figures of any kind. This is a "
    "background wash only.\n\n"
    "NEVER: three-dimensional rendering, isometric views, photorealism, "
    "product shots, glowing edges, neon, cyan, teal, holograms, network "
    "nodes, circuit textures, coins, currency glyphs, lens flare, light "
    "streaks, particles, cyberpunk aesthetics."
)

FIELD_CARD = (
    "A plain deep violet-to-near-black field, darkest at the top left and "
    "softly luminous toward the lower right, with a very faint regular "
    "pattern of small evenly spaced plus marks across the upper area, barely "
    "visible. The lower centre of the frame is clean and unobstructed. Very "
    "fine even film grain.\n\n"
    "RENDER NO TEXT: no words, letters, numerals, labels or captions "
    "anywhere. No icons, logos, diagrams or figures.\n\n"
    "RENDER NO USER INTERFACE: no rounded rectangles, cards, panels, bars, "
    "segmented strips, progress indicators, tabs or windows. Every one of "
    "those is composited afterwards, and a drawn one becomes a second, "
    "broken copy of a real element.\n\n"
    "NEVER: three-dimensional rendering, isometric views, photorealism, "
    "product shots, glowing edges, neon, cyan, teal, holograms, network "
    "nodes, circuit textures, coins, currency glyphs, lens flare, light "
    "streaks, particles, cyberpunk aesthetics."
)


def _field(prompt: str, out_raw: Path, size: tuple[int, int],
           model: str) -> Image.Image:
    """Render the background, or fall back to the deterministic ground.

    A field is atmosphere. If the model is unavailable the poster should still
    be made — the type carries it — so this degrades to `vanna_ground()`
    rather than failing the render.
    """
    # The Vanna ground is the base, always. Asking the model for the whole
    # field produced a near-black frame with none of the brand gradient — the
    # asset stopped looking like Vanna. The model now supplies texture and
    # atmosphere on top of the real docs.vanna.finance bloom, blended, so the
    # brand colour is guaranteed and the model can only enrich it.
    ground = vanna_ground(size).convert("RGB")
    try:
        from pipeline.scripts.gemini_flash_image import generate_gemini_image

        # The subject is deliberately NOT sent. A field prompt that ends
        # "...and the subject is isolated credit accounts" is a request to
        # draw isolated credit accounts, and the model obliged: spheres,
        # panels, node graphs, every one of them competing with the card that
        # actually carries the argument. The poster's meaning is carried by
        # the composited type. The field only has to be light.
        generate_gemini_image(prompt=prompt,
                              output_path=out_raw, project="vanna-mcp",
                              location="global", model=model, temperature=0.6)
        # Luminance only. Told not to use warm colour, the model still put an
        # amber sphere in the middle of three posters in one batch — a prompt
        # is a request and the palette is not negotiable. Stripping chroma
        # here means the model decides light, structure and grain, and the
        # Vanna ground decides every colour in the frame. There is no render
        # it can return that takes the poster off-palette.
        texture = Image.open(out_raw).convert("L").convert("RGB").resize(
            size, Image.Resampling.LANCZOS)
        # And low-passed, which is the part that is not a request. Told nine
        # different ways to render no objects, the model kept returning
        # spheres, rounded panels and node graphs, because "draw nothing" is
        # not a thing an image model can be relied on to do. A blur this wide
        # cannot preserve an edge, so whatever it drew arrives as a soft bloom
        # of light. There is no render it can return that puts an object on
        # the poster.
        texture = texture.filter(
            ImageFilter.GaussianBlur(int(min(size) * 0.06)))
        # Screen-style lift: the model's light adds to the ground rather than
        # replacing it, so a dark render cannot flatten the gradient away.
        # Now that the texture is pure light, it can carry more weight
        # without competing: there is nothing in it left to compete with.
        return Image.blend(ground, ImageChops.screen(ground, texture), 0.50)
    except Exception:                               # noqa: BLE001 — boundary
        return ground


def _fit_width(d: ImageDraw.ImageDraw, text: str, weight: str, max_w: int,
               start: int, minimum: int = 24):
    """Shrink until the text actually fits the width, not just the line count.

    `_fit` stops when the wrap produces few enough lines — but a single long
    word ("SmartAccounts") can never be wrapped, so it always reports one line
    and the loop exits at full size. The term then overran its column and ran
    under the badges. This measures pixels.
    """
    size = start
    while size > minimum:
        f = font(weight, size)
        if d.textlength(text, font=f) <= max_w:
            return f
        size -= 2
    return font(weight, minimum)


def pick_variant(seed: str, count: int) -> int:
    """A stable variant for a run, different across runs.

    Hashed rather than random so a re-render of the same run reproduces the
    same asset — a run is a record, and regenerating it should not silently
    produce a different picture.
    """
    if count <= 1:
        return 0
    h = 0
    for ch in str(seed or "vanna"):
        h = (h * 131 + ord(ch)) & 0xFFFFFFFF
    return h % count


def _plate(img: Image.Image, box: tuple[int, int, int, int], *,
           radius: int = 28, fill=(255, 255, 255, 12),
           border=(255, 255, 255, 46), width: int = 2,
           scrim: float = 0.0) -> None:
    """A glass panel: a translucent fill with a bright hairline edge.

    Drawn on an RGBA overlay and alpha-composited so the field shows through,
    which is what makes it read as glass rather than as a grey box.

    `scrim` lays a soft darkening under the panel first. Glass is transparent
    by definition, so whatever the image model happened to render behind the
    card came through it — one poster put a bright sphere directly under the
    figure and the number went grey. The panel now carries its own floor, so
    the value's contrast does not depend on what the field did that run.
    """
    if scrim > 0:
        # A 13px pad was enough to floor the panel's own interior and nothing
        # more. The model then drew rounded panels of its own directly against
        # the card's top edge and they read as a second, broken copy of it.
        # The halo reaches far enough past the card to put whatever is beside
        # it into shadow, so the composited panel is unambiguously the only
        # real one in the frame.
        pad = max(24, int((box[3] - box[1]) * 0.55))
        shade = Image.new("RGBA", img.size, (0, 0, 0, 0))
        ds = ImageDraw.Draw(shade)
        ds.rounded_rectangle(
            (box[0] - pad, box[1] - pad, box[2] + pad, box[3] + pad),
            radius=radius + pad, fill=(7, 5, 12, int(255 * min(1.0, scrim))))
        shade = shade.filter(ImageFilter.GaussianBlur(int(pad * 0.8)))
        img.paste(Image.alpha_composite(img.convert("RGBA"), shade).convert("RGB"),
                  (0, 0))

    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    d.rounded_rectangle(box, radius=radius, fill=fill, outline=border, width=width)
    img.paste(Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB"), (0, 0))


def _type_scrim(img: Image.Image, box: tuple[float, float, float, float], *,
                strength: float = 0.52) -> None:
    """Guarantee the headline has something dark behind it.

    The field prompt forbids objects and the model draws them anyway — one
    render put a sphere behind the first two words, another ran a horizontal
    band through the second line. Tuning the prompt until the collision stops
    happening is not a fix, because the next render is a new roll. This is a
    floor: a wide, heavily feathered darkening under the type, invisible as an
    edge, so contrast does not depend on what the model decided to draw.
    """
    x0, y0, x1, y1 = box
    h = max(1.0, y1 - y0)
    pad_x, pad_y = h * 0.42, h * 0.26
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(layer).rounded_rectangle(
        (x0 - pad_x, y0 - pad_y, x1 + pad_x, y1 + pad_y),
        radius=int(h * 0.4), fill=(7, 5, 12, int(255 * min(1.0, strength))))
    layer = layer.filter(ImageFilter.GaussianBlur(int(max(20.0, pad_x * 0.9))))
    img.paste(Image.alpha_composite(img.convert("RGBA"), layer).convert("RGB"),
              (0, 0))


def _pill(d: ImageDraw.ImageDraw, xy, text: str, f, *, pad=(18, 10),
          fg=INK, border=(90, 90, 104)) -> int:
    """A bordered capsule — the partner-lockup device from the references."""
    x, y = xy
    tw = d.textlength(text, font=f)
    h = f.size + pad[1] * 2
    d.rounded_rectangle([(x, y), (x + tw + pad[0] * 2, y + h)],
                        radius=h // 2, outline=border, width=2)
    d.text((x + pad[0], y + pad[1]), text, font=f, fill=fg)
    return int(x + tw + pad[0] * 2)


def _corner_motif(d: ImageDraw.ImageDraw, size: tuple[int, int], *,
                  inset: int, cell: int, colour=(255, 255, 255)) -> None:
    """The dotted corner brackets Robinhood frames its metric cards with.

    A decorative device, deliberately not load-bearing: it frames the number
    without adding a claim.
    """
    W, H = size
    pattern = [(0, 0), (1, 0), (2, 0), (0, 1), (0, 2), (2, 2), (3, 0), (0, 3)]
    for cx, cy, sx, sy in ((inset, inset, 1, 1), (W - inset, inset, -1, 1),
                           (inset, H - inset, 1, -1), (W - inset, H - inset, -1, -1)):
        for gx, gy in pattern:
            x = cx + sx * gx * cell * 2
            y = cy + sy * gy * cell * 2
            x0, y0 = min(x, x + sx * cell), min(y, y + sy * cell)
            d.rectangle([(x0, y0), (x0 + cell, y0 + cell)], fill=colour)


# --------------------------------------------------------------------------
# P1 — Hero Metric
# --------------------------------------------------------------------------

def render_p1_hero_metric(eyebrow: str, metric: str, descriptor: str, *,
                          subject: str = "",
                          variant_seed: str = "",
                          out: Optional[Path] = None,
                          model: str = "gemini-3.1-flash-image",
                          size: tuple[int, int] = (1200, 1200)) -> Path:
    """One number, enormous, framed. Square by default — it is a metric card."""
    out = Path(out or (OUT_DIR / "demo_p1_hero_metric.png"))
    raw = out.with_name(out.stem + "_raw.png")
    base = _field(FIELD_METRIC, raw, size, model)
    base = premium(base)
    d = ImageDraw.Draw(base)
    W, H = size

    v = pick_variant(variant_seed, 3)
    m = int(W * 0.085)
    centred = v == 0

    # v2 swaps the corner brackets for a single rule above the metric: the
    # same card without the ornament, so consecutive metric posts differ.
    if v != 2:
        _corner_motif(d, size, inset=int(W * 0.055), cell=max(6, W // 150))

    def place(text, f, y, fill, track=None):
        if track is not None:
            w = sum(d.textlength(c, font=f) + track for c in text)
            x = (W - w) / 2 if centred else m
            _track(d, (x, y), text, f, fill, track)
            return
        w = d.textlength(text, font=f)
        d.text(((W - w) / 2 if centred else m, y), text, font=f, fill=fill)

    # Wordmark. Without it the poster carried no identity at all — the
    # eyebrow names the context, not who is speaking.
    lh_ = int(H * 0.042)
    lw_ = (_logo(lh_).width if _logo(lh_) else 0)
    # Clear of the corner bracket. At 0.10 the mark's top edge sat against
    # the bracket's lowest cell and the two read as one cramped cluster.
    ly_ = int(H * (0.135 if v != 2 else 0.10))
    paste_logo(base, ((W - lw_) // 2 if centred else m, ly_), lh_)
    d = ImageDraw.Draw(base)

    ey = int(H * 0.30) if v != 2 else int(H * 0.24)
    f_eye = font("semibold", int(W * 0.026))
    # The wordmark above already says Vanna; a director that also opens the
    # eyebrow with it prints the name twice.
    eb = re.sub(r"^\s*vanna(?:'s)?\s*[·\-–|:]?\s*", "",
                str(eyebrow), flags=re.I).strip() or str(eyebrow)
    place(eb.upper(), f_eye, ey, VIOLET_LIGHT, track=2.4)

    my = ey + int(H * 0.06)
    if v == 2:
        ry = my - int(H * 0.025)
        d.line([(m, ry), (m + int(W * 0.14), ry)], fill=VIOLET_LIGHT, width=3)

    # The metric is the composition: set as large as it fits on one line.
    f_m = _fit_width(d, metric, "semibold", int(W * (0.80 if centred else 0.82)),
                     int(W * 0.26), minimum=int(W * 0.07))
    place(metric, f_m, my, INK)

    f_desc = font("regular", int(W * 0.046))
    dy = my + int(f_m.size * 1.12)
    f_desc, dlines, dlh = _fit(d, descriptor, "regular", int(W * 0.72), 2,
                               f_desc.size, minimum=int(W * 0.028))
    for line in dlines:
        place(line, f_desc, dy, INK_MUTED)
        dy += dlh

    base.save(out, quality=96)
    return out


# --------------------------------------------------------------------------
# P2 — Announcement
# --------------------------------------------------------------------------

def render_p2_announcement(term: str, status_prefix: str, status_accent: str,
                           status_suffix: str, partners: list[str], *,
                           subject: str = "",
                           variant_seed: str = "",
                           footnote: str = "",
                           out: Optional[Path] = None,
                           model: str = "gemini-3.1-flash-image",
                           size: tuple[int, int] = (1600, 900)) -> Path:
    """A status announcement: partner pill, large term, one accent keyword."""
    out = Path(out or (OUT_DIR / "demo_p2_announcement.png"))
    raw = out.with_name(out.stem + "_raw.png")
    base = _field(FIELD_ANNOUNCE, raw, size, model)
    base = premium(base)
    d = ImageDraw.Draw(base)
    W, H = size
    m = int(W * 0.065)

    # Variant decides which side the badges take, so consecutive
    # announcements are not the same picture with different words.
    v = pick_variant(variant_seed, 2)
    r = int(H * 0.19)
    if v == 0:
        cx, cy = int(W * 0.74), int(H * 0.46)
        text_x = m
        text_w = int(cx - r - m - W * 0.04)
    else:
        cx, cy = int(W * 0.24), int(H * 0.46)
        # The second badge is offset right by r*0.95, so the column has to
        # clear ITS edge, not the first badge's. Measuring only the first left
        # the term overlapping by ~50px.
        text_x = int(cx + int(r * 0.95) + r + W * 0.045)
        text_w = int(W - text_x - m)

    # Partner lockup. Names are set as type rather than fetched as logos: a
    # third party's mark is theirs, and an invented one is worse.
    paste_logo(base, (text_x, int(H * 0.045)), int(H * 0.055))
    d = ImageDraw.Draw(base)

    if partners:
        f_p = font("semibold", 20)
        label = "  ×  ".join(str(p) for p in partners[:3])
        _pill(d, (text_x, int(H * 0.11)), label, f_p)

    # The badges occupy the right of the frame, so the type column is what is
    # left of them. Measured, not guessed: the term and the status line were
    # fitted to 0.62W and to nothing respectively, and both ran underneath the
    # badges.

    f_term = _fit_width(d, term, "semibold", text_w, int(W * 0.10),
                        minimum=int(W * 0.030))
    ty = int(H * 0.34)
    d.text((text_x, ty), term, font=f_term, fill=INK)

    # The status line: exactly one coloured keyword, drawn in three runs so the
    # accent is a word rather than a highlight box. Shrunk until all three runs
    # fit the same column.
    runs = [(status_prefix + " ", INK), (status_accent, HEALTHY),
            (" " + status_suffix, INK)]
    runs = [(t.upper(), c) for t, c in runs if t.strip()]
    s_size = int(W * 0.033)
    while s_size > 14:
        f_s = font("semibold", s_size)
        if sum(d.textlength(t, font=f_s) for t, _ in runs) <= text_w:
            break
        s_size -= 2
    f_s = font("semibold", s_size)

    sy = ty + int(f_term.size * 1.22)
    x = text_x
    for text, col in runs:
        d.text((x, sy), text, font=f_s, fill=col)
        x += d.textlength(text, font=f_s)

    # Two overlapping token badges, right — the device both Uniswap posts use.
    for i, (ox, oy, ring) in enumerate(((0, -int(r * 0.55), VIOLET_LIGHT),
                                        (int(r * 0.95), int(r * 0.55), HEALTHY))):
        box = (cx + ox - r, cy + oy - r, cx + ox + r, cy + oy + r)
        overlay = Image.new("RGBA", size, (0, 0, 0, 0))
        od = ImageDraw.Draw(overlay)
        od.ellipse(box, fill=(10, 10, 14, 235), outline=ring + (150,), width=3)
        base.paste(Image.alpha_composite(base.convert("RGBA"), overlay).convert("RGB"), (0, 0))
        d = ImageDraw.Draw(base)
        # A single initial, set — not a logo.
        glyph = (partners[i] if i < len(partners) else term)[:1].upper()
        f_g = font("semibold", int(r * 0.85))
        gx0, gy0, gx1, gy1 = d.textbbox((0, 0), glyph, font=f_g)
        d.text((cx + ox - (gx1 - gx0) / 2 - gx0,
                cy + oy - (gy1 - gy0) / 2 - gy0), glyph, font=f_g, fill=ring)

    if footnote:
        d.text((text_x, int(H * 0.88)), footnote, font=font("regular", 16),
               fill=INK_FAINT)

    base.save(out, quality=96)
    return out


# --------------------------------------------------------------------------
# P3 — Product Card
# --------------------------------------------------------------------------

def _p3_chip(base: Image.Image, chip: str, chip_note: str,
             right: int, top: int) -> None:
    """The token capsule, right-aligned to `right` with its top at `top`."""
    d = ImageDraw.Draw(base)
    # A fixed 64px capsule fitted the name alone; with a note under it the
    # second line was set at +38 and its descenders crossed the bottom edge.
    # The capsule is sized from what it has to hold.
    f_c = font("semibold", 22)
    f_n = font("regular", 15)
    chip_h = 78 if chip_note else 64
    text_w = max(d.textlength(chip, font=f_c),
                 d.textlength(chip_note, font=f_n) if chip_note else 0)
    chip_w = int(text_w) + 96
    chx = right - chip_w
    _plate(base, (chx, top, chx + chip_w, top + chip_h), radius=chip_h // 2,
           fill=(255, 255, 255, 18), border=(255, 255, 255, 60))
    d = ImageDraw.Draw(base)
    dot = 40
    dy = top + (chip_h - dot) // 2
    d.ellipse([(chx + 12, dy), (chx + 12 + dot, dy + dot)],
              fill=(10, 10, 14), outline=VIOLET_LIGHT, width=2)
    g = chip[:1].upper()
    gw = d.textlength(g, font=font("semibold", 22))
    d.text((chx + 12 + dot / 2 - gw / 2, dy + 8), g, font=font("semibold", 22),
           fill=VIOLET_LIGHT)
    if chip_note:
        d.text((chx + 64, top + 16), chip, font=f_c, fill=INK)
        d.text((chx + 64, top + 45), chip_note, font=f_n, fill=INK_FAINT)
    else:
        d.text((chx + 64, top + 20), chip, font=f_c, fill=INK)


def render_p3_product_card(wordmark: str, question: str, card_label: str,
                           card_value: str, card_sub: str, chip: str, *,
                           subject: str = "",
                           variant_seed: str = "",
                           chip_note: str = "",
                           out: Optional[Path] = None,
                           model: str = "gemini-3.1-flash-image",
                           size: tuple[int, int] = (1600, 900)) -> Path:
    """A question, then the product answering it in a glass card.

    Four compositions share one ground, one mark and one palette, which is the
    point: a family, not four unrelated posters. Two centred layouts would
    have been a template with the words swapped, and the asymmetric and banner
    variants are what stop a feed of these from looking like one image posted
    repeatedly.
    """
    out = Path(out or (OUT_DIR / "demo_p3_product_card.png"))
    raw = out.with_name(out.stem + "_raw.png")
    base = _field(FIELD_CARD, raw, size, model)
    base = premium(base)
    d = ImageDraw.Draw(base)
    W, H = size
    m3 = int(W * 0.085)

    v = pick_variant(variant_seed, 4)
    centred = v in (0, 3)

    # The mark sits centre-top over a centred composition and to the left over
    # a left-set one; a centred logo above left-aligned type reads as an error.
    lh3 = int(H * 0.055)
    lw3 = (_logo(lh3).width if _logo(lh3) else 0)
    paste_logo(base, (((W - lw3) // 2) if centred else m3, int(H * 0.06)), lh3)
    d = ImageDraw.Draw(base)

    if v == 2:
        # Split: question holds the left column, the card answers on the right.
        q_max, q_y, q_start = int(W * 0.40), int(H * 0.40), int(W * 0.046)
    elif v == 3:
        # Banner: the question is the whole upper half, the card a slim base.
        q_max, q_y, q_start = int(W * 0.80), int(H * 0.22), int(W * 0.058)
    else:
        q_max = int(W * (0.74 if centred else 0.70))
        q_y, q_start = int(H * 0.185), int(W * 0.055)

    f_q, qlines, qlh = _fit(d, question, "regular", q_max, 2, q_start,
                            minimum=int(W * 0.028))
    # Measured first so the scrim can be laid under the block, then set.
    placed: list[tuple[float, float, float]] = []
    qy = q_y
    for line in qlines:
        lw = d.textlength(line, font=f_q)
        placed.append(((W - lw) / 2 if centred else m3, qy, lw))
        qy += qlh
    if placed:
        _type_scrim(base, (min(x for x, _, _ in placed),
                           placed[0][1],
                           max(x + w for x, _, w in placed),
                           placed[-1][1] + qlh))
        d = ImageDraw.Draw(base)
        for (x, y, _), line in zip(placed, qlines):
            d.text((x, y), line, font=f_q, fill=INK)

    # ---- the card ---------------------------------------------------------
    # Values are composited, so a figure shown here is the figure that was
    # passed in — never one the model decided to draw.
    if v == 3:
        # Slim banner: label and value sit on one line, chip at the far right.
        cw, ch = int(W * 0.80), int(H * 0.17)
        cx0, cy0 = (W - cw) // 2, int(H * 0.68)
        _plate(base, (cx0, cy0, cx0 + cw, cy0 + ch), radius=26, scrim=0.50)
        d = ImageDraw.Draw(base)
        pad = int(cw * 0.042)
        d.text((cx0 + pad, cy0 + int(ch * 0.26)), card_label,
               font=font("regular", 20), fill=INK_MUTED)
        f_v = _fit_width(d, card_value, "semibold", int(cw * 0.36),
                         int(ch * 0.44), minimum=28)
        d.text((cx0 + pad + int(cw * 0.26), cy0 + int(ch * 0.5 - f_v.size * 0.62)),
               card_value, font=f_v, fill=INK)
        if card_sub:
            d.text((cx0 + pad, cy0 + int(ch * 0.26) + 30), card_sub,
                   font=font("regular", 18), fill=INK_FAINT)
        _p3_chip(base, chip, chip_note, cx0 + cw - pad,
                 cy0 + (ch - (78 if chip_note else 64)) // 2)
        base.save(out, quality=96)
        return out

    # The headline's measured width sets the card's. A card at a fixed
    # fraction sat narrower than the type above it on one poster and wider on
    # the next, and the pair read as two elements that happened to be on the
    # same canvas. Sharing an edge is what makes them read as one lockup.
    head_l = min(x for x, _, _ in placed) if placed else m3
    head_r = max(x + w for x, _, w in placed) if placed else W - m3
    head_w = head_r - head_l

    if v == 2:
        cw = int(W * 0.40)
    elif centred:
        cw = int(min(max(head_w, W * 0.46), W * 0.74))
    else:
        cw = int(min(max(head_w, W * 0.50), W - 2 * m3))

    pad = int(cw * 0.055)
    # Height follows the type, and the type is measured before the panel is
    # drawn. Sizing from a probe font and then shrinking the real one to clear
    # the chip left a band of empty glass under every card.
    f_v = _fit_width(d, card_value, "semibold", int(cw * 0.50),
                     int(H * 0.102), minimum=26)
    body_h = 30 + int(f_v.size * 1.15) + (26 if card_sub else 0)
    ch = max(pad * 2 + body_h, pad * 2 + (78 if chip_note else 64) + 6)

    if v == 2:
        # Two columns side by side that do not share a centre line read as a
        # mistake rather than as a composition. The card is hung from the
        # question's middle, and the pair is then centred in the frame below
        # the mark, which is what closes the empty lower third.
        q_mid = q_y + (len(qlines) * qlh) / 2
        cx0, cy0 = W - m3 - cw, int(q_mid - ch / 2)
    elif centred:
        cx0, cy0 = (W - cw) // 2, int(H * 0.58)
    else:
        cx0, cy0 = m3, int(H * 0.56)

    _plate(base, (cx0, cy0, cx0 + cw, cy0 + ch), radius=26, scrim=0.50)
    d = ImageDraw.Draw(base)

    top = cy0 + (ch - body_h) // 2
    d.text((cx0 + pad, top), card_label, font=font("regular", 20),
           fill=INK_MUTED)
    d.text((cx0 + pad, top + 30), card_value, font=f_v, fill=INK)
    if card_sub:
        d.text((cx0 + pad, top + 30 + int(f_v.size * 1.15)), card_sub,
               font=font("regular", 18), fill=INK_FAINT)

    _p3_chip(base, chip, chip_note, cx0 + cw - pad,
             cy0 + (ch - (78 if chip_note else 64)) // 2)

    base.save(out, quality=96)
    return out
