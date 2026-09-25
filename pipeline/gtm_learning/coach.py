"""The Coach — the part of A13 that does what a reviewing engineer did by hand.

Through 2026-09-25 the improvements between runs came from a human reading
the outputs: looking at a poster and its video frames, working out WHY a
clip went wrong ("the isometric chip made Veo tilt the camera"), turning it
into a rule, and writing the long note that says why the founder's favourite
video worked. Without that, the loop only knew approve / kill counts.

The Coach does that inside A13, with a model that can see:

  review_run(summary) — after every run: the poster, frames of the clip and
  every judge note. Up to two faults whose cause lies in how the asset was
  asked for become general rules in `learned-rules.md`, which the Motion
  Director, the image agent and the judges read on the next run.

  learn_from_decisions() — for each founder decision not yet studied: on an
  approve it looks at the poster (and clip) and writes what made it work,
  stored as the exemplar's note; on a kill or revise it reads the founder's
  note against the poster and writes the rule that would have prevented it.

It writes text the agents read, never code, and never publishes anything.
Its model is the director role (VANNA_GTM_MODEL_DIRECTOR).
"""
from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Optional

AGENT = "A16_coach"
STATE = Path(__file__).resolve().parents[2] / "pipeline" / "state"
COACH_STATE = STATE / "coach_state.json"

SYSTEM = (
    "You are the Coach for {company}'s creative agents. You look at what they "
    "made and turn what went wrong, or right, into guidance they follow next "
    "time. Rules must be GENERAL — about how posters and clips are asked for "
    "and checked — never about one topic. Be concrete: 'keep every element "
    "flat and face-on; an isometric object made Veo tilt the camera' is "
    "useful, 'improve quality' is not. Return strict JSON.")


def _frames(mp4: str, at=(2.0, 5.0, 9.0)) -> list[Path]:
    exe = shutil.which("ffmpeg") or "ffmpeg"
    tmp = Path(tempfile.mkdtemp())
    out = []
    for i, t in enumerate(at):
        f = tmp / f"c{i}.jpg"
        try:
            subprocess.run([exe, "-y", "-loglevel", "error", "-ss", str(t), "-i", mp4,
                            "-frames:v", "1", "-vf", "scale=960:-1", "-q:v", "3", str(f)],
                           check=True, timeout=60)
            out.append(f)
        except Exception:                           # noqa: BLE001 — boundary
            continue
    return out


def _assets(s: dict) -> tuple[list[Path], str]:
    imgs, labels = [], []
    v = s.get("visual_path")
    if v and Path(str(v)).exists():
        imgs.append(Path(str(v)))
        labels.append("the poster")
    vid = s.get("video_path")
    if vid and Path(str(vid)).exists():
        fr = _frames(str(vid))
        imgs += fr
        labels += ["clip frame at %ss" % t for t in (2, 5, 9)][:len(fr)]
    return imgs, ", ".join(labels)


def _notes(s: dict) -> str:
    parts = []
    for k in ("visual_review", "video_review"):
        r = s.get(k) or {}
        if r.get("verdict"):
            parts.append(k.replace("_", " ") + ": " + str(r.get("verdict")) + " — "
                         + str(r.get("critique") or r.get("fix") or ""))
    for a in (s.get("creative_review") or {}).get("assets") or []:
        parts.append("creative judge on " + str(a.get("asset")) + ": " + str(a.get("verdict"))
                     + " — " + str(a.get("critique") or "")[:300])
    return "\n".join(parts)


def review_run(s: dict, run_id: Optional[str] = None) -> list[str]:
    """Rules learned from one run's own assets and judge notes."""
    from pipeline.gtm_creative.creative_rules import (add_learned, block, coach_record,
                                                      credit, run_reward)
    from pipeline.gtm_os import agent_runtime as R

    # Reinforcement first: every rule that was active while this run was made
    # is credited with how the run came out, before any new rule is written.
    rw = run_reward(s)
    if rw is not None:
        credit(rw, since=str(s.get("started_at") or ""), run_id=str(run_id or ""))

    imgs, labels = _assets(s)
    notes = _notes(s)
    if not imgs or not notes:
        return []
    record = coach_record()
    prompt = (
        "THE RULES THE AGENTS ALREADY FOLLOW:\n" + block(max_chars=3500) + "\n\n----\n\n"
        + (record + "\n\n----\n\n" if record else "")
        + "ATTACHED: " + labels + ".\nWHAT THE JUDGES SAID:\n" + notes + "\n\n"
        "Find at most TWO faults you can SEE whose cause is in how the asset was "
        "asked for — something a rule would prevent next time — and that the "
        "rules above do not already cover. If one of YOUR active rules clearly "
        "failed here, you may instead rewrite it more precisely. Never propose a "
        "retired rule. If there are none, return an empty list; that is a good "
        "answer.\n"
        'Return JSON: {"rules": [{"rule": str (one sentence, general), '
        '"because": str (what you saw)}]}')
    try:
        out = R.brain_vision(prompt, imgs, agent=AGENT, system=__import__('pipeline.brand_brain.context', fromlist=['fill']).fill(SYSTEM), role="director",
                             temperature=0.2, max_output_tokens=4096, run_id=run_id)
    except Exception:                               # noqa: BLE001 — boundary
        return []
    added = []
    for r in (out.get("rules") or [])[:2]:
        text = str(r.get("rule") or "").strip()
        if text and add_learned(text + " — seen: " + str(r.get("because") or "")[:160],
                                source="coach " + str(run_id or s.get("run_id") or "")):
            added.append(text)
    return added


