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
    recent = _recent()
    menu ="\n".join("  " + it["id"] + ": " + it["brief"][:260] for it in items)
    topic = (query + " " + hook + " " + body).lower()
    # A post about both deployments (the waitlist takes Solana, Stellar and EVM wallets) is not a
    # Solana-only post: "Stellar" on it is a fact, not a leak.
    solana = bool(re.search(r"solana|xstock|tslax|aaplx|prestock|pre-ipo|openai|kamino|jupiter", topic)) \
        and "stellar" not in topic
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
        + "THINK FIRST. Propose THREE different concepts for this post, each a different way to SHOW the "
          "idea: a giant number, a two-way comparison, money moving through a flow, an account card with "
          "connectors, one symbolic object, a before/after, kinetic type. A phone is one option, used only when "
          "a screen is truly the clearest way. Then choose the one a stranger gets fastest and say why.\n"
        + (("THE LAST POSTS USED THESE FOUNDER SLIDES: " + ", ".join(recent) + ". Choose a different slide "
            "unless this idea truly needs that layout.\n") if recent else "")
        + "MAKE IT DIFFERENT. The founder's slide gives the DESIGN SYSTEM (type, colours, cards, spacing, "
          "footer), not the composition: a post that looks like a copy of one of his slides has failed. Change "
          "at least TWO of: the arrangement of the visual, the panel or ground colour within the founder "
          "palette, the headline position, the visual subject. Keep the logo top-left and the footer as the "
          "founder has them. List every visual element in `elements`; the image model draws nothing else.\n"
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
        + "THE TOPIC: " + " ".join(str(query).split())[:2400] + "\n"
        + ("THE POST — hook: " + hook[:300] + "\nbody: " + " ".join(body.split())[:900] + "\n" if hook or body else "")
        + '\nReturn JSON: {"concepts": [{"idea": str, "base": str, "visual": str}] (exactly 3), '
          '"chosen": int (index), "why_chosen": str, "base": str (one id from the sheet), "why_base": str, '
          '"story": {"who": str, "what": str, "means": str}, "eyebrow": str (1-3 words), '
          '"headline": [str] (2-3 lines), "sub": str, "spec_rows": [[str, str]], '
          '"ui": [{"element": str (e.g. "right phone, summary card"), "text": [str]}], '
          '"panel": str (the panel/ground colour to use, from the founder palette), '
          '"composition": str (how this slide is arranged and which two or more things differ from the base slide), '
          '"elements": [str] (every visual element, left to right), '
          '"footer": [str] (the footer strings exactly as this format uses them), "takeaway": str}')
    out = R.brain_vision(prompt, [_sheet(items)], agent=AGENT_DIRECTOR, system=system, role="director",
                         temperature=0.4, max_output_tokens=12288, run_id=run_id)
    # Told "no Stellar figure on a Solana post", the director still wrote
    # "HF ≤ 1.1" (the Stellar floor) on a Solana hedge poster, and the judge
    # passed it. Code checks the strings; one rewrite, then no poster.
    leaks = _other_deployment(out) if solana else []
    if leaks:
        out = R.brain_vision(prompt + "\n\nYOUR LAST BRIEF PUT THE OTHER DEPLOYMENT'S FIGURES OR VENUES ON THIS "
                             "SOLANA POST: " + ", ".join(leaks) + ". Write the brief again without them.",
                             [_sheet(items)], agent=AGENT_DIRECTOR, system=system, role="director",
                             temperature=0.4, max_output_tokens=12288, run_id=run_id)
        leaks = _other_deployment(out)
        if leaks:
            raise RuntimeError("the director put Stellar figures on a Solana post twice: " + ", ".join(leaks))
    # Strings the request quotes are the post's facts. Told "Health factor 1.38 → 1.34" exactly,
    # the director wrote "1.42 Safe" and the judge, comparing the image with the director's own
    # strings, passed it. Code checks the brief against the request; one rewrite, then no poster.
    def _n(s: str) -> str:
        return " ".join(str(s).lower().replace("->", "→").replace("’", "'").split()).strip(" .")
    # A quote mark at a word boundary, so the apostrophe in "account's" does not open one.
    quoted = [q for q in re.findall(r"(?<![A-Za-z])'([^']{3,120}?)'(?![A-Za-z])", query)
              if any(ch.isalnum() for ch in q)]
    if quoted:
        def _missing(o: dict) -> list[str]:
            parts = _strings(o)[0] + _strings(o)[1] + [str(o.get("sub") or "")]
            have = _n(" | ".join(parts) + " | " + " ".join(parts))   # a headline over two lines is one string
            return [q for q in quoted if _n(q) not in have]
        lost = _missing(out)
        if lost:
            out = R.brain_vision(prompt + "\n\nYOUR LAST BRIEF CHANGED OR DROPPED STRINGS THE REQUEST GAVE EXACTLY: "
                                 + " | ".join(lost) + ". Use them word for word, numbers included.",
                                 [_sheet(items)], agent=AGENT_DIRECTOR, system=system, role="director",
                                 temperature=0.3, max_output_tokens=12288, run_id=run_id)
            lost = _missing(out)
            if lost:
                raise RuntimeError("the director dropped the request's exact strings twice: " + " | ".join(lost))
    # The founder's format holds about 25 words a poster; a brief of 60 (six boxes, invented labels
    # like "Unified collateral vault") reads as a spec sheet. One rewrite to cut it.
    slide, ui = _strings(out)
    words = len(" ".join(slide[1:]).split())        # the slide's own words; a phone screen's text is the UI
    if words > 40:
        keep = (" Keep these strings word for word: " + " | ".join(quoted) + ".") if quoted else ""
        out = R.brain_vision(prompt + "\n\nYOUR LAST BRIEF HAD " + str(words) + " WORDS ON THE SLIDE. The founder's "
                             "format holds about 25. Keep the one idea, cut every other box and label, and write the "
                             "brief again." + keep, [_sheet(items)], agent=AGENT_DIRECTOR, system=system,
                             role="director", temperature=0.4, max_output_tokens=12288, run_id=run_id)
        # The cut once dropped the asked-for headline: the quoted strings are checked again.
        if quoted and _missing(out):
            raise RuntimeError("the director dropped the request's exact strings while cutting words: "
                               + " | ".join(_missing(out)))
    ids = {it["id"] for it in items}
    if str(out.get("base")) not in ids:
        out["base"] = items[0]["id"]
    out["solana"] = solana
    R.record_decision(AGENT_DIRECTOR, "poster_brief", {"brief": out}, run_id=run_id)
    return out


