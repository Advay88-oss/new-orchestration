"""Engraved-card posters: the founder's reference pattern, drawn the same way every time.

The pattern (three references in `pipeline/assets/style_refs/engraved/`):
a monochrome duotone engraving or halftone fills the frame, and a flat
opaque card sits centred on it — a small-caps label, one large serif figure
or name, a tracked mono caption, and a lockup of names joined by "+" or "x".

The image model (the run's poster model) draws only the textless engraving,
shown the references so its linework matches theirs. Everything readable is
set here in code, so spelling, figures and the logo are exact. The model's
texture is then forced into the duotone, so its colour never drifts.

Variants:
  stat     — cream card: label, big serif figure, caption, "BUILT ON" lockup
  partner  — pink card: the company logo "x" a partner name
  engraving — no card: a dark headline set straight onto a pale engraving
"""
from __future__ import annotations

import random
import re
from pathlib import Path
from typing import Any, Optional

from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

REPO = Path(__file__).resolve().parents[2]
FONTS = REPO / "pipeline" / "assets" / "fonts"
REFS = REPO / "pipeline" / "assets" / "style_refs" / "engraved"
OUT_DIR = REPO / "pipeline" / "state" / "engraved_posters"

# Sampled from the references. "vanna" keeps the pattern in the brand's violet.
PALETTES = {
    "reference": {
        "stat": {"dark": "#16302C", "light": "#9DB1AB", "card": "#EBE6DD", "ink": "#1E3A36"},
        "partner": {"dark": "#1B3834", "light": "#C9D5D0", "card": "#D9B8BD", "ink": "#203B37"},
        "engraving": {"dark": "#2C4A3D", "light": "#CBD5C6", "ink": "#2A4639"},
    },
    # Vanna: ground #07020D, violet #471485 / #703AE6 / #A387FF, pink #5E0D46.
    "vanna": {
        "stat": {"dark": "#0F0520", "light": "#8B6FD6", "card": "#EEEAF6", "ink": "#1B0A35"},
        "partner": {"dark": "#12061F", "light": "#A387FF", "card": "#EBC3D8", "ink": "#2A0B2E"},
        "engraving": {"dark": "#2A1258", "light": "#DCD3F2", "ink": "#22104A"},
    },
}

SIZES = {"stat": (1600, 1200), "partner": (1600, 1200), "engraving": (1600, 800)}
MODEL_ASPECT = {"stat": "4:3", "partner": "4:3", "engraving": "16:9"}

TEXTURES = {
    "stat": ("a financial candlestick chart rising in front of a dense city skyline, "
             "rendered as a coarse halftone screen print with fine vertical streaks"),
    "partner": ("large concentric swirling guilloche rings and ripples drawn in stippled "
                "dots and fine noise, like a security-print pattern"),
    "engraving": ("an intaglio banknote engraving of an imagined classical columned bank building "
                  "(not any real landmark or government building) with trees beside it, fine "
                  "cross-hatched linework like the back of a banknote"),
}

REF_FILES = {"stat": "stat_card.jpg", "partner": "partner_card.jpg", "engraving": "engraving_type.jpg"}


def _font(name: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONTS / name), size)


SERIF = "instrumentserif-regular.ttf"
MONO = "dmmono-medium.ttf"
SANS = "inter-semibold.ttf"
SANS_BOLD = "inter-bold.ttf"


def _rgb(hex_: str) -> tuple[int, int, int]:
    h = hex_.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))  # type: ignore[return-value]


# --------------------------------------------------------------------------
# Facts: nothing reaches the card that the brand profile does not hold
# --------------------------------------------------------------------------

def check_text(texts: list[str]) -> list[str]:
    """Figures in the text that are not one of the brand's true figures."""
    from pipeline.brand_brain import context as C

    allowed = " ".join(f["value"] for f in C.true_figures()).lower()
    bad = []
    for t in texts:
        for num in re.findall(r"\d[\d,.]*", t or ""):
            if num.rstrip(".,").lower() not in allowed:
                bad.append(num)
    return bad


