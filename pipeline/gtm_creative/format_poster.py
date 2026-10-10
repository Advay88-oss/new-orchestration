"""The founder's-format poster: what replicating the founder's launch slides taught.

When the founder has locked a format set (visual_exemplars, a set of real
slides), a new post is made the way the replicas were made well, not the way
the first attempts went wrong:

  Director (A07 Motion/Art Director, "director" model, sees the slides)
    picks the ONE founder slide whose layout fits the topic (flow diagram,
    phones on a coloured panel, a health card...), tells the story (who /
    what / what it means), and writes EVERY string on the slide: eyebrow,
    headline lines, sub line, spec rows, and the text inside every phone,
    card and chip. Facts come from the brand brain; app numbers are sample
    data and the footer says so; a Solana post carries no Stellar figure.

  Poster (A08, Nano Banana 2.1 via agent_runtime.MODELS["poster"])
    is shown that slide at full resolution plus its two halves (so the small
    text is legible to it), copies its layout with the new strings at
    temperature 0.3, 2K. It draws no logo: the real one is cut from the
    founder's slide and pasted in the same place afterwards.

  Judge (A08's own, vision) compares with the base slide, checks every
  required string on the zoomed halves, and its differences go back once.

    python -m pipeline.gtm_creative.format_poster "topic" [--out DIR]
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any, Optional

from PIL import Image, ImageFilter

AGENT_DIRECTOR = "A14_motion_director"      # journals under A07 (agent_runtime.MERGED)
AGENT_POSTER = "A08_visual_synthesis"
CACHE = Path(__file__).resolve().parents[1] / "brain" / "visual_exemplars" / "_format_cache"
SAMPLE_FOOTER = "Devnet preview · sample data"


# --------------------------------------------------------------- the set
def bases() -> list[dict]:
    """The founder's locked slides: id, path, what each one is."""
    from pipeline.gtm_learning import visual_exemplars as V
    rows = [r for r in V._rows() if r.get("format_set")]
    if not rows:
        return []
    # A named set (VANNA_FORMAT_SET) — e.g. the founder's launch deck or the
    # Vanna brand posts — else the newest one locked.
    want = os.environ.get("VANNA_FORMAT_SET", "").strip()
    newest = want if want and any(r["format_set"] == want for r in rows) else         max(rows, key=lambda r: r.get("at", ""))["format_set"]
    out = []
    for r in rows:
        p = V.EX_DIR / r["file"]
        if r["format_set"] == newest and p.exists():
            out.append({"id": r["id"], "path": p, "brief": str(r.get("brief") or ""),
                        "note": str(r.get("note") or "")})
    return out


def theme() -> str:
    """When VANNA_FORMAT_THEME=brand: the brand's own colours over the
    founder's layout, from the brand profile's palette. Empty otherwise."""
    if os.environ.get("VANNA_FORMAT_THEME", "").strip().lower() != "brand":
        return ""
    from pipeline.brand_brain import context as C
    p = C.palette()
    ground = p.get("ground", "#07020D")
    acc, acc2, risk = p.get("accent", "#703AE6"), p.get("accent_light", "#A387FF"), p.get("risk", "#FC5457")
    glows = ", ".join(v for k, v in p.items() if k.startswith("glow"))
    return ("BRAND THEME (replaces the reference's colours; keep its layout and type): a near-black ground "
            + ground + " with soft radial glows" + (" (" + glows + ")" if glows else "") + " in the corners; "
            "the rounded panel behind the phones filled with the brand gradient, coral " + risk + " to violet "
            + acc + ", not teal or a flat colour; headline line 1 white, line 2 in the coral-to-violet gradient; "
            "eyebrow in " + acc2 + " with a short gradient underline; spec-row labels grey, values white; app "
            "screens in a dark mode that matches (cards #16101F, text white, accents " + acc + " / " + acc2
            + "); buttons in the gradient; footer grey. White logo wordmark.")


def active() -> bool:
    return bool(bases())