def _solana_states(num: str) -> bool:
    """True when the brain's Solana product docs state this figure too (the
    1.1x health-factor floor holds on both deployments), so it is not a leak."""
    from pipeline.brand_brain import context as C
    want = re.compile(r"(?<![\d.])" + re.escape(num.rstrip("0").rstrip(".") if "." in num else num) + r"0*(?![\d])")
    for h in C.knowledge_hits(num + " health factor Solana", k=8, sources=["github"]):
        where = (str(h.get("title") or "") + " " + str(h.get("url") or "")).lower()
        if "solana" in where and want.search(str(h.get("text") or "")):
            return True
    return False


def _other_deployment(d: dict) -> list[str]:
    """The profile's Stellar figures and Stellar venues found in a brief's
    strings. The profile's true figures are the Stellar testnet figures
    (prompt rule figure_scope); a venue counts as Stellar when the profile's
    partner list says so."""
    from pipeline.brand_brain import context as C
    slide, ui = _strings(d)
    text = " ".join(slide + ui + [str(d.get("takeaway") or "")])
    found = []
    for f in C.true_figures():
        v = str(f.get("value") or "")
        for num, unit in re.findall(r"(\d+(?:\.\d+)?)\s*([a-zA-Z×]*)", v):
            if "." in num:                          # 1.10x: also "1.1", with or without the x
                pat = r"(?<![\d.])" + re.escape(num.rstrip("0")) + r"0*(?![\d])"
            elif unit:                              # 10x, 320ms: the unit must follow
                pat = r"(?<![\d.])" + num + r"\s*" + re.escape(unit)
            else:
                continue
            if re.search(pat, text, re.I) and not _solana_states(num):
                found.append(v)
        for word in re.findall(r"[A-Za-z]{3,}", v):
            if word.isupper() and re.search(r"\b" + word + r"\b", text):
                found.append(word)                  # e.g. XLM
    for name, what in (C.partners() or {}).items():
        if "stellar" in (str(name) + " " + str(what)).lower() and re.search(r"\b" + re.escape(name) + r"\b", text, re.I):
            found.append(name)
    return sorted(set(found))


