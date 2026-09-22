"""
Diagnostic script to answer all user questions with exact lines, files, and numbers.
"""
import json
from pathlib import Path

SNAP_PATH = Path("D:/new orchestration/pipeline/gtm_engine/registry/defillama_snapshot.json")
ENUM_MAP_PATH = Path("D:/new orchestration/pipeline/gtm_engine/registry/enum_map.tsv")
CHECKPOINT_PATH = Path("D:/new orchestration/pipeline/gtm_engine/registry/tier1_checkpoint.jsonl")

def main():
    print("=== 1. ETHENA LOOKUP ===")
    snap_data = json.loads(SNAP_PATH.read_text(encoding="utf-8"))
    protocols = snap_data.get("protocols", []) if isinstance(snap_data, dict) else snap_data
    ethena_matches = []
    for p in protocols:
        if isinstance(p, dict) and ("ethena" in p.get("name", "").lower() or "ethena" in p.get("slug", "").lower()):
            ethena_matches.append(p)
            print(f"Name: {p.get('name')} | Slug: {p.get('slug')} | Category: {p.get('category')} | TVL: ${p.get('tvl', 0):,.2f} | Parent: {p.get('parentProtocol')}")

    print("\n=== 2. TSV STABLECOINS & RESERVE CURRENCY ===")
    if ENUM_MAP_PATH.exists():
        for line in ENUM_MAP_PATH.read_text(encoding="utf-8").splitlines():
            parts = line.split("\t")
            if len(parts) >= 4 and parts[1] == "STABLECOINS":
                print(f"Raw Cat: {parts[0]:30} | Enum: {parts[1]:15} | Count: {parts[2]:5} | TVL: ${float(parts[3]):,.2f}")

    print("\n=== 3. TIER 1 CHECKPOINT & PROMOTED PLAYERS ===")
    if CHECKPOINT_PATH.exists():
        records = [json.loads(l) for l in CHECKPOINT_PATH.read_text(encoding="utf-8").splitlines() if l.strip()]
        promoted = [r for r in records if r.get("promoted_to_tier2")]
        print(f"Total Tier 1 Scanned Records: {len(records)}")
        print(f"Total Promoted to Tier 2: {len(promoted)}")
        
        # Check Curve occurrences
        curve_records = [r for r in records if "curve" in r.get("player_id", "").lower()]
        print(f"\nCurve records in Tier 1 checkpoint: {len(curve_records)}")
        for cr in curve_records:
            print(f"  Player ID: {cr.get('player_id')} | Name: {cr.get('name')} | Blog confirmed: {cr.get('blog_confirmed')} | URL: {cr.get('blog_url')}")

        # Check Credit Coop & Accountable
        print("\nChecking Credit Coop & Accountable in Tier 1 Checkpoint:")
        for r in records:
            name = r.get("name", "").lower()
            if "credit coop" in name or "accountable" in name:
                print(f"  Found: {r.get('name')} | ID: {r.get('player_id')} | TVL: ${r.get('tvl_usd', 0):,.2f} | Promoted: {r.get('promoted_to_tier2')}")

if __name__ == "__main__":
    main()
