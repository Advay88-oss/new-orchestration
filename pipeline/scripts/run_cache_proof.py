#!/usr/bin/env python3
"""Run 1 — Cache Proof Benchmark: Phase 5 Collection.
Measures fetch count, cache hits, and duration across Run A (cold) and Run B (warm).
"""

import time
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "pipeline" / "scripts"))

from source_collector import collect_artefact
import content_cache

TARGETS = [
    {"url": "https://docs.vanna.finance", "channel": "DOCS", "published_date": "2026-09-01"},
    {"url": "https://vanna.finance", "channel": "OWNED_BLOG", "published_date": "2026-09-01"},
    {"url": "https://aave.com", "channel": "OWNED_BLOG", "published_date": "2026-09-01"},
    {"url": "https://compound.finance", "channel": "OWNED_BLOG", "published_date": "2026-09-01"},
    {"url": "https://morpho.org", "channel": "OWNED_BLOG", "published_date": "2026-09-01"},
    {"url": "https://curve.fi", "channel": "OWNED_BLOG", "published_date": "2026-09-01"},
    {"url": "https://uniswap.org", "channel": "OWNED_BLOG", "published_date": "2026-09-01"},
    {"url": "https://makerdao.com", "channel": "OWNED_BLOG", "published_date": "2026-09-01"},
    {"url": "https://synthetix.io", "channel": "OWNED_BLOG", "published_date": "2026-09-01"},
    {"url": "https://yearn.fi", "channel": "OWNED_BLOG", "published_date": "2026-09-01"},
]

# 1. Clean cache for these targets to ensure Run A is cold
idx = content_cache._load_index()
target_urls = {t["url"] for t in TARGETS}
cleaned_idx = {k: v for k, v in idx.items() if v.get("url") not in target_urls}
content_cache._save_index(cleaned_idx)

# RUN A (Cold Cache)
start_a = time.time()
fetch_count_a = 0
hits_a = 0
for t in TARGETS:
    res = collect_artefact(t)
    if res["status"] == "FETCHED":
        fetch_count_a += 1
    elif res["status"] in ("SKIP", "RECLASSIFY"):
        hits_a += 1
duration_a = round(time.time() - start_a, 2)

# RUN B (Warm Cache)
start_b = time.time()
fetch_count_b = 0
hits_b = 0
for t in TARGETS:
    res = collect_artefact(t)
    if res["status"] == "FETCHED":
        fetch_count_b += 1
    elif res["status"] in ("SKIP", "RECLASSIFY"):
        hits_b += 1
duration_b = round(time.time() - start_b, 2)

print(f"RUN A: {fetch_count_a} fetched, {hits_a} cache hits, {duration_a}s")
print(f"RUN B: {fetch_count_b} fetched, {hits_b} cache hits, {duration_b}s")
saving = round((1 - (duration_b / duration_a if duration_a else 1)) * 100, 1)
print(f"SAVING: {saving}% time reduction, {hits_b}/{len(TARGETS)} fetches eliminated")
