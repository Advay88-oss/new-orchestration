#!/usr/bin/env python3
"""Branded short-form video renderer (the frame-exact 'Remotion role').

Per VIDEO-PRODUCTION-SPEC + the crypto-video-style teardown: every readable
element — hook, stat, kinetic word, logo, CTA — is rendered deterministically in
the tenant's OKF palette (PIL frames -> ffmpeg MP4), never AI-generated, so text
stays crisp and on-brand. AI B-roll (Runway/Veo) is an OPTIONAL background layer,
composited only when RUNWAY_API_KEY is set.

Styles (from the analysed reference videos):
  card    — hook + emphasis chip + subhead + CTA (default)
  stat    — huge single number reveal + label (e.g. "$5B+ / Total Deposits")
  kinetic — bold word-by-word typography reveals + accent squares + 0x hex tag

    python render_video.py --brief b.json --out clip.mp4 --style stat --bg gradient --accent #2f7bff
"""
from __future__ import annotations

import argparse
import json
import math
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent))
import render_visual as rv  # noqa: E402  (applies OKF palette from OKF_BUNDLE at import)

W = H = 1080
FPS = 15
DURATION = 7.0
N = int(FPS * DURATION)


def _ffmpeg() -> str:
    return shutil.which("ffmpeg") or "ffmpeg"


def _hex(c: str) -> tuple[int, int, int]:
    c = str(c).lstrip("#")
    return tuple(int(c[i:i + 2], 16) for i in (0, 2, 4))  # type: ignore


_FONTS = Path(__file__).resolve().parents[1] / "assets" / "fonts"
# Exact reference-look sans. VANNA_FONT can point at a licensed family dir
# (e.g. Helvetica Now); default is Inter (bundled). Arial is the last resort.
_FONT_DIR = Path(os.environ.get("VANNA_FONT_DIR", str(_FONTS)))


def _font(size: int, bold: bool = True) -> ImageFont.FreeTypeFont:
    cands = ([_FONT_DIR / "inter-extrabold.ttf", _FONT_DIR / "inter-bold.ttf", "arialbd.ttf", "arial.ttf"]
             if bold else [_FONT_DIR / "inter-regular.ttf", _FONT_DIR / "inter-semibold.ttf", "arial.ttf"])
    cands += [r"C:\Windows\Fonts\arialbd.ttf", r"C:\Windows\Fonts\arial.ttf"]
    for p in cands:
        try:
            return ImageFont.truetype(str(p), size)
        except Exception:
            pass
    return ImageFont.load_default()


def _wrap(draw, text, font, max_w):
    words, lines, cur = str(text).split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if draw.textlength(t, font=font) <= max_w:
            cur = t
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def _palette(accent_override: str | None):
    bg = _hex(rv.BACKGROUND)
    try:
        accent_hex = accent_override or (list(rv.ACCENT.values())[0] if getattr(rv, "ACCENT", None) else "#8B5CF6")
    except Exception:
        accent_hex = accent_override or "#8B5CF6"
    return bg, _hex(accent_hex)


def _base(bg_mode: str, bg: tuple, accent: tuple) -> Image.Image:
    """Background plate, built once and copied per frame."""
    import numpy as np
    yy = np.linspace(0, 1, H)[:, None]
    xx = np.linspace(0, 1, W)[None, :]
    if bg_mode == "light":
        arr = np.full((H, W, 3), 232, dtype=float)
    elif bg_mode == "blue":
        arr = np.array(accent, dtype=float)[None, None, :] * np.ones((H, W, 1))
    elif bg_mode == "gradient":
        # glossy diagonal gradient in the accent hue (V4 orb look)
        g = np.clip((xx * 0.6 + yy * 0.6), 0, 1)[:, :, None]
        dark = np.array(accent, dtype=float) * 0.55
        arr = dark[None, None, :] * (1 - g) + np.array(accent, dtype=float)[None, None, :] * g
        rad = np.sqrt((xx - 0.75) ** 2 + (yy - 0.15) ** 2)
        glow = np.clip(1 - rad * 1.2, 0, 1)[:, :, None]
        arr = arr * (1 - glow * 0.5) + np.array([255, 255, 255])[None, None, :] * (glow * 0.5)
    else:  # dark (default) — subtle accent glow top-centre + grid feel
        rad = np.sqrt((xx - 0.5) ** 2 + (yy - 0.35) ** 2)
        glow = np.clip(1 - rad * 1.5, 0, 1)[:, :, None]
        arr = np.array(bg, dtype=float)[None, None, :] * (1 - glow * 0.28) + np.array(accent, dtype=float)[None, None, :] * (glow * 0.28)
    return Image.fromarray(np.clip(arr, 0, 255).astype("uint8"), "RGB")


