"""The assistant as a long-lived child of the dashboard.

One JSON request per stdin line; every event goes to stdout as a JSON line
tagged with the request id. Turns run in parallel (a small pool), so one
slow question does not hold up another; the Brain MCP sessions and imports
are paid for once, not per message.

    {"op": "turn", "id", "tenant", "text", "thread_id"?, "base"?}
    {"op": "cancel", "id"}                 stop that turn at the next chunk
    {"op": "ping", "id"}                   -> {"type": "pong"}

    python -m pipeline.assistant.server
"""
from __future__ import annotations

import json
import os
import re
import sys
import threading
from concurrent.futures import ThreadPoolExecutor

try:
    from pipeline.ops.quiet_windows import install as _quiet_console
    _quiet_console()
except Exception:                               # noqa: BLE001 — the assistant still has to answer
    pass

TENANT = re.compile(r"^[a-z0-9][a-z0-9_-]{1,40}$")
WORKERS = int(os.environ.get("ASSISTANT_WORKERS", "4"))
_out = threading.Lock()
_cancelled: set[str] = set()


def _emit(obj: dict) -> None:
    line = json.dumps(obj, ensure_ascii=False, default=str) + "\n"
    with _out:
        sys.stdout.write(line)
        sys.stdout.flush()


def _threads(req: dict) -> None:
    from pipeline.assistant import store as ST
    rid = str(req.get("id") or "")
    tenant = str(req.get("tenant") or "")
    if not TENANT.match(tenant):
        _emit({"id": rid, "type": "result", "ok": False, "error": "pick a company first"})
        return
    try:
        if req.get("op") == "thread":
            t = ST.thread(tenant, str(req.get("thread_id") or ""))
            _emit({"id": rid, "type": "result", "ok": bool(t), "thread": t})
        elif req.get("op") == "delete":
            _emit({"id": rid, "type": "result", "ok": ST.delete_thread(tenant, str(req.get("thread_id") or ""))})
        else:
            _emit({"id": rid, "type": "result", "ok": True, "threads": ST.threads(tenant)})
    except Exception as exc:                        # noqa: BLE001 — the sidebar shows a sentence, never a connection string
        _emit({"id": rid, "type": "result", "ok": False, "error": type(exc).__name__})


def _run(req: dict) -> None:
    from pipeline.assistant.chat import turn
    rid = str(req.get("id") or "")
    tenant = str(req.get("tenant") or "")
    if not TENANT.match(tenant):
        _emit({"id": rid, "type": "error", "error": "pick a company first"})
        _emit({"id": rid, "type": "done"})
        return
    try:
        for ev in turn(tenant, str(req.get("text") or ""), thread_id=req.get("thread_id") or None,
                       cancelled=lambda: rid in _cancelled, client=bool(req.get("client")),
                       role=str(req.get("role") or "")):
            _emit({"id": rid, **ev})
    except Exception as exc:                        # noqa: BLE001 — one turn fails alone
        _emit({"id": rid, "type": "error", "error": type(exc).__name__ + ": " + str(exc)[:300]})
        _emit({"id": rid, "type": "done"})
    finally:
        _cancelled.discard(rid)


def main() -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8")        # type: ignore[attr-defined]
        sys.stdin.reconfigure(encoding="utf-8")         # type: ignore[attr-defined]
    except Exception:                                   # noqa: BLE001
        pass
    import pipeline.assistant.chat  # noqa: F401  — imports paid before "ready"
    pool = ThreadPoolExecutor(max_workers=WORKERS, thread_name_prefix="assistant-turn")
    _emit({"id": None, "type": "ready"})
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except ValueError:
            continue
        op = req.get("op", "turn")
        if req.get("base"):
            os.environ["ASSISTANT_BASE_URL"] = str(req["base"])[:200]
        if op == "cancel":
            _cancelled.add(str(req.get("id") or ""))
        elif op == "ping":
            _emit({"id": req.get("id"), "type": "pong"})
        elif op in ("threads", "thread", "delete"):
            pool.submit(_threads, req)
        else:
            pool.submit(_run, req)
    # stdin closed (the dashboard went away): finish the turns in flight.
    pool.shutdown(wait=True)


if __name__ == "__main__":
    main()
