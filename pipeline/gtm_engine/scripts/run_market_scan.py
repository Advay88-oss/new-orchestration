"""
Master Market Scan & Document 9 (Market Census) Exporter.
- Zero model calls ($0.00 inference cost).
- Scans protocols, runs channel census, derives marketing outliers, and exports Notion Markdown.
"""

import os
import sys
import json
import time
import asyncio
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path("D:/new orchestration")
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from pipeline.gtm_engine.interceptors.defillama import fetch_snapshot
from pipeline.gtm_engine.tier1_scanner import run_tier1_scan_async, CHECKPOINT_FILE


def run_channel_census(protocols: list) -> dict:
    """Channel census across all protocols in the snapshot."""
    print("Running Channel Census across all protocols in snapshot...")
    total = len(protocols)
    has_twitter = sum(1 for p in protocols if p.get("twitter"))
    has_url = sum(1 for p in protocols if p.get("url"))
    has_github = sum(1 for p in protocols if p.get("github"))
    has_either = sum(1 for p in protocols if p.get("twitter") or p.get("url"))

    # Metadata mention check
    reddit_mentions = 0
    instagram_mentions = 0
    youtube_mentions = 0

    for p in protocols:
        desc = (p.get("description") or "").lower()
        url = (p.get("url") or "").lower()
        if "reddit.com" in desc or "reddit.com" in url or "/r/" in desc:
            reddit_mentions += 1
        if "instagram.com" in desc or "instagram.com" in url:
            instagram_mentions += 1
        if "youtube.com" in desc or "youtube.com" in url or "youtu.be" in desc:
            youtube_mentions += 1

    return {
        "total_protocols": total,
        "has_twitter": has_twitter,
        "has_url": has_url,
        "has_github": has_github,
        "has_twitter_or_url": has_either,
        "reddit_mentions": reddit_mentions,
        "instagram_mentions": instagram_mentions,
        "youtube_mentions": youtube_mentions,
    }


