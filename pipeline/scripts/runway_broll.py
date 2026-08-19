#!/usr/bin/env python3
"""Generate AI B-roll via Runway (Gen-4), gated on RUNWAY_API_KEY.

The crypto-video-style split: Runway/Veo make abstract environments & motion
backgrounds; every readable element (text, logo, stat) is still rendered by
render_video and composited ON TOP. This module fetches the B-roll; compositing
is an ffmpeg overlay (see compose_over_broll).

You provide the key — I never handle it:  set RUNWAY_API_KEY in the environment
(or ~/.config/watch/.env style). Get one at dev.runwayml.com.

    RUNWAY_API_KEY=... python runway_broll.py --prompt "abstract violet liquid gradient, slow, premium" --out broll.mp4
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
from pathlib import Path

API = "https://api.dev.runwayml.com/v1"
VERSION = "2024-11-06"  # Runway API version header


def _load_dotenv() -> None:
    """Load RUNWAY_API_KEY (and friends) from a gitignored .env WITHOUT any
    dependency, so the key lives in a file the user edits — never pasted in chat
    or committed. Checks pipeline/.env then repo/.env; existing env wins."""
    root = Path(__file__).resolve().parents[2]
    for envf in (root / "pipeline" / ".env", root / ".env"):
        if not envf.exists():
            continue
        try:
            for line in envf.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                k, v = k.strip(), v.strip().strip('"').strip("'")
                if k and k not in os.environ:
                    os.environ[k] = v
        except Exception:
            pass


def _key() -> str | None:
    _load_dotenv()
    return os.environ.get("RUNWAY_API_KEY") or None


def _post(path: str, body: dict) -> dict:
    req = urllib.request.Request(
        API + path, data=json.dumps(body).encode(),
        headers={"Authorization": f"Bearer {_key()}", "X-Runway-Version": VERSION,
                 "Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read())


def _get(path: str) -> dict:
    req = urllib.request.Request(
        API + path, headers={"Authorization": f"Bearer {_key()}", "X-Runway-Version": VERSION})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read())


def generate_broll(prompt: str, out: Path, start_image: Path | None = None,
                   ratio: str = "960:960", duration: int = 5, model: str = "gen4_turbo") -> Path | None:
    """image_to_video (Runway needs a prompt image). If none is given, a flat brand
    frame is used as the seed so the motion stays on-palette."""
    if not _key():
        print(json.dumps({"ok": False, "reason": "RUNWAY_API_KEY not set — set it to enable AI b-roll",
                          "where": "environment variable RUNWAY_API_KEY"}))
        return None
    # seed image → data URI
    if start_image and Path(start_image).exists():
        img_bytes = Path(start_image).read_bytes()
    else:
        # generate a flat brand seed frame with render_video's palette
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        import render_video as rv
        from PIL import Image
        seed = Path(out).with_suffix(".seed.png")
        Image.new("RGB", (1080, 1080), tuple(int(str(rv.rv.BACKGROUND).lstrip('#')[i:i+2], 16) for i in (0, 2, 4))).save(seed)
        img_bytes = seed.read_bytes()
    data_uri = "data:image/png;base64," + base64.b64encode(img_bytes).decode()

    task = _post("/image_to_video", {"model": model, "promptImage": data_uri,
                                     "promptText": prompt, "ratio": ratio, "duration": duration})
    tid = task.get("id")
    print(f"Runway task {tid} submitted; polling…")
    for _ in range(60):
        time.sleep(5)
        st = _get(f"/tasks/{tid}")
        status = st.get("status")
        if status == "SUCCEEDED":
            url = (st.get("output") or [None])[0]
            if not url:
                print("no output url"); return None
            out = Path(out); out.parent.mkdir(parents=True, exist_ok=True)
            urllib.request.urlretrieve(url, str(out))
            print(json.dumps({"ok": True, "out": str(out)}))
            return out
        if status in ("FAILED", "CANCELLED"):
            print(json.dumps({"ok": False, "status": status, "detail": st.get("failure", "")}))
            return None
    print("timed out waiting for Runway"); return None


def compose_over_broll(broll: Path, overlay_video: Path, out: Path) -> Path:
    """Composite render_video's frames over the b-roll. render_video draws on an
    opaque ground, so here we blend it at reduced opacity to let motion show; for a
    true alpha overlay, render text-only frames (transparent) and overlay=format=auto."""
    ff = shutil.which("ffmpeg") or "ffmpeg"
    cmd = [ff, "-y", "-i", str(broll), "-i", str(overlay_video),
           "-filter_complex", "[1:v]format=yuva420p,colorchannelmixer=aa=0.92[o];[0:v][o]overlay=shortest=1[v]",
           "-map", "[v]", "-c:v", "libx264", "-pix_fmt", "yuv420p", str(out)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"composite failed: {r.stderr[-300:]}")
    return Path(out)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--prompt", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--start-image", default=None)
    ap.add_argument("--duration", type=int, default=5)
    a = ap.parse_args()
    r = generate_broll(a.prompt, Path(a.out), Path(a.start_image) if a.start_image else None, duration=a.duration)
    return 0 if r else 2


if __name__ == "__main__":
    sys.exit(main())
