#!/usr/bin/env python3
"""Turn a Vanna app screen-recording into a branded 'demo'-style promo video.

The crypto-video-style `demo` look = real app footage, topped and tailed with
brand cards. This composites:  brand intro card  ->  the recording (scaled &
letterboxed onto the tenant's brand ground, logo overlaid)  ->  brand outro card,
all at 1080x1080, concatenated. Palette/logo come from the OKF bundle (OKF_BUNDLE).

    OKF_BUNDLE=okf python pipeline/scripts/build_demo_video.py \
      --recording "rec.mp4" --title "Supply XLM. Earn onchain." \
      --subtitle "Farm" --cta "Try the testnet" --domain "vanna.finance" \
      --out farm.mp4 --max-body 22
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import render_video as rvid  # noqa: E402


def _ff() -> str:
    return shutil.which("ffmpeg") or "ffmpeg"


def _bg_hex() -> str:
    return str(getattr(rvid.rv, "BACKGROUND", "#0D0616")).lstrip("#")


def build(recording: Path, out: Path, title: str, subtitle: str, cta: str,
          domain: str, accent: str | None, max_body: float, intro_s: float) -> Path:
    tmp = Path(tempfile.mkdtemp(prefix="demo_"))
    intro = tmp / "intro.mp4"
    body = tmp / "body.mp4"
    outro = tmp / "outro.mp4"

    # 1) brand intro + outro cards (the renderer, short)
    rvid.render_video({"headline": title, "emphasis": subtitle}, intro,
                      style="card", accent=accent, seconds=intro_s)
    rvid.render_video({"headline": cta or title, "cta": domain}, outro,
                      style="card", accent=accent, seconds=max(2.5, intro_s))

    # 2) recording -> 1080x1080 on brand ground + logo overlay, silent, trimmed
    # Recording -> 1080x1080, letterboxed onto the brand ground, silent, trimmed.
    # (Brand identity comes from the intro/outro cards, which carry the logo — a
    # per-frame ffmpeg logo overlay is fragile across footage, so keep the body clean.)
    bg = _bg_hex()
    vf = (f"scale=1080:1080:force_original_aspect_ratio=decrease,"
          f"pad=1080:1080:(ow-iw)/2:(oh-ih)/2:color=0x{bg},fps=15,format=yuv420p,setsar=1")
    cmd = [_ff(), "-y", "-t", str(max_body), "-i", str(recording),
           "-vf", vf, "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", "15", str(body)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0 or not body.exists():
        raise RuntimeError(f"body encode failed: {r.stderr[-400:]}")

    # 3) concat intro + body + outro (re-encode via concat filter for safety)
    out = Path(out); out.parent.mkdir(parents=True, exist_ok=True)
    cc = [_ff(), "-y", "-i", str(intro), "-i", str(body), "-i", str(outro),
          "-filter_complex",
          "[0:v]setsar=1,fps=15[a];[1:v]setsar=1,fps=15[b];[2:v]setsar=1,fps=15[c];"
          "[a][b][c]concat=n=3:v=1:a=0[v]",
          "-map", "[v]", "-c:v", "libx264", "-pix_fmt", "yuv420p",
          "-movflags", "+faststart", str(out)]
    r = subprocess.run(cc, capture_output=True, text=True)
    shutil.rmtree(tmp, ignore_errors=True)
    if r.returncode != 0 or not out.exists():
        raise RuntimeError(f"concat failed: {r.stderr[-400:]}")
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--recording", required=True)
    ap.add_argument("--title", required=True)
    ap.add_argument("--subtitle", default="")
    ap.add_argument("--cta", default="Try the testnet")
    ap.add_argument("--domain", default="vanna.finance")
    ap.add_argument("--accent", default=None)
    ap.add_argument("--max-body", type=float, default=22.0)
    ap.add_argument("--intro-seconds", type=float, default=3.0)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    out = build(Path(a.recording), Path(a.out), a.title, a.subtitle, a.cta,
                a.domain, a.accent, a.max_body, a.intro_seconds)
    import json
    print(json.dumps({"ok": True, "out": str(out), "bytes": out.stat().st_size}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
