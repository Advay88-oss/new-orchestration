"""Queue worker — the long-lived process that actually runs pipelines.

Replaces `spawn('cmd.exe', ['/c', 'python', ...])` from an HTTP handler, which
tied a multi-minute run to a request that could not survive it.

Also replaces the bare `while True:` scheduler daemon. This loop is intended to
be supervised by the OS (Windows Task Scheduler, systemd, or a container
restart policy) — `--once` exists precisely so a scheduler can own the cadence
instead of the process owning it. A `while True` that nothing restarts drops
cron's single guarantee: that something external brings the schedule back.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import traceback
from pathlib import Path

from . import queue as Q
from .llm import LLMClient
from .pipeline import run_pipeline
from .runlog import RUNS_ROOT, RunLog, list_runs

HEARTBEAT = Path(os.environ.get("VANNA_WORKER_HEARTBEAT",
                                Path(__file__).resolve().parents[1] / "state" / "worker.json"))


def beat(state: str, **extra) -> None:
    """Liveness that cannot go stale unnoticed: it carries its own timestamp, so
    a reader can tell 'running' from 'last said running 25 hours ago'. The old
    daemon_status.json claimed RUNNING with a pid that had been dead for a day."""
    HEARTBEAT.parent.mkdir(parents=True, exist_ok=True)
    HEARTBEAT.write_text(json.dumps({
        "state": state, "pid": os.getpid(), "ts": time.time(), **extra,
    }, default=str), encoding="utf-8")


def recent_layouts(n: int = 6) -> list[str]:
    """Layouts used by recent runs, so the novelty gate has real history."""
    out: list[str] = []
    for summary in list_runs(limit=n * 2):
        rid = summary.get("run_id")
        if not rid:
            continue
        spec_file = RUNS_ROOT / rid / "artifacts"
        if not spec_file.exists():
            continue
        for p in spec_file.glob("spec.*.json"):
            try:
                out.append(json.loads(p.read_text(encoding="utf-8")).get("layout", ""))
            except Exception:
                continue
    return [x for x in out if x][:n]


def process_one(model: str | None = None) -> bool:
    """Claim and run one job. Returns False when the queue is empty."""
    job = Q.claim()
    if job is None:
        beat("idle")
        return False

    beat("running", job=job.id, directive=job.directive)
    print(f"[worker] claimed {job.id} (attempt {job.attempts}): {job.directive!r}")
    try:
        client = LLMClient(model=model) if model else LLMClient()
        summary = run_pipeline(job.directive, client=client,
                               recent_layouts=recent_layouts())
        Q.complete(job, summary["run_id"])
        print(f"[worker] {job.id} -> run {summary['run_id']} status={summary['status']}")
        if summary.get("degraded"):
            print(f"[worker]   degraded stages: {', '.join(summary['degraded'])}")
        if summary.get("failed"):
            print(f"[worker]   failed stages:   {', '.join(summary['failed'])}")
    except Exception as exc:                        # noqa: BLE001 — boundary
        where = Q.fail(job, f"{type(exc).__name__}: {exc}\n{traceback.format_exc()[:800]}")
        print(f"[worker] {job.id} errored -> {where}: {exc}", file=sys.stderr)
    finally:
        beat("idle")
    return True


def main() -> int:
    ap = argparse.ArgumentParser(description="Vanna v2 queue worker")
    ap.add_argument("--once", action="store_true",
                    help="drain the queue and exit (use this under a supervisor)")
    ap.add_argument("--interval", type=float, default=10.0)
    ap.add_argument("--model", default=None)
    ap.add_argument("--recover-stale", type=float, default=3600.0,
                    help="requeue jobs claimed longer ago than this many seconds")
    a = ap.parse_args()

    recovered = Q.requeue_stale(a.recover_stale)
    if recovered:
        print(f"[worker] requeued {len(recovered)} stale job(s): {', '.join(recovered)}")

    if a.once:
        n = 0
        while process_one(a.model):
            n += 1
        print(f"[worker] drained {n} job(s)")
        return 0

    print(f"[worker] polling every {a.interval}s (ctrl-c to stop)")
    beat("idle")
    try:
        while True:
            if not process_one(a.model):
                time.sleep(a.interval)
    except KeyboardInterrupt:
        beat("stopped")
        print("\n[worker] stopped")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
