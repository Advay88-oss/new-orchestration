"""GCS as the seam between the local pipeline and the deployed dashboard.

The agents cannot run on Cloud Run. They need the local Chrome bridge, the
Brain DB, the font files and a writable render scratch, and the cycle spends
four minutes per run — none of which belongs in a request-scoped container. So
the split is the one the architecture already describes: the pipeline runs
here, the dashboard runs there, and object storage is what they share.

Without this the deployed dashboard reads `pipeline/state/gtm_runs` from a
container filesystem where that directory does not exist, and reports zero
runs and zero agents — a working system rendered as an empty one.

What is pushed is deliberately narrow: the run journal and the assets a
reviewer needs to see — plus, since 2026-09-26, the brain and learning
state (push_state / pull_state below). Not the docs cache, not the render
scratch. A push failure never fails a run — the assets are already on disk and
the cycle has already done its work.
"""
from __future__ import annotations

import json
import mimetypes
import os
import re
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Optional

REPO_ROOT = Path(__file__).resolve().parents[2]
STATE_DIR = REPO_ROOT / "pipeline" / "state"
RUNS_DIR = STATE_DIR / "gtm_runs"

BUCKET = os.environ.get("VANNA_STATE_BUCKET", "vanna-gtm-state-504607")
PROJECT = os.environ.get("VANNA_GCP_PROJECT", "sales-agent-504607")

PREFIX_RUNS = "gtm_runs/"
PREFIX_ASSETS = "assets/"
PREFIX_PANELS = "panels/"

# Journal and summary only. The element clip and the raw pre-composite PNGs are
# intermediates — pushing them would multiply the upload for files nobody opens.
# harvest.json is what A01 actually brought back — every signal with its
# source, the companies named in it, and when it was scraped. The
# Scraped Intelligence view reads it, so it has to cross the seam.
# analysis.json is A02's reading of that harvest — grades, moves and
# strategies — and the Vanna References view is built on it; without it the
# deployed dashboard showed every run as unread.
RUN_FILES = ("summary.json", "calls.jsonl", "stages.jsonl", "harvest.json",
             "analysis.json", "feedback.json", "partial.json", "decisions.jsonl",
             "published.json")


def in_cloud() -> bool:
    """Running on GCP (a Cloud Run service or job), where the filesystem is
    ephemeral and the bucket is the record."""
    return bool(os.environ.get("K_SERVICE") or os.environ.get("CLOUD_RUN_JOB"))


def pull_run(run_id: str) -> int:
    """Fetch one run's files from the bucket into the local runs folder.
    Returns how many were fetched; never raises."""
    if not re.match(r"^GTM-\d{8}-\d{6}$", str(run_id)):
        return 0
    try:
        bucket = _client().bucket(BUCKET)
        blobs = list(bucket.list_blobs(prefix=PREFIX_RUNS + run_id + "/"))
    except Exception:                               # noqa: BLE001 — boundary
        return 0
    d = RUNS_DIR / run_id
    d.mkdir(parents=True, exist_ok=True)
    n = 0
    for b in blobs:
        name = b.name.rsplit("/", 1)[-1]
        if name in RUN_FILES:
            try:
                b.download_to_filename(str(d / name))
                n += 1
            except Exception:                       # noqa: BLE001 — this file fails alone
                pass
    return n


def ensure_run(run_id: str) -> bool:
    """A run's folder is present locally, fetching it from the bucket in the
    cloud (a fresh container has no runs on disk)."""
    if (RUNS_DIR / run_id / "summary.json").exists() or (RUNS_DIR / run_id / "partial.json").exists():
        return True
    if in_cloud() or os.environ.get("VANNA_PULL_RUNS") == "1":
        pull_run(run_id)
    return (RUNS_DIR / run_id).is_dir()


def runs_with(name: str) -> list[str]:
    """Run ids whose folder in the bucket holds `name` (e.g. published.json)."""
    try:
        bucket = _client().bucket(BUCKET)
        return sorted({b.name.split("/")[1] for b in bucket.list_blobs(prefix=PREFIX_RUNS)
                       if b.name.endswith("/" + name)})
    except Exception:                               # noqa: BLE001 — boundary
        return []


def _client():
    from google.cloud import storage
    return storage.Client(project=PROJECT)


def available() -> bool:
    try:
        _client().bucket(BUCKET).exists()
        return True
    except Exception:                               # noqa: BLE001 — boundary
        return False


