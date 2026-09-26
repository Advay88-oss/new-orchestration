"""Reward events — one number per run, from every signal the architecture names.

  human       the founder's decision: approve 1.0, edit 0.8 (approved after
              editing), revise 0.3, kill 0.0              — turant, high weight
  reviewer    A10's fact check and claim gate: a HARD GATE. A run the reviewer
              blocked scores 0, whatever else it earned  — turant
  engagement  the post's engagement rate divided by this tenant's own rolling
              baseline, so 50 likes and 5,000 likes are comparable across
              brands                                      — 48-72 h later, medium

  total = 0 when the reviewer blocked; otherwise the weighted mean of the
          signals present (human 0.6, engagement 0.4).

Each event also records the ARMS the run actually shipped (pillar, hook type,
length) and its CONTEXT (platform, weekday or weekend, whether there was news),
which is what the contextual bandit (`bandit.py`) learns from. Stored in the
tenant's brand brain, recomputed whenever a signal arrives.
"""
from __future__ import annotations

import json
import re
import statistics
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

RUNS = Path(__file__).resolve().parents[1] / "state" / "gtm_runs"
HUMAN = {"approve": 1.0, "edit": 0.8, "revise": 0.3, "kill": 0.0}
W_HUMAN, W_ENGAGEMENT = 0.6, 0.4
BASELINE_MIN = 3


def _brain():
    # The learning loop is a pipeline, not an agent: it keeps its own tables
    # and reads the brain directly. Agents go through the Brain MCP server.
    from pipeline.brand_brain.client import Brain
    return Brain()


def _json(p: Path) -> Optional[dict]:
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:                               # noqa: BLE001 — absent
        return None


# ---------------------------------------------------------------- arms & context

def hook_type(hook: str) -> str:
    h = " ".join(str(hook or "").split())
    low = h.lower()
    if not h:
        return "none"
    if h.rstrip().endswith("?"):
        return "question"
    if re.match(r"^(i |we |when |last |yesterday|in 20\d\d)", low):
        return "story"
    if re.search(r"\b(not|isn't|aren't|stop|myth|wrong|never|no one|nobody|can't|cannot|don't)\b", low):
        return "contrarian"
    if re.search(r"\d", h):
        return "data"
    return "statement"


def length_bucket(copy: str) -> str:
    n = len(str(copy or ""))
    return "short" if n < 400 else "medium" if n < 900 else "long"


# The posting slot, in the tenant's timezone (profile "timezone", else UTC).
SLOTS = (("morning", 6, 11), ("midday", 11, 15), ("evening", 15, 20), ("night", 20, 6))


def _tz():
    from zoneinfo import ZoneInfo
    try:
        from pipeline.brand_brain import context as C
        return ZoneInfo(str(C.profile().get("timezone") or "UTC"))
    except Exception:                               # noqa: BLE001 — unknown zone
        return ZoneInfo("UTC")


def slot_of(iso: str) -> str:
    """morning / midday / evening / night for a posting time."""
    try:
        h = datetime.fromisoformat(str(iso).replace("Z", "+00:00")).astimezone(_tz()).hour
    except (TypeError, ValueError):
        return ""
    for name, lo, hi in SLOTS:
        if (lo <= h < hi) if lo < hi else (h >= lo or h < hi):
            return name
    return ""


def format_of(m: dict) -> str:
    """What was actually published: video, image, thread or text."""
    f = str(m.get("format") or "").lower()
    if f in ("video", "image", "thread", "text"):
        return f
    media = [str(x).lower() for x in (m.get("media") or [])]
    if any(x in ("video", "animated_gif") for x in media):
        return "video"
    if media:
        return "image"
    return ""


