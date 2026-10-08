"""The Motion Director — the agent that writes what the image and video
models are asked for.

On 2026-09-25 the poster brief ("contrast a fragile shared pool with Vanna's
isolated SmartAccount…") and the video's motion plan ("glow, then logo, then
headline, then cards, then diagram, then settle") were written by hand for
one video, and the founder liked the result. Hand-writing it does not scale
and does not learn, so this agent does both jobs for every run:

  **poster_brief(query, post)** — reads the founder's query and the post and
  writes the brief the image model draws from: the one idea, the headline
  and its gradient word, the problem-versus-Vanna contrast, the diagram and
  its labels. It is shown the briefs of posters the founder approved and
  the notes on ones sent back.

  **motion_plan(poster, brief)** — LOOKS at the finished poster and writes
  the beat-by-beat build for Veo 3.1: which element arrives first, how each
  card enters, what the diagram does as it assembles, how it settles —
  specific to this poster's own elements, not a template. It is shown the
  motion the founder approved in past clips ("the poster builds itself from
  the empty ground…") and the faults they flagged.

Reinforcement: both prompts carry the founder's record, which grows with
every Approve / Revise / Kill on the dashboard or Telegram (a decision on a
run is also a rating of its poster and its clip), so what the founder likes
is what the agent asks for next.

What stays fixed is only the guard rails Veo is held to on every clip —
locked camera, correct words, nothing added — because those are brand
safety, not taste.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

AGENT = "A14_motion_director"            # the poster brief and the motion plan
MOTION_AGENT = AGENT

GUARDRAILS = (
    "The FIRST frame is the empty {company} ground; the LAST frame is the finished "
    "poster with its words removed. The clip is that poster building itself.\n"
    "CAMERA: completely locked off — no pan, tilt, zoom, dolly, orbit, drift, "
    "shake, parallax or depth of field. Everything moves in the flat plane.\n"
    "LETTERS: draw none. Do not write, type, reveal, fade, wipe or morph any "
    "letter, word, numeral or logo. Words are composited afterwards from the "
    "real poster, and a letter you invent is how the last video spelled "
    "'actually deploy it' as 'acilly deppe it'. Animate shapes, cards, arrows, "
    "connectors and light only. Add no objects, people, coins or scenes that "
    "are not in the last frame. The ground stays the brand's ground colours."
)


# Variety. Every poster is held to the same bar and brand, but the layout
# and the choreography change: the last few used are unavailable, the rest
# are ordered by the founder's record, and the model picks what fits.
LAYOUTS = {
    "split_contrast": "logo at top, big headline, grey subtitle, then two large cards side by side — the problem on the left in red (cracked, draining or stuck at zero), {company} on the right in violet (holding or rising) — one arrow between. Each card holds a readable mechanism (a meter, a chart, a crack, a flow) with short labels, not an empty card. The cards take the MATERIAL of this post",
    "hub_spokes": "one central card for {company} with three cards around it, joined by straight lines, on the MATERIAL of this post",
    "step_flow": "three or four cards in a row joined by arrows, a numbered sequence, on the MATERIAL of this post",
    "stack_checklist": "one tall card of 3-5 rows with check marks, and a call-to-action pill below, on the MATERIAL of this post",
    "stat_hero": "one true figure set huge, two small supporting cards under it, on the MATERIAL of this post",
    "question_cards": "a question card with 2-4 answer cards beneath it and {company}'s short take, on the MATERIAL of this post",
    "before_after": "the same diagram twice, stacked: 'today' above, 'with {company}' below, on the MATERIAL of this post",
    "grid_features": "a 2x2 grid of cards, one capability each with a flat icon, on the MATERIAL of this post",
}
# Glassmorphism (2026-10-08). The founder's references are mostly glass, and
# every poster came out glass; a blanket ban (2026-10-06) went too far the
# other way. Glass is now one material among five — an accent, chosen when the
# idea is a layer, a container or a product surface, and then on ONE element
# only. The material rotation holds it back after use, so it never runs twice
# in a row.
GLASS_WHEN = ("glass_accent is for an idea about a layer, a container or a product surface — an isolated account sitting over a pool, one product card, a shield over a position — where one see-through panel says something. A comparison, a flow, a checklist or a figure reads better flat.")
MATERIALS = {
    "glass_accent": "matte opaque ground and cards, with exactly ONE frosted-glass panel — the {company} "
                    "card the idea is about — soft blur behind it and a fine bright edge; every other card, "
                    "label and arrow stays opaque and crisp",
    "solid": "opaque matte cards in the brand ink, a hairline border, no blur, no frost, nothing glowing through the fill",
    "editorial": "no panels. The headline carries the poster. One diagram is thin lines, marks and a single arrow on the open ground",
    "line": "a technical drawing: hairline rules, open shapes, small labels. No filled slabs, no blur, no glow",
    "print": "hard-edged ink blocks like a magazine spread. Flat colour, no glow, no transparency",
}
MOTION_STYLES = {
    "sequential_slide": "cards slide in one after another from below and settle",
    "draw_on": "outlines and connectors draw themselves on, then the cards fill",
    "scale_pop": "cards scale up from nothing with a soft settle, one at a time",
    "reveal_wipe": "each card is revealed by a soft left-to-right wipe",
    "pulse_flow": "cards fade in, then light pulses travel along the connectors",
}
_STATE = Path(__file__).resolve().parents[1] / "state"


def _recent(name: str) -> list[str]:
    try:
        return json.loads((_STATE / name).read_text(encoding="utf-8"))
    except Exception:                               # noqa: BLE001 — first run
        return []


def _remember(name: str, value: str, keep: int = 6) -> None:
    hist = [value] + [v for v in _recent(name) if v != value]
    (_STATE / name).write_text(json.dumps(hist[:keep]), encoding="utf-8")


def _options(catalogue: dict[str, str], recent_file: str, block_last: int,
             dim: str) -> list[tuple[str, str, str]]:
    """Open options, freshest-first by the founder's record: (id, how, record)."""
    blocked = set(_recent(recent_file)[:block_last])
    open_ids = [k for k in catalogue if k not in blocked] or list(catalogue)
    try:
        from pipeline.gtm_learning import preferences as P
        post = P.posteriors(dim)
        ranked = [k for k, _ in P.thompson_order(dim, open_ids)]
        return [(k, _fill(catalogue[k]), P.record_text(post[k]) if k in post else "not yet reviewed")
                for k in ranked]
    except Exception:                               # noqa: BLE001 — boundary
        return [(k, _fill(catalogue[k]), "") for k in open_ids]


