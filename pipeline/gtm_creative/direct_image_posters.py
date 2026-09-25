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
REF_DIR = REPO / "design references"
LOGO = REPO / "pipeline" / "state" / "logo.png"
OUT_DIR = REPO / "pipeline" / "state" / "direct_posters"
MODEL = "gemini-3-pro-image"

FACTS = """VANNA — the only facts you may use:
- Vanna is composable credit / unified margin infrastructure, live on Stellar Soroban TESTNET (not mainnet).
- Each user gets a SmartAccount: an isolated margin-account contract. Risk stays inside that account; it is not pooled with other users.
- Users borrow credit against collateral and deploy it across venues (Blend lending, Aquarius and Soroswap AMMs on Stellar).
- Health-factor liquidation floor: 1.10x. Fixed gas: 0.00014 XLM. Indexing latency: ~320ms.
- Never state any other number: no user counts, no TVL, no APY, no percentages, no price."""


def references() -> list[Path]:
    refs = sorted(REF_DIR.glob("cl-*.png"))
    extra = REF_DIR / "image.png"
    return refs + ([extra] if extra.exists() else [])


def _prompt(brief: str, correction: str = "", approved: int = 0) -> str:
    return (
        "You are designing ONE finished square (1:1) image for an X post by "
        "Vanna Finance.\n\n"
        + ("ATTACHED IMAGES: the FIRST " + str(approved) + " are posters the "
           "founder APPROVED — the quality bar, and the way to compose one: an "
           "explanatory diagram built from glass UI elements, icons and "
           "arrows, clearly contrasting the problem with Vanna's answer. Match "
           "that level and that approach; do NOT copy their text or their "
           "exact layout. The images after them, except the last, are further "
           "STYLE REFERENCES. The LAST image is the official Vanna logo.\n\n"
           if approved else
           "ATTACHED IMAGES: all images except the last are STYLE REFERENCES. "
           "The LAST image is the official Vanna logo.\n\n")
        + "FORMAT: one full-bleed square, the dark ground running edge to "
        "edge — no white or light borders, no bands, no frame around it.\n\n"
        + "Match the references' house style exactly: very dark ground with a "
        "soft violet glow low-left and a magenta glow high-right; the logo "
        "centred at the top; a heavy bold sans-serif headline, centred, with "
        "ONE key word or short phrase in a pink-to-violet gradient italic; "
        "one short grey subtitle line; a clean centrepiece made of UI "
        "elements (glass cards, chips, rows with checkmarks, pills, arrows, "
        "stat tiles or a simple diagram) that explains the idea; and a footer "
        "line at the bottom: a few bold white words then a short grey "
        "caveat that says testnet. Generous spacing, nothing overlapping, "
        "everything aligned.\n\n"
        "LOGO: use the logo from the LAST attached image, exactly as it is — "
        "same mark, same lowercase wordmark 'vanna', same colours, drawn "
        "once. Do NOT invent a mark and do NOT use the cube icon in the "
        "style references; that is an old logo.\n\n"
        "No markdown: never render asterisks, underscores or hashes as "
        "characters; emphasis is the gradient word.\n\n"
        "TEXT RULES: every word must be spelled correctly. Keep all text "
        "short — headline under 9 words, subtitle under 14, labels 1-4 "
        "words. Use no text other than what explains the idea. Other "
        "protocols (Blend, Aquarius, Soroswap) appear as plain text names — "
        "never draw a logo or icon for them. Keep to Vanna's violet and "
        "magenta; avoid cyan and teal. " + FACTS
        + "\n\nTHE POST THIS IMAGE IS FOR:\n" + " ".join(brief.split())
        + ("\n\nFIX FROM THE PREVIOUS ATTEMPT (it was rejected): " + correction
           if correction else "")
    )


JUDGE_SYSTEM = (
    "You review a finished social image for Vanna Finance before a human "
    "sees it. Be strict and specific. Return strict JSON."
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
        "The FIRST image is the poster to review. The SECOND is the official "
        "Vanna logo.\n\n" + FACTS + "\n\nThe brief was:\n" + brief + "\n\n"
        "Check: every word spelled correctly and not garbled; no figure that "
        "is not in the facts list; the logo matches the official one (not a "
        "cube); nothing overlaps or is cut off; the image is about the brief; "
        "no logo or brand mark of ANY other protocol (Blend, Aquarius, "
        "Soroswap and others appear as plain text names only — an invented "
        "icon for them is a fake brand mark); no markdown characters "
        "(asterisks, underscores, hashes) rendered as text. "
        "REJECT on any spelling error, invented figure, wrong logo, another "
        "protocol's logo, markdown characters or overlap. Cyan or teal is "
        "NOT a reason to reject — the founder approved a poster with it — "
        "but name it in `fix` if present. `fix` says exactly what to change, "
        "in one or two sentences.\n\nReturn JSON exactly:\n" + JUDGE_SCHEMA
    )
    return R.brain_vision(prompt, [image, LOGO], agent="A07_creative_director",
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

    from pipeline.gtm_creative.brand import logo

    img = Image.open(path).convert("RGB")
    W, H = img.size
    x0, x1 = int(W * 0.22), int(W * 0.78)
    y0, y1 = int(H * 0.015), int(H * 0.135)
    px = img.load()

    def inked(x: int, y: int) -> bool:
        r, g, b = px[x, y]
        return max(r, g, b) > 150 or (max(r, g, b) - min(r, g, b) > 90 and max(r, g, b) > 90)

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
    img.paste(mark, (cx - mark.width // 2, cy - mark.height // 2), mark)
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
    try:
        from pipeline.gtm_learning.visual_exemplars import top
        approved = top(3, renderer="direct_model")
    except Exception:                               # noqa: BLE001 — boundary
        approved = []
    imgs = (approved + references()
            + [Path(p) for p in (extra_refs or []) if Path(p).exists()] + [LOGO])
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
