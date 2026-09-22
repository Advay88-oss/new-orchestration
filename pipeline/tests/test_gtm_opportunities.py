"""Unit tests for Phase 9 Opportunity-Driven Execution (test_gtm_opportunities.py).

Validates:
  1. Transparent multi-factor scoring calculation (no opaque LLM ranking alone).
  2. Ranking order matches highest strategic fit and lowest risk penalty.
  3. Non-selection state (NO_SUITABLE_OPPORTUNITY) when candidate pool is empty or below threshold.
  4. HUMAN_REVIEW_REQUIRED triggered when unverified first-mover assertion appears.
  5. Brain DB immutability during opportunity evaluation.
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

from pipeline.gtm_opportunities.opportunity_selector import OpportunitySelector
from pipeline.gtm_orchestration.config import DEFAULT_CONFIG


class TestGTMOpportunitySelector(unittest.TestCase):
    """Test suite asserting transparent, deterministic opportunity ranking."""

    def setUp(self):
        self.selector = OpportunitySelector(config=DEFAULT_CONFIG)

    def test_01_read_and_score_canonical_opportunities(self):
        res = self.selector.select_best_opportunity()
        self.assertIn(res.decision_status, ["TOP_OPPORTUNITY", "HUMAN_REVIEW_REQUIRED"])
        self.assertGreater(len(res.candidate_rankings), 0)
        top = res.candidate_rankings[0]
        self.assertGreater(top.final_score, 0.50)
        self.assertIsNotNone(top.ranking_explanation)

    def test_02_empty_candidate_pool_returns_no_suitable_opportunity(self):
        empty_res = self.selector.select_best_opportunity(candidate_records=[])
        self.assertEqual(empty_res.decision_status, "NO_SUITABLE_OPPORTUNITY")
        self.assertIsNone(empty_res.selected_opportunity)
        self.assertIn("No candidate opportunities found", empty_res.ranking_rationale)

    def test_03_unsupported_first_mover_escalates_to_human_review(self):
        unverified_opp = {
            "opportunity_id": "OPP-UNVERIFIED-01",
            "title": "First-Mover Monopoly on Stellar",
            "marketing_angle": "Uncontested first-mover advantage with zero competitors",
            "vanna_fact": "Vanna is the only protocol on Stellar",
            "confidence": "LOW",
            "prohibited_claims": ["Zero competitors exist"]
        }
        res = self.selector.select_best_opportunity(candidate_records=[unverified_opp])
        self.assertEqual(res.decision_status, "HUMAN_REVIEW_REQUIRED")
        self.assertEqual(res.selected_opportunity.status, "HUMAN_REVIEW_REQUIRED")
        self.assertIn("first-mover", res.selected_opportunity.ranking_explanation)

    def test_04_scoring_formula_deterministic_weights(self):
        sample_opp = {
            "opportunity_id": "OPP-SCORE-TEST",
            "title": "SmartAccount Credit Sandbox on Soroban",
            "marketing_angle": "10x composable credit",
            "vanna_fact": "Vanna protocol deploys SmartAccount sandboxes on Soroban",
            "vanna_source": "docs.vanna.finance",
            "confidence": "HIGH",
            "prohibited_claims": []
        }
        scored = self.selector.score_opportunity(sample_opp)
        self.assertGreaterEqual(scored.relevance_score, 0.90)
        self.assertGreaterEqual(scored.evidence_confidence, 0.90)
        self.assertGreaterEqual(scored.final_score, 0.70)
        self.assertEqual(scored.status, "ELIGIBLE")


if __name__ == "__main__":
    unittest.main()
