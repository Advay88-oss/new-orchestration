"""Posters made by the image model directly, from the references it can see.

The code-set posters (`reference_posters.py`) reproduce the founder's house
style by describing it in Python: every bloom, card and gradient is code, so
a new style means new code. This is the other approach: the image model is
shown the reference PNGs and the real logo, told what the post is about, and
returns the finished poster itself.

What the model cannot be trusted with — spelling, invented figures, the logo
— is checked afterwards by a vision judge that looks at the output. A REJECT
is fed back as a correction and the poster is made once more.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

REPO = Path(__file__).resolve().parents[2]
OUT_DIR = REPO / "pipeline" / "state" / "direct_posters"
MODEL = "gemini-3-pro-image"

# Everything company-specific here (the facts, the logo, the references, the
# approved posters, the house style) comes from the tenant's brand brain.


def _c():
    from pipeline.brand_brain import context as C
    return C


def _logo() -> Optional[Path]:
    p = _c().logo_path()
    return p if p and Path(p).exists() else None


def _palette() -> dict:
    return {k: v for k, v in (_c().palette() or {}).items() if isinstance(v, str)}


def _ground() -> str:
    p = _palette()
    return p.get("ground") or p.get("background") or p.get("bg") or ""


def _palette_line() -> str:
    """The brand's colours as hex, for the model to use — not "the brand
    palette" in the abstract, which let every tenant come out in Vanna's."""
    p = {k: v for k, v in _palette().items() if v.startswith("#")}
    return ", ".join(k.replace("_", " ") + " " + v for k, v in p.items())


def _emphasis() -> str:
    g = _palette().get("gradient_word")
    if g:
        return "emphasis is one word in the " + g + " gradient"
    acc = _palette().get("accent")
    return "emphasis is one word in the accent colour" + (" " + acc if acc else "")


def _facts() -> str:
    """The only facts an image may carry: the profile's anchors and figures."""
    C = _c()
    lines = [C.company_name().upper() + " — the only facts you may use:", "- " + C.company_line()]
    lines += ["- " + k + ": " + v for k, v in C.anchors().items()]
    lines += ["- " + f["value"] + ": " + f.get("meaning", "") for f in C.true_figures()]
    ns = C.never_state()
    if ns:
        lines.append("- Never state any other number: no " + ", no ".join(ns) + ".")
    return "\n".join(lines)


def _venues() -> str:
    """Partner names that may appear as plain text (never as a drawn logo)."""
    # Venues and protocols, not the chain, backers or infrastructure vendors.
    skip = ("chain", "backer", "infrastructure")
    names = [n for n, role in _c().partners().items()
             if not any(s in role.lower() for s in skip)][:6]
    return ", ".join(names) if names else "partner protocols"


def _refs(topic: str, kinds: list[str], n: int, min_score: float = 0.0) -> list[Path]:
    """The brain's images for a topic: `get_visual_refs`, the architecture's
    call for the visual agent."""
    try:
        rows = _c().brain().get_visual_refs(topic or "brand poster", n=n * 3 if min_score else n,
                                            kinds=kinds)
    except Exception:                               # noqa: BLE001 — boundary
        return []
    out = []
    for r in rows:
        if min_score and float(r.get("score") or 0) < min_score:
            continue
        f = REPO / r["path"]
        if f.exists():
            out.append(f)
    return out[:n]


def references(topic: str = "") -> list[Path]:
    """The tenant's design references, closest to the topic first; a company
    with none yet is shown its own website instead (the analyzer's
    screenshots), so the style is its own and not a default."""
    return _refs(topic, ["reference"], 8) or _refs(topic, ["website"], 4)


def _learned_rules() -> str:
    """Rules the Coach learned from past runs, for the image model and judge."""
    try:
        from pipeline.gtm_creative.creative_rules import learned_rules
        rules = learned_rules()
    except Exception:                               # noqa: BLE001 — boundary
        rules = []
    return ("\n\nLEARNED FROM PAST RUNS — follow these too:\n"
            + "\n".join("- " + r for r in rules[-12:])) if rules else ""