def arms_of(summary: dict, published: Optional[dict] = None) -> dict[str, str]:
    """The choices a run is credited with. Format and posting slot are what
    was actually PUBLISHED (from the post's outcome record), never what was
    recommended: a run makes every asset and the founder picks what to post,
    so crediting the recommendation would teach the loop about posts that
    never went out."""
    x = (summary.get("posts") or {}).get("x") or {}
    pillar = str(summary.get("pillar") or "")
    pub = published or {}
    return {k: v for k, v in {
        "pillar": pillar if pillar and pillar != "NONE" else "",
        "hook_type": hook_type(x.get("hook", "")) if x else "",
        "length": length_bucket(x.get("copy", "")) if x else "",
        "format": format_of(pub),
        "slot": slot_of(pub.get("posted_at", "")) if pub.get("posted_at") else "",
    }.items() if v}


def context_of(summary: dict) -> dict[str, Any]:
    try:
        when = datetime.fromisoformat(str(summary.get("started_at")).replace("Z", "+00:00"))
    except Exception:                               # noqa: BLE001 — undated
        when = datetime.now(timezone.utc)
    news = bool(((summary.get("brain") or {}).get("whats_new")))
    return {"platform": "x", "day_type": "weekend" if when.weekday() >= 5 else "weekday",
            "whats_new": news, "directive": bool(summary.get("directive"))}


# ------------------------------------------------------------------ engagement

def engagement_rate(m: dict) -> Optional[float]:
    imp = float(m.get("impressions") or m.get("views") or 0)
    if imp <= 0:
        return None
    acts = sum(float(m.get(k) or 0) for k in ("likes", "reposts", "replies", "quotes", "bookmarks"))
    return acts / imp


def published_of(run_id: str) -> Optional[dict]:
    """The newest outcome record for a run: its metrics plus what was posted
    (format, posted_at, url), if the post has been logged."""
    try:
        outs = _brain().outcomes(500)
    except Exception:                               # noqa: BLE001 — no brain
        return None
    mine = [o for o in outs if o.get("run_id") == run_id or o.get("post_id") == run_id]
    return mine[0]["metrics"] if mine else None


def normalised_engagement(run_id: str) -> Optional[float]:
    """This run's engagement rate over the tenant's rolling baseline (the
    median of its previous posts), mapped to 0..1 with 0.5 = baseline."""
    outs = _brain().outcomes(500)
    mine = [o for o in outs if o.get("run_id") == run_id or o.get("post_id") == run_id]
    if not mine:
        return None
    rate = engagement_rate(mine[0]["metrics"])            # newest measurement
    if rate is None:
        return None
    others = [r for o in outs if o not in mine and (r := engagement_rate(o["metrics"])) is not None]
    others = others[:20]
    if len(others) < BASELINE_MIN:
        return None                                        # no baseline yet: not comparable
    base = statistics.median(others) or 1e-9
    return round(min(rate / base, 2.0) / 2.0, 3)


# ---------------------------------------------------------------------- events

def compute(run_id: str) -> Optional[dict[str, Any]]:
    if not (RUNS / run_id / "summary.json").exists():
        try:
            from pipeline.gtm_os.state_sync import ensure_run
            ensure_run(run_id)
        except Exception:                           # noqa: BLE001 — boundary
            pass
    s = _json(RUNS / run_id / "summary.json")
    if not s or s.get("source") == "studio":
        return None
    fb = (_json(RUNS / run_id / "feedback.json") or {}).get("latest") or {}
    human = HUMAN.get(str(fb.get("verdict") or "").lower())
    reviewer = s.get("review_passed")
    engagement = normalised_engagement(run_id)
    if reviewer is False:
        total = 0.0                                        # the hard gate
    else:
        parts = [(v, w) for v, w in ((human, W_HUMAN), (engagement, W_ENGAGEMENT)) if v is not None]
        total = round(sum(v * w for v, w in parts) / sum(w for _, w in parts), 3) if parts else None
    arms = arms_of(s, published_of(run_id))
    if total is None or not arms:
        return None
    return {"run_id": run_id, "human": human,
            "reviewer_ok": None if reviewer is None else int(bool(reviewer)),
            "engagement": engagement, "total": total, "arms": arms, "context": context_of(s)}


