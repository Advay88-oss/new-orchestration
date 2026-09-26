"""Engagement 48-72 hours after a post goes out (the architecture's MT step).

Nothing here publishes: the founder posts by hand, then gives the post's
link — a reply on Telegram after Approve, or the dashboard's run page. The
link is recorded against the run (`published.json` in its folder), and the
scheduler's metrics_collect job reads the post back once it is 48 hours old:
impressions, likes, reposts, replies, quotes, bookmarks, the media it
carried and when it went out. That becomes the run's outcome, the reward is
recomputed (engagement over the tenant's own baseline), and the format and
posting-slot arms are credited with what was actually published.

Clicks and signups (the architecture's business outcome) count when they
are logged — there is no UTM tracking connected to read them from yet.

    python -m pipeline.gtm_learning.metrics_collector published GTM-... https://x.com/handle/status/123
    python -m pipeline.gtm_learning.metrics_collector collect [--force]
    python -m pipeline.gtm_learning.metrics_collector status
"""
from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Optional

RUNS = Path(__file__).resolve().parents[1] / "state" / "gtm_runs"
MIN_AGE_H = 48
RECOLLECT_AFTER_H = 24 * 7          # one second reading a week in, then done
STATUS = re.compile(r"https?://(?:www\.)?(?:x|twitter)\.com/([A-Za-z0-9_]{1,15})/status/(\d+)")
RUN_ID = re.compile(r"^GTM-\d{8}-\d{6}$")


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _read(run_id: str) -> Optional[dict]:
    try:
        return json.loads((RUNS / run_id / "published.json").read_text(encoding="utf-8"))
    except Exception:                               # noqa: BLE001 — not published
        return None


def _write(run_id: str, rec: dict) -> None:
    (RUNS / run_id / "published.json").write_text(json.dumps(rec, indent=1), encoding="utf-8")


def parse_url(url: str) -> Optional[tuple[str, str]]:
    m = STATUS.search(str(url or ""))
    return (m.group(1), m.group(2)) if m else None


FORMATS = ("image", "video", "thread", "text")


def mark_published(run_id: str, url: str, *, source: str = "manual",
                   fmt: Optional[str] = None) -> dict[str, Any]:
    """Record where a run's post went out (and, optionally, as what: a thread
    cannot be told from its first post's media, so the founder can say)."""
    if not RUN_ID.match(run_id) or not (RUNS / run_id).is_dir():
        return {"ok": False, "error": "unknown run " + run_id}
    got = parse_url(url)
    if not got:
        return {"ok": False, "error": "not an X post link (x.com/<handle>/status/<id>)"}
    handle, tid = got
    rec = _read(run_id) or {}
    rec.update({"url": "https://x.com/" + handle + "/status/" + tid, "handle": handle, "tweet_id": tid,
                "marked_at": rec.get("marked_at") or _now().isoformat(), "source": source})
    if fmt in FORMATS:
        rec["format"] = fmt
    _write(run_id, rec)
    return {"ok": True, "run_id": run_id, **rec,
            "collect_after": (datetime.fromisoformat(rec["marked_at"]) + timedelta(hours=MIN_AGE_H)).isoformat()}


def _fetch(rec: dict) -> Optional[dict]:
    """The post itself, found among its author's posts around when it was marked."""
    from pipeline.intelligence_stream import x_apify
    marked = datetime.fromisoformat(rec["marked_at"])
    since = (marked - timedelta(days=3)).strftime("%Y-%m-%d")
    until = (marked + timedelta(days=1)).strftime("%Y-%m-%d")
    for terms in (["from:" + rec["handle"] + " since:" + since + " until:" + until],
                  ["conversation_id:" + rec["tweet_id"]]):
        for p in x_apify.search(terms, max_items=60):
            if p["id"] == rec["tweet_id"]:
                return p
    return None


def collect(*, force: bool = False) -> dict[str, Any]:
    """Read back every published run that is due. Never raises per run."""
    from pipeline.gtm_learning import rewards
    out: dict[str, Any] = {"due": 0, "collected": [], "not_found": [], "errors": []}
    now = _now()
    for d in sorted(RUNS.glob("GTM-*")):
        rec = _read(d.name)
        if not rec or not rec.get("tweet_id"):
            continue
        age_h = (now - datetime.fromisoformat(rec["marked_at"])).total_seconds() / 3600
        last = rec.get("collected_at")
        if not force:
            if age_h < MIN_AGE_H:
                continue
            if last and (len(rec.get("readings") or []) >= 2
                         or (now - datetime.fromisoformat(last)).total_seconds() / 3600 < RECOLLECT_AFTER_H):
                continue
        out["due"] += 1
        try:
            p = _fetch(rec)
        except Exception as exc:                    # noqa: BLE001 — this run fails alone
            out["errors"].append({"run_id": d.name, "error": str(exc)[:160]})
            continue
        if not p:
            out["not_found"].append(d.name)
            continue
        metrics = {k: p.get(k) for k in ("impressions", "likes", "reposts", "replies", "quotes", "bookmarks")}
        metrics.update({"posted_at": p.get("created_at"), "url": rec["url"], "tweet_id": rec["tweet_id"],
                        "media": p.get("media") or []})
        if rec.get("format"):
            metrics["format"] = rec["format"]
        res = rewards.log_outcome(d.name, metrics, source="x_collector")
        rec["collected_at"] = now.isoformat()
        rec.setdefault("readings", []).append({"at": now.isoformat(), "age_h": round(age_h, 1),
                                               **{k: v for k, v in metrics.items() if k not in ("url", "media")}})
        _write(d.name, rec)
        out["collected"].append({"run_id": d.name, "age_h": round(age_h, 1), "impressions": metrics["impressions"],
                                 "reward": (res.get("event") or {}).get("total")})
    return out


def status() -> list[dict]:
    rows = []
    for d in sorted(RUNS.glob("GTM-*")):
        rec = _read(d.name)
        if rec:
            rows.append({"run_id": d.name, "url": rec.get("url"), "marked_at": rec.get("marked_at"),
                         "collected_at": rec.get("collected_at"), "readings": len(rec.get("readings") or [])})
    return rows


if __name__ == "__main__":
    a = sys.argv[1:]
    if a[:1] == ["published"] and len(a) >= 3:
        print(json.dumps(mark_published(a[1], a[2], source=(a[4] if len(a) > 4 else "cli"),
                                        fmt=a[3] if len(a) > 3 and a[3] in FORMATS else None)))
    elif a[:1] == ["get"] and len(a) >= 2:
        print(json.dumps(_read(a[1]) or {}))
    elif a[:1] == ["collect"]:
        print(json.dumps(collect(force="--force" in a), default=str))
    else:
        print(json.dumps(status(), indent=1))
