"""The safety gates fail closed, and the registry agrees with the facts ledger.

    .venv/Scripts/python.exe -m unittest pipeline.tests.test_p1_safety -v

No network and no paid calls: every model and HTTP call here is faked.
"""
from __future__ import annotations

import os

os.environ["BRAIN_MCP_DISABLE"] = "1"
os.environ["BRAIN_BACKEND"] = "sqlite"
os.environ["OPS_ALERTS"] = "0"      # tests never page the owner

import io
import json
import tempfile
import unittest
import urllib.error
import urllib.request
from pathlib import Path
from unittest import mock

# Ledger facts the gate is right to stop when written as a bare claim: the
# ledger records what the site shows, and its §4 says how to phrase it.
GATE_EXCEPTIONS = {
    "CLM-A28": "Site displays 15+ integrations: §4 says say 'Deep integrations with Blend, Aquarius and Soroswap'",
}


class RegistryMatchesLedger(unittest.TestCase):
    def test_registry_is_built_from_the_ledger(self):
        from pipeline.scripts import build_claims_registry as B
        have = B.REGISTRY.read_text(encoding="utf-8")
        self.assertEqual(have, B.build(), "registry/claims.jsonl is stale: run "
                                          "python -m pipeline.scripts.build_claims_registry")

    def test_no_usable_fact_is_blocked_by_the_gate(self):
        from pipeline.scripts import build_claims_registry as B
        from pipeline.scripts.claim_safety_gate import check
        rows = [json.loads(line) for line in B.build().splitlines()]
        self.assertTrue(any(r["claim"].startswith("Protocol comprises 14 Soroban") for r in rows))
        blocked = []
        for r in rows:
            if r["action"] != "USE" or r["id"] in GATE_EXCEPTIONS:
                continue
            v = check(r["claim"], platform="x", require_testnet=False)
            if any(str(x.get("severity", "")).upper() == "BLOCK" for x in v.get("violations") or []):
                blocked.append(r["id"] + " " + r["claim"][:80])
        self.assertEqual(blocked, [], "the gate blocks facts the ledger says are safe")

    def test_legacy_product_is_not_verified(self):
        from pipeline.scripts import build_claims_registry as B
        verified = " ".join(json.loads(l)["claim"].lower() for l in B.build().splitlines()
                            if json.loads(l)["action"] == "USE")
        for legacy in ("prop dashboard", "greeks dashboard", "erc-4337"):
            self.assertNotIn(legacy, verified)


class FactCheckFailsClosed(unittest.TestCase):
    def test_model_outage_blocks_and_keeps_gate_hits(self):
        from pipeline.gtm_os import agent_runtime as R
        from pipeline.gtm_os import fact_check as F
        with mock.patch.object(R, "brain_json", side_effect=RuntimeError("503 unavailable")):
            r = F.check_copy("Risk-free yield", "Vanna gives guaranteed returns.",
                             channels={"linkedin": "Earn 40% APY guaranteed."})
        self.assertFalse(r["ok"])
        joined = "\n".join(r["blocked"])
        self.assertIn("fact check could not run", joined)
        self.assertIn("(x)", joined)
        self.assertIn("(linkedin)", joined)

    def test_gate_error_blocks(self):
        from pipeline.gtm_os import fact_check as F
        with mock.patch.object(F, "_gate", side_effect=ImportError("rules missing")):
            found, blocked = F._gate_all({"x": "anything"})
        self.assertEqual(found, [])
        self.assertTrue(blocked and "could not run" in blocked[0])

    def test_poster_words_are_the_drawn_lines(self):
        from pipeline.gtm_os.fact_check import poster_words
        brief = "Material: line\nHeadline: Borrow and deploy\nSubtitle: SmartAccounts hold it.\nIdea: not drawn"
        self.assertEqual(poster_words(brief), "Borrow and deploy\nSmartAccounts hold it.")


class BudgetFailsClosed(unittest.TestCase):
    def test_unreadable_ledger_refuses_paid_calls(self):
        from pipeline.ops import budget as B

        def down():
            raise RuntimeError("db down")
        with mock.patch.object(B, "db", down):
            with self.assertRaises(B.BudgetExceeded):
                B.check("gemini")
            self.assertEqual(B.spent(), {})        # reporting stays lenient


class ModelRetries(unittest.TestCase):
    def setUp(self):
        from pipeline.gtm_os import agent_runtime as R
        self.R = R
        self.waits = mock.patch.object(R, "RETRY_WAITS", (0.0, 0.0))
        self.waits.start()

    def tearDown(self):
        self.waits.stop()

    def _resp(self, body: bytes):
        class Resp(io.BytesIO):
            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False
        return Resp(body)

    def test_503_is_retried(self):
        calls = []

        def fake(req, timeout=None):
            calls.append(1)
            if len(calls) < 3:
                raise urllib.error.HTTPError(req.full_url, 503, "busy", {}, io.BytesIO(b""))
            return self._resp(b'{"ok": 1}')
        with mock.patch.object(urllib.request, "urlopen", fake):
            self.assertEqual(self.R._post("http://model", {}, 5), {"ok": 1})
        self.assertEqual(len(calls), 3)

    def test_400_is_not_retried(self):
        calls = []

        def fake(req, timeout=None):
            calls.append(1)
            raise urllib.error.HTTPError(req.full_url, 400, "bad", {}, io.BytesIO(b""))
        with mock.patch.object(urllib.request, "urlopen", fake):
            with self.assertRaises(urllib.error.HTTPError):
                self.R._post("http://model", {}, 5)
        self.assertEqual(len(calls), 1)


class BlockedRunsCannotBeApproved(unittest.TestCase):
    def test_approve_on_blocked_run_raises(self):
        from pipeline.gtm_learning import feedback as FB
        with tempfile.TemporaryDirectory() as tmp:
            run = Path(tmp) / "GTM-20261008-000000"
            run.mkdir()
            (run / "summary.json").write_text(json.dumps({"review_passed": False}), encoding="utf-8")
            with mock.patch.object(FB, "RUNS", Path(tmp)):
                with self.assertRaises(FB.GateBlocked):
                    FB.record(run.name, "approve")

    def test_blocked_run_has_no_approve_button(self):
        from pipeline.gtm_os.telegram_sender import _decision_keyboard
        labels = [b["callback_data"].split(":")[0] for b in _decision_keyboard("R", passed=False)["inline_keyboard"][0]]
        self.assertEqual(labels, ["revise", "kill"])
        labels = [b["callback_data"].split(":")[0] for b in _decision_keyboard("R", passed=True)["inline_keyboard"][0]]
        self.assertEqual(labels, ["approve", "revise", "kill"])


if __name__ == "__main__":
    unittest.main()
