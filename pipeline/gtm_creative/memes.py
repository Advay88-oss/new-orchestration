"""Memes — a different job from the posts, so a different renderer.

The post archetypes are restrained, tonal, on a fixed dark ground, with no
characters and no rendered text. Applying that to a meme produced abstract
geometry that was on-brand and not funny, because a meme is not a smaller
version of a post. It is a situation someone recognises.

What the format actually is, read off the references the founder approved:

  * **Two panels.** Before/after, storm/calm, stressed/relaxed. The joke lives
    in the gap between them.
  * **A person in a situation**, drawn as clean cartoon line art. Not a
    diagram, not a metaphor made of shapes.
  * **A first-person caption** — "My assets, chilling on…", "When my strategies
    are safe within…". The voice is a user talking about their own life, which
    is why it lands; a protocol describing itself does not.
  * **Short labels inside the scene** on the objects that carry the argument:
    STRATEGIES on the boat, RISK FLOORS on the platform.
  * **Its own palette.** Memes are not brand assets. Locking them to the post
    ground would make them read as advertising, which is the one thing a meme
    cannot do.

Division of labour, same principle as everywhere else: the model draws the
scene and its short in-scene labels, and the caption — the long sentence a
reader actually reads — is composited, because that is the string that must be
correct.
"""
from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Any, Optional

from PIL import Image, ImageDraw

from pipeline.gtm_creative.archetypes import OUT_DIR, _wrap, font

# Palettes taken from the approved references. A meme picks one; consecutive
# memes do not repeat, which is what keeps a feed of them from flattening.
PALETTES = [
    {"name": "navy_orange", "bg": (16, 32, 56), "ink": (255, 255, 255),
     "desc": "deep navy background, warm orange subject, white line art"},
    {"name": "paper_blue", "bg": (247, 249, 252), "ink": (22, 38, 66),
     "desc": "off-white background, navy line art, pale blue and yellow fills"},
    {"name": "slate_yellow", "bg": (122, 142, 160), "ink": (18, 22, 28),
     "desc": "muted slate background, black line art, mustard yellow accents"},
    {"name": "sea_calm", "bg": (238, 243, 247), "ink": (20, 32, 48),
     "desc": "light background, navy line art, sea blues and sand tones"},
]

STYLE = (
    "Clean two-panel cartoon illustration in a simple modern vector style: "
    "confident even line weight, flat fills, minimal shading, expressive but "
    "simply drawn human figures with plain faces. The kind of drawing that "
    "reads instantly at thumbnail size. "
    "TWO PANELS side by side, equal width, separated by a clear gap, each with "
    "a thin border. The left panel is the problem, the right panel is the "
    "relief; the contrast between them IS the joke. "
    "Leave the bottom 18 percent of the canvas as a plain empty band of solid "
    "colour for a caption that is added afterwards — draw nothing there. "
    "TEXT: the ONLY words anywhere in the image are the labels listed below, "
    "spelled exactly as given. Invent no other text — no words on screens, "
    "monitors, signs, papers, phones, banners, clothing or panel headers, no "
    "alert messages, no titles, no numbers. Every surface that would normally "
    "carry writing is blank. "
    "NEVER: photorealism, 3D renders, anime, manga, hyper-detailed rendering, "
    "gradients or glow, cryptocurrency coins or currency glyphs, price charts "
    "of any kind, candlesticks, line graphs, trend arrows up or down, "
    "lambos, rockets, moons, bulls or bears, any logo or brand mark, any "
    "sentence or caption inside the panels."
)


def _recent_file() -> Path:
    return OUT_DIR / "recent_meme_palettes.json"


def _recent() -> list[str]:
    try:
        return json.loads(_recent_file().read_text(encoding="utf-8"))
    except Exception:                               # noqa: BLE001 — boundary
        return []


def _remember(name: str) -> None:
    hist = [name] + [n for n in _recent() if n != name]
    _recent_file().write_text(json.dumps(hist[:3]), encoding="utf-8")


def pick_palette() -> dict:
    blocked = set(_recent()[:2])
    pool = [p for p in PALETTES if p["name"] not in blocked] or PALETTES
    return random.choice(pool)


def build_prompt(panel_left: str, panel_right: str,
                 labels: list[str], palette: dict) -> str:
    label_line = ""
    if labels:
        label_line = ("Inside the scene, label objects with exactly these "
                      "words and nothing else: "
                      + ", ".join('"' + l.upper() + '"' for l in labels[:3]) + ". ")
    return (
        "On the left, " + panel_left.strip().rstrip(".").lstrip("A ").lstrip("a ") + ". "
        "On the right, " + panel_right.strip().rstrip(".").lstrip("A ").lstrip("a ") + ". "
        + label_line
        + "Colour: " + palette["desc"] + ". Both panels share the same palette. "
        + STYLE
    )


