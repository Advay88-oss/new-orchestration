#!/usr/bin/env python3
"""Generate B-roll via Google Veo — Vertex AI (default, uses project credits) or
AI Studio (Gemini API key).

Two backends:
  --backend vertex   (default) Veo on Vertex AI. Auth = Application Default
                     Credentials (`gcloud auth application-default login`), billed
                     to the project's Vertex credits — no free-tier 429. Needs the
                     x-goog-user-project quota header (handled here).
  --backend aistudio Veo via generativelanguage.googleapis.com, key from
                     VEO_API_KEY / GEMINI_API_KEY in pipeline/.env. Free tier
                     returns 429 RESOURCE_EXHAUSTED — needs a billed key.

Veo is a long-running op: submit -> poll -> download. Video comes back inline as
base64 (default) unless --storage-uri is a gs:// path.

    # Vertex (credits):
    python veo_broll.py --prompt "abstract violet liquid gradient, premium, slow" \
      --out broll.mp4 --model veo-3.0-fast-generate-001 --seconds 8

    # AI Studio (key):
    python veo_broll.py --backend aistudio --prompt "…" --out broll.mp4
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path

AISTUDIO_BASE = "https://generativelanguage.googleapis.com/v1beta"
DEFAULT_PROJECT = "sales-agent-504607"
DEFAULT_LOCATION = "us-central1"


# ── shared ────────────────────────────────────────────────────────────────────
def _load_dotenv() -> None:
    root = Path(__file__).resolve().parents[2]
    for envf in (root / "pipeline" / ".env", root / ".env"):
        if not envf.exists():
            continue
        for line in envf.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                k, v = k.strip(), v.strip().strip('"').strip("'")
                if k and k not in os.environ:
                    os.environ[k] = v


def _req(url: str, body: dict | None = None, headers: dict | None = None, timeout: int = 90) -> dict:
    data = json.dumps(body).encode() if body is not None else None
    h = {"Content-Type": "application/json"}
    if headers:
        h.update(headers)
    req = urllib.request.Request(url, data=data, headers=h,
                                 method="POST" if body is not None else "GET")
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def _find_video(node) -> tuple[str | None, str | None]:
    """Recursively find inline base64 video or a gs://|https uri in a response."""
    if isinstance(node, dict):
        for k, v in node.items():
            if k in ("bytesBase64Encoded", "videoBytes") and isinstance(v, str) and len(v) > 100:
                return v, None
            if k in ("uri", "gcsUri") and isinstance(v, str) and (v.startswith("gs://") or v.startswith("http")):
                return None, v
            b, u = _find_video(v)
            if b or u:
                return b, u
    elif isinstance(node, list):
        for it in node:
            b, u = _find_video(it)
            if b or u:
                return b, u
    return None, None


def _write_video(b64: str | None, uri: str | None, out: Path, key: str | None) -> bool:
    out = Path(out); out.parent.mkdir(parents=True, exist_ok=True)
    if b64:
        out.write_bytes(base64.b64decode(b64))
        return True
    if uri:
        if uri.startswith("gs://"):
            print(json.dumps({"ok": False, "reason": "got gs:// uri; re-run without --storage-uri for inline base64, or download via gsutil", "uri": uri}))
            return False
        dl = uri + (("&" if "?" in uri else "?") + f"key={key}") if (key and "generativelanguage" in uri) else uri
        urllib.request.urlretrieve(dl, str(out))
        return True
    return False


# ── One Veo call for the pipeline, on either backend ─────────────────────────────
def veo_via_apikey() -> bool:
    """GCP sets VANNA_IMAGE_VIA=apikey: the pipeline's service account may not
    call Vertex models, so Veo (like the posters) goes through the Gemini API
    key. The laptop keeps Vertex with the founder's login."""
    return os.environ.get("VANNA_IMAGE_VIA") == "apikey"


def _veo_key() -> str:
    # GEMINI_API_KEY first: it is the billed key (images and Veo both work on
    # it, 2026-09-27); VEO_API_KEY answered 429 quota-exceeded.
    key = os.environ.get("GEMINI_API_KEY") or os.environ.get("VEO_API_KEY") or ""
    if not key:
        try:
            from pipeline.brand_brain.store import _env_file
            key = _env_file("GEMINI_API_KEY") or _env_file("VEO_API_KEY") or ""
        except Exception:                           # noqa: BLE001 — boundary
            key = ""
    return key


