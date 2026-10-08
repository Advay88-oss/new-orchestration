"""The strategists compete; an independent judge picks.

The spec (ARCHITECTURE.md, CLAUDE.md) has one strategist per narrative arc,
working in parallel and arguing rather than converging, and an editorial
judge that scores each out of 100, ships the best at 70 or more and rejects
by default. The Python cycle used to run one strategist that picked its own
arc. Now:

    compete(make, signal, arcs)   one strategy per arc, in parallel
    judge(signal, entries)        scores out of 100 with reasons; the judge
                                  is a separate model call that never wrote
                                  any of them (agent A15_creative_judge,
                                  sub-step "editorial")

The arcs are the tenant's own arguments from its brand profile
(profile["arguments"]), so nothing here is Vanna-specific. A tenant with
fewer than two arguments gets a single strategist, as before.

A founder directive is never killed for scoring under the bar — the founder
already decided the subject — the judge only picks the best angle on it.
"""
from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Callable, Optional

AGENT = "A15_creative_judge"
MIN_SCORE = int(os.environ.get("VANNA_EDITORIAL_MIN", "70"))
MAX_ARCS = 3

RUBRIC = (
    "Score each strategy out of 100. Your default is rejection: a strategy has to earn its score.\n"
    "  relevance to the signal          25  (is the post about what the signal is about?)\n"
    "  a differentiated wedge           25  (says something only this company can say)\n"
    "  checkable proof                  20  (specific claims a fact checker can verify; no invented numbers)\n"
    "  audience fit                     15  (the named audience would care)\n"
    "  one clear idea                   15  (one arc, one argument, no blending)\n"
    "70 or more is publishable. Below 70 is not."
)


def arcs_for_tenant() -> list[dict]:
    from pipeline.brand_brain import context as C
    try:
        args = C.profile().get("arguments") or []
    except Exception:                               # noqa: BLE001 — no profile: one strategist
        return []
    return [a for a in args if isinstance(a, dict) and a.get("name")][:MAX_ARCS]


def compete(make: Callable[[Optional[dict]], Any], arcs: list[dict]) -> list[tuple[Optional[dict], Any]]:
    """Run `make(arc)` for every arc at once. With fewer than two arcs, one
    strategist with no arc."""
    if len(arcs) < 2 or os.environ.get("VANNA_SINGLE_STRATEGIST") == "1":
        return [(None, make(None))]
    with ThreadPoolExecutor(max_workers=len(arcs), thread_name_prefix="strategist") as pool:
        futures = [(a, pool.submit(make, a)) for a in arcs]
        out = []
        for arc, fut in futures:
            try:
                out.append((arc, fut.result()))
            except Exception as exc:                # noqa: BLE001 — one arc fails alone
                out.append((arc, exc))
        return out


def _brief(strategy: Any) -> str:
    g = lambda k: str(getattr(strategy, k, "") or "")[:500]   # noqa: E731
    proof = "; ".join(str(p)[:200] for p in (getattr(strategy, "proof", None) or [])[:6])
    return ("pillar: " + g("narrative_pillar") + "\naudience: " + g("audience_segment")
            + "\nproblem: " + g("problem") + "\nopportunity: " + g("strategic_opportunity")
            + "\npositioning: " + g("positioning") + "\nproof: " + proof)


def judge(signal: Any, entries: list[tuple[Optional[dict], Any]], *, run_id: Optional[str] = None) -> dict:
    """Score the ACTION strategies. Returns {"scores": [{i, arc, score, why}],
    "winner": i | None, "ok": bool}. A failed judge returns ok False with no
    winner; the caller decides (it does not pick at random)."""
    from pipeline.gtm_os import agent_runtime as R
    listing = []
    for i, (arc, s) in enumerate(entries):
        listing.append("STRATEGY " + str(i) + " (arc: " + str((arc or {}).get("name") or "free") + ")\n"
                       + _brief(s))
    prompt = ("SIGNAL: " + str(getattr(signal, "headline", ""))[:300] + "\n"
              + str(getattr(signal, "description", ""))[:1200] + "\n\n"
              + RUBRIC + "\n\n" + "\n\n".join(listing)
              + '\n\nReturn JSON: {"scores": [{"i": int, "score": int, "why": str (one sentence)}]}')
    try:
        out = R.brain_json(prompt, agent=AGENT, role="reasoning", temperature=0.0, max_output_tokens=2048,
                           system="You are the editorial judge. You did not write these. Be strict.",
                           run_id=run_id)
    except Exception as exc:                        # noqa: BLE001 — reported to the caller
        return {"ok": False, "error": str(exc)[:200], "scores": [], "winner": None}
    scores = []
    for r in (out.get("scores") or []):
        try:
            i = int(r.get("i"))
        except (TypeError, ValueError):
            continue
        if 0 <= i < len(entries):
            arc = entries[i][0] or {}
            scores.append({"i": i, "arc": arc.get("name") or "free",
                           "score": max(0, min(100, int(r.get("score") or 0))),
                           "why": str(r.get("why") or "")[:240]})
    if not scores:
        return {"ok": False, "error": "the judge returned no scores", "scores": [], "winner": None}
    best = max(scores, key=lambda r: r["score"])
    return {"ok": True, "scores": sorted(scores, key=lambda r: -r["score"]), "winner": best["i"],
            "best_score": best["score"]}