def _halves(path: Path) -> tuple[Path, Path]:
    CACHE.mkdir(parents=True, exist_ok=True)
    left, right = CACHE / (path.stem + "_L.jpg"), CACHE / (path.stem + "_R.jpg")
    if not (left.exists() and right.exists()):
        im = Image.open(path).convert("RGB")
        w, h = im.size
        im.crop((0, 0, w // 2 + w // 40, h)).save(left, quality=93)
        im.crop((w // 2 - w // 40, 0, w, h)).save(right, quality=93)
    return left, right


def _sheet(items: list[dict]) -> Path:
    """One contact sheet of the slides, labelled by id, for the director."""
    CACHE.mkdir(parents=True, exist_ok=True)
    key = "_".join(i["id"][:6] for i in items)
    out = CACHE / ("sheet_" + key + ".jpg")
    if out.exists():
        return out
    from PIL import ImageDraw
    tw = 640
    thumbs = []
    for it in items:
        im = Image.open(it["path"]).convert("RGB")
        im.thumbnail((tw, tw))
        thumbs.append((it["id"], im))
    th = max(t.height for _, t in thumbs)
    cols = 3
    rows = (len(thumbs) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * (tw + 16) + 16, rows * (th + 52) + 16), (235, 235, 235))
    d = ImageDraw.Draw(sheet)
    for k, (sid, t) in enumerate(thumbs):
        x, y = 16 + (k % cols) * (tw + 16), 16 + (k // cols) * (th + 52)
        d.text((x, y), sid, fill=(0, 0, 0))
        sheet.paste(t, (x, y + 20))
    sheet.save(out, quality=88)
    return out


# --------------------------------------------------------------- director
def direct(query: str, hook: str = "", body: str = "", *, run_id: Optional[str] = None) -> dict:
    """The Motion/Art Director's brief for one founder-format slide."""
    from pipeline.brand_brain import context as C
    from pipeline.gtm_os import agent_runtime as R

    items = bases()
    if not items:
        raise RuntimeError("no founder format set is locked")
    menu = "\n".join("  " + it["id"] + ": " + it["brief"][:260] for it in items)
    solana = bool(re.search(r"solana|xstock|tslax|aaplx|prestock|pre-ipo|openai|kamino|jupiter",
                            (query + " " + hook + " " + body).lower()))
    scope = str(C.rule("figure_scope") or "")
    system = C.fill(
        "You are {company}'s Motion/Art Director. You brief ONE slide in the founder's launch format, "
        "which the image model will build by copying the layout of one of the founder's own slides. "
        "Return strict JSON only.")
    prompt = (
        C.facts_block(query or hook, k=6, excerpts=3) + "\n\n----\n\n"
        + "THE FOUNDER'S FORMAT: " + items[0]["note"] + "\n\n"
        + (theme() + " Choose `panel` and every colour from this theme.\n\n" if theme() else "")
        + "THE FOUNDER'S SLIDES (attached as one sheet, labelled by id):\n" + menu + "\n\n"
        + "TELL ONE STORY a stranger gets in three seconds: WHO it is for, WHAT they can do or what happens, "
          "and what it MEANS for them. Pick the founder slide whose LAYOUT best carries that story (a flow "
          "diagram for how money moves, phones on a coloured panel for a product screen, a big number card "
          "for risk). Then write EVERY word that will be on the new slide, including the text inside every "
          "phone screen, card, chip and button: the image model may draw no other word.\n"
        + "MAKE IT DIFFERENT. The founder's slide gives the DESIGN SYSTEM (type, colours, card and phone "
          "design language, spacing, footer), not the composition: a post that looks like a copy of one of "
          "his slides has failed. Change at least TWO of: (1) the right-half arrangement (one phone instead of "
          "two, phones overlapping or tilted differently, a stack of app cards instead of phones, a different "
          "diagram shape); (2) the panel or ground colour, within the founder palette (violet, teal, magenta, "
          "graphite; dark or light ground); (3) the headline position (left, or centred above the visual); "
          "(4) the visual subject (a different screen, a different card). Keep the logo top-left and the footer "
          "as the founder has them. List every visual element in `elements`; the image model draws nothing else.\n"
        + "WORDING: use the founder's own phrases (as on his slides) and the wording of the facts above. Do not "
          "coin product terms, token names or features the facts do not name.\n"
        + "RULES: state only what the facts above say; numbers inside app screens are sample data, kept "
          "plausible and consistent with each other; the footer follows the format (with app screens: "
          "'vanna.finance' and '" + SAMPLE_FOOTER + "'; otherwise 'vanna.finance' and the deployment); "
          "no slide counter; never name a competitor; headline 2-3 short lines, under 10 words in all; "
          "sub line under 22 words; 2-3 spec rows (label, value) when the base slide has them; "
          "app text short (1-4 words per string). "
        + ("This is a Solana post: no Stellar figure or Stellar venue anywhere. " if solana else "")
        + (scope + " " if scope else "") + "\n\n"
        + "THE TOPIC: " + " ".join(str(query).split())[:600] + "\n"
        + ("THE POST — hook: " + hook[:300] + "\nbody: " + " ".join(body.split())[:900] + "\n" if hook or body else "")
        + '\nReturn JSON: {"base": str (one id from the sheet), "why_base": str, '
          '"story": {"who": str, "what": str, "means": str}, "eyebrow": str (1-3 words), '
          '"headline": [str] (2-3 lines), "sub": str, "spec_rows": [[str, str]], '
          '"ui": [{"element": str (e.g. "right phone, summary card"), "text": [str]}], '
          '"panel": str (the panel/ground colour to use, from the founder palette), '
          '"composition": str (how this slide is arranged and which two or more things differ from the base slide), '
          '"elements": [str] (every visual element, left to right), '
          '"footer": [str] (the footer strings exactly as this format uses them), "takeaway": str}')
    out = R.brain_vision(prompt, [_sheet(items)], agent=AGENT_DIRECTOR, system=system, role="director",
                         temperature=0.4, max_output_tokens=6144, run_id=run_id)
    ids = {it["id"] for it in items}
    if str(out.get("base")) not in ids:
        out["base"] = items[0]["id"]
    out["solana"] = solana
    R.record_decision(AGENT_DIRECTOR, "poster_brief", {"brief": out}, run_id=run_id)
    return out


def brief_text(d: dict) -> str:
    """The brief as text: what the run summary keeps and the fact check reads."""
    rows = "; ".join(str(a) + ": " + str(b) for a, b in (d.get("spec_rows") or []) if a or b)
    ui = " | ".join(" ".join(str(t) for t in (el.get("text") or [])) for el in (d.get("ui") or []))
    st = d.get("story") or {}
    return ("Format: founder slide (base " + str(d.get("base")) + ")"
            + "\nComposition: " + str(d.get("composition") or "")
            + "\nTakeaway: " + str(d.get("takeaway") or "")
            + "\nStory: who = " + str(st.get("who", "")) + "; what = " + str(st.get("what", ""))
            + "; means = " + str(st.get("means", ""))
            + "\nHeadline: " + " ".join(str(x) for x in d.get("headline") or [])
            + "\nSubtitle: " + str(d.get("sub") or "")
            + "\nLabels (exact words): " + str(d.get("eyebrow") or "") + "; " + rows + "; " + ui)


# --------------------------------------------------------------- poster
def _strings(d: dict) -> tuple[list[str], list[str]]:
    slide = ["vanna", str(d.get("eyebrow") or "")] + [str(x) for x in d.get("headline") or []]
    slide += [str(d.get("sub") or "")]
    for row in d.get("spec_rows") or []:
        slide += [str(x) for x in row]
    slide += [str(x) for x in (d.get("footer") or ["vanna.finance", SAMPLE_FOOTER])]
    ui = ["[" + str(el.get("element")) + "] " + " | ".join(str(t) for t in el.get("text") or [])
          for el in d.get("ui") or []]
    return [s for s in slide if s.strip()], ui


def _prompt(d: dict, correction: str = "") -> str:
    slide, ui = _strings(d)
    return (
        "You are Vanna's visual agent. Make a NEW slide in the DESIGN SYSTEM of the FIRST attached image (the "
        "founder's launch slide): its type sizes and weights (Plus Jakarta Sans), colours, spec-row styling, "
        "card and phone-mockup design language, spacing, logo position and footer"
        + (", with " + str(d["panel"]) if d.get("panel") else "") + ". The SECOND and THIRD images are its "
        "halves at full resolution, for the details. Do NOT copy its composition; use THIS one:\n  "
        + str(d.get("composition") or "a new arrangement of the same kind of elements") + "\n"
        + ("ELEMENTS (draw these and nothing else; no extra cards, rows or screens):\n"
           + "\n".join("  - " + str(e) for e in d.get("elements") or []) + "\n" if d.get("elements") else "")
        + (theme() + "\n" if theme() else "")
        + "No slide counter.\n\n"
        "SLIDE TEXT (exactly these words, in the places the reference uses for them; headline lines break "
        "where given):\n" + "\n".join("  " + s for s in slide)
        + ("\n\nTEXT INSIDE THE PHONES, CARDS AND CHIPS (copy every string exactly, letter for letter; these "
           "are the only words allowed there):\n" + "\n".join("  " + s for s in ui) if ui else "")
        + "\n\nLOGO: leave the logo area top-left as the reference has it; the real logo is pasted afterwards. "
          "Add no other logo, watermark or element."
        + ("\n\nFIX THESE PROBLEMS FROM THE LAST ATTEMPT:\n" + correction if correction else ""))


def _logo_box(im: Image.Image) -> tuple[int, int, int, int]:
    """The logo in the slide's top-left corner: the first ink cluster."""
    w, h = im.size
    region = im.crop((0, 0, int(w * .28), int(h * .16))).convert("RGB")
    bg = region.getpixel((5, 5))
    px = region.load()
    rw, rh = region.size

    def ink(x: int, y: int) -> bool:
        return sum(abs(a - b) for a, b in zip(px[x, y], bg)) > 60
    cols = [x for x in range(rw) if any(ink(x, y) for y in range(0, rh, 2))]
    if not cols:
        return (0, 0, 0, 0)
    end = cols[0]
    for x in cols[1:]:
        if x - end > int(w * .012):
            break
        end = x
    rows = [y for y in range(rh) if any(ink(x, y) for x in range(cols[0], end + 1, 2))]
    return (cols[0], rows[0], end + 1, rows[-1] + 1)


def paste_logo(made: Path, base: Path) -> bool:
    """Replace whatever logo was drawn with the real one from the founder's
    slide: clear the area to the new slide's own ground, then lay the logo's
    ink (masked, so the base slide's ground never comes along)."""
    out = Image.open(made).convert("RGB")

    def lum(px: tuple) -> float:
        return .299 * px[0] + .587 * px[1] + .114 * px[2]
    # The logo's wordmark is dark on a light slide and light on a dark one:
    # take it from a founder slide whose ground matches the NEW slide's.
    dark = lum(out.getpixel((max(1, int(out.width * .01)), max(1, int(out.height * .02))))) < 128
    candidates = [Path(base)] + [it["path"] for it in bases() if Path(it["path"]) != Path(base)]
    src_path = Path(base)
    for p in candidates:
        with Image.open(p) as im:
            g = im.convert("RGB").getpixel((5, 5))
        if (lum(g) < 128) == dark:
            src_path = p
            break
    ref = Image.open(src_path).convert("RGB")
    box = _logo_box(ref)
    if box[2] <= box[0]:
        return False
    sx, sy = out.width / ref.width, out.height / ref.height
    pad = int(ref.width * .006)
    src = ref.crop((max(0, box[0] - pad), max(0, box[1] - pad), box[2] + pad, box[3] + pad))
    bg = src.getpixel((1, 1))
    mask = Image.new("L", src.size, 0)
    sp, mp = src.load(), mask.load()
    for x in range(src.width):
        for y in range(src.height):
            d = sum(abs(a - b) for a, b in zip(sp[x, y], bg))
            mp[x, y] = max(0, min(255, int(d * 2.2)))
    tw, th = max(1, int(src.width * sx)), max(1, int(src.height * sy))
    tx, ty = int((box[0] - pad) * sx), int((box[1] - pad) * sy)
    # Clear the drawn logo with the ground that surrounds it, interpolated
    # between the rows just above and below: a flat fill left a visible box
    # on a glowing, gradient ground.
    clear = int(out.width * .012)
    x0, y0 = max(1, tx - clear), max(1, ty - clear)
    x1, y1 = min(out.width - 2, tx + tw + clear), min(out.height - 2, ty + th + clear)
    px = out.load()
    for x in range(x0, x1):
        top, bot = px[x, y0 - 1], px[x, y1 + 1]
        for y in range(y0, y1):
            t = (y - y0) / max(1, y1 - y0)
            px[x, y] = tuple(int(a + (b - a) * t) for a, b in zip(top, bot))
    region = out.crop((x0, y0, x1, y1)).filter(ImageFilter.GaussianBlur(3))
    out.paste(region, (x0, y0))
    out.paste(src.resize((tw, th), Image.LANCZOS), (tx, ty),
              mask.resize((tw, th), Image.LANCZOS).filter(ImageFilter.GaussianBlur(.6)))
    out.save(made)
    return True


def judge(made: Path, base: Path, d: dict) -> dict:
    from pipeline.gtm_os import agent_runtime as R
    m = Image.open(made).convert("RGB")
    w, h = m.size
    ml, mr = made.with_name(made.stem + "_L.jpg"), made.with_name(made.stem + "_R.jpg")
    m.crop((0, 0, w // 2 + w // 40, h)).save(ml, quality=92)
    m.crop((w // 2 - w // 40, 0, w, h)).save(mr, quality=92)
    slide, ui = _strings(d)
    return R.brain_vision(
        "Image 1 is the founder's slide (the style). Image 2 is a NEW slide in that style; images 3 and 4 are "
        "its left and right halves. Check: (a) the layout and type match the founder's slide"
        + ("; its colours follow this theme instead of the reference's: " + theme() if theme() else "")
        + "; (b) every required "
        "string appears exactly, spelled exactly, with no invented text; (c) the logo appears once, top-left; "
        "(d) a stranger gets the point in three seconds; (e) it is NOT a copy of the founder slide's composition "
        "(the asked composition: " + str(d.get("composition") or "") + ") — a near-copy is REVISE; (f) no "
        "element beyond these: " + " / ".join(str(e) for e in d.get("elements") or []) + "."
        "\nREQUIRED SLIDE TEXT: " + " / ".join(slide)
        + "\nREQUIRED UI TEXT: " + " / ".join(ui) + "\n"
        'Return JSON: {"score": int (0-10), "differences": [str] (most important first, each a concrete fix '
        'with the exact correct text), "verdict": "SHIP"|"REVISE"|"REJECT"}',
        [base, made, ml, mr], agent=AGENT_POSTER, role="reasoning", temperature=0.0, max_output_tokens=2048,
        system="You are the visual agent's judge. Be exact and brief.")


def make(d: dict, name: str, out_dir: Path, attempts: int = 2) -> dict[str, Any]:
    from pipeline.gtm_os import agent_runtime as R
    from pipeline.scripts.gemini_flash_image import generate_gemini_image
    base = next((it["path"] for it in bases() if it["id"] == d.get("base")), bases()[0]["path"])
    left, right = _halves(base)
    with Image.open(base) as im:
        r = im.width / max(1, im.height)
    aspect = "16:9" if r > 1.3 else "4:5" if r < 0.9 else "1:1"
    out_dir.mkdir(parents=True, exist_ok=True)
    history, correction = [], ""
    for k in range(1, attempts + 1):
        path = out_dir / f"{name}_try{k}.png"
        # 4K, the size of the founder's own slides (4800 px); a model or
        # endpoint that refuses 4K gets 2K instead of failing the post.
        size = os.environ.get("VANNA_POSTER_SIZE", "4K")
        try:
            generate_gemini_image(prompt=_prompt(d, correction), output_path=path, model=R.MODELS["poster"],
                                  temperature=0.3, images=[base, left, right], aspect_ratio=aspect,
                                  image_size=size)
        except Exception:                           # noqa: BLE001 — one retry at 2K
            if size == "2K":
                raise
            generate_gemini_image(prompt=_prompt(d, correction), output_path=path, model=R.MODELS["poster"],
                                  temperature=0.3, images=[base, left, right], aspect_ratio=aspect,
                                  image_size="2K")
        paste_logo(path, base)
        try:
            v = judge(path, base, d)
        except Exception as exc:                    # noqa: BLE001 — keep the image; an unjudged one does not ship
            v = {"score": 0, "differences": ["judge failed: " + str(exc)[:120]], "verdict": "UNJUDGED"}
        history.append({"path": str(path), **v})
        if str(v.get("verdict")).upper() == "SHIP" or int(v.get("score") or 0) >= 9:
            break
        correction = "\n".join("- " + str(x) for x in (v.get("differences") or [])[:8])
    best = max(history, key=lambda h: (str(h.get("verdict")).upper() == "SHIP", int(h.get("score") or 0)))
    final = out_dir / f"{name}.png"
    final.write_bytes(Path(best["path"]).read_bytes())
    return {"name": name, "final": str(final), "attempts": history, "base": str(base)}


def run(query: str, hook: str = "", body: str = "", *, name: str, out_dir: Path,
        run_id: Optional[str] = None) -> dict[str, Any]:
    d = direct(query, hook, body, run_id=run_id)
    res = make(d, name, out_dir)
    res["brief"] = brief_text(d)
    res["director"] = d
    return res


if __name__ == "__main__":
    import argparse
    import sys
    ap = argparse.ArgumentParser()
    ap.add_argument("topic")
    ap.add_argument("--name", default="format_post")
    ap.add_argument("--out", default=str(Path(__file__).resolve().parents[2] / "exports" / "agent-posts"))
    a = ap.parse_args()
    res = run(a.topic, name=a.name, out_dir=Path(a.out))
    print(json.dumps({"final": res["final"], "base": Path(res["base"]).name,
                      "verdicts": [h.get("verdict") for h in res["attempts"]],
                      "scores": [h.get("score") for h in res["attempts"]],
                      "headline": res["director"].get("headline")}, ensure_ascii=False))
    sys.exit(0)