def render_meme(panel_left: str, panel_right: str, caption: str,
                labels: Optional[list[str]] = None, *,
                out: Optional[Path] = None,
                model: str = "gemini-3-pro-image",
                size: tuple[int, int] = (1400, 760),
                palette: Optional[dict] = None) -> Path:
    """Draw the scene with the model; composite the caption ourselves."""
    from pipeline.scripts.gemini_flash_image import generate_gemini_image

    out = Path(out or (OUT_DIR / "demo_meme.png"))
    raw = out.with_name(out.stem + "_raw.png")
    pal = palette or pick_palette()

    generate_gemini_image(
        prompt=build_prompt(panel_left, panel_right, labels or [], pal),
        output_path=raw, project="vanna-mcp", location="global",
        model=model, temperature=0.85)

    base = Image.open(raw).convert("RGB").resize(size, Image.Resampling.LANCZOS)
    W, H = size

    # The caption band is painted over whatever the model left in the reserved
    # strip. Asking it to leave the space is a request; painting the band is a
    # guarantee, and the caption is the one string that has to be right.
    band_h = int(H * 0.19)
    d = ImageDraw.Draw(base)
    d.rectangle([(0, H - band_h), (W, H)], fill=pal["bg"])
    d.line([(0, H - band_h), (W, H - band_h)], fill=pal["ink"], width=2)

    size_px = 40
    while size_px > 22:
        f = font("bold", size_px)
        lines = _wrap(d, caption, f, int(W * 0.92))
        if len(lines) <= 2:
            break
        size_px -= 2
    f = font("bold", size_px)
    lines = _wrap(d, caption, f, int(W * 0.92))[:2]

    # Balance the break rather than filling line one. Greedy wrapping left
    # "hit." alone on the second line, which reads as a mistake at the size a
    # caption is set.
    if len(lines) == 2:
        words = caption.split()
        best, best_gap = lines, 10 ** 9
        for cut in range(1, len(words)):
            a, b = " ".join(words[:cut]), " ".join(words[cut:])
            if max(d.textlength(a, font=f), d.textlength(b, font=f)) > W * 0.92:
                continue
            gap = abs(d.textlength(a, font=f) - d.textlength(b, font=f))
            if gap < best_gap:
                best, best_gap = [a, b], gap
        lines = best

    lh = int(size_px * 1.24)
    y = H - band_h + (band_h - lh * len(lines)) // 2
    for line in lines:
        w = d.textlength(line, font=f)
        d.text(((W - w) / 2, y), line, font=f, fill=pal["ink"])
        y += lh

    base.save(out, quality=96)
    _remember(pal["name"])
    return out


# --------------------------------------------------------------------------
# Briefing
# --------------------------------------------------------------------------

MEME_SYSTEM = (
    "You write memes for Vanna, composable credit infrastructure on Stellar "
    "Soroban testnet. A meme is a situation a user recognises, not a product "
    "description.\n\n"
    "Rules that make the difference between a meme and an advert:\n"
    "- The caption is FIRST PERSON, from the user's side: \"My assets, "
    "chilling on…\", \"When my strategies are safe within…\", \"Using Vanna's "
    "margin accounts to…\". Never \"Vanna provides\" or \"Vanna enables\".\n"
    "- The left panel is a felt problem — stress, storm, a mess of "
    "spreadsheets, a sinking boat. The right panel is relief: the same person, "
    "calm, because of the mechanism. The gap between them is the joke.\n"
    "- Describe a SCENE with a person in it, not a diagram and not a metaphor "
    "made of shapes.\n"
    "- Labels are 1-2 words, on objects, and they carry the argument.\n"
    "- Never imply mainnet, never name a competitor, never invent a figure.\n\n"
    "Return strict JSON."
)


def brief_meme(strategy: Any, hook: str, body: str,
               run_id: Optional[str] = None) -> dict[str, Any]:
    """Ask A07 for the two panels, the labels and the caption."""
    from pipeline.gtm_os import agent_runtime as R

    prompt = (
        "THIS POST\n"
        "  pillar:  " + str(getattr(strategy, "narrative_pillar", "")) + "\n"
        "  problem: " + str(getattr(strategy, "problem", ""))[:300] + "\n"
        "  hook:    " + str(hook)[:200] + "\n"
        "  body:    " + str(body)[:800] + "\n\n"
        "Write the meme. Return JSON:\n"
        '{"panel_left": str, "panel_right": str, "labels": [str], '
        '"caption": str}\n\n'
        "panel_left and panel_right are one sentence each describing what is "
        "drawn — a person, doing something, somewhere. labels is 1-3 short "
        "strings. caption is under 14 words, first person."
    )
    return R.brain_json(prompt, agent="A07_creative_director", role="reasoning",
                        system=MEME_SYSTEM, temperature=0.9,
                        max_output_tokens=2048, run_id=run_id)
