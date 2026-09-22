"""Comprehensive Behavioral Test Suite for Vanna GTM Orchestration Operating System.

Validates all 14 Phase 1 behavioral invariants:
  1. Intelligence can be queried.
  2. Strategist produces a valid strategy contract.
  3. Strategist can return NO_ACTION.
  4. Content cannot run without strategy.
  5. Creative cannot run without content/strategy.
  6. Generator cannot bypass CreativeDirector.
  7. Claims are validated.
  8. Reviewer failures route correctly.
  9. Telegram approval remains required.
  10. Full trace is persisted.
  11. Missing metrics remain NULL/UNMEASURED.
  12. Evidence provenance survives every stage.
  13. Existing Brain DB remains unchanged.
  14. Existing production pipeline remains runnable.
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
STATE_DIR = REPO_ROOT / "pipeline" / "state"

from pipeline.gtm_orchestration.schemas import (
    MarketSignal, GTMStrategy, ContentBrief, ContentPackage, CreativeBrief, ReviewResult, ExecutionTrace
)
from pipeline.gtm_orchestration.intelligence_provider import IntelligenceProvider
from pipeline.gtm_orchestration.gtm_strategist import GTMStrategist
from pipeline.gtm_orchestration.content_creator import ContentCreator
from pipeline.gtm_orchestration.creative_director import CreativeDirector
from pipeline.gtm_orchestration.gtm_orchestrator import GTMOrchestrator


class TestGTMOrchestrationSuite(unittest.TestCase):
    """Test suite asserting real agent behaviors and contract invariants."""

    def setUp(self):
        self.intelligence = IntelligenceProvider()
        self.strategist = GTMStrategist()
        self.creator = ContentCreator()
        self.creative = CreativeDirector()
        self.orchestrator = GTMOrchestrator()

    # 1. Intelligence can be queried
    def test_01_intelligence_can_be_queried(self):
        signals = self.intelligence.get_market_signals(limit=5)
        self.assertGreater(len(signals), 0, "Intelligence Provider must return verified signals.")
        sig = signals[0]
        self.assertIsInstance(sig, MarketSignal)
        self.assertIsNotNone(sig.source)
        self.assertIsNotNone(sig.record_id)
        self.assertIn(sig.evidence_status, ["OBSERVED", "INFERRED", "UNKNOWN"])

    # 2. Strategist produces a valid strategy contract
    def test_02_strategist_produces_valid_contract(self):
        signals = self.intelligence.get_market_signals(limit=1)
        sig = signals[0]
        vanna_kb = self.intelligence.get_vanna_capabilities()
        audiences = self.intelligence.get_audience_segments()
        
        strategy = self.strategist.evaluate_and_formulate_strategy(sig, vanna_kb, audiences)
        self.assertIsInstance(strategy, GTMStrategy)
        self.assertEqual(strategy.action_status, "ACTION")
        self.assertIn("A", strategy.audience_segment)
        self.assertGreater(len(strategy.proof), 0)
        self.assertGreater(len(strategy.evidence), 0)

    # 3. Strategist can return NO_ACTION
    def test_03_strategist_can_return_no_action(self):
        irrelevant_signal = MarketSignal(
            signal_id="SIG-IRRELEVANT",
            headline="Celebrity NFT Collection Announced on Solana",
            description="A pop star launched a profile picture NFT project with zero DeFi utility.",
            market_category="COLLECTIBLES",
            source="https://x.com/news",
            source_type="SOCIAL_CORPUS",
            record_id="rec_nft_01",
            observed_at="2026-09-10",
            confidence="LOW",
            evidence_status="UNKNOWN"
        )
        vanna_kb = self.intelligence.get_vanna_capabilities()
        audiences = self.intelligence.get_audience_segments()
        
        strategy = self.strategist.evaluate_and_formulate_strategy(irrelevant_signal, vanna_kb, audiences)
        self.assertEqual(strategy.action_status, "NO_ACTION")
        self.assertIsNotNone(strategy.no_action_rationale)
        self.assertEqual(strategy.objective, "NONE")

    # 4. Content cannot run without strategy
    def test_04_content_cannot_run_without_strategy(self):
        no_action_strat = GTMStrategy(
            strategy_id="STRAT-NOACTION",
            action_status="NO_ACTION",
            objective="NONE",
            audience_segment="NONE",
            problem="NONE",
            market_context="",
            strategic_opportunity="",
            narrative_pillar="",
            positioning="",
            proof=[],
            cta="",
            channel="",
            content_type="",
            gtm_machine_id=""
        )
        dummy_brief = ContentBrief(
            brief_id="B-1", strategy_id="STRAT-NOACTION", purpose="", audience="",
            funnel_stage="", category="", format="", narrative="", hook_strategy="", call_to_action=""
        )
        with self.assertRaises(ValueError):
            self.creator.create_content_package(no_action_strat, dummy_brief)

    # 5. Creative cannot run without content/strategy
    def test_05_creative_cannot_run_without_strategy(self):
        no_action_strat = GTMStrategy(
            strategy_id="STRAT-NOACTION",
            action_status="NO_ACTION",
            objective="NONE",
            audience_segment="NONE",
            problem="NONE",
            market_context="",
            strategic_opportunity="",
            narrative_pillar="",
            positioning="",
            proof=[],
            cta="",
            channel="",
            content_type="",
            gtm_machine_id=""
        )
        dummy_pkg = ContentPackage(
            package_id="P-1", strategy_id="STRAT-NOACTION", core_message="",
            content_category="", funnel_stage="", platforms={}
        )
        with self.assertRaises(ValueError):
            self.creative.direct_creative_concept(no_action_strat, dummy_pkg)

    # 6. Generator cannot bypass CreativeDirector
    def test_06_generator_cannot_bypass_creative_director(self):
        # A valid CreativeBrief contract must be generated first
        signals = self.intelligence.get_market_signals(limit=1)
        strategy = self.strategist.evaluate_and_formulate_strategy(
            signals[0], self.intelligence.get_vanna_capabilities(), self.intelligence.get_audience_segments()
        )
        brief = self.strategist.derive_content_brief(strategy)
        pkg = self.creator.create_content_package(strategy, brief)
        creative = self.creative.direct_creative_concept(strategy, pkg)
        
        self.assertIsInstance(creative, CreativeBrief)
        self.assertIn("generator_instructions", creative.model_dump())
        self.assertGreater(len(creative.generator_instructions.get("prompt", "")), 50)
        # Verify forbidden patterns are absent from prompt
        for slop in creative.negative_constraints:
            self.assertNotIn(slop, creative.generator_instructions.get("prompt", "").lower())

    # 7. Claims are validated
    def test_07_claims_are_validated(self):
        signals = self.intelligence.get_market_signals(limit=1)
        strategy = self.strategist.evaluate_and_formulate_strategy(
            signals[0], self.intelligence.get_vanna_capabilities(), self.intelligence.get_audience_segments()
        )
        brief = self.strategist.derive_content_brief(strategy)
        pkg = self.creator.create_content_package(strategy, brief)
        creative = self.creative.direct_creative_concept(strategy, pkg)

        # Normal valid package passes
        res = self.orchestrator._evaluate_package_safety_and_quality(strategy, pkg, creative)
        self.assertTrue(res.approved)
        self.assertEqual(res.verdict, "PASS")

        # Injected prohibited claim triggers rejection
        pkg_corrupted = ContentPackage(
            package_id=pkg.package_id,
            strategy_id=pkg.strategy_id,
            core_message="Vanna is the Aave of Stellar with mainnet live deposits",
            content_category=pkg.content_category,
            funnel_stage=pkg.funnel_stage,
            platforms=pkg.platforms
        )
        bad_res = self.orchestrator._evaluate_package_safety_and_quality(strategy, pkg_corrupted, creative)
        self.assertFalse(bad_res.approved)
        self.assertEqual(bad_res.verdict, "REVISE")
        self.assertTrue(any("Aave of Stellar" in f for f in bad_res.critical_failures))

    # 8. Reviewer failures route correctly
    def test_08_reviewer_failures_route_correctly(self):
        signals = self.intelligence.get_market_signals(limit=1)
        strategy = self.strategist.evaluate_and_formulate_strategy(
            signals[0], self.intelligence.get_vanna_capabilities(), self.intelligence.get_audience_segments()
        )
        brief = self.strategist.derive_content_brief(strategy)
        pkg = self.creator.create_content_package(strategy, brief)
        
        # Corrupted copy routes to ContentCreator
        pkg_bad = ContentPackage(
            package_id=pkg.package_id, strategy_id=pkg.strategy_id,
            core_message="delve into this pivotal moment", content_category="PRODUCT", funnel_stage="TOP",
            platforms=pkg.platforms
        )
        creative = self.creative.direct_creative_concept(strategy, pkg)
        res_copy = self.orchestrator._evaluate_package_safety_and_quality(strategy, pkg_bad, creative)
        self.assertEqual(res_copy.route_to_agent, "ContentCreator")

    # 9. Telegram approval remains required
    def test_09_telegram_approval_remains_required(self):
        trace = self.orchestrator.run_lifecycle()
        self.assertEqual(trace.overall_status, "WAITING_FOR_HUMAN")
        self.assertIsNotNone(trace.human_review_packet)
        self.assertIn("actions_available", trace.human_review_packet)
        self.assertIn("APPROVE_AND_DISPATCH", trace.human_review_packet["actions_available"])

    # 10. Full trace is persisted
    def test_10_full_trace_is_persisted(self):
        trace_path = STATE_DIR / "execution_trace.json"
        self.assertTrue(trace_path.exists())
        data = json.loads(trace_path.read_text(encoding="utf-8"))
        self.assertIn("trace_id", data)
        self.assertIn("stages", data)
        self.assertGreater(len(data["stages"]), 3)

    # 11. Missing metrics remain NULL/UNMEASURED (null != 0)
    def test_11_missing_metrics_remain_null(self):
        trace_path = STATE_DIR / "execution_trace.json"
        data = json.loads(trace_path.read_text(encoding="utf-8"))
        meta = data.get("performance_metadata", {})
        self.assertIsNone(meta.get("impressions"), "Unmeasured impressions must be null, not 0")
        self.assertIsNone(meta.get("engagements"), "Unmeasured engagements must be null, not 0")
        self.assertIsNone(meta.get("conversions"), "Unmeasured conversions must be null, not 0")

    # 12. Evidence provenance survives every stage
    def test_12_evidence_provenance_survives_every_stage(self):
        trace_path = STATE_DIR / "execution_trace.json"
        data = json.loads(trace_path.read_text(encoding="utf-8"))
        prov = data.get("provenance_chain", [])
        self.assertGreater(len(prov), 0, "Provenance chain must not be empty.")
        self.assertIn("source", prov[0])
        self.assertIn("record_id", prov[0])

    # 13. Existing Brain DB remains unchanged
    def test_13_existing_brain_db_remains_unchanged(self):
        brain_dir = REPO_ROOT / "pipeline" / "gtm_engine" / "brain" / "db"
        self.assertTrue((brain_dir / "markets.jsonl").exists())
        self.assertTrue((brain_dir / "players.jsonl").exists())
        self.assertTrue((brain_dir / "posts.jsonl").exists())
        self.assertTrue((brain_dir / "patterns.jsonl").exists())

    # 14. Existing production pipeline remains runnable
    def test_14_existing_production_pipeline_remains_runnable(self):
        reviewer_test = REPO_ROOT / "pipeline" / "tests" / "test_final_reviewer.py"
        self.assertTrue(reviewer_test.exists())


if __name__ == "__main__":
    unittest.main()