def _load_logo(px: int = 150):
    try:
        if rv.LOGO_PATH and Path(rv.LOGO_PATH).exists():
            lg = Image.open(rv.LOGO_PATH).convert("RGBA")
            return lg.resize((px, int(lg.height * px / lg.width)))
    except Exception:
        pass
    return None


# ----------------------------------------------------------- style: card
def _draw_card(d, img, t, B, accent, ink, mut, logo):
    if logo is not None:
        a = min(1.0, t / 0.15)
        lg = logo.copy()
        if a < 1:
            lg.putalpha(lg.split()[3].point(lambda p: int(p * a)))
        img.paste(lg, (70, 70), lg)
    d.rectangle([70, 250, 70 + int((W - 140) * min(1.0, t / 0.3)), 256], fill=accent)
    y = 300
    hook = _wrap(d, B.get("headline") or B.get("hook") or "", _font(66), W - 140)[:3]
    reveal = int(len(hook) * min(1.0, max(0, (t - 0.1) / 0.4)) + 0.999)
    for ln in hook[:reveal]:
        d.text((70, y), ln, font=_font(66), fill=ink); y += 82
    emph = str(B.get("emphasis_phrase") or B.get("emphasis") or "").strip()
    if emph and t > 0.45:
        a = min(1.0, (t - 0.45) / 0.2)
        fe = _font(84)
        d.rounded_rectangle([70, y + 20, 70 + int(d.textlength(emph, font=fe)) + 48, y + 130], radius=16, fill=(*accent, int(40 * a)))
        d.text((94, y + 34), emph, font=fe, fill=(*accent, int(255 * a))); y += 150
    sub = str(B.get("subhead") or B.get("body") or "").strip()
    if sub and t > 0.6:
        for ln in _wrap(d, sub, _font(34, False), W - 140)[:3]:
            d.text((70, y + 30), ln, font=_font(34, False), fill=mut); y += 44
    cta = str(B.get("cta") or "").strip()
    if cta and t > 0.75:
        fc = _font(38); cw = int(d.textlength(cta, font=fc)) + 64
        d.rounded_rectangle([70, H - 150, 70 + cw, H - 76], radius=37, fill=accent)
        d.text((102, H - 134), cta, font=fc, fill=_hex(rv.BACKGROUND))
    pr = 10 + 4 * math.sin(t * math.pi * 6)
    d.ellipse([W - 90 - pr, H - 90 - pr, W - 90 + pr, H - 90 + pr], outline=accent, width=3)


# ----------------------------------------------------------- style: stat
def _draw_stat(d, img, t, B, accent, ink, mut, logo):
    stat = str(B.get("stat") or B.get("headline") or B.get("emphasis") or "").strip()
    label = str(B.get("label") or B.get("subhead") or B.get("body") or "").strip()
    # huge number scales + fades in
    a = min(1.0, t / 0.35)
    scale = 0.8 + 0.2 * a
    size = int(230 * scale)
    fS = _font(size)
    tw = d.textlength(stat, font=fS)
    white = (255, 255, 255)
    # semi-transparent draw for fade
    d.text(((W - tw) / 2, H * 0.28), stat, font=fS, fill=(*white, int(255 * a)))
    if label and t > 0.4:
        la = min(1.0, (t - 0.4) / 0.25)
        fL = _font(44, False)
        for k, ln in enumerate(_wrap(d, label, fL, W - 220)[:2]):
            lw = d.textlength(ln, font=fL)
            d.text(((W - lw) / 2, H * 0.52 + k * 56), ln, font=fL, fill=(235, 240, 255, int(220 * la)))
    # logo chips bottom-centre
    if logo is not None and t > 0.55:
        lg = logo.resize((72, int(logo.height * 72 / logo.width)))
        img.paste(lg, (int(W / 2 - 40), H - 150), lg)


