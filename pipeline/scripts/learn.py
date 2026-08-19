#!/usr/bin/env python3
"""ANALYSE + LEARN — turn measurements into a cross-company pattern knowledge base.

Ingests two real sources:
  1. Competitor/market signals from the trend scout (pipeline/state/trends/*.json)
     — what topics/hooks are getting engagement in each company's market.
  2. Own published-post performance (pipeline/state/learning/performance.jsonl)
     — what actually worked for content we shipped.

Aggregates both by abstract feature (hook type, theme, format, platform),
cross-company AND per-tenant, and writes:
  - patterns.json  — the machine-readable knowledge base
  - INSIGHTS.md    — the brief injected into the next generation (the "Improve" step)

Cross-company by design: patterns are feature-level, so a signal learned in
Auri's gold market can bias Vanna's strategy without any tenant fact crossing
over (OKF V6 isolation holds — we share the lesson, never the copy).

    python pipeline/scripts/learn.py
"""

from __future__ import annotations

import json
import re
import statistics
import sys
import time
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import learning as L  # noqa: E402

REPO = HERE.parents[1]
HISTORY = REPO / "pipeline" / "state" / "content_history.json"
TRENDS = REPO / "pipeline" / "state" / "trends"


def ingest_competitive() -> list[dict]:
    items = []
    for jf in sorted(TRENDS.glob("*.json")):
        try:
            data = json.loads(jf.read_text(encoding="utf-8"))
        except Exception:
            continue
        tenant = data.get("tenant", jf.stem.split("-")[0])
        for it in data.get("items", []):
            eng = it.get("engagement")
            if not eng:            # only signals with a real engagement number teach us
                continue
            title = it.get("title", "")
            items.append({
                "kind": "competitive", "tenant_market": tenant, "channel": it.get("channel"),
                "hook_type": L.hook_type(title), "theme": L.theme_bucket("", title),
                "engagement": float(eng), "title": title[:80], "source": it.get("source"),
            })
    return items


def latest_perf_by_post() -> dict:
    latest = {}
    if L.PERF.exists():
        for line in L.PERF.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            latest[row["post_id"]] = row     # last write wins (newest measurement)
    return latest


def ingest_own() -> list[dict]:
    """Own published content: features from history, engagement from performance.jsonl if measured."""
    hist = json.loads(HISTORY.read_text(encoding="utf-8"))
    perf = latest_perf_by_post()
    items = []
    for r in hist:
        out = str(r.get("publish_outcome", ""))
        m = re.search(r"status/(\d+)", out)
        if not m:
            continue
        pid = m.group(1)
        feats = L.features(tenant=r.get("tenant", "vanna"), platform="x",
                           topic=r.get("topic_covered", ""), hook=r.get("hook_shipped", ""),
                           fmt=r.get("format", "stat-card"), arc=r.get("angle_covered", ""))
        eng = None
        if pid in perf:
            eng = perf[pid]["engagement"].get("score")
        items.append({"kind": "own", "post_id": pid, "hook": r.get("hook_shipped", ""),
                      **feats, "engagement": eng})
    return items


def agg(items, dim, value_key="engagement"):
    """Average engagement per value of a feature dimension, with counts."""
    buckets = defaultdict(list)
    for it in items:
        v = it.get(dim)
        e = it.get(value_key)
        if v and e is not None:
            buckets[v].append(e)
    out = []
    for v, xs in buckets.items():
        out.append({"value": v, "n": len(xs), "avg": round(statistics.mean(xs), 1),
                    "max": round(max(xs), 1)})
    return sorted(out, key=lambda x: x["avg"], reverse=True)


