"""Reference-style posters — the house style in `design references/`.

The founder's references (cl-11, cl-13, cl-16, cl-23, cl-25, cl-27) share one
grammar, and it is not the P-series grammar:

  * a 1080x1080 square on a dark ground, a violet bloom low-left and a magenta
    bloom high-right;
  * the lockup centred at the top;
  * a heavy headline, centred, with ONE phrase set in a rose-to-violet
    gradient and slanted — "DeFi today: chaos. Vanna: *one* account.";
  * one grey line under it;
  * a drawn centrepiece — a comparison, a glass card of rows, stat tiles, a
    flow — made of real UI furniture, not an illustration;
  * a footer: a bold white lead, then a grey caveat.

Everything here is drawn in code. There is no image model in this file, so
there is nothing that can put a shape under a word. Each centrepiece renders
to its own transparent layer at its natural size and is then fitted into the
box left between the subtitle and the footer — scaled down if it has to be,
never allowed to run into either. That is the whole overlap guarantee.
"""
from __future__ import annotations

import math
from pathlib import Path
from typing import Any, Optional

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

from pipeline.gtm_creative.archetypes import font
from pipeline.gtm_creative.brand import logo as _logo

OUT_DIR = Path(__file__).resolve().parents[1] / "state"

SIZE = (1080, 1080)

# Sampled from the reference PNGs, not invented.
GROUND = (14, 10, 20)
ROSE = (255, 61, 139)
VIOLET = (146, 92, 255)
INK = (246, 244, 250)
INK_MUTED = (176, 168, 192)
INK_FAINT = (122, 114, 140)
CARD_FILL = (30, 20, 44, 215)
CARD_EDGE = (150, 110, 230, 120)
CHIP_FILL = (40, 24, 40, 230)
CHIP_EDGE = (200, 70, 120, 110)
OK = (74, 222, 155)
BAD = (255, 110, 120)


# --------------------------------------------------------------------------
# Ground
# --------------------------------------------------------------------------

