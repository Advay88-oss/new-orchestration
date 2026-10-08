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
    lines += ["- " + f["value"] + ": " + f.get("meaning", "") + " (Stellar testnet only)" for f in C.true_figures()]
    lines.append("- Solana only, when the post is about Solana: xStocks and PreStocks, one margin account, up to 5x, no funding rate. Do not draw a Stellar figure on that poster.")
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


def _taste_rules() -> str:
    from pipeline.gtm_creative.taste import rubric
    text = rubric()
    return ("\n\n" + text) if text else ""


# The founder's rulebook forbids these, and the creative judge rejects on
# them, but neither the image prompt nor this file's own judge said so. Run
# GTM-20260925-104259 drew an isometric safe with a dial and a 3D cardboard
# box, passed its own judge as SHIP, and was rejected at the end of a
# 14-minute run, after its video had been built from it.
FLAT_RULE = (
    "FLAT, FACE-ON ONLY: every element is drawn flat and straight-on "
    "(cards, boundaries, straight arrows). Never "
    "isometric, 3D, angled or perspective objects; never safes, vaults, "
    "combination dials, boxes or crates, coins, tokens or piles of wealth.")
# Flat is for Veo: an angled object makes it tilt the camera.
STILL_RULE = (
    "FLAT AND FACE-ON. Cards are opaque. Never safes, vaults, "
    "combination dials, boxes or crates, coins, tokens or piles of wealth.")

NO_GLASS = (
    "NO GLASSMORPHISM. This is binding and overrides the attached posters. "
    "Do not draw frosted glass, blur, a translucent or see-through card, "
    "a glow bleeding through a fill, or a neon glass border. "
    "Cards are solid and opaque, with a hairline edge. "
    "The attached posters are the bar for type, spacing, logo, and contrast only. "
    "Do not copy their glass.")


GLASS_ACCENT = (
    "GLASS AS AN ACCENT ONLY. Exactly ONE element is frosted glass: the card this brief is about "
    "(see Material). It is a soft frosted panel with a fine bright edge. Everything else — the "
    "ground, every other card, every label, arrow and icon — is opaque, matte and crisp. Do not "
    "frost the background, do not make several glass cards, do not let a glow bleed across the poster.")


def _line(brief: str, key: str) -> str:
    """One `Key: value` line of the brief."""
    for ln in str(brief or "").splitlines():
        if ln.lower().startswith(key.lower() + ":"):
            return ln.split(":", 1)[1].strip()
    return ""


def _point(brief: str) -> str:
    """The poster's job in one line: what a stranger must get in three seconds."""
    take, focal = _line(brief, "Takeaway"), _line(brief, "Focal")
    if not take:
        return ""
    return ("THE POINT: a stranger must understand \"" + take + "\" from this image in three seconds, before "
            "reading the caption." + (" The focal element is " + focal + ": make it the largest, clearest "
            "thing on the poster, and let everything else support it." if focal else "") + "\n\n")


def _material(brief: str) -> str:
    line = next((ln for ln in brief.splitlines() if ln.lower().startswith("material:")), "")
    return line.split("—", 1)[0].replace("Material:", "").strip().lower()


def _material_rule(brief: str) -> str:
    """The surface the brief names. Glass only when it names glass_accent, on one card."""
    name = _material(brief)
    if name == "glass_accent":
        return "SURFACE: matte opaque cards with ONE glass accent. " + GLASS_ACCENT
    if name == "editorial":
        return "SURFACE: no cards and no panels. Type and one thin-line diagram on the open ground. " + NO_GLASS
    if name == "line":
        return "SURFACE: a hairline technical drawing. Open shapes, no filled slabs. " + NO_GLASS
    if name == "print":
        return "SURFACE: hard-edged flat ink blocks, like a printed page. No transparency. " + NO_GLASS
    return "SURFACE: opaque matte cards, a hairline border, nothing showing through the fill. " + NO_GLASS


def _shape_rule(animated: bool) -> str:
    return FLAT_RULE if animated else STILL_RULE


