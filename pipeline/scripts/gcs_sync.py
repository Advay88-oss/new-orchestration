#!/usr/bin/env python3
"""GCS sync for the hybrid pipeline (google-cloud-storage lib, ADC auth).

The scraping bridge (OpenCLI Chrome) is local-only, so the pipeline RUNS locally
but its state is mirrored to a GCS bucket the Cloud Run dashboard reads. Layout:

    gs://<bucket>/runs/<run_id>.meta.json      run summaries (dashboard list)
    gs://<bucket>/drafts/<run_id>.json         winning draft copy
    gs://<bucket>/cards/<run_id>.png|.gif      rendered visual
    gs://<bucket>/requests/<req_id>.json       run requests FROM the dashboard
    gs://<bucket>/requests/done/<req_id>.json  claimed/processed requests

Auth = Application Default Credentials (gcloud auth application-default login).

    python gcs_sync.py push  --run-id vanna-...
    python gcs_sync.py runs
    python gcs_sync.py requests
    python gcs_sync.py claim --req-id <id> --out d/
"""
from __future__ import annotations
import argparse, json, os, sys
from pathlib import Path
from google.cloud import storage

REPO = Path(__file__).resolve().parents[2]
STATE = REPO / "pipeline" / "state"
BUCKET = os.environ.get("VANNA_GCS_BUCKET", "gs://vanna-pipeline-state-506009").replace("gs://", "")
PROJECT = os.environ.get("VERTEX_PROJECT", "video-506009")

_client = None
def bucket():
    global _client
    if _client is None:
        _client = storage.Client(project=PROJECT)
    return _client.bucket(BUCKET)


def push_run(run_id: str) -> dict:
    b = bucket()
    out = {"run_id": run_id, "uploaded": []}
    meta = STATE / "runs" / f"{run_id}.meta.json"
    if meta.exists():
        b.blob(f"runs/{run_id}.meta.json").upload_from_filename(str(meta), content_type="application/json")
        out["uploaded"].append("meta")
    draft = STATE / "drafts" / "temp_winner.json"
    if draft.exists():
        b.blob(f"drafts/{run_id}.json").upload_from_filename(str(draft), content_type="application/json")
        out["uploaded"].append("draft")
    for card in (STATE / "temp_rendered.png", STATE / "temp_animated.gif"):
        if card.exists():
            ct = "image/png" if card.suffix == ".png" else "image/gif"
            b.blob(f"cards/{run_id}{card.suffix}").upload_from_filename(str(card), content_type=ct)
            out["uploaded"].append(f"card{card.suffix}")
    print(json.dumps(out))
    return out


def list_runs() -> list[dict]:
    b = bucket()
    metas = []
    for blob in b.list_blobs(prefix="runs/"):
        if blob.name.endswith(".meta.json"):
            try:
                metas.append(json.loads(blob.download_as_text()))
            except Exception:
                pass
    metas.sort(key=lambda m: m.get("started", 0), reverse=True)
    print(json.dumps({"runs": metas}, ensure_ascii=False))
    return metas


def list_requests() -> list[dict]:
    b = bucket()
    reqs = []
    for blob in b.list_blobs(prefix="requests/"):
        if "/done/" in blob.name or not blob.name.endswith(".json"):
            continue
        try:
            m = json.loads(blob.download_as_text())
            m["_blob"] = blob.name
            reqs.append(m)
        except Exception:
            pass
    print(json.dumps({"requests": reqs}, ensure_ascii=False))
    return reqs


def claim(req_id: str, out_dir: str) -> dict:
    b = bucket()
    src = b.blob(f"requests/{req_id}.json")
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    local = Path(out_dir) / f"{req_id}.json"
    res = {"claimed": False, "req_id": req_id, "local": None}
    try:
        src.download_to_filename(str(local))
        # move to done/ so no other runner takes it
        b.copy_blob(src, b, f"requests/done/{req_id}.json")
        src.delete()
        res.update(claimed=True, local=str(local))
    except Exception as e:
        res["error"] = str(e)[:200]
    print(json.dumps(res))
    return res


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("push"); p.add_argument("--run-id", required=True)
    sub.add_parser("runs")
    sub.add_parser("requests")
    c = sub.add_parser("claim"); c.add_argument("--req-id", required=True); c.add_argument("--out", default=str(STATE / "requests"))
    a = ap.parse_args()
    if a.cmd == "push": push_run(a.run_id)
    elif a.cmd == "runs": list_runs()
    elif a.cmd == "requests": list_requests()
    elif a.cmd == "claim": claim(a.req_id, a.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
