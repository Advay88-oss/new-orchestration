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
MODEL = "veo-3.1-generate-001"
DURATION_S = 8

MOTION_BRIEF = (
    "ANIMATE THIS EXACT IMAGE. It is the first frame; the video explains it "
    "by bringing its own elements to life.\n"
    "CAMERA: completely locked off. No pan, tilt, dolly, zoom, orbit, drift, "
    "shake, parallax, depth of field or rack focus at any point.\n"
    "MOTION: flat 2D motion-graphics, like a product explainer: panels and "
    "cards settle in, arrows and connectors draw along their path, icons "
    "pulse once, the problem side visibly strains or breaks while Vanna's "
    "side resolves calmly, a soft glow breathes in the background. Smooth, "
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
    row = {"id": digest, "file": dest.name, "score": max(0.0, min(1.0, float(score))),
           "note": " ".join(str(note).split())[:500] or None,
           "prompt": " ".join(str(prompt).split())[:1500] or None,
           "still": str(still) if still else None,
           "at": datetime.now(timezone.utc).isoformat()}
    rows = [r for r in _rows() if r.get("id") != digest] + [row]
    INDEX.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n",
                     encoding="utf-8")
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
    from pipeline.scripts.veo_broll import _find_video, _vertex_token, _write_video

    started = time.time()
    token = _vertex_token()
    if not token:
        raise RuntimeError("no Vertex token; run `gcloud auth application-default login`")
    base = ("https://" + location + "-aiplatform.googleapis.com/v1/projects/" + project
            + "/locations/" + location + "/publishers/google/models/" + MODEL)
    headers = {"Authorization": "Bearer " + token, "x-goog-user-project": project,
               "Content-Type": "application/json"}
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
    body = {"instances": [instance],
            "parameters": {"aspectRatio": "16:9", "sampleCount": 1,
                           "durationSeconds": DURATION_S, "generateAudio": False,
                           "resolution": "1080p"}}
    req = urllib.request.Request(base + ":predictLongRunning",
                                 data=json.dumps(body).encode(), headers=headers,
                                 method="POST")
    op = json.loads(urllib.request.urlopen(req, timeout=120).read())
    name = op.get("name")
    if not name:
        raise RuntimeError("Veo returned no operation: " + json.dumps(op)[:300])
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        time.sleep(15)
        poll = urllib.request.Request(base + ":fetchPredictOperation",
                                      data=json.dumps({"operationName": name}).encode(),
                                      headers=headers, method="POST")
        res = json.loads(urllib.request.urlopen(poll, timeout=90).read())
        if not res.get("done"):
            continue
        if res.get("error"):
            _journal(False, round(time.time() - started, 2), MODEL, "image-to-video failed")
            raise RuntimeError("Veo failed: " + json.dumps(res["error"])[:300])
        b64, uri = _find_video(res)
        if not (b64 or uri) or not _write_video(b64, uri, out, None):
            raise RuntimeError("Veo finished with no usable video")
        _journal(True, round(time.time() - started, 2), MODEL, "image-to-video")
        return out
    raise RuntimeError("Veo did not finish within " + str(int(timeout_s)) + "s")


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
    return R.brain_vision(prompt, [poster] + frames, agent="A09_video_production",
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
    "The FIRST frame is the empty Vanna ground. The LAST frame is the finished "
    "poster. Animate the poster BUILDING ITSELF out of that empty ground, as a "
    "premium product-explainer motion graphic:\n"
    "  1. the soft violet and magenta glows breathe in on the empty ground;\n"
    "  2. the Vanna logo fades up at the top;\n"
    "  3. the headline arrives line by line, the gradient word sweeping in last;\n"
    "  4. the glass cards and panels slide and scale in from nothing, one "
    "after another;\n"
    "  5. inside them the diagram assembles: icons pop in, connectors and "
    "arrows draw along their paths, gauges and bars fill to their values, the "
    "problem side strains while Vanna's side settles;\n"
    "  6. labels and the footer resolve, and everything settles exactly into "
    "the last frame and holds.\n"
    "CAMERA: completely locked off — no pan, tilt, zoom, dolly, orbit, drift, "
    "shake, parallax or depth of field. Everything moves in the flat plane.\n"
    "TEXT: every word, when it appears, is sharp, correctly spelled and "
    "identical to the last frame; never scramble, melt or morph letters. Add "
    "no text, objects, people, coins or scenes that are not in the last frame. "
    "The ground stays Vanna's dark violet-and-magenta throughout."
)


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
        "Check: any text that is visible is sharp and spelled correctly, never "
        "garbled or morphing; the END frame matches the poster; the camera "
        "never moves or zooms; the build reads as a deliberate motion graphic; "
        "nothing appears that is not in the poster. "
        "Verdict rules: REJECT when the END frame's text is wrong or garbled, "
        "the camera moves, or something off-brand (coins, people, a scene) "
        "appears. A typo or an invented icon that shows only MID-build and "
        "resolves by the end is a REVISE, not a REJECT — the founder approved "
        "a clip with exactly that fault. Name every such fault in `fix`. "
        "Return JSON exactly:\n" + JUDGE_SCHEMA)
    return R.brain_vision(prompt, [poster] + frames, agent="A09_video_production",
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
    first = empty_ground(last, out.with_name(out.stem + "_first.png"))
    learned = learned_block()
    history, correction = [], ""
    for n in range(1, attempts + 1):
        head = directed or (BUILD_BRIEF + ("\n\n" + learned if learned else ""))
        prompt = (head
                  + "\n\nWHAT THIS POST SAYS (the build should tell it): "
                  + " ".join(brief.split())[:700]
                  + ("\n\nFIX FROM THE PREVIOUS ATTEMPT: " + correction if correction else ""))
        clip = out.with_name(out.stem + f"_try{n}.mp4")
        _veo(prompt, first, clip, last_frame=last)
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
    return {"final": str(out), "first": str(first), "last": str(last), "attempts": history}


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
