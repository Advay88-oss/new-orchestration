"""
Unit tests for content-type aware hashing and cache decisions.
"""

import unittest
from pipeline.gtm_engine.interceptors.hashing import (
    canonicalise_url,
    artefact_hash,
    evaluate_cache_status,
    CacheDecision,
    CURRENT_SCHEMA_VERSION,
    is_record_stale,
)


class TestHashing(unittest.TestCase):
    def test_canonicalise_url(self):
        url1 = "https://aave.com/blog/v3-update/?utm_source=twitter&utm_medium=social#section2"
        url2 = "https://aave.com/blog/v3-update"
        self.assertEqual(canonicalise_url(url1), canonicalise_url(url2))

    def test_forum_hash_detects_reply_and_length(self):
        artefact_forum_v1 = {
            "channel": "GOVERNANCE_FORUM",
            "url": "https://governance.aave.com/t/proposal-123",
            "published_date": "2026-07-01",
            "reply_count": 5,
            "text": "Initial proposal draft",
        }
        artefact_forum_v2 = {
            "channel": "GOVERNANCE_FORUM",
            "url": "https://governance.aave.com/t/proposal-123",
            "published_date": "2026-07-01",
            "reply_count": 6,  # New reply added
            "text": "Initial proposal draft",
        }
        h1 = artefact_hash(artefact_forum_v1)
        h2 = artefact_hash(artefact_forum_v2)
        self.assertNotEqual(h1, h2, "Governance forum hash must change when reply_count changes")

    def test_immutable_hash_ignores_reply_count(self):
        artefact_blog_v1 = {
            "channel": "OWNED_BLOG",
            "url": "https://mirror.xyz/morpho/announcement",
            "published_date": "2026-07-01",
            "text": "Immutable announcement",
            "reply_count": 0,
        }
        artefact_blog_v2 = {
            "channel": "OWNED_BLOG",
            "url": "https://mirror.xyz/morpho/announcement",
            "published_date": "2026-07-01",
            "text": "Immutable announcement",
            "reply_count": 5,  # Should be ignored for blog
        }
        h1 = artefact_hash(artefact_blog_v1)
        h2 = artefact_hash(artefact_blog_v2)
        self.assertEqual(h1, h2, "Blog hash must be immutable to reply count changes")

    def test_cache_decision_logic(self):
        # 1. Not in cache
        self.assertEqual(
            evaluate_cache_status("hash123", None),
            CacheDecision.FETCH_AND_CLASSIFY,
        )
        # 2. In cache with older schema -> RECLASSIFY
        old_entry = {"artefact_hash": "hash123", "schema_version": CURRENT_SCHEMA_VERSION - 1}
        self.assertEqual(
            evaluate_cache_status("hash123", old_entry),
            CacheDecision.RECLASSIFY,
        )
        # 3. In cache with current schema -> SKIP
        current_entry = {"artefact_hash": "hash123", "schema_version": CURRENT_SCHEMA_VERSION}
        self.assertEqual(
            evaluate_cache_status("hash123", current_entry),
            CacheDecision.SKIP,
        )


if __name__ == "__main__":
    unittest.main()
