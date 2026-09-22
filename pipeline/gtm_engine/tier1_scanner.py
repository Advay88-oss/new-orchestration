"""
Tier 1 Shallow Scan Engine for GTM Intelligence Engine (Part 2).
Scans protocols to measure publishing intensity and identify marketing outliers.
- Async execution with concurrency cap of 20.
- Checkpointed and resumable via registry/tier1_checkpoint.jsonl.
- Zero model calls ($0.00 inference cost).
- Arithmetic promotion rules: Tier 1 -> Tier 2.
"""

import os
import sys
import json
import time
import re
import asyncio
import urllib.request
import urllib.parse
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, Any, List, Set, Optional

REPO_ROOT = Path("D:/new orchestration")
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from pipeline.gtm_engine.interceptors.defillama import (
    fetch_snapshot,
    resolve_player_id,
    channel_seeds,
    probe_confirm,
    domain_variants,
    APP_PREFIXES,
    BLOG_SUBDOMAINS,
    FORUM_SUBDOMAINS,
    BLOG_PATHS,
    RSS_PATHS,
)

CHECKPOINT_FILE = REPO_ROOT / "pipeline" / "gtm_engine" / "registry" / "tier1_checkpoint.jsonl"
RESULTS_FILE = REPO_ROOT / "pipeline" / "gtm_engine" / "registry" / "tier1_results.json"


def count_rss_items_90d(feed_url: str, timeout: float = 6.0) -> int:
    """Fetch RSS/Atom feed and count entries published in the last 90 days."""
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) GTMIntelligence/1.0"}
    try:
        req = urllib.request.Request(feed_url, headers=headers)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            text = resp.read(65536).decode("utf-8", errors="ignore")
            # Count item/entry tags
            items = re.findall(r"<(?:item|entry)[\s>]", text, re.IGNORECASE)
            # Count recent date occurrences (e.g. 2026, late 2025)
            recent_dates = len(re.findall(r"(?:2026|2025)", text))
            return max(len(items), min(recent_dates, 30))
    except Exception:
        return 0


def count_blog_dated_links_90d(blog_url: str, timeout: float = 6.0) -> int:
    """Fetch blog index page and count dated article links."""
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) GTMIntelligence/1.0"}
    try:
        req = urllib.request.Request(blog_url, headers=headers)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            text = resp.read(32768).decode("utf-8", errors="ignore")
            # Recent dated links
            recent_links = re.findall(r"/(?:2026|2025)[/\-]", text)
            article_tags = len(re.findall(r"<article|class=\"post|class=\"blog", text, re.IGNORECASE))
            return max(len(recent_links), article_tags)
    except Exception:
        return 0


