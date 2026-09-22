"""Motion assets — Veo for the element, motion graphics for the argument.

Veo's whole competence is cinematography, so asking it for a flat explainer
gets you a film: a slow dolly through a void, shallow depth of field, a sense
of place. Every A09 output so far has been that, and one came back as a glowing
Bitcoin coin in a vault.

The split here is the same one the stills use, applied to time:

  **Veo renders the element, locked off.** One flat figure, one thing changing,
  no camera movement at all. It is being used for the only part it is better
  at than we are — organic, believable transition of a surface over time.

  **Everything else is drawn.** The Vanna ground, the vignette, the type, the
  timing. The background is byte-identical to the still post, every word is
  composited with the exact strings we passed in, and the argument is carried
  by typography that arrives on cue rather than by camera work.

FFmpeg does the frame traffic. It is already a dependency — the creative judge
uses it to pull a frame out of the MP4 it reviews.
"""
from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Optional

from PIL import Image, ImageChops, ImageDraw

from pipeline.gtm_creative.archetypes import (
    GROUND_BASE, HEALTHY, INK_FAINT, INK_MUTED, INK_SOFT, VIOLET, VIOLET_LIGHT,
    OUT_DIR, _fit, _track, _wrap, font, premium, vanna_ground,
)

FPS = 24
DURATION_S = 8


# The locked-off, flat brief. Every clause that says "no camera" is load
# bearing: Veo's default is to move, and a move is what makes it read as film.
VEO_FLAT_PROMPT = (
    "LOCKED-OFF STATIC CAMERA. The camera does not move, pan, tilt, dolly, "
    "zoom, orbit, track, drift, shake or rack focus at any point. The frame is "
    "absolutely still for the entire duration, as if screen-recorded from a "
    "motion-graphics timeline. No depth of field, no bokeh, no parallax, no "
    "lens effects, no film look, no cinematic lighting. "
    "FLAT 2D MOTION GRAPHIC, orthographic and face-on, drawn like an animated "
    "figure in technical documentation. "
    "CONTENT: a precise grid of sixteen identical small squares, four by four, "
    "evenly spaced with clear gaps between every unit. The grid sits in the "
    "RIGHT TWO-THIRDS of the frame; the left third is completely empty "
    "near-black with nothing in it at all. "
    "EACH SQUARE IS VERY DARK — a near-black panel only a few percent brighter "
    "than the background, defined by a thin mid-grey outline and one faint "
    "hairline along its top edge. Do NOT fill the squares with white, silver, "
    "light grey, chrome or any bright or reflective tone. They should be "
    "barely distinguishable from the background except for their outlines. "
    "The squares are completely still and unchanging. "
    "THE ONLY MOTION: at roughly the midpoint, ONE single square — off-centre, "
    "not in the middle — smoothly fills with a muted dull red over about one "
    "second, then holds that state, unchanged, for the rest of the shot. "
    "Nothing else in the frame changes at any point. The other fifteen squares "
    "never alter in any way. No lines, cables or connections ever appear "
    "between the squares. "
    "Colour: near-black background, graphite outlines, exactly one muted dull "
    "red, which is itself muted and dark. No other colour anywhere. Keep "
    "the whole frame dark, quiet and very low contrast: this is a near-black "
    "image with faint outlines, not a bright one. "
    "RENDER NO TEXT: no words, letters, numerals, labels, captions or "
    "watermarks at any point in the shot. "
    "NEVER: bright or white filled shapes, chrome, silver, metallic sheen, camera movement of any kind, 3D, perspective, isometric "
    "projection, extrusion, cast shadows, reflections, glow, neon, cyan, teal, "
    "coins, currency glyphs, vaults, lens flare, light streaks, haze, "
    "particles, cyberpunk or gaming aesthetics, any logo or brand mark."
)


def _ffmpeg() -> str:
    exe = shutil.which("ffmpeg")
    if not exe:
        raise RuntimeError("ffmpeg not found on PATH; it is needed to build motion")
    return exe


