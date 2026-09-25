"""A01 learns where the useful signals come from.

Every run A01 scrapes six collectors (Google News over a rotating slice of
queries, Reddit, X, Telegram, docs/blogs, DefiLlama) plus the archive, and
brings back ~26 signals of which A02 uses one. Nothing told it which of those
places tend to produce something Vanna can actually talk about, so a
Google News query that returns price-prediction listicles got the same slot
every run as one that surfaces liquidation incidents.

Each place is an ARM: the collector, and inside it the sub-source — the X
handle, the subreddit, the news query. An arm's record is a Beta posterior
built from two kinds of evidence, recomputed from the run folders every time
(no state to drift):

  * A02's reading of every harvested signal (`analysis.json`): DIRECT 1,
    ADJACENT 0.5, NONE 0. Available on every run, including directive runs.
  * The founder's decision on a run whose subject came from a scraped signal:
    the arm that produced that signal gets the reward at weight 3.

Evidence halves in weight every HALF_LIFE_DAYS, because last month's good
source is not necessarily this week's.

What the record changes, and the guard against a filter bubble:

  * Every collector still runs every run. The harvest — what the Scraped
    Intelligence view shows and what A02 reads — is never narrowed.
  * News queries: most slots go to queries by Thompson draw, one is always a
    random query, so a query with a bad record still gets looked at.
  * What goes forward to the selector: the top ~70% by relevance plus the
    arm's draw; the remaining ~30% are reserved — first for any collector not
    yet represented, then filled at random. No source can drop to zero.

    python -m pipeline.gtm_learning.source_learning      # print the record
"""
from __future__ import annotations

import json
import math
import random
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Optional

RUNS = Path(__file__).resolve().parents[1] / "state" / "gtm_runs"
HALF_LIFE_DAYS = 14.0
FOUNDER_WEIGHT = 3.0
EXPLORE_SHARE = 0.3            # of the forwarded slots, never ranked by the record
MIN_N_FOR_SUB = 5.0            # a sub-source's own record is used from this much evidence
BONUS_SCALE = 6.0              # a draw of 1.0 is worth +3 over the keyword score
GRADE = {"DIRECT": 1.0, "ADJACENT": 0.5, "NONE": 0.0}


def arm_of(signal_id: str, query: Optional[str] = None) -> tuple[str, Optional[str]]:
    """(collector, sub-source) from a signal id — the collectors' own prefixes."""
    sid = str(signal_id or "").upper()
    if sid.startswith("SIG-NEWS"):
        return "google_news", (query or None)
    if sid.startswith("SIG-FEED-"):
        return "news_feeds", sid.split("-")[2].lower()
    if sid.startswith("SIG-GDELT"):
        return "gdelt", None
    if sid.startswith("SIG-HACK"):
        return "defillama_hacks", None
    if sid.startswith("SIG-TWITTER-"):
        return "twitter", sid.split("-")[2].lower()
    if sid.startswith("SIG-REDDIT-"):
        return "reddit", sid.split("-")[2].lower()
    if sid.startswith("SIG-TG-") and sid.count("-") >= 3:
        return "telegram", sid.split("-")[2].lower()
    if sid.startswith("SIG-TG"):
        return "telegram", None
    if sid.startswith("SIG-DOCS"):
        return "docs_blogs", None
    if sid.startswith("SIG-LLAMA"):
        return "defillama", None
    return "archive", None


def _json(p: Path) -> Optional[dict]:
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:                               # noqa: BLE001 — boundary
        return None


def _age_weight(at: str, now: datetime) -> float:
    try:
        t = datetime.fromisoformat(str(at).replace("Z", "+00:00"))
        if t.tzinfo is None:
            t = t.replace(tzinfo=timezone.utc)
    except Exception:                               # noqa: BLE001 — undated
        return 0.5
    days = max(0.0, (now - t).total_seconds() / 86400.0)
    return 0.5 ** (days / HALF_LIFE_DAYS)


def _founder_rows() -> dict[str, dict]:
    try:
        from pipeline.gtm_learning.preferences import latest_per_run
        return {str(r.get("run_id")): r for r in latest_per_run()}
    except Exception:                               # noqa: BLE001 — boundary
        return {}