def _rules_block() -> str:
    try:
        from pipeline.gtm_creative.creative_rules import block
        return block()
    except Exception:                               # noqa: BLE001 — boundary
        return ""


def _approved_posters(k: int = 3) -> list[dict]:
    try:
        from pipeline.gtm_learning.visual_exemplars import _rows
        rows = [r for r in _rows() if r.get("score", 0) >= 0.7 and r.get("brief")]
        rows.sort(key=lambda r: (r["score"], r["at"]), reverse=True)
        return rows[:k]
    except Exception:                               # noqa: BLE001 — boundary
        return []


def _corrections() -> list[str]:
    try:
        from pipeline.gtm_learning.preferences import corrections
        return [c["note"] for c in corrections(k=5)]
    except Exception:                               # noqa: BLE001 — boundary
        return []


def _competitors() -> list[str]:
    """The tenant's competitors (never its partners), lowercased."""
    from pipeline.brand_brain import context as C
    partners = {p.lower() for p in C.partners()}
    return [c.lower() for c in C.competitors() if c.lower() not in partners]


def _fill(text: str) -> str:
    """Company facts into a prompt written without them."""
    from pipeline.brand_brain import context as C
    figs = ", ".join(f["value"] + " " + f.get("meaning", "") for f in C.true_figures())
    skip = ("chain", "backer", "infrastructure")
    venues = ", ".join([n for n, r in C.partners().items()
                        if not any(s in r.lower() for s in skip)][:5])
    comps = ", ".join(c.title() for c in _competitors()[:3])
    avoid = C.avoid_colors()
    return (text.replace("{company_line}", C.company_line())
            .replace("{company}", C.company_name())
            .replace("{figures}", figs)
            .replace("{venues}", venues or "partner protocols")
            .replace("{competitor_examples}", comps or "any competitor")
            .replace("{competitor_rule}", str(C.profile().get("competitor_rule", "")))
            .replace("{palette_rule}", "Keep to the brand palette"
                     + ("; no " + " or ".join(avoid) if avoid else "") + "."))