RECENT = Path(__file__).resolve().parents[2] / "pipeline" / "state" / "format_recent.json"


def _recent() -> list[str]:
    """The founder slides the last posts were built on (runtime state). Four
    posts in a row came out on the same comparison slide."""
    try:
        return [str(x) for x in json.loads(RECENT.read_text(encoding="utf-8"))][-4:]
    except (OSError, ValueError):
        return []


def _remember(base: str) -> None:
    try:
        RECENT.parent.mkdir(parents=True, exist_ok=True)
        RECENT.write_text(json.dumps((_recent() + [base])[-8:]), encoding="utf-8")
    except OSError:
        pass


def caption(d: dict, query: str, *, run_id: Optional[str] = None) -> dict:
    """The copywriter (A06): the X and LinkedIn text that carries this poster,
    from the facts, the founder's vocabulary and the brain's channel playbook;
    each checked by the claim gate."""
    from pipeline.brand_brain import context as C
    from pipeline.gtm_os import agent_runtime as R
    from pipeline.scripts import claim_safety_gate as G
    play = C.knowledge_hits("channel playbook X LinkedIn Reddit rules", k=4, sources=["rulebook"])
    prompt = (C.facts_block(query, k=6, excerpts=3) + "\n\n----\n\nCHANNEL PLAYBOOK:\n"
              + "\n".join(" ".join(h["text"].split())[:900] for h in play) + "\n\n"
              + "THE REQUEST (this post's own facts): " + " ".join(query.split())[:2400] + "\n\n"
              + "THE POSTER: " + brief_text(d) + "\n\nWrite the post that carries this poster. Say only what the "
              "request and the facts above state: no feature, leverage figure, market or promise they don't give "
              "(never 'guaranteed'; early access is a waitlist, not a promise); any reward keeps its conditions. X: at most 280 "
              "characters, the hook first, one idea, the CTA last. LinkedIn: 80-160 words, the institutional "
              "register, first person plural, one link placeholder [link] at the end. Every number from the "
              "facts with its source; name the deployment.\n"
              'Return JSON: {"x": str, "linkedin": str}')
    out = R.brain_json(prompt, agent="A06_copywriter", role="director", temperature=0.4,
                       max_output_tokens=3072, run_id=run_id)
    for k in ("x", "linkedin"):
        g = G.check(str(out.get(k) or ""), platform="x" if k == "x" else "linkedin", require_testnet=False)
        out[k + "_gate"] = {"pass": g["pass"], "violations": [str(v.get("rule")) + ": " + str(v.get("matched"))
                                                              for v in g["violations"]]}
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
    if d.get("counter"):                            # an improved deck slide keeps its "07 / 09"
        slide.append(str(d["counter"]))
    ui = ["[" + str(el.get("element")) + "] " + " | ".join(str(t) for t in el.get("text") or [])
          for el in d.get("ui") or []]
    return [s for s in slide if s.strip()], ui


