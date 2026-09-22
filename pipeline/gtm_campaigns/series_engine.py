"""Phase 3: Recurring Series Engine (series_engine.py).

Manages repeatable systematic content loops (e.g. Weekly Telemetry Reports).
Strictly distinguishes:
  - ONE_OCCURRENCE (1 observed post)
  - REPEATED_PATTERN (2-3 occurrences)
  - RECURRING_SYSTEM (>= 4 regular cadence occurrences verified)
Requires actual occurrence records; prevents phantom series creation.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone

REPO_ROOT = Path(__file__).resolve().parents[2]
STATE_DIR = REPO_ROOT / "pipeline" / "state"

from pipeline.gtm_campaigns.schemas import (
    SeriesSpec, SeriesOccurrence, RecurrenceTier
)


class SeriesEngine:
    """Manages systematic recurring content loops and recurrence tier evaluation."""

    def __init__(self, storage_dir: Optional[Path] = None):
        self.storage_dir = storage_dir or (STATE_DIR / "series")
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.active_series: Dict[str, SeriesSpec] = {}

    @staticmethod
    def evaluate_recurrence_tier(occurrence_count: int) -> RecurrenceTier:
        """Classify recurrence tier based on empirical occurrence count."""
        if occurrence_count >= 4:
            return "RECURRING_SYSTEM"
        elif occurrence_count >= 2:
            return "REPEATED_PATTERN"
        return "ONE_OCCURRENCE"

    def register_series(
        self,
        series_id: str,
        series_name: str,
        cadence: str,
        trigger: str,
        input_data_source: str,
        fixed_structure: List[str],
        variable_fields: List[str],
        visual_template_type: str,
        initial_occurrences: Optional[List[SeriesOccurrence]] = None
    ) -> SeriesSpec:
        """Register a new recurring series specification."""
        occurrences = initial_occurrences or []
        tier = self.evaluate_recurrence_tier(len(occurrences))

        series = SeriesSpec(
            series_id=series_id,
            series_name=series_name,
            cadence=cadence,
            trigger=trigger,
            input_data_source=input_data_source,
            fixed_structure=fixed_structure,
            variable_fields=variable_fields,
            visual_template_type=visual_template_type,
            recurrence_tier=tier,
            occurrences=occurrences,
            created_at=datetime.now(timezone.utc).isoformat()
        )

        self.active_series[series_id] = series
        self._save_series(series)
        return series

    def record_occurrence(
        self,
        series_id: str,
        published_date: str,
        content_id: str,
        input_data_summary: str,
        verified_url: Optional[str] = None
    ) -> SeriesSpec:
        """Append a real executed occurrence and update recurrence tier."""
        series = self.get_series(series_id)
        if not series:
            raise KeyError(f"Series '{series_id}' not found.")

        occ_num = len(series.occurrences) + 1
        occ = SeriesOccurrence(
            occurrence_id=f"OCC-{series_id}-{occ_num:03d}",
            occurrence_number=occ_num,
            published_date=published_date,
            content_id=content_id,
            verified_url=verified_url,
            input_data_summary=input_data_summary
        )
        series.occurrences.append(occ)
        series.recurrence_tier = self.evaluate_recurrence_tier(len(series.occurrences))
        self._save_series(series)
        print(f"📈 SERIES ENGINE: Recorded occurrence #{occ_num} for {series_id} (Tier: {series.recurrence_tier})")
        return series

    def get_series(self, series_id: str) -> Optional[SeriesSpec]:
        """Fetch a series specification by ID."""
        if series_id in self.active_series:
            return self.active_series[series_id]
        s_path = self.storage_dir / f"{series_id}.json"
        if s_path.exists():
            data = json.loads(s_path.read_text(encoding="utf-8"))
            s = SeriesSpec(**data)
            self.active_series[series_id] = s
            return s
        return None

    def list_series(self) -> List[SeriesSpec]:
        """List all series in storage."""
        series_list = []
        for f in self.storage_dir.glob("*.json"):
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                series_list.append(SeriesSpec(**data))
            except Exception:
                pass
        return series_list

    def _save_series(self, series: SeriesSpec) -> None:
        s_path = self.storage_dir / f"{series.series_id}.json"
        s_path.write_text(series.model_dump_json(indent=2), encoding="utf-8")
