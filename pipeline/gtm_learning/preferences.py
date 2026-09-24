"""What the founder's decisions teach — the part of the loop that was missing.

`feedback.py` records each approve / revise / kill with the run's features.
This reads that ledger and turns it into the two things agents can act on:

  **Choice weights** for the decisions the pipeline makes from a fixed set —
  A07's archetype, A03's pillar, A04's machine. Each option keeps a Beta
  posterior over "the founder approves this": alpha = 1 + summed reward,
  beta = 1 + summed (1 - reward). Thompson sampling draws from those, so an
  option that keeps getting approved is chosen more, one that keeps getting
  killed fades out, and an option with little data still gets tried — the
  loop explores instead of locking onto its first lucky result.

  **Prompt memory** for the decisions that are free text — A06's copy and
  A03's framing: the hooks the founder approved, as examples to learn from,
  and the notes on revisions and kills, as corrections to follow.

Only each run's LATEST decision counts. A run killed and later approved after
a revision is one approved run, not one of each.

With no decisions recorded, every function here returns neutral output and
the pipeline behaves exactly as before. That is deliberate: learning starts
when there is something to learn from, not before.
"""
from __future__ import annotations

import json
import random
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Optional

from pipeline.gtm_learning import feedback as _fb

STATE = Path(__file__).resolve().parents[2] / "pipeline" / "state"
SNAPSHOT = STATE / "learned_preferences.json"

DIMENSIONS = ("visual_archetype", "pillar", "machine")

# An option is retired only on real evidence: at least this many decisions,
# and an approval mean below the floor. Three straight kills under the
# Beta(1, 1) prior is a mean of exactly 0.20, so the floor sits just above it;
# two kills and a revise (0.26) stays in play.
RETIRE_MIN_N = 3
RETIRE_BELOW = 0.25


def latest_per_run(rows: Optional[list[dict]] = None) -> list[dict]:
    """The ledger reduced to one row per run: its most recent decision."""
    if rows is None:
        try:
            rows = [json.loads(l) for l in Path(_fb.LEDGER).read_text(encoding="utf-8").splitlines()
                    if l.strip()]
        except FileNotFoundError:
            rows = []
    by_run: dict[str, dict] = {}
    for r in rows:
        prev = by_run.get(r.get("run_id"))
        if prev is None or str(r.get("at")) >= str(prev.get("at")):
            by_run[r.get("run_id")] = r
    return list(by_run.values())


def posteriors(dim: str, rows: Optional[list[dict]] = None) -> dict[str, dict[str, float]]:
    """Beta(alpha, beta) per option of one dimension, from the latest decisions."""
    out: dict[str, dict[str, float]] = {}
    for r in latest_per_run(rows):
        opt = (r.get("features") or {}).get(dim)
        if not opt:
            continue
        p = out.setdefault(str(opt), {"alpha": 1.0, "beta": 1.0, "n": 0})
        reward = float(r.get("reward", 0.0))
        p["alpha"] += reward
        p["beta"] += 1.0 - reward
        p["n"] += 1
    for p in out.values():
        p["mean"] = round(p["alpha"] / (p["alpha"] + p["beta"]), 3)
    return out


def retired(dim: str, rows: Optional[list[dict]] = None) -> set[str]:
    """Options the founder has consistently rejected."""
    return {k for k, p in posteriors(dim, rows).items()
            if p["n"] >= RETIRE_MIN_N and p["mean"] < RETIRE_BELOW}


def thompson_order(dim: str, options: Iterable[str], *,
                   rows: Optional[list[dict]] = None,
                   rng: Optional[random.Random] = None) -> list[tuple[str, float]]:
    """Options ranked by one Thompson draw each. Unseen options draw from
    Beta(1, 1), so they compete on equal terms until the founder has an
    opinion about them."""
    rng = rng or random.Random()
    post = posteriors(dim, rows)
    scored = []
    for o in options:
        p = post.get(o, {"alpha": 1.0, "beta": 1.0})
        scored.append((o, round(rng.betavariate(p["alpha"], p["beta"]), 3)))
    return sorted(scored, key=lambda t: -t[1])


def _summary(run_id: str) -> dict:
    try:
        return json.loads((Path(_fb.RUNS) / run_id / "summary.json").read_text(encoding="utf-8"))
    except Exception:                               # noqa: BLE001 — boundary
        return {}