def evidence(now: Optional[datetime] = None) -> list[tuple[str, Optional[str], float, float]]:
    """(collector, sub, reward, weight) for every graded signal and decision."""
    now = now or datetime.now(timezone.utc)
    founder = _founder_rows()
    out: list[tuple[str, Optional[str], float, float]] = []
    for d in sorted(RUNS.glob("GTM-*")):
        h = _json(d / "harvest.json")
        if not h:
            continue
        w = _age_weight(h.get("scraped_at", ""), now)
        by_id = {s.get("signal_id"): s for s in h.get("signals") or []}
        a = _json(d / "analysis.json") or {}
        for r in a.get("signals") or []:
            g = GRADE.get(str(r.get("relevance", "")).upper())
            sid = r.get("signal_id")
            if g is None or sid not in by_id:
                continue
            col, sub = arm_of(sid, by_id[sid].get("query"))
            out.append((col, sub, g, w))
        f = founder.get(d.name)
        feats = (f or {}).get("features") or {}
        if f and not feats.get("directive") and feats.get("signal"):
            head = str(feats["signal"]).lower()[:120]
            hit = next((s for s in by_id.values()
                        if str(s.get("headline", "")).lower()[:120] == head), None)
            if hit:
                col, sub = arm_of(hit.get("signal_id"), hit.get("query"))
                out.append((col, sub, float(f.get("reward", 0.0)), w * FOUNDER_WEIGHT))
    return out


def posteriors(now: Optional[datetime] = None) -> dict[str, dict[str, float]]:
    """Beta per arm. Keys are the collector ("twitter") and "collector:sub"."""
    post: dict[str, dict[str, float]] = {}
    for col, sub, r, w in evidence(now):
        for key in ([col] + ([col + ":" + sub] if sub else [])):
            p = post.setdefault(key, {"alpha": 1.0, "beta": 1.0, "n": 0.0})
            p["alpha"] += r * w
            p["beta"] += (1.0 - r) * w
            p["n"] += w
    for p in post.values():
        p["mean"] = round(p["alpha"] / (p["alpha"] + p["beta"]), 3)
        p["n"] = round(p["n"], 1)
    return post


def _draw(post: dict, col: str, sub: Optional[str], rng: random.Random) -> float:
    p = post.get(col + ":" + sub) if sub else None
    if not p or p["n"] < MIN_N_FOR_SUB:
        p = post.get(col)
    if not p:
        return rng.betavariate(1.0, 1.0)
    return rng.betavariate(p["alpha"], p["beta"])


def pick_queries(queries: list[str], n: int, rng: Optional[random.Random] = None) -> list[str]:
    """n news queries: all but one by Thompson draw, one always at random."""
    rng = rng or random.Random()
    qs = list(dict.fromkeys(queries))
    if len(qs) <= n:
        return qs
    post = posteriors()
    ranked = sorted(qs, key=lambda q: _draw(post, "google_news", q, rng), reverse=True)
    chosen = ranked[:n - 1]
    rest = [q for q in qs if q not in chosen]
    return chosen + [rng.choice(rest)]


def forward(signals: list, limit: int, base: Callable[[Any], float],
            query_of: Optional[dict] = None, rng: Optional[random.Random] = None) -> list:
    """The signals that go on to the selector, learned order plus a reserve.

    `base` is A01's keyword relevance score. The record adds a Thompson draw
    per arm; ~30% of the slots are kept out of that ranking entirely.
    """
    rng = rng or random.Random()
    query_of = query_of or {}
    if len(signals) <= limit:
        limit = len(signals)
    post = posteriors()

    def arm(s):
        return arm_of(getattr(s, "signal_id", ""), query_of.get(getattr(s, "signal_id", "")))

    # The archive gets no learned bonus. It grades well because it is the
    # Brain DB's own curated opportunities — the same Blend-heavy set that
    # once took 32 of 41 runs to one topic — and it stays behind live news.
    draws = {id(s): (0.5 if arm(s)[0] == "archive" else _draw(post, *arm(s), rng))
             for s in signals}
    ranked = sorted(signals, key=lambda s: base(s) + BONUS_SCALE * (draws[id(s)] - 0.5),
                    reverse=True)
    top_n = max(1, limit - int(math.ceil(limit * EXPLORE_SHARE)))
    out = ranked[:top_n]
    rest = ranked[top_n:]
    # Reserve: every live collector that brought something is represented.
    have = {arm(s)[0] for s in out}
    for s in list(rest):
        if len(out) >= limit:
            break
        col = arm(s)[0]
        if col != "archive" and col not in have:
            out.append(s)
            have.add(col)
            rest.remove(s)
    rng.shuffle(rest)
    out += rest[:max(0, limit - len(out))]
    return out


def record_text(k: int = 4) -> str:
    """A01's stage note: where the good signals have been coming from."""
    post = posteriors()
    cols = {k_: v for k_, v in post.items()
            if ":" not in k_ and k_ != "archive" and v["n"] >= 1}
    if not cols:
        return "no source record yet"
    best = sorted(cols.items(), key=lambda kv: -kv[1]["mean"])
    txt = "source record: " + ", ".join(
        c + " " + str(int(round(p["mean"] * 100))) + "%" for c, p in best[:k])
    return txt + " useful (A02-graded + founder), 30% of slots reserved for exploration"


if __name__ == "__main__":
    print(json.dumps(dict(sorted(posteriors().items(),
                                 key=lambda kv: -kv[1]["mean"])), indent=1))
    print(record_text())
