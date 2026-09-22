"""A scripted spot — three Veo beats, a voice, and typography on cue.

`motion.py` builds an eight-second explainer from one locked-off element. This
is the longer form: a written script with named beats, so the visual has to
change three times and the type has to land against a voice rather than
against a timer.

The division of labour is unchanged, and it is the whole reason the output is
publishable:

  **Veo renders the three beats.** Capital held still, capital dividing,
  capital returning to one place. Here the founder's script asks for a slow
  pull-back in the final beat, so Veo is allowed camera movement in that beat
  and forbidden it in the other two.

  **Everything readable is drawn.** Ground, vignette, every word, every cue.
  Nothing published can be misspelt because nothing published was generated.

  **Transitions happen in the frame domain.** Crossfades are blended between
  the composited sequences rather than handed to ffmpeg's xfade filter, so the
  type can continue across a cut instead of dying with its clip.
"""
from __future__ import annotations

import base64
import json
import pathlib
import shutil
import struct
import subprocess
import tempfile
import urllib.request
from pathlib import Path
from typing import Optional

from PIL import Image, ImageChops, ImageDraw

from pipeline.gtm_creative.archetypes import (
    GROUND_BASE, INK_FAINT, INK_MUTED, INK_SOFT, VIOLET_LIGHT,
    OUT_DIR, _fit, _track, _wrap, font, premium, vanna_ground,
)
from pipeline.gtm_creative.motion import _ffmpeg, _window, veo_element

REPO_ROOT = Path(__file__).resolve().parents[2]
FPS = 24
BEAT_S = 6
XFADE_S = 0.6

TTS_MODEL = "gemini-3.1-flash-tts-preview"
TTS_VOICE = "Charon"          # low, unhurried; the script is not excitable

SCRIPT = (
    "Your capital shouldn't sit still.\n\n"
    "Deposit collateral once. Borrow against it. "
    "Move that capital across DeFi.\n\n"
    "One account. Multiple opportunities.\n\n"
    "Vanna. Composable credit for DeFi."
)

# --------------------------------------------------------------------------
# Beats
# --------------------------------------------------------------------------

_COMMON = (
    "Dark, minimal, near-black environment. Matte surfaces, one soft key light "
    "from upper left, clinical and restrained. Everything close in value and "
    "very low contrast. One muted violet is the only colour; everything else "
    "is graphite and near-black. Fine 35mm grain. "
    "RENDER NO TEXT: no words, letters, numerals, labels or captions at any "
    "point. "
    "NEVER: floating crypto coins, currency glyphs, neon chains, glowing "
    "links, generic 3D blocks or cubes, network-node constellations, circuit "
    "textures, vaults, holographic surfaces, cyan, teal, neon, lens flare, "
    "light streaks, starfields, particles, cyberpunk or gaming aesthetics, "
    "bright white, chrome, mercury, silver, liquid metal or any "
    "reflective or glossy surface, any logo or brand mark. The whole "
    "frame must stay dark: a near-black image, not a bright one."
)

_LOCKED = (
    "LOCKED-OFF STATIC CAMERA: the camera does not move, pan, tilt, dolly, "
    "zoom, orbit or drift at any point. "
)

BEATS = [
    # 0-6s — the hook. Stillness has to be the subject, so nothing moves.
    (_LOCKED
     + "A single small pool of matte black ink rests in a shallow circular "
     "basin on a wide empty floor. The ink is non-reflective and absorbs light; "
     "it is NOT metallic, chrome, mercury, silver or shiny. Its surface is "
     "perfectly flat and "
     "completely motionless for the entire shot — not a ripple, not a "
     "reflection moving, no drift. The stillness is the subject. Wide "
     "composition, the left third of the frame entirely empty. "
     + _COMMON),

    # 6-12s — division. Three paths, deliberately unequal, no symmetry.
    (_LOCKED
     + "The matte black ink begins to flow out of its basin along three "
     "separate narrow channels cut into the floor, each heading in a different "
     "direction across the frame. The three channels are deliberately unequal "
     "in width and angle, not symmetrical. A thin muted violet line runs "
     "along the centre of each moving channel. The flow is smooth, purposeful and "
     "unhurried. Wide composition, the left third of the frame kept empty. "
     + _COMMON),

    # 12-18s — return, and the one camera move the script asks for.
    ("The three channels of flowing matte black ink curve back inward and converge "
     "into a single solid form at the centre: a low, calm, sealed monolith "
     "that stays completely stable and unchanged while the ink keeps moving "
     "around it. The camera performs one very slow, smooth pull-back, revealing "
     "more empty floor around the stable centre. No other camera movement. "
     "A thin muted violet line runs in the moving ink; the central form "
     "itself is quiet matte graphite. "
     + _COMMON),
]

