"""
Test suite verifying vanna_verdict.py and L1_verdict_grounding.
"""

import sys
from pathlib import Path

REPO_ROOT = Path("D:/new orchestration")
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from exporters.notion.vanna_verdict import (
    load_internal_context,
    vanna_verdict,
    L1_verdict_grounding
)

def test_engine():
    print("Testing load_internal_context()...")
    ctx = load_internal_context()
    for k, v in ctx.items():
        print(f"  ✓ Loaded {k:12} ({len(v.splitlines())} lines)")

    test_patterns = [
        {
            "pattern_id": "PAT_MORPHO_EMBED",
            "name": "[Brand] chooses Morpho template",
            "category": "Partnership",
            "pattern": "Fixed headline: '[Brand] chooses Morpho'. Body: TL;DR reach -> role decomposition."
        },
        {
            "pattern_id": "PAT_MORPHO_RECAP",
            "name": "Monthly recap with fixed sections",
            "category": "Narrative / Metrics",
            "pattern": "'The Morpho Effect' — 5-6 titled sections in fixed order."
        },
        {
            "pattern_id": "PAT_TVL_FLOOR",
            "name": "Milestone reframed as a floor",
            "category": "Metrics / Milestones",
            "pattern": "The number is reframed as a floor, never a ceiling — '$5B is the new day one'."
        }
    ]

    print("\nTesting vanna_verdict() with internal context...")
    verdict_records = []
    for pat in test_patterns:
        res = vanna_verdict(pat, ctx)
        verdict_records.append(res)
        print(f"\n--- Pattern: {pat['name']} ---")
        print(f"  Verdict:              {res['verdict']}")
        print(f"  Target Segment:       {res['target_segment']}")
        print(f"  Objection Addressed:  {res['objection_addressed']}")
        print(f"  Positioning Applied:  {res['positioning_applied']}")
        print(f"  Prior Learning:       {res['prior_learning']}")
        print(f"  Blocked By:           {res['blocked_by']}")
        print(f"  Vanna Version:        {res['vanna_version'][:110]}...")

    print("\nTesting L1_verdict_grounding assertion...")
    violations = L1_verdict_grounding(verdict_records)
    print(f"Violations detected: {len(violations)}")
    assert len(violations) == 0, f"Unfounded verdicts found: {violations}"
    print("✅ L1_verdict_grounding assertion passed!")

if __name__ == "__main__":
    test_engine()
