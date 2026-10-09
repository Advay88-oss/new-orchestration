"""Veo 3.1 animates the post's own visual — and learns what the founder likes.

The last A09 direction (motion-direction.md, 2026-09-22) rejected Veo's
cinematic register: dollies through a void, a glowing coin in a vault. What
was asked for was "a simple video explaining the post or visuals we have
created — Vanna colour background, transitions, basic motion graphics". The
answer since then was to hand-describe one flat element per archetype in
code and composite everything else — the same "explain it in code" pattern
the founder rejected for stills.

This is the direct path, the same shape as the posters:

    approved poster ──▶ Veo 3.1 image-to-video ──▶ clip
                              ▲                      │
                              └── retry ◀── judge (frames vs poster)

  * The first frame IS the approved visual, placed on the Vanna ground at
    16:9, so the brand, the logo and every word start correct.
  * Veo animates what is already there — cards arrive, arrows flow, the
    contrast resolves — with the camera locked. It is told what it must not
    touch: the text and the logo stay exactly as drawn.
  * A vision judge reads frames from the start, middle and end against the
    poster: text garbled or changed, camera moved, off-brand motion, a new
    object that was not in the poster. A REJECT is fed back once.
  * It learns: approved clips are stored with the prompt that made them and
    the founder's note; the next prompt carries what worked and every
    correction, so motion the founder liked is what Veo is asked for.

Veo's daily quota is small. Every call here is one clip; nothing retries on
its own beyond the one correction.
"""
from __future__ import annotations

import base64
import hashlib
import json
import shutil
import subprocess
import tempfile
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

REPO = Path(__file__).resolve().parents[2]
EX_DIR = REPO / "pipeline" / "brain" / "video_exemplars"
INDEX = EX_DIR / "exemplars.jsonl"
DURATION_S = 8

MOTION_BRIEF = (
    "ANIMATE THIS EXACT IMAGE. It is the first frame; the video explains it "
    "by bringing its own elements to life.\n"
    "CAMERA: completely locked off. No pan, tilt, dolly, zoom, orbit, drift, "
    "shake, parallax, depth of field or rack focus at any point.\n"
    "MOTION: flat 2D motion-graphics, like a product explainer: the panels and "
    "marks already in the image settle in, arrows and connectors draw along "
    "their path, icons pulse once, the problem side visibly strains or breaks "
    "while Vanna's side resolves calmly. Do not add frosted glass, blur, "
    "a see-through card, or a glowing glass border. Smooth, "
    "restrained, satisfying; every move explains the idea.\n"
    "DO NOT CHANGE: every word, letter and number stays exactly as it is, "
    "sharp and in place, for the whole clip; the Vanna logo at the top stays "
    "exactly as it is. Add no new text, no new objects, no people, no coins, "
    "no currency symbols, no scene outside the frame. The ground stays the "
    "same dark Vanna violet-and-magenta."
)


# --------------------------------------------------------------------------
# Learning
# --------------------------------------------------------------------------

def _rows() -> list[dict]:
    try:
        return [json.loads(l) for l in INDEX.read_text(encoding="utf-8").splitlines()
                if l.strip()]
    except FileNotFoundError:
        return []


def add_exemplar(video: str | Path, *, score: float, note: str = "",
                 prompt: str = "", still: str | Path | None = None) -> dict:
    """Store a founder-rated clip with the prompt that made it."""
    src = Path(video)
    digest = hashlib.sha1(src.read_bytes()).hexdigest()[:12]
    EX_DIR.mkdir(parents=True, exist_ok=True)
    dest = EX_DIR / (digest + ".mp4")
    if not dest.exists():
        shutil.copyfile(src, dest)
    prior = next((r for r in _rows() if r.get("id") == digest), {})
    row = {"id": digest, "file": dest.name, "score": max(0.0, min(1.0, float(score))),
           "note": " ".join(str(note).split())[:500] or None,
           "prompt": " ".join(str(prompt).split())[:1500] or None,
           "still": str(still) if still else None,
           "at": datetime.now(timezone.utc).isoformat()}
    # Re-rating a clip keeps a longer note already written for it: approving
    # the run behind the benchmark replaced its detailed description with a
    # one-line "approved", and the description is what Veo learns from.
    if prior.get("note") and len(prior["note"]) > len(row["note"] or ""):
        row["note"] = prior["note"]
    row["prompt"] = row["prompt"] or prior.get("prompt")
    rows = [r for r in _rows() if r.get("id") != digest] + [row]
    INDEX.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n",
                     encoding="utf-8")
    # Into the brand brain's visual memory, as the clip's last frame.
    try:
        from pipeline.brand_brain.client import current_tenant
        from pipeline.brand_brain.onboard import _still, remember_image
        from pipeline.brand_brain.store import tenant_dir
        d = tenant_dir(current_tenant()) / "stills"
        d.mkdir(parents=True, exist_ok=True)
        st = _still(dest, d / (digest + "_last.png"))
        if st:
            remember_image(st, kind="video_still", score=row["score"], note=row["note"] or "",
                           source=str(dest))
    except Exception:                               # noqa: BLE001 — boundary
        pass
    return row