# Typography, timed against the voice rather than the clips.
TYPE_BEATS = [
    {"at": 1.0, "until": 5.4, "lines": ["Capital shouldn't", "sit still."],
     "size": 88, "kind": "statement"},
    {"at": 7.6, "until": 12.0, "lines": ["One account.", "Multiple opportunities."],
     "size": 76, "kind": "statement"},
    {"at": 13.4, "until": 99, "lines": ["Vanna"], "size": 116, "kind": "logo",
     "sub": "Composable credit for DeFi."},
]

EYEBROW = "Stellar Soroban · testnet"


# --------------------------------------------------------------------------
# Voice
# --------------------------------------------------------------------------

def _api_key() -> str:
    env = REPO_ROOT / "pipeline" / ".env"
    for line in env.read_text(encoding="utf-8").splitlines():
        if line.strip().startswith(("GEMINI_API_KEY=", "GOOGLE_API_KEY=")):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    raise RuntimeError("no API key in pipeline/.env")


def voiceover(text: str, out_wav: Path, *, voice: str = TTS_VOICE) -> Path:
    """Render the script, and wrap the raw PCM the API returns as a WAV.

    Gemini TTS returns headerless L16 — `audio/l16; rate=24000; channels=1`.
    Handing that straight to ffmpeg gets you noise, so the header is written
    here rather than relying on format sniffing.
    """
    url = ("https://generativelanguage.googleapis.com/v1beta/models/"
           + TTS_MODEL + ":generateContent?key=" + _api_key())
    body = {
        "contents": [{"parts": [{"text":
            "Read this slowly and calmly, with a short pause at each blank "
            "line. Understated, confident, unhurried:\n\n" + text}]}],
        "generationConfig": {
            "responseModalities": ["AUDIO"],
            "speechConfig": {"voiceConfig": {
                "prebuiltVoiceConfig": {"voiceName": voice}}},
        },
    }
    req = urllib.request.Request(url, data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    res = json.loads(urllib.request.urlopen(req, timeout=180).read())
    part = res["candidates"][0]["content"]["parts"][0]
    blob = part.get("inlineData") or part.get("inline_data")
    pcm = base64.b64decode(blob["data"])

    rate = 24000
    mime = str(blob.get("mimeType") or blob.get("mime_type") or "")
    if "rate=" in mime:
        try:
            rate = int(mime.split("rate=")[1].split(";")[0])
        except ValueError:
            pass

    out_wav.parent.mkdir(parents=True, exist_ok=True)
    with out_wav.open("wb") as f:
        f.write(b"RIFF" + struct.pack("<I", 36 + len(pcm)) + b"WAVEfmt ")
        f.write(struct.pack("<IHHIIHH", 16, 1, 1, rate, rate * 2, 2, 16))
        f.write(b"data" + struct.pack("<I", len(pcm)) + pcm)
    return out_wav


# --------------------------------------------------------------------------
# Build
# --------------------------------------------------------------------------

def _dim(rgb, a: float):
    a = max(0.0, min(1.0, a))
    return tuple(int(GROUND_BASE[i] + (rgb[i] - GROUND_BASE[i]) * a) for i in range(3))


def _extract(ff: str, clip: Path, dest: Path, W: int, H: int) -> list[Path]:
    dest.mkdir(parents=True, exist_ok=True)
    subprocess.run([ff, "-y", "-i", str(clip), "-vf",
                    "fps=" + str(FPS) + ",scale=" + str(W) + ":" + str(H),
                    str(dest / "f_%05d.jpg")],
                   capture_output=True, check=True, timeout=300)
    return sorted(dest.glob("f_*.jpg"))



_FEATHER_CACHE: dict = {}


def _feather(w: int, h: int, pct: float = 0.14) -> Image.Image:
    """A soft-edged mask, cached: the same one is used on every frame."""
    from PIL import ImageFilter

    key = (w, h, pct)
    if key in _FEATHER_CACHE:
        return _FEATHER_CACHE[key]
    inset = int(min(w, h) * pct)
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).rectangle(
        [(inset, inset), (w - inset, h - inset)], fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(inset * 0.62))
    _FEATHER_CACHE[key] = mask
    return mask


