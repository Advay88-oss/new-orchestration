"""A02 (market analyst) learns from whether its calls came true — not from approval.

A02's job is to say what is happening in the market. Rewarding it with the
founder's approve/kill would teach it to describe the market the founder
likes, which is the one thing an analyst must not do (reward-trained models
drift toward agreeing with the rater — "sycophancy"). So its reward is
accuracy, measured by the scrapes that come after it.

Each theme in a reading now carries a CALL:

  outlook      rising | steady | fading — where this theme goes in the next days
  watch_terms  2–4 short terms, each of which must appear in a headline the
               theme cites (checked in code), so the call is tied to evidence
               and cannot be made on words that appear everywhere

A call is scored against later harvests of live signals (archive excluded)
scraped between MIN_HOURS and MAX_DAYS after it. The theme's share is the
fraction of live headlines containing any watch term; the outcome is rising
if the later share is ≥1.25× the original, fading if ≤0.8×, else steady.
A call with no later harvest in the window is still pending.

The record — hit rate per outlook, and recent misses with what actually
happened — is shown to A02 on its next reading, so it can calibrate: if its
"rising" calls keep coming out steady, it sees that.

    python -m pipeline.gtm_learning.analyst_accuracy     # print the record
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

RUNS = Path(__file__).resolve().parents[1] / "state" / "gtm_runs"
OUTLOOKS = ("rising", "steady", "fading")
MIN_HOURS = 20.0
MAX_DAYS = 7.0
UP, DOWN = 1.25, 0.8


def _json(p: Path) -> Optional[dict]:
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:                               # noqa: BLE001 — boundary
        return None


def _t(s: str) -> Optional[datetime]:
    try:
        t = datetime.fromisoformat(str(s).replace("Z", "+00:00"))
        return t if t.tzinfo else t.replace(tzinfo=timezone.utc)
    except Exception:                               # noqa: BLE001 — undated
        return None


def _live(h: dict) -> list[str]:
    return [str(s.get("headline", "")).lower() for s in h.get("signals") or []
            if not str(s.get("source_type", "")).startswith("ARCHIVE")]


def _share(heads: list[str], terms: list[str]) -> tuple[float, int, int]:
    c = sum(1 for h in heads if any(t in h for t in terms))
    return (c + 0.5) / (len(heads) + 1.0), c, len(heads)


def clean_call(theme: dict, headlines: dict[str, str]) -> dict:
    """Keep a theme's call only if it is well formed and grounded in its citations."""
    out = str(theme.get("outlook") or "").lower().strip()
    cited = " ".join(headlines.get(str(i), "") for i in theme.get("signal_ids") or []).lower()
    terms = []
    for t in theme.get("watch_terms") or []:
        t = " ".join(str(t).lower().split())
        if 3 <= len(t) <= 40 and t in cited and t not in terms:
            terms.append(t)
    if out in OUTLOOKS and terms:
        theme["outlook"], theme["watch_terms"] = out, terms[:4]
    else:
        theme.pop("outlook", None)
        theme.pop("watch_terms", None)
    return theme


def calls() -> list[dict]:
    """Every call made, scored where a later harvest exists."""
    harvests = []
    for d in sorted(RUNS.glob("GTM-*")):
        h = _json(d / "harvest.json")
        t = _t((h or {}).get("scraped_at", ""))
        if h and t:
            harvests.append((t, d.name, _live(h)))
    at = {rid: (t, heads) for t, rid, heads in harvests}
    out = []
    for d in sorted(RUNS.glob("GTM-*")):
        a = _json(d / "analysis.json")
        if not a or d.name not in at:
            continue
        t0, heads0 = at[d.name]
        for th in (a.get("landscape") or {}).get("themes") or []:
            if not isinstance(th, dict) or th.get("outlook") not in OUTLOOKS:
                continue
            terms = [str(x).lower() for x in th.get("watch_terms") or []]
            if not terms:
                continue
            later = [heads for t, rid, heads in harvests
                     if t0 + timedelta(hours=MIN_HOURS) <= t <= t0 + timedelta(days=MAX_DAYS)]
            row = {"run_id": d.name, "at": t0.isoformat(), "theme": th.get("theme"),
                   "outlook": th["outlook"], "terms": terms}
            base, c0, n0 = _share(heads0, terms)
            row["share_then"] = f"{c0}/{n0}"
            if not later:
                row["status"] = "pending"
            else:
                shares = [_share(h, terms) for h in later]
                after = sum(s[0] for s in shares) / len(shares)
                ratio = after / base
                actual = "rising" if ratio >= UP else "fading" if ratio <= DOWN else "steady"
                row.update(status="scored", actual=actual, right=actual == row["outlook"],
                           share_after=f"{sum(s[1] for s in shares)}/{sum(s[2] for s in shares)}"
                                       f" over {len(shares)} later scrape(s)")
            out.append(row)
    return out


def record() -> dict:
    rows = calls()
    scored = [r for r in rows if r["status"] == "scored"]
    per = {}
    for o in OUTLOOKS:
        rs = [r for r in scored if r["outlook"] == o]
        per[o] = {"right": sum(r["right"] for r in rs), "of": len(rs),
                  # Beta(1,1) mean — calibration, shrunk toward 50% while n is small
                  "mean": round((1 + sum(r["right"] for r in rs)) / (2 + len(rs)), 2)}
    return {"scored": len(scored), "right": sum(r["right"] for r in scored),
            "pending": len(rows) - len(scored), "per_outlook": per,
            "misses": [r for r in scored if not r["right"]][-5:]}


def prompt_block() -> str:
    """A02's own track record, as it sees it before its next reading."""
    r = record()
    if not r["scored"]:
        return ("YOUR TRACK RECORD: no call has been checked yet"
                + (" (" + str(r["pending"]) + " pending)" if r["pending"] else "")
                + ". Calls are scored against the scrapes that follow, not against "
                  "anyone's approval.")
    lines = ["YOUR TRACK RECORD — each theme's outlook is checked against the scrapes "
             "that follow it, not against anyone's approval. Calibrate to it:",
             "  overall: " + str(r["right"]) + " of " + str(r["scored"]) + " calls right"]
    for o, p in r["per_outlook"].items():
        if p["of"]:
            lines.append("  '" + o + "' calls: right " + str(p["right"]) + " of " + str(p["of"]))
    if r["misses"]:
        lines.append("  recent misses:")
        lines += ["   - '" + str(m["theme"])[:80] + "': you said " + m["outlook"]
                  + ", it was " + m["actual"] + " (" + m["share_then"] + " then, "
                  + m["share_after"] + ")" for m in r["misses"]]
    return "\n".join(lines)


def record_text() -> str:
    r = record()
    if not r["scored"]:
        return "accuracy: no call checked yet (" + str(r["pending"]) + " pending)"
    return ("accuracy: " + str(r["right"]) + "/" + str(r["scored"]) + " calls right"
            + (", " + str(r["pending"]) + " pending" if r["pending"] else ""))


if __name__ == "__main__":
    print(json.dumps(record(), indent=1, ensure_ascii=False))
    print(prompt_block())
