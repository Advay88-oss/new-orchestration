"""Notion OAuth: the code is exchanged, the token is sealed per tenant, the
sync uses it, and disconnecting deletes it.

    .venv/Scripts/python.exe -m unittest pipeline.tests.test_notion_oauth -v
"""
from __future__ import annotations

import os

os.environ["BRAIN_MCP_DISABLE"] = "1"
os.environ["BRAIN_BACKEND"] = "sqlite"

import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from cryptography.fernet import Fernet

from pipeline.brand_brain import notion_oauth as O
from pipeline.brand_brain import notion_sync as N
from pipeline.brand_brain import store as S
from pipeline.brand_brain.client import Brain


class NotionOAuthTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.patches = [
            mock.patch.object(S, "ROOT", self.tmp),
            mock.patch.dict(os.environ, {"BRAIN_SECRET_KEY": Fernet.generate_key().decode()}),
            mock.patch.object(O, "_cfg", lambda: {"client_id": "cid", "client_secret": "csecret",
                                                  "redirect_uri": "http://localhost:3000/cb"}),
        ]
        for p in self.patches:
            p.start()
        Brain("acme", create=True)
        Brain("globex", create=True)

    def tearDown(self):
        for p in self.patches:
            p.stop()
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_connect_seal_use_disconnect(self):
        sent = {}

        def http(body):
            sent.update(body)
            return {"access_token": "ntn_live_token", "workspace_name": "Acme HQ", "bot_id": "b1"}

        self.assertIn("state=s1", O.authorize_url("s1"))
        r = O.exchange("acme", "the-code", http=http)
        self.assertEqual((r["ok"], r["workspace"]), (True, "Acme HQ"))
        self.assertEqual(sent["code"], "the-code")
        # Sealed at rest: the database holds ciphertext, not the token.
        sealed = Brain("acme").get_secret("notion_token")
        self.assertNotIn("ntn_live_token", sealed)
        self.assertEqual(O.token("acme"), "ntn_live_token")
        self.assertIsNone(O.token("globex"))                      # per tenant
        with mock.patch("pipeline.intelligence_stream.social_and_docs_collector._env", lambda k: None):
            self.assertEqual(N._token("acme"), "ntn_live_token")  # the sync uses the tenant's token
            self.assertIsNone(N._token("globex"))
        self.assertTrue(O.status("acme")["connected"])
        O.disconnect("acme")
        self.assertIsNone(O.token("acme"))
        self.assertIsNone(Brain("acme").get_secret("notion_token"))
        self.assertFalse(O.status("acme")["connected"])

    def test_a_key_mismatch_reads_nothing(self):
        O.exchange("acme", "c", http=lambda b: {"access_token": "t"})
        with mock.patch.dict(os.environ, {"BRAIN_SECRET_KEY": Fernet.generate_key().decode()}):
            self.assertIsNone(O.token("acme"))


if __name__ == "__main__":
    unittest.main()
