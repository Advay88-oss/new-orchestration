"""What the pipeline does on GCP — one entry point for the Cloud Run Job and
the dashboard container.

    python -m pipeline.gtm_os.cloud_job cycle [--directive "..."] [--no-video]
    python -m pipeline.gtm_os.cloud_job tick            # the scheduler's due jobs (Cloud Scheduler, hourly)
    python -m pipeline.gtm_os.cloud_job admin-schema    # Cloud SQL: schema, role, row-level security
    python -m pipeline.gtm_os.cloud_job admin-migrate   # the bucket's brain snapshots -> Cloud SQL
    python -m pipeline.gtm_os.cloud_job telegram        # one Telegram update on stdin (the webhook)

A container starts with an empty disk. Each command first restores the
learned state from the bucket (the brand brain itself lives in Cloud SQL;
the bucket holds its images, the Coach's rules, the scheduler's clock), does
its work, and pushes what changed back. A cycle pushes its run as it goes,
so the dashboard shows it live.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any

# Jobs the cloud scheduler runs by default. The autonomous GTM cycle and the
# model-heavy panels spend money on every tick, so they are opt-in:
# SCHEDULER_ONLY=notion_sync,metrics_collect,gtm_cycle,... on the job.
DEFAULT_CLOUD_JOBS = "notion_sync,metrics_collect"


def _restore() -> dict[str, Any]:
    from pipeline.gtm_os.state_sync import pull_state
    return pull_state()


def _save() -> dict[str, Any]:
    from pipeline.gtm_os.state_sync import push_state
    return push_state()


def cycle(directive: str | None, with_video: bool) -> int:
    _restore()
    from pipeline.gtm_os.autonomous_cycle import run_cycle
    out = run_cycle(directive or None, with_video=with_video)     # pushes run + state at the end
    print(json.dumps({"run_id": out.get("run_id"), "status": out.get("status")}))
    return 0 if out.get("status") in ("completed", "review_blocked", "NO_ACTION", "KILL") else 1


def tick() -> int:
    os.environ.setdefault("SCHEDULER_ONLY", DEFAULT_CLOUD_JOBS)
    _restore()
    from pipeline.scheduler.configurable_scheduler_daemon import run_scheduler_tick
    out = run_scheduler_tick()
    _save()
    print(json.dumps(out, default=str)[:4000])
    return 0


def admin_schema() -> int:
    from pipeline.brand_brain import pg
    print(json.dumps(pg.apply_schema(os.environ["BRAIN_PG_ADMIN_URL"], os.environ.get("BRAIN_APP_PASSWORD"))))
    return 0


def admin_migrate() -> int:
    """Import every tenant snapshot in the bucket that Cloud SQL lacks."""
    from pathlib import Path
    from pipeline.brand_brain import store as S
    from pipeline.brand_brain.pg import migrate_tenant
    # pull_state imports missing tenants into Postgres itself when the
    # backend is Postgres; this reports what is there afterwards.
    res = _restore()
    have = S.tenants()
    root = Path(__file__).resolve().parents[1] / "brain" / "tenants"
    extra = []
    for db in sorted(root.glob("*/brain.db")):
        if db.parent.name not in have:
            extra.append(migrate_tenant(db.parent.name, db, S.database_url()))
    print(json.dumps({"restored": res, "tenants": S.tenants(), "imported": extra}, default=str))
    return 0


def telegram() -> int:
    """One update from Telegram's webhook, on stdin: a button or a reply."""
    from pipeline.gtm_os.feedback_listener import handle
    from pipeline.gtm_os.telegram_sender import NotConfigured, _chat_id, _token
    update = json.loads(sys.stdin.read() or "{}")
    try:
        reviewer = _chat_id()
    except NotConfigured:
        reviewer = None
    # The web container restored the state at start; only the two pending
    # notes (revise, posted) change here, so only they are pushed back.
    row = handle(update, _token(), reviewer)
    from pipeline.gtm_os.state_sync import push_state_files
    push_state_files(["pipeline/state/telegram_pending_revise.json",
                      "pipeline/state/telegram_pending_post.json"])
    print(json.dumps({"ok": True, "recorded": bool(row)}, default=str))
    return 0


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["cycle", "tick", "admin-schema", "admin-migrate", "telegram"])
    ap.add_argument("--directive", default=None)
    ap.add_argument("--no-video", action="store_true")
    a = ap.parse_args(argv)
    if a.cmd == "cycle":
        return cycle(a.directive, not a.no_video)
    return {"tick": tick, "admin-schema": admin_schema, "admin-migrate": admin_migrate,
            "telegram": telegram}[a.cmd]()


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
