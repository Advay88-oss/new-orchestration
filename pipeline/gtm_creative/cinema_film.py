"""The agents' cinematic film: Veo 3.1 animates between frames whose words are already right.

The founder liked a Veo text-to-video clip for its look — a glossy phone, a
finger tapping the button, a glowing ring around the asset, soft violet light —
and rejected its mistakes: "Earn Kamiino yeed", "Route sumpiuiry", invented
numbers, no real logo. Text-to-video draws every letter itself, so it melts
them. Here no letter is left to Veo:

  Motion/Art Director (A14, "director" model)
    sees the liked clip's frames (video exemplars with style "cinema") and
    writes three shots: every string on screen, from the brand brain's facts
    only, what each keyframe shows, how the shot ends and what moves.
  Visual agent (A08, MODELS["poster"] — Nano Banana 2.1)
    draws each keyframe in the liked clip's look with the director's exact
    strings; a shot that ends differently (the tap's confirmation) gets its
    end frame drawn as an edit of the start. The real logo is pasted, and a
    judge rejects any misspelled or invented text before Veo is paid.
  Veo 3.1 (A09, MODELS["video"])
    animates each shot between its start and end keyframes: the finger, the
    ring, the light.
  Typesetting (code)
    paints the keyframes' own letters back over every Veo frame, except where
    something has moved over them (the finger), so small text cannot melt.
  Editor + creative judge (A15)
    retimes and joins the shots with the director's transitions; the judge
    checks sampled frames for the strings and the hand.

    python -m pipeline.gtm_creative.cinema_film "post brief" --name farm
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Optional

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "exports" / "agent-posts" / "video" / "cinema"
W, H, FPS = 1920, 1080, 30
XFADES = ("fade", "smoothleft", "smoothright", "smoothup", "wipeleft", "circleopen", "fadeblack", "slideleft")
NEGATIVE = ("new text, changing letters, garbled words, extra numbers, misspelled words, extra fingers, "
            "deformed hand, cartoon hand, extra phones, new screens, extra cards, logo, watermark, "
            "camera movement, zoom, cut, flicker")

SCHEMA = (
    '{"shots": [{"id": str, "use_s": float (seconds this shot keeps in the edit), "frame": str (what the '
    'start keyframe shows: composition, objects, light; concrete), "text": [str] (EVERY string readable in '
    'the start keyframe, exact, in reading order), "end_frame": str (the same frame at the shot\'s end — '
    'only what has changed; "" when nothing but light moves), "end_text": [str] (every string readable at '
    'the end; [] when end_frame is ""), "motion": str (the Veo prompt: what moves between the two frames; '
    'names no words, letters or numbers), "transition": str (into the next shot; one of ' + ", ".join(XFADES)
    + ')}] (exactly 3), "poster": str (the id of the shot whose keyframe is the post\'s poster)}')


def _rel(p: Path) -> str:
    try:
        return str(p.relative_to(ROOT))
    except ValueError:
        return str(p)


# --------------------------------------------------------------------------
# What the founder liked
# --------------------------------------------------------------------------

def style_refs(n: int = 3) -> tuple[list[Path], str]:
    """Frames of the best-rated "cinema" exemplar and its note."""
    from pipeline.gtm_creative import veo_video as VV
    rows = sorted((r for r in VV._rows() if r.get("style") == "cinema"),
                  key=lambda r: -float(r.get("score") or 0))
    if not rows:
        raise RuntimeError("no video exemplar with style 'cinema' — rate one first (veo_video add_exemplar)")
    row = rows[0]
    clip = VV.EX_DIR / row["file"]
    dest = OUT / "refs" / row["id"]
    dest.mkdir(parents=True, exist_ok=True)
    exe = shutil.which("ffmpeg") or "ffmpeg"
    frames = []
    for i in range(n):
        f, clean = dest / f"ref_{i}.jpg", dest / f"ref_{i}_clean.png"
        if not f.exists():
            t = 8.0 * (0.12 + 0.76 * i / max(1, n - 1))
            subprocess.run([exe, "-y", "-loglevel", "error", "-ss", f"{t:.2f}", "-i", str(clip),
                            "-frames:v", "1", "-q:v", "2", str(f)], check=True, timeout=60)
        # The liked clip's words are misspelled ("Earn Kamiino yeed"); with them
        # in the reference the image model copied "Kamiino" into a sign-off
        # that asked for "Kamino". The look goes in, the letters do not.
        if not clean.exists():
            VV.without_letters(f, clean)
        frames.append(clean)
    return frames, str(row.get("note") or "")


def _logo() -> Optional[Path]:
    """The sharpest copy of the tenant's real logo."""
    from pipeline.brand_brain import context as C
    from pipeline.brand_brain.client import current_tenant
    found = [p for p in [C.logo_path()] if p and Path(p).exists()]
    found += sorted((ROOT / "pipeline" / "assets" / "logos").glob(current_tenant() + "*.png"))
    if not found:
        return None
    return max(found, key=lambda p: Image.open(p).size[0])


