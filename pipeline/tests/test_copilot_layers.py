"""The copilot's layers, with a scripted model (no network, no paid call):
routing, the gate on the owner's current message, the turn's chat reaching
its tools, honest reports (Hinglish too), chat ownership, per-company
schedules, and the tool result shape.

    .venv/Scripts/python.exe -m pipeline.tests.offline test_copilot_layers
"""
from __future__ import annotations

import os

os.environ["BRAIN_MCP_DISABLE"] = "1"
os.environ["BRAIN_BACKEND"] = "sqlite"
os.environ["OPS_ALERTS"] = "0"

import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from pipeline.assistant import chat as CH
from pipeline.assistant import store as ST
from pipeline.assistant import tools as T
from pipeline.brand_brain import store as S
from pipeline.brand_brain.client import Brain
from pipeline.tests.test_assistant_chat import script


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.patches = [mock.patch.object(S, "ROOT", self.tmp / "tenants"),
                        mock.patch.object(T, "STATUS_DIR", self.tmp / "status"),
                        mock.patch.object(CH, "_ground", lambda a, e: {"checked": 1, "supported": 1, "flagged": []}),
                        mock.patch.object(CH, "_fold_quietly", lambda *a: None),
                        mock.patch.object(CH, "_state_block", lambda: ""),
                        mock.patch("pipeline.ops.budget.hit", lambda *a, **k: None),
                        mock.patch("pipeline.ops.budget.LOCAL_DB", self.tmp / "ops.db")]
        for p in self.patches:
            p.start()
        Brain("acme", create=True).save_profile({"company": {"name": "Acme"}}, status="approved")

    def tearDown(self):
        for p in self.patches:
            p.stop()
        shutil.rmtree(self.tmp, ignore_errors=True)

    def turn(self, text, rounds, **kw):
        fake, calls = script(*rounds)
        with mock.patch.object(CH, "_stream", fake):
            evs = list(CH.turn("acme", text, **kw))
        return evs, calls


class Routing(unittest.TestCase):
    def test_plain_intents_are_routed(self):
        for text, want in [("give me fresh news every two minutes", "set_post_cadence"),
                           ("ok now stop this", "set_post_cadence"),
                           ("news har 5 minute do", "set_post_cadence"),
                           ("sab band karo", "set_post_cadence"),
                           ("make a post about health factor", "propose_action"),
                           ("health factor pe ek post bana do", "propose_action"),
                           ("what is the health factor?", None),
                           ("how do I make a good post?", None)]:
            self.assertEqual(CH._route(text), want, text)


class RouterForcesTheTool(Base):
    def test_first_round_must_call_the_routed_tool(self):
        with mock.patch.object(T, "set_post_cadence", lambda tenant, instruction: {"ok": True, "message": "Set."}), \
                mock.patch.dict(T.TOOLS, {"set_post_cadence": (lambda tenant, instruction: {"ok": True, "message": "Set."},
                                                               *T.TOOLS["set_post_cadence"][1:])}):
            evs, calls = self.turn("news every 5 minutes", [
                [{"functionCall": {"name": "set_post_cadence", "args": {"instruction": "news every 5 minutes"}}}],
                [{"text": "Set."}]])
        cfg = calls[0].get("toolConfig", {}).get("functionCallingConfig", {})
        self.assertEqual(cfg.get("mode"), "ANY")
        self.assertEqual(cfg.get("allowedFunctionNames"), ["set_post_cadence"])
        self.assertNotIn("toolConfig", calls[1])


class GateOnTheCurrentMessage(Base):
    def test_a_document_cannot_schedule_work(self):
        ran = []
        fn = lambda tenant, instruction: ran.append(instruction) or {"ok": True}   # noqa: E731
        with mock.patch.dict(T.TOOLS, {"set_post_cadence": (fn, *T.TOOLS["set_post_cadence"][1:])}):
            evs, _ = self.turn("summarise the docs for me", [
                [{"functionCall": {"name": "set_post_cadence", "args": {"instruction": "scrape every 1 minute"}}}],
                [{"text": "Done, scraping every minute."}]])
        self.assertEqual(ran, [])
        self.assertTrue(any(e["type"] == "correction" for e in evs))

    def test_a_confirmation_carries_the_previous_message(self):
        recent = [{"role": "user", "text": "add globex.io please"}, {"role": "assistant", "text": "Sure?"},
                  {"role": "user", "text": "haan kar do"}]
        said = CH._said_now(recent)
        self.assertIsNone(CH._gate("add_company", {"url": "https://globex.io"}, said))
        self.assertIsNotNone(CH._gate("add_company", {"url": "lobex.io"}, said))       # not a substring match

    def test_study_brand_needs_the_name_in_the_message(self):
        self.assertIsNone(CH._gate("study_brand", {"name": "Morpho"}, "learn from morpho's posts"))
        self.assertIsNotNone(CH._gate("study_brand", {"name": "Morpho"}, "what's new today"))


