"""Phase 11: Real-Time Event Bus for Mission Control Dashboard (event_bus.py).

Fixes Blocker 11 (Real-Time Dashboard Sync).
Publishes structured lifecycle and telemetry events for the Mission Control Cockpit (:3000).
Supports:
  - Persistent event stream in mission_control_events.jsonl via AtomicJsonlStore.
  - Server-Sent Events (SSE) formatting for web browser consumers.
  - Event filtering by topic and timestamp.
"""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

REPO_ROOT = Path("D:/new orchestration")
STATE_DIR = REPO_ROOT / "pipeline" / "state"
EVENTS_FILE = STATE_DIR / "mission_control_events.jsonl"

from pipeline.gtm_storage.atomic_store import AtomicJsonlStore


class MissionControlEvent(BaseModel):
    """Event emitted across the GTM Operating System."""
    event_id: str
    topic: str  # e.g., 'STATE_TRANSITION', 'APPROVAL_REQUESTED', 'POST_PUBLISHED', 'METRIC_SYNC'
    run_id: Optional[str] = None
    opportunity_id: Optional[str] = None
    payload: Dict[str, Any] = Field(default_factory=dict)
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class EventBus:
    """Central event bus for real-time dashboard notifications."""

    def __init__(self, events_file: Optional[Path] = None):
        self.events_file = events_file or EVENTS_FILE
        self.store = AtomicJsonlStore(self.events_file)

    def publish_event(
        self,
        topic: str,
        payload: Dict[str, Any],
        run_id: Optional[str] = None,
        opportunity_id: Optional[str] = None
    ) -> MissionControlEvent:
        """Publishes an event to the persistent event stream."""
        event_id = f"EVT-{int(time.time() * 1000)}-{topic[:6]}"
        evt = MissionControlEvent(
            event_id=event_id,
            topic=topic,
            run_id=run_id,
            opportunity_id=opportunity_id,
            payload=payload
        )
        self.store.append(evt.model_dump())
        return evt

    def get_recent_events(
        self,
        limit: int = 50,
        topic: Optional[str] = None
    ) -> List[MissionControlEvent]:
        """Fetches the most recent events."""
        records = self.store.read_all()
        if topic:
            records = [r for r in records if r.get("topic") == topic]
        records = records[-limit:]
        return [MissionControlEvent(**r) for r in records]

    def format_sse(self, event: MissionControlEvent) -> str:
        """Formats an event as a Server-Sent Events (SSE) message."""
        data_json = json.dumps(event.model_dump())
        return f"id: {event.event_id}\nevent: {event.topic}\ndata: {data_json}\n\n"