# --------------------------------------------------------------------------
# The engraving
# --------------------------------------------------------------------------

def _texture_prompt(variant: str) -> str:
    return (
        "Make ONE textless background texture in the exact print style of the attached reference image.\n\n"
        "SUBJECT: " + TEXTURES[variant] + ".\n\n"
        "STYLE: monochrome only — a single ink on paper, like an engraving or halftone print. "
        "Visible dot screen, film grain and fine linework, matching the reference's density and "
        "contrast. Full bleed, edge to edge.\n\n"
        "ABSOLUTELY NO TEXT: no letters, numbers, words, logos, symbols, watermarks, cards, frames, "
        "panels or borders. Do not copy the card or the words in the reference — copy only its "
        "background texture. Flat and face-on.")


def _procedural(variant: str, size: tuple[int, int], seed: int) -> Image.Image:
    """A guilloche-and-noise ground for when the model is unreachable."""
    W, H = size
    rnd = random.Random(seed)
    img = Image.new("L", size, 90)
    d = ImageDraw.Draw(img)
    cx, cy = rnd.randint(0, W), rnd.randint(0, H)
    for r in range(20, int(max(W, H) * 1.3), 18):
        d.ellipse((cx - r, cy - r * 0.8, cx + r, cy + r * 0.8), outline=rnd.choice((170, 200, 230)), width=3)
    noise = Image.effect_noise(size, 70)
    return Image.blend(img, noise, 0.45)


def _duotone(src: Image.Image, size: tuple[int, int], dark: str, light: str) -> Image.Image:
    """The texture cropped to size and forced into two inks, plus grain."""
    img = ImageOps.fit(src.convert("L"), size, Image.Resampling.LANCZOS)
    img = ImageOps.autocontrast(img, cutoff=1)
    grain = Image.effect_noise(size, 28).convert("L")
    img = Image.blend(img, grain, 0.12)
    return ImageOps.colorize(img, black=_rgb(dark), white=_rgb(light)).convert("RGB")


def engraving(variant: str, size: tuple[int, int], pal: dict, out: Path,
              *, use_model: bool = True, seed: int = 7,
              texture: Optional[Path] = None) -> tuple[Image.Image, bool]:
    """The duotone ground and whether the image model drew it. `texture`
    reuses a ground the model drew before; it is recoloured either way."""
    if texture and Path(texture).exists():
        return _duotone(Image.open(texture), size, pal["dark"], pal["light"]), True
    raw = out.with_name(out.stem + "_texture.png")
    made = False
    if use_model:
        try:
            from pipeline.gtm_creative.direct_image_posters import _model
            from pipeline.scripts.gemini_flash_image import generate_gemini_image

            generate_gemini_image(prompt=_texture_prompt(variant), output_path=raw,
                                  model=_model(), temperature=0.5,
                                  images=[REFS / REF_FILES[variant]],
                                  aspect_ratio=MODEL_ASPECT[variant])
            made = raw.exists() and raw.stat().st_size > 4096
        except Exception as exc:                    # noqa: BLE001 — boundary
            print("  engraving: model texture failed, using the drawn one: " + str(exc)[:160])
    src = Image.open(raw) if made else _procedural(variant, size, seed)
    return _duotone(src, size, pal["dark"], pal["light"]), made


# --------------------------------------------------------------------------
# Type and lockups
# --------------------------------------------------------------------------

def _tracked(d: ImageDraw.ImageDraw, text: str, f: ImageFont.FreeTypeFont, track: float) -> int:
    return int(sum(d.textlength(c, font=f) for c in text) + track * f.size * max(0, len(text) - 1))


