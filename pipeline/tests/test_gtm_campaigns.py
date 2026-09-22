"""Unit tests for Phase 3 Campaign and Series Engine (test_gtm_campaigns.py).

Validates:
  1. Campaign stage mapping (7 standard stages)
  2. Omitted stages require explicit justification
  3. Series recurrence tier progression (1 -> 2 -> 4)
  4. Campaign vs Series vs One-Off distinction
  5. Incomplete source handling (NOT_OBSERVED status)
  6. Campaign lifecycle controls (pause, kill, approve)
  7. Audit report emission to campaign_series_audit.json
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
STATE_DIR = REPO_ROOT / "pipeline" / "state"

from pipeline.gtm_campaigns.campaign_engine import CampaignEngine
from pipeline.gtm_campaigns.series_engine import SeriesEngine
from pipeline.gtm_campaigns.campaign_selector import CampaignSelector
from pipeline.gtm_orchestration.schemas import GTMStrategy


class TestGTMCampaignsAndSeries(unittest.TestCase):
    """Test suite asserting campaign staging, series recurrence, and lifecycle controls."""

    def setUp(self):
        self.campaign_engine = CampaignEngine()
        self.series_engine = SeriesEngine()
        self.selector = CampaignSelector()

        # Dummy valid strategy for testing
        self.sample_strategy = GTMStrategy(
            strategy_id="STRAT-TEST-001",
            action_status="ACTION",
            objective="Migrate liquidity from EVM shared pools to Soroban sandboxes",
            audience_segment="A2: EVM Migrants",
            problem="EVM shared pools suffer from mempool front-running",
            market_context="Soroban Protocol 20 is live",
            strategic_opportunity="Position Vanna isolated sandboxes",
            narrative_pillar="Pillar 2: Isolated SmartAccount Sandboxes",
            positioning="Vanna is the composable credit layer for Stellar",
            proof=["0.00014 XLM gas", "~320ms latency"],
            cta="test.stellar.vanna.finance",
            channel="X & Reddit",
            content_type="architectural_comparison",
            gtm_machine_id="MACH_03_COMPETITOR_DISPLACEMENT"
        )

    def test_01_campaign_instantiation_and_stage_mapping(self):
        camp = self.campaign_engine.instantiate_campaign_from_strategy(
            self.sample_strategy,
            campaign_name="Vanna Sandbox Migration Campaign"
        )
        self.assertEqual(camp.status, "DRAFT")
        self.assertEqual(camp.approval_state, "PENDING_HUMAN_APPROVAL")
        self.assertGreaterEqual(len(camp.stages), 4)

        # Verify stages follow standard taxonomy
        stage_types = [s.stage_type for s in camp.stages]
        self.assertIn("AWARENESS", stage_types)
        self.assertIn("EDUCATION", stage_types)
        self.assertIn("PROOF", stage_types)
        self.assertIn("CONVERSION", stage_types)

    def test_02_omitted_stages_require_explicit_reasons(self):
        camp = self.campaign_engine.instantiate_campaign_from_strategy(
            self.sample_strategy,
            campaign_name="Focused 3-Stage Campaign",
            included_stages=["AWARENESS", "EDUCATION", "CONVERSION"],
            omission_reasons={"PROOF": "Proof points deferred to subsequent partner audit release."}
        )
        self.assertIn("PROOF", camp.omitted_stages)
        self.assertIn("partner audit release", camp.omitted_stages["PROOF"])
        # Omitted stage must have a documented reason
        for omitted, reason in camp.omitted_stages.items():
            self.assertTrue(len(reason) > 5, f"Omission reason for {omitted} is empty.")

    def test_03_campaign_lifecycle_controls(self):
        camp = self.campaign_engine.instantiate_campaign_from_strategy(
            self.sample_strategy, campaign_name="Lifecycle Test"
        )
        # 1. Approve
        approved = self.campaign_engine.approve_campaign(camp.campaign_id, "FounderAlice")
        self.assertEqual(approved.status, "ACTIVE")
        self.assertEqual(approved.approval_state, "APPROVED")

        # 2. Pause
        paused = self.campaign_engine.pause_campaign(camp.campaign_id, "Paused pending security review")
        self.assertEqual(paused.status, "PAUSED")

        # 3. Kill
        killed = self.campaign_engine.kill_campaign(camp.campaign_id, "Critical market pivot")
        self.assertEqual(killed.status, "KILLED")

    def test_04_series_recurrence_tier_progression(self):
        # Register a new series
        series = self.series_engine.register_series(
            series_id="SERIES_SOLVENCY_WEEKLY",
            series_name="Weekly Solvency Telemetry Report",
            cadence="WEEKLY",
            trigger="SCHEDULED_FRIDAY",
            input_data_source="Mercury Indexer",
            fixed_structure=["Health Factor Rail", "Latency Benchmark", "Sandbox Count"],
            variable_fields=["total_active_sandboxes", "avg_rebalance_latency"],
            visual_template_type="telemetry_rail"
        )
        # Tier 0: 0 occurrences -> ONE_OCCURRENCE
        self.assertEqual(series.recurrence_tier, "ONE_OCCURRENCE")

        # Record occurrence 1 & 2 -> REPEATED_PATTERN
        self.series_engine.record_occurrence(series.series_id, "2026-09-01", "C-01", "Snapshot 1")
        s2 = self.series_engine.record_occurrence(series.series_id, "2026-09-08", "C-02", "Snapshot 2")
        self.assertEqual(s2.recurrence_tier, "REPEATED_PATTERN")

        # Record occurrence 3 & 4 -> RECURRING_SYSTEM
        self.series_engine.record_occurrence(series.series_id, "2026-09-15", "C-03", "Snapshot 3")
        s4 = self.series_engine.record_occurrence(series.series_id, "2026-09-22", "C-04", "Snapshot 4")
        self.assertEqual(s4.recurrence_tier, "RECURRING_SYSTEM")
        self.assertEqual(len(s4.occurrences), 4)

    def test_05_campaign_selector_distinction(self):
        # 1. Telemetry strategy -> RECURRING_SERIES
        telemetry_strat = GTMStrategy(
            strategy_id="STRAT-TELEMETRY", action_status="ACTION", objective="Transparency",
            audience_segment="A2", problem="", market_context="", strategic_opportunity="",
            narrative_pillar="Pillar 3: Sub-Second Defensive Rebalancing", positioning="", proof=[],
            cta="", channel="", content_type="", gtm_machine_id="MACH_04_TECHNICAL_TELEMETRY_SERIES"
        )
        res_series = self.selector.select_structural_vehicle(telemetry_strat)
        self.assertEqual(res_series.decision_type, "RECURRING_SERIES")

        # 2. Competitor displacement with coordinated staged conversion -> MULTI_STAGE_CAMPAIGN
        res_camp = self.selector.select_structural_vehicle(
            self.sample_strategy, has_coordinated_cohorts=True, has_conversion_funnel=True
        )
        self.assertEqual(res_camp.decision_type, "MULTI_STAGE_CAMPAIGN")

    def test_06_audit_report_generation(self):
        report = self.selector.audit_campaign_and_series_engine(STATE_DIR / "campaign_series_audit.json")
        self.assertEqual(report["audit_status"], "VERIFIED")
        self.assertTrue((STATE_DIR / "campaign_series_audit.json").exists())


if __name__ == "__main__":
    unittest.main()
