"""Regression tests specifically reproducing and preventing the OPP_COMPOSABLE_SANDBOX failures.

Validates the 4 Decision Quality Gates:
  1. AUDIENCE FIT: LP audience + trader/mempool copy -> REVISE
  2. AUDIENCE FIT: Trader audience + trader/mempool copy -> PASS
  3. PRODUCT / STAGE FIT: Competitor displacement + testnet migration -> REJECT
  4. PRODUCT / STAGE FIT: Technical education + testnet architecture demo -> PASS
  5. VEHICLE FIT: Single technical topic + multi-channel -> SERIES/ONE_OFF, not automatically CAMPAIGN
  6. VEHICLE FIT: True staged conversion sequence -> CAMPAIGN
  7. CLAIM CONSISTENCY: 1.25x proactive threshold + 1.10x floor with explicit relationship -> PASS
  8. CLAIM CONSISTENCY: Contradictory 1.25x / 1.10x wording -> REJECT
  9. CLAIM CONSISTENCY: 'Zero liquidation penalty' with possible DEX execution costs -> REVISE
  10. NULL EVIDENCE: Null metrics remain None and are never converted to 0.0 or observed.
"""

from __future__ import annotations

import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

from pipeline.gtm_orchestration.decision_quality_gates import (
    AudienceFitGate, ProductStageFitGate, VehicleFitGate, ClaimConsistencyGate
)
from pipeline.gtm_learning.outcome_schema import MetricValue


class TestGTMRegressionOppSandbox(unittest.TestCase):
    """Regression test suite for OPP_COMPOSABLE_SANDBOX strategic audit failures."""

    def setUp(self):
        self.audience_gate = AudienceFitGate()
        self.stage_gate = ProductStageFitGate()
        self.vehicle_gate = VehicleFitGate()
        self.claim_gate = ClaimConsistencyGate()

    # 1. LP audience + trader/mempool copy -> REVISE
    def test_01_lp_audience_with_trader_mempool_copy_revises(self):
        lp_audience = "A3: Institutional Liquidity Providers & Risk Architects"
        trader_copy = (
            "In an EVM liquidation cascade, gas spikes to 150 gwei while your rebalance transaction "
            "sits pending in the mempool. Front-running bots and bidding wars cost you a 10% penalty."
        )
        res = self.audience_gate.evaluate(lp_audience, trader_copy)
        self.assertEqual(res.status, "REVISE")
        self.assertIn("misaligned", res.reason.lower())
        self.assertIn("Institutional LPs care about reserve solvency", res.reason)

    # 2. Trader audience + trader/mempool copy -> PASS
    def test_02_trader_audience_with_trader_mempool_copy_passes(self):
        trader_audience = "A2: EVM Migrants & Quantitative Traders"
        trader_copy = (
            "In an EVM liquidation cascade, gas spikes to 150 gwei while your rebalance transaction "
            "sits pending in the mempool. Front-running bots cost you money."
        )
        res = self.audience_gate.evaluate(trader_audience, trader_copy)
        self.assertEqual(res.status, "PASS")
        self.assertIn("demonstrably aligned", res.reason.lower())

    # 3. Competitor displacement + testnet-only migration objective -> REJECT/REVISE
    def test_03_competitor_displacement_on_testnet_rejected(self):
        machine_id = "MACHINE_03: COMPETITOR_DISPLACEMENT_CAMPAIGN"
        objective = "Displace Aave by migrating liquidity providers to Vanna testnet sandboxes."
        res = self.stage_gate.evaluate(machine_id, objective)
        self.assertEqual(res.status, "REJECT")
        self.assertIn("strategically inappropriate", res.reason.lower())
        self.assertIn("testnet", res.reason.lower())

    # 4. Technical education + architecture/testnet objective -> PASS
    def test_04_technical_education_on_testnet_passes(self):
        machine_id = "MACHINE_04: TECHNICAL_EDUCATION_DISPATCH"
        objective = "Educate developers on isolated SmartAccount sandboxes and testnet verification."
        res = self.stage_gate.evaluate(machine_id, objective)
        self.assertEqual(res.status, "PASS")
        self.assertIn("aligned with product stage", res.reason.lower())

    # 5. Single technical topic + multi-channel distribution -> SERIES/ONE_OFF, not automatically CAMPAIGN
    def test_05_single_technical_topic_is_series_not_campaign(self):
        topic = "Pillar 2: Isolated SmartAccount Sandboxes"
        veh_type, res = self.vehicle_gate.evaluate(
            topic=topic,
            stage_count=1,
            is_repeatable_theme=True,
            has_coordinated_cohorts=False,
            has_conversion_funnel=False
        )
        self.assertNotEqual(veh_type, "CAMPAIGN")
        self.assertEqual(veh_type, "SERIES")
        self.assertEqual(res.status, "PASS")
        self.assertIn("not a campaign", res.reason.lower())

    # 6. True staged conversion sequence -> CAMPAIGN
    def test_06_true_staged_conversion_sequence_is_campaign(self):
        topic = "Vanna Testnet Launch Sprint"
        veh_type, res = self.vehicle_gate.evaluate(
            topic=topic,
            stage_count=5,
            is_repeatable_theme=False,
            has_coordinated_cohorts=True,
            has_conversion_funnel=True
        )
        self.assertEqual(veh_type, "CAMPAIGN")
        self.assertEqual(res.status, "PASS")
        self.assertIn("meets strict criteria", res.reason.lower())

    # 7. 1.25x proactive threshold + 1.10x hard floor with explicit relationship -> PASS
    def test_07_explicit_threshold_relationship_passes(self):
        consistent_claims = (
            "Risk Guardian executes proactive rebalancing at 1.25x Net Health Factor "
            "prior to the protocol's 1.10x hard liquidation floor, preventing punitive liquidation."
        )
        res = self.claim_gate.evaluate(consistent_claims)
        self.assertEqual(res.status, "PASS")
        self.assertTrue(any("1.10x" in e for e in res.evidence))

    # 8. Contradictory 1.25x/1.10x wording -> REJECT
    def test_08_contradictory_threshold_wording_rejected(self):
        contradictory_claims = (
            "Positions enter liquidation at 1.25x liquidation floor."
        )
        res = self.claim_gate.evaluate(contradictory_claims)
        self.assertEqual(res.status, "REJECT")
        self.assertIn("contradictory threshold", res.reason.lower())

    # 9. 'Zero liquidation penalty' with possible DEX execution costs -> REVISE
    def test_09_zero_liquidation_penalty_revises(self):
        absolute_claims = (
            "Automated keeper rebalances fixed at 0.00014 XLM. No mempool bidding wars. Zero liquidation penalty."
        )
        res = self.claim_gate.evaluate(absolute_claims)
        self.assertEqual(res.status, "REVISE")
        self.assertIn("absolute penalty assertion", res.reason.lower())
        self.assertIn("dex", res.reason.lower())

    # 10. Null evidence remains null and is never converted to zero/observed
    def test_10_null_evidence_remains_null(self):
        unmeasured = MetricValue.unmeasured()
        self.assertIsNone(unmeasured.raw_value)
        self.assertEqual(unmeasured.status, "NOT_MEASURED")
        self.assertFalse(unmeasured.is_measured_zero)
        
        # Test serialization
        d = unmeasured.model_dump()
        self.assertIsNone(d["raw_value"])
        self.assertEqual(d["status"], "NOT_MEASURED")
        self.assertFalse(d["is_measured_zero"])


if __name__ == "__main__":
    unittest.main()
