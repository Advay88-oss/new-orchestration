"""Phase 4 learning loop: reward events, the reviewer's hard gate, engagement
normalised against the brand's baseline, the contextual bandit, locks, and
the founder's edits as preference pairs.

    .venv/Scripts/python.exe -m unittest pipeline.tests.test_learning_loop -v
"""
from __future__ import annotations

import collections
import json
import random
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from pipeline.brand_brain import store as S
from pipeline.brand_brain.client import Brain
from pipeline.gtm_learning import bandit as B
from pipeline.gtm_learning import feedback as F
from pipeline.gtm_learning import rewards as R


def _run(runs: Path, rid: str, *, passed: bool, hook: str, copy: str, pillar: str = "P1") -> None:
    d = runs / rid
    d.mkdir(parents=True)
    (d / "summary.json").write_text(json.dumps({
        "run_id": rid, "status": "completed", "review_passed": passed, "pillar": pillar,
        "started_at": "2026-09-23T10:00:00+00:00", "signal": "s",
        "posts": {"x": {"hook": hook, "copy": copy}}}), encoding="utf-8")


class LoopTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.runs = self.tmp / "runs"
        self.runs.mkdir()
        self.patches = [
            mock.patch.object(S, "ROOT", self.tmp / "tenants"),
            mock.patch.object(R, "RUNS", self.runs),
            mock.patch.object(F, "RUNS", self.runs),
            mock.patch.object(F, "LEDGER", self.tmp / "feedback.jsonl"),
            mock.patch("pipeline.brand_brain.context.current_tenant", lambda: "acme"),
            mock.patch("pipeline.brand_brain.client.current_tenant", lambda: "acme"),
            mock.patch("pipeline.gtm_os.state_sync.push_run", lambda *a, **k: None),
        ]
        for p in self.patches:
            p.start()
        b = Brain("acme", create=True)
        b.save_profile({"company": {"name": "Acme"}, "pillars": ["P1", "P2"]}, status="approved")
        from pipeline.brand_brain import context as C
        C._cache.clear()

    def tearDown(self):
        for p in self.patches:
            p.stop()
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_reviewer_is_a_hard_gate(self):
        _run(self.runs, "GTM-20260923-100000", passed=False, hook="Is pooled risk fair?", copy="x" * 300)
        (self.runs / "GTM-20260923-100000" / "feedback.json").write_text(
            json.dumps({"latest": {"verdict": "approve"}}), encoding="utf-8")
        ev = R.record_run("GTM-20260923-100000")
        self.assertEqual(ev["total"], 0.0)
        self.assertEqual(ev["arms"], {"pillar": "P1", "hook_type": "question", "length": "short"})

    def test_founder_decision_and_engagement_combine(self):
        for i, (lk, imp) in enumerate([(10, 1000), (20, 1000), (30, 1000)]):
            Brain("acme").log_post_outcome("GTM-2026092%d-0900%02d" % (0, i), {"impressions": imp, "likes": lk})
        rid = "GTM-20260923-110000"
        _run(self.runs, rid, passed=True, hook="Stop pooling risk", copy="y" * 1000)
        (self.runs / rid / "feedback.json").write_text(json.dumps({"latest": {"verdict": "approve"}}), encoding="utf-8")
        R.log_outcome(rid, {"impressions": 1000, "likes": 40})           # 2x the baseline median
        ev = R.events()[0]
        self.assertEqual(ev["engagement"], 1.0)
        self.assertAlmostEqual(ev["total"], 0.6 * 1.0 + 0.4 * 1.0, places=3)
        self.assertEqual(ev["arms"]["hook_type"], "contrarian")
        self.assertEqual(ev["arms"]["length"], "long")

    def test_edit_records_a_preference_pair(self):
        rid = "GTM-20260923-120000"
        _run(self.runs, rid, passed=True, hook="Hook", copy="Draft body")
        F.record(rid, "edit", "tightened", source="test", edited="Hook\n\nBetter body")
        pairs = R.pairs()
        self.assertEqual(len(pairs), 1)
        self.assertIn("Draft body", pairs[0]["rejected"])
        self.assertEqual(R.events()[0]["human"], 0.8)

    def test_bandit_explores_and_honours_locks(self):
        for i in range(6):
            rid = "GTM-2026092%d-13%04d" % (3, i)
            _run(self.runs, rid, passed=True, hook="Is it?" if i % 2 else "Plain claim", copy="z" * 200)
            (self.runs / rid / "feedback.json").write_text(
                json.dumps({"latest": {"verdict": "approve" if i % 2 else "kill"}}), encoding="utf-8")
            R.record_run(rid)
        ctx = {"day_type": "weekday", "whats_new": False}
        why = collections.Counter(B.recommend(ctx, rng=random.Random(i))["hook_type"]["why"].split(" (")[0]
                                  for i in range(600))
        self.assertTrue(0.10 < why["exploring"] / 600 < 0.20, why)
        B.set_lock("hook_type", "story")
        self.assertEqual(B.recommend(ctx)["hook_type"], {"choice": "story", "why": "locked by the founder"})
        B.set_lock("hook_type", None)
        self.assertNotIn("hook_type", B.locks())


if __name__ == "__main__":
    unittest.main()