def _prompt(brief: str, correction: str = "", approved: int = 0,
            animated: bool = True) -> str:
    has_logo = _logo() is not None
    last = " The LAST image is the official logo." if has_logo else ""
    ground = _ground()
    return (
        "You are designing ONE finished square (1:1) image for an X post by "
        + _c().company_name() + ".\n\n"
        + ("ATTACHED IMAGES: the FIRST " + str(approved) + " are posters the "
           "founder APPROVED — the quality bar, and the way to compose one: an "
           "explanatory diagram built from clear cards, icons and "
           "arrows, clearly contrasting the problem with " + _c().company_name() + "'s answer. Match "
           "that level and that density. Follow the layout and the MATERIAL named in this brief. "
           + ("Their glass is allowed on the ONE accent card only. " if _material(brief) == "glass_accent"
              else "Do not copy their frosted glass, blur, or glowing translucent borders. ") +
           "Do NOT copy their text or redraw the same diagram. The images after them" + (", except the last," if has_logo else "")
           + " are further STYLE REFERENCES." + last + "\n\n"
           if approved else
           "ATTACHED IMAGES: " + ("all images except the last" if has_logo else "the images")
           + " are STYLE REFERENCES from the brand's own website and designs." + last + "\n\n")
        + "FORMAT: one full-bleed square, the brand's ground colour" + (" " + ground if ground else "")
        + " running edge to edge — no borders, bands or frame around it.\n\n"
        + ("BRAND COLOURS (use these, not others): " + _palette_line() + ".\n\n" if _palette_line() else "")
        + "Match the references' house style exactly: " + _c().house_style()
        + ". Generous spacing, nothing overlapping, everything aligned.\n\n"
        + _point(brief)
        + _shape_rule(animated) + "\n\n"
        + _material_rule(brief) + "\n\n"
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
        + _taste_rules()
        + "\n\nTHE POST THIS IMAGE IS FOR:\n" + " ".join(brief.split())
        + "\n\nDraw the mechanism this post describes. Do not add Blend, "
          "Aquarius, or a SmartAccount sandbox unless the post text names them. "
          "A Solana post does not use the Stellar diagram."
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
    '"taste_score": int (1-10, would the founder approve it), '
    '"closer_to": "approved"|"sent_back", "taste_faults": [str], '
    '"verdict": "SHIP"|"REVISE"|"REJECT", "fix": str}'
)
TASTE_BAR = 7


def _taste_section(n_ok: int, n_bad: int, first: int) -> str:
    from pipeline.gtm_creative.taste import rubric

    if not (n_ok or n_bad):
        return ""
    lines = ["\n\nTASTE — the founder's own decisions, attached after the poster"
             + (" and the logo" if _logo() else "") + ":"]
    if n_ok:
        lines.append("  images " + str(first) + "-" + str(first + n_ok - 1)
                     + ": posters the founder APPROVED.")
    if n_bad:
        lines.append("  images " + str(first + n_ok) + "-" + str(first + n_ok + n_bad - 1)
                     + ": posters the founder KILLED or sent back, although each passed "
                     "every check above.")
    lines.append("Score `taste_score` 1-10 for how surely the founder approves the poster "
                 "under review, set `closer_to` to the pile it resembles in headline, idea "
                 "and composition (not colours, which all share), and list `taste_faults` "
                 "in the words of the taste rules below. A poster under " + str(TASTE_BAR)
                 + " or closer to the sent-back pile is not SHIP, and `fix` names what to "
                 "change.\n" + rubric())
    return "\n".join(lines)


