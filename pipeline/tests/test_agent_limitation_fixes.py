"""Automated Test Suite for Upgrades and Limitation Fixes Across Agents 2-13.

Verifies:
  1. Agent 2 (Opportunity Selector): Multi-track diverse portfolio selection.
  2. Agent 6 (Channel Adapter): Intelligent thread-splitting (<280 char enforcement).
  3. Agents 7 & 8 (Creative Director): Metaphor diversity rotation across physical families.
  4. Agent 11 (Dispatch Worker): Automated dispatch retry queue with exponential backoff.
  5. Agent 13 (Learning Engine): Bayesian UCB exploration bonus for low-sample-size patterns.
"""

from __future__ import annotations

import shutil
import tempfile
import time
import unittest
from pathlib import Path

from pipeline.gtm_opportunities.opportunity_selector import OpportunitySelector
from pipeline.gtm_content.channel_adapter import ChannelAdapter
from pipeline.gtm_creative.metaphor_registry import MetaphorDiversityManager
from pipeline.gtm_publish.dispatch_retry_queue import DispatchRetryQueue
from pipeline.gtm_publish.publisher_schemas import ChannelContentPayload
from pipeline.gtm_learning.pattern_weighting import PatternWeightingEngine


class TestAgentLimitationFixes(unittest.TestCase):
    """Test suite verifying fixes for operational limitations across Agents 2-13."""

    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_agent_2_opportunity_selector_diversity(self):
        """Agent 2: Verify select_top_opportunities selects diverse multi-track portfolio."""
        selector = OpportunitySelector()
        mock_candidates = [
            {
                "opportunity_id": "OPP-01",
                "title": "SmartAccount Isolation for Traders",
                "target_audience": "A2: Quantitative Traders",
                "recommended_machine": "MACH_04",
                "confidence": "HIGH",
                "relevance": 0.95,
                "vanna_source": True
            },
            {
                "opportunity_id": "OPP-02",
                "title": "Blend v2 Institutional Vaults",
                "target_audience": "A3: Institutional LPs",
                "recommended_machine": "MACH_02",
                "confidence": "HIGH",
                "relevance": 0.90,
                "vanna_source": True
            },
            {
                "opportunity_id": "OPP-03",
                "title": "Duplicate Angle for Traders",
                "target_audience": "A2: Quantitative Traders",
                "recommended_machine": "MACH_04",
                "confidence": "HIGH",
                "relevance": 0.85,
                "vanna_source": True
            }
        ]

        portfolio = selector.select_top_opportunities(limit=2, require_diversity=True, candidate_records=mock_candidates)
        self.assertEqual(len(portfolio), 2)
        # Ensure diverse audience tracks were selected
        audiences = [c.raw_record.get("target_audience") for c in portfolio]
        self.assertIn("A2: Quantitative Traders", audiences)
        self.assertIn("A3: Institutional LPs", audiences)

    def test_agent_6_channel_adapter_smart_thread_splitter(self):
        """Agent 6: Verify long technical copy splits into clean thread chunks without clipping."""
        adapter = ChannelAdapter()
        long_copy = (
            "During high-volatility market events, decentralized lending markets face two structural failure modes: "
            "mempool congestion spikes transaction fees delaying defensive rebalances, and shared pool storage forces haircuts.\n\n"
            "Vanna addresses both challenges directly at the smart contract execution layer on Stellar Soroban with dedicated SmartAccounts.\n\n"
            "Sub-second event streaming via the Mercury indexer enables automated rebalances in ~320ms, with deterministic fees fixed at 0.00014 XLM."
        )

        thread_chunks = adapter.split_into_thread(long_copy, max_chars=200)
        self.assertGreater(len(thread_chunks), 1)
        for chunk in thread_chunks:
            self.assertLessEqual(len(chunk), 200)
            self.assertTrue(chunk.startswith("[") and "/" in chunk[:6])

    def test_agents_7_and_8_metaphor_diversity_manager(self):
        """Agents 7 & 8: Verify MetaphorDiversityManager rotates across physical concept families."""
        reg_file = self.test_dir / "test_metaphors.jsonl"
        mgr = MetaphorDiversityManager(registry_file=reg_file)

        fam1 = mgr.select_next_metaphor_family()
        mgr.record_metaphor(fam1, "Prism Refraction", "Smoked glass prism splitting filaments")

        fam2 = mgr.select_next_metaphor_family()
        self.assertNotEqual(fam1, fam2)
        mgr.record_metaphor(fam2, "Laminar Flow Conduits", "Fluid channels with isolation valves")

        fam3 = mgr.select_next_metaphor_family()
        self.assertNotIn(fam3, [fam1, fam2])

    def test_agent_11_dispatch_retry_queue(self):
        """Agent 11: Verify failed dispatches are enqueued and retried successfully."""
        ret_file = self.test_dir / "test_retries.jsonl"
        queue = DispatchRetryQueue(retry_file=ret_file)

        payload = ChannelContentPayload(
            channel="X",
            copy="Sub-second Mercury telemetry streams ledger events in ~320ms on Stellar Soroban."
        )

        entry = queue.enqueue_failure("REQ-FAIL-01", payload, error_message="Transient 503 Gateway Timeout")
        self.assertEqual(entry.status, "PENDING_RETRY")

        # Fast-forward retry timestamp for testing
        records = queue.store.read_all()
        records[0]["next_retry_at"] = time.time() - 1.0
        queue.store.atomic_overwrite(records)

        receipts = queue.process_pending_retries(mode="SIMULATED_TESTNET")
        self.assertEqual(len(receipts), 1)
        self.assertEqual(receipts[0].status, "SUCCESS")

        updated_records = queue.store.read_all()
        self.assertEqual(updated_records[0]["status"], "RETRIED_SUCCESS")

    def test_agent_13_bayesian_exploration_priority(self):
        """Agent 13: Verify Bayesian UCB bonus prioritizes unmeasured patterns with low sample sizes."""
        engine = PatternWeightingEngine()
        priority_zero_samples = engine.get_exploration_priority("PAT_01_TECHNICAL_TELEMETRY", [])
        # Base weight 1.0 + 0.25 = 1.25
        self.assertEqual(priority_zero_samples, 1.25)

        priority_two_samples = engine.get_exploration_priority("PAT_01_TECHNICAL_TELEMETRY", [None, None])
        # Base weight 1.0 + (0.25 / 3) = 1.083
        self.assertEqual(priority_two_samples, 1.083)
        self.assertGreater(priority_zero_samples, priority_two_samples)


if __name__ == "__main__":
    unittest.main()