def _draw_tracked(d, cx: int, y: int, text: str, f, fill, track: float) -> int:
    """Centred, letter-spaced text; returns the y below it."""
    w = _tracked(d, text, f, track)
    x = cx - w / 2
    for c in text:
        d.text((x, y), c, font=f, fill=fill)
        x += d.textlength(c, font=f) + track * f.size
    box = d.textbbox((0, 0), "HG", font=f)
    return y + box[3]


def _fit(d, text: str, name: str, size: int, max_w: int, track: float = 0.0) -> ImageFont.FreeTypeFont:
    f = _font(name, size)
    while size > 12 and _tracked(d, text, f, track) > max_w:
        size -= 4
        f = _font(name, size)
    return f


def _logo_ink(height: int, ink: str) -> Optional[Image.Image]:
    """The company lockup as a one-ink silhouette, like the references' logos."""
    from pipeline.brand_brain import context as C
    from pipeline.gtm_creative.brand import logo

    # The brain's logo is small; scaled up to card size it goes jagged.
    hires = REPO / "pipeline" / "assets" / "logos" / (C.company_name().lower() + "_hires.png")
    if hires.exists():
        src = Image.open(hires).convert("RGBA")
        src = src.crop(src.getchannel("A").getbbox() or (0, 0, src.width, src.height))
        mark = src.resize((max(1, int(src.width * height / src.height)), height), Image.Resampling.LANCZOS)
    else:
        mark = logo(height)
    if mark is None:
        return None
    solid = Image.new("RGBA", mark.size, _rgb(ink) + (255,))
    solid.putalpha(mark.getchannel("A"))
    return solid