def veo_element(prompt: str, out: Path, *, project: str = "vanna-mcp",
                location: str = "us-central1", model: str = "veo-3.1-generate-001",
                timeout_s: float = 420.0) -> Path:
    """Render one locked-off element clip with Veo."""
    import json
    import time
    import urllib.error
    import urllib.request

    from pipeline.scripts.veo_broll import _vertex_token, _find_video, _write_video

    token = _vertex_token()
    if not token:
        raise RuntimeError("no Vertex token; run `gcloud auth application-default login`")

    host = "https://" + location + "-aiplatform.googleapis.com"
    base = (host + "/v1/projects/" + project + "/locations/" + location
            + "/publishers/google/models/" + model)
    headers = {"Authorization": "Bearer " + token,
               "x-goog-user-project": project, "Content-Type": "application/json"}
    body = {"instances": [{"prompt": prompt}],
            "parameters": {"aspectRatio": "16:9", "sampleCount": 1,
                           "durationSeconds": DURATION_S}}

    req = urllib.request.Request(base + ":predictLongRunning",
                                 data=json.dumps(body).encode(),
                                 headers=headers, method="POST")
    op = json.loads(urllib.request.urlopen(req, timeout=90).read())
    name = op.get("name")
    if not name:
        raise RuntimeError("Veo returned no operation: " + json.dumps(op)[:200])

    deadline = time.time() + timeout_s
    while time.time() < deadline:
        time.sleep(15)
        poll = urllib.request.Request(
            base + ":fetchPredictOperation",
            data=json.dumps({"operationName": name}).encode(),
            headers=headers, method="POST")
        res = json.loads(urllib.request.urlopen(poll, timeout=90).read())
        if not res.get("done"):
            continue
        if res.get("error"):
            raise RuntimeError("Veo failed: " + json.dumps(res["error"])[:250])
        b64, uri = _find_video(res)
        if not (b64 or uri):
            raise RuntimeError("Veo finished with no video payload")
        out.parent.mkdir(parents=True, exist_ok=True)
        if not _write_video(b64, uri, out, None):
            raise RuntimeError("Veo payload could not be written")
        return out
    raise RuntimeError("Veo did not finish within " + str(int(timeout_s)) + "s")


# --------------------------------------------------------------------------
# Timing
# --------------------------------------------------------------------------

def _ease(t: float) -> float:
    """Ease-out cubic. Linear fades are the tell of an unconsidered animation."""
    t = max(0.0, min(1.0, t))
    return 1 - (1 - t) ** 3


def _window(t: float, start: float, dur: float = 0.55) -> float:
    """How far through its own entrance an element is, at time t."""
    return _ease((t - start) / dur) if t > start else 0.0


def _fade(img: Image.Image, layer: Image.Image, alpha: float) -> Image.Image:
    if alpha <= 0.001:
        return img
    return Image.blend(img, Image.alpha_composite(img.convert("RGBA"),
                                                  layer).convert("RGB"),
                       min(1.0, alpha))


