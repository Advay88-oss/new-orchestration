"""Phase 8: Performance Store (performance_store.py).

Persists and queries real outcome data.
Strictly enforces NULL != 0.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone

REPO_ROOT = Path(__file__).resolve().parents[2]
STATE_DIR = REPO_ROOT / "pipeline" / "state"

from pipeline.gtm_learning.outcome_schema import PostPerformanceRecord, MetricValue
from pipeline.gtm_storage.atomic_store import AtomicJsonlStore


class PerformanceStore:
    """Manages performance outcome storage without fabricating missing metrics.
    Protected by atomic inter-process file locks.
    """

    def __init__(self, storage_file: Optional[Path] = None):
        self.storage_file = storage_file or (STATE_DIR / "performance_records.jsonl")
        self.atomic_store = AtomicJsonlStore(self.storage_file)

    def record_performance(self, record: PostPerformanceRecord) -> None:
        """Append a validated performance record atomically."""
        self.atomic_store.append(record.model_dump())

    def get_performance(self, content_id: str) -> Optional[PostPerformanceRecord]:
        """Fetch performance record for a specific content ID."""
        for rec in self.list_records():
            if rec.content_id == content_id:
                return rec
        return None

    def list_records(self) -> List[PostPerformanceRecord]:
        """List all performance records atomically."""
        raw_records = self.atomic_store.read_all()
        return [PostPerformanceRecord(**r) for r in raw_records]
