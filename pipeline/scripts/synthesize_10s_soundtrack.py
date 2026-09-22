#!/usr/bin/env python3
"""Synthesizes a 10.0-second, 48kHz stereo electronic sound-design soundtrack
frame-synced to the 10-second Vanna partnership & 10X coin video:
- 0.0s: Deep sub-bass 45Hz impact as 3D coin appears
- 2.0s: Subtle specular metallic shimmer
- 5.0s: Clean mechanical lock click + transition surge
- 7.5s: Resonant F# minor ambient pad chord resolve
"""

from __future__ import annotations

import math
import wave
from pathlib import Path
import numpy as np

SAMPLE_RATE = 48000
DURATION_SEC = 10.04
TOTAL_SAMPLES = int(SAMPLE_RATE * DURATION_SEC)

t = np.linspace(0, DURATION_SEC, TOTAL_SAMPLES, endpoint=False)

left = np.zeros(TOTAL_SAMPLES, dtype=np.float32)
right = np.zeros(TOTAL_SAMPLES, dtype=np.float32)

# Continuous atmospheric sub-drone
drone = 0.12 * np.sin(2 * np.pi * 46.25 * t) + 0.07 * np.sin(2 * np.pi * 92.5 * t)
drone_r = 0.12 * np.sin(2 * np.pi * 46.40 * t) + 0.07 * np.sin(2 * np.pi * 92.8 * t)
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

def add_click(start_t: float, amp: float = 0.32):
    idx_start = int(start_t * SAMPLE_RATE)
    dur = int(0.08 * SAMPLE_RATE)
    idx_end = min(TOTAL_SAMPLES, idx_start + dur)
    seg_t = np.linspace(0, 0.08, idx_end - idx_start)
    noise = np.random.uniform(-1, 1, idx_end - idx_start) * np.exp(-seg_t * 80)
    click = amp * (noise + 0.5 * np.sin(2 * np.pi * 2400 * seg_t))
    left[idx_start:idx_end] += click
    right[idx_start:idx_end] += click

# 0.0s: Initial coin reveal impact
add_impact(start_t=0.1, freq=85.0, decay=2.0, amp=0.6, pan=0.0)
add_click(start_t=0.05, amp=0.35)

# 5.0s: Transition click & lockup surge
add_impact(start_t=5.02, freq=105.0, decay=1.5, amp=0.55, pan=0.0)
add_click(start_t=5.0, amp=0.4)

# 6.0s - 10.0s: Outro pad chord resolve
pad_dur = 4.0
pad_t = np.linspace(0, pad_dur, int(pad_dur * SAMPLE_RATE))
idx_pad_start = int(6.0 * SAMPLE_RATE)
idx_pad_end = min(TOTAL_SAMPLES, idx_pad_start + len(pad_t))
actual_len = idx_pad_end - idx_pad_start

pad_fade = np.exp(-pad_t[:actual_len] * 0.4)
pad = 0.18 * (
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
out_wav = out_dir / "vanna_10s_sfx.wav"

with wave.open(str(out_wav), "wb") as wf:
    wf.setnchannels(2)
    wf.setsampwidth(2)
    wf.setframerate(SAMPLE_RATE)
    wf.writeframes(interleaved.tobytes())

print(f"✅ Synthesized 10s SFX Soundtrack: {out_wav} ({out_wav.stat().st_size:,} bytes)")
