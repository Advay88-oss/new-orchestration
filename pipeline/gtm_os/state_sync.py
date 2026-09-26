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

import mimetypes
import os
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
             "analysis.json", "feedback.json")


def _client():
    from google.cloud import storage
    return storage.Client(project=PROJECT)


def available() -> bool:
    try:
        _client().bucket(BUCKET).exists()
        return True
    except Exception:                               # noqa: BLE001 — boundary
        return False


def _upload(bucket, local: Path, key: str) -> Optional[str]:
    try:
        blob = bucket.blob(key)
        ctype = mimetypes.guess_type(local.name)[0]
        blob.upload_from_filename(str(local), content_type=ctype)
        return key
    except Exception:                               # noqa: BLE001 — boundary
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
    "pipeline/brain/knowledge/learned-rules.json",
    "pipeline/brain/knowledge/learned-rules.md",
)
STATE_DIRS = (
    "pipeline/brain/visual_exemplars",
    "pipeline/brain/video_exemplars",
)


def _brain_snapshot(tenant_dir: Path) -> Optional[Path]:
    """A consistent copy of a live SQLite brain (WAL-safe), for upload."""
    import sqlite3
    import tempfile
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
        for p in sorted((REPO_ROOT / rel).glob("*")):
            if p.is_file():
                jobs.append((p, PREFIX_STATE + p.relative_to(REPO_ROOT).as_posix()))
    tenants = REPO_ROOT / "pipeline" / "brain" / "tenants"
    for td in sorted(tenants.glob("*")) if tenants.exists() else []:
        snap = _brain_snapshot(td)
        if snap:
            jobs.append((snap, PREFIX_STATE + "pipeline/brain/tenants/" + td.name + "/brain.db"))
        for sub in ("images", "stills"):
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


def push_state() -> dict[str, Any]:
    """Back up brain and learning state; only files that changed are sent.
    Never raises."""
    try:
        bucket = _client().bucket(BUCKET)
        remote = {b.name: b.md5_hash for b in bucket.list_blobs(prefix=PREFIX_STATE)}
    except Exception as exc:                        # noqa: BLE001 — boundary
        return {"pushed": False, "reason": "no GCS client: " + str(exc)[:160]}
    jobs = [(p, k) for p, k in _state_jobs() if remote.get(k) != _md5_b64(p)]
    if not jobs:
        return {"pushed": True, "objects": 0, "unchanged": len(remote), "bucket": BUCKET}
    with ThreadPoolExecutor(max_workers=6) as pool:
        done = list(pool.map(lambda j: _upload(bucket, j[0], j[1]), jobs))
    ok = [d for d in done if d]
    return {"pushed": bool(ok), "objects": len(ok), "failed": len(done) - len(ok), "bucket": BUCKET}


def pull_state(*, overwrite: bool = False) -> dict[str, Any]:
    """Restore brain and learning state from the bucket. By default only
    files missing locally are fetched, so a pull never clobbers newer local
    work; `overwrite=True` makes the local copy match the bucket."""
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
    return {"pulled": True, "objects": n, "kept_local": skipped, "bucket": BUCKET}


def _cli() -> None:
    import json
    import sys

    if sys.argv[1:2] == ["push-state"]:
        print(json.dumps(push_state(), indent=2))
        return
    if sys.argv[1:2] == ["pull-state"]:
        print(json.dumps(pull_state(overwrite="--overwrite" in sys.argv), indent=2))
        return
    rid = sys.argv[1] if len(sys.argv) > 1 else sorted(
        d.name for d in RUNS_DIR.iterdir()
        if d.is_dir() and d.name.startswith("GTM-"))[-1]
    s = json.loads((RUNS_DIR / rid / "summary.json").read_text(encoding="utf-8"))
    print(json.dumps(push_all(rid, s), indent=2))


if __name__ == "__main__":
    _cli()
