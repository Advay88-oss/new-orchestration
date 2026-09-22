"""Phase 8: Central Learning Engine (learning_engine.py).

Connects what we thought would work with what actually happened.
Updates pattern weights without corrupting the canonical Brain DB.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone

REPO_ROOT = Path(__file__).resolve().parents[2]
STATE_DIR = REPO_ROOT / "pipeline" / "state"

from pipeline.gtm_learning.performance_store import PerformanceStore
from pipeline.gtm_learning.pattern_weighting import PatternWeightingEngine
from pipeline.gtm_learning.outcome_schema import PatternAdjustmentRecord


class LearningEngine:
    """The central closed-loop learning engine."""

    def __init__(self):
        self.performance_store = PerformanceStore()
        self.weighting_engine = PatternWeightingEngine()

    def process_feedback_loop(self) -> List[PatternAdjustmentRecord]:
        """Process stored performance records and update pattern weights."""
        records = self.performance_store.list_records()
        adjustments = []

        # Group by pattern if metadata exists
        by_pattern: Dict[str, List[Any]] = {}
        for r in records:
            pat_id = getattr(r, "campaign_id", None) or "PAT_01_TECHNICAL_TELEMETRY"
            by_pattern.setdefault(pat_id, []).append(r)

        for pat_id, outcomes in by_pattern.items():
            adj = self.weighting_engine.evaluate_and_adjust_pattern(pat_id, outcomes)
            if adj:
                adjustments.append(adj)

        return adjustments