def main() -> int:
    L.ensure_store()
    comp = ingest_competitive()
    own = ingest_own()

    # persist a competitive ledger snapshot
    with open(L.COMP, "w", encoding="utf-8") as f:
        for it in comp:
            f.write(json.dumps(it, ensure_ascii=False) + "\n")

    own_measured = [o for o in own if o.get("engagement") is not None]

    patterns = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "n_competitive_signals": len(comp),
        "n_own_posts": len(own),
        "n_own_measured": len(own_measured),
        "market": {
            "by_hook_type": agg(comp, "hook_type"),
            "by_theme": agg(comp, "theme"),
            "by_channel": agg(comp, "channel"),
        },
        "own": {
            "by_hook_type": agg(own_measured, "hook_type"),
            "by_theme": agg(own_measured, "theme"),
            "posts": [{"hook": o["hook"], "tenant": o["tenant"], "hook_type": o["hook_type"],
                       "theme": o["theme"], "engagement": o["engagement"]} for o in own],
        },
    }
    L.PATTERNS.write_text(json.dumps(patterns, indent=2, ensure_ascii=False), encoding="utf-8")

    # ---- INSIGHTS.md : the brief fed back into generation ----
    def table(rows, head):
        if not rows:
            return "_(no data yet)_\n"
        out = f"| {head} | avg engagement | n |\n|---|---|---|\n"
        for r in rows[:6]:
            out += f"| {r['value']} | {r['avg']} | {r['n']} |\n"
        return out

    md = f"""# Content learning — current insights

_Generated {patterns['generated_at']} from {len(comp)} competitor/market signals
and {len(own)} published posts ({len(own_measured)} with measured engagement)._

**How to use this:** these are cross-company, feature-level learnings. Bias the
next generation toward the higher-performing hook types, themes and formats.
They carry no tenant's proprietary claims — safe to apply to every brand.

## What is performing in the MARKET (competitor signal)

By hook type:

{table(patterns['market']['by_hook_type'], 'hook type')}
By theme:

{table(patterns['market']['by_theme'], 'theme')}
By channel:

{table(patterns['market']['by_channel'], 'channel')}
## Our OWN published content

"""
    if own_measured:
        md += "By hook type:\n\n" + table(patterns['own']['by_hook_type'], 'hook type')
        md += "\nBy theme:\n\n" + table(patterns['own']['by_theme'], 'theme')
    else:
        md += ("_Engagement for our own posts is not measured yet — the OpenCLI bridge "
               "was down at last run. Features are logged; run `performance_tracker.py` "
               "when the bridge is up and re-run this. Until then, learnings are "
               "market-driven only._\n\n")
        md += "Posts awaiting measurement:\n\n"
        for o in own:
            md += f"- [{o['tenant']}] {o['hook_type']}/{o['theme']}: \"{o['hook']}\"\n"

    # Recommended biases (the actionable output)
    rec = []
    if patterns['market']['by_hook_type']:
        top = patterns['market']['by_hook_type'][0]['value']
        rec.append(f"Lead with **{top}** hooks — highest market engagement in the set.")
    if patterns['market']['by_theme']:
        tt = patterns['market']['by_theme'][0]['value']
        rec.append(f"**{tt}** is the hottest theme in the market right now — trend-jack it while it's live.")
    rec.append("Keep every claim gated — engagement never overrides the OKF safety rules.")
    md += "\n## Recommended biases for the next generation\n\n" + "\n".join(f"- {r}" for r in rec) + "\n"

    L.INSIGHTS.write_text(md, encoding="utf-8")

    print(f"competitive signals: {len(comp)} | own posts: {len(own)} ({len(own_measured)} measured)")
    print(f"wrote {L.PATTERNS.relative_to(REPO)} and {L.INSIGHTS.relative_to(REPO)}")
    print("\n--- top market signals ---")
    print("hook types:", [f"{r['value']}={r['avg']}" for r in patterns['market']['by_hook_type'][:4]])
    print("themes    :", [f"{r['value']}={r['avg']}" for r in patterns['market']['by_theme'][:4]])
    return 0


if __name__ == "__main__":
    sys.exit(main())
