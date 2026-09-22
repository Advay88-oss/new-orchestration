#!/usr/bin/env python3
"""Generates a subtle, minimalist, luxury-institutional Vanna Introduction Video.

Removes harsh god-rays, chaotic plasma, and blinding spotlights.
Emphasizes matte obsidian surfaces, gentle breathing luminescence,
muted edge bevel reflections, and vast, calm negative space.
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

from pipeline.scripts.veo_broll import _vertex_token, _find_video, _write_video

PROJECT = "vanna-mcp"
LOCATION = "us-central1"
MODEL = "veo-3.1-generate-001"
LOGO_IMG_PATH = STATE_DIR / "vanna_logo_hero_canvas.png"
OUT_VIDEO = STATE_DIR / "vanna_subtle_logo_intro.mp4"

if not LOGO_IMG_PATH.exists():
    print(f"❌ Logo image not found: {LOGO_IMG_PATH}")
    sys.exit(1)

logo_b64 = base64.b64encode(LOGO_IMG_PATH.read_bytes()).decode("utf-8")

# Refined, restrained prompt without aggressive lighting
prompt = (
    "Minimalist luxury product motion design video. The official Vanna geometric logo glyph and VANNA wordmark "
    "are centered in an expansive, tranquil obsidian void (#07020D). Extremely subtle, soft, restrained studio lighting. "
    "The folded geometric ribbon glyph has a quiet, gentle breathing internal glow of soft coral and lavender, "
    "with delicate, matte chamfered edge highlights. The clean white VANNA typography remains razor-sharp and steady. "
    "The camera executes a very slow, smooth, elegant cinematic pull-back across a clean, dark satin floor with faint, "
    "muted reflections. Muted, soft ambient violet (#471485) and fuchsia (#5E0D46) tones stay gracefully in the far background. "
    "Tactile 35mm film grain, supreme visual calm, quiet institutional confidence, zero aggressive spotlights, "
    "zero blinding god-rays, zero smoke clouds, zero particle clutter. Photorealistic architectural polish."
)

print(f"▶ Initiating Veo 3.1 Subtle Intro Generation...")
print(f"   Project / Model: {PROJECT} / {MODEL}")
print(f"   Prompt:          {prompt[:110]}...")

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
                "bytesBase64Encoded": logo_b64,
                "mimeType": "image/png"
            }
        }
    ],
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
            
        print(f"🎉 Veo 3.1 subtle video synthesis complete in {elapsed}s! Extracting MP4 bytes...")
        b64, uri = _find_video(st.get("response", st))
        if _write_video(b64, uri, OUT_VIDEO, None):
            print(f"✅ Subtle Vanna Logo Video saved: {OUT_VIDEO.name} ({OUT_VIDEO.stat().st_size:,} bytes)")
            sys.exit(0)
        else:
            print(f"❌ Could not extract video: {str(st)[:400]}")
            sys.exit(1)
            
    print(f"   ...rendering ({elapsed}s elapsed)")

print("❌ Timed out.")
sys.exit(1)
