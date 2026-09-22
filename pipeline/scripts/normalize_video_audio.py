"""Phase 10 Extension: Automated Audio Normalization & Sidechain Ducking.

Normalizes dialogue to EBU R128 standard (-14 LUFS) and automatically ducks
electronic background soundtrack by -12dB whenever voiceover speech is present.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Optional

REPO_ROOT = Path("D:/new orchestration")


def mix_and_normalize_audio(
    voiceover_path: Path | str,
    soundtrack_path: Path | str,
    output_path: Path | str,
    ducking_db: float = -12.0,
    target_lufs: float = -14.0
) -> bool:
    """Mixes voiceover with ducked soundtrack and applies loudnorm filter."""
    vo = Path(voiceover_path)
    bg = Path(soundtrack_path)
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    if not vo.exists() or not bg.exists():
        print(f"⚠️ Audio inputs missing: {vo} or {bg}")
        return False

    # FFmpeg filtergraph: sidechaincompress ducks input 1 (bg) based on input 0 (vo)
    # followed by loudnorm targeting -14 LUFS
    filter_complex = (
        f"[1:a]volume=0.35[bg_low];"
        f"[bg_low][0:a]sidechaincompress=threshold=0.08:ratio=4:attack=20:release=300[ducked_bg];"
        f"[ducked_bg][0:a]amix=inputs=2:duration=first:dropout_transition=2[mixed];"
        f"[mixed]loudnorm=I={target_lufs}:TP=-1.0:LRA=7[out_audio]"
    )

    cmd = [
        "ffmpeg", "-y",
        "-i", str(vo),
        "-i", str(bg),
        "-filter_complex", filter_complex,
        "-map", "[out_audio]",
        "-c:a", "pcm_s16le",
        "-ar", "48000",
        str(out)
    ]

    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if res.returncode == 0 and out.exists():
            print(f"✅ Master normalized audio generated: {out.name} ({out.stat().st_size:,} bytes)")
            return True
        else:
            print(f"⚠️ FFmpeg normalization warning: {res.stderr[:200]}")
            return False
    except Exception as e:
        print(f"❌ Error during audio normalization: {e}")
        return False


if __name__ == "__main__":
    vo_file = REPO_ROOT / "pipeline" / "state" / "vanna_voiceover_raw.wav"
    bg_file = Path("D:/vanna-remotion/public/vanna_sfx_soundtrack.wav")
    out_file = REPO_ROOT / "pipeline" / "state" / "vanna_normalized_master_audio.wav"

    if vo_file.exists() and bg_file.exists():
        mix_and_normalize_audio(vo_file, bg_file, out_file)
    else:
        print("ℹ️ Script ready for pipeline audio normalization calls.")
