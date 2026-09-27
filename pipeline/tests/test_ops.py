"""Budget, rate limits, the paid-call guard and alerts.

    .venv/Scripts/python.exe -m unittest pipeline.tests.test_ops -v
"""
from __future__ import annotations

import os

os.environ["BRAIN_BACKEND"] = "sqlite"
os.environ["OPS_ALERTS"] = "0"      # tests never page the owner
os.environ["BRAIN_MCP_DISABLE"] = "1"

import io
import json
import shutil
import tempfile
import unittest
import urllib.request
from pathlib import Path
from unittest import mock

from pipeline.ops import alerts as A
from pipeline.ops import budget as B
from pipeline.ops import guard as G


class FakeResp(io.BytesIO):
    status = 200

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


class OpsTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        cfg = {"daily_usd": 1.0, "alert_at": 0.8, "services": {"veo": 0.5},
               "limits": {"assistant_per_minute": 2, "assistant_per_day": 3},
               "rates": {"gemini": {"input_per_1m": 1.0, "output_per_1m": 2.0, "per_call_estimate": 0.01},
                         "veo": {"per_call": 0.3}, "apify": {"per_call": 0.01, "per_result": 0.001}}}
        (self.tmp / "budget.json").write_text(json.dumps(cfg), encoding="utf-8")
        self.sent = []
        self.patches = [mock.patch.object(B, "LOCAL_DB", self.tmp / "ops.db"),
                        mock.patch.object(B, "CONFIG", self.tmp / "budget.json"),
                        mock.patch.object(B, "_cfg_cache", (0.0, {})),
                        mock.patch.object(A, "_telegram", lambda text: self.sent.append(text) or True)]
        for p in self.patches:
            p.start()

    def tearDown(self):
        for p in self.patches:
            p.stop()
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_classify(self):
        g = "https://generativelanguage.googleapis.com/v1beta/models/"
        self.assertEqual(G.classify(g + "gemini-3.8-flash:generateContent?key=x", "POST"), "gemini")
        self.assertEqual(G.classify(g + "gemini-3.1-flash-image:generateContent", "POST"), "image")
        self.assertEqual(G.classify(g + "veo-3.1-generate-001:predictLongRunning", "POST"), "veo")
        self.assertEqual(G.classify(g + "gemini-embedding-2:batchEmbedContents", "POST"), "embed")
        self.assertIsNone(G.classify(g.replace("/models/", "/operations/") + "abc", "GET"))     # a poll
        self.assertEqual(G.classify("https://api.apify.com/v2/acts/x/run-sync-get-dataset-items", "POST"), "apify")
        self.assertIsNone(G.classify("https://api.telegram.org/bot1/sendMessage", "POST"))

    def test_guard_counts_tokens_and_refuses_over_cap(self):
        body = json.dumps({"usageMetadata": {"promptTokenCount": 100000, "candidatesTokenCount": 50000}}).encode()
        url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash:generateContent"
        with mock.patch.object(G, "_orig", lambda *a, **k: FakeResp(body)):
            with G._guarded(urllib.request.Request(url, data=b"{}", method="POST")) as r:
                r.read()
        s = B.spent()["gemini"]
        self.assertEqual((s["input_tokens"], s["output_tokens"]), (100000, 50000))
        self.assertAlmostEqual(s["usd"], 0.1 + 0.1, places=6)
        # Veo: 0.3 a call, capped at 0.5 — the second call is allowed, the third is not made.
        veo = "https://generativelanguage.googleapis.com/v1beta/models/veo-3.1:predictLongRunning"
        made = []
        with mock.patch.object(G, "_orig", lambda *a, **k: made.append(1) or FakeResp(b"{}")):
            for _ in range(2):
                with G._guarded(urllib.request.Request(veo, data=b"{}", method="POST")) as r:
                    r.read()
            with self.assertRaises(B.BudgetExceeded):
                G._guarded(urllib.request.Request(veo, data=b"{}", method="POST"))
        self.assertEqual(len(made), 2)

    def test_daily_total_alerts_at_80_and_100(self):
        B.add("gemini", 0.85)
        self.assertTrue(any("80%" in t or "85%" in t for t in self.sent))
        B.add("gemini", 0.2)
        self.assertTrue(any("used up" in t for t in self.sent))
        with self.assertRaises(B.BudgetExceeded):
            B.check("gemini")

    def test_rate_limit(self):
        B.hit("assistant_turn", per_minute=2, per_day=3)
        B.hit("assistant_turn", per_minute=2, per_day=3)
        with self.assertRaises(B.BudgetExceeded) as e:
            B.hit("assistant_turn", per_minute=2, per_day=3)
        self.assertIn("a minute", str(e.exception))

    def test_alerts_are_sent_once_per_window(self):
        self.assertTrue(A.send("x", "first"))
        self.assertFalse(A.send("x", "again"))
        rows = A.recent()["alerts"]
        self.assertEqual(rows[0]["count"], 2)

    def test_errors_alert_on_first_sighting_only(self):
        A.capture("scheduler notion_sync", RuntimeError("Notion 401"))
        A.capture("scheduler notion_sync", RuntimeError("Notion 401"))
        self.assertEqual(sum("New error" in t for t in self.sent), 1)
        self.assertEqual(A.recent()["errors"][0]["count"], 2)


if __name__ == "__main__":
    unittest.main()
