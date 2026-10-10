"""A profile cover (LinkedIn or X banner), made by the agents.

  Motion/Art Director (A14, "director")
    reads the brand brain (facts, the founder's vocabulary rule) and looks at
    the current cover and the founder's newest post format; lists what is wrong
    with the current cover and writes the new one: every word, the layout, the
    elements. The platform's crop and avatar zone are given as data.
  Visual agent (A08, MODELS["poster"] — Nano Banana 2.1)
    draws it in the founder's format, ultra-wide, with an empty slot where the
    real logo is pasted afterwards.
  Judge (A15)
    transcribes the cover; code compares the transcription with the director's
    strings. A cover with a wrong word is redrawn, never shipped.

    python -m pipeline.gtm_creative.cover linkedin --current path/to/old_cover.png
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Optional

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "exports" / "agent-posts" / "cover"

# Platform facts: the size the platform serves and what covers part of it.
PLATFORMS = {
    "linkedin": {"size": (1584, 396), "label": "LinkedIn profile background",
                 "covered": "the round profile photo covers the lower-left: roughly the left 25% of the width and "
                            "the bottom 55% of the height"},
    "linkedin-company": {"size": (1128, 191), "label": "LinkedIn company page cover",
                         "covered": "the square company logo covers the lower-left: roughly the left 20% of the width "
                                    "and the bottom 50% of the height"},
    "x": {"size": (1500, 500), "label": "X header",
          "covered": "the round avatar covers the lower-left: roughly the left 25% of the width and the bottom 45% "
                     "of the height; the very top and bottom 10% crop on some screens"},
}
# Where the content block starts, as a share of the cover: right of the covered zone.
BLOCK_X, LOGO_Y, LOGO_H = 0.36, 0.20, 0.15


def direct(platform: str, current: Optional[Path], refs: list[Path], *, run_id: Optional[str] = None) -> dict:
    from pipeline.brand_brain import context as C
    from pipeline.gtm_os import agent_runtime as R
    spec = PLATFORMS[platform]
    system = C.fill("You are {company}'s Motion/Art Director. You brief the company's profile cover. Strict JSON only.")
    prompt = (
        C.facts_block("what " + C.company_name() + " is: identity, one-liner, positioning, current campaign",
                      k=8, excerpts=4) + "\n\n----\n\n"
        + "THE COVER: " + spec["label"] + ", " + "x".join(map(str, spec["size"])) + " px. " + spec["covered"]
        + " — nothing may sit there. The content block starts at " + str(int(BLOCK_X * 100)) + "% of the width: "
        "the real logo is pasted at its top-left (leave that slot empty), the words go under it.\n"
        + ("Image 1 is the CURRENT cover. List what is wrong with it (wording, positioning against the facts above, "
           "type, layout, crop, the platform's covered zone) — concretely.\n" if current else "")
        + "The other images are the founder's newest post format: use its design system (ground, glow, type, the "
          "gradient emphasis), not its layout.\n"
        "A cover is read in one second and lives for months: the company's identity, not a campaign. One headline "
        "(the founder's one-liner or a shorter rung of it, from the facts), at most one short sub-line, the website. "
        "Use the founder's vocabulary above; never a phrase the facts rule out. No numbers, no claims about traction.\n"
        'Return JSON: {"critique": [str], "headline": [str] (1-2 lines), "emphasis": str (the words in the gradient), '
        '"sub": str, "url": str, "composition": str (what sits where, right of the covered zone), '
        '"elements": [str] (every visual element besides the words)}')
    images = ([current] if current else []) + refs
    out = R.brain_vision(prompt, images, agent="A14_motion_director", role="director", system=system,
                         temperature=0.4, max_output_tokens=6144, run_id=run_id)
    R.record_decision("A14_motion_director", "cover_brief", {"brief": out, "platform": platform}, run_id=run_id)
    return out


def _strings(d: dict) -> list[str]:
    return [str(x) for x in (d.get("headline") or [])] + [str(d.get("sub") or ""), str(d.get("url") or "")]


def _prompt(d: dict, platform: str, fix: str) -> str:
    from pipeline.brand_brain import context as C
    pal, spec = C.palette(), PLATFORMS[platform]
    return (
        "Make an ultra-wide brand cover for " + C.company_name() + " (" + spec["label"] + "). The images are the "
        "founder's own posts: match their design system exactly — ground, glow, type, the gradient emphasis.\n"
        "LAYOUT: the whole design sits in the middle horizontal band; the top 20% and bottom 20% are plain ground "
        "(they are cropped). The left " + str(int(BLOCK_X * 100)) + "% of the width is quiet ground with only soft "
        "glow (the platform covers part of it). The content block starts at " + str(int(BLOCK_X * 100)) + "% of the "
        "width: at its top an EMPTY slot for the logo (draw no logo, no mark, no wordmark anywhere), then the "
        "headline, then the sub-line, then the website.\n"
        "COMPOSITION: " + str(d.get("composition") or "") + "\nELEMENTS: " + "; ".join(map(str, d.get("elements") or [])) + "\n"
        "TEXT — exactly these strings and nothing else readable: " + " | ".join(s for s in _strings(d) if s.strip())
        + ". The words '" + str(d.get("emphasis") or "") + "' in the " + str(pal.get("gradient_word", "")) + " gradient.\n"
        + "BRAND: ground " + pal.get("ground", "") + ", accent " + pal.get("accent", "") + ", font like "
        + C.fonts().get("display", "") + "."
        + ("\nFIX THESE PROBLEMS FROM THE LAST TRY:\n" + fix if fix else ""))


def _text_box(im: Image.Image) -> tuple[int, int, int, int]:
    """Where the words are, right of the covered zone: the letter mask's
    bounding box (glows are smooth and stay out of the mask)."""
    import numpy as np
    from pipeline.gtm_creative.veo_video import letter_mask
    m = np.asarray(letter_mask(im)) > 120
    m[:, : int(im.width * (BLOCK_X - 0.04))] = False
    rows, cols = np.where(m.any(axis=1))[0], np.where(m.any(axis=0))[0]
    if not len(rows):
        return (int(im.width * BLOCK_X), int(im.height * 0.35), int(im.width * 0.95), int(im.height * 0.65))
    return (int(cols[0]), int(rows[0]), int(cols[-1]), int(rows[-1]))


def compose(raw: Path, platform: str, out: Path) -> Path:
    """The real logo just above the words, then the platform's band cropped
    around logo and words together. (A fixed crop cut the website off when the
    model set the words lower; a fixed logo position landed on the headline.)"""
    from pipeline.gtm_creative.cinema_film import _logo
    W, H = PLATFORMS[platform]["size"]
    im = Image.open(raw).convert("RGB")
    x0, y0, x1, y1 = _text_box(im)
    band = int(im.width * H / W)
    src = _logo()
    top = y0
    if src:
        logo = Image.open(src).convert("RGBA")
        box = logo.getchannel("A").point(lambda a: 255 if a > 8 else 0).getbbox()
        logo = logo.crop(box) if box else logo
        lh = max(1, int(band * LOGO_H))
        logo = logo.resize((max(1, int(logo.width * lh / logo.height)), lh), Image.Resampling.LANCZOS)
        ly = max(0, y0 - int(lh * 1.7))
        im.paste(logo, (x0, ly), logo)
        top = ly
    need = int((y1 - top) * 1.22)                   # logo + words + a margin above and below
    if need > band:
        # Taller than the platform's band: crop taller, and widen the frame on
        # the left with the image's own plain ground (more room for the avatar).
        cw = int(need * W / H)
        edge = im.crop((0, 0, max(4, im.width // 100), im.height)).resize((cw - im.width, im.height),
                                                                          Image.Resampling.BICUBIC)
        wide = Image.new("RGB", (cw, im.height))
        wide.paste(edge, (0, 0))
        wide.paste(im, (cw - im.width, 0))
        im, band = wide, need
    mid = (top + y1) // 2
    t = min(max(0, mid - band // 2), im.height - band)
    im.crop((0, t, im.width, t + band)).resize((W * 2, H * 2), Image.Resampling.LANCZOS).save(out)
    return out


def judge(path: Path, d: dict) -> dict:
    """The judge reads; code compares."""
    from pipeline.brand_brain import context as C
    from pipeline.gtm_creative.cinema_film import _norm
    from pipeline.gtm_os import agent_runtime as R
    v = R.brain_vision(
        "A brand cover. FIRST transcribe every readable string exactly as drawn, letter by letter, including the "
        "logo's wordmark; do not correct spelling. THEN judge the look: one logo (placed on purpose), the words "
        "clear of the lower-left corner, premium and calm. "
        'Return JSON: {"seen": [str], "look_ok": bool, "look_fixes": [str], "score": int (0-10)}',
        [path], agent="A15_creative_judge", role="reasoning", temperature=0.0, max_output_tokens=3072)
    seen = [_norm(x) for x in (v.get("seen") or []) if _norm(x)]
    blob = " | ".join(seen) + " | " + " ".join(seen)
    need = [s for s in _strings(d) if _norm(s)]
    missing = [s for s in need if _norm(s) not in blob]
    allowed = [_norm(s) for s in need] + [_norm(C.company_name())]
    extra = [x for x in seen if not any(x in a or a in x for a in allowed)]
    fixes = (['write exactly "' + s + '"' for s in missing] + ['remove "' + x + '"' for x in extra]
             + ([str(x) for x in v.get("look_fixes") or []] if not v.get("look_ok", True) else []))
    return {"verdict": "SHIP" if not missing and not extra and v.get("look_ok", True) else "REVISE",
            "score": int(v.get("score") or 0), "seen": v.get("seen"), "fixes": fixes}


def run(platform: str = "linkedin", *, current: Optional[Path] = None, name: str = "cover",
        attempts: int = 3) -> dict[str, Any]:
    from pipeline.gtm_creative.format_poster import bases
    from pipeline.gtm_os import agent_runtime as R
    from pipeline.scripts.gemini_flash_image import generate_gemini_image
    OUT.mkdir(parents=True, exist_ok=True)
    refs = [b["path"] for b in bases()][:3]
    d = direct(platform, current, refs)
    (OUT / f"{name}.brief.json").write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    tries, fix = [], ""
    for k in range(1, attempts + 1):
        raw = OUT / f"{name}_try{k}_raw.png"
        generate_gemini_image(prompt=_prompt(d, platform, fix), output_path=raw, model=R.MODELS["poster"],
                              temperature=0.3, images=refs, aspect_ratio="21:9",
                              image_size=os.environ.get("VANNA_POSTER_SIZE", "4K"))
        made = compose(raw, platform, OUT / f"{name}_try{k}.png")
        v = judge(made, d)
        tries.append({"path": str(made), **v})
        if v["verdict"] == "SHIP":
            break
        fix = "\n".join("- " + f for f in v["fixes"][:8])
    best = max(tries, key=lambda t: (t["verdict"] == "SHIP", t["score"]))
    final = OUT / f"{name}.png"
    final.write_bytes(Path(best["path"]).read_bytes())
    return {"final": str(final), "critique": d.get("critique"), "headline": d.get("headline"),
            "sub": d.get("sub"), "tries": [(t["verdict"], t["score"], t["fixes"][:3]) for t in tries]}


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("platform", choices=sorted(PLATFORMS))
    ap.add_argument("--current")
    ap.add_argument("--name", default="cover")
    a = ap.parse_args()
    print(json.dumps(run(a.platform, current=Path(a.current) if a.current else None, name=a.name),
                     ensure_ascii=False, indent=1))
