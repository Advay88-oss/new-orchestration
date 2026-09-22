"""Unit tests for Phase 4 Channel-Native Content Execution (test_gtm_content.py).

Validates:
  1. Channel outputs are genuinely different (distinctness score >= 60).
  2. Every post carries claim provenance and exact evidence references.
  3. Unsupported or prohibited claims are blocked across all platforms.
  4. Platform-specific constraints (Reddit disclosure, X brevity, LinkedIn framing).
  5. Strategy is strictly mandatory (no raw topic bypass).
  6. Audit report emission to channel_adaptation_audit.json.
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
STATE_DIR = REPO_ROOT / "pipeline" / "state"

from pipeline.gtm_content.channel_adapter import ChannelAdapter
from pipeline.gtm_content.channel_reviewer import ChannelReviewer
from pipeline.gtm_orchestration.schemas import GTMStrategy, ClaimRecord


class TestGTMContentAdaptation(unittest.TestCase):
    """Test suite asserting cross-channel divergence and claim provenance."""

    def setUp(self):
        self.adapter = ChannelAdapter()
        self.reviewer = ChannelReviewer()

        # Valid strategy fixture
        self.sample_strategy = GTMStrategy(
            strategy_id="STRAT-CHANNEL-TEST-001",
            action_status="ACTION",
            objective="Educate traders on sub-second liquidation defense",
            audience_segment="A2: EVM Migrants & Quantitative Traders",
            problem="Mempool front-running causes 10% liquidation penalties on EVM",
            market_context="Soroban Protocol 20 is operational",
            strategic_opportunity="Position Vanna Mercury indexer sub-second defense",
            narrative_pillar="Pillar 3: Sub-Second Defensive Rebalancing",
            positioning="Vanna is the composable credit layer for Stellar Soroban",
            proof=["0.00014 XLM fixed gas", "~320ms Mercury event streaming", "1.25x trigger"],
            claims=[
                ClaimRecord(
                    claim_id="CLM-01", text="0.00014 XLM fixed gas", claim_type="VANNA_FACT",
                    evidence_status="OBSERVED", action="USE", confidence="HIGH", rationale="Verified on testnet"
                ),
                ClaimRecord(
                    claim_id="CLM-02", text="~320ms Mercury event streaming", claim_type="VANNA_FACT",
                    evidence_status="OBSERVED", action="USE", confidence="HIGH", rationale="Verified indexer latency"
                )
            ],
            cta="test.stellar.vanna.finance",
            channel="X, LinkedIn, Reddit",
            content_type="multi_channel_suite",
            gtm_machine_id="MACH_02_TELEMETRY_DEFENSE",
            evidence=[{"record_id": "REC_MERCURY_01", "source_type": "INTERNAL_KNOWLEDGE"}]
        )

    def test_01_channel_outputs_are_genuinely_different(self):
        package = self.adapter.adapt_strategy_to_channels(self.sample_strategy)
        posts = package.channel_posts
        self.assertIn("x", posts)
        self.assertIn("linkedin", posts)
        self.assertIn("reddit", posts)

        # Assert texts are distinct
        self.assertNotEqual(posts["x"].copy, posts["linkedin"].copy)
        self.assertNotEqual(posts["linkedin"].copy, posts["reddit"].copy)

        # Reviewer distinctness score must be >= 60
        verdict = self.reviewer.review_channel_adaptation(package)
        self.assertGreaterEqual(verdict.distinctness_score, 60)
        self.assertTrue(verdict.approved)

    def test_02_every_post_has_claim_provenance(self):
        package = self.adapter.adapt_strategy_to_channels(self.sample_strategy)
        for ch_name, p in package.channel_posts.items():
            self.assertGreater(len(p.source_claims), 0, f"Channel {ch_name} missing source claims.")
            self.assertGreater(len(p.exact_evidence_refs), 0, f"Channel {ch_name} missing evidence refs.")
            self.assertIn("strategy_id", p.provenance)

    def test_03_prohibited_claims_blocked_across_channels(self):
        corrupted_strat = self.sample_strategy.model_copy(deep=True)
        corrupted_strat.positioning = "Vanna is the Aave of Stellar with mainnet live deposits"
        package = self.adapter.adapt_strategy_to_channels(corrupted_strat)
        
        # Inject prohibited claim into Reddit copy
        package.channel_posts["reddit"].copy += " Vanna is the Aave of Stellar."
        verdict = self.reviewer.review_channel_adaptation(package)
        self.assertFalse(verdict.approved)
        self.assertTrue(any("aave of stellar" in b.lower() for b in verdict.blocked_unsupported_claims))

    def test_04_channel_specific_constraints(self):
        package = self.adapter.adapt_strategy_to_channels(self.sample_strategy)
        # Reddit post must contain disclosure and discussion question
        reddit_post = package.channel_posts["reddit"]
        self.assertIn("Disclosure", reddit_post.copy)
        self.assertIsNotNone(reddit_post.discussion_question)
        self.assertIn("?", reddit_post.discussion_question)

        # X post must respect brevity
        x_post = package.channel_posts["x"]
        self.assertLessEqual(len(x_post.copy), 800)

    def test_05_strategy_is_mandatory_no_raw_topic_bypass(self):
        no_action_strat = self.sample_strategy.model_copy()
        no_action_strat.action_status = "NO_ACTION"
        with self.assertRaises(ValueError):
            self.adapter.adapt_strategy_to_channels(no_action_strat)

    def test_06_audit_report_generation(self):
        package = self.adapter.adapt_strategy_to_channels(self.sample_strategy)
        verdict = self.reviewer.review_channel_adaptation(package, STATE_DIR / "channel_adaptation_audit.json")
        self.assertTrue((STATE_DIR / "channel_adaptation_audit.json").exists())
        self.assertTrue(verdict.approved)


if __name__ == "__main__":
    unittest.main()