def run_veo(model: str, instance: dict, parameters: dict, *, project: str,
            location: str, timeout_s: float, poll_s: float = 15.0) -> tuple[dict, str | None, str]:
    """Submit a Veo job and wait for it. Returns (finished operation, the API
    key to download a generativelanguage URI with or None, transport).

    Vertex: `<loc>-aiplatform` with an OAuth token, polled with
    fetchPredictOperation. API key: generativelanguage, where the model ids end
    in -preview rather than -001, the operation is polled by name, and the
    Vertex-only parameters (sampleCount, generateAudio) are not accepted.
    """
    if veo_via_apikey():
        key = _veo_key()
        if not key:
            raise RuntimeError("VANNA_IMAGE_VIA=apikey but no VEO_API_KEY / GEMINI_API_KEY")
        m = model[:-4] + "-preview" if model.endswith("-001") else model
        params = {k: v for k, v in parameters.items() if k not in ("sampleCount", "generateAudio")}
        h = {"x-goog-api-key": key}
        try:
            op = _req(f"{AISTUDIO_BASE}/models/{m}:predictLongRunning",
                      {"instances": [instance], "parameters": params}, h)
        except urllib.error.HTTPError as e:
            raise RuntimeError(f"Veo submit HTTP {e.code}: " + e.read().decode("utf-8", "replace")[:300]) from e
        name = op.get("name")
        if not name:
            raise RuntimeError("Veo returned no operation: " + json.dumps(op)[:300])
        deadline = time.time() + timeout_s
        while time.time() < deadline:
            time.sleep(poll_s)
            res = _req(f"{AISTUDIO_BASE}/{name}", None, h)
            if res.get("done"):
                return res, key, "gemini-api"
        raise RuntimeError("Veo did not finish within " + str(int(timeout_s)) + "s")

    token = _vertex_token()
    if not token:
        raise RuntimeError("no Vertex token; run `gcloud auth application-default login`")
    base = (f"https://{location}-aiplatform.googleapis.com/v1/projects/{project}"
            f"/locations/{location}/publishers/google/models/{model}")
    h = {"Authorization": "Bearer " + token, "x-goog-user-project": project}
    try:
        op = _req(f"{base}:predictLongRunning", {"instances": [instance], "parameters": parameters}, h)
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"Veo submit HTTP {e.code}: " + e.read().decode("utf-8", "replace")[:300]) from e
    name = op.get("name")
    if not name:
        raise RuntimeError("Veo returned no operation: " + json.dumps(op)[:300])
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        time.sleep(poll_s)
        res = _req(f"{base}:fetchPredictOperation", {"operationName": name}, h)
        if res.get("done"):
            return res, None, "vertex"
    raise RuntimeError("Veo did not finish within " + str(int(timeout_s)) + "s")


# ── Vertex backend (ADC + credits) ─────────────────────────────────────────────
def _vertex_token() -> str | None:
    try:
        import google.auth
        from google.auth.transport.requests import Request as GRequest
        creds, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
        creds.refresh(GRequest())
        if creds.token:
            return creds.token
    except Exception:
        pass
    exe = shutil.which("gcloud") or shutil.which("gcloud.cmd") or "gcloud.cmd"
    try:
        r = subprocess.run([exe, "auth", "application-default", "print-access-token"],
                           capture_output=True, text=True, timeout=60)
        tok = (r.stdout or "").strip()
        return tok or None
    except Exception:
        return None


