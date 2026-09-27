"""Agents reach the brain through the Brain MCP server.

Starts the real server as a child process over stdio, against a throwaway
SQLite brain, and checks the agent handle (`context.brain()`) gets its
answers over MCP rather than in-process.

    .venv/Scripts/python.exe -m unittest pipeline.tests.test_brain_mcp -v
"""
from __future__ import annotations

import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

os.environ["OPS_ALERTS"] = "0"      # tests never page the owner


class BrainOverMCPTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp())
        cls.env = mock.patch.dict(os.environ, {"BRAIN_ROOT": str(cls.tmp), "BRAIN_BACKEND": "sqlite",
                                               "BRAIN_TENANT": "mcptest", "BRAIN_MCP_DISABLE": ""})
        cls.env.start()
        from pipeline.brand_brain import mcp_client as M
        M.enable()
        from pipeline.brand_brain import store as S
        cls.root = mock.patch.object(S, "ROOT", cls.tmp)
        cls.root.start()
        from pipeline.brand_brain.client import Brain
        b = Brain("mcptest", create=True)
        b.save_profile({"company": {"name": "MCP Test Co"}}, status="approved")
        b.add_event("e1", at="2026-09-20T00:00:00Z", kind="feature_launch", title="Credit lines are live")

    @classmethod
    def tearDownClass(cls):
        from pipeline.brand_brain import mcp_client as M
        M._close_all()
        M._sessions.clear()
        cls.root.stop()
        cls.env.stop()
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_agent_reads_go_over_mcp(self):
        from pipeline.brand_brain import context as C
        from pipeline.brand_brain import mcp_client as M
        with mock.patch("pipeline.brand_brain.client.Brain.get_brand_profile",
                        side_effect=AssertionError("read in-process, not over MCP")):
            p = C.brain("mcptest").get_brand_profile()
        self.assertEqual(p["company"]["name"], "MCP Test Co")
        self.assertEqual(M.transport("mcptest")["transport"], "mcp-stdio")
        ev = C.brain("mcptest").get_whats_new("2026-01-01T00:00:00Z", 5)
        self.assertEqual(ev[0]["title"], "Credit lines are live")
        self.assertEqual(C.brain("mcptest").get_competitor_patterns("x"), [])


if __name__ == "__main__":
    unittest.main()