# The founder's rulebook forbids these, and the creative judge rejects on
# them, but neither the image prompt nor this file's own judge said so. Run
# GTM-20260925-104259 drew an isometric safe with a dial and a 3D cardboard
# box, passed its own judge as SHIP, and was rejected at the end of a
# 14-minute run, after its video had been built from it.
FLAT_RULE = (
    "FLAT, FACE-ON ONLY: every element is drawn flat and straight-on (2D "
    "glass cards, flat boundaries and enclosures, straight arrows). Never "
    "isometric, 3D, angled or perspective objects; never safes, vaults, "
    "combination dials, boxes or crates, coins, tokens or piles of wealth.")


def _prompt(brief: str, correction: str = "", approved: int = 0) -> str:
    has_logo = _logo() is not None
    last = " The LAST image is the official logo." if has_logo else ""
    ground = _ground()
    return (
        "You are designing ONE finished square (1:1) image for an X post by "
        + _c().company_name() + ".\n\n"
        + ("ATTACHED IMAGES: the FIRST " + str(approved) + " are posters the "
           "founder APPROVED — the quality bar, and the way to compose one: an "
           "explanatory diagram built from glass UI elements, icons and "
           "arrows, clearly contrasting the problem with " + _c().company_name() + "'s answer. Match "
           "that level and that approach; do NOT copy their text or their "
           "exact layout. The images after them" + (", except the last," if has_logo else "")
           + " are further STYLE REFERENCES." + last + "\n\n"
           if approved else
           "ATTACHED IMAGES: " + ("all images except the last" if has_logo else "the images")
           + " are STYLE REFERENCES from the brand's own website and designs." + last + "\n\n")
        + "FORMAT: one full-bleed square, the brand's ground colour" + (" " + ground if ground else "")
        + " running edge to edge — no borders, bands or frame around it.\n\n"
        + ("BRAND COLOURS (use these, not others): " + _palette_line() + ".\n\n" if _palette_line() else "")
        + "Match the references' house style exactly: " + _c().house_style()
        + ". Generous spacing, nothing overlapping, everything aligned.\n\n"
        + FLAT_RULE + "\n\n"
        + ("LOGO: use the logo from the LAST attached image, exactly as it is: "
           + _c().logo_description() + ". Same mark, same wordmark, drawn once, in a tone that "
           "reads on the ground (dark on a light ground, light on a dark one). Do NOT invent a "
           "mark and do NOT copy any logo or icon from the style references.\n\n"
           if has_logo else
           "LOGO: no logo file is available; set the name " + _c().company_name() + " once, small, "
           "as a plain wordmark in the text colour. Do NOT invent a mark.\n\n")
        + "No markdown: never render asterisks, underscores or hashes as "
        "characters; " + _emphasis() + ".\n\n"
        "TEXT RULES: every word must be spelled correctly. Keep all text "
        "short — headline under 9 words, subtitle under 14, labels 1-4 "
        "words. Use no text other than what explains the idea. Other "
        "protocols (" + _venues() + ") appear as plain text names — "
        "never draw a logo or icon for them. Keep to the brand palette"
        + ("; avoid " + " and ".join(_c().avoid_colors()) if _c().avoid_colors() else "")
        + ". " + _facts()
        + _learned_rules()
        + "\n\nTHE POST THIS IMAGE IS FOR:\n" + " ".join(brief.split())
        + ("\n\nFIX FROM THE PREVIOUS ATTEMPT (it was rejected): " + correction
           if correction else "")
    )


JUDGE_SYSTEM = (
    "You review a finished social image for a brand before a human sees it. "
    "Be strict and specific. Return strict JSON."
)

JUDGE_SCHEMA = (
    '{"spelling_errors": [str], "invented_figures": [str], '
    '"logo_correct": bool, "overlapping_or_clipped": [str], '
    '"matches_brief": bool, "matches_reference_style": bool, '
    '"verdict": "SHIP"|"REVISE"|"REJECT", "fix": str}'
)