def _brief_faults(out: dict, animated: bool = True) -> list[str]:
    """Rule breaks a model reliably makes in a brief, found in code."""
    import re
    faults = []
    head = str(out.get("headline") or "")
    if len(head.split()) > 9:
        faults.append("headline has " + str(len(head.split())) + " words; under 9")
    words = head.split()
    if len(words) >= 4 and sum(w[:1].isupper() for w in words) >= len(words) - 1:
        faults.append("headline is Title Case; use sentence case")
    if len(str(out.get("subtitle") or "").split()) > 14:
        faults.append("subtitle is over 14 words")
    from pipeline.gtm_creative.taste import jargon, overclaims
    said = head + " " + str(out.get("subtitle") or "") + " " + str(out.get("footer") or "")
    spec = jargon(said)
    if spec:
        faults.append("headline/subtitle uses protocol jargon (" + ", ".join(spec)
                      + "); say it the way a trader would, in plain words")
    promised = overclaims(said)
    if promised:
        faults.append("promises more than the facts (" + ", ".join(promised)
                      + "); say what the mechanism does, not that risk is gone")
    labels_l = [str(l).strip().lower() for l in (out.get("labels") or []) if str(l).strip()]
    twice = sorted({l for l in labels_l if labels_l.count(l) > 1})
    if twice:
        faults.append("the same label appears twice (" + ", ".join(twice)
                      + "); every label is printed once")
    labels = out.get("labels") or []
    if len(labels) > 6:
        faults.append(str(len(labels)) + " labels; at most 6")
    blob = " ".join(str(v) for v in out.values()).lower()
    named = [c for c in _competitors() if re.search(r"\b" + re.escape(c) + r"\b", blob)]
    if named:
        faults.append("names a competitor (" + ", ".join(named) + "); "
                      + _fill("{competitor_rule}"))
    # The image model draws markdown literally: a "**" in the footer became
    # two printed asterisks on a poster.
    if any(m in str(v) for v in out.values() for m in ("**", "__", "`")):
        faults.append("contains markdown (** __ `); write plain text, emphasis is the gradient word")
    diag = str(out.get("diagram") or "").lower()
    if animated and any(w in diag for w in ("isometric", " 3d", "3-d", "perspective")):
        faults.append("diagram is isometric/3D; keep every element flat and face-on so Veo "
                      "does not tilt the camera")
    from pipeline.brand_brain import context as C
    drawn = [w for w in ("coin", "token logo", "bitcoin", "ethereum", "currency", *C.avoid_colors())
             if w in diag]
    if drawn:
        faults.append("diagram asks for " + ", ".join(drawn) + "; never draw coins, token "
                      "logos or currency, and keep to the brand palette")
    if "─" in str(out.get("diagram") or "") or "-->" in str(out.get("diagram") or ""):
        faults.append("diagram is a text flowchart; describe it visually")
    material = str(out.get("material") or "")
    if material not in MATERIALS:
        faults.append("material must be one of: " + ", ".join(MATERIALS))
    blob_l = " ".join(str(v) for k, v in out.items() if k != "material").lower()
    glass_words = [w for w in ("glass", "frost", "blur", "translucent", "glassmorphism", "see-through")
                   if w in blob_l]
    if glass_words and material != "glass_accent":
        faults.append("the brief asks for " + ", ".join(glass_words) + " on the " + (material or "?")
                      + " material; glass belongs only to glass_accent, on one card")
    return faults


