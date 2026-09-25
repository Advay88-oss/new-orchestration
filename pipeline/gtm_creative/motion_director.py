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

AGENT = "A07_creative_director"          # poster brief: A07 owns creative
MOTION_AGENT = "A09_video_production"    # motion plan: A09 owns the clip

GUARDRAILS = (
    "The FIRST frame is the empty Vanna ground; the LAST frame is the finished "
    "poster. The clip is that poster building itself.\n"
    "CAMERA: completely locked off — no pan, tilt, zoom, dolly, orbit, drift, "
    "shake, parallax or depth of field. Everything moves in the flat plane.\n"
    "TEXT: every word, when it appears, is sharp, correctly spelled and "
    "identical to the last frame; never scramble, melt or morph letters. Add "
    "no text, icons, objects, people, coins or scenes that are not in the last "
    "frame. The ground stays Vanna's dark violet-and-magenta throughout."
)


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


COMPETITORS = ("aave", "compound", "euler", "maker", "sky protocol", "spark",
               "kamino", "solend", "venus", "radiant", "fluid", "silo")


def _brief_faults(out: dict) -> list[str]:
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
    labels = out.get("labels") or []
    if len(labels) > 6:
        faults.append(str(len(labels)) + " labels; at most 6")
    blob = " ".join(str(v) for v in out.values()).lower()
    named = [c for c in COMPETITORS if re.search(r"\b" + re.escape(c) + r"\b", blob)]
    if named:
        faults.append("names a competitor (" + ", ".join(named) + "); say 'pooled lending'")
    # The image model draws markdown literally: a "**" in the footer became
    # two printed asterisks on a poster.
    if any(m in str(v) for v in out.values() for m in ("**", "__", "`")):
        faults.append("contains markdown (** __ `); write plain text, emphasis is the gradient word")
    diag = str(out.get("diagram") or "").lower()
    if any(w in diag for w in ("isometric", " 3d", "3-d", "perspective")):
        faults.append("diagram is isometric/3D; keep every element flat and face-on so Veo "
                      "does not tilt the camera")
    drawn = [w for w in ("coin", "token logo", "bitcoin", "ethereum", "currency", "cyan", "teal")
             if w in diag]
    if drawn:
        faults.append("diagram asks for " + ", ".join(drawn) + "; never draw coins, token "
                      "logos or currency, and keep to violet and magenta")
    if "─" in str(out.get("diagram") or "") or "-->" in str(out.get("diagram") or ""):
        faults.append("diagram is a text flowchart; describe it visually")
    return faults