def judge(image: Path, brief: str, *, animated: bool = True) -> dict[str, Any]:
    from pipeline.gtm_creative.taste import jargon, overclaims, piles
    from pipeline.gtm_os import agent_runtime as R

    import hashlib

    def _digest(p: Path) -> str:
        return hashlib.sha1(Path(p).read_bytes()).hexdigest()

    pile = piles(approved=2, sent_back=5)
    me = _digest(image)
    # The approved side is the founder's approved posters closest to this
    # topic (the same ones the image model was shown), the newest as fallback.
    # A poster is never compared with a copy of itself.
    ok = [p for p in _refs(brief, ["approved_poster"], 3, min_score=0.7)
          if _digest(p) != me] or [
        p["path"] for p in pile["approved"] if _digest(p["path"]) != me]
    bad = [p["path"] for p in pile["sent_back"] if _digest(p["path"]) != me]
    said = " ".join(line for line in brief.splitlines()
                    if line.lower().startswith(("headline", "subtitle", "footer")))
    first = 3 if _logo() else 2
    prompt = (
        ("The FIRST image is the poster to review. The SECOND is the official "
         + _c().company_name() + " logo.\n\n" if _logo() else
         "The image is the poster to review (no logo file exists; the name should appear once as a "
         "plain wordmark).\n\n") + _facts() + "\n\nThe brief was:\n" + brief + "\n\n"
        "Check: every word spelled correctly and not garbled; no figure that "
        "is not in the facts list; the logo matches the official one (not a "
        "cube); nothing overlaps or is cut off; the image is about the brief; "
        + ("THREE-SECOND TEST: from the image alone, would a stranger get \"" + _line(brief, "Takeaway")
           + "\"? If the picture is a generic diagram that does not show it, that is a REVISE, and the fix "
           "says what to draw instead. " if _line(brief, "Takeaway") else "")
        + ("GLASS: this brief allows ONE frosted-glass accent card; more than one glass element, "
           "a frosted background, or glow bleeding across the poster is a REJECT. "
           if _material(brief) == "glass_accent" else
           "NO GLASSMORPHISM on this poster: frosted, blurred, see-through, or neon-bordered glass "
           "cards are a REJECT, even if an approved poster looks like that. ") +
        "matches_reference_style means type, spacing, logo, contrast and density, "
        "not a frosted fill. "
        "no logo or brand mark of ANY other protocol (" + _venues() + " and "
        "others appear as plain text names only — an invented "
        "icon for them is a fake brand mark); no markdown characters "
        "(asterisks, underscores, hashes) rendered as text; " + _shape_rule(animated) + " "
        "BASIC ERRORS the founder never wants: the same label, name or figure "
        "printed twice (a card titled \"~320ms\" that also holds \"~320ms\"; a "
        "container and the card inside it both named \"Isolated SmartAccount\"; "
        "the venue names drawn twice); an arrow that leaves the frame, ends at "
        "nothing or goes through a card; a figure written on an arrow as its "
        "label; an icon or chart that explains nothing (radar rings, a random "
        "spike line, a progress bar, bars or brackets clamped on a card); a card "
        "that is empty or holds only a title; a grid of cards that are each just a "
        "figure; a sentence left hanging (ends on a dash or comma); a promise the "
        "facts do not support (eliminates, cannot, never, guaranteed, bank-grade, "
        "stays safe); a drawing that contradicts the headline (isolated accounts "
        "wired into a shared pool in the middle); filler status text (\"Calm "
        "status\", \"Healthy\") standing in for a mechanism. Count every figure "
        "on the poster, subtitle and labels included: a figure that appears more "
        "than once (\"1.10x floor\" in a title and \"1.10x\" beside its meter) is a "
        "BASIC ERROR. "
        "REJECT on any spelling error, invented figure, wrong logo, another "
        "protocol's logo, markdown characters, overlap, any BASIC ERROR above, "
        + ("any isometric/3D object, " if animated else "")
        + "or any safe, vault, box or coin. A colour outside the palette is "
        "NOT a reason to reject on its own, but name it in `fix` if present. `fix` says exactly what to change, "
        "in one or two sentences." + _learned_rules()
        + _taste_section(len(ok), len(bad), first)
        + "\n\nReturn JSON exactly:\n" + JUDGE_SCHEMA
    )
    v = R.brain_vision(prompt, [image] + ([_logo()] if _logo() else []) + ok + bad,
                       agent="A15_creative_judge", system=JUDGE_SYSTEM, role="reasoning",
                       temperature=0.1, max_output_tokens=4096)
    # The model's own verdict can still say SHIP beside a low taste score;
    # the bar is applied here so a poster like the killed ones is redrawn.
    try:
        score = int(v.get("taste_score"))
    except (TypeError, ValueError):
        score = None
    spec = jargon(said)
    if spec:
        v["taste_faults"] = list(v.get("taste_faults") or []) + [
            "protocol jargon in the headline or subtitle: " + ", ".join(spec)]
    promised = overclaims(said)
    if promised:
        v["taste_faults"] = list(v.get("taste_faults") or []) + [
            "headline or subtitle promises more than the facts: " + ", ".join(promised)]
        spec = spec + promised
    if str(v.get("verdict")).upper() == "SHIP" and (
            spec or ((ok or bad) and (
                (score is not None and score < TASTE_BAR)
                or str(v.get("closer_to")).lower() == "sent_back"))):
        faults = "; ".join(str(f) for f in (v.get("taste_faults") or []) if f)
        why = ("taste " + str(score) + "/10" if score is not None else "taste unscored")
        if str(v.get("closer_to")).lower() == "sent_back":
            why += ", closer to the posters the founder sent back"
        v["verdict"] = "REVISE"
        v["fix"] = (why[0].upper() + why[1:] + (": " + faults if faults else "") + ". "
                    + str(v.get("fix") or "")).strip()
    return v