def build_film(out: Optional[Path] = None, *,
               size: tuple[int, int] = (1600, 900),
               reuse_beats: bool = True) -> Path:
    """Render the spot end to end."""
    out = Path(out or (OUT_DIR / "vanna_capital_should_move.mp4"))
    ff = _ffmpeg()
    W, H = size
    m = int(W * 0.082)

    # Beats
    clips: list[Path] = []
    for i, prompt in enumerate(BEATS):
        clip = OUT_DIR / ("film_beat_" + str(i + 1) + ".mp4")
        if not (reuse_beats and clip.exists()):
            print("  veo beat", i + 1, "of", len(BEATS), "...")
            veo_element(prompt, clip)
        clips.append(clip)

    vo = OUT_DIR / "film_vo.wav"
    if not (reuse_beats and vo.exists()):
        print("  voiceover ...")
        voiceover(SCRIPT, vo)

    ground = premium(vanna_ground(size))
    scratch_root = REPO_ROOT / "pipeline" / "state" / ".render"
    scratch_root.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp(prefix="film_", dir=str(scratch_root)))
    # Veo renders 8s clips; the edit wants 6s beats. Trim on the way in rather
    # than re-generating, and take the trim off the END so the one thing each
    # beat is about — the pour starting, the convergence landing — is kept.
    seqs = [_extract(ff, c, tmp / ("in" + str(i)), W, H)[:BEAT_S * FPS]
            for i, c in enumerate(clips)]

    # Stitch the raw frames with crossfades first, so the type can be drawn
    # over a continuous timeline and carry across a cut.
    xf = int(XFADE_S * FPS)
    timeline: list[Image.Image] = []
    for i, seq in enumerate(seqs):
        frames = [Image.open(f).convert("RGB") for f in seq]
        if i == 0:
            timeline.extend(frames)
            continue
        tail = timeline[-xf:]
        head = frames[:xf]
        blended = [Image.blend(a, b, (n + 1) / (xf + 1))
                   for n, (a, b) in enumerate(zip(tail, head))]
        timeline = timeline[:-xf] + blended + frames[xf:]

    f_eyebrow = font("semibold", 15)
    f_sub = font("regular", 26)
    f_foot = font("regular", 15)

    outdir = tmp / "out"
    outdir.mkdir()
    scratch = ImageDraw.Draw(Image.new("RGB", size))

    for i, frame in enumerate(timeline):
        t = i / FPS
        # Veo fills whatever frame it is given, so composition is taken back
        # here rather than argued for in the prompt: the element is scaled down
        # and placed in a reserved region, and the ground owns everything else.
        ew = int(W * 0.52)
        eh = int(ew * H / W)
        el = frame.resize((ew, eh), Image.Resampling.LANCZOS)
        placed = Image.new("RGB", size, GROUND_BASE)
        # Feather the placement. Pasted square-on, the element announced itself
        # as a rectangle sitting on the ground rather than as part of it.
        placed.paste(el, (int(W * 0.46), int((H - eh) / 2)), _feather(ew, eh))
        base = ImageChops.lighter(ground, placed)

        # The left column is reserved for type throughout, so it is scrimmed
        # for the whole run rather than only while words are on screen —
        # otherwise the falloff itself becomes a visible event.
        mask = Image.new("L", (W, 1), 0)
        px = mask.load()
        edge = int(W * 0.52)
        for x in range(W):
            px[x, 0] = int(255 * 0.74 * (1 - x / edge) ** 1.6) if x < edge else 0
        base = Image.composite(Image.new("RGB", size, GROUND_BASE),
                               base, mask.resize((W, H)))
        d = ImageDraw.Draw(base)

        a = _window(t, 0.4, 0.8)
        if a > 0:
            _track(d, (m, int(H * 0.105)), EYEBROW.upper(), f_eyebrow,
                   _dim(VIOLET_LIGHT, a), 2.2)

        for b in TYPE_BEATS:
            if t < b["at"]:
                continue
            # Out is slower than in. A fast exit reads as a cut, and a cut
            # competes with the crossfade already happening underneath.
            alpha = _window(t, b["at"], 0.7)
            if t > b["until"]:
                alpha *= max(0.0, 1 - (t - b["until"]) / 0.9)
            if alpha <= 0.01:
                continue

            f_line = font("regular", b["size"])
            y = int(H * 0.30) if b["kind"] == "statement" else int(H * 0.34)
            for n, line in enumerate(b["lines"]):
                la = _window(t, b["at"] + n * 0.25, 0.7) * (alpha / max(alpha, 1e-6))
                la = min(la, alpha)
                d.text((m, y + int(16 * (1 - la))), line, font=f_line,
                       fill=_dim(INK_SOFT, la))
                y += int(b["size"] * 1.18)
            if b.get("sub"):
                sa = _window(t, b["at"] + 0.5, 0.8)
                sa = min(sa, alpha)
                d.text((m, y + 18), b["sub"], font=f_sub, fill=_dim(INK_MUTED, sa))

        fa = _window(t, 15.0, 1.0)
        if fa > 0:
            d.text((m, int(H * 0.915)),
                   "Stellar Soroban testnet · docs.vanna.finance",
                   font=f_foot, fill=_dim(INK_FAINT, fa))

        base.save(outdir / ("f_%05d.jpg" % (i + 1)), quality=95)

    silent = tmp / "silent.mp4"
    subprocess.run([ff, "-y", "-framerate", str(FPS), "-i",
                    str(outdir / "f_%05d.jpg"), "-c:v", "libx264",
                    "-pix_fmt", "yuv420p", "-crf", "18", str(silent)],
                   capture_output=True, check=True, timeout=600)

    # The voice leads the picture by a beat; a spot whose audio starts on
    # frame one feels like it began before the viewer arrived.
    # Fit the read to the picture. TTS pacing varies run to run, and letting
    # `-shortest` arbitrate produced a 22.8s file from a 17s edit: the audio was
    # simply longer and dragged the container with it. atempo stays under 1.25
    # so the voice does not acquire that sped-up quality.
    # Resolve ffprobe properly. Deriving it from the ffmpeg path by string
    # replacement breaks the moment the binary lives in a directory whose own
    # name contains "ffmpeg", which on Windows it usually does.
    probe = shutil.which("ffprobe")
    if not probe:
        raise RuntimeError("ffprobe not found on PATH")

    def _dur(path: Path) -> float:
        r = subprocess.run([probe, "-v", "error", "-show_entries",
                            "format=duration", "-of", "csv=p=0", str(path)],
                           capture_output=True, text=True, timeout=60)
        return float(r.stdout.strip())

    vid_s = _dur(silent)
    vo_s = _dur(vo)

    lead = 0.7
    target = max(1.0, vid_s - lead - 0.4)
    tempo = min(1.25, max(1.0, vo_s / target))
    chain = "[1:a]adelay=700|700"
    if tempo > 1.001:
        chain += ",atempo=" + ("%.4f" % tempo)
    chain += ",apad[a]"

    subprocess.run([ff, "-y", "-i", str(silent), "-i", str(vo),
                    "-filter_complex", chain,
                    "-map", "0:v", "-map", "[a]", "-c:v", "copy",
                    "-c:a", "aac", "-b:a", "160k", "-t", ("%.3f" % vid_s),
                    "-movflags", "+faststart", str(out)],
                   capture_output=True, check=True, timeout=600)

    shutil.rmtree(tmp, ignore_errors=True)
    return out


if __name__ == "__main__":
    print(build_film())
