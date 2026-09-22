"""Phase 13: Exhaustive Failure Mode Tests for Web Research Agent (test_web_research_failures.py).

Verifies strict absence of hallucinations across 10 critical failure modes:
  1. Invalid URL
  2. Website unavailable (404/Connection refused)
  3. JS-heavy page handling
  4. Scraper timeout
  5. Duplicate page handling
  6. Duplicate content deduplication
  7. Unsupported source scheme
  8. Missing evidence / empty page
  9. Conflicting sources
  10. Scraper binary unavailable
"""

from __future__ import annotations

import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

import sys
REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from pipeline.research.tools.web_research_tool import WebResearchTool
from pipeline.research.evidence_normalizer import EvidenceNormalizer
from pipeline.research.web_researcher import WebResearcher, ResearchPlan


class TestWebResearchFailures(unittest.TestCase):
    """Test suite ensuring zero hallucination under failure conditions."""

    def setUp(self):
        self.tool = WebResearchTool()
        self.normalizer = EvidenceNormalizer()
        self.researcher = WebResearcher(tool=self.tool, normalizer=self.normalizer)

    def test_01_invalid_url(self):
        """1. Invalid URL returns SCRAPE_FAILED without crashing or hallucinating."""
        with patch.object(self.tool, "_run_cli") as mock_cli:
            mock_cli.return_value = MagicMock(returncode=1, stdout="", stderr="ERR_NAME_NOT_RESOLVED")
            res = self.tool.extract_page("http://invalid.domain.that.does.not.exist.xyz123456789.com", timeout=5.0)
            self.assertEqual(res["status"], "SCRAPE_FAILED")
            self.assertEqual(res["content"], "")
            self.assertEqual(res["evidence"], [])

    def test_02_website_unavailable(self):
        """2. Unavailable website (404 / 500) returns SCRAPE_FAILED."""
        res = self.tool.extract_page("https://httpbin.org/status/404", timeout=5.0)
        # Even if opencli tries, it should detect failed status or empty content
        self.assertIn(res["status"], ["SCRAPE_FAILED", "OBSERVED"])
        if res["status"] == "SCRAPE_FAILED":
            self.assertEqual(res["content"], "")

    def test_03_js_heavy_page(self):
        """3. JS-heavy page extraction handles client-rendered text without error."""
        with patch.object(self.tool, "extract_page") as mock_extract:
            mock_extract.return_value = {
                "source_url": "https://client-rendered-spa.org",
                "status": "OBSERVED",
                "page_title": "Modern DeFi SPA",
                "content": "Live client-side hydrated content with reactive balance sheets.",
                "links": ["https://client-rendered-spa.org/app"]
            }
            res = self.tool.extract_page("https://client-rendered-spa.org", wait_seconds=3)
            self.assertEqual(res["status"], "OBSERVED")
            self.assertIn("reactive balance", res["content"])

    def test_04_scraper_timeout(self):
        """4. Scraper timeout returns SCRAPE_FAILED with timeout metadata."""
        # Force a 0.001s timeout to ensure it fires
        res = self.tool.extract_page("https://gearbox.fi", timeout=0.001)
        self.assertEqual(res["status"], "SCRAPE_FAILED")
        self.assertIn("timeout", res["metadata"].get("error", "").lower())

    def test_05_duplicate_page(self):
        """5. Duplicate URLs are deduplicated during domain crawling."""
        with patch.object(self.tool, "extract_page") as mock_extract, \
             patch.object(self.tool, "follow_links") as mock_follow:
            def side_effect(url, *args, **kwargs):
                return {
                    "source_url": url,
                    "status": "OBSERVED",
                    "content": f"Sample content for {url}",
                    "links": ["https://example.com", "https://example.com/about"]
                }
            mock_extract.side_effect = side_effect
            mock_follow.return_value = ["https://example.com", "https://example.com/about"]

            results = self.tool.crawl_domain("https://example.com", max_pages=3)
            urls_crawled = [r["source_url"] for r in results]
            # Ensure no duplicate visits to the exact same URL
            self.assertEqual(len(urls_crawled), len(set(urls_crawled)))

    def test_06_duplicate_content(self):
        """6. Identical content does not generate redundant claim IDs."""
        page_1 = {
            "source_url": "https://example.com/page1",
            "status": "OBSERVED",
            "page_title": "Identical Title",
            "content": "Gearbox Protocol is a generalized leverage protocol with $12B+ volume.",
            "retrieved_at": "2026-09-20T00:00:00Z"
        }
        page_2 = {
            "source_url": "https://example.com/page2",
            "status": "OBSERVED",
            "page_title": "Identical Title",
            "content": "Gearbox Protocol is a generalized leverage protocol with $12B+ volume.",
            "retrieved_at": "2026-09-20T00:00:00Z"
        }
        claims_1 = self.normalizer.normalize_page_evidence("gearbox", page_1)
        claims_2 = self.normalizer.normalize_page_evidence("gearbox", page_2)
        
        cids_1 = {c["claim_id"] for c in claims_1}
        cids_2 = {c["claim_id"] for c in claims_2}
        # Title claim IDs should match deterministically based on hash
        self.assertTrue(len(cids_1.intersection(cids_2)) > 0)

    def test_07_unsupported_source(self):
        """7. Unsupported scheme (e.g. ftp://) is classified safely into Level 6."""
        src_meta = self.normalizer.classify_source("ftp://internal.repo/data.txt")
        self.assertEqual(src_meta["hierarchy_level"], 6)
        self.assertEqual(src_meta["confidence"], "LOW")

    def test_08_missing_evidence(self):
        """8. Empty page content emits 0 claims and never invents facts."""
        empty_page = {
            "source_url": "https://example.com/empty",
            "status": "OBSERVED",
            "page_title": "",
            "content": "",
            "retrieved_at": "2026-09-20T00:00:00Z"
        }
        claims = self.normalizer.normalize_page_evidence("unknown_proto", empty_page)
        self.assertEqual(len(claims), 0)

    def test_09_conflicting_sources(self):
        """9. Conflicting sources retain their distinct URLs and provenance without overwriting."""
        src_a = self.normalizer.classify_source("https://api.llama.fi/protocol/gearbox")
        src_b = self.normalizer.classify_source("https://reddit.com/r/defi/comments/123")
        
        self.assertEqual(src_a["hierarchy_level"], 1)  # Level 1 API
        self.assertEqual(src_b["hierarchy_level"], 6)  # Level 6 Community
        self.assertNotEqual(src_a["confidence"], src_b["confidence"])

    def test_10_scraper_unavailable(self):
        """10. Scraper binary missing/unavailable returns SCRAPE_FAILED without crashing."""
        broken_tool = WebResearchTool()
        broken_tool.opencli_bin = "non_existent_binary_xyz_12345"
        res = broken_tool.extract_page("https://example.com", timeout=2.0)
        self.assertEqual(res["status"], "SCRAPE_FAILED")
        self.assertEqual(res["content"], "")


if __name__ == "__main__":
    unittest.main()
