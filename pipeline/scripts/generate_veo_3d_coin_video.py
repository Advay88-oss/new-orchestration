#!/usr/bin/env python3
"""Generates a 3D rotating Vanna 10X physical coin video using Google Veo 3.1 Image-to-Video.
Conditioned on: D:/vanna-remotion/public/vanna-coin.png
Outputs:
- D:/vanna-remotion/public/veo-coin-rotate.mp4
- D:/new orchestration/pipeline/state/veo_vanna_coin_rotate.mp4
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

REPO_ROOT = Path("D:/new orchestration")
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

STATE_DIR = REPO_ROOT / "pipeline" / "state"
PUBLIC_DIR = Path("D:/vanna-remotion/public")

from pipeline.scripts.veo_broll import _vertex_token, _find_video, _write_video

PROJECT = "vanna-mcp"
LOCATION = "us-central1"
MODEL = "veo-3.1-generate-001"
COIN_IMG = PUBLIC_DIR / "vanna-coin.png"
OUT_VIDEO_STATE = STATE_DIR / "veo_vanna_coin_rotate.mp4"
OUT_VIDEO_PUBLIC = PUBLIC_DIR / "veo-coin-rotate.mp4"

if not COIN_IMG.exists():
    print(f"❌ Input coin image not found: {COIN_IMG}")
    sys.exit(1)

coin_b64 = base64.b64encode(COIN_IMG.read_bytes()).decode("utf-8")

prompt = (
    "A photorealistic, tactile 3D physical copper and rose-gold coin with debossed 10X glyph slowly rotates in three-quarter perspective, "
    "floating weightlessly in the center against a deep obsidian black background. "
    "Striking electric royal violet (#471485) and fuchsia-magenta (#5E0D46) rim lighting gleams along the beveled edges as the coin turns smoothly, "
    "revealing its fine circular brushed metallic grain and specular light glints. "
    "Ultra-smooth motion, cinematic studio macro product shot, shallow depth of field."
)

print(f"▶ Initiating Veo 3.1 Image-to-Video generation for 3D Vanna coin...")
print(f"   Conditioning Image: {COIN_IMG.name} ({COIN_IMG.stat().st_size:,} bytes)")
print(f"   Project / Model:    {PROJECT} / {MODEL}")

token = _vertex_token()
if not token:
    print("❌ No Vertex token available.")
    sys.exit(1)

host = f"https://{LOCATION}-aiplatform.googleapis.com"
base = f"{host}/v1/projects/{PROJECT}/locations/{LOCATION}/publishers/google/models/{MODEL}"
headers = {
    "Authorization": f"Bearer {token}",
    "x-goog-user-project": PROJECT,
    "Content-Type": "application/json"
}

body = {
    "instances": [
        {
            "prompt": prompt,
            "image": {
                "bytesBase64Encoded": coin_b64,
                "mimeType": "image/png"
            }
        }
    ],
    "parameters": {
        "aspectRatio": "16:9",
        "sampleCount": 1,
        "durationSeconds": 6
    }
}

req = urllib.request.Request(f"{base}:predictLongRunning", data=json.dumps(body).encode(), headers=headers, method="POST")
try:
    op = json.loads(urllib.request.urlopen(req, timeout=90).read())
except urllib.error.HTTPError as e:
    print(f"❌ Submission Error HTTP {e.code}: {e.read().decode('utf-8', 'replace')}")
    sys.exit(1)

op_name = op.get("name")
print(f"✅ Operation submitted: {op_name}")
print("⏳ Polling Vertex AI for video rendering (45–90s)...")

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
            
        print(f"🎉 Veo 3.1 video synthesis complete in {elapsed}s! Extracting MP4 bytes...")
        b64, uri = _find_video(st.get("response", st))
        if _write_video(b64, uri, OUT_VIDEO_STATE, None):
            print(f"✅ Saved to state: {OUT_VIDEO_STATE.name} ({OUT_VIDEO_STATE.stat().st_size:,} bytes)")
            # Copy to public
            OUT_VIDEO_PUBLIC.write_bytes(OUT_VIDEO_STATE.read_bytes())
            print(f"✅ Saved to public: {OUT_VIDEO_PUBLIC.name}")
            sys.exit(0)
        else:
            print(f"❌ Could not extract video: {str(st)[:400]}")
            sys.exit(1)
            
    print(f"   ...rendering ({elapsed}s elapsed)")

print("❌ Timed out.")
sys.exit(1)
