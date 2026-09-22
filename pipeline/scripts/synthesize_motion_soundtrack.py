#!/usr/bin/env python3
"""Synthesizes a 30-second, 48kHz stereo electronic soundtrack
frame-synced to Vanna's 4-scene 30s product intro:
- Scene 1 (0-7.5s): Deep sub-bass 45Hz impact + atmospheric drone
- Scene 2 (7.5-15s): Clean modular lock click + deposit-to-deployment surge
- Scene 3 (15-22.5s): ~320ms sub-second telemetry radar pings + solvency chime
- Scene 4 (22.5-30s): Resonant electronic ambient pad chord resolve
"""

from __future__ import annotations

import math
import wave
from pathlib import Path
import numpy as np

SAMPLE_RATE = 48000
DURATION_SEC = 30.04
TOTAL_SAMPLES = int(SAMPLE_RATE * DURATION_SEC)

t = np.linspace(0, DURATION_SEC, TOTAL_SAMPLES, endpoint=False)

left = np.zeros(TOTAL_SAMPLES, dtype=np.float32)
right = np.zeros(TOTAL_SAMPLES, dtype=np.float32)

# Continuous atmospheric sub-drone (F# minor: 46.25 Hz & 92.5 Hz)
drone = 0.11 * np.sin(2 * np.pi * 46.25 * t) + 0.07 * np.sin(2 * np.pi * 92.5 * t)
drone_r = 0.11 * np.sin(2 * np.pi * 46.40 * t) + 0.07 * np.sin(2 * np.pi * 92.8 * t)
left += drone
right += drone_r

def add_impact(start_t: float, freq: float, decay: float, amp: float = 0.45, pan: float = 0.0):
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

def add_click(start_t: float, amp: float = 0.28):
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
        ping = 0.16 * np.sin(2 * np.pi * (freq + (i * 80)) * seg_t) * np.exp(-seg_t * 70)
        pan = -0.4 if i % 2 == 0 else 0.4
        l_gain = math.cos((pan + 1) * math.pi / 4)
        r_gain = math.sin((pan + 1) * math.pi / 4)
        left[idx_start:idx_end] += ping * l_gain
        right[idx_start:idx_end] += ping * r_gain

# --- Scene 1 (t=0.0s): Core Hook Impact ---
add_impact(start_t=0.1, freq=80.0, decay=2.0, amp=0.6, pan=0.0)
add_click(start_t=0.05, amp=0.35)

# --- Scene 2 (t=7.5s): Deposit to Deployment Latch ---
add_impact(start_t=7.52, freq=110.0, decay=1.4, amp=0.5, pan=-0.2)
add_click(start_t=7.5, amp=0.4)
add_click(start_t=7.65, amp=0.25)

# --- Scene 3 (t=15.0s): Sub-Second Solvency & Mercury Pings ---
add_impact(start_t=15.02, freq=95.0, decay=1.5, amp=0.5, pan=0.0)
add_click(start_t=15.0, amp=0.35)
add_telemetry_pulses(start_t=15.3, count=12, interval=0.32, freq=1400.0)
add_impact(start_t=19.5, freq=523.25, decay=1.8, amp=0.35, pan=0.2) # Safe chime

# --- Scene 4 (t=22.5s): Vanna Resolving Chord Outro ---
add_impact(start_t=22.52, freq=72.0, decay=3.0, amp=0.7, pan=0.0)
add_click(start_t=22.5, amp=0.4)

# Outro chord pads (F# - C# - A)
pad_dur = 7.5
pad_t = np.linspace(0, pad_dur, int(pad_dur * SAMPLE_RATE))
idx_pad_start = int(22.55 * SAMPLE_RATE)
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

# Master soft limiter & normalize to -1 dB
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
out_wav = out_dir / "vanna_sfx_soundtrack.wav"

with wave.open(str(out_wav), "wb") as wf:
    wf.setnchannels(2)
    wf.setsampwidth(2)
    wf.setframerate(SAMPLE_RATE)
    wf.writeframes(interleaved.tobytes())

print(f"✅ Synthesized 30s SFX Soundtrack: {out_wav} ({out_wav.stat().st_size:,} bytes)")