def judge(image: Path, brief: str) -> dict[str, Any]:
    from pipeline.gtm_os import agent_runtime as R

    prompt = (
        ("The FIRST image is the poster to review. The SECOND is the official "
         + _c().company_name() + " logo.\n\n" if _logo() else
         "The image is the poster to review (no logo file exists; the name should appear once as a "
         "plain wordmark).\n\n") + _facts() + "\n\nThe brief was:\n" + brief + "\n\n"
        "Check: every word spelled correctly and not garbled; no figure that "
        "is not in the facts list; the logo matches the official one (not a "
        "cube); nothing overlaps or is cut off; the image is about the brief; "
        "no logo or brand mark of ANY other protocol (" + _venues() + " and "
        "others appear as plain text names only — an invented "
        "icon for them is a fake brand mark); no markdown characters "
        "(asterisks, underscores, hashes) rendered as text; " + FLAT_RULE + " "
        "REJECT on any spelling error, invented figure, wrong logo, another "
        "protocol's logo, markdown characters, overlap, or any isometric/3D "
        "object, safe, vault, box or coin. A colour outside the palette is "
        "NOT a reason to reject on its own, but name it in `fix` if present. `fix` says exactly what to change, "
        "in one or two sentences." + _learned_rules()
        + "\n\nReturn JSON exactly:\n" + JUDGE_SCHEMA
    )
    return R.brain_vision(prompt, [image] + ([_logo()] if _logo() else []), agent="A15_creative_judge",
                          system=JUDGE_SYSTEM, role="reasoning",
                          temperature=0.1, max_output_tokens=2048)


