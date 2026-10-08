"""The strategists compete across arcs and an independent judge picks.

    .venv/Scripts/python.exe -m pipeline.tests.offline test_agents_debate

Every model call is faked.
"""
from __future__ import annotations

import os

os.environ["BRAIN_MCP_DISABLE"] = "1"
os.environ["BRAIN_BACKEND"] = "sqlite"
os.environ["OPS_ALERTS"] = "0"

import types
import unittest
from unittest import mock

ARCS = [{"name": "capital efficiency", "claim": "credit stays usable"},
        {"name": "risk isolation", "claim": "one account per borrower"}]


def _strategy(status="ACTION", pillar="P", proof=("a",)):
    from pipeline.gtm_orchestration.schemas import GTMStrategy
    return GTMStrategy(strategy_id="S", action_status=status, objective="o", audience_segment="a",
                       problem="p", market_context="m", strategic_opportunity="s", narrative_pillar=pillar,
                       positioning="x", proof=list(proof), cta="c", channel="X", content_type="t",
                       gtm_machine_id="M", reasoning=[], evidence=[])


class Debate(unittest.TestCase):
    def run_compete(self, made, verdict, directive=False):
        from pipeline.gtm_os import autonomous_cycle as AC
        from pipeline.gtm_os import editorial_judge as EJ
        signal = types.SimpleNamespace(headline="h", description="d")
        summary: dict = {}

        def make(self_, sig, arc=None):
            return made[arc["name"]] if arc else made[None]
        with mock.patch.object(EJ, "arcs_for_tenant", return_value=ARCS), \
                mock.patch("pipeline.gtm_orchestration.gtm_strategist.GTMStrategist.__init__", return_value=None), \
                mock.patch("pipeline.gtm_orchestration.gtm_strategist.GTMStrategist.evaluate_and_formulate_strategy",
                           make), \
                mock.patch.object(EJ, "judge", return_value=verdict), \
                mock.patch.object(AC.R, "record_decision"), mock.patch.object(AC.R, "record_stage"):
            out = AC._compete(None, signal, summary, "GTM-1", directive=directive)
        return out, summary

    def test_one_strategy_per_arc_and_the_judge_picks(self):
        made = {"capital efficiency": _strategy(pillar="CE"), "risk isolation": _strategy(pillar="RI")}
        verdict = {"ok": True, "winner": 1, "best_score": 82,
                   "scores": [{"i": 1, "arc": "risk isolation", "score": 82, "why": "w"},
                              {"i": 0, "arc": "capital efficiency", "score": 61, "why": "w"}]}
        out, summary = self.run_compete(made, verdict)
        self.assertEqual(out.narrative_pillar, "RI")
        self.assertEqual(summary["strategist_debate"]["arcs"], ["capital efficiency", "risk isolation"])
        self.assertEqual(summary["strategist_debate"]["winner"], "risk isolation")

    def test_under_the_bar_is_rejected_when_autonomous(self):
        made = {"capital efficiency": _strategy(pillar="CE"), "risk isolation": _strategy(pillar="RI")}
        verdict = {"ok": True, "winner": 0, "best_score": 55,
                   "scores": [{"i": 0, "arc": "capital efficiency", "score": 55, "why": "thin"}]}
        out, _ = self.run_compete(made, verdict)
        self.assertEqual(out.action_status, "NO_ACTION")
        self.assertEqual(out.decision_reason_class, "EDITORIAL_BELOW_BAR")

    def test_a_directive_is_not_killed_by_the_bar(self):
        made = {"capital efficiency": _strategy(pillar="CE"), "risk isolation": _strategy(pillar="RI")}
        verdict = {"ok": True, "winner": 0, "best_score": 55,
                   "scores": [{"i": 0, "arc": "capital efficiency", "score": 55, "why": "thin"}]}
        out, _ = self.run_compete(made, verdict, directive=True)
        self.assertEqual(out.action_status, "ACTION")

    def test_only_one_arc_found_an_angle(self):
        made = {"capital efficiency": _strategy(status="NO_ACTION"), "risk isolation": _strategy(pillar="RI")}
        out, summary = self.run_compete(made, {"ok": False})
        self.assertEqual(out.narrative_pillar, "RI")
        self.assertEqual(summary["strategist_debate"]["winner"], "risk isolation")

    def test_judge_down_takes_the_most_proof_not_a_coin(self):
        made = {"capital efficiency": _strategy(pillar="CE", proof=("a",)),
                "risk isolation": _strategy(pillar="RI", proof=("a", "b", "c"))}
        out, _ = self.run_compete(made, {"ok": False, "error": "503"})
        self.assertEqual(out.narrative_pillar, "RI")

    def test_judge_scores_are_clamped_and_indexed(self):
        from pipeline.gtm_os import agent_runtime as R
        from pipeline.gtm_os import editorial_judge as EJ
        entries = [(ARCS[0], _strategy()), (ARCS[1], _strategy())]
        fake = {"scores": [{"i": 0, "score": 140, "why": "x"}, {"i": 7, "score": 99}, {"i": 1, "score": 40}]}
        with mock.patch.object(R, "brain_json", return_value=fake):
            v = EJ.judge(types.SimpleNamespace(headline="h", description="d"), entries)
        self.assertTrue(v["ok"])
        self.assertEqual(v["winner"], 0)
        self.assertEqual(v["best_score"], 100)
        self.assertEqual(len(v["scores"]), 2)


if __name__ == "__main__":
    unittest.main()