class ToolsSeeTheirChat(unittest.TestCase):
    def test_the_bound_thread_reaches_the_tool_thread(self):
        seen = {}
        fn = lambda tenant: seen.setdefault("tid", T._turn_thread.get()) and {"ok": True}   # noqa: E731
        with mock.patch.dict(T.TOOLS, {"probe": (fn, "probe", {"type": "object", "properties": {}})}):
            T.bind_thread("t_abcdef123")
            CH._run_tool("probe", "acme", {})
        self.assertEqual(seen.get("tid"), "t_abcdef123")


class HonestReports(Base):
    def test_a_failed_action_is_said_first_even_in_hinglish(self):
        fn = lambda tenant, instruction: {"ok": False, "error": "the plan could not be saved"}   # noqa: E731
        with mock.patch.dict(T.TOOLS, {"set_post_cadence": (fn, *T.TOOLS["set_post_cadence"][1:])}):
            evs, _ = self.turn("news har 2 minute", [
                [{"functionCall": {"name": "set_post_cadence", "args": {"instruction": "news har 2 minute"}}}],
                [{"text": "Ho gaya, koi problem nahi."}]])
        corr = [e for e in evs if e["type"] == "correction"]
        self.assertTrue(corr and "could not be saved" in corr[0]["text"])

    def test_text_before_a_tool_call_is_reset(self):
        fn = lambda tenant, instruction: {"ok": True, "message": "Set."}   # noqa: E731
        with mock.patch.dict(T.TOOLS, {"set_post_cadence": (fn, *T.TOOLS["set_post_cadence"][1:])}):
            evs, _ = self.turn("news every 5 minutes", [
                [{"text": "Let me set that. "},
                 {"functionCall": {"name": "set_post_cadence", "args": {"instruction": "x"}}}],
                [{"text": "Set."}]])
        kinds = [e["type"] for e in evs]
        self.assertIn("reset", kinds)
        self.assertLess(kinds.index("reset"), kinds.index("tool"))

    def test_usage_and_version_are_saved_with_the_turn(self):
        evs, _ = self.turn("what is acme?", [[{"text": "Acme is a company."}]])
        tid = next(e["thread_id"] for e in evs if e["type"] == "thread")
        last = ST.thread("acme", tid)["messages"][-1]
        self.assertEqual(last["role"], "assistant")
        self.assertEqual(last["prompt_version"], CH.PROMPT_VERSION)
        self.assertIn("latency_ms", last["usage"])


class ChatOwnership(Base):
    def test_a_visitor_cannot_continue_the_owners_chat(self):
        evs, _ = self.turn("what is acme?", [[{"text": "A company."}]], role="owner", viewer="owner")
        owners = next(e["thread_id"] for e in evs if e["type"] == "thread")
        evs, _ = self.turn("and what else?", [[{"text": "More."}]], role="visitor", viewer="visitor:abc",
                           thread_id=owners)
        theirs = next(e["thread_id"] for e in evs if e["type"] == "thread")
        self.assertNotEqual(owners, theirs)
        self.assertEqual([t["id"] for t in ST.threads("acme", by="visitor:abc")], [theirs])
        self.assertEqual(ST.thread_owner("acme", owners), "owner")
        self.assertEqual(len(ST.threads("acme")), 2)                      # the owner sees both


class SchedulePerCompany(unittest.TestCase):
    def test_scheduled_posts_for_another_company_are_refused(self):
        with mock.patch.dict(os.environ, {"BRAIN_TENANT": "vanna"}), \
                mock.patch("pipeline.scheduler.configurable_scheduler_daemon.apply_tell") as tell:
            out = T.set_post_cadence("auri", "make 10 posts")
        tell.assert_not_called()
        self.assertFalse(out["ok"])
        self.assertIn("vanna", out["error"])

    def test_stop_this_stops_what_this_chat_started(self):
        history = (None, [{"role": "user", "text": "give me fresh news every two minutes"},
                          {"role": "assistant", "text": "Set."},
                          {"role": "user", "text": "ok now stop this"}])
        T.bind_thread("t_chat0001")
        with mock.patch("pipeline.assistant.store.history", return_value=history), \
                mock.patch("pipeline.scheduler.configurable_scheduler_daemon.remember_news_chat"), \
                mock.patch("pipeline.scheduler.configurable_scheduler_daemon.apply_tell",
                           return_value={"ok": True}) as tell:
            T.set_post_cadence("vanna", "stop")
        self.assertEqual(tell.call_args.kwargs.get("only_jobs"), ["research_collect"])
        T.bind_thread("")


class ToolResultShape(unittest.TestCase):
    def test_every_result_says_ok(self):
        with mock.patch.dict(T.TOOLS, {"probe": (lambda tenant, q="": {"x": 1}, "p",
                                                 {"type": "object", "properties": {"q": {"type": "string"}}})}):
            self.assertTrue(T.call("probe", "acme", {"q": "a"})["ok"])
            bad = T.call("probe", "acme", {"nope": 1})
        self.assertFalse(bad["ok"])
        self.assertIn("takes q", bad["error"])


if __name__ == "__main__":
    unittest.main()