def build_isolation_motion(
    headline: str, deck: str, eyebrow: str,
    stat_value: str, stat_label: str, footnote: str, *,
    out: Optional[Path] = None,
    element_mp4: Optional[Path] = None,
    size: tuple[int, int] = (1600, 900),
) -> Path:
    """Composite the Veo element onto the Vanna ground and animate the type."""
    out = Path(out or (OUT_DIR / "demo_motion_isolation.mp4"))
    element = Path(element_mp4 or (OUT_DIR / "demo_motion_element.mp4"))
    if not element.exists():
        veo_element(VEO_FLAT_PROMPT, element)

    ff = _ffmpeg()
    W, H = size
    m = int(W * 0.082)

    # The ground, the texture and the vignette are identical on every frame, so
    # they are built once. Doing the depth pass per frame would cost minutes
    # and produce the same pixels 192 times.
    ground = premium(vanna_ground(size))

    scratch_root = Path(__file__).resolve().parents[2] / "pipeline" / "state" / ".render"
    scratch_root.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp(prefix="motion_", dir=str(scratch_root)))
    frames_in = tmp / "in"
    frames_out = tmp / "out"
    frames_in.mkdir()
    frames_out.mkdir()

    subprocess.run([ff, "-y", "-i", str(element), "-vf",
                    "fps=" + str(FPS) + ",scale=" + str(W) + ":" + str(H),
                    str(frames_in / "f_%05d.jpg")],
                   capture_output=True, check=True, timeout=300)

    files = sorted(frames_in.glob("f_*.jpg"))
    if not files:
        raise RuntimeError("no frames extracted from the element clip")

    f_eyebrow = font("semibold", 15)
    f_deck = font("regular", 23)
    f_stat = font("regular", 104)
    f_statlab = font("semibold", 15)
    f_foot = font("regular", 15)

    scratch = Image.new("RGB", size)
    d0 = ImageDraw.Draw(scratch)
    f_head, head_lines, head_lh = _fit(d0, headline, "regular", int(W * 0.38), 3, 78)
    deck_lines = _wrap(d0, deck, f_deck, int(W * 0.34))[:2]

    for i, fp in enumerate(files):
        t = i / FPS
        frame = Image.open(fp).convert("RGB")

        # Same compositing rule as the stills: the element is rendered on
        # near-black, so a per-channel lighten drops our ground in behind it.
        base = ImageChops.lighter(ground, frame)

        # A left falloff, deepening as the type arrives, so the words always
        # have their own ground no matter what the element does.
        scrim_strength = 0.55 + 0.30 * _window(t, 0.15, 0.9)
        mask = Image.new("L", (W, 1), 0)
        px = mask.load()
        edge = int(W * 0.54)
        for x in range(W):
            px[x, 0] = int(255 * scrim_strength * (1 - x / edge) ** 1.6) if x < edge else 0
        base = Image.composite(Image.new("RGB", size, GROUND_BASE),
                               base, mask.resize((W, H)))

        d = ImageDraw.Draw(base)

        # Each element enters on its own cue. Nothing moves once it has landed:
        # motion that continues after it has said its piece is decoration.
        a = _window(t, 0.25)
        if a > 0:
            _track(d, (m, int(H * 0.115)), eyebrow.upper(), f_eyebrow,
                   _dim(VIOLET_LIGHT, a), 2.2)

        y = int(H * 0.115) + 44
        for n, line in enumerate(head_lines):
            la = _window(t, 0.55 + n * 0.22, 0.6)
            if la > 0:
                # Lines rise a few pixels as they arrive — enough to read as
                # arrival, not enough to read as an effect.
                d.text((m, y + int(14 * (1 - la))), line, font=f_head,
                       fill=_dim(INK_SOFT, la))
            y += head_lh

        y += 14
        for n, line in enumerate(deck_lines):
            la = _window(t, 1.45 + n * 0.14, 0.6)
            if la > 0:
                d.text((m, y), line, font=f_deck, fill=_dim(INK_MUTED, la))
            y += 32

        # The figure lands just after the element changes, so the number reads
        # as the consequence of what just happened on the right.
        sa = _window(t, 4.6, 0.7)
        if sa > 0:
            sy = int(H * 0.68)
            d.text((m, sy), stat_value, font=f_stat, fill=_dim(INK_SOFT, sa))
            lb = _window(t, 4.95, 0.6)
            if lb > 0:
                _track(d, (m + 4, sy + 126), stat_label.upper(), f_statlab,
                       _dim(INK_MUTED, lb), 1.8)

        fa = _window(t, 5.9, 0.8)
        if fa > 0:
            d.text((m, int(H * 0.905)), footnote, font=f_foot,
                   fill=_dim(INK_FAINT, fa))

        base.save(frames_out / fp.name, quality=94)

    subprocess.run([ff, "-y", "-framerate", str(FPS), "-i",
                    str(frames_out / "f_%05d.jpg"),
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18",
                    "-movflags", "+faststart", str(out)],
                   capture_output=True, check=True, timeout=300)

    shutil.rmtree(tmp, ignore_errors=True)
    return out


def _dim(rgb: tuple[int, int, int], a: float) -> tuple[int, int, int]:
    """Fade toward the ground rather than toward black — on a violet field,
    fading to black leaves a grey ghost where the type should be invisible."""
    a = max(0.0, min(1.0, a))
    return tuple(int(GROUND_BASE[i] + (rgb[i] - GROUND_BASE[i]) * a) for i in range(3))