def _upload(bucket, local: Path, key: str, *, if_generation: Optional[int] = None) -> Optional[str]:
    """Upload one file. `if_generation`: only if the object is still at that
    generation (0: only if it does not exist yet), so a write that landed
    since it was listed is never overwritten. Returns the key, or None."""
    try:
        blob = bucket.blob(key)
        ctype = mimetypes.guess_type(local.name)[0]
        kwargs = {} if if_generation is None else {"if_generation_match": int(if_generation)}
        blob.upload_from_filename(str(local), content_type=ctype, **kwargs)
        return key
    except Exception:                               # noqa: BLE001 — boundary (412: someone wrote first)
        return None


def push_run(run_id: str, summary: dict[str, Any]) -> dict[str, Any]:
    """Push one run's journal and assets. Never raises."""
    try:
        bucket = _client().bucket(BUCKET)
    except Exception as exc:                        # noqa: BLE001 — boundary
        return {"pushed": False, "reason": "no GCS client: " + str(exc)[:160]}

    jobs: list[tuple[Path, str]] = []

    run_dir = RUNS_DIR / run_id
    for name in RUN_FILES:
        p = run_dir / name
        if p.exists():
            jobs.append((p, PREFIX_RUNS + run_id + "/" + name))

    # Assets live outside the run folder (the visual and meme are written to
    # STATE_DIR so /api/media can serve them locally), so they are collected by
    # the summary's own paths rather than by globbing a directory.
    for key, ext in (("visual_path", ".png"), ("meme_path", ".png"),
                     ("video_path", ".mp4")):
        raw = summary.get(key)
        if not raw:
            continue
        p = Path(str(raw))
        if p.exists():
            jobs.append((p, PREFIX_ASSETS + run_id + "/"
                         + key.replace("_path", "") + ext))

    if not jobs:
        return {"pushed": False, "reason": "nothing to push"}

    with ThreadPoolExecutor(max_workers=6) as pool:
        done = list(pool.map(lambda j: _upload(bucket, j[0], j[1]), jobs))

    ok = [d for d in done if d]
    return {"pushed": bool(ok), "objects": len(ok), "failed": len(done) - len(ok),
            "bucket": BUCKET}


def push_panels() -> dict[str, Any]:
    """Push the Ideas and Memes feeds the dashboard panels read."""
    try:
        bucket = _client().bucket(BUCKET)
    except Exception as exc:                        # noqa: BLE001 — boundary
        return {"pushed": False, "reason": str(exc)[:160]}

    src = STATE_DIR / "panels"
    if not src.exists():
        return {"pushed": False, "reason": "no panels directory"}

    n = 0
    for p in src.glob("*.json"):
        if _upload(bucket, p, PREFIX_PANELS + p.name):
            n += 1
    return {"pushed": n > 0, "objects": n}


def push_config() -> dict[str, Any]:
    """Push the model rate table the deployed Cost view prices against."""
    try:
        bucket = _client().bucket(BUCKET)
    except Exception as exc:                        # noqa: BLE001 — boundary
        return {"pushed": False, "reason": str(exc)[:160]}

    p = STATE_DIR / "model_rates.json"
    if not p.exists():
        return {"pushed": False, "reason": "no model_rates.json"}
    return {"pushed": bool(_upload(bucket, p, "config/model_rates.json"))}


def push_all(run_id: str, summary: dict[str, Any]) -> dict[str, Any]:
    run = push_run(run_id, summary)
    panels = push_panels()
    config = push_config()
    # Every finished run also backs up what the system has learned.
    state = push_state()
    return {"run": run, "panels": panels, "config": config, "state": state}


# --------------------------------------------------------------------------
# Brain and learning state: what the system has learned, backed up and
# restorable on any machine.
#
# Everything above is for the dashboard to read. This is different: it is
# the state a restarted container or a second laptop needs to carry on where
# the last run left off — the brand brain of each tenant, the founder's
# decisions, the Coach's rules, the approved posters and clips, and the
# rotations that keep consecutive posts different. Without it a fresh
# container starts with no brain and no memory, and a laptop's disk is the
# only copy. One writer at a time is assumed (the pipeline runs in one
# place); a push overwrites, a pull fills what is missing locally.
# --------------------------------------------------------------------------

PREFIX_STATE = "state/"

