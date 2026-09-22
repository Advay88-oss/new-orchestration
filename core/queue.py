"""Durable job queue.

The dashboard's `/api/run` spawned a subprocess and awaited `child.on('close')`,
so a run lived and died with the HTTP request. A full pipeline takes minutes;
the request times out, a deploy kills it, and there is no resume point because
nothing was journaled before the work started.

Here the dashboard only ever *enqueues*. A separate long-lived worker claims
jobs atomically (via `os.rename`, which is atomic on one filesystem, so two
workers cannot claim the same job) and runs them. Jobs that exceed
`max_attempts` move to `dead/` with their history intact rather than being
retried forever or silently dropped.
"""
from __future__ import annotations

import json
import os
import secrets
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

REPO = Path(__file__).resolve().parents[1]
QUEUE_ROOT = Path(os.environ.get("VANNA_QUEUE", REPO / "state" / "queue"))

PENDING = "pending"
CLAIMED = "claimed"
DONE = "done"
DEAD = "dead"

MAX_ATTEMPTS = 3


def _dir(name: str) -> Path:
    d = QUEUE_ROOT / name
    d.mkdir(parents=True, exist_ok=True)
    return d


@dataclass
class Job:
    id: str
    directive: str
    created_at: str
    attempts: int = 0
    idempotency_key: str | None = None
    requested_by: str = "dashboard"
    run_id: str | None = None
    last_error: str | None = None

    def to_json(self) -> str:
        return json.dumps(self.__dict__, ensure_ascii=False, indent=2)

    @staticmethod
    def from_path(p: Path) -> "Job":
        return Job(**json.loads(p.read_text(encoding="utf-8")))


def _write(path: Path, job: Job) -> None:
    tmp = path.with_suffix(".tmp")
    tmp.write_text(job.to_json(), encoding="utf-8")
    os.replace(tmp, path)


def enqueue(directive: str, *, requested_by: str = "dashboard",
            idempotency_key: str | None = None) -> Job:
    """Add a job. An idempotency key makes a retried POST a no-op rather than a
    duplicate run — a timeout does not mean the request did not land."""
    if idempotency_key:
        for state in (PENDING, CLAIMED, DONE):
            for p in _dir(state).glob("*.json"):
                try:
                    existing = Job.from_path(p)
                except Exception:
                    continue
                if existing.idempotency_key == idempotency_key:
                    return existing

    job = Job(
        id=f"JOB-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}-{secrets.token_hex(3)}",
        directive=directive.strip(),
        created_at=datetime.now(timezone.utc).isoformat(),
        requested_by=requested_by,
        idempotency_key=idempotency_key,
    )
    _write(_dir(PENDING) / f"{job.id}.json", job)
    return job


def claim() -> Job | None:
    """Atomically take the oldest pending job, or None.

    `os.rename` between two directories on the same filesystem is atomic and
    fails if the destination exists, so two workers racing for the same job
    cannot both win.
    """
    for p in sorted(_dir(PENDING).glob("*.json")):
        target = _dir(CLAIMED) / p.name
        try:
            os.rename(p, target)
        except OSError:
            continue                      # another worker got it
        try:
            job = Job.from_path(target)
        except Exception:
            target.unlink(missing_ok=True)
            continue
        job.attempts += 1
        _write(target, job)
        return job
    return None


def complete(job: Job, run_id: str) -> None:
    job.run_id = run_id
    src = _dir(CLAIMED) / f"{job.id}.json"
    _write(src, job)
    os.replace(src, _dir(DONE) / f"{job.id}.json")


def fail(job: Job, error: str, *, max_attempts: int = MAX_ATTEMPTS) -> str:
    """Requeue for another attempt, or dead-letter it. Never silently drop."""
    job.last_error = error[:1000]
    src = _dir(CLAIMED) / f"{job.id}.json"
    _write(src, job)
    if job.attempts >= max_attempts:
        os.replace(src, _dir(DEAD) / f"{job.id}.json")
        return DEAD
    os.replace(src, _dir(PENDING) / f"{job.id}.json")
    return PENDING


def requeue_stale(older_than_s: float = 3600) -> list[str]:
    """Recover jobs whose worker died mid-run. A claimed job that has not moved
    in an hour is assumed orphaned."""
    recovered = []
    cutoff = time.time() - older_than_s
    for p in _dir(CLAIMED).glob("*.json"):
        if p.stat().st_mtime < cutoff:
            try:
                job = Job.from_path(p)
            except Exception:
                continue
            job.last_error = "worker did not finish; requeued as stale"
            _write(p, job)
            os.replace(p, _dir(PENDING) / p.name)
            recovered.append(job.id)
    return recovered


def counts() -> dict[str, int]:
    return {s: len(list(_dir(s).glob("*.json"))) for s in (PENDING, CLAIMED, DONE, DEAD)}


def listing(state: str = PENDING, limit: int = 50) -> Iterator[dict[str, Any]]:
    for p in sorted(_dir(state).glob("*.json"), reverse=True)[:limit]:
        try:
            yield Job.from_path(p).__dict__
        except Exception:
            continue
