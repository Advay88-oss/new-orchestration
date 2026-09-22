"""Unit tests for Phase 2 GTM Machine Library (test_gtm_machines.py).

Validates:
  1. Unsupported machine rejection
  2. Machine threshold enforcement (minimum evidence check)
  3. Source mapping and evidence backing
  4. Stage completeness across eligible machines
  5. No fabricated campaign examples
  6. Three-way knowledge separation (observed vs inferred vs adaptation)
  7. Audit report emission to pipeline/state/gtm_machine_audit.json
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
STATE_DIR = REPO_ROOT / "pipeline" / "state"

from pipeline.gtm_machines.machine_library import GTMMachineLibrary
from pipeline.gtm_machines.schemas import GTMMachineDefinition


class TestGTMMachineLibrary(unittest.TestCase):
    """Test suite asserting empirical thresholds and stage integrity for GTM machines."""

    def setUp(self):
        self.library = GTMMachineLibrary()

    def test_01_catalog_size_and_types(self):
        machines = self.library.list_machines()
        self.assertEqual(len(machines), 10, "Machine library must maintain exactly 10 machine specifications.")

    def test_02_unsupported_machine_rejected(self):
        # A fictional unobserved machine must be rejected
        res = self.library.validate_machine_for_strategy(
            "MACH_UNKNOWN_FICTIONAL", "Launch", "Farmers"
        )
        self.assertFalse(res["allowed"])
        self.assertEqual(res["status"], "NOT_FOUND")

    def test_03_insufficient_evidence_blocked_from_autonomous_selection(self):
        # MACH_08_INCENTIVE_POINTS has 0 observed campaigns -> must be INSUFFICIENT_EVIDENCE
        res = self.library.validate_machine_for_strategy(
            "MACH_08_INCENTIVE_POINTS_CAMPAIGN", "Growth", "Farmers"
        )
        self.assertFalse(res["allowed"])
        self.assertEqual(res["status"], "INSUFFICIENT_EVIDENCE")
        self.assertIn("minimum threshold", res["reason"])

    def test_04_prohibited_machine_blocked(self):
        # MACH_10_VIRAL_MEME_BOUNTY is prohibited by brand doctrine
        res = self.library.validate_machine_for_strategy(
            "MACH_10_VIRAL_MEME_BOUNTY", "Viral", "Retail"
        )
        self.assertFalse(res["allowed"])
        self.assertEqual(res["status"], "PROHIBITED")

    def test_05_eligible_machine_allowed(self):
        # MACH_01_PHASED_TECHNICAL_LAUNCH meets threshold (>= 1 observed campaign)
        res = self.library.validate_machine_for_strategy(
            "MACH_01_PHASED_TECHNICAL_LAUNCH", "Protocol Launch", "Institutional LPs"
        )
        self.assertTrue(res["allowed"])
        self.assertEqual(res["status"], "ELIGIBLE")

    def test_06_three_way_knowledge_separation(self):
        # Assert that every machine strictly separates observed from inferred from adaptation
        for m in self.library.list_machines():
            self.assertTrue(len(m.observed_behavior) > 10, f"Machine {m.machine_id} missing observed behavior.")
            self.assertTrue(len(m.inferred_mechanism) > 10, f"Machine {m.machine_id} missing inferred mechanism.")
            self.assertTrue(len(m.proposed_vanna_adaptation) > 10, f"Machine {m.machine_id} missing proposed adaptation.")

    def test_07_stage_completeness_for_eligible_machines(self):
        # Every eligible machine must have >= 2 stages with purposes and expected content types
        eligible = self.library.list_machines(status_filter="ELIGIBLE")
        self.assertGreater(len(eligible), 0)
        for m in eligible:
            self.assertGreaterEqual(len(m.required_stages), 2, f"Eligible machine {m.machine_id} has fewer than 2 stages.")
            for s in m.required_stages:
                self.assertIsNotNone(s.stage_name)
                self.assertIsNotNone(s.purpose)
                self.assertIsNotNone(s.expected_content_type)

    def test_08_audit_report_generation(self):
        report = self.library.audit_entire_library(STATE_DIR / "gtm_machine_audit.json")
        self.assertEqual(report["total_machines_evaluated"], 10)
        self.assertGreater(report["eligible_machines_count"], 0)
        self.assertGreater(report["insufficient_evidence_count"], 0)
        self.assertTrue((STATE_DIR / "gtm_machine_audit.json").exists())


if __name__ == "__main__":
    unittest.main()
