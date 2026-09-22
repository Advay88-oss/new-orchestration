#!/usr/bin/env python3
"""Synthesizes a 41.2-second, 48kHz stereo electronic sound-design soundtrack
and mixes it with the voiceover narration:
- Act 1 (0.0s): Deep sub-bass 45Hz impact (Problem)
- Act 2 (8.0s): Metallic shimmer & latch (Vanna Intro & 3D Coin)
- Act 3 (16.0s): Clean modular lock click (SmartAccount 10x Solution)
- Act 4 (25.0s): ~320ms telemetry radar pings + solvency chime (Risk HUD)
- Act 5 (33.5s): Full resonant electronic ambient chord resolve (CTA)
"""

from __future__ import annotations

import math
import subprocess
import wave
from pathlib import Path
import numpy as np

SAMPLE_RATE = 48000
DURATION_SEC = 41.20
TOTAL_SAMPLES = int(SAMPLE_RATE * DURATION_SEC)

t = np.linspace(0, DURATION_SEC, TOTAL_SAMPLES, endpoint=False)

left = np.zeros(TOTAL_SAMPLES, dtype=np.float32)
right = np.zeros(TOTAL_SAMPLES, dtype=np.float32)

# Continuous atmospheric sub-drone
drone = 0.11 * np.sin(2 * np.pi * 46.25 * t) + 0.07 * np.sin(2 * np.pi * 92.5 * t)
drone_r = 0.11 * np.sin(2 * np.pi * 46.40 * t) + 0.07 * np.sin(2 * np.pi * 92.8 * t)
left += drone
right += drone_r

def add_impact(start_t: float, freq: float, decay: float, amp: float = 0.55, pan: float = 0.0):
    idx_start = int(start_t * SAMPLE_RATE)
    dur_samples = int(decay * SAMPLE_RATE)
    idx_end = min(TOTAL_SAMPLES, idx_start + dur_samples)
    seg_t = np.linspace(0, (idx_end - idx_start) / SAMPLE_RATE, idx_end - idx_start)
    
    pitch = freq * np.exp(-seg_t * 6.0)
    sig = amp * np.sin(2 * np.pi * pitch * seg_t) * np.exp(-seg_t / (decay * 0.35))
    
    l_gain = math.cos((pan + 1) * math.pi / 4)
    r_gain = math.sin((pan + 1) * math.pi / 4)
    left[idx_start:idx_end] += sig * l_gain
    right[idx_start:idx_end] += sig * r_gain

def add_click(start_t: float, amp: float = 0.3):
    idx_start = int(start_t * SAMPLE_RATE)
    dur = int(0.08 * SAMPLE_RATE)
    idx_end = min(TOTAL_SAMPLES, idx_start + dur)
    seg_t = np.linspace(0, 0.08, idx_end - idx_start)
    noise = np.random.uniform(-1, 1, idx_end - idx_start) * np.exp(-seg_t * 80)
    click = amp * (noise + 0.5 * np.sin(2 * np.pi * 2400 * seg_t))
    left[idx_start:idx_end] += click
    right[idx_start:idx_end] += click

def add_telemetry_pulses(start_t: float, count: int, interval: float = 0.32, freq: float = 1760.0):
    for i in range(count):
        pt = start_t + i * interval
        idx_start = int(pt * SAMPLE_RATE)
        dur = int(0.06 * SAMPLE_RATE)
        idx_end = min(TOTAL_SAMPLES, idx_start + dur)
        seg_t = np.linspace(0, 0.06, idx_end - idx_start)
        ping = 0.15 * np.sin(2 * np.pi * (freq + (i * 80)) * seg_t) * np.exp(-seg_t * 70)
        pan = -0.4 if i % 2 == 0 else 0.4
        l_gain = math.cos((pan + 1) * math.pi / 4)
        r_gain = math.sin((pan + 1) * math.pi / 4)
        left[idx_start:idx_end] += ping * l_gain
        right[idx_start:idx_end] += ping * r_gain

