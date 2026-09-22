#!/usr/bin/env python3
"""Test harness demonstrating the Final Reviewer Agent on a deliberately bad case and a pass case."""

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from pipeline.reviewer.reviewer import review_package

def run_tests():
    print("=================================================================")
    print("RUNNING CASE 1: DELIBERATELY BAD CASE (TEMPLATE REPETITION + UNGROUNDED)")
    print("=================================================================")
    
    bad_draft = {
        "final_hook": "Next-gen revolutionary DeFi credit with guaranteed 40% APY!",
        "final_body": "Next-gen revolutionary DeFi credit with guaranteed 40% APY! Vanna eliminates all cross-account contagion completely on Solana with zero risk. Check docs.vanna.finance",
        "visual_brief": {
            "type": "infographic",
            "content_category": "single_stat",
            "headline": "Generic Headline",
            "subhead": "Generic Subtitle",
            "data": [
                {"label": "Metric 1", "value": "100%", "note": "row 1"},
                {"label": "Metric 2", "value": "200%", "note": "row 2"},
                {"label": "Metric 3", "value": "300%", "note": "row 3"}
            ],
            "footer": "docs.vanna.finance"
        }
    }
    
    # We point to a generic placeholder or existing card
    bad_image = REPO_ROOT / "pipeline" / "state" / "temp_rendered.png"
    
    bad_result = review_package(
        draft=bad_draft,
        image_path=bad_image,
        run_id="test-run-deliberately-bad-001"
    )
    
    print("\n--- CASE 1 REVIEW RESULT ---")
    print(json.dumps(bad_result, indent=2))
    
    print("\n" + "=" * 65)
    print("RUNNING CASE 2: HIGH-QUALITY PASS CASE (GROUNDED + GEMINI 3.1 METAPHOR)")
    print("=================================================================")
    
    pass_draft = {
        "final_hook": "Borrowing in DeFi is broken. Overcollateralization forces you to lock $150 to touch $100.",
        "final_body": """Borrowing in DeFi is broken. Overcollateralization forces you to lock $150 to touch $100.

Vanna unlocks up to 10× undercollateralized margin borrowing on Stellar.

Deposit XLM collateral. Select 1× to 10× leverage. Borrow Blend Protocol yield assets (BLUSDC) in a single click.

How capital stays secure:
• Borrowed funds never enter personal custody; they remain sealed in an isolated Margin Account vault.
• The Vanna Risk Engine enforces a continuous Net Health Factor safety rail to prevent bad debt.

Test the live dApp on Stellar: test.stellar.vanna.finance""",
        "visual_brief": {
            "content_category": "PRODUCT",
            "layout_archetype": "mechanism_visualization",
            "headline": "10x Leverage Multiplier & Health Factor Circuit",
            "metaphor": "Crystalline margin account vault with illuminated lavender liquidation rail",
            "footer": "test.stellar.vanna.finance"
        }
    }
    
    pass_image = REPO_ROOT / "pipeline" / "state" / "vanna_competitor_matched_post1.png"
    
    pass_result = review_package(
        draft=pass_draft,
        image_path=pass_image,
        run_id="test-run-verified-pass-001"
    )
    
    print("\n--- CASE 2 REVIEW RESULT ---")
    print(json.dumps(pass_result, indent=2))

if __name__ == "__main__":
    run_tests()
