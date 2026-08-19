#!/usr/bin/env python3
"""MEASURE — pull real engagement for every published post and record it with features.

Reads content_history.json for posts that were actually published (a real x.com
URL), pulls current engagement for each via OpenCLI, and appends a row to
pipeline/state/learning/performance.jsonl tagged with the abstract features the
learner aggregates on.

    python pipeline/scripts/performance_tracker.py            # all accounts seen
    python pipeline/scripts/performance_tracker.py --account AnandAdvay91289

Run it repeatedly — engagement grows over time, and each measurement is a fresh
row (measured_at), so the learner can see trajectories, not just a snapshot.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import learning as L  # noqa: E402

REPO = HERE.parents[1]
HISTORY = REPO / "pipeline" / "state" / "content_history.json"


def opencli_tweets(account: str, limit: int = 50) -> list[dict]:
    try:
        r = subprocess.run(["opencli", "twitter", "tweets", account, "--limit", str(limit), "-f", "json"],
                           capture_output=True, text=True, timeout=120, shell=True,
                           encoding="utf-8", errors="replace")
        if r.returncode != 0:
            print(f"  ! opencli tweets {account}: {r.stderr[:120] or r.stdout[:120]}")
            return []
        data = json.loads(r.stdout)
        return data if isinstance(data, list) else data.get("results", data.get("tweets", []))
    except Exception as e:
        print(f"  ! opencli tweets {account}: {e}")
        return []


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--account", default="AnandAdvay91289")
    args = ap.parse_args()
    L.ensure_store()

    history = json.loads(HISTORY.read_text(encoding="utf-8"))
    published = []
    for r in history:
        out = str(r.get("publish_outcome", ""))
        m = re.search(r"status/(\d+)", out)
        if m:
            published.append((m.group(1), r))
    print(f"published posts in history: {len(published)}")
    if not published:
        return 0

    print(f"pulling live engagement from @{args.account} ...")
    live = opencli_tweets(args.account)
    by_id = {str(t.get("id")): t for t in live}
    print(f"  fetched {len(live)} tweets from the timeline\n")

    measured_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    rows = []
    for tid, r in published:
        t = by_id.get(tid)
        if not t:
            print(f"  [skip] {tid} not on the fetched timeline (older than limit?)")
            continue
        feats = L.features(
            tenant=r.get("tenant", "vanna"),
            platform="x",
            topic=r.get("topic_covered", ""),
            hook=r.get("hook_shipped", ""),
            fmt=r.get("format", "stat-card"),
            arc=r.get("angle_covered", ""),
        )
        eng = {
            "likes": t.get("likes", 0) or 0,
            "retweets": t.get("retweets", 0) or 0,
            "replies": t.get("replies", 0) or 0,
            "views": t.get("views", 0) or 0,
        }
        eng["score"] = eng["likes"] * 3 + eng["retweets"] * 5 + eng["replies"] * 4 + eng["views"] * 0.1
        row = {"post_id": tid, "run_id": r.get("run_id"), "hook": r.get("hook_shipped", ""),
               "published_at": r.get("timestamp"), "measured_at": measured_at,
               "url": f"https://x.com/{args.account}/status/{tid}",
               "features": feats, "engagement": eng}
        rows.append(row)
        print(f"  {feats['tenant']:6} {feats['hook_type']:11} {feats['theme']:14} "
              f"likes={eng['likes']} rt={eng['retweets']} views={eng['views']} score={eng['score']:.0f}")

    with PERF_open() as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"\nappended {len(rows)} measurement rows -> {L.PERF.relative_to(REPO)}")
    return 0


def PERF_open():
    return open(L.PERF, "a", encoding="utf-8")


if __name__ == "__main__":
    sys.exit(main())
