"""Public watch into the brain, without the network: trust levels, dedupe by
URL, and agents told that news is context, not a claim.

    .venv/Scripts/python.exe -m unittest pipeline.tests.test_brain_watch -v
"""
from __future__ import annotations

import os

os.environ["BRAIN_MCP_DISABLE"] = "1"
os.environ["BRAIN_BACKEND"] = "sqlite"
os.environ["OPS_ALERTS"] = "0"      # tests never page the owner

import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from pipeline.brand_brain import store as S
from pipeline.brand_brain import watch as W
from pipeline.brand_brain.client import Brain

ITEMS = [
    {"url": "https://acme.xyz/blog/v2", "title": "Acme V2 is live", "text": "Today we ship V2 vaults.",
     "at": "2026-09-25T10:00:00Z", "via": "blog", "owned": True, "by": "Acme"},
    {"url": "https://news.example/acme-exploit", "title": "Acme vault drained", "text": "An exploit ...",
     "at": "2026-09-26T08:00:00Z", "via": "news", "owned": False, "by": "Example News"},
    {"url": "https://news.example/acme-launch", "title": "Acme launches V3", "text": "Reportedly V3 ...",
     "at": "2026-09-26T09:00:00Z", "via": "news", "owned": False, "by": "Example News"},
    {"url": "https://reddit.com/r/x/1", "title": "free airdrop", "text": "click here",
     "at": "2026-09-26T09:00:00Z", "via": "reddit", "owned": False},
]


def fake_classify(name, items):
    kinds = {"acme.xyz/blog/v2": "feature_launch", "acme-exploit": "incident",
             "acme-launch": "feature_launch", "reddit.com": "noise"}
    out = []
    for it in items:
        kind = next(k for u, k in kinds.items() if u in it["url"])
        if kind in W.OWN_ONLY and not it.get("owned"):
            kind = "mention"                         # what classify() enforces
        out.append({**it, "about": kind != "noise", "kind": kind, "c_title": it["title"],
                    "c_detail": it["by"] if it.get("by") else ""})
    return out


class BrainWatchTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.p = [mock.patch.object(S, "ROOT", self.tmp / "tenants"),
                  mock.patch("pipeline.brand_brain.embed.texts", side_effect=RuntimeError("offline"))]
        for p in self.p:
            p.start()
        Brain("acme", create=True).save_profile({"company": {"name": "Acme"}}, status="approved")

    def tearDown(self):
        for p in self.p:
            p.stop()
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_trust_levels_events_and_dedupe(self):
        n = W.ingest("acme", ITEMS, classify_fn=fake_classify)
        self.assertEqual((n["new"], n["stored"], n["noise"]), (4, 3, 1))
        b = Brain("acme")
        own = b.search_knowledge("V2 vaults", k=5, max_authority=5)
        self.assertEqual(own[0]["authority"], W.OWN_AUTHORITY)
        # Agents search at authority <= 4: the exploit report is not there for them.
        self.assertFalse([h for h in b.search_knowledge("vault drained exploit", k=5, max_authority=4)
                          if "exploit" in h["url"]])
        ext = [h for h in b.search_knowledge("vault drained exploit", k=5, max_authority=5) if "exploit" in h["url"]]
        self.assertEqual(ext[0]["authority"], W.EXTERNAL)
        ev = {e["url"]: e for e in b.get_whats_new(limit=10)}
        self.assertEqual(ev["https://acme.xyz/blog/v2"]["source"], "company:blog")
        self.assertEqual(ev["https://news.example/acme-exploit"]["kind"], "incident")
        self.assertNotIn("https://news.example/acme-launch", ev)       # a news "launch" is only a mention
        again = W.ingest("acme", ITEMS, classify_fn=fake_classify)
        self.assertEqual(again["new"], 0)                                # each URL once

    def test_agents_see_news_as_context_only(self):
        from pipeline.brand_brain import context as C
        W.ingest("acme", ITEMS, classify_fn=fake_classify)
        block = C.whats_new_block(days=3650, tenant="acme")
        head, news = block.split("IN THE NEWS", 1)
        self.assertIn("Acme V2 is live", head)
        self.assertIn("Acme vault drained", news)
        self.assertIn("do not repeat allegations", news)


if __name__ == "__main__":
    unittest.main()
