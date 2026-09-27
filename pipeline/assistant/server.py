"""The assistant as a long-lived child of the dashboard.

One JSON request per stdin line, `{"id", "tenant", "messages"}`; every event
of that turn goes to stdout as a JSON line `{"id", ...event}`. Kept alive by
the dashboard (hermes-mission/lib/assistant.ts) so the Brain MCP session and
the imports are paid for once, not per message.

    python -m pipeline.assistant.server
"""
from __future__ import annotations

import json
import re
import sys

TENANT = re.compile(r"^[a-z0-9][a-z0-9_-]{1,40}$")


def _emit(obj: dict) -> None:
    sys.stdout.write(json.dumps(obj, ensure_ascii=False, default=str) + "\n")
    sys.stdout.flush()


def main() -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8")        # type: ignore[attr-defined]
        sys.stdin.reconfigure(encoding="utf-8")         # type: ignore[attr-defined]
    except Exception:                                   # noqa: BLE001
        pass
    from pipeline.assistant.chat import turn
    _emit({"id": None, "type": "ready"})
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except ValueError:
            continue
        rid = req.get("id")
        if req.get("base"):
            import os
            os.environ["ASSISTANT_BASE_URL"] = str(req["base"])[:200]
        tenant = str(req.get("tenant") or "")
        if not TENANT.match(tenant):
            _emit({"id": rid, "type": "error", "error": "pick a company first"})
            _emit({"id": rid, "type": "done"})
            continue
        try:
            for ev in turn(tenant, list(req.get("messages") or [])):
                _emit({"id": rid, **ev})
        except Exception as exc:                        # noqa: BLE001 — one turn fails alone
            _emit({"id": rid, "type": "error", "error": type(exc).__name__ + ": " + str(exc)[:300]})
            _emit({"id": rid, "type": "done"})


if __name__ == "__main__":
    main()
