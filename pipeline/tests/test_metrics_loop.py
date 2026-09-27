"""The format and posting-slot arms, and engagement read back after posting.

Approve -> the founder replies with the X link (Telegram) -> 48 hours later
the collector reads the post (a fake Apify) -> the run's outcome and reward
event carry what was actually published: its format and its posting slot.

    .venv/Scripts/python.exe -m unittest pipeline.tests.test_metrics_loop -v
"""
from __future__ import annotations

import os

os.environ["BRAIN_MCP_DISABLE"] = "1"
os.environ["BRAIN_BACKEND"] = "sqlite"
os.environ["OPS_ALERTS"] = "0"      # tests never page the owner

import json
import shutil
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock

from pipeline.brand_brain import store as S
from pipeline.brand_brain.client import Brain
from pipeline.gtm_learning import bandit as B
from pipeline.gtm_learning import feedback as F
from pipeline.gtm_learning import metrics_collector as MC
from pipeline.gtm_learning import rewards as R

RID = "GTM-20260920-100000"


class MetricsLoopTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.runs = self.tmp / "runs"
        (self.runs / RID).mkdir(parents=True)
        (self.runs / RID / "summary.json").write_text(json.dumps({
            "run_id": RID, "status": "completed", "review_passed": True, "pillar": "P1",
            "started_at": "2026-09-20T10:00:00+00:00",
            "posts": {"x": {"hook": "Why pool risk?", "copy": "c" * 500}}}), encoding="utf-8")
        (self.runs / RID / "feedback.json").write_text(json.dumps({"latest": {"verdict": "approve"}}),
                                                       encoding="utf-8")
        self.patches = [
            mock.patch.object(S, "ROOT", self.tmp / "tenants"),
            mock.patch.object(R, "RUNS", self.runs),
            mock.patch.object(F, "RUNS", self.runs),
            mock.patch.object(MC, "RUNS", self.runs),
            mock.patch("pipeline.brand_brain.context.current_tenant", lambda: "acme"),
            mock.patch("pipeline.brand_brain.client.current_tenant", lambda: "acme"),
            mock.patch("pipeline.gtm_os.state_sync.push_run", lambda *a, **k: None),
        ]
        for p in self.patches:
            p.start()
        Brain("acme", create=True).save_profile(
            {"company": {"name": "Acme"}, "pillars": ["P1"], "timezone": "UTC"}, status="approved")
        from pipeline.brand_brain import context as C
        C._cache.clear()

    def tearDown(self):
        for p in self.patches:
            p.stop()
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_slot_and_format(self):
        self.assertEqual(R.slot_of("2026-09-20T07:30:00+00:00"), "morning")
        self.assertEqual(R.slot_of("2026-09-20T23:10:00+00:00"), "night")
        self.assertEqual(R.slot_of("2026-09-20T02:00:00+00:00"), "night")
        self.assertEqual(R.format_of({"media": ["video"]}), "video")
        self.assertEqual(R.format_of({"media": ["photo"]}), "image")
        self.assertEqual(R.format_of({"format": "thread", "media": ["photo"]}), "thread")
        self.assertEqual(set(B.options()) >= {"pillar", "format", "hook_type", "length", "slot"}, True)

    def test_recommendation_is_not_credited_until_posted(self):
        ev = R.compute(RID)
        self.assertNotIn("format", ev["arms"])
        self.assertNotIn("slot", ev["arms"])

    def test_link_then_collect_credits_what_was_published(self):
        from pipeline.gtm_os import feedback_listener as L
        replies = []
        with mock.patch.object(L, "STATE", self.tmp), \
             mock.patch.object(L, "POSTED_FILE", self.tmp / "posted.json"), \
             mock.patch.object(L, "_reply", lambda t, c, text: replies.append(text)):
            L._save(L.POSTED_FILE, {"chat_id": 7, "run_id": RID, "at": __import__("time").time()})
            res = L._posted_link("here https://x.com/acme/status/1234567", 7, L.FOUNDER_USER_ID, "tok", None)
        self.assertTrue(res["ok"])
        self.assertIn("Engagement will be read", replies[-1])

        post = {"id": "1234567", "handle": "acme", "text": "t", "url": "https://x.com/acme/status/1234567",
                "created_at": "2026-09-20T17:45:00+00:00", "is_reply": False, "is_retweet": False,
                "impressions": 5000, "likes": 120, "reposts": 30, "replies": 9, "quotes": 2, "bookmarks": 11,
                "media": ["video"]}
        with mock.patch("pipeline.intelligence_stream.x_apify.search", lambda terms, **k: [post]):
            self.assertEqual(MC.collect()["due"], 0)               # not 48 hours old yet
            later = datetime.now(timezone.utc) + timedelta(hours=49)
            with mock.patch.object(MC, "_now", lambda: later):
                out = MC.collect()
        self.assertEqual(len(out["collected"]), 1)
        ev = R.events()[0]
        self.assertEqual(ev["arms"]["format"], "video")
        self.assertEqual(ev["arms"]["slot"], "evening")
        self.assertIsNotNone(R.published_of(RID).get("posted_at"))

    def test_posting_plan(self):
        plan = B.posting_plan({"format": {"choice": "thread", "why": "x"}, "slot": {"choice": "evening", "why": "y"}})
        self.assertEqual((plan["format"], plan["slot"], plan["window"]), ("thread", "evening", "15:00-20:00"))


if __name__ == "__main__":
    unittest.main()
