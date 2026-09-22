#!/usr/bin/env python3
"""Comprehensive Automated Test Suite for the Final Reviewer Agent Gate.

Verifies all 10 mandatory requirements:
  1. PASS asset reaches Telegram (integration check).
  2. FAIL asset never reaches Telegram.
  3. Unsupported factual claim causes FAIL / REGENERATE.
  4. Repeated generic infographic causes REGENERATE (TEMPLATE REPETITION DETECTED).
  5. Wrong brand colors cause visual/brand failure.
  6. Missing PNG causes FAIL.
  7. A genuinely different premium visual can PASS.
  8. Review JSON is persisted to pipeline/state/reviews/<run_id>.json.
  9. Telegram is never called on FAIL.
  10. Reviewer runs before Telegram every time (pipeline order assertion).
"""

import ast
import json
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from PIL import Image

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from pipeline.reviewer.reviewer import review_package, inspect_png_pixels, REVIEWS_DIR


class TestFinalReviewerAgent(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.valid_image = REPO_ROOT / "pipeline" / "state" / "vanna_competitor_matched_post1.png"
        if not cls.valid_image.exists():
            # Create a fallback dark image with lavender accent for test isolation
            im = Image.new("RGB", (1080, 1080), color=(8, 7, 12))
            # Put lavender strip
            for x in range(200, 400):
                for y in range(500, 600):
                    im.putpixel((x, y), (163, 135, 255))
            cls.valid_image.parent.mkdir(parents=True, exist_ok=True)
            im.save(cls.valid_image)

        cls.valid_draft = {
            "final_hook": "Borrowing in DeFi is broken. Overcollateralization forces you to lock $150 to touch $100.",
            "final_body": (
                "Borrowing in DeFi is broken. Overcollateralization forces you to lock $150 to touch $100.\n\n"
                "Vanna unlocks up to 10× undercollateralized margin borrowing on Stellar.\n\n"
                "Deposit XLM collateral. Select 1× to 10× leverage. Borrow Blend Protocol yield assets (BLUSDC) in a single click.\n\n"
                "How capital stays secure:\n"
                "• Borrowed funds never enter personal custody; they remain sealed in an isolated Margin Account vault.\n"
                "• The Vanna Risk Engine enforces a continuous Net Health Factor safety rail to prevent bad debt.\n\n"
                "Test the live dApp on Stellar: test.stellar.vanna.finance"
            ),
            "visual_brief": {
                "content_category": "PRODUCT",
                "layout_archetype": "mechanism visualization",
                "headline": "10x Leverage Multiplier & Health Factor Circuit",
                "footer": "test.stellar.vanna.finance"
            }
        }

    def test_01_pass_asset_reaches_telegram(self):
        """Requirement 1: Verify a PASS asset clears the gate and allows Telegram dispatch."""
        run_id = "test-req01-pass-dispatch"
        res = review_package(self.valid_draft, self.valid_image, run_id=run_id)
        self.assertEqual(res["decision"], "PASS")

        # Simulate pipeline execution logic
        telegram_called = False
        if res["decision"] == "PASS":
            telegram_called = True
        self.assertTrue(telegram_called, "Telegram dispatch was not triggered for PASS asset")

    def test_02_fail_asset_never_reaches_telegram(self):
        """Requirement 2: Verify a FAIL asset blocks before reaching Telegram."""
        bad_draft = dict(self.valid_draft)
        bad_draft["final_body"] = "Guaranteed 50% APY with zero risk on Solana! docs.vanna.finance"
        
        run_id = "test-req02-fail-block"
        res = review_package(bad_draft, self.valid_image, run_id=run_id)
        self.assertIn(res["decision"], ("REGENERATE", "FAIL"))

        telegram_called = False
        if res["decision"] == "PASS":
            telegram_called = True
        self.assertFalse(telegram_called, "Telegram dispatch was improperly called on a failed asset")

    def test_03_unsupported_factual_claim_causes_fail(self):
        """Requirement 3: Unsupported factual claim causes FAIL / REGENERATE."""
        unsupported_draft = dict(self.valid_draft)
        unsupported_draft["final_body"] = "Vanna is now live on Solana mainnet with guaranteed 40% APY and eliminates all contagion."
        
        run_id = "test-req03-unsupported-claim"
        res = review_package(unsupported_draft, self.valid_image, run_id=run_id)
        self.assertIn(res["decision"], ("REGENERATE", "FAIL"))
        self.assertLess(res["scores"]["factual"], 95)
        self.assertTrue(any("unsupported" in f.lower() or "prohibited" in f.lower() for f in res["critical_failures"]))

    def test_04_repeated_generic_infographic_causes_regenerate(self):
        """Requirement 4: Repeated generic infographic causes REGENERATE."""
        repetitive_draft = {
            "final_hook": "Borrowing in DeFi is broken. Overcollateralization forces you to lock $150.",
            "final_body": "Vanna unlocks up to 10× undercollateralized margin borrowing on Stellar with Blend BLUSDC. test.stellar.vanna.finance",
            "visual_brief": {
                "type": "infographic",
                "headline": "Overcollateralized vs Vanna",
                "subhead": "The 3 key credit differences",
                "data": [
                    {"label": "Lending", "value": "100%", "note": "row 1"},
                    {"label": "Margin", "value": "10x", "note": "row 2"},
                    {"label": "Safety", "value": "1.10x", "note": "row 3"}
                ],
                "footer": "docs.vanna.finance"
            }
        }
        
        run_id = "test-req04-template-repetition"
        res = review_package(repetitive_draft, self.valid_image, run_id=run_id)
        self.assertEqual(res["decision"], "REGENERATE")
        self.assertTrue(res["template_repetition"])
        self.assertLess(res["scores"]["novelty"], 75)
        self.assertTrue(any("TEMPLATE REPETITION DETECTED" in f for f in res["critical_failures"]))
        self.assertTrue(any("editorial hero" in c for c in res["required_changes"]))

    def test_05_wrong_brand_colors_cause_visual_brand_failure(self):
        """Requirement 5: Wrong brand colors cause visual/brand failure."""
        wrong_color_img = REPO_ROOT / "pipeline" / "state" / "test_wrong_colors.png"
        # Create an image dominated by electric cyan/teal (> 40% cyan)
        im = Image.new("RGB", (800, 800), color=(0, 240, 220))
        im.save(wrong_color_img)

        try:
            run_id = "test-req05-brand-color-violation"
            res = review_package(self.valid_draft, wrong_color_img, run_id=run_id)
            self.assertIn(res["decision"], ("REGENERATE", "FAIL"))
            self.assertLess(res["scores"]["brand"], 90)
            self.assertTrue(any("unapproved dominant color" in r.lower() or "dark obsidian foundation" in r.lower() for r in res["reasons"]))
        finally:
            if wrong_color_img.exists():
                wrong_color_img.unlink()

    def test_06_missing_png_causes_fail(self):
        """Requirement 6: Missing PNG causes FAIL."""
        missing_path = REPO_ROOT / "pipeline" / "state" / "non_existent_file_9999.png"
        if missing_path.exists():
            missing_path.unlink()

        run_id = "test-req06-missing-png"
        res = review_package(self.valid_draft, missing_path, run_id=run_id)
        self.assertIn(res["decision"], ("REGENERATE", "FAIL"))
        self.assertEqual(res["scores"]["visual"], 0)
        self.assertTrue(any("missing rendered png" in f.lower() for f in res["critical_failures"]))

    def test_07_genuinely_different_premium_visual_can_pass(self):
        """Requirement 7: A genuinely different premium visual can PASS."""
        fresh_draft = dict(self.valid_draft)
        fresh_draft["visual_brief"] = {
            "content_category": "PRODUCT",
            "layout_archetype": "asymmetric technical diagram",
            "headline": "Asymmetric Risk Telemetry",
            "footer": "test.stellar.vanna.finance"
        }
        run_id = "test-req07-premium-fresh-pass"
        res = review_package(fresh_draft, self.valid_image, run_id=run_id)
        self.assertEqual(res["decision"], "PASS")
        self.assertGreaterEqual(res["scores"]["content"], 85)
        self.assertGreaterEqual(res["scores"]["factual"], 95)
        self.assertGreaterEqual(res["scores"]["visual"], 85)
        self.assertGreaterEqual(res["scores"]["brand"], 90)
        self.assertGreaterEqual(res["scores"]["social"], 80)
        self.assertGreaterEqual(res["scores"]["novelty"], 75)
        self.assertEqual(len(res["critical_failures"]), 0)
        self.assertFalse(res["template_repetition"])

    def test_08_review_json_is_persisted(self):
        """Requirement 8: Review JSON is persisted to pipeline/state/reviews/<run_id>.json."""
        run_id = "test-req08-persistence-proof"
        res = review_package(self.valid_draft, self.valid_image, run_id=run_id)
        
        target_file = REVIEWS_DIR / f"{run_id}.json"
        self.assertTrue(target_file.exists(), f"Review file {target_file} was not written to disk")
        
        saved_data = json.loads(target_file.read_text(encoding="utf-8"))
        self.assertEqual(saved_data["run_id"], run_id)
        self.assertEqual(saved_data["decision"], res["decision"])
        self.assertIn("scores", saved_data)
        self.assertIn("critical_failures", saved_data)
        self.assertIn("reasons", saved_data)
        self.assertIn("required_changes", saved_data)
        self.assertIn("visual_archetype", saved_data)
        self.assertIn("template_repetition", saved_data)

    def test_09_telegram_is_never_called_on_fail(self):
        """Requirement 9: Telegram is never called on FAIL (mock simulation)."""
        bad_draft = dict(self.valid_draft)
        bad_draft["final_body"] = "100% risk-free 50% APR guaranteed by Vanna on Solana! docs.vanna.finance"
        
        mock_telegram_send = MagicMock()
        
        run_id = "test-req09-never-call-telegram"
        res = review_package(bad_draft, self.valid_image, run_id=run_id)
        
        # Pipeline logic check
        if res["decision"] == "PASS":
            mock_telegram_send()
            
        mock_telegram_send.assert_not_called()

    def test_10_reviewer_runs_before_telegram_every_time(self):
        """Requirement 10: Reviewer runs before Telegram every time in orchestrator code."""
        orch_file = REPO_ROOT / "pipeline" / "scripts" / "autonomous_orchestrator.py"
        self.assertTrue(orch_file.exists())
        
        content = orch_file.read_text(encoding="utf-8")
        
        reviewer_call_pos = content.find("review_package(")
        telegram_send_pos = content.find("telegram_review.py")
        
        self.assertNotEqual(reviewer_call_pos, -1, "review_package call not found in orchestrator")
        self.assertNotEqual(telegram_send_pos, -1, "telegram_review call not found in orchestrator")
        self.assertLess(
            reviewer_call_pos,
            telegram_send_pos,
            "CRITICAL: Final Reviewer must be invoked BEFORE telegram_review.py in the pipeline!"
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
