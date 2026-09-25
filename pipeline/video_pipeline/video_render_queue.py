"""Phase 10: Asynchronous Video Rendering Queue (video_render_queue.py).

Decouples Remotion rendering from foreground terminal execution.
Features:
  - Background thread pool / worker process execution.
  - Job tracking: QUEUED -> RENDERING -> COMPLETED / FAILED.
  - Progress and elapsed time monitoring.
  - Persistent job state in video_render_jobs.jsonl via AtomicJsonlStore.
  - Non-blocking job submission.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

REPO_ROOT = Path(__file__).resolve().parents[2]
REMOTION_DIR = Path(os.environ.get("REMOTION_DIR") or (REPO_ROOT / "remotion-video"))
STATE_DIR = REPO_ROOT / "pipeline" / "state"
JOBS_FILE = STATE_DIR / "video_render_jobs.jsonl"

from pipeline.gtm_storage.atomic_store import AtomicJsonlStore


class RenderJob(BaseModel):
    """Encapsulates a Remotion video render job."""
    job_id: str
    composition_id: str
    output_path: str
    status: str = "QUEUED"  # QUEUED, RENDERING, COMPLETED, FAILED
    submitted_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    duration_sec: float = 0.0
    output_size_bytes: int = 0
    error_message: Optional[str] = None
    command: List[str] = Field(default_factory=list)


class VideoRenderQueue:
    """Asynchronous background rendering queue for Remotion product films."""

    def __init__(self, remotion_dir: Optional[Path] = None):
        self.remotion_dir = remotion_dir or REMOTION_DIR
        self.jobs_store = AtomicJsonlStore(JOBS_FILE)
        self.active_jobs: Dict[str, RenderJob] = {}
        self._lock = threading.Lock()

    def submit_render_job(
        self,
        composition_id: str,
        output_filename: str,
        simulate: bool = False
    ) -> str:
        """Submits a video rendering job to run asynchronously in background."""
        job_id = f"JOB-VID-{int(time.time())}-{composition_id[:8]}"
        out_path = str(self.remotion_dir / "out" / output_filename)

        cmd = ["npx", "remotion", "render", composition_id, f"out/{output_filename}"]
        if sys.platform == "win32":
            cmd = ["cmd.exe", "/c", "npx", "remotion", "render", composition_id, f"out/{output_filename}"]

        job = RenderJob(
            job_id=job_id,
            composition_id=composition_id,
            output_path=out_path,
            status="QUEUED",
            command=cmd
        )

        with self._lock:
            self.active_jobs[job_id] = job
        self.jobs_store.append(job.model_dump())

        # Spawn background worker thread
        thread = threading.Thread(
            target=self._worker_execute,
            args=(job_id, simulate),
            daemon=True
        )
        thread.start()

        print(f"🎬 VIDEO QUEUE: Submitted {composition_id} as Job {job_id} (Background Rendering Active).")
        return job_id

    def get_job_status(self, job_id: str) -> Optional[RenderJob]:
        """Gets current in-memory or persisted job status."""
        with self._lock:
            if job_id in self.active_jobs:
                return self.active_jobs[job_id]

        for record in self.jobs_store.read_all():
            if record.get("job_id") == job_id:
                return RenderJob(**record)
        return None

    def list_jobs(self) -> List[RenderJob]:
        """Lists all rendering jobs."""
        records = self.jobs_store.read_all()
        return [RenderJob(**r) for r in records]

    def _worker_execute(self, job_id: str, simulate: bool):
        """Worker thread executing the render command."""
        job = self.active_jobs.get(job_id)
        if not job:
            return

        job.status = "RENDERING"
        job.started_at = datetime.now(timezone.utc).isoformat()
        start_t = time.time()
        self._sync_job_state(job)

        if simulate:
            # Deterministic fast execution for automated tests
            time.sleep(0.3)
            job.status = "COMPLETED"
            job.completed_at = datetime.now(timezone.utc).isoformat()
            job.duration_sec = round(time.time() - start_t, 2)
            job.output_size_bytes = 8740120
            self._sync_job_state(job)
            return

        try:
            res = subprocess.run(
                job.command,
                cwd=str(self.remotion_dir),
                capture_output=True,
                text=True,
                timeout=600
            )

            job.duration_sec = round(time.time() - start_t, 2)
            job.completed_at = datetime.now(timezone.utc).isoformat()

            if res.returncode == 0:
                job.status = "COMPLETED"
                out_p = Path(job.output_path)
                if out_p.exists():
                    job.output_size_bytes = out_p.stat().st_size
                print(f"✅ VIDEO QUEUE: Job {job_id} completed successfully in {job.duration_sec}s.")
            else:
                job.status = "FAILED"
                job.error_message = res.stderr[:500] if res.stderr else "Non-zero exit code"
                print(f"❌ VIDEO QUEUE: Job {job_id} failed: {job.error_message}")
        except Exception as e:
            job.status = "FAILED"
            job.error_message = str(e)
            job.completed_at = datetime.now(timezone.utc).isoformat()
            print(f"❌ VIDEO QUEUE: Job {job_id} exception: {e}")

        self._sync_job_state(job)

    def _sync_job_state(self, job: RenderJob):
        """Syncs in-memory job updates into persistent Atomic store."""
        records = self.jobs_store.read_all()
        updated = []
        found = False
        for r in records:
            if r.get("job_id") == job.job_id:
                updated.append(job.model_dump())
                found = True
            else:
                updated.append(r)
        if not found:
            updated.append(job.model_dump())
        self.jobs_store.atomic_overwrite(updated)
