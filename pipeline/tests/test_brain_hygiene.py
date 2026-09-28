"""Brain hygiene: the same passage is stored once across pages, legal pages
stay out of the agents' searches, and pricing figures are checked verbatim.

    .venv/Scripts/python.exe -m unittest pipeline.tests.test_brain_hygiene -v
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
from pipeline.brand_brain.chunking import chunk_markdown, chunk_page, page_kind
from pipeline.brand_brain.client import Brain

PARA = ("Isolated SmartAccounts keep each borrower's positions in their own contract, so one "
        "account's liquidation never touches another's collateral.")


class HygieneTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.p = [mock.patch.object(S, "ROOT", self.tmp / "tenants"),
                  mock.patch("pipeline.brand_brain.embed.texts", side_effect=RuntimeError("offline"))]
        for p in self.p:
            p.start()
        self.b = Brain("acme", create=True)

    def tearDown(self):
        for p in self.p:
            p.stop()
        shutil.rmtree(self.tmp, ignore_errors=True)

    def page(self, url, text=PARA, title="Features", authority=3):
        return self.b.upsert_page("website:" + url, chunk_page(text, title=title, company="Acme",
                                  source_label="website"), source="website", authority=authority, url=url)

    def test_same_passage_stored_once_across_pages(self):
        self.assertEqual(self.page("https://acme.xyz/")["added_or_changed"], 1)
        r = self.page("https://acme.xyz/features")
        self.assertEqual((r["added_or_changed"], r["duplicates"]), (0, 1))
        hits = self.b.search_knowledge("isolated SmartAccounts liquidation", k=5)
        self.assertEqual(len(hits), 1)
        # A less trusted page does not hide a more trusted one's copy.
        r = self.b.upsert_page("docs:features", chunk_markdown("## Isolation\n\n" + PARA, title="Docs",
                               company="Acme", source_label="docs"), source="docs", authority=2)
        self.assertEqual((r["duplicates"], r["added_or_changed"] >= 1), (0, True))

    def test_tagging_and_legal_out_of_agent_search(self):
        self.assertEqual(page_kind("website:https://acme.xyz/terms-of-service"), "legal")
        self.assertEqual(page_kind("docs:oracle", "Price oracle"), None)
        self.assertEqual(page_kind("docs:fees", "Fees"), "pricing")
        self.page("https://acme.xyz/terms-of-service",
                  "Acme is not liable for any loss of funds arising from the use of isolated SmartAccounts "
                  "or liquidation events on the protocol.", title="Terms of Service")
        self.page("https://acme.xyz/pricing", "Opening a SmartAccount costs a flat fee of 0.10% of the "
                  "borrowed amount, charged once at open; there are no monthly fees.", title="Pricing")
        agent = self.b.search_knowledge("liable loss of funds liquidation", k=5)
        self.assertFalse([h for h in agent if h["content_type"] == "legal"])
        owner = self.b.search_knowledge("liable loss of funds liquidation", k=5, include_legal=True)
        self.assertTrue([h for h in owner if h["content_type"] == "legal"])
        fee = self.b.search_knowledge("SmartAccount open fee", k=3)
        self.assertEqual(fee[0]["content_type"], "pricing")

    def test_tidy_cleans_an_old_brain(self):
        self.page("https://acme.xyz/")
        # As if stored before dedupe existed: write the copy directly.
        with self.b._db() as con:
            con.execute("INSERT INTO chunks(id, source, authority, url, page_id, title, section, content_type, "
                        "prefix, text, hash, updated_at, deleted) VALUES ('website:dup','website',3,'u',"
                        "'website:https://acme.xyz/legal','Legal','Legal','blog','p',?, 'h','2026-01-01',0)",
                        (PARA,))
        out = self.b.tidy()
        self.assertEqual(out["duplicates_dropped"], 1)
        self.assertEqual(len(self.b.search_knowledge("isolated SmartAccounts", k=5, include_legal=True)), 1)

    def test_pricing_figures_must_match_verbatim(self):
        from pipeline.gtm_os import fact_check as F
        ev = [{"id": "c1", "source": "website", "section": "Pricing", "content_type": "pricing",
               "text": "a flat fee of 0.10% of the borrowed amount", "url": "u"}]
        replies = iter([{"claims": ["Acme charges a 0.25% open fee", "Acme charges a 0.1% open fee"]},
                        {"claims": [{"i": 0, "verdict": "SUPPORTED", "evidence_id": "c1"},
                                    {"i": 1, "verdict": "SUPPORTED", "evidence_id": "c1"}]}])
        with mock.patch("pipeline.gtm_os.agent_runtime.brain_json", lambda *a, **k: next(replies)), \
             mock.patch("pipeline.brand_brain.context.knowledge_hits", lambda *a, **k: ev), \
             mock.patch("pipeline.brand_brain.context.company_name", lambda *a, **k: "Acme"), \
             mock.patch.object(F, "_gate", lambda t: []):
            out = F.check_copy("hook", "copy")
        verdicts = [c["verdict"] for c in out["claims"]]
        self.assertEqual(verdicts, ["CONTRADICTED", "SUPPORTED"])
        self.assertIn("0.25%", out["blocked"][0])


if __name__ == "__main__":
    unittest.main()
