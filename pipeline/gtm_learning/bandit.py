"""The strategist's contextual bandit (the architecture's fast loop).

Arms are strategy choices — the narrative pillar, the hook type, the post
length. Context is the platform, weekday or weekend, whether the brand has
news, and what the last posts used. Each (arm, option) has a Beta posterior
over the reward events (`rewards.py`); a context's posterior is that global
record, counted at half weight, as a prior (the hierarchical model the
architecture describes), plus the events seen in that context — so a new
context starts from what is known overall and becomes its own as data comes.

Per run:
  * ~15% of choices explore: a uniformly random option, so the loop never
    settles on one format for good;
  * otherwise Thompson sampling picks the option with the highest draw;
  * an option used by both of the last two runs is passed over (repetition);
  * a founder LOCK overrides all of it — the architecture's "enterprise can
    lock an arm or pillar".

The recommendation is guidance to A03 and A06, not a constraint on the
subject: the reviewer and the founder stay the hard gates, and the arm that
is credited afterwards is the one the run actually shipped.

    python -m pipeline.gtm_learning.bandit            # overview
"""
from __future__ import annotations

import json
import random
from typing import Any, Optional

EXPLORE = 0.15
# This process's current run's recommendation (one run per process), set by
# the cycle after A02 and read by A03 and A06 when they build their prompts.
CURRENT: dict[str, dict[str, Any]] = {}
GLOBAL_WEIGHT = 0.5
HOOK_TYPES = ("question", "contrarian", "data", "story", "statement")
LENGTHS = ("short", "medium", "long")


def _brain():
    from pipeline.brand_brain.context import brain
    return brain()


def options() -> dict[str, list[str]]:
    from pipeline.brand_brain import context as C
    return {"pillar": list(C.pillars()), "hook_type": list(HOOK_TYPES), "length": list(LENGTHS)}


def _ctx_key(ctx: dict) -> str:
    return str(ctx.get("day_type", "")) + "|" + ("news" if ctx.get("whats_new") else "quiet")


def posteriors(evs: Optional[list[dict]] = None) -> dict[str, dict[str, dict[str, Any]]]:
    """{dimension: {option: {alpha, beta, n, mean, by_context: {key: {...}}}}}"""
    from pipeline.gtm_learning import rewards
    evs = rewards.events() if evs is None else evs
    out: dict[str, dict[str, dict[str, Any]]] = {}
    for e in evs:
        r = float(e["total"])
        key = _ctx_key(e["context"])
        for dim, opt in e["arms"].items():
            p = out.setdefault(dim, {}).setdefault(opt, {"alpha": 1.0, "beta": 1.0, "n": 0, "by_context": {}})
            p["alpha"] += r
            p["beta"] += 1 - r
            p["n"] += 1
            c = p["by_context"].setdefault(key, {"r": 0.0, "n": 0})
            c["r"] += r
            c["n"] += 1
    for dim in out.values():
        for p in dim.values():
            p["mean"] = round(p["alpha"] / (p["alpha"] + p["beta"]), 3)
    return out


def _draw(p: Optional[dict], ctx_key: str, rng: random.Random) -> float:
    if not p:
        return rng.betavariate(1, 1)
    c = p["by_context"].get(ctx_key, {"r": 0.0, "n": 0})
    ga, gb = (p["alpha"] - 1) * GLOBAL_WEIGHT, (p["beta"] - 1) * GLOBAL_WEIGHT
    return rng.betavariate(1 + ga + c["r"], 1 + gb + (c["n"] - c["r"]))


def locks() -> dict[str, str]:
    try:
        return json.loads(_brain().meta("arm_locks") or "{}")
    except Exception:                               # noqa: BLE001 — no locks
        return {}


def set_lock(dim: str, option: Optional[str]) -> dict[str, str]:
    lk = locks()
    if option:
        lk[dim] = option
    else:
        lk.pop(dim, None)
    _brain().meta("arm_locks", json.dumps(lk))
    return lk


def recommend(context: dict, *, rng: Optional[random.Random] = None) -> dict[str, dict[str, Any]]:
    from pipeline.gtm_learning import rewards
    rng = rng or random.Random()
    evs = rewards.events()
    post = posteriors(evs)
    recent = [e["arms"] for e in evs[:2]]                  # newest first
    lk = locks()
    key = _ctx_key(context)
    rec: dict[str, dict[str, Any]] = {}
    for dim, opts in options().items():
        if not opts:
            continue
        if lk.get(dim) in opts:
            rec[dim] = {"choice": lk[dim], "why": "locked by the founder"}
            continue
        used_twice = {a.get(dim) for a in recent} if len(recent) == 2 and len({a.get(dim) for a in recent}) == 1 else set()
        pool = [o for o in opts if o not in used_twice] or opts
        if rng.random() < EXPLORE:
            rec[dim] = {"choice": rng.choice(pool), "why": "exploring (15% of choices)"}
            continue
        draws = {o: _draw(post.get(dim, {}).get(o), key, rng) for o in pool}
        best = max(draws, key=draws.get)
        p = post.get(dim, {}).get(best)
        rec[dim] = {"choice": best,
                    "why": ("best record in this context (" + str(p["mean"]) + " over " + str(p["n"]) + " runs)")
                    if p else "not tried yet"}
    return rec


def prompt_block(rec: dict[str, dict[str, Any]], *, for_agent: str) -> str:
    """The recommendation as guidance for A03 (pillar) or A06 (hook, length)."""
    if not rec:
        return ""
    lines = ["STRATEGY BANDIT — what the reward record suggests this run (guidance; the subject and the truth come first):"]
    if for_agent == "A03" and "pillar" in rec:
        r = rec["pillar"]
        lines.append("  - narrative pillar: " + r["choice"] + " — " + r["why"]
                     + (". Use it." if "locked" in r["why"] else ". Prefer it when it fits the subject."))
    if for_agent == "A06":
        for dim, label in (("hook_type", "hook type"), ("length", "length")):
            if dim in rec:
                r = rec[dim]
                lines.append("  - " + label + ": " + r["choice"] + " — " + r["why"]
                             + (". Use it." if "locked" in r["why"] else "."))
        lines.append("    (hook types: question = ends with a question; contrarian = challenges a belief; "
                     "data = leads with a true figure; story = a short narrative; statement = a plain claim. "
                     "Lengths: short < 400 characters, medium < 900, long beyond.)")
    return "\n".join(lines) if len(lines) > 1 else ""


def overview() -> dict[str, Any]:
    from pipeline.gtm_learning import rewards
    evs = rewards.events()
    post = posteriors(evs)
    opts = options()
    arms = {dim: [{"option": o, **{k: v for k, v in (post.get(dim, {}).get(o) or
                                                       {"alpha": 1, "beta": 1, "n": 0, "mean": 0.5}).items()
                                  if k != "by_context"}} for o in os]
            for dim, os in opts.items()}
    return {"ok": True, "arms": arms, "locks": locks(), "explore": EXPLORE,
            "events": evs[:40], "n_events": len(evs),
            "pairs": rewards.pairs(10), "n_pairs": len(rewards.pairs(10000))}


if __name__ == "__main__":
    import sys
    if sys.argv[1:2] == ["lock"] and len(sys.argv) >= 4:
        print(json.dumps({"ok": True, "locks": set_lock(sys.argv[2], " ".join(sys.argv[3:]))}))
    elif sys.argv[1:2] == ["unlock"] and len(sys.argv) >= 3:
        print(json.dumps({"ok": True, "locks": set_lock(sys.argv[2], None)}))
    else:
        print(json.dumps(overview(), default=str))
