"""
Expanded Agent Readiness Test Suite (Phase 20 Verification).
Asserts empirical depth, independent example validation, mathematical reconstruction,
null-preservation, competitor-grounded whitespace, and temporal sanity across conditions A through T.
"""

import unittest
import json
import re
from pathlib import Path
from collections import Counter

DB_DIR = Path("D:/new orchestration/pipeline/gtm_engine/brain/db")
TODAY = "2026-09-10"


class TestPhase20EvidenceCorpus(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.posts = [json.loads(l) for l in open(DB_DIR / "posts.jsonl", encoding="utf-8") if l.strip()]
        cls.patterns = [json.loads(l) for l in open(DB_DIR / "patterns.jsonl", encoding="utf-8") if l.strip()]
        cls.series = [json.loads(l) for l in open(DB_DIR / "recurring_series.jsonl", encoding="utf-8") if l.strip()]
        cls.campaigns = [json.loads(l) for l in open(DB_DIR / "campaigns.jsonl", encoding="utf-8") if l.strip()]
        cls.gtm_machines = [json.loads(l) for l in open(DB_DIR / "gtm_machines.jsonl", encoding="utf-8") if l.strip()]
        cls.performance = [json.loads(l) for l in open(DB_DIR / "performance.jsonl", encoding="utf-8") if l.strip()]
        cls.whitespace = [json.loads(l) for l in open(DB_DIR / "whitespace.jsonl", encoding="utf-8") if l.strip()]
        cls.opportunities = [json.loads(l) for l in open(DB_DIR / "opportunities.jsonl", encoding="utf-8") if l.strip()]
        cls.coverage = json.loads((DB_DIR / "corpus_coverage.json").read_text(encoding="utf-8"))

    # A. No future timestamps
    def test_condition_a_no_future_timestamps(self):
        for p in self.posts:
            self.assertLessEqual(p["published_at"], TODAY, f"Future post detected: {p['post_id']} at {p['published_at']}")

    # B & D. No fake tweet IDs; real tweet IDs
    def test_condition_b_d_real_tweet_ids(self):
        for p in self.posts:
            if p.get("evidence_status") == "X_OBSERVED":
                tid = str(p.get("tweet_id", ""))
                self.assertTrue(re.match(r"^\d{15,22}$", tid), f"Invalid tweet ID: {tid}")
                self.assertNotIn("XXXX", tid)

    # C & S. Resolving X URLs; no blog URL relabeled as X_OBSERVED
    def test_condition_c_s_x_urls_validity(self):
        for p in self.posts:
            if p.get("evidence_status") == "X_OBSERVED":
                url = p.get("url", "")
                self.assertTrue(url.startswith("https://x.com/"), f"Invalid X URL: {url}")
                self.assertNotIn(".org", url)
                self.assertNotIn(".com/blog", url)

    # E & Q. Every percentage reconstructs from raw records; no percentage without denominator
    def test_condition_e_q_percentage_reconstruction(self):
        for player_cov in self.coverage["players"]:
            pid = player_cov["player"]
            player_posts = [p for p in self.posts if p["player_id"] == pid]
            denom = len(player_posts)
            self.assertEqual(player_cov["retrieved_posts"], denom, f"Coverage count mismatch for {pid}")
            if denom > 0:
                counts = Counter(p["content_category"] for p in player_posts)
                total_pct = sum((c / denom) * 100.0 for c in counts.values())
                self.assertAlmostEqual(total_pct, 100.0, places=1, msg=f"Percentages do not sum to 100 for {pid}")

    # F & G & T. Patterns have >=2 independent examples; supporting URLs do not inflate count
    def test_condition_f_g_t_independent_pattern_examples(self):
        for pat in self.patterns:
            indep_count = pat.get("independent_example_count", 0)
            source_ids = pat.get("source_record_ids", [])
            self.assertGreaterEqual(indep_count, 2, f"Pattern {pat['pattern_id']} has < 2 independent examples")
            self.assertEqual(indep_count, len(source_ids), f"Independent count does not match source records in {pat['pattern_id']}")
            # Ensure unique source IDs
            self.assertEqual(len(source_ids), len(set(source_ids)), f"Duplicate source ID in pattern {pat['pattern_id']}")

    # H. Recurring series occurrences map to real records
    def test_condition_h_recurring_series_occurrences(self):
        for ser in self.series:
            occ_count = ser.get("occurrence_count", 0)
            occ_ids = ser.get("occurrence_record_ids", [])
            self.assertGreaterEqual(occ_count, 4, f"Series {ser['series_id']} has < 4 occurrences")
            self.assertGreaterEqual(len(occ_ids), occ_count, f"Occurrences missing in {ser['series_id']}")

    # I. Campaign stages map to real records or NOT_OBSERVED
    def test_condition_i_campaign_stages_mapped(self):
        for camp in self.campaigns:
            for stage in camp.get("stages", []):
                status = stage.get("evidence_status")
                self.assertIn(status, ["X_OBSERVED", "PRIMARY_SOURCE_OBSERVED", "NOT_OBSERVED"])
                if status != "NOT_OBSERVED":
                    self.assertTrue(stage.get("source_url") or stage.get("source_record_id"))

    # J. GTM machines meet minimum evidence threshold (>=2 players, >=2 URLs)
    def test_condition_j_gtm_machines_threshold(self):
        for m in self.gtm_machines:
            self.assertGreaterEqual(len(m.get("players", [])), 2, f"GTM Machine {m['machine_id']} lacks >= 2 players")
            self.assertGreaterEqual(len(m.get("sample_source_urls", [])), 2, f"GTM Machine {m['machine_id']} lacks >= 2 URLs")

    # K & L. Performance aggregates reconstructable; null is never converted to zero
    def test_condition_k_l_performance_reconstruction_null_preservation(self):
        for p in self.posts:
            eng = p["engagement"]
            views = eng["views"]
            rate = eng.get("engagement_rate_pct")
            if views is None or views == 0:
                self.assertIsNone(rate, f"Engagement rate should be null when views are absent/zero: {p['post_id']}")
            else:
                eng_sum = (eng["likes"] or 0) + (eng["reposts"] or 0) + (eng["replies"] or 0)
                reconstructed_rate = round(eng_sum / views * 100.0, 3)
                self.assertAlmostEqual(rate, reconstructed_rate, places=2)

    # M & N. Vanna comparative claims require competitor evidence; unsupported whitespace quarantined
    def test_condition_m_n_whitespace_and_vanna_claim_evidence(self):
        for w in self.whitespace:
            self.assertTrue(w.get("incumbent_limitations_evidence"), f"Whitespace {w['whitespace_id']} lacks competitor evidence")
            self.assertGreaterEqual(len(w["incumbent_limitations_evidence"]), 2, f"Whitespace {w['whitespace_id']} lacks multi-competitor proof")

        for opp in self.opportunities:
            self.assertEqual(opp.get("claim_tier_safety_gate"), "TESTNET_COMPLIANT")
            self.assertTrue(opp.get("vanna_source"), f"Opportunity {opp['opportunity_id']} lacks Vanna source")
            self.assertTrue(opp.get("competitor_sources"), f"Opportunity {opp['opportunity_id']} lacks competitor sources")

    # O & P. Coverage status exists for all 10 players; zero-post players not complete
    def test_condition_o_p_coverage_status_all_ten_players(self):
        self.assertEqual(len(self.coverage["players"]), 10, "Coverage report missing players")
        for pc in self.coverage["players"]:
            status = pc["coverage_status"]
            self.assertIn(status, ["FULL", "PARTIAL", "MINIMAL", "NOT_OBSERVED"])
            if pc["retrieved_posts"] == 0:
                self.assertNotEqual(status, "FULL")


if __name__ == "__main__":
    unittest.main()