def generate_vertex(prompt: str, out: Path, model: str, aspect: str, seconds: int,
                    project: str, location: str, storage_uri: str | None) -> Path | None:
    token = _vertex_token()
    if not token:
        print(json.dumps({"ok": False, "reason": "no ADC token — run: gcloud auth application-default login"})); return None
    # the `global` location uses the un-prefixed host; regional uses `<loc>-aiplatform`.
    host = "https://aiplatform.googleapis.com" if location == "global" else f"https://{location}-aiplatform.googleapis.com"
    base = f"{host}/v1/projects/{project}/locations/{location}/publishers/google/models/{model}"
    headers = {"Authorization": f"Bearer {token}", "x-goog-user-project": project}
    params: dict = {"aspectRatio": aspect, "sampleCount": 1}
    if seconds:
        params["durationSeconds"] = seconds
    if storage_uri:
        params["storageUri"] = storage_uri
    body = {"instances": [{"prompt": prompt}], "parameters": params}
    try:
        op = _req(f"{base}:predictLongRunning", body, headers)
    except urllib.error.HTTPError as e:
        print(json.dumps({"ok": False, "http": e.code, "body": e.read().decode("utf-8", "replace")[:700]})); return None
    name = op.get("name")
    if not name:
        print(json.dumps({"ok": False, "resp": str(op)[:400]})); return None
    print(f"Veo(Vertex) op submitted; polling… [{model}, {seconds}s, {aspect}]")
    for i in range(75):
        time.sleep(8)
        try:
            st = _req(f"{base}:fetchPredictOperation", {"operationName": name}, headers)
        except urllib.error.HTTPError as e:
            print(json.dumps({"ok": False, "poll_http": e.code, "body": e.read().decode("utf-8", "replace")[:400]})); return None
        if st.get("done"):
            if "error" in st:
                print(json.dumps({"ok": False, "op_error": st["error"]})); return None
            b64, uri = _find_video(st.get("response", st))
            if _write_video(b64, uri, out, None):
                print(json.dumps({"ok": True, "out": str(out), "bytes": Path(out).stat().st_size, "backend": "vertex"}))
                return Path(out)
            print(json.dumps({"ok": False, "no_video": str(st)[:600]})); return None
        print(f"  …still generating ({(i + 1) * 8}s)")
    print(json.dumps({"ok": False, "reason": "timed out"})); return None


# ── AI Studio backend (key) ─────────────────────────────────────────────────────
def generate_aistudio(prompt: str, out: Path, model: str, aspect: str) -> Path | None:
    _load_dotenv()
    key = os.environ.get("VEO_API_KEY") or os.environ.get("GEMINI_API_KEY")
    if not key:
        print(json.dumps({"ok": False, "reason": "VEO_API_KEY not set in pipeline/.env"})); return None
    try:
        op = _req(f"{AISTUDIO_BASE}/models/{model}:predictLongRunning?key={key}",
                  {"instances": [{"prompt": prompt}], "parameters": {"aspectRatio": aspect}})
    except urllib.error.HTTPError as e:
        print(json.dumps({"ok": False, "http": e.code, "body": e.read().decode("utf-8", "replace")[:600]})); return None
    name = op.get("name")
    if not name:
        print(json.dumps({"ok": False, "resp": str(op)[:400]})); return None
    print(f"Veo(AIStudio) op {name} submitted; polling…")
    for i in range(60):
        time.sleep(8)
        try:
            st = _req(f"{AISTUDIO_BASE}/{name}?key={key}")
        except urllib.error.HTTPError as e:
            print(json.dumps({"ok": False, "poll_http": e.code, "body": e.read().decode("utf-8", "replace")[:400]})); return None
        if st.get("done"):
            if "error" in st:
                print(json.dumps({"ok": False, "op_error": st["error"]})); return None
            b64, uri = _find_video(st.get("response", st))
            if _write_video(b64, uri, out, key):
                print(json.dumps({"ok": True, "out": str(out), "bytes": Path(out).stat().st_size, "backend": "aistudio"}))
                return Path(out)
            print(json.dumps({"ok": False, "no_video": str(st)[:600]})); return None
        print(f"  …still generating ({(i + 1) * 8}s)")
    print(json.dumps({"ok": False, "reason": "timed out"})); return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--prompt", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--backend", choices=["vertex", "aistudio"], default="vertex")
    ap.add_argument("--model", default="veo-3.0-fast-generate-001",
                    help="vertex: veo-3.0-fast-generate-001 / veo-3.0-generate-001 / veo-2.0-generate-001")
    ap.add_argument("--aspect", default="16:9")
    ap.add_argument("--seconds", type=int, default=8)
    ap.add_argument("--project", default=DEFAULT_PROJECT)
    ap.add_argument("--location", default=DEFAULT_LOCATION)
    ap.add_argument("--storage-uri", default=None, help="gs:// prefix to save to GCS instead of inline base64")
    a = ap.parse_args()
    if a.backend == "vertex":
        ok = generate_vertex(a.prompt, Path(a.out), a.model, a.aspect, a.seconds, a.project, a.location, a.storage_uri)
    else:
        ok = generate_aistudio(a.prompt, Path(a.out), a.model, a.aspect)
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())
