"""Notion sync against a fake Notion API: baseline import, incremental edits,
classified What's new events, noise ignored, deletions tombstoned.

    .venv/Scripts/python.exe -m unittest pipeline.tests.test_notion_sync -v
"""
from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from pipeline.brand_brain import notion_sync as N
from pipeline.brand_brain import store as S
from pipeline.brand_brain.client import Brain


class FakeNotion:
    def __init__(self):
        self.pages = {}
        self.block_calls = 0

    def page(self, pid, title, edited, paras, created="2026-01-01T00:00:00.000Z"):
        self.pages[pid] = {"id": pid, "object": "page", "last_edited_time": edited, "created_time": created,
                           "url": "https://notion.so/" + pid,
                           "properties": {"Name": {"type": "title", "title": [{"plain_text": title}]}},
                           "_blocks": [{"id": pid + "-h", "type": "heading_2", "heading_2": {"rich_text": [{"plain_text": "Status"}]}}]
                           + [{"id": pid + str(i), "type": "paragraph", "paragraph": {"rich_text": [{"plain_text": p}]}}
                              for i, p in enumerate(paras)]}

    def http(self, method, path, body):
        if path == "search":
            return {"results": sorted(self.pages.values(), key=lambda p: p["last_edited_time"], reverse=True),
                    "has_more": False}
        pid = path.split("/")[1]
        self.block_calls += 1
        return {"results": self.pages[pid]["_blocks"], "has_more": False}


class NotionSyncTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.p = mock.patch.object(S, "ROOT", self.tmp)
        self.p.start()
        # Offline: keyword search only, no embedding calls.
        self.e = mock.patch("pipeline.brand_brain.embed.texts", side_effect=RuntimeError("offline"))
        self.e.start()
        Brain("acme", create=True).save_profile({"company": {"name": "Acme"}}, status="approved")
        self.fake = FakeNotion()
        self.api = N.Notion("t", http=self.fake.http)
        self.kinds = []

        def classify(title, before, after):
            kind = "noise" if "typo" in after else "feature_launch"
            self.kinds.append(kind)
            return {"kind": kind, "title": title + " changed", "detail": "d"}
        self.classify = classify

    def tearDown(self):
        self.p.stop()
        self.e.stop()
        shutil.rmtree(self.tmp, ignore_errors=True)

    def run_sync(self):
        return N.sync("acme", notion=self.api, classify_fn=self.classify)

    def test_baseline_then_incremental(self):
        self.fake.page("p1", "Roadmap", "2026-09-01T00:00:00.000Z", ["Credit lines are in testnet."])
        self.fake.page("p2", "Pricing", "2026-09-01T00:00:00.000Z", ["Fees are fixed."])
        r = self.run_sync()
        self.assertTrue(r["baseline"])
        self.assertEqual((r["changed"], r["events"]), (2, 0))            # an import is not news
        b = Brain("acme")
        self.assertTrue(b.search_knowledge("credit lines testnet"))

        calls = self.fake.block_calls
        r = self.run_sync()                                                # nothing edited
        self.assertEqual((r["changed"], self.fake.block_calls), (0, calls))

        self.fake.page("p1", "Roadmap", "2026-09-20T00:00:00.000Z", ["Credit lines are live on mainnet."])
        r = self.run_sync()
        self.assertEqual((r["changed"], r["events"]), (1, 1))
        ev = b.get_whats_new(None)
        self.assertEqual(ev[0]["kind"], "feature_launch")
        self.assertEqual(ev[0]["at"], "2026-09-20T00:00:00.000Z")

        self.fake.page("p2", "Pricing", "2026-09-21T00:00:00.000Z", ["Fees are fixed (typo fixed)."])
        r = self.run_sync()
        self.assertEqual(r["events"], 0)                                  # noise is not news
        self.assertIn("noise", self.kinds)

        del self.fake.pages["p2"]
        r = self.run_sync()
        self.assertEqual(r["tombstoned"], 1)
        self.assertFalse([h for h in b.search_knowledge("Fees fixed pricing") if "p2" in (h["url"] or "")])

    def test_no_token_is_explained(self):
        with mock.patch.object(N, "_token", lambda: None):
            r = N.sync("acme")
        self.assertFalse(r["ok"])
        self.assertIn("NOTION_TOKEN", r["error"])


if __name__ == "__main__":
    unittest.main()
