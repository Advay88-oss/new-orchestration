"""Phase 8: Pattern Weighting Engine (pattern_weighting.py).

Enforces:
  - Minimum sample size threshold (>= 3 observations) before updating weights.
  - Full traceability: previous_weight, new_weight, sample_size, confidence, reason.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone

REPO_ROOT = Path(__file__).resolve().parents[2]
STATE_DIR = REPO_ROOT / "pipeline" / "state"

from pipeline.gtm_learning.outcome_schema import PatternAdjustmentRecord, PostPerformanceRecord


class PatternWeightingEngine:
    """Manages empirical pattern weights with strict sample size thresholds."""

    MIN_SAMPLE_SIZE = 3

    def __init__(self, storage_file: Optional[Path] = None):
        self.storage_file = storage_file or (STATE_DIR / "learned_pattern_adjustments.jsonl")
        self.storage_file.parent.mkdir(parents=True, exist_ok=True)
        self.weights: Dict[str, float] = {
            "PAT_01_TECHNICAL_TELEMETRY": 1.0,
            "PAT_02_COMPETITOR_DISPLACEMENT": 1.0,
            "PAT_03_PARTNER_INTEGRATION": 1.0
        }
        # The weights are rebuilt from the adjustment log: the last new_weight
        # per pattern. They were an in-memory dict reset to 1.0 on every
        # construction, so each run re-applied the same first step — 151 of
        # 157 logged adjustments were "1.0 -> 1.15". The log is the record, so
        # it is also the state; there is no second file to drift from it.
        try:
            for line in self.storage_file.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    row = json.loads(line)
                    self.weights[str(row["pattern_id"])] = float(row["new_weight"])
        except FileNotFoundError:
            pass

    def get_exploration_priority(self, pattern_id: str, observed_outcomes: List[PostPerformanceRecord]) -> float:
        """Computes Bayesian UCB exploration priority for patterns with low sample size."""
        base_weight = self.weights.get(pattern_id, 1.0)
        n = len(observed_outcomes)
        uncertainty_bonus = 0.25 / (1.0 + n)
        return round(base_weight + uncertainty_bonus, 3)

    def evaluate_and_adjust_pattern(
        self,
        pattern_id: str,
        observed_outcomes: List[PostPerformanceRecord]
    ) -> Optional[PatternAdjustmentRecord]:
        """Evaluate performance and update weight if sample size threshold is met."""
        if len(observed_outcomes) < self.MIN_SAMPLE_SIZE:
            print(f"⚠️ PATTERN WEIGHTING: Insufficient sample size ({len(observed_outcomes)} < {self.MIN_SAMPLE_SIZE}) for {pattern_id}. Adjustment suppressed.")
            return None

        # Calculate average clicks / deployments
        measured_deployments = [
            o.deployments.raw_value for o in observed_outcomes
            if o.deployments.status == "MEASURED" and o.deployments.raw_value is not None
        ]

        if not measured_deployments:
            return None

        avg_dep = sum(measured_deployments) / len(measured_deployments)
        prev_weight = self.weights.get(pattern_id, 1.0)

        # Learning adjustment factor
        if avg_dep >= 5.0:
            delta = +0.15
            reason = f"Empirical high conversion: {avg_dep:.1f} avg sandbox deployments across {len(observed_outcomes)} posts."
        elif avg_dep == 0.0:
            delta = -0.15
            reason = f"Empirical zero conversion across {len(observed_outcomes)} observed posts."
        else:
            delta = +0.05
            reason = f"Moderate conversion performance ({avg_dep:.1f} avg deployments)."

        new_weight = round(max(0.2, min(2.0, prev_weight + delta)), 2)
        self.weights[pattern_id] = new_weight

        record = PatternAdjustmentRecord(
            adjustment_id=f"ADJ-{pattern_id}-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M')}",
            pattern_id=pattern_id,
            previous_weight=prev_weight,
            new_weight=new_weight,
            evidence_refs=[o.record_id for o in observed_outcomes],
            sample_size=len(observed_outcomes),
            confidence=0.85,
            timestamp=datetime.now(timezone.utc).isoformat(),
            reason=reason
        )

        with open(self.storage_file, "a", encoding="utf-8") as f:
            f.write(record.model_dump_json() + "\n")

        print(f"📈 PATTERN WEIGHTING: Adjusted {pattern_id} weight: {prev_weight} -> {new_weight} ({reason})")
        return record