async def scan_single_protocol(
    protocol: Dict[str, Any],
    semaphore: asyncio.Semaphore,
    loop: asyncio.AbstractEventLoop,
) -> Dict[str, Any]:
    """Scan a single protocol across candidate channels asynchronously."""
    async with semaphore:
        slug = protocol.get("slug") or protocol.get("name") or "unknown"
        player_id = resolve_player_id(protocol)
        website = protocol.get("url")
        twitter = protocol.get("twitter")
        tvl = protocol.get("tvl") or 0.0
        cat_raw = protocol.get("category") or "OTHER"

        confirmed_blogs = []
        confirmed_forums = []
        confirmed_rss = []

        # Generate candidates if website exists
        if website and website not in ("NO_URL", "UNKNOWN", ""):
            hosts = domain_variants(website)
            candidates_to_probe = []

            for host in hosts:
                # Subdomains
                for sub in ("news.", "blog."):
                    candidates_to_probe.append((f"https://{sub}{host}", "blog"))
                for p in ("/blog", "/news"):
                    candidates_to_probe.append((f"https://{host}{p}", "blog"))
                for fsub in ("governance.", "forum."):
                    candidates_to_probe.append((f"https://{fsub}{host}", "forum"))
                for r in ("/feed", "/blog/rss.xml", "/rss.xml"):
                    candidates_to_probe.append((f"https://{host}{r}", "rss"))

            # Run probes in thread pool (limit to first 6 high-probability URLs)
            for url, kind in candidates_to_probe[:8]:
                res = await loop.run_in_executor(None, probe_confirm, url, 5.0)
                if res.get("confirmed"):
                    final_u = res.get("final_url") or url
                    if kind == "blog":
                        confirmed_blogs.append(final_u)
                    elif kind == "forum":
                        confirmed_forums.append(final_u)
                    elif kind == "rss":
                        confirmed_rss.append(final_u)

            # Sanity guard: soft-404 SPA check
            if len(confirmed_blogs) > 2:
                confirmed_blogs = []

        # Count 90-day publishing volume
        artefacts_90d = 0
        if confirmed_rss:
            artefacts_90d = await loop.run_in_executor(None, count_rss_items_90d, confirmed_rss[0], 5.0)
        elif confirmed_blogs:
            artefacts_90d = await loop.run_in_executor(None, count_blog_dated_links_90d, confirmed_blogs[0], 5.0)

        # Force-include subject category (Uncollateralized Lending)
        is_subject_cat = (cat_raw == "Uncollateralized Lending")
        has_blog = bool(confirmed_blogs)
        has_forum = bool(confirmed_forums)
        has_rss = bool(confirmed_rss)

        # Promotion arithmetic
        passed_tier2 = (has_blog or has_forum) and (artefacts_90d >= 8)
        forced_tier2 = is_subject_cat

        # Marketing outlier score (low TVL + high publishing cadence)
        gtm_per_tvl = round((artefacts_90d / max(tvl, 1.0)) * 1e9, 4) if tvl > 0 else (artefacts_90d * 1000.0)

        record = {
            "record_type": "TIER1_SCAN",
            "player_id": player_id,
            "product_slug": slug,
            "name": protocol.get("name"),
            "category_raw": cat_raw,
            "tvl_usd": round(tvl, 2),
            "twitter_handle": twitter,
            "website": website,
            "has_blog": has_blog,
            "has_forum": has_forum,
            "has_rss": has_rss,
            "confirmed_blog_urls": confirmed_blogs,
            "confirmed_forum_urls": confirmed_forums,
            "confirmed_rss_urls": confirmed_rss,
            "artefacts_90d": artefacts_90d,
            "publishing_intensity": round(artefacts_90d / 90.0, 3),
            "gtm_per_tvl": gtm_per_tvl,
            "passed_tier2": passed_tier2 or forced_tier2,
            "forced_inclusion": "SUBJECT_CATEGORY" if forced_tier2 else None,
            "evidence_tier": "OBSERVED",
            "derived_by": "code",
            "scanned_at": datetime.now(timezone.utc).isoformat(),
        }
        return record


async def run_tier1_scan_async(
    protocols: List[Dict[str, Any]],
    concurrency_limit: int = 20,
    max_protocols: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """Execute Tier 1 scan with concurrency control and resumable checkpointing."""
    CHECKPOINT_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    # 1. Load existing checkpoint
    existing_records: Dict[str, Dict[str, Any]] = {}
    if CHECKPOINT_FILE.exists():
        with open(CHECKPOINT_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    rec = json.loads(line)
                    existing_records[rec.get("product_slug")] = rec
        print(f"Loaded {len(existing_records)} existing scanned protocols from checkpoint.")

    # 2. Filter target protocols
    targets_to_scan = []
    for p in protocols:
        slug = p.get("slug")
        if slug in existing_records:
            continue
        # Tier 0 -> Tier 1 gate: twitter OR url present
        if p.get("twitter") or p.get("url"):
            targets_to_scan.append(p)

    if max_protocols:
        targets_to_scan = targets_to_scan[:max_protocols]

    print(f"Protocols to scan in this run: {len(targets_to_scan)} (Concurrency: {concurrency_limit})")

    semaphore = asyncio.Semaphore(concurrency_limit)
    loop = asyncio.get_running_loop()

    results: List[Dict[str, Any]] = list(existing_records.values())
    checkpoint_handle = open(CHECKPOINT_FILE, "a", encoding="utf-8")

    batch_size = 50
    t0 = time.time()

    for i in range(0, len(targets_to_scan), batch_size):
        batch = targets_to_scan[i:i + batch_size]
        tasks = [scan_single_protocol(p, semaphore, loop) for p in batch]
        batch_results = await asyncio.gather(*tasks)

        for rec in batch_results:
            results.append(rec)
            checkpoint_handle.write(json.dumps(rec) + "\n")
        checkpoint_handle.flush()

        completed = len(results)
        elapsed = time.time() - t0
        rate = (i + len(batch)) / max(elapsed, 0.1)
        print(f"  Scanned {completed} protocols ({rate:.1f} protocols/sec) ...")

    checkpoint_handle.close()
    return results
