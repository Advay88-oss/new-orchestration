"""What the agents show and prove is measured, not written in.

    .venv/Scripts/python.exe -m pipeline.tests.offline test_agent_hardcoding

The review card carries no fixed score, the creative judge fails closed,
the image and video models come from the model table, a tenant without
Vanna's rules gets none of them, and a claim is never proved by the profile
that states it. Every model call is faked.
"""
from __future__ import annotations

import os

os.environ["BRAIN_MCP_DISABLE"] = "1"
os.environ["BRAIN_BACKEND"] = "sqlite"
os.environ["OPS_ALERTS"] = "0"

import types
import unittest
from pathlib import Path
from unittest import mock


def _strategy():
    from pipeline.gtm_orchestration.schemas import GTMStrategy
    return GTMStrategy(strategy_id="STRAT-TEST-0001", action_status="ACTION", objective="o",
                       audience_segment="a", problem="p", market_context="m", strategic_opportunity="s",
                       narrative_pillar="P", positioning="x", proof=[], cta="c", channel="X",
                       content_type="t", gtm_machine_id="M", reasoning=[], evidence=[])


class ReviewCard(unittest.TestCase):
    def packet(self, review):
        from pipeline.gtm_os.telegram_packet import TelegramPacketBuilder as T
        signal = types.SimpleNamespace(headline="h", source_type="NEWS", confidence="LOW")
        content = types.SimpleNamespace(channel_posts={"x": types.SimpleNamespace(hook="hk")})
        p = T.build_packet(signal=signal, strategy=_strategy(), claims=[], machine="M", campaign=None,
                           content_pkg=content, creative_brief=None, review_result=review)
        return p, T.render_telegram_markdown(p)

    def test_no_invented_score_or_confidence(self):
        p, md = self.packet(None)
        self.assertIsNone(p.reviewer_score)
        self.assertEqual(p.confidence_dimensions, {})
        self.assertNotIn("95/100", md)
        self.assertIn("not scored this run", md)

    def test_a_blocked_run_says_why_and_offers_no_approve(self):
        p, md = self.packet({"score": 81, "passed": False, "blocking": ["fact check: unsupported 9x"]})
        self.assertIn("81/100", md)
        self.assertIn("BLOCKED", md)
        self.assertIn("unsupported 9x", md)
        self.assertNotIn("Approve", md)

    def test_blocking_lines_name_every_reason(self):
        from pipeline.gtm_os.autonomous_cycle import _blocking_lines
        lines = _blocking_lines({"review_passed": False, "review_notes": {
            "facts": ["unsupported: 9x"], "creative": "UNJUDGED", "slop": []}})
        self.assertTrue(any("9x" in x for x in lines))
        self.assertIn("creative judge: UNJUDGED", lines)
        self.assertEqual(_blocking_lines({"review_passed": True}), [])


class CreativeJudge(unittest.TestCase):
    def judge(self, verdict, tmp):
        from pipeline.gtm_os import creative_judge as CJ
        img = Path(tmp) / "v.png"
        img.write_bytes(b"x")
        with mock.patch.object(CJ.R, "brain_vision", return_value=verdict), \
                mock.patch.object(CJ.R, "record_stage"):
            return CJ.judge_assets({"visual_path": str(img), "posts": {}}, "GTM-T")

    def test_no_verdict_is_unjudged_not_ship(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(self.judge({}, tmp)["overall"], "UNJUDGED")

    def test_a_rejected_copy_rejects_the_run(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            v = self.judge({"assets": [{"asset": "visual", "verdict": "SHIP"}], "copy_verdict": "REJECT",
                            "overall": "SHIP"}, tmp)
        self.assertEqual(v["overall"], "REJECT")


class ModelTable(unittest.TestCase):
    def test_poster_meme_and_video_read_the_table(self):
        from pipeline.gtm_os import agent_runtime as R
        from pipeline.gtm_creative import direct_image_posters as DP, memes
        with mock.patch.dict(R.MODELS, {"poster": "p-model", "meme": "m-model"}):
            self.assertEqual(DP._model(), "p-model")
            self.assertEqual(memes._meme_model(), "m-model")
        self.assertFalse(hasattr(DP, "MODEL"))
        from pipeline.gtm_creative import veo_video
        self.assertFalse(hasattr(veo_video, "MODEL"))


class TenantRules(unittest.TestCase):
    def test_vanna_keeps_its_rules_and_another_tenant_gets_none(self):
        from pipeline.brand_brain import context as C
        seed = C._seed("vanna")
        self.assertIn("Blend", seed["prompt_rules"]["stay_on_source"])
        with mock.patch.object(C, "_get", return_value=None), \
                mock.patch.object(C, "_seed", return_value={}), \
                mock.patch.object(C, "true_figures", return_value=[]), \
                mock.patch.object(C, "company_name", return_value="Auri"):
            self.assertEqual(C.rule("deployments"), "")
            self.assertEqual(C.rule("kill_phrases", []), [])

    def test_no_subjects_to_rotate_is_none(self):
        from pipeline.gtm_os import subject_rotation as S
        with mock.patch.object(S, "fixed_subjects", return_value=[]), \
                mock.patch.object(S, "doc_subjects", return_value=[]):
            self.assertIsNone(S.next_subject("auri"))


class Evidence(unittest.TestCase):
    def test_the_profile_never_proves_its_own_claim(self):
        from pipeline.brand_brain import context as C
        hits = [{"id": "p", "source": "profile", "text": "0.00014 XLM"},
                {"id": "r", "source": "rulebook", "text": "0.00014 XLM"},
                {"id": "g", "source": "github", "text": "docs"}]
        with mock.patch.object(C, "knowledge_hits", return_value=hits):
            self.assertEqual([h["id"] for h in C.evidence_hits("gas", k=4)], ["g"])

    def test_a_comparison_is_looked_up_not_approved_by_name(self):
        from pipeline.gtm_orchestration import claim_evidence_gate as G
        gate = G.ClaimEvidenceGate()
        with mock.patch.object(G, "_support", return_value=(None, 0.0, [])), \
                mock.patch.object(G, "_fact_triggers", return_value=[r"\bvanna\b"]), \
                mock.patch.object(G, "_competitor_names", return_value=[]):
            r = gate.evaluate_claim("Vanna isolates each account unlike shared pools")
        self.assertEqual(r.claim_type, "COMPARATIVE_CLAIM")
        self.assertNotEqual(r.action, "USE")
        self.assertNotIn("DOCS_VANNA_FINANCE", r.source_records)


if __name__ == "__main__":
    unittest.main()