def record_run(run_id: str) -> Optional[dict[str, Any]]:
    """(Re)compute and store a run's reward event. Never raises."""
    try:
        ev = compute(run_id)
        if not ev:
            return None
        with _brain()._db() as con:
            con.execute(
                "INSERT INTO reward_events(run_id, human, reviewer_ok, engagement, total, arms, context, at) "
                "VALUES (?,?,?,?,?,?,?,?) ON CONFLICT(run_id) DO UPDATE SET human=excluded.human, "
                "reviewer_ok=excluded.reviewer_ok, engagement=excluded.engagement, total=excluded.total, "
                "arms=excluded.arms, context=excluded.context, at=excluded.at",
                (ev["run_id"], ev["human"], ev["reviewer_ok"], ev["engagement"], ev["total"],
                 json.dumps(ev["arms"]), json.dumps(ev["context"]), datetime.now(timezone.utc).isoformat()))
        return ev
    except Exception:                               # noqa: BLE001 — boundary
        return None


def events(limit: int = 500) -> list[dict[str, Any]]:
    with _brain()._db() as con:
        rows = con.execute("SELECT * FROM reward_events ORDER BY run_id DESC LIMIT ?", (limit,)).fetchall()
    return [{**dict(r), "arms": json.loads(r["arms"]), "context": json.loads(r["context"])} for r in rows]


def backfill() -> dict[str, int]:
    n = 0
    for d in sorted(RUNS.glob("GTM-*")):
        if record_run(d.name):
            n += 1
    return {"events": n}


# ------------------------------------------------------ preference pairs, outcomes

def add_pair(run_id: str, *, platform: str, rejected: str, chosen: str, context: str = "",
             source: str = "dashboard") -> bool:
    if not chosen.strip() or " ".join(chosen.split()) == " ".join(rejected.split()):
        return False
    with _brain()._db() as con:
        con.execute("INSERT INTO preference_pairs(run_id, platform, context, rejected, chosen, source, at) "
                    "VALUES (?,?,?,?,?,?,?)",
                    (run_id, platform, context[:2000], rejected[:6000], chosen[:6000], source,
                     datetime.now(timezone.utc).isoformat()))
    return True


def pairs(limit: int = 50) -> list[dict[str, Any]]:
    with _brain()._db() as con:
        return [dict(r) for r in con.execute(
            "SELECT * FROM preference_pairs ORDER BY id DESC LIMIT ?", (limit,)).fetchall()]


def log_outcome(run_id: str, metrics: dict[str, Any], *, source: str = "manual") -> dict[str, Any]:
    """A published post's metrics, then the run's reward recomputed."""
    clean: dict[str, Any] = {k: float(v) for k, v in metrics.items()
                             if k in ("impressions", "views", "likes", "reposts", "replies", "quotes",
                                      "bookmarks", "clicks", "signups") and v not in (None, "")}
    # What was published, for the format and posting-slot arms.
    for k in ("format", "posted_at", "url", "tweet_id"):
        if metrics.get(k):
            clean[k] = str(metrics[k])
    if metrics.get("media"):
        clean["media"] = [str(x) for x in metrics["media"]][:4]
    _brain().log_post_outcome(run_id, clean, run_id=run_id, source=source)
    return {"ok": True, "metrics": clean, "event": record_run(run_id)}


if __name__ == "__main__":
    import sys
    if sys.argv[1:2] == ["backfill"]:
        print(json.dumps(backfill()))
    elif sys.argv[1:2] == ["outcome"] and len(sys.argv) >= 4:
        print(json.dumps(log_outcome(sys.argv[2], json.loads(sys.argv[3]), source="dashboard"), default=str))
    else:
        print(json.dumps(events(20), indent=1, default=str))