# -------------------------------------------------------- style: kinetic
def _draw_kinetic(d, img, t, B, accent, ink, mut, logo, dark: bool):
    words = B.get("words") or B.get("lines") or [B.get("headline") or B.get("hook") or ""]
    if isinstance(words, str):
        words = [words]
    hextag = str(B.get("hex_tag") or "0x" + "".join(["A", "B", "C", "D"][:4])).strip()
    txt_col = (245, 245, 250) if dark else (20, 20, 24)
    # which phrase is active
    seg = 1.0 / max(1, len(words))
    idx = min(len(words) - 1, int(t / seg))
    local = (t - idx * seg) / seg  # 0..1 within this word
    phrase = str(words[idx])
    fW = _font(96)
    lines = _wrap(d, phrase, fW, W - 200)[:2]
    a = min(1.0, local / 0.25) * (1.0 if local < 0.85 else max(0.0, (1 - local) / 0.15))
    y = H / 2 - len(lines) * 60
    for ln in lines:
        lw = d.textlength(ln, font=fW)
        d.text((W / 2 - lw / 2, y), ln, font=fW, fill=(*txt_col, int(255 * a))); y += 118
    # floating blue accent squares (parallax)
    for k, (px, py, s) in enumerate([(0.18, 0.22, 26), (0.82, 0.3, 34), (0.7, 0.72, 22), (0.28, 0.78, 18)]):
        off = int(14 * math.sin(t * math.pi * 2 + k))
        x0 = int(W * px) + off; y0 = int(H * py) - off
        d.rectangle([x0, y0, x0 + s, y0 + s], fill=accent)
    # hex address tag bottom-right (mono-ish)
    fh = _font(24, False)
    d.rectangle([W - 260, H - 90, W - 260 + 18, H - 72], fill=accent)
    d.text((W - 232, H - 92), hextag, font=fh, fill=(txt_col if dark else (90, 90, 100)))


# -------------------------------------------------------- style: mockup
def _countup(value: str, frac: float) -> str:
    """Animate a numeric value from 0 -> value; keep any prefix/suffix."""
    import re
    m = re.search(r"[-+]?\d[\d,]*\.?\d*", value or "")
    if not m:
        return value
    num = m.group(0)
    try:
        target = float(num.replace(",", ""))
    except Exception:
        return value
    cur = target * max(0.0, min(1.0, frac))
    dec = 2 if "." in num else 0
    shown = f"{cur:,.{dec}f}"
    return value[:m.start()] + shown + value[m.end():]


def _draw_mockup(d, img, t, B, accent, ink, mut, logo):
    """A SYNTHETIC app-UI card (recreated, not a screenshot): logo + wallet chip,
    a counting-up hero stat, a token row, and a CTA button with a tap ripple."""
    title = str(B.get("title") or B.get("headline") or "").strip()
    stat_label = str(B.get("stat_label") or "Supply APY").strip()
    stat_value = str(B.get("stat_value") or B.get("stat") or "378.88%").strip()
    token = str(B.get("token") or "XLM").strip()
    balance = str(B.get("balance") or "1,307.36 XLM").strip()
    cta = str(B.get("cta") or "Supply").strip()
    wallet = str(B.get("wallet") or "GC2D…PY6X").strip()
    card = (24, 20, 38)

    # card slides up + fades in
    a = min(1.0, t / 0.18)
    cy = int(40 * (1 - a))
    x0, y0, x1, y1 = 150, 210 + cy, 930, 900 + cy
    d.rounded_rectangle([x0, y0, x1, y1], radius=28, fill=(*card, int(255 * a)), outline=(*accent, int(90 * a)), width=2)
    if a < 0.35:
        return
    # header: logo + product + wallet chip
    if logo is not None:
        lg = logo.resize((54, int(logo.height * 54 / logo.width)))
        img.paste(lg, (x0 + 34, y0 + 34), lg)
    d.text((x0 + 100, y0 + 44), title or "Vanna", font=_font(34), fill=ink)
    fw = _font(24, False)
    ww = int(d.textlength(wallet, font=fw)) + 34
    d.rounded_rectangle([x1 - 34 - ww, y0 + 40, x1 - 34, y0 + 82], radius=21, fill=(40, 34, 58))
    d.text((x1 - 34 - ww + 17, y0 + 48), wallet, font=fw, fill=mut)
    # hero stat, counting up
    if t > 0.2:
        f2 = min(1.0, (t - 0.2) / 0.4)
        d.text((x0 + 44, y0 + 150), stat_label, font=_font(30, False), fill=mut)
        d.text((x0 + 44, y0 + 190), _countup(stat_value, f2), font=_font(120), fill=accent)
    # token row
    if t > 0.5:
        ry = y0 + 360
        d.rounded_rectangle([x0 + 44, ry, x1 - 44, ry + 96], radius=16, fill=(34, 28, 50))
        d.ellipse([x0 + 64, ry + 24, x0 + 112, ry + 72], fill=accent)
        gl = token[:1]
        gw = d.textlength(gl, font=_font(28))
        d.text((x0 + 88 - gw / 2, ry + 28), gl, font=_font(28), fill=(12, 8, 22))
        d.text((x0 + 136, ry + 22), token, font=_font(34), fill=ink)
        bw = d.textlength(balance, font=_font(28, False))
        d.text((x1 - 64 - bw, ry + 30), balance, font=_font(28, False), fill=mut)
    # CTA button + tap ripple near the end
    if t > 0.58:
        by0, by1 = y1 - 130, y1 - 46
        d.rounded_rectangle([x0 + 44, by0, x1 - 44, by1], radius=20, fill=accent)
        fc = _font(38)
        cw = d.textlength(cta, font=fc)
        d.text(((x0 + x1) / 2 - cw / 2, by0 + 20), cta, font=fc, fill=(12, 8, 22))
        if t > 0.78:
            rp = (t - 0.78) / 0.2
            r = int(20 + rp * 120)
            al = int(150 * (1 - rp))
            cxr, cyr = int((x0 + x1) / 2), int((by0 + by1) / 2)
            d.ellipse([cxr - r, cyr - r, cxr + r, cyr + r], outline=(255, 255, 255, al), width=4)