STATE_FILES = (
    "pipeline/state/feedback.jsonl",
    "pipeline/state/coach_state.json",
    "pipeline/state/recent_layouts.json",
    "pipeline/state/recent_motion_styles.json",
    "pipeline/state/docs_watch.json",
    "pipeline/brain/knowledge/creative-rules.md",
    "pipeline/brain/knowledge/poster-taste.md",
    "pipeline/brain/knowledge/learned-rules.json",
    "pipeline/brain/knowledge/learned-rules.md",
    "pipeline/state/scheduler_state.json",
    # The gap chosen on the dashboard is written only by --set-interval.
    # A tick must not upload its own copy: that put the old gap back over
    # the one the founder just picked.
    # research_latest.json is not here on purpose. The scout writes it and
    # uploads that file itself. A tick or a meme run that uploaded the copy
    # baked into the image put yesterday's headlines back over a fresh scrape.
    "pipeline/state/telegram_pending_post.json",
    "pipeline/state/telegram_pending_revise.json",
    # What has already been seen and sent. Without these a cloud run starts
    # from the image's old copy and repeats news and X posts already sent.
    "pipeline/state/x_seen.json",
    "pipeline/state/x_context_cursor.json",
    "pipeline/state/telegram_sent_news.json",
    "pipeline/state/research_seen.json",
)
STATE_DIRS = (
    "pipeline/brain/visual_exemplars",
    "pipeline/brain/video_exemplars",
    # Every other company's own learning state (tenant_paths.py).
    "pipeline/state/tenants",
    "pipeline/brain/knowledge/tenants",
)


def _brain_snapshot(tenant_dir: Path) -> Optional[Path]:
    """A consistent SQLite copy of a tenant's brain, for upload.

    On Postgres the tenant is exported to a SQLite file of the same schema,
    so the bucket holds one portable format whichever backend wrote it."""
    import sqlite3
    import tempfile
    from pipeline.brand_brain import store as S
    if S.in_fallback():
        # The SQLite files are a stale stand-in for an unreachable Postgres:
        # uploading them would replace the bucket's copy of the real brain.
        return None
    if S.backend() == "pg":
        if tenant_dir.name not in S.tenants():
            return None
        from pipeline.brand_brain.pg import export
        return export(tenant_dir.name, Path(tempfile.mkdtemp()) / "brain.db")
    db = tenant_dir / "brain.db"
    if not db.exists():
        return None
    out = Path(tempfile.mkdtemp()) / "brain.db"
    src = sqlite3.connect(str(db))
    dst = sqlite3.connect(str(out))
    try:
        src.backup(dst)
    finally:
        src.close()
        dst.close()
    return out


def _state_jobs() -> list[tuple[Path, str]]:
    jobs: list[tuple[Path, str]] = []
    for rel in STATE_FILES:
        p = REPO_ROOT / rel
        if p.exists():
            jobs.append((p, PREFIX_STATE + rel))
    for rel in STATE_DIRS:
        # tenants/<id>/... are a level deeper: walked whole.
        walk = (REPO_ROOT / rel).rglob("*") if rel.endswith("/tenants") else (REPO_ROOT / rel).glob("*")
        for p in sorted(walk):
            if p.is_file() and not p.name.endswith((".lock", ".tmp", ".bak")):
                jobs.append((p, PREFIX_STATE + p.relative_to(REPO_ROOT).as_posix()))
    tenants = REPO_ROOT / "pipeline" / "brain" / "tenants"
    from pipeline.brand_brain import store as S
    names = {p.name for p in tenants.glob("*") if p.is_dir()} if tenants.exists() else set()
    if S.backend() == "pg":
        names |= set(S.tenants())
    for td in (tenants / n for n in sorted(names)):
        snap = _brain_snapshot(td)
        if snap:
            jobs.append((snap, PREFIX_STATE + "pipeline/brain/tenants/" + td.name + "/brain.db"))
        for sub in ("images", "stills", "website"):
            for p in sorted((td / sub).glob("*")):
                if p.is_file():
                    jobs.append((p, PREFIX_STATE + p.relative_to(REPO_ROOT).as_posix()))
    return jobs


def _md5_b64(p: Path) -> str:
    import base64
    import hashlib
    h = hashlib.md5()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return base64.b64encode(h.digest()).decode()


