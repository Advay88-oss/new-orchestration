#!/usr/bin/env python3
"""Calls Google Veo 3.1 (veo-3.1-generate-001) on Vertex AI Model Garden.

Project: vanna-mcp
Location: us-central1
Model: veo-3.1-generate-001
"""

from __future__ import annotations

import base64
import json
import os
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

STATE_DIR = REPO_ROOT / "pipeline" / "state"
STATE_DIR.mkdir(parents=True, exist_ok=True)

from pipeline.scripts.veo_broll import _vertex_token, _find_video, _write_video

PROJECT = "vanna-mcp"
LOCATION = "us-central1"
MODEL = "veo-3.1-generate-001"
OUT_VIDEO = STATE_DIR / "vanna_intro_veo31.mp4"

# Load Art Director's Prompt
art_spec = json.loads((STATE_DIR / "VANNA_INTRO_ART_DIRECTION.json").read_text(encoding="utf-8"))
prompt = art_spec["hero_veo_scene"]["veo_31_prompt"]

print(f"▶ Initiating Veo 3.1 Video Generation...")
print(f"   Project:  {PROJECT}")
print(f"   Location: {LOCATION}")
print(f"   Model:    {MODEL}")
print(f"   Prompt:   {prompt[:120]}...")

token = _vertex_token()
if not token:
    print("❌ No Vertex token available.")
    sys.exit(1)

host = "https://aiplatform.googleapis.com" if LOCATION == "global" else f"https://{LOCATION}-aiplatform.googleapis.com"
base = f"{host}/v1/projects/{PROJECT}/locations/{LOCATION}/publishers/google/models/{MODEL}"
headers = {
    "Authorization": f"Bearer {token}",
    "x-goog-user-project": PROJECT,
    "Content-Type": "application/json"
}

body = {
    "instances": [{"prompt": prompt}],
    "parameters": {
        "aspectRatio": "16:9",
        "sampleCount": 1,
        "durationSeconds": 8
    }
}

req = urllib.request.Request(f"{base}:predictLongRunning", data=json.dumps(body).encode(), headers=headers, method="POST")
try:
    op = json.loads(urllib.request.urlopen(req, timeout=90).read())
except urllib.error.HTTPError as e:
    print(f"❌ Submission Error HTTP {e.code}: {e.read().decode('utf-8', 'replace')}")
    sys.exit(1)

op_name = op.get("name")
print(f"✅ Operation submitted successfully: {op_name}")
print("⏳ Polling Vertex AI for completion (typical duration: 45–90s)...")

start_time = time.time()
for i in range(90):
    time.sleep(8)
    elapsed = int(time.time() - start_time)
    
    poll_body = {"operationName": op_name}
    poll_req = urllib.request.Request(f"{base}:fetchPredictOperation", data=json.dumps(poll_body).encode(), headers=headers, method="POST")
    try:
        st = json.loads(urllib.request.urlopen(poll_req, timeout=90).read())
    except urllib.error.HTTPError as e:
        print(f"   Poll warning HTTP {e.code}: {e.read().decode('utf-8', 'replace')[:200]}")
        continue

    if st.get("done"):
        if "error" in st:
            print(f"❌ Operation error: {st['error']}")
            sys.exit(1)
            
        print(f"🎉 Veo 3.1 generation finished in {elapsed}s! Extracting video bytes...")
        b64, uri = _find_video(st.get("response", st))
        if _write_video(b64, uri, OUT_VIDEO, None):
            print(f"✅ Master Video saved: {OUT_VIDEO.name} ({OUT_VIDEO.stat().st_size:,} bytes)")
            sys.exit(0)
        else:
            print(f"❌ Could not write video from response: {str(st)[:400]}")
            sys.exit(1)
            
    print(f"   ...generating in progress ({elapsed}s elapsed)")

print("❌ Timed out waiting for Veo operation.")
sys.exit(1)