def _prompt(d: dict, correction: str = "") -> str:
    slide, ui = _strings(d)
    if d.get("mode") == "improve":
        return (
            "You are Vanna's visual agent. Make a NEW, better version of the FIRST attached image (the founder's "
            "slide). Keep its design system (Plus Jakarta Sans, colours and what each colour means, footer, counter, "
            "logo position) and its topic, but it must NOT be a copy: arrange it like this:\n  "
            + str(d.get("composition") or "") + "\nDESIGN MOVES (all visible):\n"
            + "\n".join("  - " + str(c) for c in d.get("design_moves") or []) + "\n"
            "The founder's slide is a STYLE reference only: do not trace its layout. "
            + ("The OTHER attached images are the founder's launch slides: the FINISH to reach (depth, lit borders, "
               "glass cards, soft glows, crisp product UI), never their layout, text or numbers. "
               if d.get("style_refs") else "")
            + "Content fixes:\n"
            + "\n".join("  - " + str(c) for c in d.get("changes") or []) + "\n"
            "Nothing may be cut off by an edge or by another element; every word whole.\n\n"
            "SLIDE TEXT (exactly these words, in the places the slide uses for them):\n"
            + "\n".join("  " + s for s in slide)
            + ("\n\nTEXT INSIDE THE PHONES, CARDS AND CHIPS (copy every string exactly, letter for letter; these "
               "are the only words allowed there):\n" + "\n".join("  " + s for s in ui) if ui else "")
            + "\n\nLOGO: leave the logo area top-left as the slide has it; the real logo is pasted afterwards."
            + ("\n\nFIX THESE PROBLEMS FROM THE LAST ATTEMPT:\n" + correction if correction else ""))
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
        "(d) a stranger gets the point in three seconds; "
        + ("(e) it keeps the founder slide's topic and design system but visibly applies these design moves: "
           + "; ".join(str(c) for c in d.get("design_moves") or [])
           + " — a near-identical copy of the founder's slide is REVISE, and so is any word cut off by an edge; (f) no "
           if d.get("mode") == "improve" else
           "(e) it is NOT a copy of the founder slide's composition (the asked composition: "
           + str(d.get("composition") or "") + ") — a near-copy is REVISE; (f) no ")
        + "element beyond these: " + " / ".join(str(e) for e in d.get("elements") or []) + "."
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
    # A redesign gets the founder's slide as a style reference only: given it at full resolution with
    # both halves, the image model reproduced it almost pixel for pixel.
    redesign = d.get("mode") == "improve"
    refs, temp = ([base] + [Path(x) for x in d.get("style_refs") or []][:2], 0.5) if redesign \
        else ([base, left, right], 0.3)
    history, correction = [], ""
    for k in range(1, attempts + 1):
        path = out_dir / f"{name}_try{k}.png"
        # 4K, the size of the founder's own slides (4800 px); a model or
        # endpoint that refuses 4K gets 2K instead of failing the post.
        size = os.environ.get("VANNA_POSTER_SIZE", "4K")
        try:
            generate_gemini_image(prompt=_prompt(d, correction), output_path=path, model=R.MODELS["poster"],
                                  temperature=temp, images=refs, aspect_ratio=aspect,
                                  image_size=size)
        except Exception:                           # noqa: BLE001 — one retry at 2K
            if size == "2K":
                raise
            generate_gemini_image(prompt=_prompt(d, correction), output_path=path, model=R.MODELS["poster"],
                                  temperature=temp, images=refs, aspect_ratio=aspect,
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


def _transcript(base_id: str) -> str:
    """The founder slide's own text, transcribed once when the set was locked (exports/founder-refs)."""
    from pipeline.gtm_learning import visual_exemplars as V
    row = next((r for r in V._rows() if r.get("id") == base_id), {})
    m = re.search(r"p(\d\d)_", str(row.get("from") or ""))
    f = Path(__file__).resolve().parents[2] / "exports" / "founder-refs" / ("text_" + m.group(1) + ".json") if m else None
    return f.read_text(encoding="utf-8")[:9000] if f and f.exists() else ""


def improve(base_id: str, *, name: str, out_dir: Path, notes: str = "", post: str = "",
            style_refs: Optional[list] = None, kind: str = "app",
            run_id: Optional[str] = None) -> dict[str, Any]:
    """The founder's own slide, improved in place: the same layout and design, its content checked
    against the brand brain and its finish refined. (The director's usual brief makes a NEW slide in
    the founder's style and is judged for not copying it; this is the opposite job.)"""
    from pipeline.brand_brain import context as C
    from pipeline.gtm_os import agent_runtime as R
    from pipeline.scripts import claim_safety_gate as G
    items = {it["id"]: it for it in bases()}
    if base_id not in items:
        raise RuntimeError("no founder slide " + base_id + " in the active format set")
    base = items[base_id]
    left, right = _halves(base["path"])
    words = _transcript(base_id)
    data = kind == "data"
    style = [Path(x) for x in style_refs or []][:2]
    system = C.fill("You are {company}'s Motion/Art Director. You improve one of the founder's own launch "
                    "slides without changing what it is. Return strict JSON only.")
    prompt = (
        C.facts_block(base["brief"] + " " + (post or words)[:400], k=6, excerpts=3) + "\n\n----\n\n"
        + "THE SLIDE: images 1-3 (full, left half, right half). What it is: " + base["brief"] + "\n"
        + ("THE POST IT CARRIES (the founder's own copy; the slide must agree with it, carry no number or claim "
           "it doesn't make, and keep its careful wording, e.g. 'largely offset', 'we're building'):\n" + post + "\n"
           if post else "")
        + ("THE FINISH THE FOUNDER WANTS: images " + ", ".join(str(4 + i) for i in range(len(style)))
           + " are the founder's launch slides. This slide reads as too basic next to them: bring their depth, "
             "lit borders, glass cards, soft glows and product UI to it, never their layout or text.\n"
           if style else "")
        + ("ITS TEXT NOW (transcribed): " + words + "\n" if words else "")
        + ("THE FOUNDER'S NOTES: " + notes + "\n" if notes else "")
        + "Improve it; it must stay the SAME slide: the same layout, composition, ground and panel colour, phones "
          "and modules, the same topic, eyebrow and slide counter.\n"
        + ("THIS IS A DATA POSTER, not an app screen: no sample-data footer; keep 'vanna.finance', the counter "
           "'n / 8' and the source line exactly as the slide has them. Colour keeps its meaning: coral-red = "
           "synthetic margin, loss, risk; teal = real margin; the violet-to-magenta gradient = Vanna. Design moves "
           "for a data poster: a visual that SHOWS the number (a bar, a stack or a scale drawn to the real ratio), "
           "the comparison as a diagram (two paths, a flow, a ledger), cards with depth (glass, lit borders, glow), "
           "a product moment (the Vanna account card, or a phone showing the margin account) ONLY where the post "
           "is about Vanna, the headline larger with more air. One idea per poster: the headline, ONE short grey "
           "line (never the whole post) and the module; no extra columns of explanation. A venue pill carries "
           "the venue's name and at most what the post says it is for (no 'zero-funding', no invented feature). "
           "No number the post doesn't carry, not even a sample account. The phone rules below apply only where "
           "a phone is drawn.\n" if data else "")
        + "CONTENT: keep every string that is right. Rewrite only a string the facts or the vocabulary above rule "
          "out (for example 'deposit once' is factually wrong: collateral is pooled and deposited many times), a "
          "claim the facts don't support, or the deployment named too strongly (it is a Solana test app"
        + ("" if data else "; the footer reads 'vanna.finance' and '" + SAMPLE_FOOTER + "'")
        + "). Keep sample numbers consistent with each "
          "other. Replace empty states ('—', '0.00', 'Enter an amount') with one filled sample state that agrees "
          "with the slide's own numbers. Never add a feature, market or venue the slide or the facts don't name.\n"
          "DESIGN: nothing cut off by the frame or by another element (a word like 'Histo' or 'levera' is a fault); "
          "clear hierarchy; aligned numbers; even spacing; the same type and colours.\n"
          "REDESIGN, DON'T COPY: the founder wants it better, not the same picture. Keep the topic, the right "
          "strings and the design system (type, colours, card and phone language, footer, counter), and make it "
          "visibly a new, better slide with at least TWO design moves, for example: one hero phone instead of two "
          "overlapping (no phone half-hidden behind another); the phone at a new angle; the key number or card "
          "pulled out of the phone as a floating card; a stronger panel (gradient, shape or position); the headline "
          "larger with more air; a visual element that shows the idea (a flow line, a gauge, chips). Choose the "
          "moves that make the idea clearer, and set `composition` to the NEW arrangement. At least one move must "
          "change the composition itself: a SINGLE hero phone, a card floating OUTSIDE the phone, or the phone at a "
          "NEW ANGLE. Filling an empty state or fixing a cut-off word is a content fix, not a design move. Never "
          "call the test app or its yield 'live'. A floating card never makes a yield, APY or return its hero "
          "number (no return is promised): feature the account's health factor, the leverage change or the route.\n"
        + 'Return JSON: {"base": "' + base_id + '", "counter": str (as on the slide, e.g. "07 / 09"), '
          '"eyebrow": str, "headline": [str], "sub": str, "spec_rows": [[str, str]], '
          '"ui": [{"element": str, "text": [str]}] (every string in every phone, card and chip, after the fixes), '
          '"panel": str, "composition": str (the slide\'s own composition), "elements": [str], '
          '"footer": [str], "changes": [str] (each content or finish fix, with what was wrong), '
          '"design_moves": [str] (at least 2: what is arranged differently and why it reads better), '
          '"takeaway": str}')
    for attempt in range(2):
        out = R.brain_vision(prompt, [base["path"], left, right] + style, agent=AGENT_DIRECTOR, system=system,
                             role="director", temperature=0.3, max_output_tokens=12288, run_id=run_id)
        slide, ui = _strings(out)
        g = G.check(" \n".join(slide + ui), platform="linkedin", require_testnet=False)
        blocked = [v["rule"] + ": " + v["matched"] for v in g["violations"] if v.get("severity") == "BLOCK"]
        if post:
            # A data poster carries the post's numbers and no others (a director once added a
            # $10,000 / $40,000 / 1.60 account the post never mentions), and no jargon.
            def nums(t: str) -> set[str]:
                return {re.sub(r"[,$]", "", m).rstrip(".").lower()
                        for m in re.findall(r"\$?\d[\d,]*(?:\.\d+)?(?:[%xXBMTk](?![A-Za-z]))?", t)}
            extra = sorted(nums(" ".join(slide + ui)) - nums(post) - {"1", "2", "3", "4", "5", "6", "7", "8"}
                           - {str(y) for y in range(2024, 2031)})
            blocked += ["a number the post doesn't carry: " + x for x in extra]
            blocked += [v["rule"] + ": " + v["matched"] for v in g["violations"]
                        if v.get("rule") == "L-custody-jargon"]
        if not blocked:
            break
        prompt += ("\n\nTHE CLAIM GATE BLOCKED YOUR LAST BRIEF: " + "; ".join(blocked)
                   + ". Rewrite those strings within the facts and the vocabulary.")
    else:
        raise RuntimeError(base_id + ": the claim gate blocked the improved slide twice: " + "; ".join(blocked))
    out["base"], out["mode"] = base_id, "improve"
    if style:
        out["style_refs"] = [str(x) for x in style]
    R.record_decision(AGENT_DIRECTOR, "slide_improvement", {"brief": out}, run_id=run_id)
    res = make(out, name, Path(out_dir))
    res["director"] = out
    (Path(out_dir) / (name + ".changes.json")).write_text(json.dumps(
        {"base": base_id, "changes": out.get("changes"), "headline": out.get("headline"), "sub": out.get("sub"),
         "spec_rows": out.get("spec_rows"), "design_moves": out.get("design_moves"),
         "composition": out.get("composition")}, ensure_ascii=False, indent=1), encoding="utf-8")
    return res


def _tokens(s: str) -> set[str]:
    return {t.lower() for t in re.findall(r"[A-Za-z0-9$%+.,:·→-]*[A-Za-z0-9%]", s) if len(t) > 1}


def _words(img: Path) -> set[str]:
    """Every word on a slide, transcribed by the reasoning model."""
    from pipeline.gtm_os import agent_runtime as R
    ask = ('Transcribe every piece of text in this image letter by letter, including tiny labels, numbers and '
           'misspellings (a typo like "Wtset" or "Merit price" is copied as it is, never corrected). '
           'Return JSON: {"text": [str]}')
    for k in range(2):
        try:
            t = R.brain_vision(ask, [img], agent=AGENT_POSTER, role="reasoning", temperature=0.0,
                               max_output_tokens=4096, system="You transcribe. Exact, no corrections.")
            break
        except R.BrainError:
            if k:
                raise
    return {w for s in t.get("text") or [] for w in _tokens(str(s))}


def polish(current: Path, base_id: str, *, name: str, out_dir: Path, notes: str = "",
           run_id: Optional[str] = None) -> dict[str, Any]:
    """Small fixes to a slide that is already right: the director looks at it and lists exact fixes,
    the image model edits that slide (not the founder's) and keeps everything else, and the judge
    checks the fixes landed and nothing else moved. improve() redesigns; this does not."""
    from pipeline.brand_brain import context as C
    from pipeline.gtm_os import agent_runtime as R
    from pipeline.scripts import claim_safety_gate as G
    from pipeline.scripts.gemini_flash_image import generate_gemini_image
    items = {it["id"]: it for it in bases()}
    founder = items[base_id]["path"] if base_id in items else bases()[0]["path"]
    current = Path(current)
    system = C.fill("You are {company}'s Motion/Art Director. You make small, exact fixes to a finished "
                    "slide without changing its design. Return strict JSON only.")
    prompt = (C.facts_block(items.get(base_id, {}).get("brief", "") + " " + notes[:400], k=6, excerpts=3)
              + "\n\n----\n\nTHE SLIDE (image 1) is approved in design. "
              + ("THE FOUNDER'S NOTES: " + notes + "\n" if notes else "")
              + "List the small fixes it still needs: the notes first, then anything cut off, overlapping, "
                "repeated, misaligned, unbalanced, illegible, or a number that disagrees with another on the "
                "slide. Each fix names the element, where it is and exactly what it becomes (any new text "
                "in quotes, letter for letter). No redesign, no new feature, venue or claim; never call the "
                "test app 'live'.\n"
                'Return JSON: {"fixes": [str], "new_text": [str] (every string a fix adds or changes), '
                '"keep": [str] (what must not move)}')
    for _ in range(2):
        d = R.brain_vision(prompt, [current], agent=AGENT_DIRECTOR, system=system, role="director",
                           temperature=0.2, max_output_tokens=4096, run_id=run_id)
        g = G.check(" \n".join(str(s) for s in d.get("new_text") or []) or ".", platform="linkedin",
                    require_testnet=False)
        blocked = [v["rule"] + ": " + v["matched"] for v in g["violations"] if v.get("severity") == "BLOCK"]
        if not blocked:
            break
        prompt += "\n\nTHE CLAIM GATE BLOCKED: " + "; ".join(blocked) + ". Rewrite those strings."
    else:
        raise RuntimeError(name + ": the claim gate blocked the fixes twice: " + "; ".join(blocked))
    R.record_decision(AGENT_DIRECTOR, "slide_polish", {"brief": d, "from": str(current)}, run_id=run_id)
    fixes = [str(f) for f in d.get("fixes") or []]
    keep = [str(k) for k in d.get("keep") or []]
    with Image.open(current) as im:
        r = im.width / max(1, im.height)
    aspect = "16:9" if r > 1.3 else "4:5" if r < 0.9 else "1:1"
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    # The image model redraws every word when it edits, and the judge's eye misses a one-letter slip
    # ('Wallet' -> 'Wtset', 'Mark' -> 'Merit'): transcribe both slides and diff the words instead.
    before = _words(current)
    allowed = {w for s in d.get("new_text") or [] for w in _tokens(str(s))}
    history, correction = [], ""
    for k in range(1, 4):
        path = out_dir / f"{name}_try{k}.png"
        p = ("Edit the attached slide. Keep it the same slide: the same layout, type, colours, phone, cards, "
             "every string and every number, except for exactly these fixes:\n"
             + "\n".join("- " + f for f in fixes)
             + ("\nMUST NOT MOVE: " + "; ".join(keep) if keep else "")
             + "\nNothing cut off by the frame or by another element. The logo top-left stays as it is."
             + ("\n\nFIX THESE PROBLEMS FROM THE LAST ATTEMPT:\n" + correction if correction else ""))
        generate_gemini_image(prompt=p, output_path=path, model=R.MODELS["poster"], temperature=0.2,
                              images=[current], aspect_ratio=aspect,
                              image_size=os.environ.get("VANNA_POSTER_SIZE", "4K"))
        paste_logo(path, founder)
        try:
            v = R.brain_vision(
                "Image 1 is the approved slide; image 2 is its fixed version. Check: (a) each of these fixes "
                "is applied: " + " | ".join(fixes) + "; (b) nothing else changed: same layout, type, colours, "
                "strings and numbers; (c) no word cut off, misspelled or invented; (d) the logo appears once, "
                'top-left. Return JSON: {"score": int (0-10), "differences": [str] (each a concrete fix), '
                '"verdict": "SHIP"|"REVISE"|"REJECT"}',
                [current, path], agent=AGENT_POSTER, role="reasoning", temperature=0.0, max_output_tokens=2048,
                system="You are the visual agent's judge. Be exact and brief.")
        except Exception as exc:                    # noqa: BLE001 — an unjudged image does not ship
            v = {"score": 0, "differences": ["judge failed: " + str(exc)[:120]], "verdict": "UNJUDGED"}
        after = _words(path)
        slips = sorted(after - before - allowed)
        lost = sorted(before - after - allowed)
        if slips:
            v["verdict"], v["score"] = "REVISE", min(int(v.get("score") or 0), 5)
            v.setdefault("differences", []).insert(
                0, "Text changed that no fix asked for: " + ", ".join(repr(s) for s in slips[:10])
                + (" — the approved slide reads: " + ", ".join(repr(s) for s in lost[:10]) if lost else "")
                + ". Copy every unchanged string from the approved slide letter for letter.")
        v["slips"], v["lost"] = slips, lost
        history.append({"path": str(path), **v})
        if not slips and (str(v.get("verdict")).upper() == "SHIP" or int(v.get("score") or 0) >= 9):
            break
        correction = "\n".join("- " + str(x) for x in (v.get("differences") or [])[:8])
    best = max(history, key=lambda h: (not h.get("slips"), str(h.get("verdict")).upper() == "SHIP",
                                       int(h.get("score") or 0)))
    final = out_dir / f"{name}.png"
    final.write_bytes(Path(best["path"]).read_bytes())
    (out_dir / (name + ".fixes.json")).write_text(json.dumps(
        {"from": str(current), "fixes": fixes, "keep": keep,
         "attempts": [{k2: h.get(k2) for k2 in ("path", "score", "verdict", "differences", "slips", "lost")}
                      for h in history]},
        ensure_ascii=False, indent=1), encoding="utf-8")
    return {"name": name, "final": str(final), "attempts": history, "director": d}


def run(query: str, hook: str = "", body: str = "", *, name: str, out_dir: Path,
        run_id: Optional[str] = None) -> dict[str, Any]:
    d = direct(query, hook, body, run_id=run_id)
    res = make(d, name, out_dir)
    _remember(str(d.get("base")))
    res["brief"] = brief_text(d)
    res["director"] = d
    try:
        res["caption"] = caption(d, query, run_id=run_id)
    except Exception as exc:                        # noqa: BLE001 — the poster stands without it
        res["caption"] = {"error": str(exc)[:200]}
    (Path(out_dir) / (name + ".post.json")).write_text(json.dumps(
        {"caption": res["caption"], "concepts": d.get("concepts"), "chosen": d.get("chosen"),
         "why_chosen": d.get("why_chosen"), "base": d.get("base")}, ensure_ascii=False, indent=1), encoding="utf-8")
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