def poster_brief(query: str, hook: str = "", body: str = "", *,
                 run_id: Optional[str] = None, animated: bool = True) -> dict[str, Any]:
    """The brief the image model draws from. Raises on model failure."""
    from pipeline.gtm_os import agent_runtime as R
    from pipeline.brand_brain.context import facts_block as prompt_block

    from pipeline.gtm_creative import taste

    approved = _approved_posters()
    fixes = _corrections()
    sent_back = [p for p in taste.piles(approved=0, sent_back=4)["sent_back"] if p["brief"]]
    record = ""
    if approved or fixes or sent_back:
        record = "FOUNDER'S RECORD — learn from it:\n"
        if approved:
            record += "Posters the founder APPROVED (the level and the kind of idea):\n"
            record += "\n".join("  - " + r["brief"] + (" — " + r["note"] if r.get("note") else "")
                                for r in approved) + "\n"
        if sent_back:
            record += ("Posters the founder KILLED or sent back — do not make posters like "
                       "these:\n")
            record += "\n".join("  - (" + p["verdict"] + ") " + p["brief"] for p in sent_back) + "\n"
        if fixes:
            record += "Corrections from revisions and kills:\n"
            record += "\n".join("  - " + f for f in fixes) + "\n"
    taste_text = taste.rubric()
    if taste_text:
        record += "\n" + taste_text + "\n"

    if animated:
        shape = (
            "The poster will be ANIMATED by Veo, building itself element by "
            "element, so design it to build cleanly: headline and subtitle on "
            "top, then 2-4 large, clearly separated cards, each holding one "
            "simple diagram, short plain-text labels, a footer. Distinct elements "
            "with space between them animate well; crowded, overlapping or "
            "text-dense layouts come out garbled. Keep everything FLAT and "
            "face-on: flat icons, straight arrows. No isometric "
            "or 3D objects (chips, cubes, platforms seen at an angle) — Veo turns "
            "them into a moving 3D scene and the camera tilts. "
            "Cards are opaque unless the material is glass_accent, and then only "
            "the one card it names is glass. ")
    else:
        shape = (
            "The poster is a STILL (no video this run): headline and subtitle on "
            "top, then the cards the layout describes, short plain-text "
            "labels, a footer. Cards are opaque and flat unless the material is "
            "glass_accent, and then only the one card it names is glass. ")
    system = _fill(
        "You are {company}'s Motion Director, briefing the poster that will be "
        "drawn" + (" and then animated" if animated else "") + ". {company_line} "
        "Write a brief an image model can draw "
        "from: ONE idea, as a diagram of cards, icons and arrows, on ONE material.\n"
        "The diagram depicts the mechanism in the post body. Draw those names "
        "and those figures. Do not add Blend, Aquarius, a SmartAccount sandbox, "
        "or 1.10× unless the post body names them. A Solana post draws the "
        "Solana mechanism (a stock token, one margin account, a borrow), not "
        "the Stellar diagram.\n"
        "Pick the layout from LAYOUT FAMILIES below. Consecutive posts must "
        "not share a layout. Logo at top, one headline, one subtitle, then "
        "the cards that layout describes, then a footer.\n"
        "First choose the FORMAT the query is asking for:\n"
        "  announcement — something is live, launched or open to try (e.g. "
        "'testnet is live', 'check it now'): one bold message, 2-4 "
        "cards of what the reader can do or test right now, and a clear call "
        "to action. No problem-versus-{company} comparison.\n"
        "  explainer / hot take — how something works or a belief to "
        "challenge: the problem side against {company}'s answer.\n"
        "  question — a discussion prompt: the question and 2-4 answer cards.\n"
        "  metric — one true figure is the whole point.\n"
        "Never draw coins, token logos, currency symbols or any protocol's "
        "logo. {palette_rule}\n"
        + shape +
        "A figure is drawn only when the post body already states it. The "
        "profile figures ({figures}) belong to Stellar testnet posts. Invent none. "
        "Other protocols ({venues}) appear as plain text names.\n"
        "Rules:\n"
        "- Cover EVERY subject the founder's query names. If it asks about "
        "two things (e.g. health factor AND liquidity), the idea, both sides "
        "and the diagram show both.\n"
        "- Headline in sentence case, under 9 words. Subtitle under 14 words.\n"
        "- Never name a competitor ({competitor_examples} and the like). "
        "{competitor_rule}\n"
        "- At most 6 diagram labels, each 1-4 words; fewer is better — every "
        "word is drawn, and every word is a chance to misspell.\n"
        "- Describe the diagram visually (shapes, cards, what breaks, what "
        "flows), not as a text flowchart.\n"
        "Return strict JSON.")
    layouts = _options(LAYOUTS, "recent_layouts.json", 3, "poster_layout")
    materials = _options(MATERIALS, "recent_materials.json", 2, "poster_material")
    rules = _rules_block()
    prompt = (
        prompt_block((query or hook)[:300], excerpts=4) + "\n\n----\n\n"
        + (rules + "\n\n----\n\n" if rules else "")
        + (record + "\n" if record else "")
        + "LAYOUT FAMILIES open this run (the last three used are held back so "
          "consecutive posts look different; ordered by the founder's record — "
          "prefer higher when two fit):\n"
        + "\n".join("  " + k + ": " + how + (" [" + rec + "]" if rec else "")
                    for k, how, rec in layouts) + "\n\n"
        + "MATERIALS open this run (the last two used are held back). Pick the one that fits THIS "
          "idea. " + GLASS_WHEN + " Glass on everything is the look to avoid:\n"
        + "\n".join("  " + k + ": " + how for k, how, _rec in materials) + "\n\n"
        + "THE FOUNDER'S QUERY: " + " ".join(str(query).split())[:800] + "\n"
        + ("THE POST — hook: " + hook[:300] + "\nbody: " + " ".join(body.split())[:1200] + "\n"
           if hook or body else "")
        + '\nReturn JSON: {"format": "announcement"|"explainer"|"question"|"metric", '
        '"layout": str (one id from LAYOUT FAMILIES), '
        '"material": str (one id from MATERIALS), '
        '"idea": str, "headline": str (under 9 words), '
        '"gradient_word": str (1-2 words from the headline), "subtitle": str '
        '(under 14 words), "problem_side": str, "brand_side": str, '
        '"diagram": str (what is drawn, laid out as the chosen layout family), '
        '"labels": [str] (every word that appears on the diagram, 1-4 words '
        'each), "footer": str (bold lead + testnet caveat), "why": str}')
    out = R.brain_json(prompt, agent=AGENT, role="director", system=system,
                       temperature=0.5, max_output_tokens=8192, run_id=run_id)
    # The rules are checked, not only stated: in testing, both Flash and Pro
    # broke one (a competitor named, eight labels, a 16-word subtitle). A
    # broken brief is sent back once with exactly what to fix.
    faults = _brief_faults(out, animated)
    if faults:
        out = R.brain_json(prompt + "\n\nYOUR PREVIOUS BRIEF BROKE THESE RULES — fix "
                           "every one and return the whole JSON again:\n- "
                           + "\n- ".join(faults),
                           agent=AGENT, role="director", system=system,
                           temperature=0.3, max_output_tokens=8192, run_id=run_id)
    sides = "".join(
        "\n" + label + ": " + str(out.get(k)) for k, label in
        (("problem_side", "Problem side"), ("brand_side", _fill("{company} side")))
        if str(out.get(k) or "").strip() and str(out.get(k)).strip().lower() not in ("n/a", "none"))
    text = ("Format: " + str(out.get("format") or "explainer")
            + "\nHeadline: " + str(out.get("headline", "")) + " (gradient word: "
            + str(out.get("gradient_word", "")) + ")\nSubtitle: "
            + str(out.get("subtitle", "")) + "\nIdea: " + str(out.get("idea", ""))
            + sides
            + "\nDiagram: " + str(out.get("diagram", ""))
            + "\nLabels (exact words): " + ", ".join(str(x) for x in out.get("labels") or [])
            + "\nFooter: " + str(out.get("footer", "")))
    R.record_decision(AGENT, "poster_brief", {"brief": out, "learned_from": {
        "approved_posters": len(approved), "corrections": len(fixes)}}, run_id=run_id)
    open_ids = [k for k, _, _ in layouts]
    layout = str(out.get("layout") or "")
    if layout not in open_ids:
        layout = open_ids[0]
    _remember("recent_layouts.json", layout)
    open_materials = [k for k, _, _ in materials]
    material = str(out.get("material") or "")
    if material not in open_materials:
        material = open_materials[0]
    _remember("recent_materials.json", material)
    text = ("Material: " + material + " — " + MATERIALS[material] + "\n"
            + "Layout: " + layout + " — " + _fill(LAYOUTS[layout]) + "\n" + text)
    return {"brief": text, "raw": out, "layout": layout}


