"""The brand brain's contract: isolation, the six tools, and no agent reading
company files behind the brain's back.

    .venv/Scripts/python.exe -m unittest pipeline.tests.test_brand_brain -v
"""
from __future__ import annotations

import asyncio
import re
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from pipeline.brand_brain import store as S
from pipeline.brand_brain.chunking import chunk_markdown
from pipeline.brand_brain.client import Brain

REPO = Path(__file__).resolve().parents[2]


class Isolation(unittest.TestCase):
    def test_bad_tenant_ids_are_refused(self):
        for bad in ("../vanna", "Vanna", "a", "x/y", "vanna;drop"):
            with self.assertRaises(S.TenantError):
                Brain(bad)

    def test_tenants_are_separate_databases(self):
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(S, "ROOT", Path(tmp)):
            a, b = Brain("acme", create=True), Brain("globex", create=True)
            a.save_profile({"company": {"name": "Acme"}}, status="approved")
            chunks = chunk_markdown("# Rockets\n\nAcme rockets use the Zorblax engine.",
                                    title="Rockets", company="Acme", source_label="docs")
            a.upsert_page("docs:rockets", chunks, source="docs", authority=2, embed=False)
            self.assertEqual(a.get_brand_profile()["company"]["name"], "Acme")
            self.assertEqual(b.get_brand_profile(), {})
            self.assertTrue(a.search_knowledge("Zorblax"))
            self.assertEqual(b.search_knowledge("Zorblax"), [])
            self.assertNotEqual(S.tenant_dir("acme"), S.tenant_dir("globex"))

    def test_unknown_tenant_is_not_created_by_a_read(self):
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(S, "ROOT", Path(tmp)):
            with self.assertRaises(S.TenantError):
                Brain("nobody").get_brand_profile()
            self.assertFalse((Path(tmp) / "nobody" / "brain.db").exists())


class Incremental(unittest.TestCase):
    def test_unchanged_chunks_are_kept_and_removed_ones_tombstoned(self):
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(S, "ROOT", Path(tmp)):
            b = Brain("acme", create=True)
            md = "# Page\n\n## One\n\nFirst section.\n\n## Two\n\nSecond section."
            c1 = chunk_markdown(md, title="Page", company="Acme", source_label="docs")
            r1 = b.upsert_page("docs:page", c1, source="docs", authority=2, embed=False)
            r2 = b.upsert_page("docs:page", c1, source="docs", authority=2, embed=False)
            self.assertEqual(r2["added_or_changed"], 0)
            c3 = chunk_markdown("# Page\n\n## One\n\nFirst section.", title="Page",
                                company="Acme", source_label="docs")
            r3 = b.upsert_page("docs:page", c3, source="docs", authority=2, embed=False)
            self.assertGreater(r1["added_or_changed"], 0)
            self.assertEqual(r3["tombstoned"], 1)
            self.assertEqual(b.search_knowledge("Second"), [])


class Vanna(unittest.TestCase):
    """Tenant #1 is onboarded on this machine."""

    @classmethod
    def setUpClass(cls):
        if not S.exists("vanna"):
            raise unittest.SkipTest("vanna brain not onboarded")
        cls.brain = Brain("vanna")

    def test_profile_is_loaded_whole(self):
        p = self.brain.get_brand_profile()
        for k in ("company", "voice", "claims", "partners", "visual"):
            self.assertIn(k, p)
        self.assertTrue(p["visual"]["palette"])

    def test_keyword_search_finds_product_terms(self):
        hits = self.brain.search_knowledge("health factor liquidation", k=5)
        self.assertTrue(hits)
        self.assertTrue(any("health" in (h["text"] + h["section"]).lower() for h in hits))
        self.assertTrue(all(h["source"] for h in hits))


class NoDirectReads(unittest.TestCase):
    """Agents reach company knowledge only through the brain."""

    AGENT_DIRS = ("gtm_os", "gtm_creative", "gtm_content", "gtm_orchestration",
                  "gtm_machines", "gtm_campaigns", "gtm_learning")
    FORBIDDEN = (r"brain[/\\]docs", r"knowledge[/\\](approved-claims|positioning|audience|"
                 r"notion-ground-truth|customer-objections|category-patterns)",
                 r"gtm_os[./]vanna_knowledge", r"companies[/\\]vanna\.json", r"design references[/\\]",
                 r"state[/\\]logo\.png", r'"logo\.png"', r"docs\.vanna\.finance/llms")
    # Stores the brain itself owns, read by their own modules.
    ALLOWED = {"gtm_creative/creative_rules.py"}

    def test_no_agent_module_reads_company_files(self):
        offenders = []
        for d in self.AGENT_DIRS:
            for f in (REPO / "pipeline" / d).rglob("*.py"):
                rel = str(f.relative_to(REPO / "pipeline")).replace("\\", "/")
                if rel in self.ALLOWED or "__pycache__" in rel:
                    continue
                text = f.read_text(encoding="utf-8", errors="replace")
                code = re.sub(r'"""[\s\S]*?"""|#.*', "", text)
                for pat in self.FORBIDDEN:
                    if re.search(pat, code):
                        offenders.append(rel + " ~ " + pat)
        self.assertEqual(offenders, [], "\n".join(offenders))


class McpServer(unittest.TestCase):
    def test_exposes_the_six_tools(self):
        if not S.exists("vanna"):
            raise unittest.SkipTest("vanna brain not onboarded")
        from pipeline.brand_brain.mcp_server import build
        tools = asyncio.run(build("vanna").list_tools())
        names = {t.name for t in tools}
        self.assertEqual(names, {"get_brand_profile", "get_whats_new", "search_knowledge",
                                 "get_visual_refs", "get_competitor_patterns", "log_post_outcome"})


if __name__ == "__main__":
    unittest.main()