def _newer_than(local: Path, remote_updated) -> bool:
    """True when the local file was written after the bucket's copy."""
    if remote_updated is None:
        return True
    try:
        return local.stat().st_mtime > remote_updated.timestamp() + 1
    except OSError:
        return False


def push_state() -> dict[str, Any]:
    """Back up brain and learning state. A file is sent only when it differs
    from the bucket's copy AND was written after it: an older copy — one
    baked into the image, or a laptop that was asleep — never replaces a
    newer one. Each upload is conditional on the generation just listed, so
    a write that lands in between wins. Never raises."""
    try:
        bucket = _client().bucket(BUCKET)
        remote = {b.name: (b.md5_hash, b.updated, b.generation)
                  for b in bucket.list_blobs(prefix=PREFIX_STATE)}
    except Exception as exc:                        # noqa: BLE001 — boundary
        return {"pushed": False, "reason": "no GCS client: " + str(exc)[:160]}
    jobs, older = [], 0
    for p, k in _state_jobs():
        md5, updated, gen = remote.get(k, (None, None, 0))
        if md5 == _md5_b64(p):
            continue
        if not _newer_than(p, updated):
            older += 1
            continue
        jobs.append((p, k, gen))
    if not jobs:
        return {"pushed": True, "objects": 0, "unchanged": len(remote), "kept_newer_remote": older,
                "bucket": BUCKET}
    with ThreadPoolExecutor(max_workers=6) as pool:
        done = list(pool.map(lambda j: _upload(bucket, j[0], j[1], if_generation=j[2]), jobs))
    ok = [d for d in done if d]
    return {"pushed": bool(ok), "objects": len(ok), "failed_or_raced": len(done) - len(ok),
            "kept_newer_remote": older, "bucket": BUCKET}


def push_state_files(rels: list[str]) -> int:
    """Upload a few state files (repo-relative); a deleted one is removed
    from the bucket too. Never raises."""
    try:
        bucket = _client().bucket(BUCKET)
    except Exception:                               # noqa: BLE001 — boundary
        return 0
    n = 0
    for rel in rels:
        p = REPO_ROOT / rel
        try:
            if p.exists():
                n += bool(_upload(bucket, p, PREFIX_STATE + rel))
            else:
                blob = bucket.blob(PREFIX_STATE + rel)
                if blob.exists():
                    blob.delete()
                    n += 1
        except Exception:                           # noqa: BLE001 — this file fails alone
            pass
    return n


def pull_state(*, overwrite: Optional[bool] = None) -> dict[str, Any]:
    """Restore brain and learning state from the bucket. On a laptop only
    files missing locally are fetched, so a pull never clobbers newer local
    work. In the cloud (and with `overwrite=True`) the bucket wins: the
    container's own copies were baked into the image at build time and are
    older than anything the bucket holds."""
    if overwrite is None:
        overwrite = in_cloud()
    try:
        bucket = _client().bucket(BUCKET)
        blobs = list(bucket.list_blobs(prefix=PREFIX_STATE))
    except Exception as exc:                        # noqa: BLE001 — boundary
        return {"pulled": False, "reason": "no GCS client: " + str(exc)[:160]}
    n = skipped = 0
    for b in blobs:
        rel = b.name[len(PREFIX_STATE):]
        if not rel or ".." in rel.split("/"):
            continue
        dest = REPO_ROOT / rel
        if dest.exists() and not overwrite:
            skipped += 1
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        try:
            b.download_to_filename(str(dest))
            n += 1
        except Exception:                           # noqa: BLE001 — this file fails alone
            continue
    # On Postgres, a snapshot for a tenant the database does not have yet is
    # imported (a fresh machine); a tenant it has is left alone.
    imported = []
    try:
        from pipeline.brand_brain import store as S
        if S.backend() == "pg":
            from pipeline.brand_brain.pg import migrate_tenant
            have = set(S.tenants())
            for db in sorted((REPO_ROOT / "pipeline" / "brain" / "tenants").glob("*/brain.db")):
                if db.parent.name not in have:
                    migrate_tenant(db.parent.name, db, S.database_url())
                    imported.append(db.parent.name)
    except Exception as exc:                        # noqa: BLE001 — the files are still on disk
        imported.append("failed: " + str(exc)[:120])
    return {"pulled": True, "objects": n, "kept_local": skipped, "bucket": BUCKET,
            "imported_to_postgres": imported}


SCHEDULER_STATE_REL = "pipeline/state/scheduler_state.json"
_LOCKS_HELD: dict[str, str] = {}


