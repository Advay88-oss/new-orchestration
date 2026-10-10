"""Vanna "Night Instrument" — a poster theme set from the brand itself, no references.

The idea: Vanna is credit infrastructure, so every post reads like a precise
instrument at night. One luminous form on the near-black ground carries the
post's mechanism (an isolated account, a rebalance, capital routed between
venues); a fine grid says infrastructure; the headline is the brand's heavy
sans with one word in the pink-to-violet gradient; a mono spec strip along the
bottom carries the true figures like a term sheet.

  ground     #07020D, violet glow low-left (#471485), magenta high-right (#5E0D46)
  art        drawn per post by the poster model on black, screened onto the ground
  type       Plus Jakarta Sans ExtraBold headline, JetBrains Mono kicker and specs
  gradient   pink #FF5C9E -> violet #A387FF on the one emphasis word

The agent (`slots_for`) reads the post and writes the kicker, headline,
emphasis word, spec items (true figures only) and the art direction. The
model draws the art fresh each run; the type is set in code so it is exact.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Optional

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont, ImageOps

REPO = Path(__file__).resolve().parents[2]
FONTS = REPO / "pipeline" / "assets" / "fonts"
OUT_DIR = REPO / "pipeline" / "state" / "vanna_theme"

W = H = 1600
M = 110                      # outer margin
GROUND = (7, 2, 13)
GLOW_LOW_LEFT = (71, 20, 133)
GLOW_HIGH_RIGHT = (94, 13, 70)
WHITE = (255, 255, 255)
MUTED = (150, 140, 170)
ACCENT_LIGHT = (163, 135, 255)
GRAD = ((255, 92, 158), (163, 135, 255))

ART_RULES = (
    "Full bleed: pure black (#000000) from edge to edge — no border, frame, margin or white "
    "anywhere. ONE luminous abstract form, "
    "drawn with thin precise lines of light and soft glow, in a gradient from pink (#FF5C9E) "
    "through magenta to violet (#703AE6). Flat and face-on, like a precise light diagram or an "
    "oscilloscope trace — minimal, elegant, generous empty black space, the form centred in the "
    "upper two thirds. ABSOLUTELY NO text, letters, numbers, logos, symbols or UI. Never coins, "
    "tokens, safes, vaults, boxes, buildings, people, hands or 3D isometric objects; no glass, "
    "no frosted panels.")


def _font(file: str, size: int, weight: Optional[int] = None) -> ImageFont.FreeTypeFont:
    f = ImageFont.truetype(str(FONTS / file), size)
    if weight is not None:
        try:
            f.set_variation_by_axes([weight])
        except Exception:                           # noqa: BLE001 — static font
            pass
    return f


def display(size: int, weight: int = 800) -> ImageFont.FreeTypeFont:
    return _font("plusjakartasans-var.ttf", size, weight)


def display_italic(size: int, weight: int = 800) -> ImageFont.FreeTypeFont:
    return _font("plusjakartasans-italic-var.ttf", size, weight)


def mono(size: int, weight: int = 500) -> ImageFont.FreeTypeFont:
    return _font("jetbrainsmono-var.ttf", size, weight)


# --------------------------------------------------------------------------
# Ground
# --------------------------------------------------------------------------

def _glow(colour, centre, radius, strength) -> Image.Image:
    mask = Image.new("L", (W, H), 0)
    cx, cy = centre
    ImageDraw.Draw(mask).ellipse((cx - radius, cy - radius, cx + radius, cy + radius),
                                 fill=int(255 * strength))
    mask = mask.filter(ImageFilter.GaussianBlur(radius * 0.45))
    return Image.composite(Image.new("RGB", (W, H), colour), Image.new("RGB", (W, H), GROUND), mask)


def ground() -> Image.Image:
    img = Image.new("RGB", (W, H), GROUND)
    img = ImageChops.lighter(img, _glow(GLOW_LOW_LEFT, (0, H), 900, 0.55))
    img = ImageChops.lighter(img, _glow(GLOW_HIGH_RIGHT, (W, 0), 760, 0.45))
    grid = Image.new("RGB", (W, H), (0, 0, 0))
    d = ImageDraw.Draw(grid)
    for x in range(M, W - M + 1, 115):
        d.line((x, 0, x, H), fill=(14, 10, 22), width=1)
    for y in range(M, H - M + 1, 115):
        d.line((0, y, W, y), fill=(14, 10, 22), width=1)
    img = ImageChops.add(img, grid)
    grain = Image.effect_noise((W, H), 10).convert("RGB")
    return Image.blend(img, ImageChops.lighter(img, grain.point(lambda v: max(0, v - 120))), 0.35)


# --------------------------------------------------------------------------
# Art (the model)
# --------------------------------------------------------------------------

def art(direction: str, out: Path, *, use_model: bool = True) -> tuple[Optional[Image.Image], bool]:
    if not use_model:
        return None, False
    try:
        from pipeline.gtm_creative.direct_image_posters import _model
        from pipeline.scripts.gemini_flash_image import generate_gemini_image

        generate_gemini_image(prompt="Make ONE square image.\n\nTHE FORM: " + direction + "\n\n" + ART_RULES,
                              output_path=out, model=_model(), temperature=0.8, aspect_ratio="1:1")
        if out.exists() and out.stat().st_size > 4096:
            return Image.open(out).convert("RGB"), True
    except Exception as exc:                        # noqa: BLE001 — boundary
        print("  vanna theme: art failed, poster without it: " + str(exc)[:160])
    return None, False


def _place_art(img: Image.Image, a: Image.Image) -> Image.Image:
    """Screen the art onto the ground, fading out above the headline."""
    # The model sometimes frames its black canvas in white; keep only the canvas.
    dark = a.convert("L").point(lambda v: 255 if v < 40 else 0)
    box = dark.getbbox()
    if box and (box[2] - box[0]) * (box[3] - box[1]) > 0.4 * a.width * a.height:
        a = a.crop(box)
    a = ImageOps.fit(a, (W, W), Image.Resampling.LANCZOS).resize((W, H))
    # Near-black in the art becomes true black, so its ground never shows as a box.
    a = a.point(lambda v: 0 if v < 18 else v)
    fade = Image.linear_gradient("L").resize((W, H)).point(
        lambda v: 255 if v < 130 else max(0, 255 - (v - 130) * 4))
    a = Image.composite(a, Image.new("RGB", (W, H)), fade)
    return ImageChops.screen(img, a)


# --------------------------------------------------------------------------
# Type
# --------------------------------------------------------------------------

def _gradient_fill(mask: Image.Image, box) -> Image.Image:
    x0, _, x1, _ = box
    span = max(1, x1 - x0)
    grad = Image.new("RGB", mask.size)
    gd = ImageDraw.Draw(grad)
    for x in range(mask.width):
        t = min(1.0, max(0.0, (x - x0) / span))
        gd.line((x, 0, x, mask.height),
                fill=tuple(int(GRAD[0][i] + (GRAD[1][i] - GRAD[0][i]) * t) for i in range(3)))
    return grad


def _tracked(d, xy, text, f, fill, track=0.14, anchor_right=False):
    w = sum(d.textlength(c, font=f) for c in text) + track * f.size * (len(text) - 1)
    x, y = xy
    if anchor_right:
        x -= w
    for c in text:
        d.text((x, y), c, font=f, fill=fill)
        x += d.textlength(c, font=f) + track * f.size
    return w


def _lines(words: list[str], fonts, max_w: int, d) -> list[list[str]]:
    lines, cur = [], []
    for w in words:
        trial = cur + [w]
        width = sum(d.textlength(x + " ", font=fonts(x)) for x in trial)
        if cur and width > max_w:
            lines.append(cur)
            cur = [w]
        else:
            cur = trial
    if cur:
        lines.append(cur)
    return lines


def headline(img: Image.Image, text: str, emphasis: str, bottom: int) -> None:
    d = ImageDraw.Draw(img)
    words = text.split()
    emph = {w.strip(".,!?").lower() for w in emphasis.split()} if emphasis else set()
    size = 118
    while size > 60:
        reg, ita = display(size), display_italic(size)

        def pick(w, reg=reg, ita=ita):
            return ita if w.strip(".,!?").lower() in emph else reg
        lines = _lines(words, pick, W - 2 * M, d)
        if len(lines) <= 3:
            break
        size -= 6
    lh = int(size * 1.08)
    y = bottom - lh * len(lines)
    for line in lines:
        x = M
        for w in line:
            f = pick(w)
            if w.strip(".,!?").lower() in emph:
                mask = Image.new("L", img.size, 0)
                ImageDraw.Draw(mask).text((x, y), w, font=f, fill=255)
                box = mask.getbbox() or (x, y, x + 10, y + 10)
                img.paste(_gradient_fill(mask, box), (0, 0), mask)
            else:
                d.text((x, y), w, font=f, fill=WHITE)
            x += d.textlength(w + " ", font=f)
        y += lh


def specs(img: Image.Image, items: list[dict], top: int) -> None:
    d = ImageDraw.Draw(img)
    d.line((M, top, W - M, top), fill=(60, 48, 82), width=2)
    if not items:
        return
    col = (W - 2 * M) // len(items)
    for i, it in enumerate(items[:3]):
        x = M + i * col
        _tracked(d, (x, top + 34), str(it.get("label", "")).upper(), mono(24, 500), MUTED, 0.12)
        d.text((x, top + 74), str(it.get("value", "")), font=mono(46, 700), fill=WHITE)


def top_bar(img: Image.Image, kicker: str) -> None:
    hires = REPO / "pipeline" / "assets" / "logos" / "vanna_hires.png"
    if hires.exists():
        src = Image.open(hires).convert("RGBA")
        src = src.crop(src.getchannel("A").getbbox())
        h = 62
        mark = src.resize((int(src.width * h / src.height), h), Image.Resampling.LANCZOS)
        img.paste(mark, (M, M - 10), mark)
    if kicker:
        d = ImageDraw.Draw(img)
        _tracked(d, (W - M, M + 6), kicker.upper(), mono(26, 600), ACCENT_LIGHT, 0.16, anchor_right=True)


# --------------------------------------------------------------------------
# Render
# --------------------------------------------------------------------------

def check_figures(texts: list[str]) -> list[str]:
    from pipeline.brand_brain import context as C

    allowed = " ".join(f["value"] for f in C.true_figures()).lower()
    return [n for t in texts for n in re.findall(r"\d[\d,.]*", t or "")
            if n.rstrip(".,").lower() not in allowed]


def render(slots: dict[str, Any], name: str, *, out_dir: Optional[Path] = None,
           use_model: bool = True, art_path: Optional[Path] = None) -> dict[str, Any]:
    items = [i for i in (slots.get("specs") or []) if isinstance(i, dict)][:3]
    texts = [str(slots.get(k) or "") for k in ("kicker", "headline")] + \
            [str(i.get("label", "")) + " " + str(i.get("value", "")) for i in items]
    bad = check_figures(texts)
    if bad:
        raise ValueError("figures not in the brand's true figures: " + ", ".join(bad))
    out_dir = Path(out_dir or OUT_DIR)
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / (name + ".png")
    img = ground()
    if art_path and Path(art_path).exists():
        a, made = Image.open(art_path).convert("RGB"), True
    else:
        a, made = art(str(slots.get("art") or "a single luminous ring of light"),
                      out.with_name(name + "_art.png"), use_model=use_model)
    if a is not None:
        img = _place_art(img, a)
    top_bar(img, str(slots.get("kicker") or ""))
    strip_top = H - M - 130
    specs(img, items, strip_top)
    headline(img, str(slots.get("headline") or ""), str(slots.get("emphasis") or ""), strip_top - 60)
    img.save(out)
    return {"path": str(out), "art_by_model": made, "slots": slots}


def slots_for(post: str) -> dict[str, Any]:
    """The agent's reading of a post: kicker, headline, emphasis, specs, art."""
    from pipeline.brand_brain import context as C
    from pipeline.gtm_os import agent_runtime as R

    figures = "\n".join("- " + f["value"] + ": " + f.get("meaning", "") for f in C.true_figures())
    prompt = (
        "You art-direct ONE poster for this post by " + C.company_name() + " in its 'Night Instrument' "
        "theme: a near-black ground, one luminous abstract light form that shows the post's mechanism, "
        "a heavy headline with one word in a pink-to-violet gradient, and a mono spec strip like a term sheet.\n\n"
        "Write:\n"
        "- kicker: the topic in 1-3 words (e.g. 'Risk isolation', 'Rebalancing').\n"
        "- headline: sentence case, 3-7 words, plain words a stranger gets in three seconds; no figure; "
        "no promise the facts do not support (never 'eliminates', 'guaranteed', 'never').\n"
        "- emphasis: ONE word copied from the headline.\n"
        "- specs: 1-3 items {label (1-3 words), value}; each value copied exactly from the true figures, "
        "or 'Stellar Soroban' / 'Testnet' as a value. Labels must not repeat the headline.\n"
        "- art: one or two sentences describing an abstract light form that shows THIS mechanism "
        "(e.g. 'four separate rings of light, one cracked and dimmed while the other three glow intact' "
        "for isolation). Lines, rings, waves, paths, nodes only — no objects, no text.\n\n"
        "TRUE FIGURES (the only numbers allowed):\n" + figures + "\n\n"
        "THE POST:\n" + " ".join(post.split())[:1600] + "\n\n"
        'Return JSON: {"kicker": str, "headline": str, "emphasis": str, '
        '"specs": [{"label": str, "value": str}], "art": str}')
    out = R.brain_json(prompt, agent="A08_visual_synthesis", temperature=0.5)
    return out if isinstance(out, dict) else {}


def from_post(post: str, name: str, *, out_dir: Optional[Path] = None) -> dict[str, Any]:
    s = slots_for(post)
    try:
        return render(s, name, out_dir=out_dir)
    except ValueError as exc:
        print("  vanna theme: " + str(exc) + "; dropping the specs")
        return render({**s, "specs": []}, name, out_dir=out_dir)


if __name__ == "__main__":
    import argparse
    import json

    ap = argparse.ArgumentParser(description="A Night Instrument poster from a post.")
    ap.add_argument("post")
    ap.add_argument("--name", default="sample")
    a = ap.parse_args()
    print(json.dumps(from_post(a.post, a.name), indent=1))
