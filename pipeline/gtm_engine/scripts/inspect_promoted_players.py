"""
Inspect and list the 34 promoted players from Tier 1 checkpoint.
"""
import json
from pathlib import Path

CHECKPOINT_PATH = Path("D:/new orchestration/pipeline/gtm_engine/registry/tier1_checkpoint.jsonl")

FIRST_BATCH = {
    "aave", "morpho", "uniswap", "curve-finance", "hyperliquid",
    "pendle", "lido", "ethena", "credit-coop", "accountable"
}

def main():
    records = []
    if CHECKPOINT_PATH.exists():
        records = [json.loads(l) for l in CHECKPOINT_PATH.read_text(encoding="utf-8").splitlines() if l.strip()]

    # Group by player_id
    players_map = {}
    for r in records:
        pid = r.get("player_id") or r.get("product_slug")
        if pid not in players_map:
            players_map[pid] = r
        else:
            # Aggregate or keep best
            if r.get("passed_tier2") or r.get("has_blog"):
                players_map[pid] = r

    # Filter promoted
    promoted = [p for p in players_map.values() if p.get("passed_tier2") or p.get("has_blog") or p.get("artefacts_90d", 0) >= 4]
    
    # Sort by TVL
    promoted = sorted(promoted, key=lambda x: x.get("tvl_usd", 0.0), reverse=True)

    print(f"Total Unique Protocols in Checkpoint: {len(players_map)}")
    print(f"Total Promoted to Tier 2: {len(promoted)}")

    batch1 = [p for p in promoted if (p.get("player_id") in FIRST_BATCH or p.get("product_slug") in FIRST_BATCH)]
    remaining_24 = [p for p in promoted if (p.get("player_id") not in FIRST_BATCH and p.get("product_slug") not in FIRST_BATCH)][:24]

    print(f"\nBatch 1 Completed ({len(batch1)} players):")
    for p in batch1:
        print(f"  ✓ {p.get('name')} ({p.get('player_id')}) — TVL: ${p.get('tvl_usd', 0):,.0f}")

    print(f"\nRemaining 24 Promoted Players to Process ({len(remaining_24)} players):")
    for idx, p in enumerate(remaining_24, 1):
        print(f"  {idx:2d}. {p.get('name'):28} | ID: {p.get('player_id'):22} | TVL: ${p.get('tvl_usd', 0):>12,.0f} | Blog: {p.get('confirmed_blog_urls', ['—'])[0] if p.get('confirmed_blog_urls') else '—'}")

if __name__ == "__main__":
    main()
