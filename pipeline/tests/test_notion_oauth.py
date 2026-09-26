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
            mock.patch.dict(os.environ, {"BRAIN_SECRET_KEY": Fernet.generate_key().decode(),
                                         "BRAIN_INVITE_SECRET": "test-invite-secret-0123456789"}),
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

    def test_client_invite_is_signed_scoped_and_single_use(self):
        inv = O.make_invite("globex", base="https://dash.example")
        self.assertTrue(inv["url"].startswith("https://dash.example/connect/notion?invite="))
        chk = O.check_invite(inv["invite"])
        self.assertEqual((chk["ok"], chk["tenant"]), (True, "globex"))
        payload, sig = inv["invite"].split(".")
        forged = O._b64(__import__("json").dumps({"t": "acme", "n": "x", "exp": 9999999999}).encode()) + "." + sig
        self.assertFalse(O.check_invite(forged)["ok"])           # a tenant swap breaks the signature
        r = O.exchange_invite(inv["invite"], "code", http=lambda b: {"access_token": "g-token"})
        self.assertTrue(r["ok"])
        self.assertEqual(O.token("globex"), "g-token")
        self.assertIsNone(O.token("acme"))
        self.assertFalse(O.check_invite(inv["invite"])["ok"])    # used once
        fresh = O.make_invite("acme")["invite"]
        with mock.patch("time.time", lambda: 9999999999 + 1):
            self.assertIn("expired", O.check_invite(fresh)["error"])

    def test_a_key_mismatch_reads_nothing(self):
        O.exchange("acme", "c", http=lambda b: {"access_token": "t"})
        with mock.patch.dict(os.environ, {"BRAIN_SECRET_KEY": Fernet.generate_key().decode()}):
            self.assertIsNone(O.token("acme"))


if __name__ == "__main__":
    unittest.main()