def paste_logo(path: Path) -> None:
    """The real logo, top-left, at the same place in every keyframe."""
    src = _logo()
    if not src:
        return
    im = Image.open(path).convert("RGB")
    logo = Image.open(src).convert("RGBA")
    bbox = logo.getchannel("A").point(lambda a: 255 if a > 8 else 0).getbbox()
    if bbox:
        logo = logo.crop(bbox)
    w = int(im.width * 0.085)
    logo = logo.resize((w, max(1, int(logo.height * w / logo.width))), Image.Resampling.LANCZOS)
    im.paste(logo, (int(im.width * 0.034), int(im.height * 0.05)), logo)
    im.save(path)


# --------------------------------------------------------------------------
# A14 — the director
# --------------------------------------------------------------------------

def direct(brief: str, refs: list[Path], note: str, *, run_id: Optional[str] = None) -> dict:
    from pipeline.brand_brain import context as C
    from pipeline.gtm_os import agent_runtime as R
    system = C.fill(
        "You are {company}'s Motion/Art Director. You direct a short cinematic product film that Veo 3.1 "
        "animates between keyframes the visual agent draws. You write every word on screen. Strict JSON only.")
    prompt = (
        C.facts_block(brief, k=6, excerpts=3) + "\n\n----\n\n"
        "THE POST: " + " ".join(brief.split())[:900] + "\n\n"
        "THE LOOK: the attached frames are from a film the founder liked. What they said about it: " + note
        + "\nKeep its look and its kind of shots — the hero object, the phone moment with a real tap, the "
        "sign-off — but its words are wrong: never reuse any of its text or numbers.\n\n"
        "Direct three shots, in the film's order. RULES:\n"
        "- every string comes from the facts above or the post; a number inside the app is sample data, and "
        "a footer string says so with the deployment named in the facts;\n"
        "- few words: a frame holds at most 12 strings and none longer than 6 words, each big enough to read "
        "at 1080p — tiny labels are what Veo melts;\n"
        "- the phone shot shows a realistic smartphone and a realistic human finger: it starts with the finger "
        "about to touch the main button and ends with the finger lifting and the confirmation shown beside "
        "the phone;\n"
        "- leave the top-left corner empty: the real logo is placed there; never ask for a logo;\n"
        "- the camera is locked off in every shot; motion is the finger, the light, the ring, the UI settling;\n"
        "- use_s: 2.5-4.5 each, the phone shot longest; never name a competitor.\n\n"
        "Return JSON: " + SCHEMA)
    spec = R.brain_vision(prompt, refs, agent="A14_motion_director", role="director", system=system,
                          temperature=0.4, max_output_tokens=4096, run_id=run_id)
    shots = spec.get("shots") if isinstance(spec, dict) else None
    if not isinstance(shots, list) or len(shots) < 3:
        raise RuntimeError("director returned no three shots")
    for s in shots[:3]:
        s["use_s"] = max(2.0, min(5.0, float(s.get("use_s") or 3.0)))
        s["text"] = [str(t) for t in s.get("text") or []]
        s["end_text"] = [str(t) for t in s.get("end_text") or []]
        if s.get("transition") not in XFADES:
            s["transition"] = "fade"
    spec["shots"] = shots[:3]
    R.record_decision("A14_motion_director", "cinema_spec", {"spec": spec}, run_id=run_id)
    return spec