def motion_plan(poster: str | Path, brief: str, *,
                run_id: Optional[str] = None) -> dict[str, Any]:
    """The beat-by-beat build for THIS poster, written by looking at it."""
    from pipeline.gtm_os import agent_runtime as R

    try:
        from pipeline.gtm_creative.veo_video import learned_block
        learned = learned_block()
    except Exception:                               # noqa: BLE001 — boundary
        learned = ""
    system = _fill(
        "You are {company}'s Motion Director. You direct Veo 3.1, which animates "
        "a poster building itself from an empty ground in 8 seconds with a "
        "locked camera. You look at the finished poster and write the build "
        "for ITS elements — not a template. Motion must explain the idea: the "
        "problem side should visibly fail or strain, {company}'s side should "
        "settle calmly. Keep beats few and clear. Do not write a beat in which "
        "a headline, subtitle, label, footer or logo appears, fades, types or "
        "wipes: Veo invents the spelling when it draws letters. Words are "
        "painted on after the clip, from the poster. Your beats move shapes, "
        "cards, arrows, connectors and light only. Describe every "
        "element as flat and face-on; never use the words isometric, 3D, "
        "perspective or depth, which make Veo tilt the camera. "
        "Never say glass, frost, blur, translucent, or glassmorphism, and do not "
        "add a glass slab. Cards stay opaque. Return strict JSON.")
    styles = _options(MOTION_STYLES, "recent_motion_styles.json", 2, "motion_style")
    rules = _rules_block()
    prompt = (
        (rules + "\n\n----\n\n" if rules else "")
        + (learned + "\n\n" if learned else "")
        + "MOTION STYLES open this run (the last two used are held back; "
          "ordered by the founder's record):\n"
        + "\n".join("  " + k + ": " + how + (" [" + rec + "]" if rec else "")
                    for k, how, rec in styles) + "\n\n"
        + "THE POSTER'S BRIEF:\n" + brief[:1500] + "\n\n"
        "The attached image is the finished poster (the clip's last frame).\n"
        'Return JSON: {"motion_style": str (one id from MOTION STYLES), '
        '"beats": [{"t": str (e.g. "0-1.5s"), "action": str}] '
        '(5-7 beats covering 0-8s, naming this poster\'s actual elements), '
        '"text_rule": str (how text enters without morphing), '
        '"why": str (how the motion explains the idea, under 30 words)}')
    out = R.brain_vision(prompt, [Path(poster)], agent=MOTION_AGENT, system=system,
                         role="director", temperature=0.4, max_output_tokens=8192,
                         run_id=run_id)
    beats = [b for b in (out.get("beats") or []) if isinstance(b, dict)]
    plan = ("BUILD, beat by beat:\n"
            + "\n".join("  " + str(b.get("t", "")) + ": " + str(b.get("action", "")) for b in beats)
            + ("\nTEXT: " + str(out.get("text_rule")) if out.get("text_rule") else ""))
    R.record_decision(MOTION_AGENT, "motion_plan", {"beats": beats,
        "text_rule": out.get("text_rule"), "why": out.get("why"),
        "learned_from_clips": bool(learned)}, run_id=run_id)
    open_styles = [k for k, _, _ in styles]
    style = str(out.get("motion_style") or "")
    if style not in open_styles:
        style = open_styles[0]
    _remember("recent_motion_styles.json", style)
    plan = "MOTION STYLE: " + style + " — " + MOTION_STYLES[style] + "\n" + plan
    plan += ("\nSURFACE: no glassmorphism. Do not add frost, blur, a see-through fill, "
             "or a glowing glass border. Move only the opaque shapes already drawn."
             "\nLETTERS: do not draw, type, reveal, fade, wipe or morph any letter, "
             "word, numeral or logo. Those are composited afterwards. Animate "
             "shapes, cards, arrows, connectors and light only.")
    return {"plan": plan, "raw": out, "motion_style": style,
            "prompt": _fill(GUARDRAILS) + "\n\n" + plan + ("\n\n" + learned if learned else "")}
