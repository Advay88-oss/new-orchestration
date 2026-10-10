"""The agents' short film: Veo 3.1 for what it is good at, code for what it is not.

What a hand-made Remotion film taught, after two Veo-only attempts at the
same film failed (the headline spelled "Earn Kamiino yeed", small text melted,
numbers like 105% invented, no real logo, a black frame mid-clip):

  Motion/Art Director (A07, "director" model)
    writes the film spec from the post: four scenes (hook, steps, app,
    sign-off), every word, number and chip on screen, from the brand brain's
    facts only, and two prompts for Veo's TEXTLESS cinematic layers.
  Veo 3.1 (A09, MODELS["video"])
    renders those layers — a living glow-and-light background and a hero
    object — with a negative prompt for text, numbers, logos and UI. Veo never
    draws a letter.
  Typesetter (code: Remotion composition AgentFilm)
    lays the director's exact words, the UI, the real logo, the timing and the
    transitions over Veo's layers.
  Creative judge (A15)
    checks sampled frames against the spec; a fault in the words or layout is
    fixed by the director and re-typeset (free), not by another Veo render.

    python -m pipeline.gtm_creative.film_director "post brief" --name farm
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any, Optional

REMOTION = Path(os.environ.get("VANNA_REMOTION_DIR", r"D:\vanna-remotion"))
OUT = Path(__file__).resolve().parents[2] / "exports" / "agent-posts" / "video" / "agent-film"
FPS, FRAMES = 30, 240
NEGATIVE = ("text, letters, words, numbers, digits, labels, captions, typography, logo, watermark, "
            "user interface, screens, phones, charts, people, hands, coins, camera shake")

SCHEMA = (
    '{"tag1": str (mono caps tag, 1-2 words), "eyebrow": str (2-4 words), "hook": str (the hook headline, '
    '2-4 words), "hookSub": str (under 9 words), "token": str (the asset shown on the hero object, e.g. a '
    'ticker), "tokenSub": str (2 words, caps), "tag2": str, "stepsHead": str (3-4 words), "steps": '
    '[{"n": "01", "title": str (1 word), "sub": str (2-4 words)}] (exactly 3), "stepValue": str (a sample '
    'number for step 1, e.g. "10"), "stepUnit": str (its unit/ticker), "lev": [str] (the leverage stops the '
    'facts state, e.g. "1x".."5x"), "levPick": int (index of the stop shown), "stepEarn": str (step 3 '
    'destination, 2-3 words), "stepsNote": [str, str] (a sentence split in two; part 2 is emphasised), '
    '"tag3": str, "app1": str (1 word), "app2": str (2 words, the payoff, shown in gradient), "appSub": str '
    '(under 14 words), "phoneTitle": str (under 4 words), "rows": [[label, value]] (exactly 4, sample '
    'values), "button": str (2-3 words), "routeTitle": str, "route": [str] (exactly 3, 2-4 words each), '
    '"confirm": str (2-3 words), "sign1": str (= the hook), "sign2": str (= app1 + app2), "chips": [str] '
    '(exactly 3, 2-4 words), "footerL": "vanna.finance", "footerR": str (deployment + "sample data"), '
    '"plate_bg": str (Veo prompt), "plate_hero": str (Veo prompt)}')


def direct(brief: str, *, run_id: Optional[str] = None, fix: str = "", prior: Optional[dict] = None) -> dict:
    """The Motion/Art Director's film spec."""
    from pipeline.brand_brain import context as C
    from pipeline.gtm_os import agent_runtime as R

    system = C.fill(
        "You are {company}'s Motion/Art Director. You write the spec of an 8-second motion-graphics film. "
        "Code typesets every word you write exactly; Veo 3.1 renders only two TEXTLESS cinematic layers "
        "from your prompts. Return strict JSON only.")
    prompt = (
        C.facts_block(brief, k=6, excerpts=3) + "\n\n----\n\n"
        "THE POST: " + " ".join(brief.split())[:900] + "\n\n"
        "The film has four scenes: (1) the hook with a hero object, (2) how it works in three steps, "
        "(3) the app moment (a phone screen, a tap, a summary card, a confirmation), (4) the sign-off. "
        "RULES: state only what the facts above say; every number inside the phone or steps is sample data "
        "and the footer says so; never name a competitor; keep to the word limits — words that are too long "
        "break the layout. "
        "VEO LAYERS: Veo draws every word it is given, so the two plate prompts name NO text, letters, "
        "numbers, logos, tickers, UI, phones or people. plate_bg: an 8-second locked-off abstract "
        "background on near-black #07020D — slow drifting violet #703AE6 and magenta #C2479F light fields, "
        "soft light streaks in coral #FC5457 to violet, faint particles; darker on the left where text sits. "
        "plate_hero: an 8-second locked-off shot of one abstract glossy object centred on pure black that "
        "stands for the hook's asset (a coin-like glass ring in the coral-to-violet gradient, slowly "
        "rotating, light gliding across it), no markings on it.\n"
        + ("\nYOUR PREVIOUS SPEC:\n" + json.dumps(prior, ensure_ascii=False)[:3000]
           + "\nTHE JUDGE FOUND THESE PROBLEMS — fix them and return the whole spec:\n" + fix + "\n" if fix else "")
        + "\nReturn JSON: " + SCHEMA)
    spec = R.brain_json(prompt, agent="A14_motion_director", role="director", system=system,
                        temperature=0.4, max_output_tokens=4096, run_id=run_id)
    for key, n in (("steps", 3), ("rows", 4), ("route", 3), ("chips", 3)):
        if not isinstance(spec.get(key), list) or len(spec[key]) < n:
            raise RuntimeError("director's spec is missing " + key)
        spec[key] = spec[key][:n]
    spec["levPick"] = int(spec.get("levPick") or 0)
    spec["stepsNote"] = (list(spec.get("stepsNote") or ["", ""]) + ["", ""])[:2]
    R.record_decision("A14_motion_director", "film_spec", {"spec": spec}, run_id=run_id)
    return spec


