#!/usr/bin/env python3
"""Mux a voiceover (and optional ducked music bed) onto a rendered video.

Runs locally on any machine — pure ffmpeg, no ML, no GPU. The heavy part
(cloning the voice with OmniVoice) happens on a hosted GPU; this just combines
the resulting vo.wav with the film.

  python add_voice.py --video vanna-brand.mp4 --voice vo.wav --out vanna-brand-vo.mp4
  python add_voice.py --video vanna-brand.mp4 --voice vo.wav --music bed.mp3 --out out.mp4

Video is the master clock: the voice is padded with trailing silence to the
video length (never stretched), and the output is exactly the video's duration.
A --music bed is looped, ducked ~14 dB under the voice (sidechain), and mixed.
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path


def probe_dur(path: str) -> float:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "json", path],
        capture_output=True, text=True, check=True,
    )
    return float(json.loads(out.stdout)["format"]["duration"])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--video", required=True)
    ap.add_argument("--voice", required=True, help="cloned voiceover wav (from OmniVoice)")
    ap.add_argument("--music", help="optional royalty-free bed; looped + ducked under VO")
    ap.add_argument("--voice-gain", type=float, default=1.0)
    ap.add_argument("--music-gain", type=float, default=0.16)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    for f in (a.video, a.voice, *( [a.music] if a.music else [] )):
        if not Path(f).exists():
            print(f"missing: {f}", file=sys.stderr)
            return 2

    vdur = probe_dur(a.video)
    print(f"video duration: {vdur:.2f}s")

    cmd = ["ffmpeg", "-y", "-i", a.video, "-i", a.voice]
    if a.music:
        cmd += ["-stream_loop", "-1", "-i", a.music]

    if a.music:
        # voice -> normalize/pad; music -> loop, trim, gain, duck under voice, then mix
        fc = (
            f"[1:a]aresample=48000,volume={a.voice_gain},"
            f"apad,atrim=0:{vdur:.3f},asetpts=N/SR/TB[vo];"
            f"[2:a]aresample=48000,volume={a.music_gain},atrim=0:{vdur:.3f}[bed];"
            f"[bed][vo]sidechaincompress=threshold=0.03:ratio=8:attack=20:release=300[ducked];"
            f"[vo][ducked]amix=inputs=2:normalize=0:duration=first[aout]"
        )
    else:
        fc = (
            f"[1:a]aresample=48000,volume={a.voice_gain},"
            f"apad,atrim=0:{vdur:.3f},asetpts=N/SR/TB[aout]"
        )

    cmd += [
        "-filter_complex", fc,
        "-map", "0:v", "-map", "[aout]",
        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
        "-t", f"{vdur:.3f}", a.out,
    ]
    print("running ffmpeg…")
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stderr[-2000:], file=sys.stderr)
        return r.returncode
    print(f"wrote {a.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