def _find_lockup(inked, x0: int, x1: int, y0: int, y1: int):
    """(top, bottom, left, right) of the first inked run in the band, or None."""
    # A row inked across most of the width is a band or rule the model drew
    # along the edge, not a lockup; one poster opened with a violet strip and
    # the strip was patched instead of the logo.
    cols_sampled = len(range(x0, x1, 2))
    rows = [y for y in range(y0, y1)
            if 3 <= sum(inked(x, y) for x in range(x0, x1, 2)) < cols_sampled * 0.6]
    if not rows:
        return None
    # The first contiguous run of inked rows is the lockup; anything below a
    # gap is the headline starting.
    top_y, bot_y = rows[0], rows[0]
    for y in rows[1:]:
        if y - bot_y > 6:
            break
        bot_y = y
    cols = [x for x in range(x0, x1) if any(inked(x, y) for y in range(top_y, bot_y + 1, 2))]
    if not cols or bot_y - top_y < 12:
        return None
    return top_y, bot_y, cols[0], cols[-1]


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
    # Ink is whatever differs from the ground under it. The ground is taken
    # per row from the edges of the scanned band, so a gradient (Vanna's glow,
    # a blue Morpho field) is ground, and a light or saturated ground is not
    # mistaken for ink — a fixed "bright or saturated" test marked a whole
    # blue poster as ink and never found its lockup.
    row_ground = {}
    for y in range(y0, y1):
        edge = [px[x, y] for x in list(range(x0, x0 + 12)) + list(range(x1 - 12, x1))]
        row_ground[y] = tuple(sorted(c[i] for c in edge)[len(edge) // 2] for i in range(3))

    def local_ink(x: int, y: int) -> bool:
        r, g, b = px[x, y]
        gr = row_ground.get(y) or px[x0, y]
        return abs(r - gr[0]) + abs(g - gr[1]) + abs(b - gr[2]) > 140

    def dark_ink(x: int, y: int) -> bool:      # the original test, right for Vanna's dark ground
        r, g, b = px[x, y]
        return max(r, g, b) > 150 or (max(r, g, b) - min(r, g, b) > 90 and max(r, g, b) > 90)

    found = None
    for inked in (local_ink, dark_ink):
        found = _find_lockup(inked, x0, x1, y0, y1)
        if found:
            break
    if not found:
        return False
    top_y, bot_y, lx0, lx1 = found

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
         attempts: int = 3, extra_refs: Optional[list] = None,
         animated: bool = True) -> dict[str, Any]:
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
        generate_gemini_image(prompt=_prompt(brief, correction, len(approved), animated),
                              output_path=path,
                              model=MODEL, temperature=0.7, images=imgs,
                              aspect_ratio="1:1")
        # The real lockup replaces the drawn one before the judge looks, so a
        # wrong mark costs nothing instead of a whole attempt.
        fix_logo(path)
        v = {}
        for _ in range(2):                          # a transient model error is not a verdict
            try:
                v = judge(path, brief, animated=animated)
                break
            except Exception as exc:                # noqa: BLE001 — boundary
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
