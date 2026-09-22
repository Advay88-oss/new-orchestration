"""
Generate Step 1 Shortlist and Step 2 Growth Lever Classification for Undercategorized Competitors.
"""

import json
from pathlib import Path
from collections import Counter

REPO_ROOT = Path("D:/new orchestration")
SNAP_FILE = REPO_ROOT / "pipeline" / "gtm_engine" / "registry" / "defillama_snapshot.json"
CHECKPOINT_FILE = REPO_ROOT / "pipeline" / "gtm_engine" / "registry" / "tier1_checkpoint.jsonl"

protocols = json.loads(SNAP_FILE.read_text(encoding="utf-8"))
if isinstance(protocols, dict):
    protocols = protocols.get("protocols", [])

# Candidates selection:
# 1. Gearbox (Classic undercategorized margin/credit account protocol sitting in standard Lending)
# 2. Contango (Looping / perps via lending, sitting in Derivatives)
# 3. Sentiment (Undercollateralized margin borrowing)
# 4. Credit Coop (Uncollateralized lending outlier)
# 5. Accountable (Corporate credit telemetry outlier)
# 6. Pareto Credit (Category TVL leader)
# 7. Wildcat Protocol (Undercollateralized institutional vaults)
# 8. Kasu (Private credit)
# 9. 3Jane Lending (Undercollateralized crypto native lending)
# 10. Blend Pools V2 (Vanna's core Soroban lending integration target)
# 11. Aquarius Stellar (Vanna's core Soroban DEX integration target)
# 12. Soroswap (Soroban AMM swap router)
# 13. Huma Finance V2 (Stellar RWA credit line)
# 14. Upshift (Onchain capital allocator on Stellar)
# 15. Clearpool (Uncollateralized institutional borrower pools)

TARGET_SLUGS = [
    "gearbox", "contango", "sentiment", "credit-coop", "accountable",
    "pareto-credit", "wildcat-protocol", "kasu", "3jane-lending",
    "blend-pools-v2", "aquarius-stellar", "soroswap", "huma-finance-v2",
    "upshift", "clearpool-lending"
]

shortlist = []
for p in protocols:
    slug = p.get("slug")
    if slug in TARGET_SLUGS:
        shortlist.append(p)

print(f"Total shortlisted candidates found: {len(shortlist)}")
for s in sorted(shortlist, key=lambda x: x.get("tvl") or 0.0, reverse=True):
    print(f"  • {s.get('name'):24} | Cat: {s.get('category'):24} | TVL: ${s.get('tvl', 0):>12,.2f} | Slug: {s.get('slug')}")