def blend_scheduler_records(memory: dict, other: dict) -> dict:
    """Per job, keep the later last_run and the higher run count.

    A tick that started earlier must not put an older clock back over a job
    a later tick already claimed.
    """
    out = {k: v for k, v in memory.items()}
    for name, rec in other.items():
        if not isinstance(rec, dict):
            continue
        cur = out.get(name)
        if not isinstance(cur, dict):
            out[name] = rec
            continue
        if str(rec.get("last_run") or "") > str(cur.get("last_run") or ""):
            cur["last_run"] = rec["last_run"]
        try:
            if int(rec.get("total_runs") or 0) > int(cur.get("total_runs") or 0):
                cur["total_runs"] = int(rec["total_runs"])
        except (TypeError, ValueError):
            pass
        out[name] = cur
    return out


def refresh_interval_overrides() -> None:
    """Replace the local gap file with the bucket copy. The dashboard is the writer."""
    if not in_cloud():
        return
    rel = "pipeline/state/scheduler_intervals.json"
    path = REPO_ROOT / rel
    try:
        blob = _client().bucket(BUCKET).blob(PREFIX_STATE + rel)
        if not blob.exists():
            return
        path.parent.mkdir(parents=True, exist_ok=True)
        blob.download_to_filename(str(path))
    except Exception:                               # noqa: BLE001 — the yaml default stands
        return


def merge_scheduler_state_from_bucket() -> None:
    """Pull a newer scheduler clock from the bucket into the local file. Never raises."""
    if not in_cloud():
        return
    path = REPO_ROOT / SCHEDULER_STATE_REL
    try:
        blob = _client().bucket(BUCKET).blob(PREFIX_STATE + SCHEDULER_STATE_REL)
        if not blob.exists():
            return
        remote = json.loads(blob.download_as_text())
    except Exception:                               # noqa: BLE001 — the local file stands
        return
    if not isinstance(remote, dict):
        return
    from pipeline.ops.atomic import FileLock, read_json, write_json
    try:
        with FileLock(path):
            local = read_json(path, {})
            if not isinstance(local, dict):
                local = {}
            merged = blend_scheduler_records(local, remote)
            if merged != local:
                write_json(path, merged)
    except (OSError, TimeoutError):
        return


def claim_scheduler_job(job_name: str, interval_s: int, *, force: bool = False) -> tuple[bool, str]:
    """Record last_run=now if the job is due.

    On GCP the write uses the object's generation, so two ticks cannot both
    pass. The loser is told the job is not due.
    """
    import json
    from datetime import datetime, timezone

    path = REPO_ROOT / SCHEDULER_STATE_REL
    now = datetime.now(timezone.utc)

    def _too_soon(rec: dict) -> bool:
        if force:
            return False
        last = str(rec.get("last_run") or "")
        if not last:
            return False
        try:
            dt = datetime.fromisoformat(last)
        except ValueError:
            return False
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return (now - dt).total_seconds() < interval_s

    def _stamp(state: dict) -> dict:
        rec = state.get(job_name) if isinstance(state.get(job_name), dict) else {}
        rec = dict(rec)
        rec["job"] = job_name
        rec["last_run"] = now.isoformat()
        state[job_name] = rec
        return state

    if not in_cloud():
        from pipeline.ops.atomic import CorruptState, FileLock, read_json, write_json
        try:
            with FileLock(path):
                state = read_json(path, {}, strict=True)
                if not isinstance(state, dict):
                    state = {}
                rec = state.get(job_name) if isinstance(state.get(job_name), dict) else {}
                if _too_soon(rec):
                    return False, "not due"
                write_json(path, _stamp(state))
        except (CorruptState, TimeoutError) as exc:
            return False, "state unreadable or busy: " + str(exc)[:120]
        return True, "claimed"

    try:
        from google.api_core.exceptions import PreconditionFailed
        blob = _client().bucket(BUCKET).blob(PREFIX_STATE + SCHEDULER_STATE_REL)
        if blob.exists():
            blob.reload()
            state = json.loads(blob.download_as_text())
            generation = blob.generation
        else:
            state = {}
            generation = 0
        if not isinstance(state, dict):
            state = {}
        rec = state.get(job_name) if isinstance(state.get(job_name), dict) else {}
        if _too_soon(rec):
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(state, indent=2), encoding="utf-8")
            return False, "not due"
        payload = json.dumps(_stamp(state), indent=2)
        blob.upload_from_string(payload, content_type="application/json", if_generation_match=generation)
    except PreconditionFailed:
        return False, "another tick already claimed this job"
    except Exception as exc:                        # noqa: BLE001 — do not start a post we could not record
        return False, "clock claim failed: " + str(exc)[:160]
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(payload, encoding="utf-8")
    except OSError:
        pass
    return True, "claimed"