def _veo_plate(prompt: str, out: Path) -> Path:
    """One textless Veo 3.1 layer (A09)."""
    import time
    from pipeline.gtm_creative.motion import _journal
    from pipeline.gtm_os.agent_runtime import MODELS
    from pipeline.scripts.veo_broll import _find_video, _write_video, run_veo
    t = time.time()
    params = {"aspectRatio": "16:9", "sampleCount": 1, "durationSeconds": 8, "generateAudio": False,
              "resolution": "1080p", "negativePrompt": NEGATIVE}
    res, key, via = run_veo(MODELS["video"], {"prompt": prompt + " No text of any kind."}, params,
                            project="vanna-mcp", location="us-central1", timeout_s=600)
    if res.get("error"):
        raise RuntimeError("Veo failed: " + json.dumps(res["error"])[:300])
    b64, uri = _find_video(res)
    if not (b64 or uri) or not _write_video(b64, uri, out, key):
        raise RuntimeError("Veo returned no video")
    _journal(True, round(time.time() - t, 2), MODELS["video"], "textless film layer", transport=via)
    return out


def _frames(mp4: Path, dest: Path) -> int:
    """Veo's clip as a 30 fps JPEG sequence for the typesetter."""
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)
    exe = shutil.which("ffmpeg") or "ffmpeg"
    subprocess.run([exe, "-y", "-loglevel", "error", "-i", str(mp4), "-vf", f"fps={FPS},scale=1920:1080",
                    "-q:v", "3", str(dest / "f_%04d.jpg")], check=True, timeout=300)
    return len(list(dest.glob("f_*.jpg")))


