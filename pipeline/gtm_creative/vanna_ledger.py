"""Vanna "Ledger" — the sober poster theme.

What the DeFi protocols' posters share (Superform, Base x Aave, $UP): a quiet
monochrome print texture, one flat card, very little type. What makes this
one Vanna's own:

  card       platinum #F7F7F7, sharp corners, flat — no glow, no glass
  type       Plus Jakarta Sans (the brand font): a light, very large figure or a
             semibold headline; JetBrains Mono for the small labels
  signature  one short line in the brand gradient (#FC5457 -> #703AE6) under
             the figure or headline — the only colour on the card besides the logo
  logo       the real mark in its gradient, wordmark in ink, top-left of the card
  texture    Vanna's own motifs as a stippled engraving, never a borrowed object:
             a grid of separate cells (isolated accounts), ribbon lines folding
             together (composability), contour lines (statements)
  ground     the texture forced into two inks, #111111 and a muted violet

Variants: stat (a true figure), partner (Vanna x a listed partner),
statement (a short headline). The agent picks one and writes the words from
the true figures; the poster model draws the texture fresh every run.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

from PIL import Image, ImageDraw, ImageFont

from pipeline.gtm_creative.engraved_posters import _duotone, _procedural, _rgb, check_text

REPO = Path(__file__).resolve().parents[2]
FONTS = REPO / "pipeline" / "assets" / "fonts"
OUT_DIR = REPO / "pipeline" / "state" / "vanna_ledger"
LOGO = REPO / "pipeline" / "assets" / "logos" / "vanna_hires.png"

W, H = 1600, 1200
DARK, LIGHT = "#111111", "#3D3160"
CARD = (247, 247, 247)
INK = (31, 31, 31)
GREY = (89, 89, 89)
LABEL = (119, 119, 119)
GRAD = ((252, 84, 87), (112, 58, 230))

TEXTURES = {
    "stat": ("a field of many small separate rectangular cells in a precise grid, like isolated "
             "compartments, a few cells filled slightly darker than the rest"),
    "partner": ("two bundles of fine parallel ribbon lines flowing in from the left and the right "
                "and folding together in the centre"),
    "statement": "fine flowing contour lines, like a topographic map of a gentle landscape",
}

PRINT_RULES = (
    "STYLE: a monochrome print — one ink on paper, a stippled dot halftone with fine engraved "
    "linework and soft grain, quiet and low in contrast, full bleed edge to edge. "
    "ABSOLUTELY NO text, letters, numbers, logos, symbols, cards, frames, borders or panels. "
    "No objects, buildings, people, coins or charts. Flat and face-on.")


def _font(file: str, size: int, weight: Optional[int] = None) -> ImageFont.FreeTypeFont:
    f = ImageFont.truetype(str(FONTS / file), size)
    if weight is not None:
        f.set_variation_by_axes([weight])
    return f


def jakarta(size: int, weight: int) -> ImageFont.FreeTypeFont:
    return _font("plusjakartasans-var.ttf", size, weight)


def mono(size: int, weight: int = 500) -> ImageFont.FreeTypeFont:
    return _font("jetbrainsmono-var.ttf", size, weight)


# --------------------------------------------------------------------------
# Pieces
# --------------------------------------------------------------------------

def texture(variant: str, out: Path, *, use_model: bool = True) -> tuple[Image.Image, bool]:
    raw = out.with_name(out.stem + "_texture.png")
    made = False
    if use_model:
        try:
            from pipeline.gtm_creative.direct_image_posters import _model
            from pipeline.scripts.gemini_flash_image import generate_gemini_image

            generate_gemini_image(prompt="Make ONE textless background texture.\n\nSUBJECT: "
                                  + TEXTURES[variant] + ".\n\n" + PRINT_RULES,
                                  output_path=raw, model=_model(), temperature=0.6, aspect_ratio="4:3")
            made = raw.exists() and raw.stat().st_size > 4096
        except Exception as exc:                    # noqa: BLE001 — boundary
            print("  ledger: model texture failed, using the drawn one: " + str(exc)[:160])
    src = Image.open(raw) if made else _procedural(variant, (W, H), 7)
    return _duotone(src, (W, H), DARK, LIGHT), made


def logo(height: int) -> Optional[Image.Image]:
    """The real lockup: the gradient mark kept, the white wordmark turned to ink."""
    if not LOGO.exists():
        return None
    src = Image.open(LOGO).convert("RGBA")
    src = src.crop(src.getchannel("A").getbbox())
    src = src.resize((int(src.width * height / src.height), height), Image.Resampling.LANCZOS)
    px = src.load()
    for y in range(src.height):
        for x in range(src.width):
            r, g, b, a = px[x, y]
            if a and max(r, g, b) - min(r, g, b) < 40:
                px[x, y] = INK + (a,)
    return src


def gradient_line(img: Image.Image, cx: int, y: int, w: int = 110, h: int = 6) -> None:
    d = ImageDraw.Draw(img)
    x0 = cx - w // 2
    for i in range(w):
        t = i / max(1, w - 1)
        d.line((x0 + i, y, x0 + i, y + h - 1),
               fill=tuple(int(GRAD[0][k] + (GRAD[1][k] - GRAD[0][k]) * t) for k in range(3)))


def _tracked_w(d, text, f, track):
    return sum(d.textlength(c, font=f) for c in text) + track * f.size * max(0, len(text) - 1)


def _tracked(d, x, y, text, f, fill, track=0.12, align="left"):
    w = _tracked_w(d, text, f, track)
    if align == "right":
        x -= w
    elif align == "center":
        x -= w / 2
    for c in text:
        d.text((x, y), c, font=f, fill=fill)
        x += d.textlength(c, font=f) + track * f.size


def _centred(d, cx, y, text, f, fill) -> int:
    l, t, r, b = d.textbbox((0, 0), text, font=f)
    d.text((cx - (r - l) / 2 - l, y - t), text, font=f, fill=fill)
    return y + (b - t)


def _fit(d, text, make, size, max_w):
    f = make(size)
    while size > 20 and d.textlength(text, font=f) > max_w:
        size -= 4
        f = make(size)
    return f


def _wrap(d, text, f, max_w) -> list[str]:
    lines, cur = [], ""
    for w in text.split():
        t = (cur + " " + w).strip()
        if cur and d.textlength(t, font=f) > max_w:
            lines.append(cur)
            cur = w
        else:
            cur = t
    return lines + ([cur] if cur else [])


def card(img: Image.Image, s: dict, *, small_logo: bool = True) -> tuple[int, int, int, int]:
    """The flat card: logo top-left, kicker top-right, footer bottom-centre."""
    cw, ch = int(W * 0.62), int(H * 0.70)
    box = ((W - cw) // 2, (H - ch) // 2, (W + cw) // 2, (H + ch) // 2)
    d = ImageDraw.Draw(img)
    d.rectangle(box, fill=CARD)
    pad = 56
    mark = logo(40) if small_logo else None
    if mark:
        img.paste(mark, (box[0] + pad, box[1] + pad), mark)
    kicker = str(s.get("kicker") or "")
    if kicker:
        _tracked(d, box[2] - pad if small_logo else (box[0] + box[2]) // 2, box[1] + pad + 8,
                 kicker.upper(), mono(22), LABEL, 0.14, align="right" if small_logo else "center")
    footer = str(s.get("footer") or "")
    if footer:
        _tracked(d, (box[0] + box[2]) // 2, box[3] - pad - 22, footer.upper(), mono(20), LABEL,
                 0.16, align="center")
    return box


# --------------------------------------------------------------------------
# Variants
# --------------------------------------------------------------------------

def _stat(img, s):
    x0, y0, x1, y1 = card(img, s)
    d = ImageDraw.Draw(img)
    cx, cw = (x0 + x1) // 2, x1 - x0
    f = _fit(d, s["figure"], lambda z: jakarta(z, 300), 230, int(cw * 0.82))
    l, t, r, b = d.textbbox((0, 0), s["figure"], font=f)
    y = y0 + int((y1 - y0) * 0.30)
    _centred(d, cx, y, s["figure"], f, INK)
    y += (b - t) + 52
    gradient_line(img, cx, y)
    y += 44
    if s.get("caption"):
        cf = _fit(d, s["caption"], lambda z: jakarta(z, 500), 36, int(cw * 0.8))
        _centred(d, cx, y, s["caption"], cf, GREY)


def _partner(img, s):
    x0, y0, x1, y1 = card(img, s, small_logo=False)
    d = ImageDraw.Draw(img)
    cx, cy = (x0 + x1) // 2, (y0 + y1) // 2
    mark = logo(96)
    name = s["partners"][0]
    nf = jakarta(104, 600)
    l, t, r, b = d.textbbox((0, 0), name, font=nf)
    times = jakarta(44, 300)
    gap = 46
    total = (mark.height if mark else 0) + gap + 44 + gap + (b - t)
    y = cy - total // 2 - 10
    if mark:
        img.paste(mark, (cx - mark.width // 2, y), mark)
        y += mark.height + gap
    y = _centred(d, cx, y, "\u00d7", times, LABEL) + gap
    y = _centred(d, cx, y, name, nf, INK) + 56
    gradient_line(img, cx, y)


def _statement(img, s):
    x0, y0, x1, y1 = card(img, s)
    d = ImageDraw.Draw(img)
    cx, cw = (x0 + x1) // 2, x1 - x0
    size = 96
    while True:
        f = jakarta(size, 600)
        lines = _wrap(d, s["headline"], f, int(cw * 0.80))
        if len(lines) <= 3 or size <= 56:
            break
        size -= 6
    lh = int(size * 1.18)
    block = lh * len(lines) + 40 + 6
    y = (y0 + y1) // 2 - block // 2 + 10
    for ln in lines:
        _centred(d, cx, y, ln, f, INK)
        y += lh
    gradient_line(img, cx, y + 34)


DRAW = {"stat": _stat, "partner": _partner, "statement": _statement}


def render(variant: str, slots: dict[str, Any], name: str, *, out_dir: Optional[Path] = None,
           use_model: bool = True, texture_path: Optional[Path] = None) -> dict[str, Any]:
    from pipeline.brand_brain import context as C

    if variant not in DRAW:
        raise ValueError("unknown variant " + repr(variant))
    bad = check_text([str(v) for v in slots.values() if isinstance(v, str)])
    if bad:
        raise ValueError("figures not in the brand's true figures: " + ", ".join(bad))
    if variant == "stat" and not slots.get("figure"):
        raise ValueError("the stat variant needs a figure")
    if variant == "statement" and not slots.get("headline"):
        raise ValueError("the statement variant needs a headline")
    if variant == "partner":
        p = (slots.get("partners") or [None])[0]
        if not p or not C.is_partner(p):
            raise ValueError(repr(p) + " is not a listed partner")
    out_dir = Path(out_dir or OUT_DIR)
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / (name + ".png")
    if texture_path and Path(texture_path).exists():
        img, made = _duotone(Image.open(texture_path), (W, H), DARK, LIGHT), True
    else:
        img, made = texture(variant, out, use_model=use_model)
    DRAW[variant](img, slots)
    img.save(out)
    return {"path": str(out), "variant": variant, "texture_by_model": made, "slots": slots}


# --------------------------------------------------------------------------
# The agent
# --------------------------------------------------------------------------

def slots_for(post: str) -> dict[str, Any]:
    from pipeline.brand_brain import context as C
    from pipeline.gtm_os import agent_runtime as R

    figures = "\n".join("- " + f["value"] + ": " + f.get("meaning", "") for f in C.true_figures())
    prompt = (
        "Choose ONE sober poster layout for this post by " + C.company_name() + " and write its words. "
        "The poster is a flat card with very little text, so every word must earn its place.\n\n"
        "Layouts:\n"
        "- stat: one figure copied exactly from the true figures, a caption of 3-6 words in sentence "
        "case saying what it means.\n"
        "- partner: the post is about working with ONE listed partner; give its name.\n"
        "- statement: a headline of 3-8 plain words in sentence case, no figure, no hype, nothing the "
        "facts do not support (never 'eliminates', 'guaranteed', 'never', 'everywhere').\n"
        "All layouts: kicker = the topic in 1-2 words (e.g. 'Risk', 'Rebalancing', 'Integration'); "
        "footer = 2-4 plain words (e.g. 'Built on Stellar', 'Live on testnet'). "
        "No word of the kicker repeats in the caption or headline.\n\n"
        "TRUE FIGURES (the only numbers allowed):\n" + figures + "\n\n"
        "LISTED PARTNERS: " + ", ".join(C.partners().keys()) + "\n\n"
        "THE POST:\n" + " ".join(post.split())[:1600] + "\n\n"
        'Return JSON: {"variant": "stat"|"partner"|"statement", "kicker": str, "figure": str, '
        '"caption": str, "footer": str, "partners": [str], "headline": str}')
    out = R.brain_json(prompt, agent="A08_visual_synthesis", temperature=0.4)
    return out if isinstance(out, dict) else {}


def from_post(post: str, name: str, *, out_dir: Optional[Path] = None) -> dict[str, Any]:
    s = slots_for(post)
    variant = str(s.get("variant") or "statement")
    try:
        return render(variant, s, name, out_dir=out_dir)
    except ValueError as exc:
        print("  ledger: " + str(exc) + "; using the statement layout")
        from pipeline.brand_brain import context as C
        s["headline"] = s.get("headline") or s.get("caption") or C.company_line()
        return render("statement", s, name, out_dir=out_dir)


if __name__ == "__main__":
    import argparse
    import json

    ap = argparse.ArgumentParser(description="A Vanna Ledger poster from a post.")
    ap.add_argument("post")
    ap.add_argument("--name", default="sample")
    a = ap.parse_args()
    print(json.dumps(from_post(a.post, a.name), indent=1))
