"""A07 grading its own output — the assets, not the brief.

Until now nothing looked at what the generators actually produced. A08 audited
its PNG for resolution and corner luminance; A09 checked only that an MP4 came
back. Neither could tell whether the image was about Vanna, which is how a run
shipped an elegant optical sculpture that could have advertised a wristwatch
while the post underneath it argued about liquidation thresholds.

This module sends the rendered assets back to the creative director, along with
the copy that will ship with them, and asks the one question the pipeline was
never asking: **does this show Vanna's mechanism, and does it match the post?**

Two rules keep it from being decorative:

  * It looks at the actual pixels via `brain_vision`, not at the prompt that
    produced them. Grading the brief grades the intention.
  * A verdict of REJECT is recorded as a blocking defect on the run. A judge
    whose rejection changes nothing is a comment, not a gate.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

from pipeline.gtm_os import agent_runtime as R
from pipeline.gtm_os.vanna_knowledge import PROHIBITED_VISUAL, VISUAL_ANCHORS

AGENT = "A07_creative_director"

JUDGE_SYSTEM = (
    "You are Vanna's creative director reviewing finished assets before they "
    "go to the founder. Vanna is composable credit infrastructure on Stellar "
    "Soroban TESTNET.\n\n"

    "You are the last person who sees these before a human does, and your "
    "default posture is scepticism. A beautiful image that does not show "
    "Vanna's mechanism is a failure — it is stock art, and shipping it teaches "
    "the audience that Vanna posts are decoration.\n\n"

    "Vanna's mechanism means these concrete things:\n"
    + "\n".join("  - " + k + ": " + v for k, v in VISUAL_ANCHORS.items()) + "\n\n"

    "Judge each asset on:\n"
    "  on_brand      house style — obsidian void, negative space, matte and "
    "optical materials, restraint. No neon, no crypto slop.\n"
    "  shows_mechanism  can you name the Vanna mechanism depicted? If the "
    "honest answer is 'abstract shapes', that is a NO regardless of beauty.\n"
    "  matches_copy  does the asset argue the same thing the post argues?\n"
    "  no_text       no MODEL-GENERATED text, letterforms or numerals. One "
    "exception, and only one: the still image carries a composited Vanna "
    "brand lockup in a corner and a composited headline along the top. Those "
    "are drawn deterministically after generation with the exact words we "
    "supplied, so they are correct by construction — do not fault them. "
    "Everything else that reads as a word, label, axis tick, formula or "
    "figure IS a defect: the model cannot spell, and a misspelt number ships "
    "as a false claim. Video has no exception — any text in frame is a \n"
    "defect.\n"
    "  prohibited    " + PROHIBITED_VISUAL + "\n\n"

    "Verdicts: SHIP (good as is), REVISE (usable but name what is wrong), "
    "REJECT (do not publish). Use REJECT when the asset shows no mechanism, "
    "carries text, contradicts the copy, or breaks the prohibited list.\n\n"
    "Return strict JSON. Be specific: 'the three chambers read as decorative "
    "vases, not as isolated accounts' is useful, 'could be stronger' is not."
)

SCHEMA_HINT = (
    '{"assets": [{"asset": "visual"|"meme"|"video_still", '
    '"verdict": "SHIP"|"REVISE"|"REJECT", "shows_mechanism": bool, '
    '"mechanism_named": str, "on_brand": bool, "matches_copy": bool, '
    '"has_text": bool, "prohibited_elements": [str], "critique": str, '
    '"fix": str}], '
    '"copy_verdict": "SHIP"|"REVISE"|"REJECT", "copy_critique": str, '
    '"overall": "SHIP"|"REVISE"|"REJECT", "summary": str}'
)


def _video_still(video_path: str, out: Path) -> Optional[Path]:
    """Pull one frame so the video can be judged on what it shows.

    Vision models take images, not MP4s. A midpoint frame is enough to tell
    whether the shot is about the mechanism or about ambient glassware — which
    is the question being asked.
    """
    import shutil
    import subprocess

    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        return None
    out.parent.mkdir(parents=True, exist_ok=True)
    try:
        subprocess.run(
            [ffmpeg, "-y", "-ss", "4", "-i", str(video_path),
             "-frames:v", "1", "-q:v", "3", str(out)],
            capture_output=True, timeout=60, check=True)
    except Exception:                               # noqa: BLE001 — boundary
        return None
    return out if out.exists() and out.stat().st_size > 1024 else None


def judge_assets(summary: dict[str, Any], run_id: str) -> dict[str, Any]:
    """Review the run's assets and copy together. Raises BrainError on failure."""
    images: list[Path] = []
    labels: list[str] = []

    for key, label in (("visual_path", "visual"), ("meme_path", "meme")):
        p = summary.get(key)
        if p and Path(str(p)).exists():
            images.append(Path(str(p)))
            labels.append(label)

    video = summary.get("video_path")
    if video and Path(str(video)).exists():
        still = _video_still(
            str(video),
            Path(str(video)).with_name(run_id + "_video_still.jpg"))
        if still:
            images.append(still)
            labels.append("video_still")

    if not images:
        R.record_stage(AGENT, "skipped", "no assets to judge")
        return {"overall": "SKIPPED", "assets": [],
                "summary": "no assets were produced to review"}

    posts = summary.get("posts") or {}
    x = posts.get("x") or {}
    copy_block = ("HOOK: " + str(x.get("hook", ""))[:300] + "\n\n"
                  + "BODY: " + str(x.get("copy", ""))[:1800])

    prompt = (
        "CAMPAIGN\n"
        "  pillar:  " + str(summary.get("pillar") or "") + "\n"
        "  problem: " + str(summary.get("problem") or "")[:400] + "\n\n"
        "THE POST THAT SHIPS WITH THESE ASSETS\n" + copy_block + "\n\n"
        "ATTACHED IMAGES, in order: " + ", ".join(labels) + "\n\n"
        "Review each attached image and the copy. Return JSON exactly:\n"
        + SCHEMA_HINT
    )

    verdict = R.brain_vision(prompt, images, agent=AGENT, system=JUDGE_SYSTEM,
                             role="reasoning", temperature=0.15,
                             max_output_tokens=4096)

    assets = verdict.get("assets") or []
    rejects = [a for a in assets if str(a.get("verdict")).upper() == "REJECT"]
    no_mech = [a for a in assets if a.get("shows_mechanism") is False]
    overall = str(verdict.get("overall", "")).upper() or (
        "REJECT" if rejects else "SHIP")
    verdict["overall"] = overall

    detail = ("judged " + str(len(assets)) + " asset(s): " + overall
              + (" | " + str(len(rejects)) + " rejected" if rejects else "")
              + (" | " + str(len(no_mech)) + " show no mechanism" if no_mech else ""))
    R.record_stage(AGENT, "ok" if overall == "SHIP" else "degraded", detail)
    return verdict
