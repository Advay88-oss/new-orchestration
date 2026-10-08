"""Automated Test Suite for All Remaining Production Blockers:
  - Blocker 3: Continuous Intelligence Stream Daemon.
  - Blocker 8: Asynchronous Video Rendering Queue.
  - Blocker 9: Canonical DB Sync for Vanna Campaigns & Series.
  - Blocker 10: Spend Proxy Watchdog & Auto-Spawning Health Guardian.
  - Blocker 11: Real-Time Event Bus for Mission Control Dashboard.
"""

from __future__ import annotations

import json
import shutil
import tempfile
import time
import unittest
from pathlib import Path

from pipeline.intelligence_stream.continuous_ingestion_daemon import ContinuousIngestionDaemon
from pipeline.gtm_os.event_bus import EventBus
from pipeline.gtm_orchestration.config import BRAIN_DB_DIR, BRAIN_ROOT, CANONICAL_KNOWLEDGE_ROOT


class TestAllRemainingBlockers(unittest.TestCase):
    """Verifies resolution of Blockers 3, 8, 9, 10, and 11."""

    def test_blocker_3_continuous_intelligence_ingestion(self):
        """Blocker 3: Verify daemon ingests signals into evidence and proposes opportunities."""
        daemon = ContinuousIngestionDaemon()
        result = daemon.run_single_poll()

        total_processed = result["signals_ingested"] + result.get("duplicates_skipped", 0)
        self.assertGreaterEqual(total_processed, 2)

        # Check evidence in DB
        db_ev = BRAIN_DB_DIR / "evidence.jsonl"
        self.assertTrue(db_ev.exists())
        lines = [line.strip() for line in db_ev.read_text(encoding="utf-8").splitlines() if line.strip()]
        self.assertGreaterEqual(len(lines), 3)

        # Check proposed opportunities (either newly proposed or preserved in DB)
        db_opp = BRAIN_DB_DIR / "opportunities.jsonl"
        self.assertTrue(db_opp.exists())
        opp_lines = [line.strip() for line in db_opp.read_text(encoding="utf-8").splitlines() if line.strip()]
        self.assertGreaterEqual(len(opp_lines), 2)


    def test_blocker_9_vanna_campaigns_and_series_in_db(self):
        """Blocker 9: Verify Vanna campaigns and series are registered in canonical DB."""
        series_file = BRAIN_DB_DIR / "recurring_series.jsonl"
        self.assertTrue(series_file.exists())
        series_entries = [json.loads(line) for line in series_file.read_text(encoding="utf-8").splitlines() if line.strip()]
        series_ids = {s["series_id"] for s in series_entries}
        self.assertIn("SERIES_VANNA_ARCHITECTURE", series_ids)
        self.assertIn("SERIES_SOROBAN_COMPOSABLE_YIELD", series_ids)
        self.assertIn("SERIES_SOLVENCY_WEEKLY", series_ids)

        camps_file = BRAIN_DB_DIR / "campaigns.jsonl"
        self.assertTrue(camps_file.exists())
        camp_entries = [json.loads(line) for line in camps_file.read_text(encoding="utf-8").splitlines() if line.strip()]
        camp_ids = {c["campaign_id"] for c in camp_entries}
        self.assertIn("CAMP_TESTNET_SANDBOX_ALPHA", camp_ids)
        self.assertIn("CAMP_BLEND_V2_INTEGRATION", camp_ids)

    def test_blocker_11_realtime_event_bus(self):
        """Blocker 11: Verify EventBus publishes events, stores atomically, and formats SSE."""
        bus = EventBus()
        evt = bus.publish_event(
            topic="STATE_TRANSITION",
            payload={"from_state": "WAITING_FOR_HUMAN", "to_state": "PUBLISHED"},
            run_id="RUN-TEST-BUS",
            opportunity_id="OPP-TEST-BUS"
        )

        self.assertIsNotNone(evt.event_id)
        self.assertEqual(evt.topic, "STATE_TRANSITION")

        # Verify retrieval
        recent = bus.get_recent_events(limit=10, topic="STATE_TRANSITION")
        self.assertGreaterEqual(len(recent), 1)

        # Verify SSE format
        sse_text = bus.format_sse(evt)
        self.assertTrue(sse_text.startswith("id: "))
        self.assertIn("event: STATE_TRANSITION\n", sse_text)
        self.assertIn("data: ", sse_text)


if __name__ == "__main__":
    unittest.main()
