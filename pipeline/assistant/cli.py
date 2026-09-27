"""Short commands the dashboard runs for the assistant's records.

    python -m pipeline.assistant.cli threads --tenant vanna
    python -m pipeline.assistant.cli thread  --tenant vanna --id t_...
    python -m pipeline.assistant.cli delete  --tenant vanna --id t_...
    python -m pipeline.assistant.cli audit   --tenant vanna            # the log
    python -m pipeline.assistant.cli record  --tenant vanna            # one entry, JSON on stdin
"""
from __future__ import annotations

import argparse
import json
import re
import sys

from pipeline.assistant import store as ST

TENANT = re.compile(r"^[a-z0-9][a-z0-9_-]{1,40}$")
THREAD = re.compile(r"^t_[A-Za-z0-9_-]{6,40}$")
OWNER_ACTIONS = {"launch_run", "approve", "revise", "kill", "approve_profile", "open_notion_link", "copy_invite"}


def main(argv: list[str]) -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["threads", "thread", "delete", "audit", "record"])
    ap.add_argument("--tenant", required=True)
    ap.add_argument("--id", default="")
    a = ap.parse_args(argv)
    if not TENANT.match(a.tenant):
        raise SystemExit("bad tenant")
    if a.cmd in ("thread", "delete") and not THREAD.match(a.id):
        raise SystemExit("bad thread id")
    if a.cmd == "threads":
        out = {"ok": True, "threads": ST.threads(a.tenant)}
    elif a.cmd == "thread":
        t = ST.thread(a.tenant, a.id)
        out = {"ok": bool(t), "thread": t}
    elif a.cmd == "delete":
        out = {"ok": ST.delete_thread(a.tenant, a.id)}
    elif a.cmd == "audit":
        out = {"ok": True, "log": ST.audit_log(a.tenant)}
    else:
        d = json.loads(sys.stdin.read() or "{}")
        action = str(d.get("action") or "")
        if action not in OWNER_ACTIONS:
            raise SystemExit("unknown action")
        ST.audit(a.tenant, "owner", action, {k: d.get(k) for k in ("run_id", "directive", "result", "asked")},
                 str(d.get("thread_id") or ""))
        out = {"ok": True}
    print(json.dumps(out, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main(sys.argv[1:])