STYLES = {"card": _draw_card, "stat": _draw_stat}


def render_video(brief: dict, out: Path, style: str = "card",
                 bg: str | None = None, accent: str | None = None,
                 seconds: float = DURATION) -> Path:
    bg_col, ac = _palette(accent)
    ink, mut = (245, 242, 250), (150, 143, 165)
    style = style if style in ("card", "stat", "kinetic", "mockup") else "card"
    bg_mode = bg or ("gradient" if style == "stat" else "light" if style == "kinetic" else "dark")
    base = _base(bg_mode, bg_col, ac)
    logo = _load_logo()
    dark_kinetic = bg_mode in ("dark", "blue")

    n = max(2, int(FPS * seconds))
    tmp = Path(tempfile.mkdtemp(prefix="vid_"))
    for i in range(n):
        t = i / (n - 1)
        img = base.copy()
        d = ImageDraw.Draw(img, "RGBA")
        if style == "kinetic":
            _draw_kinetic(d, img, t, brief, ac, ink, mut, logo, dark_kinetic)
        elif style == "stat":
            _draw_stat(d, img, t, brief, ac, ink, mut, logo)
        elif style == "mockup":
            _draw_mockup(d, img, t, brief, ac, ink, mut, logo)
        else:
            _draw_card(d, img, t, brief, ac, ink, mut, logo)
        img.save(tmp / f"f{i:04d}.png")

    if os.environ.get("RUNWAY_API_KEY"):
        print("RUNWAY_API_KEY present — (Runway b-roll compositing hook; skipped in this build)")

    out = Path(out); out.parent.mkdir(parents=True, exist_ok=True)
    cmd = [_ffmpeg(), "-y", "-framerate", str(FPS), "-i", str(tmp / "f%04d.png"),
           "-c:v", "libx264", "-pix_fmt", "yuv420p", "-movflags", "+faststart",
           "-vf", "scale=1080:1080", str(out)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    shutil.rmtree(tmp, ignore_errors=True)
    if r.returncode != 0 or not out.exists():
        raise RuntimeError(f"ffmpeg failed: {r.stderr[-400:]}")
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--brief", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--style", default="card", choices=["card", "stat", "kinetic", "mockup"])
    ap.add_argument("--bg", default=None, choices=[None, "dark", "light", "blue", "gradient"])
    ap.add_argument("--accent", default=None)
    args = ap.parse_args()
    brief = json.loads(Path(args.brief).read_text(encoding="utf-8"))
    out = render_video(brief, Path(args.out), style=args.style, bg=args.bg, accent=args.accent)
    print(json.dumps({"ok": True, "out": str(out), "style": args.style, "bytes": out.stat().st_size}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