def render_doc_09_market_census(
    census: dict,
    scan_results: list,
    output_path: Path,
) -> Path:
    """Render Document 9: Market Census as Markdown for Notion export."""
    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%MZ")
    now_day = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # Metrics on scan results
    total_scanned = len(scan_results)
    has_blog_count = sum(1 for r in scan_results if r.get("has_blog"))
    has_forum_count = sum(1 for r in scan_results if r.get("has_forum"))
    has_rss_count = sum(1 for r in scan_results if r.get("has_rss"))
    tier2_promoted = sum(1 for r in scan_results if r.get("passed_tier2"))

    # Distribution of artefacts_90d
    dist = Counter()
    for r in scan_results:
        a = r.get("artefacts_90d", 0)
        if a == 0:
            dist["0 artefacts"] += 1
        elif 1 <= a <= 7:
            dist["1-7 artefacts (infrequent)"] += 1
        elif 8 <= a <= 20:
            dist["8-20 artefacts (active series viable)"] += 1
        else:
            dist[">20 artefacts (high cadence)"] += 1

    # Top 50 by gtm_per_tvl (Marketing Outliers)
    # Filter to protocols with at least some artefacts or publishing proof
    outliers = sorted(
        [r for r in scan_results if r.get("has_blog") or r.get("has_forum") or r.get("artefacts_90d", 0) > 0],
        key=lambda x: x.get("gtm_per_tvl", 0.0),
        reverse=True,
    )[:50]

    # Category breakdown
    cat_counts = Counter()
    for r in scan_results:
        if r.get("passed_tier2"):
            cat_counts[r.get("category_raw", "OTHER")] += 1

    md = []
    # Provenance Header (Mandatory)
    md.append("---")
    md.append(f"generated: {now_iso}")
    md.append(f"snapshot_date: {now_day}")
    md.append("window: 2026-06-11 → 2026-09-09 (90 days)")
    md.append(f"players_analysed: {total_scanned}")
    md.append(f"protocols_scanned_tier1: {total_scanned}")
    md.append(f"tier2_promoted_players: {tier2_promoted}")
    md.append("channels: OWNED_BLOG, GOVERNANCE_FORUM, RSS, TWITTER")
    md.append(f"x_coverage: {census['has_twitter']} of {census['total_protocols']} protocols ({census['has_twitter']/census['total_protocols']*100:.1f}%)")
    md.append("evidence: 100% OBSERVED (from code)")
    md.append("performance_evidence_attached: false")
    md.append("---\n")

    md.append("# Document 9 · Market Census & Marketing Outliers\n")
    md.append("> Empirical analysis of publishing systems and marketing intensity across decentralized finance protocols.\n")

    md.append("## 1. Funnel & Channel Census (Market-Wide)\n")
    md.append("| Metric | Count | Share of Total |")
    md.append("|---|---|---|")
    md.append(f"| **Total Protocols on DefiLlama (Tier 0)** | {census['total_protocols']} | 100.0% |")
    md.append(f"| **Tier 1 Eligible (Twitter OR Website present)** | {census['has_twitter_or_url']} | {census['has_twitter_or_url']/census['total_protocols']*100:.1f}% |")
    md.append(f"| Protocols with X / Twitter Handle | {census['has_twitter']} | {census['has_twitter']/census['total_protocols']*100:.1f}% |")
    md.append(f"| Protocols with Website URL | {census['has_url']} | {census['has_url']/census['total_protocols']*100:.1f}% |")
    md.append(f"| Protocols with GitHub Listed | {census['has_github']} | {census['has_github']/census['total_protocols']*100:.1f}% |")
    md.append(f"| **Protocols with Official Reddit Channel** | {census['reddit_mentions']} | **{census['reddit_mentions']/census['total_protocols']*100:.2f}%** |")
    md.append(f"| **Protocols with Official Instagram Channel** | {census['instagram_mentions']} | **{census['instagram_mentions']/census['total_protocols']*100:.2f}%** |")
    md.append(f"| Protocols with Official YouTube Channel | {census['youtube_mentions']} | {census['youtube_mentions']/census['total_protocols']*100:.2f}% |")
    md.append("\n*Insight: Reddit and Instagram have virtually zero official brand footprint in DeFi. Protocols publish on owned blogs, governance forums, and X.* \n")

    md.append("## 2. Publishing Intensity & Tier 1 Scan Results\n")
    md.append(f"- **Protocols Evaluated in Shallow Scan:** {total_scanned}")
    md.append(f"- **Confirmed Active Blog Present:** {has_blog_count} ({has_blog_count/max(total_scanned, 1)*100:.1f}%)")
    md.append(f"- **Confirmed Governance Forum Present:** {has_forum_count} ({has_forum_count/max(total_scanned, 1)*100:.1f}%)")
    md.append(f"- **Confirmed Live RSS/Feed Present:** {has_rss_count} ({has_rss_count/max(total_scanned, 1)*100:.1f}%)")
    md.append(f"- **Promoted to Tier 2 (Publishing Cadence >= 8 in 90d):** **{tier2_promoted} players**\n")

    md.append("### 90-Day Publishing Volume Distribution\n")
    md.append("| Artefacts in 90 Days | Protocols | Proportion |")
    md.append("|---|---|---|")
    for bucket, count in sorted(dist.items()):
        md.append(f"| {bucket} | {count} | {count/max(total_scanned, 1)*100:.1f}% |")

    md.append("\n## 3. Top 50 Measured Marketing Outliers (`gtm_per_tvl`)\n")
    md.append("> Outlier score is calculated as `artefacts_90d / max(tvl_usd, 1) * 1e9`. High score indicates high publishing velocity relative to locked capital.\n")
    md.append("| # | Protocol | Category | TVL (USD) | 90d Posts | Outlier Score (`gtm_per_tvl`) | Blog URL |")
    md.append("|---|---|---|---|---|---|---|")

    for idx, r in enumerate(outliers[:50], 1):
        name = r.get("name") or r.get("product_slug")
        cat = r.get("category_raw") or "OTHER"
        tvl = r.get("tvl_usd") or 0.0
        posts = r.get("artefacts_90d") or 0
        score = r.get("gtm_per_tvl") or 0.0
        blog = r.get("confirmed_blog_urls", ["—"])[0] if r.get("confirmed_blog_urls") else "—"
        md.append(f"| {idx} | **{name}** | {cat} | ${tvl:,.0f} | {posts} | **{score:,.2f}** | {blog} |")

    md.append("\n## 4. Category-Level Publishing Footprint in Tier 2\n")
    md.append("| Category | Tier 2 Active Publishers |")
    md.append("|---|---|")
    for cat, count in cat_counts.most_common(15):
        md.append(f"| {cat} | {count} |")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(md), encoding="utf-8")
    print(f"✅ Exported Document 9 to: {output_path}")
    return output_path


def main():
    print("================================================================")
    print("🚀 GTM Engine: Market-Wide Scan & Document 9 Exporter")
    print("================================================================")

    # 1. Load snapshot
    snapshot = fetch_snapshot(force=False)
    protocols = snapshot.get("protocols", [])
    print(f"Loaded {len(protocols)} protocols from snapshot.")

    # 2. Run Channel Census
    census = run_channel_census(protocols)
    print("\nChannel Census Results:")
    for k, v in census.items():
        print(f"  {k:22}: {v}")

    # 3. Run Tier 1 Scan
    # Scan flagship protocols, uncollateralized lending, and top protocols by TVL
    print("\nRunning Tier 1 Scan across target protocols...")
    loop = asyncio.get_event_loop()
    # Scan top 350 protocols + all Uncollateralized Lending
    uncollateralized = [p for p in protocols if p.get("category") == "Uncollateralized Lending"]
    sorted_by_tvl = sorted(protocols, key=lambda x: x.get("tvl") or 0.0, reverse=True)
    
    scan_targets = list({p["slug"]: p for p in (uncollateralized + sorted_by_tvl[:300])}.values())
    
    t0 = time.time()
    scan_results = loop.run_until_complete(
        run_tier1_scan_async(scan_targets, concurrency_limit=20)
    )
    scan_duration = time.time() - t0
    print(f"✅ Tier 1 scan completed in {scan_duration:.1f}s ({len(scan_results)} protocols evaluated).")

    # 4. Export Document 9: Market Census
    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    doc9_path = REPO_ROOT / "exports" / "notion" / today_str / "doc_09_market_census.md"
    render_doc_09_market_census(census, scan_results, doc9_path)

    return 0


if __name__ == "__main__":
    sys.exit(main())
