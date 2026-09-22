"""Unit tests for Phase 8 Performance & Learning Loop (test_gtm_learning.py).

Validates:
  1. NULL != 0 invariant (Unmeasured metrics remain None, NOT 0.0).
  2. Measured zero is explicitly distinguished (val=0.0, is_measured_zero=True).
  3. Minimum sample size threshold (adjustments suppressed for < 3 records).
  4. Traceable adjustments occur when sample size >= 3.
  5. Brain DB is never directly mutated by learning loop adjustments.
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
STATE_DIR = REPO_ROOT / "pipeline" / "state"

from pipeline.gtm_learning.outcome_schema import PostPerformanceRecord, MetricValue
from pipeline.gtm_learning.performance_store import PerformanceStore
from pipeline.gtm_learning.pattern_weighting import PatternWeightingEngine
from pipeline.gtm_orchestration.config import DEFAULT_CONFIG


class TestGTMLearningLoop(unittest.TestCase):
    """Test suite asserting NULL-safety, sample-size thresholds, and traceable adjustments."""

    def setUp(self):
        self.temp_store_file = STATE_DIR / "test_performance_temp.jsonl"
        self.temp_adj_file = STATE_DIR / "test_adjustments_temp.jsonl"
        if self.temp_store_file.exists(): self.temp_store_file.unlink()
        if self.temp_adj_file.exists(): self.temp_adj_file.unlink()

        self.store = PerformanceStore(storage_file=self.temp_store_file)
        self.weighting = PatternWeightingEngine(storage_file=self.temp_adj_file)

    def tearDown(self):
        if self.temp_store_file.exists(): self.temp_store_file.unlink()
        if self.temp_adj_file.exists(): self.temp_adj_file.unlink()

    def test_01_null_distinct_from_zero(self):
        # 1. Unmeasured metric
        unmeasured = MetricValue.unmeasured()
        self.assertIsNone(unmeasured.raw_value)
        self.assertEqual(unmeasured.status, "NOT_MEASURED")
        self.assertFalse(unmeasured.is_measured_zero)

        # 2. Measured zero
        measured_zero = MetricValue.measured(0.0)
        self.assertEqual(measured_zero.raw_value, 0.0)
        self.assertEqual(measured_zero.status, "MEASURED")
        self.assertTrue(measured_zero.is_measured_zero)

        # Assert they are not equal in status
        self.assertNotEqual(unmeasured.status, measured_zero.status)

    def test_02_sample_size_threshold_enforcement(self):
        # Create only 2 records (< minimum threshold of 3)
        r1 = PostPerformanceRecord(
            record_id="REC-01", content_id="C-01", campaign_id="PAT_01_TECHNICAL_TELEMETRY",
            platform="X", deployments=MetricValue.measured(6.0), recorded_at="2026-09-10"
        )
        r2 = PostPerformanceRecord(
            record_id="REC-02", content_id="C-02", campaign_id="PAT_01_TECHNICAL_TELEMETRY",
            platform="X", deployments=MetricValue.measured(8.0), recorded_at="2026-09-11"
        )
        # Attempt adjustment with only 2 records -> must be None (suppressed)
        adj = self.weighting.evaluate_and_adjust_pattern("PAT_01_TECHNICAL_TELEMETRY", [r1, r2])
        self.assertIsNone(adj, "Adjustments must be suppressed when sample size is below minimum threshold (3).")

    def test_03_traceable_adjustment_at_threshold(self):
        # Provide 3 records (meets threshold)
        records = [
            PostPerformanceRecord(
                record_id=f"REC-0{i}", content_id=f"C-0{i}", campaign_id="PAT_01_TECHNICAL_TELEMETRY",
                platform="X", deployments=MetricValue.measured(7.0), recorded_at="2026-09-10"
            )
            for i in range(1, 4)
        ]
        adj = self.weighting.evaluate_and_adjust_pattern("PAT_01_TECHNICAL_TELEMETRY", records)
        self.assertIsNotNone(adj)
        self.assertEqual(adj.sample_size, 3)
        self.assertEqual(adj.previous_weight, 1.0)
        self.assertEqual(adj.new_weight, 1.15)
        self.assertIn("Empirical high conversion", adj.reason)
        self.assertTrue(self.temp_adj_file.exists())

    def test_04_brain_db_remains_unmutated_by_learning(self):
        brain_patterns = DEFAULT_CONFIG.brain_db_dir / "patterns.jsonl"
        mod_before = brain_patterns.stat().st_mtime
        # Perform learning updates
        _ = self.test_03_traceable_adjustment_at_threshold()
        mod_after = brain_patterns.stat().st_mtime
        self.assertEqual(mod_before, mod_after, "Learning loop adjustments must never mutate canonical Brain DB.")


if __name__ == "__main__":
    unittest.main()
