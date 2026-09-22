"""
Phase 19 Audit Script: Rigorously audits the GTM Intelligence Brain database.
Tests data completeness, source validity, arithmetic reconstruction, and timestamp sanity.
"""

import json
import re
from pathlib import Path
from datetime import datetime, timezone

DB_DIR = Path("D:/new orchestration/pipeline/gtm_engine/brain/db")
TODAY = "2026-09-10"


def load_jsonl(filename: str):
    p = DB_DIR / filename
    if not p.exists():
        return []
    with open(p, "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def audit():
    print("================================================================")
    print("🔍 PHASE 19 AUDIT: PROVING THE GTM INTELLIGENCE BRAIN")
    print("================================================================\n")

    findings = {}

    # 1. Are all 10 players really present?
    players = load_jsonl("players.jsonl")
    player_ids = [p["player_id"] for p in players]
    expected_10 = [
        "aave", "morpho", "uniswap", "curve-finance", "hyperliquid",
        "dydx", "pendle", "lido", "ethena", "pareto-credit"
    ]
    missing_players = [p for p in expected_10 if p not in player_ids]
    findings["total_players"] = len(players)
    findings["player_ids"] = player_ids
    findings["missing_players"] = missing_players
    print(f"1. Players Present: {len(players)}/10. Missing from DB: {missing_players}")

    # 2. Are all player facts sourced?
    unsourced_players = []
    for p in players:
        if not p.get("website") and not p.get("twitter_handle"):
            unsourced_players.append(p["player_id"])
    findings["unsourced_players"] = unsourced_players
    print(f"2. Unsourced Players: {len(unsourced_players)}")

    # 3. How many X posts retrieved & classified?
    posts = load_jsonl("posts.jsonl")
    x_observed = [p for p in posts if p.get("evidence_status") == "X_OBSERVED"]
    primary_observed = [p for p in posts if p.get("evidence_status") == "PRIMARY_SOURCE_OBSERVED"]
    findings["total_posts_in_db"] = len(posts)
    findings["x_observed_count"] = len(x_observed)
    findings["primary_observed_count"] = len(primary_observed)
    print(f"3. Posts in DB: {len(posts)} total ({len(x_observed)} X_OBSERVED, {len(primary_observed)} PRIMARY_SOURCE_OBSERVED)")

    # Per-player breakdown
    player_post_counts = {}
    for p in posts:
        pid = p["player_id"]
        player_post_counts[pid] = player_post_counts.get(pid, 0) + 1
    findings["player_post_counts"] = player_post_counts
    print(f"   Breakdown: {player_post_counts}")

    # 4. Can every pattern show >= 2 actual source records?
    patterns = load_jsonl("patterns.jsonl")
    under_evidenced_patterns = []
    for pat in patterns:
        urls = pat.get("sample_urls", [])
        if len(urls) < 2:
            under_evidenced_patterns.append(pat["pattern_id"])
    findings["under_evidenced_patterns"] = under_evidenced_patterns
    print(f"4. Patterns with < 2 source URLs: {under_evidenced_patterns}")

    # 5. Can every recurring series show every occurrence?
    series = load_jsonl("recurring_series.jsonl")
    incomplete_series = []
    for s in series:
        claimed_count = s.get("occurrence_count", 0)
        urls = s.get("source_urls", [])
        if len(urls) < claimed_count:
            incomplete_series.append({
                "series_id": s["series_id"],
                "claimed": claimed_count,
                "verified_urls": len(urls)
            })
    findings["incomplete_series"] = incomplete_series
    print(f"5. Recurring series missing full occurrence URL lists: {len(incomplete_series)}")
    for s in incomplete_series:
        print(f"   • {s['series_id']}: claimed {s['claimed']}, has {s['verified_urls']} URLs")

    # 6. Can every campaign stage point to an actual post?
    campaigns = load_jsonl("campaigns.jsonl")
    unmapped_stages = []
    for camp in campaigns:
        for st in camp.get("stages", []):
            x_u = st.get("x_url")
            p_u = st.get("primary_source_url")
            if (not x_u or x_u == "X_URL_NOT_OBSERVED") and (not p_u or p_u == "NOT_OBSERVED"):
                unmapped_stages.append((camp["campaign_id"], st.get("stage_name")))
    findings["unmapped_campaign_stages"] = unmapped_stages
    print(f"6. Campaign stages missing any source: {unmapped_stages}")

    # 7. Are there any future timestamps?
    future_timestamps = []
    for p in posts:
        d = p.get("date", "")
        if d > TODAY:
            future_timestamps.append((p["post_id"], d))
    findings["future_timestamps"] = future_timestamps
    print(f"7. Future Timestamps (> {TODAY}): {future_timestamps}")

    # 8. Are any X URLs fabricated?
    fabricated_x_urls = []
    for p in posts:
        xu = p.get("x_url")
        if xu and xu != "X_URL_NOT_OBSERVED":
            # Check for dummy IDs like XXXXXXXX or 12345
            if "status/XXXXXXXX" in xu or "status/12345" in xu:
                fabricated_x_urls.append((p["post_id"], xu))
            elif not re.search(r"status/\d{15,22}", xu):
                fabricated_x_urls.append((p["post_id"], xu))
    findings["fabricated_x_urls"] = fabricated_x_urls
    print(f"8. Fabricated / Invalid X URLs: {fabricated_x_urls}")

    # 9. GTM machines underlying evidence
    machines = load_jsonl("gtm_machines.jsonl")
    findings["gtm_machines_count"] = len(machines)
    for m in machines:
        print(f"9. Machine: {m['machine_id']} ({m['name']}) -> {len(m.get('sample_source_urls', []))} URLs")

    # Write audit findings
    out = DB_DIR / "audit_findings.json"
    out.write_text(json.dumps(findings, indent=2), encoding="utf-8")
    print(f"\n💾 Saved full audit findings to {out}")


if __name__ == "__main__":
    audit()
