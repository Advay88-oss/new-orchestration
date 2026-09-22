#!/usr/bin/env python3
"""Canonical Creative Memory Event Stream (pipeline/creative_memory/canonical_events.py).

Fulfills Mandates 11 & 12:
  - Eliminates duplicate writes across approved/rejected/reward files.
  - Standardizes canonical event types:
      CREATIVE_GENERATED
      CREATIVE_REVIEWED
      CREATIVE_APPROVED
      CREATIVE_REJECTED
      CREATIVE_REGENERATED
      HUMAN_APPROVED
      HUMAN_REJECTED
      PERFORMANCE_OBSERVED
      REWARD_UPDATED
  - Stores nuanced, principled human feedback (e.g. 'wrong object', 'too cinematic', 'too similar').
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

REPO_ROOT = Path(__file__).resolve().parents[2]
MEMORY_DIR = REPO_ROOT / "pipeline" / "creative_memory"
MEMORY_DIR.mkdir(parents=True, exist_ok=True)
CANONICAL_EVENTS_FILE = MEMORY_DIR / "canonical_creative_events.jsonl"


@dataclass
class CanonicalCreativeEvent:
    event_id: str
    event_type: str  # One of the canonical event types
    run_id: str
    asset_id: str
    content_type: str
    timestamp: str
    payload: Dict[str, Any]
    human_feedback: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class CanonicalCreativeEventStore:
    """Manages deduplicated canonical event logging and principled feedback ingestion."""

    def __init__(self, events_file: Optional[Path] = None):
        self.events_file = events_file or CANONICAL_EVENTS_FILE
        self._seen_event_keys: Set[str] = set()
        self._load_seen_keys()

    def _load_seen_keys(self) -> None:
        """Loads existing event keys to guarantee idempotent deduplication."""
        if not self.events_file.exists():
            return
        for line in self.events_file.read_text(encoding="utf-8", errors="ignore").splitlines():
            line = line.strip()
            if line:
                try:
                    data = json.loads(line)
                    k = f"{data.get('event_type')}:{data.get('run_id')}:{data.get('asset_id')}"
                    self._seen_event_keys.add(k)
                except Exception:
                    pass

    def record_event(
        self,
        event_type: str,
        run_id: str,
        asset_id: str,
        content_type: str,
        payload: Dict[str, Any],
        human_feedback: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Appends event if and only if it has not been recorded previously (idempotent)."""
        dedup_key = f"{event_type}:{run_id}:{asset_id}"
        if dedup_key in self._seen_event_keys:
            # Duplicate write blocked!
            return False

        event = CanonicalCreativeEvent(
            event_id=f"EVT_{event_type}_{int(datetime.now(timezone.utc).timestamp()*1000)}",
            event_type=event_type,
            run_id=run_id,
            asset_id=asset_id,
            content_type=content_type,
            timestamp=datetime.now(timezone.utc).isoformat(),
            payload=payload,
            human_feedback=human_feedback
        )

        with self.events_file.open("a", encoding="utf-8") as f:
            f.write(json.dumps(event.to_dict()) + "\n")

        self._seen_event_keys.add(dedup_key)
        return True

    def ingest_human_feedback(
        self,
        run_id: str,
        asset_id: str,
        content_type: str,
        feedback_type: str,  # APPROVE | REVISE | REJECT | REGENERATE
        tags: List[str],  # e.g. ["too_cinematic", "wrong_object", "too_basic", "too_similar"]
        critique_notes: str,
        specific_modifications: Optional[Dict[str, str]] = None
    ) -> None:
        """Records nuanced human feedback with fine-grained attribution."""
        feedback_payload = {
            "feedback_type": feedback_type,
            "tags": tags,
            "critique_notes": critique_notes,
            "specific_modifications": specific_modifications or {},
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        evt_type = "HUMAN_APPROVED" if feedback_type == "APPROVE" else "HUMAN_REJECTED"
        self.record_event(
            event_type=evt_type,
            run_id=run_id,
            asset_id=asset_id,
            content_type=content_type,
            payload=feedback_payload,
            human_feedback=feedback_payload
        )
        print(f"📝 [CanonicalEvents] Ingested human feedback for {asset_id}: {feedback_type} (Tags: {tags})")

    def get_recent_fingerprints(self, limit: int = 15) -> List[Dict[str, Any]]:
        """Retrieves recent creative fingerprints for fatigue tracking and novelty auditing."""
        fps = []
        if not self.events_file.exists():
            return []
        lines = self.events_file.read_text(encoding="utf-8", errors="ignore").splitlines()
        for line in reversed(lines):
            line = line.strip()
            if line:
                try:
                    data = json.loads(line)
                    if data.get("event_type") in ["CREATIVE_GENERATED", "CREATIVE_APPROVED"]:
                        fp = data.get("payload", {}).get("fingerprint")
                        if fp:
                            fps.append(fp)
                            if len(fps) >= limit:
                                break
                except Exception:
                    pass
        return fps