def poster_brief(query: str, hook: str = "", body: str = "", *,
                 run_id: Optional[str] = None) -> dict[str, Any]:
    """The brief the image model draws from. Raises on model failure."""
    from pipeline.gtm_os import agent_runtime as R
    from pipeline.gtm_os.vanna_knowledge import prompt_block

    approved = _approved_posters()
    fixes = _corrections()
    record = ""
    if approved or fixes:
        record = "FOUNDER'S RECORD — learn from it:\n"
        if approved:
            record += "Posters the founder APPROVED (the level and the kind of idea):\n"
            record += "\n".join("  - " + r["brief"] + (" — " + r["note"] if r.get("note") else "")
                                for r in approved) + "\n"
        if fixes:
            record += "Corrections from revisions and kills:\n"
            record += "\n".join("  - " + f for f in fixes) + "\n"

    system = (
        "You are Vanna's Motion Director, briefing the poster that will be "
        "drawn and then animated. Vanna is composable credit infrastructure "
        "on Stellar Soroban TESTNET. Write a brief an image model can draw "
        "from: ONE idea, as a diagram of glass cards, icons and arrows.\n"
        "First choose the FORMAT the query is asking for — do not force every "
        "poster into the same shape:\n"
        "  announcement — something is live, launched or open to try (e.g. "
        "'testnet is live', 'check it now'): one bold message, 2-4 glass "
        "cards of what the reader can do or test right now, and a clear call "
        "to action. No problem-versus-Vanna comparison.\n"
        "  explainer / hot take — how something works or a belief to "
        "challenge: the problem side against Vanna's answer.\n"
        "  question — a discussion prompt: the question and 2-4 answer cards.\n"
        "  metric — one true figure is the whole point.\n"
        "Never draw coins, token logos, currency symbols or any protocol's "
        "logo. Keep to Vanna's violet and magenta; no cyan or teal.\n"
        "The poster will be ANIMATED by Veo, building itself element by "
        "element, so design it to build cleanly: headline and subtitle on "
        "top, then 2-4 large, clearly separated glass cards, each holding one "
        "simple diagram, short plain-text labels, a footer. Distinct elements "
        "with space between them animate well; crowded, overlapping or "
        "text-dense layouts come out garbled. Keep everything FLAT and "
        "face-on: 2D glass cards, flat icons, straight arrows. No isometric "
        "or 3D objects (chips, cubes, platforms seen at an angle) — Veo turns "
        "them into a moving 3D scene and the camera tilts. "
        "Every figure must be true of Vanna (1.10x liquidation floor, "
        "0.00014 XLM gas, ~320ms indexing) — invent none. Other protocols "
        "(Blend, Aquarius, Soroswap) appear as plain text names.\n"
        "Rules:\n"
        "- Cover EVERY subject the founder's query names. If it asks about "
        "two things (e.g. health factor AND liquidity), the idea, both sides "
        "and the diagram show both.\n"
        "- Headline in sentence case, under 9 words. Subtitle under 14 words.\n"
        "- Never name a competitor (Aave, Compound, Euler and the like); say "
        "'pooled lending' instead.\n"
        "- At most 6 diagram labels, each 1-4 words; fewer is better — every "
        "word is drawn, and every word is a chance to misspell.\n"
        "- Describe the diagram visually (shapes, cards, what breaks, what "
        "flows), not as a text flowchart.\n"
        "Return strict JSON.")
    prompt = (
        prompt_block((query or hook)[:300], excerpts=4) + "\n\n----\n\n"
        + (record + "\n" if record else "")
        + "THE FOUNDER'S QUERY: " + " ".join(str(query).split())[:800] + "\n"
        + ("THE POST — hook: " + hook[:300] + "\nbody: " + " ".join(body.split())[:1200] + "\n"
           if hook or body else "")
        + '\nReturn JSON: {"format": "announcement"|"explainer"|"question"|"metric", '
        '"idea": str, "headline": str (under 9 words), '
        '"gradient_word": str (1-2 words from the headline), "subtitle": str '
        '(under 14 words), "problem_side": str, "vanna_side": str, '
        '"diagram": str (what is drawn and how the two sides contrast), '
        '"labels": [str] (every word that appears on the diagram, 1-4 words '
        'each), "footer": str (bold lead + testnet caveat), "why": str}')
    out = R.brain_json(prompt, agent=AGENT, role="director", system=system,
                       temperature=0.5, max_output_tokens=8192, run_id=run_id)
    # The rules are checked, not only stated: in testing, both Flash and Pro
    # broke one (a competitor named, eight labels, a 16-word subtitle). A
    # broken brief is sent back once with exactly what to fix.
    faults = _brief_faults(out)
    if faults:
        out = R.brain_json(prompt + "\n\nYOUR PREVIOUS BRIEF BROKE THESE RULES — fix "
                           "every one and return the whole JSON again:\n- "
                           + "\n- ".join(faults),
                           agent=AGENT, role="director", system=system,
                           temperature=0.3, max_output_tokens=8192, run_id=run_id)
    sides = "".join(
        "\n" + label + ": " + str(out.get(k)) for k, label in
        (("problem_side", "Problem side"), ("vanna_side", "Vanna side"))
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
    return {"brief": text, "raw": out}


def motion_plan(poster: str | Path, brief: str, *,
                run_id: Optional[str] = None) -> dict[str, Any]:
    """The beat-by-beat build for THIS poster, written by looking at it."""
    from pipeline.gtm_os import agent_runtime as R

    try:
        from pipeline.gtm_creative.veo_video import learned_block
        learned = learned_block()
    except Exception:                               # noqa: BLE001 — boundary
        learned = ""
    system = (
        "You are Vanna's Motion Director. You direct Veo 3.1, which animates "
        "a poster building itself from an empty ground in 8 seconds with a "
        "locked camera. You look at the finished poster and write the build "
        "for ITS elements — not a template. Motion must explain the idea: the "
        "problem side should visibly fail or strain, Vanna's side should "
        "settle calmly. Keep beats few and clear; big simultaneous changes "
        "make Veo garble text, so text should arrive in its own beat and "
        "never change after. Every text element appears in its FINAL "
        "position and size — never slide, grow or move text. Describe every "
        "element as flat and face-on; never use the words isometric, 3D, "
        "perspective or depth, which make Veo tilt the camera. Return strict "
        "JSON.")
    prompt = (
        (learned + "\n\n" if learned else "")
        + "THE POSTER'S BRIEF:\n" + brief[:1500] + "\n\n"
        "The attached image is the finished poster (the clip's last frame).\n"
        'Return JSON: {"beats": [{"t": str (e.g. "0-1.5s"), "action": str}] '
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
    return {"plan": plan, "raw": out,
            "prompt": GUARDRAILS + "\n\n" + plan + ("\n\n" + learned if learned else "")}
