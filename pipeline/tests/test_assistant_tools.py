"""The assistant's tools, without the model: every declared tool is callable,
actions only ever come back as cards, and bad input is refused.

    .venv/Scripts/python.exe -m unittest pipeline.tests.test_assistant_tools -v
"""
from __future__ import annotations

import os

os.environ["BRAIN_MCP_DISABLE"] = "1"
os.environ["BRAIN_BACKEND"] = "sqlite"
os.environ["OPS_ALERTS"] = "0"      # tests never page the owner

import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from pipeline.assistant import tools as T
from pipeline.brand_brain import store as S
from pipeline.brand_brain.client import Brain


class AssistantToolsTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.runs = self.tmp / "runs"
        (self.runs / "GTM-20260926-100000").mkdir(parents=True)
        (self.runs / "GTM-20260926-100000" / "summary.json").write_text(json.dumps({
            "status": "review_blocked", "signal": "s", "brain": {"tenant": "acme"}, "review_notes": {"creative": "REJECT",
            "channel_issues": {"linkedin": ["too vague"]}}, "posts": {"x": {"hook": "h"}}}), encoding="utf-8")
        self.patches = [mock.patch.object(S, "ROOT", self.tmp / "tenants"), mock.patch.object(T, "RUNS", self.runs),
                        mock.patch.object(T, "STATUS_DIR", self.tmp / "status")]
        for p in self.patches:
            p.start()
        Brain("acme", create=True).save_profile({"company": {"name": "Acme"}}, status="approved")

    def tearDown(self):
        for p in self.patches:
            p.stop()
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_every_declared_tool_has_a_function(self):
        names = {d["name"] for d in T.declarations()}
        self.assertEqual(names, set(T.TOOLS))
        for d in T.declarations():
            self.assertEqual(d["parameters"]["type"], "object")

    def test_runs_say_why_they_were_blocked(self):
        r = T.call("list_runs", "acme", {"limit": 5})
        self.assertEqual(r["runs"][0]["run_id"], "GTM-20260926-100000")
        self.assertIn("creative judge: REJECT", r["runs"][0]["why"])
        self.assertIn("linkedin: too vague", r["runs"][0]["why"])

    def test_another_companys_runs_stay_out(self):
        (self.runs / "GTM-20260926-110000").mkdir(parents=True)
        (self.runs / "GTM-20260926-110000" / "summary.json").write_text(json.dumps({
            "status": "completed", "signal": "other", "brain": {"tenant": "globex"}}), encoding="utf-8")
        ids = [r["run_id"] for r in T.call("list_runs", "acme", {"limit": 10})["runs"]]
        self.assertEqual(ids, ["GTM-20260926-100000"])
        self.assertIn("error", T.call("get_run", "acme", {"run_id": "GTM-20260926-110000"}))
        names = {d["name"] for d in T.declarations(client=True)}
        self.assertFalse(names & T.CLIENT_BLOCKED)

    def test_actions_are_cards_not_deeds(self):
        r = T.call("propose_action", "acme", {"action": "launch_run", "directive": "post on health factor"})
        self.assertEqual(r["card"]["type"], "action")
        self.assertIn("error", T.call("propose_action", "acme", {"action": "approve"}))       # needs a run
        self.assertIn("error", T.call("propose_action", "acme", {"action": "publish"}))       # not a thing

    def test_add_company_validates_before_starting(self):
        self.assertIn("error", T.call("add_company", "acme", {"url": "not a site"}))
        with mock.patch.object(T, "_spawn") as sp:
            r = T.call("add_company", "acme", {"url": "https://www.globex.io/about"})
        self.assertEqual((r["tenant"], r["card"]["type"]), ("globex", "analysis"))
        self.assertEqual(sp.call_args[0][0][:2], ["pipeline.brand_brain.analyzer", "https://www.globex.io/about"])

    def test_unknown_tool_and_bad_args_are_errors(self):
        self.assertIn("error", T.call("rm_rf", "acme", {}))
        self.assertIn("error", T.call("get_run", "acme", {"run_id": "nope"}))


if __name__ == "__main__":
    unittest.main()