CLOCK_LEASE = PREFIX_STATE + "clock_lease.json"


def renew_clock_lease(ttl_s: int = 600) -> bool:
    """The laptop says, in the bucket, that it is running the schedule now.
    Renewed every couple of minutes while it does; a cloud tick that finds a
    fresh lease runs nothing, so a job never runs in both places even if the
    GCP tick is switched on while the laptop is still going. Never raises."""
    if in_cloud():
        return False
    import socket
    import time as _t
    try:
        body = json.dumps({"owner": "laptop", "host": socket.gethostname(), "pid": os.getpid(),
                           "until": _t.time() + ttl_s})
        _client().bucket(BUCKET).blob(CLOCK_LEASE).upload_from_string(body, content_type="application/json")
        return True
    except Exception:                               # noqa: BLE001 — no sign-in: the lease lapses
        return False


def release_clock_lease() -> None:
    try:
        _client().bucket(BUCKET).blob(CLOCK_LEASE).delete()
    except Exception:                               # noqa: BLE001 — it lapses by itself
        pass


def laptop_holds_clock() -> Optional[dict]:
    """The laptop's lease when it is still fresh, else None."""
    import time as _t
    try:
        lease = json.loads(_client().bucket(BUCKET).blob(CLOCK_LEASE).download_as_text())
    except Exception:                               # noqa: BLE001 — none, or unreadable
        return None
    if isinstance(lease, dict) and lease.get("owner") == "laptop" and float(lease.get("until", 0)) > _t.time():
        return lease
    return None


def cloud_lock_acquire(blob_name: str, stale_s: int) -> bool:
    """Take a bucket lock. Only the holder can release it. Fail closed."""
    if not in_cloud():
        return True
    import uuid
    from datetime import datetime, timezone
    from google.api_core.exceptions import PreconditionFailed

    token = uuid.uuid4().hex
    try:
        blob = _client().bucket(BUCKET).blob(blob_name)
        try:
            blob.upload_from_string(token, content_type="text/plain", if_generation_match=0)
            _LOCKS_HELD[blob_name] = token
            return True
        except PreconditionFailed:
            pass
        blob.reload()
        updated = blob.updated
        if updated is None:
            return False
        if updated.tzinfo is None:
            updated = updated.replace(tzinfo=timezone.utc)
        if (datetime.now(timezone.utc) - updated).total_seconds() < stale_s:
            return False
        blob.upload_from_string(token, content_type="text/plain", if_generation_match=blob.generation)
        _LOCKS_HELD[blob_name] = token
        return True
    except PreconditionFailed:
        return False
    except Exception:
        return False


def cloud_lock_release(blob_name: str) -> None:
    """Delete the lock only when it still holds the token this process wrote."""
    token = _LOCKS_HELD.pop(blob_name, None)
    if not token or not in_cloud():
        return
    try:
        from google.api_core.exceptions import PreconditionFailed
        blob = _client().bucket(BUCKET).blob(blob_name)
        blob.reload()
        if blob.download_as_text().strip() != token:
            return
        blob.delete(if_generation_match=blob.generation)
    except PreconditionFailed:
        return
    except Exception:
        return


def _cli() -> None:
    import json
    import sys

    if sys.argv[1:2] == ["push-state"]:
        print(json.dumps(push_state(), indent=2))
        return
    if sys.argv[1:2] == ["pull-state"]:
        print(json.dumps(pull_state(overwrite=True if "--overwrite" in sys.argv else None), indent=2))
        return
    rid = sys.argv[1] if len(sys.argv) > 1 else sorted(
        d.name for d in RUNS_DIR.iterdir()
        if d.is_dir() and d.name.startswith("GTM-"))[-1]
    s = json.loads((RUNS_DIR / rid / "summary.json").read_text(encoding="utf-8"))
    print(json.dumps(push_all(rid, s), indent=2))


if __name__ == "__main__":
    _cli()
