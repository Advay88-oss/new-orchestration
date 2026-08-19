#!/usr/bin/env python3
"""Add a music bed to a video (mux + loop/trim + fade-out).

Give it your own royalty-free track with --audio (recommended). With no track it
synthesizes a soft ambient placeholder bed via ffmpeg so the clip isn't silent —
swap in real music before publishing.

    python add_music.py --video clip.mp4 --audio track.mp3 --out clip_music.mp4
    python add_music.py --video clip.mp4 --out clip_music.mp4        # placeholder bed
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path


def _ff() -> str:
    return shutil.which("ffmpeg") or "ffmpeg"


def _probe_dur(path: Path) -> float:
    ffprobe = shutil.which("ffprobe") or "ffprobe"
    r = subprocess.run([ffprobe, "-v", "error", "-show_entries", "format=duration",
                        "-of", "default=nw=1:nk=1", str(path)], capture_output=True, text=True)
    try:
        return float(r.stdout.strip())
    except Exception:
        return 10.0


def add_music(video: Path, out: Path, audio: Path | None, gain: float = 0.6) -> Path:
    dur = _probe_dur(video)
    fout = max(0.0, dur - 1.2)
    out = Path(out); out.parent.mkdir(parents=True, exist_ok=True)
    if audio and Path(audio).exists():
        # real track: loop to fill, trim to video, fade out the tail
        cmd = [_ff(), "-y", "-i", str(video), "-stream_loop", "-1", "-i", str(audio),
               "-filter_complex", f"[1:a]volume={gain},afade=t=out:st={fout:.2f}:d=1.2[a]",
               "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac",
               "-shortest", "-movflags", "+faststart", str(out)]
    else:
        # placeholder: two soft detuned sines -> gentle pad, faded in/out
        pad = (f"sine=frequency=196:duration={dur:.2f}[s1];"
               f"sine=frequency=293.66:duration={dur:.2f}[s2];"
               f"[s1][s2]amix=inputs=2,volume=0.10,"
               f"afade=t=in:d=1.2,afade=t=out:st={fout:.2f}:d=1.2[a]")
        cmd = [_ff(), "-y", "-i", str(video), "-filter_complex", pad,
               "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac",
               "-shortest", "-movflags", "+faststart", str(out)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0 or not out.exists():
        raise RuntimeError(f"music mux failed: {r.stderr[-400:]}")
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--video", required=True)
    ap.add_argument("--audio", default=None)
    ap.add_argument("--gain", type=float, default=0.6)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    out = add_music(Path(a.video), Path(a.out), Path(a.audio) if a.audio else None, a.gain)
    print(json.dumps({"ok": True, "out": str(out), "placeholder": not bool(a.audio)}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