def learned_block() -> str:
    """What the founder approved and sent back, for the next Veo prompt."""
    rows = _rows()
    if not rows:
        return ""
    good = sorted([r for r in rows if r.get("score", 0) >= 0.7],
                  key=lambda r: (r["score"], r["at"]), reverse=True)[:3]
    bad = sorted([r for r in rows if r.get("score", 0) < 0.5 and r.get("note")],
                 key=lambda r: r["at"], reverse=True)[:5]
    lines = ["FOUNDER'S RECORD ON PAST CLIPS — follow it."]
    if good:
        lines.append("Approved motion (do more of this):")
        lines += ["  - " + (r.get("note") or "approved") for r in good]
    if bad:
        lines.append("Rejected (never repeat):")
        lines += ["  - " + r["note"] for r in bad]
    return "\n".join(lines) if len(lines) > 1 else ""


# --------------------------------------------------------------------------
# Frame in, clip out
# --------------------------------------------------------------------------

def first_frame(poster: Path, out: Path, size=(1920, 1080)) -> Path:
    """The square poster on the Vanna ground at 16:9, edges feathered so it
    reads as one frame, not a card pasted on a background."""
    from PIL import Image, ImageEnhance, ImageFilter

    W, H = size
    p = Image.open(poster).convert("RGB")
    side = H
    p = p.resize((side, side), Image.Resampling.LANCZOS)
    # The sides are the poster's own outermost columns — pure ground —
    # stretched outward. A separately drawn ground was brighter than the
    # poster's and read as a column; a blurred copy of the whole poster kept
    # the ghost of its content (a big "1.10x" became a soft grey shape) and
    # Veo animated that shape as an object — the judge rejected the clip for
    # a "blurred silhouette" on the left.
    pad = (W - side) // 2
    strip = max(4, side // 120)
    left = p.crop((0, 0, strip, side)).resize((pad, side), Image.Resampling.BICUBIC)
    right = p.crop((side - strip, 0, side, side)).resize((W - side - pad, side),
                                                          Image.Resampling.BICUBIC)
    canvas = Image.new("RGB", (W, H))
    canvas.paste(left, (0, 0))
    canvas.paste(right, (pad + side, 0))
    canvas = ImageEnhance.Brightness(canvas.filter(ImageFilter.GaussianBlur(40))).enhance(0.9)
    mask = Image.new("L", (side, side), 255)
    feather = int(side * 0.06)
    edge = Image.new("L", (side, side), 0)
    edge.paste(255, (feather, 0, side - feather, side))
    mask = edge.filter(ImageFilter.GaussianBlur(feather * 0.6))
    canvas.paste(p, ((W - side) // 2, 0), mask)
    out.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(out)
    return out


def _veo(prompt: str, image: Path, out: Path, *, project: str = "vanna-mcp",
         location: str = "us-central1", timeout_s: float = 480.0,
         last_frame: Optional[Path] = None) -> Path:
    from pipeline.gtm_creative.motion import _journal
    from pipeline.scripts.gemini_flash_image import media_project
    from pipeline.scripts.veo_broll import _find_video, _write_video, run_veo

    project = media_project(project)
    started = time.time()
    instance: dict[str, Any] = {"prompt": prompt, "image": {
        "bytesBase64Encoded": base64.b64encode(image.read_bytes()).decode(),
        "mimeType": "image/png"}}
    if last_frame is not None:
        # First and last frame both fixed: Veo animates what happens between
        # them and must land exactly on the finished poster, which is what
        # keeps the words intact at the end.
        instance["lastFrame"] = {
            "bytesBase64Encoded": base64.b64encode(last_frame.read_bytes()).decode(),
            "mimeType": "image/png"}
    params = {"aspectRatio": "16:9", "sampleCount": 1, "durationSeconds": DURATION_S,
              "generateAudio": False, "resolution": "1080p"}
    from pipeline.gtm_os.agent_runtime import MODELS
    model = MODELS["video"]
    res, key, via = run_veo(model, instance, params, project=project,
                             location=location, timeout_s=timeout_s)
    if res.get("error"):
        _journal(False, round(time.time() - started, 2), model, "image-to-video failed", transport=via)
        raise RuntimeError("Veo failed: " + json.dumps(res["error"])[:300])
    b64, uri = _find_video(res)
    if not (b64 or uri) or not _write_video(b64, uri, out, key):
        raise RuntimeError("Veo finished with no usable video")
    _journal(True, round(time.time() - started, 2), model, "image-to-video", transport=via)
    return out


def _frames(mp4: Path, at: tuple[float, ...] = (0.4, 4.0, 7.6)) -> list[Path]:
    exe = shutil.which("ffmpeg") or "ffmpeg"
    tmp = Path(tempfile.mkdtemp())
    out = []
    for i, t in enumerate(at):
        f = tmp / f"f{i}.jpg"
        subprocess.run([exe, "-y", "-loglevel", "error", "-ss", str(t), "-i", str(mp4),
                        "-frames:v", "1", "-q:v", "2", str(f)], check=True, timeout=60)
        out.append(f)
    return out


JUDGE_SCHEMA = ('{"text_intact": bool, "logo_intact": bool, "camera_locked": bool, '
                '"motion_explains": bool, "new_objects": [str], "verdict": '
                '"SHIP"|"REVISE"|"REJECT", "critique": str, "fix": str}')


def judge(mp4: Path, poster: Path, brief: str) -> dict[str, Any]:
    from pipeline.gtm_os import agent_runtime as R

    frames = _frames(mp4)
    prompt = (
        "The FIRST image is the approved poster the clip must animate. The next "
        "three are frames from the clip at the start, middle and end.\n\n"
        "The post: " + brief[:600] + "\n\n"
        "Check: every word and number in the frames is still sharp, correctly "
        "spelled and the same as the poster (garbled, melting, changed or "
        "added text is a REJECT); the Vanna logo is unchanged; the camera did "
        "not move or zoom; the motion explains the idea rather than just "
        "wobbling; no new objects, people, coins or scenes appeared. "
        "Return JSON exactly:\n" + JUDGE_SCHEMA)
    return R.brain_vision(prompt, [poster] + frames, agent="A15_creative_judge",
                          system="You review a short brand video before a human sees it. "
                                 "Be strict and specific. Return strict JSON.",
                          role="reasoning", temperature=0.1, max_output_tokens=2048)


def make(poster: str | Path, brief: str, out: str | Path, *,
         attempts: int = 2) -> dict[str, Any]:
    """Poster in, judged clip out. Returns every attempt with its verdict."""
    poster, out = Path(poster), Path(out)
    frame = first_frame(poster, out.with_name(out.stem + "_frame.png"))
    learned = learned_block()
    history, correction = [], ""
    for n in range(1, attempts + 1):
        prompt = (MOTION_BRIEF
                  + ("\n\n" + learned if learned else "")
                  + "\n\nWHAT THIS POST SAYS (the motion should explain it): "
                  + " ".join(brief.split())[:700]
                  + ("\n\nFIX FROM THE PREVIOUS ATTEMPT: " + correction if correction else ""))
        clip = out.with_name(out.stem + f"_try{n}.mp4")
        _veo(prompt, frame, clip)
        try:
            v = judge(clip, poster, brief)
        except Exception as exc:                    # noqa: BLE001 — boundary
            v = {"verdict": "UNJUDGED", "fix": str(exc)[:200]}
        history.append({"path": str(clip), "prompt": prompt, **v})
        if str(v.get("verdict")).upper() == "SHIP":
            break
        correction = str(v.get("fix") or "")
    best = next((h for h in history if str(h.get("verdict")).upper() == "SHIP"), history[-1])
    shutil.copyfile(best["path"], out)
    return {"final": str(out), "frame": str(frame), "attempts": history}


# --------------------------------------------------------------------------
# Build mode — the poster assembling itself out of the empty ground
# --------------------------------------------------------------------------

BUILD_BRIEF = (
    "The FIRST frame is the empty {company} ground. The LAST frame is the finished "
    "poster. Animate the poster BUILDING ITSELF out of that empty ground, as a "
    "premium product-explainer motion graphic:\n"
    "  1. the soft glows of the brand ground breathe in on the empty ground;\n"
    "  2. the {company} logo fades up at the top;\n"
    "  3. cards, panels and marks slide and scale in from nothing, one "
    "after another, keeping the surface of the finished poster "
    "(do not add frost or glass if the last frame has none);\n"
    "  4. inside them the diagram assembles: icons pop in, connectors and "
    "arrows draw along their paths, gauges and bars fill to their values, the "
    "problem side strains while {company}'s side settles;\n"
    "  5. everything settles exactly into the last frame and holds.\n"
    "CAMERA: completely locked off — no pan, tilt, zoom, dolly, orbit, drift, "
    "shake, parallax or depth of field. Everything moves in the flat plane.\n"
    "LETTERS: draw none. Do not write, type, reveal, fade or morph any letter, "
    "word, numeral or logo — a previous clip spelled 'actually deploy it' as "
    "'acilly deppe it'. Words are composited afterwards. Add no objects, "
    "people, coins or scenes that are not in the last frame. "
    "The ground stays {company}'s {video_ground} throughout."
)


def _build_brief() -> str:
    from pipeline.brand_brain import context as C
    return C.fill(BUILD_BRIEF).replace("{video_ground}", C.rule("video_ground") or "own ground colours")


def letter_mask(im):
    """Type, not hairlines. A 1px rule is dropped; a letter is kept and grown
    enough to cover the misspelled glyph Veo puts in the same place."""
    from PIL import Image, ImageFilter
    import numpy as np

    lum = np.asarray(im.convert("L"), dtype=np.int16)
    soft = np.asarray(im.convert("L").filter(ImageFilter.BoxBlur(1)), dtype=np.int16)
    ink = np.abs(lum - soft) > 16
    mask = Image.fromarray(np.where(ink, 255, 0).astype("uint8"), "L")
    mask = mask.filter(ImageFilter.MinFilter(3))
    mask = mask.filter(ImageFilter.MaxFilter(7))
    return mask.filter(ImageFilter.GaussianBlur(0.6))


def without_letters(frame: Path, out: Path) -> Path:
    """The poster with its words dissolved, so Veo is not asked to draw them."""
    from PIL import Image, ImageFilter

    im = Image.open(frame).convert("RGB")
    ground = im.filter(ImageFilter.GaussianBlur(14))
    im.paste(ground, mask=letter_mask(im))
    out.parent.mkdir(parents=True, exist_ok=True)
    im.save(out)
    return out


def stamp_poster_text(clip: Path, plate: Path, out: Path) -> Path:
    """Paint the plate's real letters over every frame of the clip."""
    from PIL import Image

    exe = shutil.which("ffmpeg") or "ffmpeg"
    probe = shutil.which("ffprobe") or "ffprobe"
    meta = subprocess.run(
        [probe, "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=width,height", "-of", "json", str(clip)],
        capture_output=True, text=True, timeout=30, check=True)
    st = json.loads(meta.stdout)["streams"][0]
    w, h = int(st["width"]), int(st["height"])
    im = Image.open(plate).convert("RGB")
    if im.size != (w, h):
        im = im.resize((w, h), Image.Resampling.LANCZOS)
    rgba = im.convert("RGBA")
    rgba.putalpha(letter_mask(im))
    overlay = out.with_name(out.stem + "_type.png")
    rgba.save(overlay)
    # Letters fade in whole, late, once the shapes have settled. Painting
    # them from the first frame floats labels over a layout that is still moving.
    subprocess.run(
        [exe, "-y", "-loglevel", "error", "-i", str(clip), "-loop", "1", "-i", str(overlay),
         "-filter_complex",
         "[1:v]format=rgba,fade=t=in:st=5.2:d=1.3:alpha=1[ov];"
         "[0:v][ov]overlay=0:0:format=auto:shortest=1",
         "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "16", "-an", str(out)],
        check=True, timeout=300)
    return out


def empty_ground(frame: Path, out: Path) -> Path:
    """The last frame with every element dissolved: only its own glow and
    ground remain, so the build starts from the same light it ends in."""
    from PIL import Image, ImageEnhance, ImageFilter

    img = Image.open(frame).convert("RGB")
    ground = ImageEnhance.Brightness(img.filter(ImageFilter.GaussianBlur(160))).enhance(0.72)
    ground.save(out)
    return out


def _hold(clip: Path, out: Path, total_s: float) -> Path:
    """Hold the final frame so the clip runs total_s — reading time for the
    finished poster. Veo 3.1 renders at most 8 seconds per clip."""
    exe = shutil.which("ffmpeg") or "ffmpeg"
    extra = max(0.0, total_s - DURATION_S)
    subprocess.run([exe, "-y", "-loglevel", "error", "-i", str(clip),
                    "-vf", "tpad=stop_mode=clone:stop_duration=" + str(extra),
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "16",
                    "-an", str(out)], check=True, timeout=180)
    return out


def judge_build(mp4: Path, poster: Path, brief: str) -> dict[str, Any]:
    """A build clip is judged on how it builds and where it lands."""
    from pipeline.gtm_os import agent_runtime as R

    frames = _frames(mp4, at=(1.5, 4.0, 6.0, 7.8))
    prompt = (
        "The FIRST image is the finished poster the clip must build. The next "
        "four are frames from the clip at 1.5s, 4s, 6s and the end.\n\n"
        "The post: " + brief[:600] + "\n\n"
        "Elements appearing progressively is EXPECTED in the early frames. "
        "Words are composited from the poster, so any letter that is visible "
        "must match the poster exactly. "
        "Verdict rules: REJECT when ANY frame shows a misspelled, melted, "
        "duplicated or invented word (mid-clip garbage is a REJECT, even if "
        "the end frame recovers). Also REJECT when the camera moves or "
        "something off-brand (coins, people, a scene) appears. "
        "Name every such fault in `fix`. "
        "Return JSON exactly:\n" + JUDGE_SCHEMA)
    return R.brain_vision(prompt, [poster] + frames, agent="A15_creative_judge",
                          system="You review a short brand video before a human sees it. "
                                 "Be strict and specific. Return strict JSON.",
                          role="reasoning", temperature=0.1, max_output_tokens=2048)


def make_build(poster: str | Path, brief: str, out: str | Path, *,
               total_s: float = 10.0, attempts: int = 1,
               directed: Optional[str] = None) -> dict[str, Any]:
    """Empty ground in, finished poster out: the video of the poster building.

    `directed` is the Motion Director's prompt for this poster (guard rails,
    its own beat-by-beat build and the founder's record). Without it the
    generic build brief is used.
    """
    poster, out = Path(poster), Path(out)
    last = first_frame(poster, out.with_name(out.stem + "_last.png"))
    # Veo interpolates toward the last frame. If that frame contains words,
    # the middle of the clip is Veo inventing the spelling. It builds a
    # wordless plate; the real letters are painted on afterwards.
    bare = without_letters(last, out.with_name(out.stem + "_bare.png"))
    first = empty_ground(bare, out.with_name(out.stem + "_first.png"))
    learned = learned_block()
    history, correction = [], ""
    for n in range(1, attempts + 1):
        head = directed or (_build_brief() + ("\n\n" + learned if learned else ""))
        prompt = (head
                  + "\n\nWHAT THIS POST SAYS (the build should tell it): "
                  + " ".join(brief.split())[:700]
                  + ("\n\nFIX FROM THE PREVIOUS ATTEMPT: " + correction if correction else ""))
        clip = out.with_name(out.stem + f"_try{n}.mp4")
        _veo(prompt, first, clip, last_frame=bare)
        stamped = out.with_name(out.stem + f"_try{n}_sharp.mp4")
        stamp_poster_text(clip, last, stamped)
        clip = stamped
        # One retry on a failed judge call: a dropped connection left a clip
        # UNJUDGED, and an unjudged clip was then chosen as the final video.
        v = None
        for _ in range(2):
            try:
                v = judge_build(clip, poster, brief)
                break
            except Exception as exc:                # noqa: BLE001 — boundary
                v = {"verdict": "UNJUDGED", "fix": str(exc)[:200]}
                time.sleep(5)
        history.append({"path": str(clip), "prompt": prompt, **v})
        if str(v.get("verdict")).upper() == "SHIP":
            break
        correction = str(v.get("fix") or "")
    rank = {"SHIP": 0, "REVISE": 1}
    best = min(history, key=lambda h: rank.get(str(h.get("verdict")).upper(), 2))
    _hold(Path(best["path"]), out, total_s)
    # `chosen` is the attempt now in `out`; the caller judges that one, not the last.
    return {"final": str(out), "first": str(first), "last": str(last), "attempts": history,
            "chosen": history.index(best)}


def main(argv: Optional[list] = None) -> int:
    import argparse
    ap = argparse.ArgumentParser(description="Rate a Veo clip so A09 learns from it.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("add")
    a.add_argument("video")
    a.add_argument("--score", type=float, required=True)
    a.add_argument("--note", default="")
    a.add_argument("--prompt", default="")
    sub.add_parser("list")
    args = ap.parse_args(argv)
    if args.cmd == "add":
        print(json.dumps(add_exemplar(args.video, score=args.score, note=args.note,
                                      prompt=args.prompt), ensure_ascii=False))
    else:
        print(json.dumps({"exemplars": _rows(), "prompt_block": learned_block()},
                         indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
