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
DEFAULT_CLOUD_JOBS = "notion_sync,metrics_collect,ops_watch,brain_watch"


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
    ok = out.get("status") in ("completed", "review_blocked", "NO_ACTION", "KILL", "refused_budget", "skipped_locked")
    if not ok:
        from pipeline.ops import alerts
        alerts.send("cycle-failed-" + str(out.get("run_id")), "A GTM cycle failed: " + str(out.get("run_id"))
                    + " — " + str(out.get("status")) + ": " + str(out.get("error") or out.get("reason") or "")[:300],
                    severity="critical")
    return 0 if ok else 1


def video(run_id: str) -> int:
    """A Veo video for a run that already has its poster: the cycle's own
    video step (Motion Director plan, Veo build from the empty ground, the
    frame-by-frame judge), then the clip goes to the bucket and to Telegram
    for review. Nothing is published."""
    import re
    from pathlib import Path
    from pipeline.gtm_os import state_sync as S
    if not re.match(r"^GTM-\d{8}-\d{6}$", run_id or ""):
        print(json.dumps({"ok": False, "error": "--run GTM-YYYYMMDD-HHMMSS"}))
        return 2
    _restore()
    S.pull_run(run_id)
    summ = S.RUNS_DIR / run_id / "summary.json"
    if not summ.exists():
        print(json.dumps({"ok": False, "error": "run not in the bucket: " + run_id}))
        return 1
    s = json.loads(summ.read_text(encoding="utf-8"))
    poster = S.STATE_DIR / (run_id + "_visual.png")
    S._client().bucket(S.BUCKET).blob(S.PREFIX_ASSETS + run_id + "/visual.png").download_to_filename(str(poster))
    s["visual_path"] = str(poster)
    from pipeline.brand_brain import mcp_client
    mcp_client.enable()
    from pipeline.gtm_os import agent_runtime as R
    from pipeline.gtm_os.autonomous_cycle import render_video
    R.set_run(run_id)                               # the calls and stages join this run
    path = render_video(s, run_id)
    if not path or not Path(path).exists():
        print(json.dumps({"ok": False, "run_id": run_id, "error": "no video was made"}))
        return 1
    s["video_path"] = str(path)
    summ.write_text(json.dumps(s, indent=2, default=str), encoding="utf-8")
    pushed = S.push_run(run_id, s)
    sent = False
    try:
        from pipeline.gtm_os import telegram_sender as T
        cap = ("Video for " + run_id + " (" + str(s.get("video_mode")) + ", judge "
               + str((s.get("video_review") or {}).get("verdict")) + "). For review; nothing is published.")
        T._post_file("sendVideo", "video", Path(path), {"chat_id": T._chat_id(), "caption": cap[:1000]}, T._token())
        sent = True
    except Exception as exc:                        # noqa: BLE001 — the video is in the bucket regardless
        print("telegram: " + str(exc)[:200])
    print(json.dumps({"ok": True, "run_id": run_id, "video_mode": s.get("video_mode"),
                      "review": s.get("video_review"), "pushed": pushed, "telegram": sent}, default=str))
    return 0


def admin_tidy() -> int:
    """Every tenant's brain on Cloud SQL: tag legal/pricing, drop duplicate
    passages and site menus (Brain.tidy), and register a logo that ships in
    the image (brand_brain.logo saved it under the tenant's images) when the
    brain has none."""
    import json as _json
    from pipeline.brand_brain import store as S
    from pipeline.brand_brain.client import Brain
    from pipeline.brand_brain.logo import register_shipped
    out = {}
    for t in S.tenants():
        r = {"tidy": Brain(t).tidy()}
        got = register_shipped(t)
        if got:
            r["logo"] = got
        out[t] = r
    print(_json.dumps(out, default=str))
    return 0


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


def _guarded_main(argv: list[str]) -> int:
    """Any crash of a job is recorded and alerted before it exits."""
    try:
        return main(argv)
    except SystemExit:
        raise
    except BaseException as exc:                    # noqa: BLE001
        try:
            from pipeline.ops import alerts
            alerts.capture("cloud_job " + (argv[0] if argv else "?"), exc)
        finally:
            raise


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["cycle", "tick", "admin-schema", "admin-migrate", "admin-tidy", "telegram", "watch", "video"])
    ap.add_argument("--directive", default=None)
    ap.add_argument("--no-video", action="store_true")
    ap.add_argument("--run", default=None, help="video: the run whose poster to animate")
    a = ap.parse_args(argv)
    if a.cmd == "video":
        return video(a.run or "")
    if a.cmd == "cycle":
        return cycle(a.directive, not a.no_video)
    if a.cmd == "watch":
        from pipeline.ops.watch import run as watch
        print(json.dumps(watch(), default=str)[:4000])
        return 0
    return {"tick": tick, "admin-schema": admin_schema, "admin-migrate": admin_migrate, "admin-tidy": admin_tidy,
            "telegram": telegram}[a.cmd]()


if __name__ == "__main__":
    sys.exit(_guarded_main(sys.argv[1:]))