# --------------------------------------------------------------------------
# A08 — keyframes
# --------------------------------------------------------------------------

def _key_prompt(frame: str, text: list[str], fix: str, *, edit: bool) -> str:
    from pipeline.brand_brain import context as C
    pal = C.palette()
    head = ("Image 1 is this shot's start frame. Return the SAME frame — identical composition, phone, "
            "position, light, text and type — with only this change: " + frame + "\n"
            "Images 2 onward are the founder's liked film, for the look only.\n") if edit else (
            "Make one 16:9 frame of a premium cinematic product film for " + C.company_name() + ". "
            "The images are frames of a film the founder liked: match their look — deep near-black ground, "
            "soft violet and magenta light, glossy realistic objects with depth and reflections, a bold "
            "geometric sans. Their words are wrong: never copy any text or number from them.\n"
            "THIS FRAME: " + frame + "\n")
    return (head
            + "BRAND: ground " + pal.get("ground", "") + ", accents " + pal.get("accent", "") + " and "
            + pal.get("risk", "") + ", emphasis words in a " + pal.get("gradient_word", "") + " gradient, "
            "font like " + C.fonts().get("display", "") + ".\n"
            "TEXT — exactly these strings, spelled exactly, and NOTHING else readable anywhere (no extra "
            "labels, numbers, icons with letters, status-bar text): " + " | ".join(text) + "\n"
            "Every string large and sharp. The top-left corner stays empty: draw no logo anywhere. A hand, "
            "if any, is a realistic human hand with five fingers."
            + ("\nFIX THESE PROBLEMS FROM THE LAST TRY:\n" + fix if fix else ""))


def _norm(t: str) -> str:
    import re
    return re.sub(r"[^a-z0-9&%.$]+", " ", str(t).lower()).strip(" .")


