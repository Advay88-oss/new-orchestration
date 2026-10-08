"""Run the test suite with the network switched off.

Some tests reach real model APIs when nothing is mocked, and every model
call costs money. This runner blocks every connection that is not to this
machine before any test module is imported, so a test that would make a
paid call fails instead of spending:

    python -m pipeline.tests.offline                    # every module in OFFLINE_SAFE
    python -m pipeline.tests.offline test_p1_safety     # named modules

CI runs it the same way (.github/workflows/ci.yml).
"""
from __future__ import annotations

import os
import socket
import sys
import unittest

# Modules known to pass with no network. A new test file joins this list once
# it passes here; the ones left out call live services when nothing is mocked.
OFFLINE_SAFE = [
    "test_p1_safety",
    "test_agents_debate",
    "test_copilot_layers",
    "test_assistant_chat",
    "test_assistant_tools",
    "test_blockers_4_5_6_7",
    "test_brain_hygiene",
    "test_brain_mcp",
    "test_brain_postgres",          # skips without a database
    "test_brain_watch",
    "test_brand_brain",
    "test_gtm_campaigns",
    "test_gtm_learning",
    "test_gtm_machines",
    "test_gtm_regression_opp_sandbox",
    "test_learning_loop",
    "test_metrics_loop",
    "test_notion_oauth",
    "test_notion_sync",
    "test_ops",
]
# Not yet offline (they call the live model when nothing is mocked):
# test_all_remaining_blockers, test_gtm_content, test_gtm_creative,
# test_gtm_orchestration, test_gtm_phase1_1_integrity.

_LOCAL = {"127.0.0.1", "::1", "localhost"}
_real_connect = socket.socket.connect
_real_create = socket.create_connection


class NetworkBlocked(OSError):
    pass


def _host(address) -> str:
    return str(address[0] if isinstance(address, tuple) else address)


def _connect(self, address):
    if self.family == getattr(socket, "AF_UNIX", None) or _host(address) in _LOCAL:
        return _real_connect(self, address)
    raise NetworkBlocked("network is off in tests: " + _host(address))


def _create(address, *a, **k):
    if _host(address) in _LOCAL:
        return _real_create(address, *a, **k)
    raise NetworkBlocked("network is off in tests: " + _host(address))


def block_network() -> None:
    socket.socket.connect = _connect
    socket.create_connection = _create
    # No key, no paid call even if something slips past the socket check.
    for k in ("GEMINI_API_KEY", "GOOGLE_API_KEY", "APIFY_TOKEN", "CONTEXT_DEV_API_KEY",
              "TELEGRAM_BOT_TOKEN", "NOTION_TOKEN"):
        os.environ.pop(k, None)
    os.environ.setdefault("OPS_ALERTS", "0")
    os.environ.setdefault("BRAIN_MCP_DISABLE", "1")
    os.environ.setdefault("BRAIN_BACKEND", "sqlite")


def main(argv: list[str]) -> int:
    block_network()
    names = argv or OFFLINE_SAFE
    suite = unittest.TestSuite()
    loader = unittest.defaultTestLoader
    for n in names:
        suite.addTests(loader.loadTestsFromName("pipeline.tests." + n.removesuffix(".py")))
    result = unittest.TextTestRunner(verbosity=1).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
