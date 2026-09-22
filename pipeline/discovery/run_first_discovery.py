#!/usr/bin/env python3
"""Run First Discovery Cycle on axis 'chain:stellar' (run_first_discovery.py).

Implements Part C:
  1. Load seen registry players
  2. Screen axis chain:stellar from defillama_snapshot.json
  3. Exclude, enrich candidates with live HTTP HEAD verification
  4. Assert novelty and evidence completeness
  5. Append to registry/discovery_log.jsonl
  6. Emit full deterministic report
"""

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from pipeline.discovery.discovery_engine import (
    load_all_registry_players,
    next_axis,
    verify_url_head,
    assert_discovery_novelty,
    assert_evidence_complete,
    append_discovery_log,
    SNAPSHOT_PATH,
    REGISTRY_DIR
)


def run_stellar_discovery():
    axis = "chain:stellar"
    print("=" * 80)
    print(f"🚀 EXECUTING DISCOVERY RUN: {axis}")
    print("=" * 80)

    # 1. Load seen players
    seen = load_all_registry_players()
    print(f"Known players in registry before run: {len(seen)}")

    # 2. Load DefiLlama snapshot
    if not SNAPSHOT_PATH.exists():
        raise FileNotFoundError(f"Missing snapshot: {SNAPSHOT_PATH}")
    snapshot = json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))
    protocols = snapshot.get("protocols", [])
    snapshot_date = snapshot.get("snapshot_day", "2026-09-10")

    # 3. Screen axis: chain:stellar
    stellar_candidates = [p for p in protocols if "Stellar" in (p.get("chains") or [])]
    total_screened = len(stellar_candidates)
    print(f"Candidates screened on axis '{axis}': {total_screened}")

    # Calculate ecosystem totals
    combined_tvl = 0.0
    for p in stellar_candidates:
        c_tvls = p.get("chainTvls") or {}
        st_tvl = c_tvls.get("Stellar")
        if st_tvl is not None:
            combined_tvl += float(st_tvl)
        else:
            combined_tvl += float(p.get("tvl") or 0.0)

    # Specific checks for Blend & Aquarius
    blend_info = [p for p in stellar_candidates if "blend" in p.get("slug", "").lower()]
    aqua_info = [p for p in stellar_candidates if "aquarius" in p.get("slug", "").lower() or "aqua" in p.get("slug", "").lower()]

    # 4. Exclude and Enrich candidates
    records = []
    quarantine = []
    excluded_count = 0
    urls_checked = 0
    urls_resolved = 0
    unknown_fields_count = 0

    for cand in stellar_candidates:
        raw_slug = cand.get("slug") or cand.get("name", "").lower().replace(" ", "-")
        player_id = raw_slug.lower().strip()

        # Check if already covered
        if player_id in seen or cand.get("name", "").lower().strip() in seen:
            excluded_count += 1
            continue

        category = cand.get("category", "Uncategorized")
        name = cand.get("name", player_id)
        description = cand.get("description", "")
        website = cand.get("url", "").strip() if cand.get("url") else None
        twitter_handle = cand.get("twitter")
        twitter = f"@{twitter_handle.strip().lstrip('@')}" if twitter_handle else None

        # Stellar specific TVL resolution
        c_tvls = cand.get("chainTvls") or {}
        tvl = c_tvls.get("Stellar")
        if tvl is None:
            tvl = cand.get("tvl")
        tvl_usd = round(float(tvl), 2) if tvl is not None else None

        # Verify Website URL via HTTP HEAD
        website_probe = "NO_URL"
        if website:
            urls_checked += 1
            ok, code, status_str = verify_url_head(website)
            if ok:
                urls_resolved += 1
                website_probe = "CONFIRMED_200"
            else:
                website_probe = f"DEAD_{code}" if code else "DEAD"
        else:
            unknown_fields_count += 1

        if not twitter:
            unknown_fields_count += 1
        if tvl_usd is None:
            unknown_fields_count += 1

        # Classify Relevance to Vanna Protocol
        cat_low = category.lower()
        desc_low = description.lower()
        relevance = "NOT_RELEVANT"
        why = ""
        why_evidence = []

        if cat_low == "cex":
            relevance = "NOT_RELEVANT"
            why = "Centralized custodial exchange with no composable on-chain credit interfaces"
            why_evidence = ["@url:`https://api.llama.fi/protocols`"]
        elif "lending" in cat_low or "borrow" in desc_low or "margin" in desc_low:
            relevance = "MECHANISM"
            why = f"Direct money market/lending mechanism on Stellar Soroban ({category})"
            why_evidence = ["@url:`https://api.llama.fi/protocols`"]
            if website and website_probe == "CONFIRMED_200":
                why_evidence.append(f"@url:`{website}`")
        elif "dex" in cat_low or "amm" in desc_low or "swap" in desc_low:
            relevance = "AUDIENCE"
            why = f"Decentralized liquidity venue — candidate integration target for Vanna SmartAccount credit routing ({category})"
            why_evidence = ["@url:`https://api.llama.fi/protocols`"]
            if website and website_probe == "CONFIRMED_200":
                why_evidence.append(f"@url:`{website}`")
        elif "basis" in desc_low or "derivative" in cat_low or "perp" in desc_low:
            relevance = "GTM_PATTERN"
            why = f"Basis trading and structured leverage yield mechanisms on Soroban ({category})"
            why_evidence = ["@url:`https://api.llama.fi/protocols`"]
            if website and website_probe == "CONFIRMED_200":
                why_evidence.append(f"@url:`{website}`")
        elif "rwa" in cat_low or "rwa" in desc_low:
            relevance = "ADJACENT"
            why = f"Real-World Asset tokenization running on Stellar with secondary credit demand potential"
            why_evidence = ["@url:`https://api.llama.fi/protocols`"]
        elif "insurance" in cat_low or "backstop" in desc_low:
            relevance = "RISK_MODEL"
            why = f"Backstop pool and insolvency risk mitigation mechanism"
            why_evidence = ["@url:`https://api.llama.fi/protocols`"]
        else:
            relevance = "ADJACENT"
            why = f"Ecosystem infrastructure on Stellar ({category})"
            why_evidence = ["@url:`https://api.llama.fi/protocols`"]

        evidence_tier = "OBSERVED" if (website_probe == "CONFIRMED_200" or website_probe == "NO_URL") else "UNKNOWN"

        rec = {
            "player_id": player_id,
            "name": name,
            "discovery_axis": axis,
            "run_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "tvl_usd": tvl_usd,
            "tvl_source": "@url:`https://api.llama.fi/protocols`",
            "snapshot_date": snapshot_date,
            "category_raw": category,
            "twitter": twitter,
            "twitter_source": "@url:`https://api.llama.fi/protocols`" if twitter else None,
            "website": website,
            "website_probe_status": website_probe,
            "confirmed_blog_urls": [],
            "confirmed_forum_urls": [],
            "probe_status": "PROBED",
            "relevance": relevance,
            "why": why,
            "why_evidence": why_evidence,
            "evidence_tier": evidence_tier,
            "derived_by": "code"
        }

        # Check quarantine
        if website_probe.startswith("DEAD"):
            rec["evidence_tier"] = "UNKNOWN"
            rec["quarantine_reason"] = f"unresolvable: {website}"
            quarantine.append(rec)
        else:
            records.append(rec)

    # 5. Assertions
    new_players = assert_discovery_novelty(records + quarantine, seen, axis)
    bad_evidence = assert_evidence_complete(records)
    if bad_evidence:
        raise ValueError(f"Evidence assertion failed: {bad_evidence}")

    resolution_rate = (urls_resolved / urls_checked * 100.0) if urls_checked > 0 else 100.0
    relevant_count = len([r for r in records if r["relevance"] != "NOT_RELEVANT"])

    # 6. Write discovery log entry
    log_entry = append_discovery_log(
        discovery_axis=axis,
        candidates_screened=total_screened,
        already_seen_excluded=excluded_count,
        new_players_found=len(new_players),
        relevant=relevant_count,
        urls_checked=urls_checked,
        urls_resolved=urls_resolved,
        unknown_fields=unknown_fields_count
    )

    # 7. Write discovered records to registry/discovered_players.jsonl
    disc_file = REGISTRY_DIR / "discovered_players.jsonl"
    with open(disc_file, "a", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")

    return {
        "axis": axis,
        "total_screened": total_screened,
        "excluded_count": excluded_count,
        "new_players_count": len(new_players),
        "records": records,
        "quarantine": quarantine,
        "combined_tvl": combined_tvl,
        "blend_info": blend_info,
        "aqua_info": aqua_info,
        "urls_checked": urls_checked,
        "urls_resolved": urls_resolved,
        "resolution_rate": resolution_rate,
        "unknown_fields_count": unknown_fields_count,
        "log_entry": log_entry,
        "total_registry_players": len(seen) + len(new_players)
    }


if __name__ == "__main__":
    res = run_stellar_discovery()
    print("\n✅ DISCOVERY RUN FINISHED SUCCESSFULLY!")
    print(json.dumps(res["log_entry"], indent=2))