def judge_key(path: Path, text: list[str], frame: str) -> dict:
    """The judge reads the frame; code compares what it read with the
    director's strings. Asked only "is everything spelled right?", the model
    passed "Earn Kamiino yield." for "Earn Kamino yield."."""
    from pipeline.brand_brain import context as C
    from pipeline.gtm_os import agent_runtime as R
    im = Image.open(path).convert("RGB")
    w, h = im.size
    left, right = path.with_name(path.stem + "_L.jpg"), path.with_name(path.stem + "_R.jpg")
    im.crop((0, 0, w // 2 + w // 40, h)).save(left, quality=92)
    im.crop((w // 2 - w // 40, 0, w, h)).save(right, quality=92)
    v = R.brain_vision(
        "Image 1 is a keyframe of a product film; images 2 and 3 are its halves. FIRST transcribe every "
        "readable string in the frame exactly as drawn, letter by letter — do not correct spelling, do not "
        "guess what was meant; include the logo's wordmark and any small label. THEN judge the look (the "
        "logo in the top-left corner is placed there on purpose and is correct): it "
        "should show " + frame + "; any hand is realistic with five fingers; it reads as one cinematic frame. "
        'Return JSON: {"seen": [str], "look_ok": bool, "look_fixes": [str], "score": int (0-10)}',
        [path, left, right], agent="A15_creative_judge", role="reasoning", temperature=0.0,
        max_output_tokens=1536)
    seen = [_norm(x) for x in (v.get("seen") or []) if _norm(x)]
    blob = " | ".join(seen) + " | " + " ".join(seen)     # a headline set on two lines is still one string
    need = [t for t in text if _norm(t)]
    missing = [t for t in need if _norm(t) not in blob]
    allowed = [_norm(t) for t in need] + [_norm(C.company_name())]
    extra = [x for x in seen if not any(x in a or a in x for a in allowed)]
    fixes = (['write exactly "' + t + '" (it is missing or misspelled)' for t in missing]
             + ['remove the text "' + x + '": it is not in the script' for x in extra]
             + ([str(x) for x in v.get("look_fixes") or []] if not v.get("look_ok", True) else []))
    ok = not missing and not extra and bool(v.get("look_ok", True))
    return {"score": int(v.get("score") or 0), "seen": v.get("seen"), "fixes": fixes,
            "verdict": "SHIP" if ok else "REVISE"}


def keyframe(name: str, frame: str, text: list[str], refs: list[Path], *, start: Optional[Path] = None,
             attempts: int = 3) -> dict:
    from pipeline.gtm_os import agent_runtime as R
    from pipeline.scripts.gemini_flash_image import generate_gemini_image
    final = OUT / "keys" / f"{name}.png"
    if final.exists():                              # a kept frame is judged again, for free
        v = judge_key(final, text, frame)
        if v["verdict"] == "SHIP":
            return {"path": final, "tries": [{"path": str(final), **v}]}
    done = len(list((OUT / "keys").glob(name + "_try*.png")))
    tries, fix = [], ""
    for k in range(done + 1, done + attempts + 1):
        path = OUT / "keys" / f"{name}_try{k}.png"
        images = ([start] if start else []) + list(refs)
        for size in (os.environ.get("VANNA_POSTER_SIZE", "4K"), "2K"):
            try:
                generate_gemini_image(prompt=_key_prompt(frame, text, fix, edit=bool(start)), output_path=path,
                                      model=R.MODELS["poster"], temperature=0.3, images=images,
                                      aspect_ratio="16:9", image_size=size)
                break
            except Exception:                       # noqa: BLE001 — 4K refused: 2K, then fail
                if size == "2K":
                    raise
        paste_logo(path)
        try:
            v = judge_key(path, text, frame)
        except Exception as exc:                    # noqa: BLE001 — unjudged never counts as shipped
            v = {"score": 0, "fixes": ["judge failed: " + str(exc)[:120]], "verdict": "UNJUDGED"}
        tries.append({"path": str(path), **v})
        if str(v.get("verdict")).upper() == "SHIP":
            break
        fix = "\n".join("- " + str(x) for x in (v.get("fixes") or [])[:8])
    best = max(tries, key=lambda t: (str(t.get("verdict")).upper() == "SHIP", int(t.get("score") or 0)))
    if str(best.get("verdict")).upper() != "SHIP":
        # Veo animates what it is given: a wrong word in a keyframe is a wrong
        # word in the film, so no Veo money is spent on it.
        raise RuntimeError(name + ": no keyframe passed: " + "; ".join(best.get("fixes") or [])[:400])
    final.write_bytes(Path(best["path"]).read_bytes())
    return {"path": final, "tries": tries}


def _frame_1080(src: Path) -> Path:
    out = src.with_name(src.stem + "_1080.png")
    Image.open(src).convert("RGB").resize((W, H), Image.Resampling.LANCZOS).save(out)
    return out


# --------------------------------------------------------------------------
# A09 — Veo between keyframes
# --------------------------------------------------------------------------

def animate(motion: str, start: Path, end: Path, out: Path) -> Path:
    import base64
    import time
    from pipeline.gtm_creative.motion import _journal
    from pipeline.gtm_os.agent_runtime import MODELS
    from pipeline.scripts.veo_broll import _find_video, _write_video, run_veo

    def img(p: Path) -> dict:
        return {"bytesBase64Encoded": base64.b64encode(p.read_bytes()).decode(), "mimeType": "image/png"}
    t = time.time()
    prompt = (motion + " Cinematic, smooth and eased; the camera stays completely locked off. Every word and "
              "number stays exactly as in the first frame, sharp and in place; nothing new is written.")
    params = {"aspectRatio": "16:9", "sampleCount": 1, "durationSeconds": 8, "generateAudio": False,
              "resolution": "1080p", "negativePrompt": NEGATIVE}
    res, key, via = run_veo(MODELS["video"], {"prompt": prompt, "image": img(start), "lastFrame": img(end)},
                            params, project="vanna-mcp", location="us-central1", timeout_s=600)
    if res.get("error"):
        _journal(False, round(time.time() - t, 2), MODELS["video"], "cinema shot failed", transport=via)
        raise RuntimeError("Veo failed: " + json.dumps(res["error"])[:300])
    b64, uri = _find_video(res)
    if not (b64 or uri) or not _write_video(b64, uri, out, key):
        raise RuntimeError("Veo returned no video")
    _journal(True, round(time.time() - t, 2), MODELS["video"], "cinema shot", transport=via)
    return out


# --------------------------------------------------------------------------
# Typesetting — the keyframes' letters over Veo's frames
# --------------------------------------------------------------------------

def _small(a, f: int = 8):
    import numpy as np
    h, w = a.shape[0] // f * f, a.shape[1] // f * f
    return a[:h, :w].reshape(h // f, f, w // f, f, -1).mean(axis=(1, 3)).astype(np.float32)


def _up(m, shape):
    import numpy as np
    from PIL import ImageFilter
    im = Image.fromarray(np.clip(m, 0, 255).astype("uint8"), "L").filter(ImageFilter.GaussianBlur(1.2))
    return np.asarray(im.resize((shape[1], shape[0]), Image.Resampling.BILINEAR), dtype=np.float32)


def stamp(clip: Path, keys: list[Path], out: Path, *, thr: float = 34.0) -> Path:
    """Each pixel of a keyframe's letters goes back over the frame where the
    frame still looks like that keyframe there (an 8-px block average), so a
    melted letter is replaced and a finger passing over one is left alone.

    A frame whose letters match a keyframe better when the keyframe is shifted
    a few pixels is one where Veo moved the layout (the phone's screen
    scrolled mid-shot and every label showed twice): it is cut, not painted
    over. A finger or a ripple hides letters; shifting never brings them back."""
    import numpy as np
    from pipeline.gtm_creative.veo_video import letter_mask
    exe = shutil.which("ffmpeg") or "ffmpeg"
    kim = [Image.open(k).convert("RGB").resize((W, H), Image.Resampling.LANCZOS) for k in keys]
    karr = [np.asarray(k, dtype=np.float32) for k in kim]
    ksmall = [_small(k) for k in karr]
    kmask = [np.asarray(letter_mask(k), dtype=np.float32) / 255.0 for k in kim]
    holds = _drift(clip, karr, kmask, thr)
    med = float(np.median(holds)) if holds else 0.0
    drop = {i for i, g in enumerate(holds) if g > med + 0.1}
    drop |= {i + d for i in drop for d in (-1, 1)}
    dec = subprocess.Popen([exe, "-loglevel", "error", "-i", str(clip), "-vf", f"scale={W}:{H}",
                            "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    enc = subprocess.Popen([exe, "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                            "-s", f"{W}x{H}", "-r", "24", "-i", "-", "-c:v", "libx264", "-pix_fmt", "yuv420p",
                            "-crf", "15", str(out)], stdin=subprocess.PIPE)
    n, i = W * H * 3, -1
    while True:
        buf = dec.stdout.read(n)
        if len(buf) < n:
            break
        i += 1
        if i in drop:
            continue
        f = np.frombuffer(buf, np.uint8).reshape(H, W, 3).astype(np.float32)
        fs = _small(f)
        best_d, best_a, best_k = None, None, None
        for k, ks, km in zip(karr, ksmall, kmask):
            d = _up(np.abs(fs - ks).mean(axis=2), (H, W))
            a = km * np.clip((thr - d) / 12.0, 0, 1)
            if best_d is None:
                best_d, best_a, best_k = d, a, np.broadcast_to(k, k.shape)
            else:
                take = d < best_d
                best_a = np.where(take, a, best_a)
                best_k = np.where(take[..., None], k, best_k)
                best_d = np.minimum(d, best_d)
        a = best_a[..., None]
        enc.stdin.write((f * (1 - a) + best_k * a).astype(np.uint8).tobytes())
    enc.stdin.close()
    enc.wait(timeout=300)
    dec.wait(timeout=60)
    (out.with_suffix(".cut.json")).write_text(json.dumps({"dropped": sorted(x for x in drop if 0 <= x < len(holds)),
                                                         "frames": len(holds)}), encoding="utf-8")
    return out


def _drift(clip: Path, karr: list, kmask: list, thr: float, f: int = 4) -> list[float]:
    """Per frame: how much better the keyframes' letters match when shifted
    (up to 40 px) than in place. Near the clip's usual value: in place."""
    import numpy as np
    exe = shutil.which("ffmpeg") or "ffmpeg"
    ks = [_small(k, f) for k in karr]
    ms = [_small(m[..., None], f)[..., 0] for m in kmask]
    shifts = ((-3, 0), (3, 0), (-6, 0), (6, 0), (-10, 0), (10, 0), (0, -4), (0, 4))

    def hold(fs, k, m, dy: int, dx: int) -> float:
        k2, m2 = np.roll(k, (dy, dx), (0, 1)), np.roll(m, (dy, dx), (0, 1))
        return float((m2 * np.clip((thr - np.abs(fs - k2).mean(axis=2)) / 12.0, 0, 1)).sum()
                     / max(1e-6, float(m2.sum())))
    dec = subprocess.Popen([exe, "-loglevel", "error", "-i", str(clip), "-vf", f"scale={W}:{H}",
                            "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    n, out = W * H * 3, []
    while True:
        buf = dec.stdout.read(n)
        if len(buf) < n:
            break
        fs = _small(np.frombuffer(buf, np.uint8).reshape(H, W, 3).astype(np.float32), f)
        h0 = max(hold(fs, k, m, 0, 0) for k, m in zip(ks, ms))
        out.append(max(hold(fs, k, m, dy, dx) for k, m in zip(ks, ms) for dy, dx in shifts) - h0)
    dec.wait(timeout=60)
    return out


def _dur(mp4: Path) -> float:
    probe = shutil.which("ffprobe") or "ffprobe"
    r = subprocess.run([probe, "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(mp4)],
                       capture_output=True, text=True, timeout=30, check=True)
    return float(r.stdout.strip() or 8.0)


# --------------------------------------------------------------------------
# Edit + A15
# --------------------------------------------------------------------------

def edit(clips: list[Path], shots: list[dict], out: Path, xd: float = 0.4) -> Path:
    """Each shot retimed to its use_s, joined with the director's transitions."""
    exe = shutil.which("ffmpeg") or "ffmpeg"
    args, chains = [exe, "-y", "-loglevel", "error"], []
    for i, (c, s) in enumerate(zip(clips, shots)):
        args += ["-i", str(c)]
        chains.append(f"[{i}:v]setpts={s['use_s'] / _dur(c):.4f}*PTS,fps={FPS},scale={W}:{H},format=yuv420p,"
                      f"trim=0:{s['use_s']:.3f},setpts=PTS-STARTPTS[v{i}]")
    prev, off = "v0", 0.0
    for i in range(1, len(clips)):
        off += shots[i - 1]["use_s"] - xd
        chains.append(f"[{prev}][v{i}]xfade=transition={shots[i - 1]['transition']}:duration={xd}:"
                      f"offset={off:.3f}[x{i}]")
        prev = f"x{i}"
    args += ["-filter_complex", ";".join(chains), "-map", f"[{prev}]", "-c:v", "libx264", "-crf", "16",
             "-pix_fmt", "yuv420p", "-an", str(out)]
    subprocess.run(args, check=True, timeout=600)
    return out


def judge(mp4: Path, spec: dict) -> dict:
    from pipeline.gtm_os import agent_runtime as R
    exe = shutil.which("ffmpeg") or "ffmpeg"
    shots, t0, frames, strings = spec["shots"], 0.0, [], []
    for i, s in enumerate(shots):
        for frac in ((0.3, 0.85) if s.get("end_frame") else (0.5,)):
            t = t0 + s["use_s"] * frac
            p = mp4.with_name(mp4.stem + f"_j{len(frames)}.jpg")
            subprocess.run([exe, "-y", "-loglevel", "error", "-ss", f"{t:.2f}", "-i", str(mp4), "-frames:v", "1",
                            "-vf", "scale=1600:-1", str(p)], check=True, timeout=60)
            frames.append(p)
        strings.append(s["id"] + ": " + " | ".join(s["text"] + [x for x in s["end_text"] if x not in s["text"]]))
        t0 += s["use_s"] - 0.4
    return R.brain_vision(
        "Frames, in order, of a cinematic product film. The words on screen must be exactly these, per shot:\n"
        + "\n".join(strings) + "\nCheck: every visible word spelled exactly; no invented text or numbers; "
        "the logo once top-left; the hand (in the phone shot) realistic with five fingers and actually "
        "touching the button (text under the finger is hidden, that is fine); no melted, doubled or ghost "
        "letters; no frame where the layout jumps; it looks like a premium film. A ticker like TSLAx may set "
        "its last letter in a different colour or size: that is styling, not a fault. "
        'Return JSON: {"verdict": "SHIP"|"REVISE"|"REJECT", "faults": [{"shot": str, "fault": str}]}',
        frames, agent="A15_creative_judge", role="reasoning", temperature=0.1, max_output_tokens=2048)


def run(brief: str, *, name: str, run_id: Optional[str] = None, spec: Optional[dict] = None,
        reuse_veo: bool = False) -> dict[str, Any]:
    (OUT / "keys").mkdir(parents=True, exist_ok=True)
    refs, note = style_refs()
    spec = spec or direct(brief, refs, note, run_id=run_id)
    (OUT / f"{name}.spec.json").write_text(json.dumps(spec, ensure_ascii=False, indent=1), encoding="utf-8")
    keys: list[dict] = []
    for s in spec["shots"]:
        a = keyframe(f"{name}_{s['id']}_a", s["frame"], s["text"], refs)
        b = keyframe(f"{name}_{s['id']}_b", s["end_frame"], s["end_text"] or s["text"], refs,
                     start=a["path"]) if s.get("end_frame") else None
        keys.append({"a": a, "b": b})
    poster_i = next((i for i, s in enumerate(spec["shots"]) if s["id"] == spec.get("poster")), 1)
    poster = OUT / f"{name}_poster.png"
    poster.write_bytes(Path(keys[poster_i]["a"]["path"]).read_bytes())

    def shot(i: int) -> Path:
        s, k = spec["shots"][i], keys[i]
        a = _frame_1080(k["a"]["path"])
        b = _frame_1080(k["b"]["path"]) if k["b"] else a
        raw = OUT / f"{name}_{s['id']}_veo.mp4"
        if not (reuse_veo and raw.exists()):            # --reuse-veo: recut and retypeset for free
            animate(s["motion"], a, b, raw)
        return stamp(raw, [a] + ([b] if b != a else []), OUT / f"{name}_{s['id']}.mp4")
    with ThreadPoolExecutor(max_workers=3) as pool:
        clips = list(pool.map(shot, range(len(spec["shots"]))))
    final = edit(clips, spec["shots"], OUT / f"{name}.mp4")
    try:
        verdict = judge(final, spec)
    except Exception as exc:                        # noqa: BLE001 — unjudged
        verdict = {"verdict": "UNJUDGED", "faults": [{"shot": "-", "fault": str(exc)[:160]}]}
    return {"final": _rel(final), "poster": _rel(poster), "verdict": verdict,
            "keys": [{"a": _rel(k["a"]["path"]), "a_tries": [(t.get("verdict"), t.get("score")) for t in k["a"]["tries"]],
                      "b": _rel(k["b"]["path"]) if k["b"] else None,
                      "b_tries": [(t.get("verdict"), t.get("score")) for t in k["b"]["tries"]] if k["b"] else None}
                     for k in keys]}


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("brief")
    ap.add_argument("--name", default="cinema")
    ap.add_argument("--keys-only", action="store_true", help="the director's spec only, no images or Veo")
    ap.add_argument("--spec", help="reuse a saved director spec; its keyframes that still pass are kept")
    ap.add_argument("--reuse-veo", action="store_true", help="with --spec: keep the Veo shots already rendered")
    a = ap.parse_args()
    if a.keys_only:
        (OUT / "keys").mkdir(parents=True, exist_ok=True)
        refs, note = style_refs()
        spec = direct(a.brief, refs, note)
        (OUT / f"{a.name}.spec.json").write_text(json.dumps(spec, ensure_ascii=False, indent=1), encoding="utf-8")
        print(json.dumps(spec, ensure_ascii=False, indent=1))
    else:
        prior = json.loads(Path(a.spec).read_text(encoding="utf-8")) if a.spec else None
        print(json.dumps(run(a.brief, name=a.name, spec=prior, reuse_veo=a.reuse_veo), ensure_ascii=False, indent=1))