def approved_examples(k: int = 3, rows: Optional[list[dict]] = None) -> list[dict]:
    """The most recent approved X posts, hook and opening, as examples."""
    out = []
    for r in sorted(latest_per_run(rows), key=lambda r: str(r.get("at")), reverse=True):
        if r.get("verdict") != "approve":
            continue
        x = (_summary(r["run_id"]).get("posts") or {}).get("x") or {}
        hook = str(x.get("hook") or (r.get("features") or {}).get("x_hook") or "").strip()
        if not hook:
            continue
        out.append({"run_id": r["run_id"], "hook": hook[:200],
                    "opening": " ".join(str(x.get("copy") or "").split())[:400],
                    "note": r.get("note")})
        if len(out) >= k:
            break
    return out


def _all_rows(rows: Optional[list[dict]] = None) -> list[dict]:
    if rows is not None:
        return rows
    try:
        return [json.loads(l) for l in Path(_fb.LEDGER).read_text(encoding="utf-8").splitlines()
                if l.strip()]
    except FileNotFoundError:
        return []


def corrections(k: int = 6, rows: Optional[list[dict]] = None) -> list[dict]:
    """The founder's notes on revisions and kills — what to stop doing.

    Read from every decision, not only each run's latest: a note written on a
    kill is still the founder's view even if the run was later decided again
    without one. Identical notes are shown once.
    """
    out, seen = [], set()
    for r in sorted(_all_rows(rows), key=lambda r: str(r.get("at")), reverse=True):
        key = " ".join(str(r.get("note") or "").lower().split())
        if key in seen:
            continue
        seen.add(key)
        if r.get("verdict") in ("revise", "kill") and r.get("note"):
            f = r.get("features") or {}
            out.append({"verdict": r["verdict"], "note": str(r["note"])[:300],
                        "hook": f.get("x_hook"), "archetype": f.get("visual_archetype")})
        if len(out) >= k:
            break
    return out


def prompt_block(*, for_agent: str) -> str:
    """Text for an agent's prompt. Empty until there is feedback to learn from."""
    rows = latest_per_run()
    if not rows:
        return ""
    counts = {v: sum(1 for r in rows if r.get("verdict") == v)
              for v in ("approve", "revise", "kill")}
    lines = ["FOUNDER PREFERENCES — learned from " + str(len(rows))
             + " reviewed runs (" + ", ".join(k + " " + str(v) for k, v in counts.items())
             + "). These are the founder's own decisions; follow them."]

    if for_agent in ("A06", "A03"):
        ex = approved_examples(rows=rows)
        if ex:
            lines.append("Approved posts — the kind of hook and framing that works:")
            lines += ['  - "' + e["hook"] + '"' + (" (founder: " + e["note"] + ")"
                                                   if e.get("note") else "") for e in ex]
    fixes = corrections()
    if fixes:
        lines.append("Corrections from revisions and kills — do not repeat these:")
        lines += ["  - [" + c["verdict"] + "] " + c["note"] for c in fixes]

    if for_agent == "A03":
        post = posteriors("pillar", rows)
        if post:
            lines.append("Approval rate by pillar (approved share of reviewed runs):")
            lines += ["  - " + k + ": " + str(int(p["mean"] * 100)) + "% of " + str(p["n"])
                      for k, p in sorted(post.items(), key=lambda kv: -kv[1]["mean"])]
    return "\n".join(lines) if len(lines) > 1 else ""


def snapshot(write: bool = True) -> dict[str, Any]:
    """Everything learned so far, for A13's report and the dashboard."""
    rows = latest_per_run()
    snap = {
        "at": datetime.now(timezone.utc).isoformat(),
        "reviewed_runs": len(rows),
        "verdicts": {v: sum(1 for r in rows if r.get("verdict") == v)
                     for v in ("approve", "revise", "kill")},
        "dimensions": {d: posteriors(d, rows) for d in DIMENSIONS},
        "retired": {d: sorted(retired(d, rows)) for d in DIMENSIONS},
        "approved_examples": approved_examples(rows=rows),
        "corrections": corrections(),
    }
    if write:
        tmp = SNAPSHOT.with_suffix(".tmp")
        tmp.write_text(json.dumps(snap, indent=2, ensure_ascii=False), encoding="utf-8")
        tmp.replace(SNAPSHOT)
    return snap