def _wordmark(name: str, height: int, ink: str) -> Image.Image:
    f = _font(SANS, int(height * 0.95))
    probe = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    l, t, r, b = probe.textbbox((0, 0), name, font=f)
    im = Image.new("RGBA", (r - l + 4, b - t + 4), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((-l + 2, -t + 2), name, font=f, fill=_rgb(ink))
    return im


def _company_mark(height: int, ink: str) -> Image.Image:
    from pipeline.brand_brain import context as C
    return _logo_ink(height, ink) or _wordmark(C.company_name().lower(), height, ink)


def _row(parts: list[Image.Image], gap: int) -> Image.Image:
    w = sum(p.width for p in parts) + gap * (len(parts) - 1)
    h = max(p.height for p in parts)
    row = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    x = 0
    for p in parts:
        row.alpha_composite(p, (x, (h - p.height) // 2))
        x += p.width + gap
    return row


def _joiner(sym: str, height: int, ink: str) -> Image.Image:
    return _wordmark(sym, height, ink)


# --------------------------------------------------------------------------
# Variants
# --------------------------------------------------------------------------

def _card(img: Image.Image, frac_w: float, frac_h: float, colour: str) -> tuple[int, int, int, int]:
    W, H = img.size
    cw, ch = int(W * frac_w), int(H * frac_h)
    box = ((W - cw) // 2, (H - ch) // 2, (W + cw) // 2, (H + ch) // 2)
    ImageDraw.Draw(img).rectangle(box, fill=_rgb(colour))
    return box


def _stat(img: Image.Image, pal: dict, s: dict) -> None:
    box = _card(img, 0.62, 0.70, pal["card"])
    d = ImageDraw.Draw(img)
    x0, y0, x1, y1 = box
    cx, cw = (x0 + x1) // 2, x1 - x0
    ink = _rgb(pal["ink"])

    y = y0 + int((y1 - y0) * 0.17)
    f = _fit(d, s["label"].upper(), SANS, 54, int(cw * 0.8), 0.04)
    y = _draw_tracked(d, cx, y, s["label"].upper(), f, ink, 0.04) + 40

    f = _fit(d, s["figure"], SERIF, 210, int(cw * 0.86))
    l, t, r, b = d.textbbox((0, 0), s["figure"], font=f)
    d.text((cx - (r - l) / 2 - l, y - t), s["figure"], font=f, fill=ink)
    y += (b - t) + 34

    if s.get("caption"):
        f = _fit(d, s["caption"].upper(), MONO, 32, int(cw * 0.8), 0.12)
        _draw_tracked(d, cx, y, s["caption"].upper(), f, ink, 0.12)

    lock_h = 50
    parts = [_company_mark(lock_h, pal["ink"])]
    for name in s.get("partners") or []:
        parts += [_joiner("+", lock_h, pal["ink"]), _wordmark(name, lock_h, pal["ink"])]
    row = _row(parts, 22)
    if row.width > cw * 0.8:
        row = row.resize((int(cw * 0.8), int(row.height * cw * 0.8 / row.width)), Image.Resampling.LANCZOS)
    ry = y1 - int((y1 - y0) * 0.11) - row.height
    if s.get("partners"):
        f = _font(MONO, 20)
        _draw_tracked(d, cx, ry - 44, (s.get("lockup_label") or "BUILT ON").upper(), f, ink, 0.14)
    img.paste(row, (cx - row.width // 2, ry), row)


def _partner(img: Image.Image, pal: dict, s: dict) -> None:
    box = _card(img, 0.70, 0.70, pal["card"])
    x0, y0, x1, y1 = box
    cx, cy, cw = (x0 + x1) // 2, (y0 + y1) // 2, x1 - x0
    top = _company_mark(118, pal["ink"])
    bottom = _wordmark(s["partners"][0], 96, pal["ink"])
    for im in (top, bottom):
        if im.width > cw * 0.78:
            im.thumbnail((int(cw * 0.78), im.height), Image.Resampling.LANCZOS)
    x = _joiner("\u00d7", 40, pal["ink"])
    gap = 70
    total = top.height + gap + x.height + gap + bottom.height
    y = cy - total // 2
    img.paste(top, (cx - top.width // 2, y), top)
    y += top.height + gap
    img.paste(x, (cx - x.width // 2, y), x)
    y += x.height + gap
    img.paste(bottom, (cx - bottom.width // 2, y), bottom)


def _engraving_type(img: Image.Image, pal: dict, s: dict) -> None:
    W, H = img.size
    d = ImageDraw.Draw(img)
    text = s["headline"].upper()
    f = _fit(d, text, SANS_BOLD, 150, int(W * 0.78), 0.0)
    l, t, r, b = d.textbbox((0, 0), text, font=f)
    x, y = (W - (r - l)) / 2 - l, (H - (b - t)) / 2 - t
    halo = Image.new("L", img.size, 0)
    ImageDraw.Draw(halo).text((x, y), text, font=f, fill=255, stroke_width=10, stroke_fill=255)
    halo = halo.filter(ImageFilter.GaussianBlur(14)).point(lambda v: int(v * 0.55))
    img.paste(Image.new("RGB", img.size, _rgb(pal["light"])), (0, 0), halo)
    d.text((x, y), text, font=f, fill=_rgb(pal["ink"]))


DRAW = {"stat": _stat, "partner": _partner, "engraving": _engraving_type}


def render(variant: str, slots: dict[str, Any], name: str, *, palette: str = "vanna",
           out_dir: Optional[Path] = None, use_model: bool = True, seed: int = 7,
           texture: Optional[Path] = None) -> dict[str, Any]:
    """One engraved-card poster. `slots`:
      stat:      label, figure, caption, partners [names], lockup_label
      partner:   partners [one name]
      engraving: headline
    Raises ValueError on a figure the brand profile does not hold."""
    from pipeline.brand_brain import context as C

    if variant not in DRAW:
        raise ValueError("unknown variant " + repr(variant))
    texts = [str(v) for k, v in slots.items() if isinstance(v, str)]
    bad = check_text(texts)
    if bad:
        raise ValueError("figures not in the brand's true figures: " + ", ".join(bad))
    for p in slots.get("partners") or []:
        if not C.is_partner(p):
            raise ValueError(repr(p) + " is not a listed partner")
    if variant == "partner" and not slots.get("partners"):
        raise ValueError("the partner variant needs one partner name")

    pal = PALETTES[palette][variant]
    out_dir = Path(out_dir or OUT_DIR)
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / (name + ".png")
    img, made = engraving(variant, SIZES[variant], pal, out, use_model=use_model, seed=seed,
                          texture=texture)
    DRAW[variant](img, pal, slots)
    img.save(out)
    return {"path": str(out), "variant": variant, "palette": palette,
            "texture_by_model": made, "slots": slots}


# --------------------------------------------------------------------------
# From a post: the visual agent picks the variant and fills the slots
# --------------------------------------------------------------------------

def slots_for(post: str) -> dict[str, Any]:
    """The variant and slots for a post, chosen by the model from the true figures only."""
    from pipeline.brand_brain import context as C
    from pipeline.gtm_os import agent_runtime as R

    figures = "\n".join("- " + f["value"] + ": " + f.get("meaning", "") for f in C.true_figures())
    partners = ", ".join(C.partners().keys())
    prompt = (
        "Choose ONE poster layout for this post by " + C.company_name() + " and fill its slots.\n\n"
        "Layouts:\n"
        "- stat: a card with a short label (2-3 words), ONE figure copied exactly from the list, "
        "a caption (2-4 words) saying what the figure is, and up to 2 partner names. The caption "
        "must not repeat any word of the label (label \"Liquidation floor\", caption \"health factor\").\n"
        "- partner: a card pairing the company with ONE partner name (an integration post).\n"
        "- engraving: one headline of 2-4 words, no figure.\n\n"
        "TRUE FIGURES (the only numbers allowed, copied exactly):\n" + figures + "\n\n"
        "PARTNER NAMES (the only ones allowed): " + partners + "\n\n"
        "THE POST:\n" + " ".join(post.split())[:1600] + "\n\n"
        'Return JSON: {"variant": "stat"|"partner"|"engraving", "label": str, "figure": str, '
        '"caption": str, "partners": [str], "lockup_label": str, "headline": str}')
    out = R.brain_json(prompt, agent="A08_visual_synthesis", temperature=0.3)
    return out if isinstance(out, dict) else {}


def from_post(post: str, name: str, *, palette: str = "vanna",
              out_dir: Optional[Path] = None) -> dict[str, Any]:
    s = slots_for(post)
    variant = str(s.get("variant") or "engraving")
    try:
        return render(variant, s, name, palette=palette, out_dir=out_dir)
    except ValueError as exc:
        # A slot that broke the facts rule falls back to the headline-only layout.
        print("  engraved poster: " + str(exc) + "; using the headline layout")
        from pipeline.brand_brain import context as C
        headline = str(s.get("headline") or s.get("label") or C.company_name())
        return render("engraving", {"headline": headline}, name, palette=palette, out_dir=out_dir)


if __name__ == "__main__":
    import argparse
    import json

    ap = argparse.ArgumentParser(description="Render an engraved-card poster.")
    ap.add_argument("variant", choices=list(DRAW))
    ap.add_argument("--name", default="sample")
    ap.add_argument("--palette", default="vanna", choices=list(PALETTES))
    ap.add_argument("--label", default="")
    ap.add_argument("--figure", default="")
    ap.add_argument("--caption", default="")
    ap.add_argument("--partner", action="append", default=[])
    ap.add_argument("--lockup-label", default="BUILT ON")
    ap.add_argument("--headline", default="")
    ap.add_argument("--no-model", action="store_true")
    ap.add_argument("--texture", default=None, help="reuse a texture the model drew before")
    a = ap.parse_args()
    slots = {"label": a.label, "figure": a.figure, "caption": a.caption, "partners": a.partner,
             "lockup_label": a.lockup_label, "headline": a.headline}
    print(json.dumps(render(a.variant, slots, a.name, palette=a.palette,
                            use_model=not a.no_model, texture=a.texture), indent=1))