def typeset(spec: dict, plates: dict, out: Path) -> Path:
    """Remotion lays the director's exact words over Veo's layers."""
    props = {"spec": {**{k: v for k, v in spec.items() if not k.startswith("plate_")}, "plates": plates}}
    pfile = out.with_suffix(".props.json")
    pfile.write_text(json.dumps(props, ensure_ascii=False), encoding="utf-8")
    env = {**os.environ, "ComSpec": r"C:\Windows\System32\cmd.exe",
           "PATH": r"C:\nvm4w\nodejs;" + os.environ.get("PATH", "")}
    cli = REMOTION / "node_modules" / ".bin" / ("remotion.cmd" if os.name == "nt" else "remotion")
    subprocess.run([str(cli), "render", "src/index.ts", "AgentFilm", str(out), "--props=" + str(pfile),
                    "--gl=angle", "--crf=16", "--log=error"], cwd=str(REMOTION), env=env, check=True, timeout=1500)
    return out


def judge(mp4: Path, spec: dict) -> dict:
    """The creative judge (A15) on sampled frames."""
    from pipeline.gtm_os import agent_runtime as R
    exe = shutil.which("ffmpeg") or "ffmpeg"
    shots = []
    for t in (1.6, 3.6, 5.6, 7.6):
        p = mp4.with_name(mp4.stem + f"_j{t}.jpg")
        subprocess.run([exe, "-y", "-loglevel", "error", "-ss", str(t), "-i", str(mp4), "-frames:v", "1",
                        "-vf", "scale=1600:-1", str(p)], check=True, timeout=60)
        shots.append(p)
    words = [spec.get(k) for k in ("hook", "stepsHead", "app1", "app2", "sign1", "sign2")]
    return R.brain_vision(
        "Four frames (1.6s, 3.6s, 5.6s, 7.6s) of an 8-second brand film. The words on screen must be exactly "
        "the spec's: " + " / ".join(str(w) for w in words) + ". Check: every visible word spelled exactly; no "
        "text overlapping other text or running off the frame; the logo appears once top-left (or centred on "
        "the sign-off); the background layers contain no letters; a stranger gets the point. "
        'Return JSON: {"verdict": "SHIP"|"REVISE"|"REJECT", "layout_fixes": [str] (fixes the spec can make, '
        'e.g. a shorter headline), "plate_faults": [str] (faults in the background layers)}',
        shots, agent="A15_creative_judge", role="reasoning", temperature=0.1, max_output_tokens=2048)


def run(brief: str, *, name: str, run_id: Optional[str] = None) -> dict[str, Any]:
    OUT.mkdir(parents=True, exist_ok=True)
    spec = direct(brief, run_id=run_id)
    plate_dir = REMOTION / "public" / "plates" / name
    plates: dict[str, Any] = {"frames": FRAMES}
    for kind in ("bg", "hero"):
        mp4 = _veo_plate(str(spec["plate_" + kind]), OUT / f"{name}_{kind}.mp4")
        plates["frames"] = min(plates["frames"], _frames(mp4, plate_dir / kind))
        plates[kind] = f"plates/{name}/{kind}"
    out = typeset(spec, plates, OUT / f"{name}.mp4")
    verdicts = []
    for _ in range(2):
        v = judge(out, spec)
        verdicts.append(v)
        if str(v.get("verdict")).upper() == "SHIP" or not v.get("layout_fixes"):
            break
        spec = direct(brief, run_id=run_id, fix="\n".join("- " + str(x) for x in v["layout_fixes"]), prior=spec)
        out = typeset(spec, plates, out)
    (OUT / f"{name}.spec.json").write_text(json.dumps(spec, ensure_ascii=False, indent=1), encoding="utf-8")
    return {"final": str(out), "spec": spec, "verdicts": verdicts}


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("brief")
    ap.add_argument("--name", default="agent_film")
    a = ap.parse_args()
    res = run(a.brief, name=a.name)
    print(json.dumps({"final": res["final"], "verdicts": [v.get("verdict") for v in res["verdicts"]],
                      "fixes": [v.get("layout_fixes") for v in res["verdicts"]],
                      "plate_faults": [v.get("plate_faults") for v in res["verdicts"]],
                      "hook": res["spec"].get("hook"), "sign2": res["spec"].get("sign2")}, ensure_ascii=False))
