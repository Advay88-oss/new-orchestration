"""Ops status for the dashboard, and a test alert.

    python -m pipeline.ops.cli status
    python -m pipeline.ops.cli test-alert
"""
from __future__ import annotations

import json
import sys

from pipeline.ops import alerts
from pipeline.ops import budget as B


def main(argv: list[str]) -> None:
    cmd = argv[0] if argv else "status"
    if cmd == "test-alert":
        sent = alerts.send("test-" + B.today() + "-" + str(len(alerts.recent(200)["alerts"])),
                           "Test alert: alerts reach this chat.", severity="info")
        print(json.dumps({"ok": True, "sent": sent}))
        return
    print(json.dumps({"ok": True, "budget": B.status(), **alerts.recent(15)}, default=str))


if __name__ == "__main__":
    main(sys.argv[1:])