def _bloom(size, centre, radius, colour, strength):
    """One soft radial light, as an RGB layer to screen onto the ground."""
    W, H = size
    small = (max(1, W // 8), max(1, H // 8))
    layer = Image.new("RGB", small, (0, 0, 0))
    d = ImageDraw.Draw(layer)
    cx, cy = centre[0] * small[0], centre[1] * small[1]
    r = radius * small[0]
    d.ellipse((cx - r, cy - r, cx + r, cy + r),
              fill=tuple(int(c * strength) for c in colour))
    layer = layer.filter(ImageFilter.GaussianBlur(r * 0.55))
    return layer.resize(size, Image.Resampling.BICUBIC)


def ground(size=SIZE) -> Image.Image:
    base = Image.new("RGB", size, GROUND)
    base = ImageChops.screen(base, _bloom(size, (0.16, 0.86), 0.42, (92, 46, 190), 0.75))
    base = ImageChops.screen(base, _bloom(size, (0.95, 0.26), 0.34, (150, 20, 80), 0.70))
    base = ImageChops.screen(base, _bloom(size, (0.55, 0.05), 0.30, (60, 20, 60), 0.35))
    # Fine grain, seeded so a re-render is identical.
    import random
    rnd = random.Random(7)
    noise = Image.new("L", (size[0] // 2, size[1] // 2))
    noise.putdata([rnd.randint(118, 138) for _ in range(noise.width * noise.height)])
    noise = noise.resize(size).convert("RGB")
    return Image.blend(base, ImageChops.overlay(base, noise), 0.35)


# --------------------------------------------------------------------------
# Type
# --------------------------------------------------------------------------

def _gradient(w: int, h: int, a=ROSE, b=VIOLET) -> Image.Image:
    g = Image.new("RGB", (max(1, w), max(1, h)))
    px = g.load()
    for x in range(g.width):
        t = x / max(1, g.width - 1)
        c = tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))
        for y in range(g.height):
            px[x, y] = c
    return g


def _word_img(word: str, f: ImageFont.FreeTypeFont, accent: bool) -> Image.Image:
    """One word as RGBA. Accent words get the gradient and a slant."""
    asc, desc = f.getmetrics()
    tw = int(math.ceil(f.getlength(word)))
    pad = int(f.size * 0.25)
    w, h = tw + pad * 2, asc + desc
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).text((pad, 0), word, font=f, fill=255)
    if accent:
        # Inter ships no italic here; a 12-degree shear is what the
        # references' slant measures, and it keeps the glyphs' own weight.
        k = math.tan(math.radians(12))
        mask = mask.transform(mask.size, Image.Transform.AFFINE,
                              (1, k, -k * h * 0.8, 0, 1, 0),
                              resample=Image.Resampling.BICUBIC)
        fill = _gradient(w, h)
    else:
        fill = Image.new("RGB", (w, h), INK)
    out = fill.convert("RGBA")
    out.putalpha(mask)
    if not accent:
        return out.crop((pad, 0, pad + tw, h))
    # The shear pushes the top of the glyphs right; keep that overhang and
    # no more, or two accent words sit a space-and-a-half apart.
    bbox = mask.getbbox() or (pad, 0, pad + tw, h)
    return out.crop((pad, 0, max(pad + tw, bbox[2]), h))


def _wrap_words(words, f, max_w, space):
    lines, cur, cur_w = [], [], 0.0
    for wd, acc in words:
        ww = f.getlength(wd)
        add = ww if not cur else cur_w + space + ww
        if cur and add > max_w:
            lines.append(cur)
            cur, cur_w = [(wd, acc)], ww
        else:
            cur.append((wd, acc))
            cur_w = add
    if cur:
        lines.append(cur)
    return lines


def headline_block(text: str, accent: str, max_w: int, *, start=70,
                   minimum=40, max_lines=2) -> tuple[Image.Image, int]:
    """The headline, centred, with the accent phrase in gradient.

    Shrinks until it fits `max_lines` — never clips a word.
    """
    acc = [a.lower() for a in accent.split()] if accent else []
    raw = text.split()
    flags = [False] * len(raw)
    # Mark the first run of words matching the accent phrase.
    if acc:
        low = [w.lower().strip(".,:;!?") for w in raw]
        for i in range(len(raw) - len(acc) + 1):
            if [x.strip(".,:;!?") for x in low[i:i + len(acc)]] == [a.strip(".,:;!?") for a in acc]:
                for j in range(i, i + len(acc)):
                    flags[j] = True
                break
    words = list(zip(raw, flags))

    size = start
    while True:
        f = font("extrabold", size)
        space = f.getlength(" ")
        lines = _wrap_words(words, f, max_w, space)
        if len(lines) <= max_lines or size <= minimum:
            break
        size -= 3

    lh = int(size * 1.12)
    imgs = []
    for ln in lines:
        parts = [_word_img(w, f, a) for w, a in ln]
        lw = sum(p.width for p in parts) + int(space) * (len(parts) - 1)
        row = Image.new("RGBA", (max(1, lw), lh), (0, 0, 0, 0))
        x = 0
        for p in parts:
            row.alpha_composite(p, (x, 0))
            x += p.width + int(space)
        imgs.append(row)
    W = max(i.width for i in imgs)
    block = Image.new("RGBA", (W, lh * len(imgs)), (0, 0, 0, 0))
    for n, r in enumerate(imgs):
        block.alpha_composite(r, ((W - r.width) // 2, n * lh))
    return block, size


def _text_center(d, cx, y, text, f, fill):
    w = d.textlength(text, font=f)
    d.text((cx - w / 2, y), text, font=f, fill=fill)


def _wrap(d, text, f, max_w):
    words, lines, cur = str(text).split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if d.textlength(t, font=f) <= max_w:
            cur = t
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def _fit_lines(d, text, weight, max_w, max_lines, start, minimum=14):
    size = start
    while size > minimum:
        f = font(weight, size)
        ls = _wrap(d, text, f, max_w)
        if len(ls) <= max_lines:
            return f, ls
        size -= 1
    f = font(weight, minimum)
    return f, _wrap(d, text, f, max_w)[:max_lines]


# --------------------------------------------------------------------------
# Furniture
# --------------------------------------------------------------------------

def _glass(layer: Image.Image, box, *, radius=26, fill=CARD_FILL,
           edge=CARD_EDGE, glow=(120, 70, 230), glow_strength=0.0) -> None:
    """A glass card with a soft coloured halo, as in cl-16 and cl-27."""
    x0, y0, x1, y1 = [int(v) for v in box]
    if glow_strength > 0:
        halo = Image.new("RGBA", layer.size, (0, 0, 0, 0))
        ImageDraw.Draw(halo).rounded_rectangle(
            (x0 - 6, y0 - 6, x1 + 6, y1 + 6), radius=radius + 6,
            fill=glow + (int(120 * glow_strength),))
        halo = halo.filter(ImageFilter.GaussianBlur(28))
        layer.alpha_composite(halo)
    card = Image.new("RGBA", layer.size, (0, 0, 0, 0))
    ImageDraw.Draw(card).rounded_rectangle((x0, y0, x1, y1), radius=radius,
                                           fill=fill, outline=edge, width=2)
    layer.alpha_composite(card)


def _gradient_pill(layer, box, radius=None):
    x0, y0, x1, y1 = [int(v) for v in box]
    g = _gradient(x1 - x0, y1 - y0).convert("RGBA")
    m = Image.new("L", g.size, 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, g.width - 1, g.height - 1),
                                        radius=radius or (y1 - y0) // 2, fill=255)
    g.putalpha(m)
    layer.alpha_composite(g, (x0, y0))


def _check(d, x, y, s, colour=OK):
    d.line([(x, y + s * 0.55), (x + s * 0.38, y + s * 0.9), (x + s, y + s * 0.1)],
           fill=colour, width=max(2, int(s * 0.16)), joint="curve")


def _arrow(d, x0, y, x1, colour=(160, 120, 255), width=3):
    d.line([(x0, y), (x1, y)], fill=colour, width=width)
    d.line([(x1 - 12, y - 9), (x1, y), (x1 - 12, y + 9)], fill=colour, width=width)


# --------------------------------------------------------------------------
# Centrepieces. Each returns an RGBA layer at its natural size.
# --------------------------------------------------------------------------

def mod_compare(left_label, left_items, left_caption, right_label, card_title,
                right_rows, right_caption, *, width=940) -> Image.Image:
    """Scattered chips on the left, one ordered card on the right (cl-16)."""
    left_items = [str(x) for x in left_items][:8]
    right_rows = [str(x) for x in right_rows][:5]
    H = 520
    L = Image.new("RGBA", (width, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(L)
    f_lab = font("bold", 17)
    f_chip = font("semibold", 18)
    f_row = font("semibold", 21)
    f_title = font("bold", 23)
    f_cap = font("regular", 17)

    col_w = int(width * 0.42)
    lx, rx = 0, width - col_w
    # Left: label, chips on a loose two-column grid with seeded tilts.
    _text_center(d, lx + col_w / 2, 40, str(left_label).upper(), f_lab, BAD)
    chip_layer = Image.new("RGBA", L.size, (0, 0, 0, 0))
    tilts = [-5, 4, -3, 6, 3, -6, -2, 5]
    for i, item in enumerate(left_items):
        cw = int(min(col_w * 0.48, f_chip.getlength(item) + 40))
        ch = 44
        cx = lx + (8 if i % 2 == 0 else col_w // 2 + 4) + (i // 2 % 2) * 14
        cy = 88 + (i // 2) * 78 + (18 if i % 2 else 0)
        chip = Image.new("RGBA", (cw + 20, ch + 20), (0, 0, 0, 0))
        cd = ImageDraw.Draw(chip)
        cd.rounded_rectangle((10, 10, 10 + cw, 10 + ch), radius=10,
                             fill=CHIP_FILL, outline=CHIP_EDGE, width=2)
        label = item
        while f_chip.getlength(label) > cw - 24 and len(label) > 4:
            label = label[:-2]
        if label != item:
            label = label.rstrip() + "…"
        cd.text((10 + (cw - f_chip.getlength(label)) / 2, 10 + 11), label,
                font=f_chip, fill=(225, 215, 230))
        chip = chip.rotate(tilts[i % len(tilts)], resample=Image.Resampling.BICUBIC,
                           expand=True)
        chip_layer.alpha_composite(chip, (int(cx), int(cy)))
    L.alpha_composite(chip_layer)
    rows_bottom = 88 + ((len(left_items) + 1) // 2) * 78 + 20
    if left_caption:
        _text_center(d, lx + col_w / 2, min(H - 40, rows_bottom), str(left_caption), f_cap, INK_FAINT)

    # Arrow between the columns.
    _arrow(d, col_w + 22, H // 2 - 10, rx - 22)

    # Right: label, card, rows with checks.
    _text_center(d, rx + col_w / 2, 40, str(right_label).upper(), f_lab, (190, 150, 255))
    row_h = 58
    ch = 80 + row_h * len(right_rows) + 14
    cy0 = 78
    _glass(L, (rx, cy0, rx + col_w, cy0 + ch))
    d = ImageDraw.Draw(L)
    _gradient_pill(L, (rx + 26, cy0 + 26, rx + 58, cy0 + 58), radius=8)
    d = ImageDraw.Draw(L)
    d.text((rx + 72, cy0 + 28), str(card_title), font=f_title, fill=INK)
    y = cy0 + 80
    for r in right_rows:
        d.line([(rx + 26, y), (rx + col_w - 26, y)], fill=(90, 70, 120), width=1)
        # Smaller before shorter: "Deploy across external venu…" lost the
        # word the row was about.
        fr, label = f_row, r
        while fr.getlength(label) > col_w - 100 and fr.size > 15:
            fr = font("semibold", fr.size - 1)
        while fr.getlength(label) > col_w - 100 and len(label) > 4:
            label = label[:-2]
        if label != r:
            label = label.rstrip() + "…"
        d.text((rx + 26, y + 16 + (f_row.size - fr.size) // 2), label, font=fr, fill=(230, 225, 240))
        _check(d, rx + col_w - 50, y + 20, 20)
        y += row_h
    if right_caption:
        _text_center(d, rx + col_w / 2, cy0 + ch + 24, str(right_caption), font("semibold", 18), (180, 150, 255))
    bottom = max(rows_bottom + 30, cy0 + ch + 60)
    return L.crop((0, 0, width, min(H, bottom)))


def mod_flow(steps, *, highlight: int = -1, caption: str = "",
             width=960) -> Image.Image:
    """Three or four cards joined by arrows: who acts, what bounds them."""
    steps = [(str(t), str(s)) for t, s in steps][:4]
    n = max(1, len(steps))
    gap = 44
    cw = int((width - gap * (n - 1)) / n)
    ch = 190
    H = ch + 40 + (60 if caption else 0)
    L = Image.new("RGBA", (width, H), (0, 0, 0, 0))
    f_t = font("bold", 23 if n <= 3 else 21)
    f_s = font("regular", 17)
    f_n = font("bold", 15)
    for i, (t, s) in enumerate(steps):
        x0 = i * (cw + gap)
        hot = i == highlight
        _glass(L, (x0, 20, x0 + cw, 20 + ch),
               edge=(235, 90, 170, 230) if hot else CARD_EDGE,
               fill=(48, 22, 52, 225) if hot else CARD_FILL)
        d = ImageDraw.Draw(L)
        d.text((x0 + 22, 42), "0" + str(i + 1), font=f_n, fill=(190, 150, 255))
        ft, tl = _fit_lines(d, t, "bold", cw - 44, 2, f_t.size, 16)
        y = 72
        for ln in tl:
            d.text((x0 + 22, y), ln, font=ft, fill=INK)
            y += int(ft.size * 1.2)
        fs, sl = _fit_lines(d, s, "regular", cw - 44, 3, f_s.size, 13)
        y += 6
        for ln in sl:
            d.text((x0 + 22, y), ln, font=fs, fill=INK_MUTED)
            y += int(fs.size * 1.3)
        if i < n - 1:
            _arrow(d, x0 + cw + 8, 20 + ch // 2, x0 + cw + gap - 8)
    if caption:
        d = ImageDraw.Draw(L)
        _text_center(d, width / 2, ch + 50, caption, font("semibold", 19), (190, 150, 255))
    return L


def mod_tiles(tiles, *, panel_label: str = "", width=900) -> Image.Image:
    """Stat tiles in one glass panel (cl-23, cl-27). Real figures only."""
    tiles = [(str(v), str(l)) for v, l in tiles][:4]
    n = max(1, len(tiles))
    pad, gap = 28, 16
    top = 64 if panel_label else pad
    tw = int((width - pad * 2 - gap * (n - 1)) / n)
    th = 150
    H = top + th + pad
    L = Image.new("RGBA", (width, H + 20), (0, 0, 0, 0))
    _glass(L, (0, 10, width, 10 + H))
    d = ImageDraw.Draw(L)
    if panel_label:
        d.text((pad, 10 + 24), str(panel_label).upper(), font=font("bold", 15), fill=INK_FAINT)
    for i, (v, lab) in enumerate(tiles):
        x0 = pad + i * (tw + gap)
        y0 = 10 + top
        d.rounded_rectangle((x0, y0, x0 + tw, y0 + th), radius=16,
                            fill=(40, 28, 56), outline=(80, 64, 110), width=1)
        size = 58
        while size > 26 and font("extrabold", size).getlength(v) > tw - 28:
            size -= 2
        fv = font("extrabold", size)
        vw = fv.getlength(v)
        g = _gradient(int(vw) + 4, int(size * 1.25)).convert("RGBA")
        m = Image.new("L", g.size, 0)
        ImageDraw.Draw(m).text((2, 0), v, font=fv, fill=255)
        g.putalpha(m)
        L.alpha_composite(g, (int(x0 + (tw - vw) / 2), int(y0 + 26)))
        d = ImageDraw.Draw(L)
        fl, ll = _fit_lines(d, lab, "regular", tw - 20, 2, 17, 12)
        y = y0 + 26 + int(size * 1.3)
        for ln in ll:
            _text_center(d, x0 + tw / 2, y, ln, fl, INK_MUTED)
            y += int(fl.size * 1.3)
    return L


def mod_question(question, options, take, *, width=900) -> Image.Image:
    """A discussion prompt: the question, the answers people will argue for,
    and Vanna's short take underneath."""
    options = [str(o) for o in options][:4]
    L = Image.new("RGBA", (width, 600), (0, 0, 0, 0))
    d = ImageDraw.Draw(L)
    pad = 40
    fq, ql = _fit_lines(d, question, "bold", width - pad * 2 - 80, 3, 32, 20)
    q_h = len(ql) * int(fq.size * 1.25)
    opt_h = 62
    ft, tl = _fit_lines(d, take, "regular", width - pad * 2 - 40, 3, 19, 14)
    take_h = (len(tl) * int(ft.size * 1.4) + 58) if take else 0
    H = pad + 70 + q_h + 24 + len(options) * (opt_h + 12) + take_h + pad
    _glass(L, (0, 10, width, 10 + H))
    d = ImageDraw.Draw(L)
    # The "?" badge, gradient, as the reference's avatar dot.
    _gradient_pill(L, (pad, 10 + pad, pad + 52, 10 + pad + 52))
    d = ImageDraw.Draw(L)
    fqm = font("extrabold", 30)
    d.text((pad + 26 - fqm.getlength("?") / 2, 10 + pad + 8), "?", font=fqm, fill=INK)
    d.text((pad + 70, 10 + pad + 4), "Question for traders", font=font("bold", 19), fill=INK)
    d.text((pad + 70, 10 + pad + 30), "Reply with yours", font=font("regular", 15), fill=INK_FAINT)
    y = 10 + pad + 80
    for ln in ql:
        d.text((pad, y), ln, font=fq, fill=INK)
        y += int(fq.size * 1.25)
    y += 22
    for i, o in enumerate(options):
        d.rounded_rectangle((pad, y, width - pad, y + opt_h), radius=14,
                            fill=(42, 28, 60), outline=(96, 74, 140), width=1)
        badge = "ABCD"[i]
        d.rounded_rectangle((pad + 14, y + 13, pad + 50, y + 49), radius=9,
                            fill=(70, 44, 110))
        fb = font("bold", 18)
        d.text((pad + 32 - fb.getlength(badge) / 2, y + 20), badge, font=fb, fill=(210, 190, 255))
        fo, ol = _fit_lines(d, o, "semibold", width - pad * 2 - 90, 1, 20, 13)
        d.text((pad + 66, y + 19), ol[0] if ol else o, font=fo, fill=(232, 226, 242))
        y += opt_h + 12
    if take:
        y += 10
        d.line([(pad, y), (width - pad, y)], fill=(90, 70, 120), width=1)
        y += 18
        d.text((pad, y), "VANNA'S TAKE", font=font("bold", 14), fill=(190, 150, 255))
        y += 26
        for ln in tl:
            d.text((pad, y), ln, font=ft, fill=INK_MUTED)
            y += int(ft.size * 1.4)
    return L.crop((0, 0, width, 10 + H + 20))


def mod_versus(myth_label, myth, fact_label, fact, points, *, width=920) -> Image.Image:
    """Assumption on the left, what is actually true on the right (a hot take)."""
    points = [str(p) for p in points][:3]
    col = int((width - 60) / 2)
    L = Image.new("RGBA", (width, 640), (0, 0, 0, 0))
    d = ImageDraw.Draw(L)
    pad = 28
    fm, ml = _fit_lines(d, myth, "bold", col - pad * 2, 4, 28, 17)
    ff, fl = _fit_lines(d, fact, "bold", col - pad * 2, 4, 28, 17)
    body_h = max(len(ml) * int(fm.size * 1.25), len(fl) * int(ff.size * 1.25))
    fp = font("regular", 18)
    pts = [_wrap(d, p, fp, col - pad * 2 - 30)[:2] for p in points]
    pts_h = sum(len(p) * 26 + 14 for p in pts)
    right_h = pad + 36 + len(fl) * int(ff.size * 1.25) + 24 + pts_h + pad
    left_h = pad + 36 + len(ml) * int(fm.size * 1.25) + pad
    card_h = right_h
    # Equal heights left the assumption card two-thirds empty. Each card is
    # as tall as its content; the shorter is centred on the taller's axis.
    ly0 = 10 + (right_h - left_h) // 2
    _glass(L, (0, ly0, col, ly0 + left_h), fill=(34, 22, 32, 210),
           edge=(200, 80, 110, 120))
    _glass(L, (width - col, 10, width, 10 + right_h))
    d = ImageDraw.Draw(L)
    d.text((pad, ly0 + pad), str(myth_label).upper(), font=font("bold", 15), fill=BAD)
    y = ly0 + pad + 36
    for ln in ml:
        d.text((pad, y), ln, font=fm, fill=(210, 200, 214))
        # Struck through, every line: the whole assumption is what is wrong.
        sy = y + fm.size * 0.62
        d.line([(pad, sy), (pad + fm.getlength(ln), sy)], fill=(255, 110, 120), width=3)
        y += int(fm.size * 1.25)
    x = width - col
    d.text((x + pad, 10 + pad), str(fact_label).upper(), font=font("bold", 15), fill=(190, 150, 255))
    y = 10 + pad + 36
    for ln in fl:
        d.text((x + pad, y), ln, font=ff, fill=INK)
        y += int(ff.size * 1.25)
    y += 24
    for p in pts:
        _check(d, x + pad, y + 4, 16)
        for ln in p:
            d.text((x + pad + 30, y), ln, font=fp, fill=INK_MUTED)
            y += 26
        y += 14
    _arrow(d, col + 10, 10 + card_h // 2, width - col - 10)
    return L.crop((0, 0, width, 10 + card_h + 30))


MODULES = {
    "compare": mod_compare,
    "flow": mod_flow,
    "tiles": mod_tiles,
    "question": mod_question,
    "versus": mod_versus,
}


# --------------------------------------------------------------------------
# The poster
# --------------------------------------------------------------------------

def render(headline: str, accent: str, subtitle: str, module: str,
           module_args: dict[str, Any], footer_lead: str, footer_note: str,
           *, out: Optional[Path] = None, size=SIZE) -> Path:
    W, H = size
    base = ground(size).convert("RGBA")
    d = ImageDraw.Draw(base)
    margin = 70

    # Lockup, centred.
    lh = 52
    mark = _logo(lh)
    y = 60
    if mark is not None:
        base.alpha_composite(mark, ((W - mark.width) // 2, y))
    y += lh + 44

    # Headline.
    block, _ = headline_block(headline, accent, W - margin * 2)
    base.alpha_composite(block, ((W - block.width) // 2, y))
    y += block.height + 16

    # Subtitle.
    d = ImageDraw.Draw(base)
    fsub, sl = _fit_lines(d, subtitle, "regular", W - margin * 2 - 40, 2, 23, 16)
    for ln in sl:
        _text_center(d, W / 2, y, ln, fsub, INK_MUTED)
        y += int(fsub.size * 1.4)

    # Footer, measured first so the centrepiece knows its floor.
    f_lead = font("bold", 19)
    f_note = font("regular", 18)
    lead = str(footer_lead).strip()
    note = str(footer_note).strip()
    while (f_lead.getlength(lead + " ") + f_note.getlength(note) > W - margin * 2
           and f_note.size > 12):
        f_lead = font("bold", f_lead.size - 1)
        f_note = font("regular", f_note.size - 1)
    fy = H - 64
    total = f_lead.getlength(lead + (" " if note else "")) + f_note.getlength(note)
    fx = (W - total) / 2
    d.text((fx, fy), lead + (" " if note else ""), font=f_lead, fill=INK)
    d.text((fx + f_lead.getlength(lead + (" " if note else "")), fy + 1), note,
           font=f_note, fill=INK_FAINT)

    # Centrepiece: rendered at natural size, fitted into what is left.
    fn = MODULES[module]
    layer = fn(**module_args)
    box_top, box_bot = y + 40, fy - 40
    box_w, box_h = W - margin * 2 + 40, box_bot - box_top
    scale = min(1.0, box_w / layer.width, box_h / layer.height)
    if scale < 1.0:
        layer = layer.resize((int(layer.width * scale), int(layer.height * scale)),
                             Image.Resampling.LANCZOS)
    lx = (W - layer.width) // 2
    ly = int(box_top + (box_h - layer.height) / 2)
    # The halo is drawn here, from the centrepiece's own silhouette, on the
    # whole canvas. Drawn inside each module it was cut off at the module's
    # edge and left a faint rectangle behind every card.
    sil = Image.new("L", (W, H), 0)
    sil.paste(layer.getchannel("A").point(lambda a: 255 if a > 150 else 0), (lx, ly))
    halo = Image.new("RGBA", (W, H), (120, 70, 230, 0))
    halo.putalpha(sil.filter(ImageFilter.GaussianBlur(30)).point(lambda a: int(a * 0.42)))
    base.alpha_composite(halo)
    base.alpha_composite(layer, (lx, ly))

    out = Path(out or (OUT_DIR / "demo_reference_poster.png"))
    base.convert("RGB").save(out, quality=96)
    return out


# --------------------------------------------------------------------------
# Direction — a prompt straight to a poster, no content agent, no scrape.
# --------------------------------------------------------------------------

DIRECT_SYSTEM = (
    "You are Vanna's visual designer. Vanna is composable credit / unified "
    "margin infrastructure on Stellar Soroban TESTNET: each user gets a "
    "SmartAccount (a margin account contract), borrows credit against "
    "collateral, and deploys it across venues; risk is isolated per "
    "account with a 1.10x health-factor floor.\n\n"
    "You receive a brief that was written for a post. You make ONLY the "
    "visual: choose one centrepiece module and write every word that "
    "appears on the poster. The house style is fixed — centred logo, heavy "
    "headline with one accent phrase in gradient, one grey subtitle line, a "
    "centrepiece, a footer. Every word is typeset in code, so write exactly "
    "what should appear.\n\n"
    "Rules:\n"
    "- headline: sentence case (not Title Case), under 9 words, punchy, the brief's idea. accent: 1-2 "
    "consecutive words copied EXACTLY from the headline — the word that "
    "carries the turn ('one', 'Hedge', 'Zero').\n"
    "- subtitle: one line, under 16 words, plain.\n"
    "- footer_lead: under 6 words, bold statement. footer_note: the caveat, "
    "under 10 words, always including 'testnet'.\n"
    "- Every figure must be TRUE of Vanna and from the facts given. No "
    "illustrative or invented numbers, no user counts, no TVL, no APY. If "
    "you have no true figure, use words.\n"
    "- Name a partner only if it is on the CONFIRMED PARTNERS list. Never "
    "imply mainnet. Never name a competitor as worse.\n"
    "- Keep strings short: chips 1-3 words, card rows 2-4 words, flow step "
    "titles 1-3 words with a sub-line under 8 words, options under 7 words.\n"
    "Return strict JSON."
)

MODULE_GUIDE = (
    "MODULES (pick the one whose shape IS the brief's argument):\n"
    "  versus  — an assumption vs what is actually true. For hot takes that "
    "challenge a belief. args: {myth_label: str, myth: str, fact_label: str, "
    "fact: str, points: [str x2-3]}\n"
    "  flow    — who acts and what bounds them, in 3-4 steps. For "
    "mechanisms and agents. args: {steps: [[title, sub] x3-4], highlight: "
    "int index of the Vanna step, caption: str}\n"
    "  question — a genuine question with 2-4 answers people will argue for, "
    "plus Vanna's short take. For discussion posts. args: {question: str, "
    "options: [str], take: str}\n"
    "  compare — scattered chips (the fragmented way) vs one ordered card "
    "(Vanna). For fragmentation, liquidity, unified accounts. args: "
    "{left_label: str, left_items: [str x5-8], left_caption: str, "
    "right_label: str, card_title: str, right_rows: [str x3-5], "
    "right_caption: str}\n"
    "  tiles   — 2-4 stat tiles, ONLY with real Vanna figures (1.10x floor, "
    "0.00014 XLM gas, ~320ms indexing). args: {tiles: [[value, label]], "
    "panel_label: str}\n"
)

SCHEMA = (
    '{"module": "versus"|"flow"|"question"|"compare"|"tiles", '
    '"headline": str, "accent": str, "subtitle": str, '
    '"module_args": {...}, "footer_lead": str, "footer_note": str, '
    '"why": str}'
)


def direct(brief: str) -> dict[str, Any]:
    from pipeline.gtm_os import agent_runtime as R
    from pipeline.brand_brain.context import facts_block as prompt_block

    prompt = (
        prompt_block(brief[:300], excerpts=5) + "\n\n----\n\n"
        "BRIEF\n  " + " ".join(brief.split()) + "\n\n"
        + MODULE_GUIDE + "\nReturn JSON exactly:\n" + SCHEMA
    )
    try:
        out = R.brain_json(prompt, agent="A07_creative_director",
                           role="reasoning", system=DIRECT_SYSTEM,
                           temperature=0.5, max_output_tokens=4096)
    except R.BrainError:
        out = R.brain_json(prompt + "\n\nReturn ONLY the JSON object.",
                           agent="A07_creative_director", role="reasoning",
                           system=DIRECT_SYSTEM, temperature=0.2,
                           max_output_tokens=4096)
    if out.get("module") not in MODULES:
        raise ValueError("unknown module " + repr(out.get("module")))
    return out


def _clean_args(module: str, args: dict[str, Any]) -> dict[str, Any]:
    """Keep only what the module accepts, coerced to its shapes."""
    import inspect

    fn = MODULES[module]
    ok = set(inspect.signature(fn).parameters) - {"width"}
    a = {k: v for k, v in (args or {}).items() if k in ok}
    if module == "flow":
        a["steps"] = [tuple((list(s) + ["", ""])[:2]) for s in a.get("steps") or []]
        try:
            a["highlight"] = int(a.get("highlight", -1))
        except (TypeError, ValueError):
            a["highlight"] = -1
    if module == "tiles":
        a["tiles"] = [tuple((list(t) + ["", ""])[:2]) for t in a.get("tiles") or []]
    return a


def make(brief: str, name: str, out_dir: Optional[Path] = None) -> dict[str, Any]:
    """Brief in, poster out. Returns the direction and the file path."""
    d = direct(brief)
    args = _clean_args(d["module"], d.get("module_args") or {})
    path = render(d.get("headline", ""), d.get("accent", ""), d.get("subtitle", ""),
                  d["module"], args, d.get("footer_lead", ""),
                  d.get("footer_note", ""),
                  out=Path(out_dir or OUT_DIR) / (name + ".png"))
    return {**d, "module_args": args, "path": str(path)}