def fix_logo(path: Path) -> bool:
    """Replace whatever lockup the model drew with the official one.

    The model places the lockup consistently — centred, in the top eighth —
    and writes the wordmark correctly, but draws the MARK from memory: a "V",
    a folded shape, rarely the real ribbon. So the drawn lockup is located
    (the first band of bright or saturated pixels from the top, inside the
    centre of the frame), covered with the ground sampled around it, and the
    real lockup is pasted at the same height and centre. Returns False, and
    leaves the file untouched, when no lockup is found where it should be.
    """
    from PIL import Image, ImageDraw, ImageFilter

    from pipeline.gtm_creative.brand import contrast_safe, logo

    img = Image.open(path).convert("RGB")
    W, H = img.size
    x0, x1 = int(W * 0.22), int(W * 0.78)
    y0, y1 = int(H * 0.015), int(H * 0.135)
    px = img.load()
    # Ink is whatever differs from the ground, dark or light: sampled at the
    # top corners (a white Morpho poster made every pixel "bright").
    corners = [px[int(W * 0.04), int(H * 0.04)], px[int(W * 0.96), int(H * 0.04)]]
    ground = tuple(sum(c[i] for c in corners) // 2 for i in range(3))

    light = sum(ground) / 3 > 140

    def inked(x: int, y: int) -> bool:
        r, g, b = px[x, y]
        if not light:       # dark grounds (Vanna): bright or saturated, as before
            return max(r, g, b) > 150 or (max(r, g, b) - min(r, g, b) > 90 and max(r, g, b) > 90)
        return abs(r - ground[0]) + abs(g - ground[1]) + abs(b - ground[2]) > 150

    # A row inked across most of the width is a band or rule the model drew
    # along the edge, not a lockup; one poster opened with a violet strip and
    # the strip was patched instead of the logo.
    cols_sampled = len(range(x0, x1, 2))
    rows = [y for y in range(y0, y1)
            if 3 <= sum(inked(x, y) for x in range(x0, x1, 2)) < cols_sampled * 0.6]
    if not rows:
        return False
    # The first contiguous run of inked rows is the lockup; anything below a
    # gap is the headline starting.
    top_y, bot_y = rows[0], rows[0]
    for y in rows[1:]:
        if y - bot_y > 6:
            break
        bot_y = y
    cols = [x for x in range(x0, x1) if any(inked(x, y) for y in range(top_y, bot_y + 1, 2))]
    if not cols or bot_y - top_y < 12:
        return False
    lx0, lx1 = cols[0], cols[-1]
    pad = 14
    box = (max(0, lx0 - pad), max(0, top_y - pad), min(W, lx1 + pad), min(H, bot_y + pad))

    # Fill: per row, blend from the ground just left of the box to the ground
    # just right of it. A single flat colour left a visible rectangle on the
    # ground's gradient beside the logo.
    fill = img.copy()
    fpx = fill.load()
    lx, rx = max(0, box[0] - 6), min(W - 1, box[2] + 6)
    span = max(1, rx - lx)
    for y in range(max(0, box[1] - 12), min(H, box[3] + 12)):
        a, b = px[lx, y], px[rx, y]
        for x in range(lx, rx + 1):
            t = (x - lx) / span
            fpx[x, y] = tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))
    fill = fill.filter(ImageFilter.GaussianBlur(3))

    patch = Image.new("L", (W, H), 0)
    ImageDraw.Draw(patch).rounded_rectangle(box, radius=12, fill=255)
    patch = patch.filter(ImageFilter.GaussianBlur(8))
    img = Image.composite(fill, img, patch)

    mark = logo(max(16, int((bot_y - top_y) * 1.0)))
    if mark is None:
        return False
    cx = (lx0 + lx1) // 2
    cy = (top_y + bot_y) // 2
    at = (cx - mark.width // 2, cy - mark.height // 2)
    mark = contrast_safe(mark, img.crop((at[0], at[1], at[0] + mark.width, at[1] + mark.height)))
    img.paste(mark, at, mark)
    img.save(path)
    return True


def make(brief: str, name: str, *, out_dir: Optional[Path] = None,
         attempts: int = 3, extra_refs: Optional[list] = None) -> dict[str, Any]:
    from pipeline.scripts.gemini_flash_image import generate_gemini_image

    out_dir = Path(out_dir or OUT_DIR)
    out_dir.mkdir(parents=True, exist_ok=True)
    # Founder-approved posters first — what the founder liked is what the
    # model is shown before anything else — then the design references.
    # The logo goes last; the prompt names it. Compositing it instead was
    # tried on 2026-09-25 and was worse: told to leave the top empty, the
    # model still wrote "Vanna" there (so the pasted lockup doubled it) or
    # returned a letterboxed frame. Shown the logo, it reproduced it in most
    # attempts, and the judge rejects the ones where it did not.
    # Both come from the brain's visual memory, ranked for this brief: the
    # founder-approved posters closest to the topic (rated 0.7 or better),
    # then the design references.
    approved = _refs(brief, ["approved_poster"], 3, min_score=0.7)
    imgs = (approved + references(brief)
            + [Path(p) for p in (extra_refs or []) if Path(p).exists()] + ([_logo()] if _logo() else []))
    history = []
    correction = ""
    for n in range(1, attempts + 1):
        path = out_dir / f"{name}_try{n}.png"
        generate_gemini_image(prompt=_prompt(brief, correction, len(approved)),
                              output_path=path,
                              model=MODEL, temperature=0.7, images=imgs,
                              aspect_ratio="1:1")
        # The real lockup replaces the drawn one before the judge looks, so a
        # wrong mark costs nothing instead of a whole attempt.
        fix_logo(path)
        try:
            v = judge(path, brief)
        except Exception as exc:                    # noqa: BLE001 — boundary
            v = {"verdict": "UNJUDGED", "fix": str(exc)[:200]}
        history.append({"path": str(path), **v})
        if str(v.get("verdict")).upper() == "SHIP":
            break
        correction = str(v.get("fix") or "")
    # Best attempt: SHIP, then REVISE, then the last REJECT — never an earlier
    # REJECT over a later REVISE.
    order = {"SHIP": 0, "REVISE": 1}
    best = min(reversed(history), key=lambda h: order.get(str(h.get("verdict")).upper(), 2))
    final = out_dir / f"{name}.png"
    final.write_bytes(Path(best["path"]).read_bytes())
    return {"name": name, "final": str(final), "attempts": history}