# Act 1 (0.0s): Problem
add_impact(start_t=0.1, freq=80.0, decay=2.0, amp=0.55, pan=0.0)
add_click(start_t=0.05, amp=0.3)

# Act 2 (8.0s): Vanna Reveal
add_impact(start_t=8.02, freq=110.0, decay=1.5, amp=0.5, pan=0.0)
add_click(start_t=8.0, amp=0.35)

# Act 3 (16.0s): SmartAccount 10x Solution
add_impact(start_t=16.02, freq=115.0, decay=1.4, amp=0.5, pan=-0.2)
add_click(start_t=16.0, amp=0.35)

# Act 4 (25.0s): Telemetry HUD & Mercury Pings
add_impact(start_t=25.02, freq=95.0, decay=1.5, amp=0.45, pan=0.0)
add_click(start_t=25.0, amp=0.3)
add_telemetry_pulses(start_t=25.3, count=14, interval=0.32, freq=1440.0)
add_impact(start_t=30.0, freq=523.25, decay=1.8, amp=0.35, pan=0.3) # Safe chime

# Act 5 (33.5s - 41.2s): Resolving Pad Chord
add_impact(start_t=33.52, freq=72.0, decay=3.2, amp=0.65, pan=0.0)
add_click(start_t=33.5, amp=0.4)

pad_dur = 7.7
pad_t = np.linspace(0, pad_dur, int(pad_dur * SAMPLE_RATE))
idx_pad_start = int(33.55 * SAMPLE_RATE)
idx_pad_end = min(TOTAL_SAMPLES, idx_pad_start + len(pad_t))
actual_len = idx_pad_end - idx_pad_start

pad_fade = np.exp(-pad_t[:actual_len] * 0.35)
pad = 0.16 * (
    np.sin(2 * np.pi * 185.0 * pad_t[:actual_len]) +
    np.sin(2 * np.pi * 277.18 * pad_t[:actual_len]) +
    np.sin(2 * np.pi * 440.0 * pad_t[:actual_len])
) * pad_fade

left[idx_pad_start:idx_pad_end] += pad
right[idx_pad_start:idx_pad_end] += pad

# Master normalization
max_val = max(np.max(np.abs(left)), np.max(np.abs(right)), 1e-6)
target_peak = 0.89
left = (left / max_val) * target_peak
right = (right / max_val) * target_peak

left_pcm = (left * 32767).astype(np.int16)
right_pcm = (right * 32767).astype(np.int16)
interleaved = np.empty((TOTAL_SAMPLES * 2,), dtype=np.int16)
interleaved[0::2] = left_pcm
interleaved[1::2] = right_pcm

out_dir = Path("D:/vanna-remotion/public")
out_dir.mkdir(parents=True, exist_ok=True)
sfx_wav = out_dir / "vanna_41s_sfx.wav"

with wave.open(str(sfx_wav), "wb") as wf:
    wf.setnchannels(2)
    wf.setsampwidth(2)
    wf.setframerate(SAMPLE_RATE)
    wf.writeframes(interleaved.tobytes())

print(f"✅ Synthesized 41s SFX Track: {sfx_wav}")

# Mix with voiceover using FFmpeg
vo_mp3 = Path("C:/Users/Advay Anand/AppData/Local/hermes/audio_cache/vanna_36s_narration.mp3")
master_wav = out_dir / "vanna_master_41s_audio.wav"

cmd = [
    "ffmpeg", "-y",
    "-i", str(vo_mp3),
    "-i", str(sfx_wav),
    "-filter_complex",
    "[0:a]volume=1.38,adelay=300|300[voice];[1:a]volume=0.38[bg];[voice][bg]amix=inputs=2:duration=first:dropout_transition=2[out]",
    "-map", "[out]",
    "-c:a", "pcm_s16le",
    "-ar", "48000",
    str(master_wav)
]

res = subprocess.run(cmd, capture_output=True, text=True)
if res.returncode == 0:
    print(f"🎉 Master 41s Audio with Voiceover Created: {master_wav} ({master_wav.stat().st_size:,} bytes)")
else:
    print(f"❌ FFmpeg mix error: {res.stderr[:300]}")