def learn_from_decisions() -> dict[str, int]:
    """Study every founder decision not yet studied."""
    from pipeline.gtm_creative.creative_rules import add_learned
    from pipeline.gtm_learning.feedback import LEDGER, RUNS
    from pipeline.gtm_os import agent_runtime as R

    try:
        state = json.loads(COACH_STATE.read_text(encoding="utf-8"))
    except Exception:                               # noqa: BLE001 — first run
        state = {"last_at": ""}
    try:
        rows = [json.loads(l) for l in Path(LEDGER).read_text(encoding="utf-8").splitlines()
                if l.strip()]
    except FileNotFoundError:
        rows = []
    fresh = [r for r in rows if str(r.get("at")) > state.get("last_at", "")][-6:]
    counts = {"studied": 0, "notes": 0, "rules": 0}
    for r in fresh:
        try:
            s = json.loads((Path(RUNS) / r["run_id"] / "summary.json").read_text(encoding="utf-8"))
        except Exception:                           # noqa: BLE001 — boundary
            continue
        # The founder's decision is the strongest reward a rule can get: the
        # rules active when this run was made are credited again, weighted.
        try:
            from pipeline.gtm_creative.creative_rules import credit
            credit(float(r.get("reward", 0.0)), since=str(s.get("started_at") or ""),
                   weight=2.0, run_id=r["run_id"])
        except Exception:                           # noqa: BLE001 — boundary
            pass
        imgs, labels = _assets(s)
        if not imgs:
            continue
        verdict, note = r.get("verdict"), r.get("note") or ""
        if verdict == "approve":
            ask = ("The founder APPROVED this. Say concretely what makes it work — "
                   "layout, hierarchy, how the idea is shown, and (for a clip) how it "
                   "builds — so the agents can do it again on a different topic. "
                   'Return JSON: {"why_it_works": str (3-4 sentences)}')
        else:
            ask = ("The founder chose " + str(verdict).upper() + ". Their note: '" + note
                   + "'. Write the ONE general rule that would have prevented it. "
                   'Return JSON: {"rule": str, "because": str}')
        try:
            out = R.brain_vision("ATTACHED: " + labels + ".\nTHE BRIEF: "
                                 + str(s.get("poster_brief") or s.get("directive") or "")[:900]
                                 + "\n\n" + ask, imgs, agent=AGENT, system=__import__('pipeline.brand_brain.context', fromlist=['fill']).fill(SYSTEM),
                                 role="director", temperature=0.2, max_output_tokens=4096)
        except Exception:                           # noqa: BLE001 — boundary
            continue
        counts["studied"] += 1
        if verdict == "approve" and out.get("why_it_works"):
            why = "Founder approved" + (" ('" + note + "')" if note else "") + ". Coach: " \
                  + str(out["why_it_works"])
            try:
                from pipeline.gtm_learning.visual_exemplars import add as add_visual
                add_visual(s["visual_path"], renderer=s.get("visual_renderer") or "direct_model",
                           score=1.0, note=why, brief=str(s.get("poster_brief") or s.get("directive") or ""))
                counts["notes"] += 1
            except Exception:                       # noqa: BLE001 — boundary
                pass
            vid = s.get("video_path")
            vrev = str((s.get("video_review") or {}).get("verdict") or "").upper()
            if vid and Path(str(vid)).exists() and vrev != "REJECT" and s.get("video_mode") == "veo_build":
                try:
                    from pipeline.gtm_creative.veo_video import add_exemplar
                    add_exemplar(vid, score=1.0, note=why, prompt=s.get("video_prompt") or "",
                                 still=s.get("visual_path"))
                except Exception:                   # noqa: BLE001 — boundary
                    pass
        elif out.get("rule"):
            if add_learned(str(out["rule"]) + " — founder " + str(verdict) + ": "
                           + note[:140], source="founder via coach"):
                counts["rules"] += 1
    if rows:
        COACH_STATE.write_text(json.dumps({"last_at": max(str(r.get("at")) for r in rows)}),
                               encoding="utf-8")
    return counts
