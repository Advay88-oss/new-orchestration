"""Reading the harvest, instead of listing it.

A01 brings back ~26 signals a cycle and records source, headline, publisher,
entities and two timestamps. Every one of those is a *fact about the fetch*,
not about the market. `market_category` is set deterministically and came back
`LENDING` on "Best Decentralized Crypto Exchanges in September 2026", which is
what a default looks like when it is presented as a finding.

So the Scraped Intelligence view could only ever show what it showed: a list
of headlines with logos beside them. The founder's note was exact — it works,
and it is not useful, because nothing in the pipeline had *read* any of it.

This is the pass that reads it. One model call over the whole harvest, because
the interesting question is not per-headline, it is what twenty-six headlines
say together. It returns two things:

  **A reading per signal.** What the item actually is in one line, and
  whether Vanna can say anything architectural about it — DIRECT, ADJACENT or
  NONE. NONE is a real answer and it is expected to be the most common one; a
  scraper that finds everything relevant has found nothing.

  **A landscape.** The themes across the harvest, what is moving, and what the
  market is conspicuously quiet about. That is the honest answer to "what is
  going on" for the days when nothing is actionable — which the founder asked
  for explicitly, and which no amount of per-signal detail provides.

  **What Vanna can do about it.** Per relevant signal, one concrete move; and
  across the harvest, two to four strategies, each citing the signals behind
  it. The founder's note: the Scraped Intelligence view showed references and
  never said what they were *for*. A strategy is a business move — position
  against, educate on, watch, open a conversation with a confirmed partner —
  and it must cite its evidence, so the Vanna References view can link every
  one back to the post, doc or article it came from.

It still writes no content. Post copy and formats are `idea_proposer`'s job;
conflating "here is what to do" with "here is what to post" is how the Ideas
Panel became a list of drafts nobody asked for.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable, Optional

AGENT = "A02_market_analyst"

# The whole harvest, not a sample. Clustering twenty-six items is the point;
# ranking them and reading the top five reproduces the problem this replaces.
MAX_SIGNALS = 40

SYSTEM = (
    "You are Vanna's market analyst. Vanna is composable credit / unified "
    "margin infrastructure on Stellar Soroban TESTNET: per-borrower "
    "SmartAccount sandboxes, credit that stays composable across venues, a "
    "health factor with a 1.10x liquidation floor, deterministic "
    "liquidation.\n\n"

    "You are given everything one scrape brought back. Your job is to READ "
    "it, not to summarise it and not to write copy. Two outputs.\n\n"

    "1. A READING PER SIGNAL.\n"
    "   what_it_is   — one sentence, plain, what actually happened or what "
    "the piece actually argues. If the headline is a listicle, an SEO "
    "buyer's guide or a price-prediction piece, say so plainly; that IS the "
    "reading.\n"
    "   relevance    — DIRECT (touches Vanna's own mechanism: margin, "
    "liquidation, collateral, credit, isolation, oracles, account "
    "abstraction, Soroban/Stellar), ADJACENT (same market, different layer — "
    "Vanna has context but no mechanism claim), NONE (nothing Vanna can say "
    "that would not be a generic take).\n"
    "   why          — one sentence defending that grade. For NONE, say what "
    "would have had to be true for it to matter.\n"
    "   vanna_move   — for DIRECT and ADJACENT only: ONE concrete thing Vanna "
    "can do in response, in one sentence starting with a verb (explain, "
    "position against, watch, benchmark, open a conversation with...). Empty "
    "string for NONE.\n\n"
    "   MOST SIGNALS ARE NONE OR ADJACENT. A harvest where everything is "
    "DIRECT is not a good harvest, it is a dishonest reading, and it makes "
    "the grade worthless. Expect roughly two to five DIRECT out of twenty.\n\n"

    "2. A LANDSCAPE across the whole harvest.\n"
    "   summary      — 2-4 sentences: what is going on in this market right "
    "now, as one picture. Written for a founder who has thirty seconds and "
    "has not read any of the headlines.\n"
    "   themes       — 2-5 things that several signals point at together. "
    "Each names the signals that evidence it. A theme supported by one "
    "signal is not a theme; leave it out.\n"
    "   quiet_on     — what is conspicuously ABSENT given what Vanna does: "
    "subjects you would expect this market to be discussing and it is not. "
    "This is often the most useful line on the page.\n"
    "   for_vanna    — what this landscape means for Vanna specifically, in "
    "2-3 sentences. If the honest answer is 'nothing this cycle', write "
    "that; it is a legitimate reading and far more useful than a "
    "manufactured implication.\n"
    "   strategies   — 2-4 moves Vanna can make given THIS harvest. Each: "
    "title (under 8 words), move (what to do, 1-2 sentences), rationale (why "
    "now, 1 sentence, from the signals), signal_ids (the signals that "
    "evidence it — at least one; a strategy with no evidence is an opinion), "
    "horizon ('this week' or 'this month'). If the harvest supports fewer "
    "than two, return fewer; do not pad.\n\n"

    "Rules:\n"
    "- Cite only what is in the signals. Invent no figure, no date, no "
    "company, no event. If a headline implies a number you cannot see, do "
    "not state the number.\n"
    "- Strategies and moves are business moves, not content. No post copy, "
    "no hooks, no formats. Another agent writes content and you will "
    "contaminate it.\n"
    "- Name a partner relationship only if it is on the CONFIRMED PARTNERS "
    "list given with the signals. Any other protocol is something Vanna can "
    "watch, compare against or explain — never something it 'integrates "
    "with' or 'partners with'.\n"
    "- Never imply Vanna is on mainnet. Never call a competitor inferior.\n"
    "- Plain language. No hype vocabulary.\n\n"
    "Return strict JSON."
)

SCHEMA_HINT = (
    '{"signals": [{"signal_id": str, "what_it_is": str, '
    '"relevance": "DIRECT"|"ADJACENT"|"NONE", "why": str, '
    '"vanna_move": str}], '
    '"landscape": {"summary": str, '
    '"themes": [{"theme": str, "what_is_happening": str, '
    '"signal_ids": [str], "matters_to_vanna": bool}], '
    '"quiet_on": [str], "for_vanna": str, '
    '"strategies": [{"title": str, "move": str, "rationale": str, '
    '"signal_ids": [str], "horizon": "this week"|"this month"}]}}'
)


def _partners_block() -> str:
    """The confirmed partner list, so a strategy cannot invent a relationship."""
    try:
        from pipeline.gtm_os.vanna_knowledge import PARTNERS
    except Exception:                               # noqa: BLE001 — boundary
        return ""
    return ("CONFIRMED PARTNERS (the whole list):\n"
            + "\n".join("  - " + n + " (" + r + ")" for n, r in PARTNERS.items()))


def _rows(signals: Iterable[Any]) -> list[dict[str, str]]:
    """Signals as the flat records the prompt lists, from objects or dicts."""
    out: list[dict[str, str]] = []
    for s in signals:
        get = (s.get if isinstance(s, dict) else lambda k, d=None: getattr(s, k, d))
        sid = str(get("signal_id", "") or "")
        if not sid:
            continue
        ents = get("entities", None) or get("entities_involved", None) or []
        out.append({
            "signal_id": sid,
            "headline": str(get("headline", "") or "")[:220],
            "publisher": str(get("source_root", "") or get("source_type", "") or ""),
            "entities": ", ".join(str(e) for e in ents if e != "(unattributed)")[:120],
            "observed_at": str(get("observed_at", "") or "")[:40],
        })
    return out[:MAX_SIGNALS]


def analyse(signals: Iterable[Any], run_id: Optional[str] = None) -> dict[str, Any]:
    """Read one cycle's harvest. Never raises — a failed reading is recorded.

    The cycle must not die because the market could not be summarised. A
    failure here returns an empty reading and records the stage as degraded,
    which is what the view then shows: no analysis, and the reason.
    """
    from pipeline.gtm_os import agent_runtime as R

    rows = _rows(signals)
    if not rows:
        R.record_stage(AGENT, "skipped", "no signals to read", run_id=run_id)
        return {"signals": [], "landscape": None, "error": "no signals"}

    listing = "\n".join(
        "- " + r["signal_id"] + " | " + r["headline"]
        + " | publisher: " + (r["publisher"] or "unknown")
        + (" | names: " + r["entities"] if r["entities"] else "")
        + (" | dated: " + r["observed_at"] if r["observed_at"] else "")
        for r in rows)

    prompt = (
        _partners_block() + "\n\n"
        "ONE SCRAPE, " + str(len(rows)) + " SIGNALS\n\n" + listing + "\n\n"
        "Return a reading for every signal_id above, plus one landscape. "
        "JSON exactly:\n" + SCHEMA_HINT
    )

    # One retry on malformed JSON. Two cycles on 2026-09-24 lost the whole
    # reading to a single bad character at char ~12,600 — well inside the
    # token budget, so it was a slip, not truncation, and worth asking again.
    try:
        try:
            out = R.brain_json(prompt, agent=AGENT, system=SYSTEM,
                               role="reasoning", temperature=0.25,
                               max_output_tokens=12288)
        except R.BrainError as first:
            R.record_stage(AGENT, "degraded",
                           "market reading returned malformed JSON, retrying: "
                           + str(first)[:160], run_id=run_id)
            out = R.brain_json(
                prompt + "\n\nReturn ONLY the JSON object. No prose, no "
                         "comments, no trailing commas. Escape every double "
                         "quote inside a string.",
                agent=AGENT, system=SYSTEM, role="reasoning",
                temperature=0.1, max_output_tokens=12288)
    except Exception as exc:                        # noqa: BLE001 — boundary
        R.record_stage(AGENT, "degraded",
                       "market reading failed: " + str(exc)[:180],
                       run_id=run_id)
        return {"signals": [], "landscape": None, "error": str(exc)[:300]}

    read = [r for r in (out.get("signals") or []) if isinstance(r, dict)]
    land = out.get("landscape") if isinstance(out.get("landscape"), dict) else None

    # A reading for a signal that was not in the harvest is a hallucinated
    # row, and it would show in the view beside real ones.
    known = {r["signal_id"] for r in rows}
    read = [r for r in read if str(r.get("signal_id")) in known]

    graded = {}
    for r in read:
        g = str(r.get("relevance", "")).upper()
        r["relevance"] = g if g in ("DIRECT", "ADJACENT", "NONE") else "NONE"
        graded[r["relevance"]] = graded.get(r["relevance"], 0) + 1
        # A move for a signal graded NONE contradicts its own grade.
        r["vanna_move"] = ("" if r["relevance"] == "NONE"
                           else str(r.get("vanna_move") or "").strip())

    # A strategy must cite signals that were actually harvested. Unknown ids
    # are dropped, and a strategy left with no evidence is dropped with them:
    # the References view links every strategy back to its sources, and one
    # with none would be an opinion presented as a reading.
    if land:
        kept = []
        for st in land.get("strategies") or []:
            if not isinstance(st, dict):
                continue
            ids = [str(i) for i in (st.get("signal_ids") or []) if str(i) in known]
            if ids and str(st.get("move") or "").strip():
                kept.append({**st, "signal_ids": ids})
        land["strategies"] = kept[:4]

    result = {
        "signals": read,
        "landscape": land,
        "read": len(read),
        "of": len(rows),
        "grades": graded,
    }
    _write(result, run_id)

    detail = ("read " + str(len(read)) + "/" + str(len(rows)) + " signals"
              + (" | " + ", ".join(k + ":" + str(v) for k, v in graded.items())
                 if graded else "")
              + (" | landscape written" if land else " | NO landscape"))
    R.record_stage(AGENT, "ok" if (read and land) else "degraded", detail,
                   run_id=run_id)
    if land:
        R.record_decision(AGENT, "landscape", {
            "summary": str(land.get("summary", ""))[:600],
            "themes": [str(t.get("theme", "")) for t in (land.get("themes") or [])
                       if isinstance(t, dict)][:5],
            "quiet_on": [str(q) for q in (land.get("quiet_on") or [])][:5],
            "strategies": [str(st.get("title", "")) for st in land.get("strategies") or []],
        }, run_id=run_id)
    return result


def _write(result: dict[str, Any], run_id: Optional[str]) -> None:
    """Beside harvest.json, so the view can read one run's facts and reading."""
    from pipeline.gtm_os import agent_runtime as R

    rid = run_id or R.current_run()
    if not rid:
        return
    try:
        d = Path(R.RUNS_DIR) / rid
        d.mkdir(parents=True, exist_ok=True)
        (d / "analysis.json").write_text(
            json.dumps({"run_id": rid, **result}, indent=2, default=str),
            encoding="utf-8")
    except Exception:                               # noqa: BLE001 — boundary
        pass
