"""The autonomous GTM cycle — all thirteen agents, one run, one journal.

Before this module the thirteen agents had no single caller that exercised them
all. `gtm_operating_system.py` ran nine of them and was itself imported only by
its own test; the Visual Synthesis Engine and the Video Production Engine were
never called by any lifecycle at all, so the two agents with the most expensive
models attached had never run inside a cycle. Nothing enqueued anything on a
schedule, so "24/7 autonomous" described a worker that woke to an empty queue.

This module is the caller. It runs the thirteen in order, records each one to
the run journal whether it called a model or not, and writes a summary the
dashboard reads directly. Three rules it does not bend:

  * **An agent that fails is written down as failed.** No stage substitutes a
    canned result for a missing one. That substitution is what let the
    2026-09-17 trace report a successful live run over pre-written copy.

  * **Media is generated, not promised.** A08 renders a real PNG through
    nano banana and A09 a real MP4 through Veo 3.1. If a render fails the run
    continues and says the asset is missing, rather than pointing at an old file.

  * **Human review is still the terminus.** The cycle ends by building the
    Telegram packet. Nothing here publishes.
"""
from __future__ import annotations

import argparse
import pathlib
import json
import os
import re
import sys
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from pipeline.gtm_os import agent_runtime as R

STATE_DIR = REPO_ROOT / "pipeline" / "state"
RUNS_DIR = STATE_DIR / "gtm_runs"

VEO_PROJECT = "vanna-mcp"
VEO_LOCATION = "us-central1"


class CycleAbort(RuntimeError):
    """A stage failed in a way that makes the rest of the cycle meaningless."""


# --------------------------------------------------------------------------
# One run at a time
# --------------------------------------------------------------------------

LOCK_FILE = STATE_DIR / "gtm_cycle.lock"
LOCK_STALE_S = 1800          # a cycle is 2-4 minutes; 30 is dead, not slow


class AlreadyRunning(RuntimeError):
    pass


def _claim_lock(run_id: str) -> bool:
    """Take the run lock, or report who holds it.

    Two cycles at once interleave on shared files — `recent_archetypes.json`
    would record one run's archetype and the other would then not block it, and
    the Ideas and Memes panels are read-modify-write. Pressing Launch Run twice
    was enough to do it.

    `O_CREAT | O_EXCL` is the primitive: it either creates the file or fails,
    with no window between the check and the write.
    """
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    try:
        age = time.time() - LOCK_FILE.stat().st_mtime
        if age > LOCK_STALE_S:
            # A crashed run leaves its lock behind. Reclaiming a stale one
            # beats requiring a human to delete a file before the scheduler
            # can work again.
            print("  [lock] reclaiming a stale lock (" + str(int(age)) + "s old)")
            LOCK_FILE.unlink(missing_ok=True)
    except FileNotFoundError:
        pass

    try:
        fd = os.open(str(LOCK_FILE), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        try:
            holder = json.loads(LOCK_FILE.read_text(encoding="utf-8"))
        except Exception:                           # noqa: BLE001 — boundary
            holder = {}
        raise AlreadyRunning(
            "another cycle holds the lock: " + str(holder.get("run_id", "?"))
            + " (pid " + str(holder.get("pid", "?")) + ", started "
            + str(holder.get("started", "?")) + ")")

    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump({"run_id": run_id, "pid": os.getpid(),
                   "started": datetime.now(timezone.utc).isoformat()}, f)
    return True


def _release_lock() -> None:
    LOCK_FILE.unlink(missing_ok=True)


def _stage(agent: str, fn, *, required: bool = True, detail: str = "",
           self_recorded: bool = False):
    """Run one agent, journal the outcome, and keep the failure honest.

    `self_recorded` is for agents that write their own stage row with something
    worth keeping — A01's per-source report, A08's artifact paths. Without it
    this wrapper's generic "completed (21.75s)" was written afterwards and
    replaced the detail the agent had just recorded.
    """
    started = time.time()
    try:
        value = fn()
    except Exception as exc:                        # noqa: BLE001 — boundary
        note = type(exc).__name__ + ": " + str(exc)
        R.record_stage(agent, "failed", note[:400])
        print("  [FAIL] " + agent + " :: " + note[:200])
        if required:
            raise CycleAbort(agent + " failed: " + note[:200]) from exc
        return None
    took = round(time.time() - started, 2)
    if not self_recorded:
        R.record_stage(agent, "ok", (detail or "completed") + " (" + str(took) + "s)")
    print("  [ ok ] " + agent + "  " + str(took) + "s")
    return value


# --------------------------------------------------------------------------
# A08 — Visual Synthesis Engine (gemini-3.1-flash-image, "nano banana")
# --------------------------------------------------------------------------

def render_visual(strategy, content_pkg, blueprint, run_id: str,
                  subject: str = "") -> Optional[dict]:
    """A08 renders the post visual through the archetype system.

    The old path called VisualPipelineEngine, which chose its composition from
    a five-branch if/else on keywords — the reason every post looked the same.
    A07 now picks an archetype (with the last two removed from the candidate
    set) and fills its slots, and the archetype's own renderer draws it. Half
    the archetypes never reach an image model at all.
    """
    from pipeline.gtm_creative.archetype_director import direct_and_render

    hook, body = "", ""
    try:
        x = content_pkg.channel_posts["x"]
        hook, body = str(x.hook), str(x.copy)
    except Exception:                               # noqa: BLE001 — boundary
        hook = str(getattr(strategy, "problem", ""))[:200]

    # Which way to make it is learned. The founder rated the posters the image
    # model made directly from the references far above the code-set ones, so
    # the direct renderer usually wins the Thompson draw — while code-set is
    # still tried now and then, so the preference can move if feedback does.
    # The founder wants every run to look like the posters they approved —
    # "ditto same" — so the direct renderer is always used. The code-set
    # renderer is still explored only when VANNA_VISUAL_EXPLORE=1.
    renderer = "direct_model"
    if os.environ.get("VANNA_VISUAL_EXPLORE") == "1":
        try:
            from pipeline.gtm_learning.visual_exemplars import preferred_renderer
            renderer = preferred_renderer()
        except Exception:                           # noqa: BLE001 — boundary
            renderer = "direct_model"

    if renderer == "direct_model":
        direct = _render_direct(hook, body, subject, run_id)
        if direct:
            return direct
        R.record_stage("A08_visual_synthesis", "degraded",
                       "direct-model poster did not pass its own review; "
                       "falling back to the archetype renderer")

    result = direct_and_render(strategy, hook, body, run_id,
                               subject=subject)
    png = Path(result["path"])
    if not png.exists() or png.stat().st_size < 4096:
        raise RuntimeError("archetype renderer produced no usable PNG")
    R.record(R.AgentCall(
        "A08_visual_synthesis",
        "image" if result["generated"] else "none",
        R.MODELS["image"] if result["generated"] else None,
        True, 0.0,
        note=result["archetype"] + (" (drawn, no model)" if not result["generated"] else ""),
        transport="model-garden" if result["generated"] else "deterministic"))
    return {"path": str(png), "filename": png.name,
            "archetype": result["archetype"], "why": result["why"],
            "public_url": "/" + png.name, "renderer": "code_set"}


def _render_direct(hook: str, body: str, subject: str,
                   run_id: str) -> Optional[dict]:
    """The poster from the image model itself, shown the founder's approved
    posters and the design references. None when it did not pass its own
    judge, so the caller can fall back."""
    from pipeline.gtm_creative.direct_image_posters import MODEL, make

    # The Motion Director writes the brief — the idea, headline, contrast and
    # diagram — from the query and the post, learning from the posters the
    # founder approved. The raw post is the fallback if the agent fails.
    director_brief = None
    layout = None
    try:
        from pipeline.gtm_creative.motion_director import poster_brief
        pb = poster_brief(subject or hook, hook, body)
        director_brief, layout = pb["brief"], pb.get("layout")
        R.record_stage("A14_motion_director", "ok",
                       "wrote the poster brief (layout " + str(layout) + ")")
    except Exception as exc:                        # noqa: BLE001 — boundary
        R.record_stage("A14_motion_director", "degraded",
                       "motion director brief failed: " + str(exc)[:160])
    brief = director_brief or ("Subject: " + (subject or hook) + "\nHook: " + hook
                               + "\nThe post: " + " ".join(body.split())[:1400])
    try:
        out = make(brief, run_id + "_visual",
                   out_dir=Path(__file__).resolve().parents[1] / "state")
    except Exception as exc:                        # noqa: BLE001 — boundary
        R.record_stage("A08_visual_synthesis", "degraded",
                       "direct-model poster failed: " + str(exc)[:200])
        return None
    for a in out["attempts"]:
        R.record(R.AgentCall("A08_visual_synthesis", "image", MODEL, True, 0.0,
                             note="direct poster attempt, judged "
                                  + str(a.get("verdict")),
                             transport="model-garden"))
    # The direct poster is kept even when no attempt reached SHIP: a code-set
    # poster is not the style the founder approved, and nothing publishes
    # without the founder's review anyway. The judge's note travels with it.
    verdicts = [str(a.get("verdict")).upper() for a in out["attempts"]]
    best = next((a for v in ("SHIP", "REVISE", "REJECT") for a in out["attempts"]
                 if str(a.get("verdict")).upper() == v), out["attempts"][-1])
    png = Path(out["final"])
    return {"path": str(png), "filename": png.name,
            "archetype": "DIRECT_MODEL",
            "visual_review": {k: best.get(k) for k in ("verdict", "fix")},
            "why": "image model shown the founder-approved posters and the "
                   "design references; own judge: " + "/".join(verdicts),
            "public_url": "/" + png.name, "renderer": "direct_model",
            "poster_brief": brief, "poster_layout": layout}


def render_visual_legacy(strategy, content_pkg, blueprint, run_id: str) -> Optional[dict]:
    from pipeline.gtm_creative.visual_pipeline_engine import VisualPipelineEngine

    hook = ""
    try:
        hook = str(content_pkg.channel_posts["x"].hook)
    except Exception:
        hook = str(getattr(strategy, "problem", ""))[:160]

    key_claim = ""
    proof = list(getattr(strategy, "proof", []) or [])
    if proof:
        key_claim = str(proof[0])[:220]

    engine = VisualPipelineEngine()
    result = engine.generate_art_directed_visual(
        brief_title=str(getattr(strategy, "title", "") or hook)[:180],
        content_type=str(getattr(strategy, "content_type", "product_deep_dive")),
        directive=str(blueprint.visual_metaphor.concept)[:900],
        audience=str(getattr(strategy, "audience_segment", "")),
        key_claim=key_claim,
        run_id=run_id,
    )
    # The engine returns a bare filename and writes into its own STATE_DIR and
    # the dashboard public dir; resolve against both rather than the cwd.
    name = str(result.get("filename") or result.get("path") or "")
    candidates = [Path(name), STATE_DIR / name,
                  REPO_ROOT / "hermes-mission" / "public" / name]
    png = next((c for c in candidates if name and c.exists()), None)
    if png is None:
        # Saying "ok" here would put a broken image path into the review packet.
        raise RuntimeError("visual engine returned no PNG on disk: " + repr(name))
    result["path"] = str(png)
    # VisualPipelineEngine calls nano banana through its own client, so the
    # call never reached the journal and the dashboard showed the one agent
    # with an image model attached as having made zero image calls. Record it
    # from the engine's own result rather than leaving the row blank.
    R.record(R.AgentCall(
        "A08_visual_synthesis", "image", R.MODELS["image"], True,
        round(float(result.get("elapsed_seconds") or 0.0), 2),
        note="novelty=" + str(result.get("novelty_score", "?"))
             + " size=" + str(png.stat().st_size // 1024) + "KB",
        transport="model-garden"))
    R.record_stage("A08_visual_synthesis", "ok",
                   "rendered " + png.name + " ("
                   + str(png.stat().st_size // 1024) + " KB)", outputs=[str(png)])
    return result


# --------------------------------------------------------------------------
# Meme — nano banana pro (gemini-3-pro-image)
# --------------------------------------------------------------------------

def render_meme(blueprint, run_id: str, strategy=None, content_pkg=None) -> str:
    """A08's second pass: a meme, which is a different job from a post.

    The post archetypes are restrained, tonal and character-free. Applying that
    to a meme produced abstract geometry that was on-brand and not funny. A
    meme is a situation someone recognises, so A07 briefs two panels and a
    first-person caption, and the renderer draws it in its own palette.
    """
    from pipeline.gtm_creative.memes import brief_meme, render_meme as draw

    hook, body = "", ""
    try:
        x = content_pkg.channel_posts["x"]
        hook, body = str(x.hook), str(x.copy)
    except Exception:                               # noqa: BLE001 — boundary
        pass

    brief = brief_meme(strategy, hook, body, run_id=run_id)
    out = STATE_DIR / (run_id + "_meme.png")
    path = draw(
        panel_left=str(brief.get("panel_left") or ""),
        panel_right=str(brief.get("panel_right") or ""),
        caption=str(brief.get("caption") or hook)[:120],
        labels=[str(l) for l in (brief.get("labels") or [])][:3],
        out=out,
    )
    R.record(R.AgentCall("A08_visual_synthesis", "meme", R.MODELS["meme"], True,
                         0.0, note="two-panel meme", transport="model-garden"))
    R.record_stage("A08_visual_synthesis", "ok",
                   "meme: " + str(brief.get("caption") or "")[:100],
                   outputs=[str(path)])
    return str(path)


def render_meme_flat(blueprint, run_id: str) -> str:
    """Render the campaign's meme with nano banana pro.

    Attributed to A08: it is the same agent's second output, at a higher tier,
    and the call carries role="meme" so the journal shows which model drew
    which asset rather than collapsing both into "the visual agent".
    """
    from pipeline.scripts.gemini_flash_image import generate_gemini_image

    formats = (getattr(blueprint, "format_specs", None) or {})
    spec = formats.get("MEME_IMAGE")
    prompt = str(getattr(spec, "compiled_prompt", "") or "").strip()
    if len(prompt) < 40:
        raise RuntimeError("no meme prompt on the creative blueprint")

    # STATE_DIR, not the run folder: the dashboard serves panel images
    # through /api/media, which takes a bare filename and looks in
    # pipeline/state. A path under gtm_runs/ resolved to nothing.
    out = STATE_DIR / (run_id + "_meme.png")
    out.parent.mkdir(parents=True, exist_ok=True)

    started = time.time()
    try:
        generate_gemini_image(prompt=prompt, output_path=out,
                              project="vanna-mcp", location="global",
                              model=R.MODELS["meme"], temperature=0.85)
    except Exception as exc:                        # noqa: BLE001 — boundary
        R.record(R.AgentCall("A08_visual_synthesis", "meme", R.MODELS["meme"],
                             False, round(time.time() - started, 2),
                             note=str(exc)[:250], transport="model-garden"))
        raise

    if not out.exists() or out.stat().st_size < 1024:
        raise RuntimeError("meme model returned no usable PNG")

    R.record(R.AgentCall("A08_visual_synthesis", "meme", R.MODELS["meme"], True,
                         round(time.time() - started, 2),
                         note="meme " + str(out.stat().st_size // 1024) + "KB",
                         transport="model-garden"))
    R.record_stage("A08_visual_synthesis", "ok",
                   "rendered meme " + out.name, outputs=[str(out)])
    return str(out)


# --------------------------------------------------------------------------
# A09 — Video Production Engine (Veo 3.1)
# --------------------------------------------------------------------------

def render_video(summary_or_blueprint, run_id: str, *, timeout_s: float = 420.0) -> Optional[str]:
    """A09: a motion graphic built from the run, not a cinematic shot.

    Veo's whole competence is cinematography, so asking it for an explainer got
    films — a slow dolly through a void, and once a glowing Bitcoin coin in a
    vault for a product that is neither a currency nor on mainnet. The founder
    rejected that register; the direction is in
    `pipeline/brain/knowledge/motion-direction.md`.

    So Veo now renders one locked-off flat element and nothing else. The Vanna
    ground, the vignette, every word and the timing are drawn, which means the
    background matches the still post byte for byte and nothing published can
    be misspelt.

    One motion treatment for now. Per-archetype motion — the threshold column
    filling, the composition bar growing — is the next step, and the archetype
    renderers already draw every element it would need.
    """
    from pipeline.gtm_creative.motion import (build_isolation_motion,
                                              element_prompt_for)

    s = summary_or_blueprint if isinstance(summary_or_blueprint, dict) else {}
    posts = (s.get("posts") or {}).get("x") or {}
    out = RUNS_DIR / run_id / (run_id + "_video.mp4")

    # First choice: Veo 3.1 animates this run's own visual, with the camera
    # locked and every word held, prompted with what the founder approved and
    # rejected in past clips, and judged frame by frame against the poster.
    # The hand-described motion graphic below is the fallback.
    visual = s.get("visual_path")
    if visual and Path(str(visual)).exists():
        try:
            from pipeline.gtm_creative import veo_video as VV
            from pipeline.gtm_creative.motion_director import motion_plan
            brief = (str(posts.get("hook") or s.get("signal") or "") + " "
                     + " ".join(str(posts.get("copy") or "").split())[:600])
            # The Motion Director looks at this run's poster and writes its
            # build, beat by beat, from what the founder approved in past
            # clips; Veo 3.1 builds the poster out of the empty ground.
            plan = motion_plan(visual, s.get("poster_brief") or brief)
            s["motion_plan"] = plan["plan"][:2000]
            s["motion_style"] = plan.get("motion_style")
            R.record_stage("A14_motion_director", "ok",
                           "wrote the poster brief and the motion plan (layout "
                           + str(s.get("poster_layout")) + ", motion "
                           + str(plan.get("motion_style")) + ")")
            res = VV.make_build(visual, brief, out, total_s=10.0, attempts=2,
                                directed=plan["prompt"])
            verdicts = [str(a.get("verdict")).upper() for a in res["attempts"]]
            if "SHIP" in verdicts or "REVISE" in verdicts:
                s["video_mode"] = "veo_build"
                s["video_prompt"] = res["attempts"][-1].get("prompt", "")[:1500]
                s["video_review"] = {k: res["attempts"][-1].get(k) for k in
                                     ("verdict", "critique", "fix")}
                R.record_stage("A09_video_production", "ok",
                               "Motion Director planned, Veo 3.1 built the poster from "
                               "the empty ground (10s); judge " + "/".join(verdicts),
                               outputs=[str(out)])
                return str(out)
            R.record_stage("A09_video_production", "degraded",
                           "Veo clip did not pass review ("
                           + str(res["attempts"][-1].get("critique") or "")[:140]
                           + "); falling back to the motion graphic")
        except Exception as exc:                    # noqa: BLE001 — boundary
            R.record_stage("A09_video_production", "degraded",
                           "Veo image-to-video failed: " + str(exc)[:160]
                           + "; falling back to the motion graphic")
    s["video_mode"] = "motion_graphic"

    # Per-run element. The default cache is one shared file, so every cycle
    # reused the same clip and the journal correctly showed no Veo call — the
    # stage reported "ok" for a video it had not made.
    # Words come from the POST, not from the strategy.
    #
    # The first version took the eyebrow from `pillar`, hard-truncated at 60
    # characters so it read "STELLAR SOROBA", and the deck from `opportunity` —
    # which is the internal brief. A frame shipped saying "Position Vanna as
    # the foundational composable credit layer on Soroban", which is what we
    # tell ourselves, not what we tell a reader. The creative judge caught it.
    hook = str(posts.get("hook") or "")
    deck = ""
    for para in str(posts.get("copy") or "").split("\n"):
        line = para.strip()
        if len(line) > 30 and line[:40] not in hook:
            deck = line.split(". ")[0].rstrip(".") + "."
            break

    archetype = str(s.get("visual_archetype") or "")
    path = build_isolation_motion(
        element_mp4=RUNS_DIR / run_id / (run_id + "_element.mp4"),
        # The motion must depict what the post argues. Rendering the isolation
        # grid for a Round Trip post is why the judge rejected the video for
        # showing no mechanism.
        # The subject, so the clip is about THIS post. Without it a
        # health-factor post and a partnership post produced the same video,
        # and the poster archetypes — absent from the element table — fell
        # back to the isolation grid entirely.
        element_prompt=element_prompt_for(
            archetype, hook or str(s.get("signal") or "")),
        eyebrow="Stellar Soroban · testnet",
        headline=(hook or str(s.get("signal") or ""))[:120],
        deck=deck[:150],
        # Only the isolation archetype has a figure that means anything here.
        # "0 accounts exposed" printed under a Round Trip post is a number
        # attached to an argument it is not making.
        stat_value="0" if archetype == "A4_isolation" else "",
        stat_label=("accounts exposed to a neighbour's deficit"
                    if archetype == "A4_isolation" else ""),
        footnote="Stellar Soroban testnet · docs.vanna.finance",
        out=out,
    )
    R.record_stage("A09_video_production", "ok",
                   "motion graphic " + Path(path).name, outputs=[str(path)])
    return str(path)


def render_video_cinematic(blueprint, run_id: str, *, timeout_s: float = 420.0) -> Optional[str]:
    """The previous cinematic path. Kept for a launch film, not for posts.

    Veo runs through Vertex, which needs ADC rather than the API key the other
    agents use. When that is not available this raises and the caller records
    A09 as failed — the cycle still completes with a still image, which is the
    honest outcome rather than a silently video-less run.
    """
    import urllib.error
    import urllib.request

    from pipeline.scripts.veo_broll import _vertex_token, _find_video, _write_video

    # The art director stores the motion prompt as the VEO_VIDEO_31 format's
    # `compiled_prompt`, not as a top-level attribute.
    prompt = ""
    formats = (getattr(blueprint, "format_specs", None)
               or getattr(blueprint, "formats", None) or {})
    for key in ("VEO_VIDEO_31", "veo_video_31"):
        fmt = formats.get(key)
        if fmt is not None:
            prompt = str(getattr(fmt, "compiled_prompt", "") or "")
            break
    if not prompt:
        for fmt in formats.values():
            if str(getattr(fmt, "format_type", "")).upper().startswith("VEO"):
                prompt = str(getattr(fmt, "compiled_prompt", "") or "")
                break
    prompt = prompt.strip()
    if prompt:
        prompt += (
            " ABSOLUTELY NO TEXT: no words, letters, labels, numerals, "
            "readouts, captions, watermarks, icons or logos anywhere in frame "
            "at any point in the shot. The model cannot spell reliably and a "
            "misspelt label ships as a false claim. Convey every quantity and "
            "every named part through form, scale, position and light only. "
            "No cryptocurrency glyphs or coin props. No neon cyberpunk "
            "palette: lighting stays clinical and restrained, with muted "
            "violet and fuchsia confined to the far background.")
    
    if not prompt:
        raise RuntimeError("no Veo prompt on the creative blueprint")

    token = _vertex_token()
    if not token:
        raise RuntimeError("no Vertex token; run `gcloud auth application-default login`")

    host = "https://" + VEO_LOCATION + "-aiplatform.googleapis.com"
    base = (host + "/v1/projects/" + VEO_PROJECT + "/locations/" + VEO_LOCATION
            + "/publishers/google/models/" + R.MODELS["video"])
    headers = {"Authorization": "Bearer " + token,
               "x-goog-user-project": VEO_PROJECT,
               "Content-Type": "application/json"}
    body = {"instances": [{"prompt": prompt}],
            "parameters": {"aspectRatio": "16:9", "sampleCount": 1,
                           "durationSeconds": 8}}

    started = time.time()
    req = urllib.request.Request(base + ":predictLongRunning",
                                 data=json.dumps(body).encode(),
                                 headers=headers, method="POST")
    try:
        op = json.loads(urllib.request.urlopen(req, timeout=90).read())
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")[:300]
        R.record(R.AgentCall("A09_video_production", "video", R.MODELS["video"],
                             False, round(time.time() - started, 2),
                             note="HTTP " + str(exc.code) + ": " + detail,
                             transport="vertex"))
        raise RuntimeError("Veo submit HTTP " + str(exc.code) + ": " + detail) from exc

    op_name = op.get("name")
    if not op_name:
        raise RuntimeError("Veo returned no operation name: " + json.dumps(op)[:200])

    deadline = time.time() + timeout_s
    while time.time() < deadline:
        time.sleep(15)
        poll = urllib.request.Request(
            base + ":fetchPredictOperation",
            data=json.dumps({"operationName": op_name}).encode(),
            headers=headers, method="POST")
        res = json.loads(urllib.request.urlopen(poll, timeout=90).read())
        if not res.get("done"):
            continue
        if res.get("error"):
            raise RuntimeError("Veo failed: " + json.dumps(res["error"])[:250])
        out = STATE_DIR / "gtm_runs" / run_id / (run_id + "_video.mp4")
        out.parent.mkdir(parents=True, exist_ok=True)
        # _find_video returns (inline_base64, uri); _write_video takes both
        # plus the destination and an API key for generativelanguage URIs.
        b64, uri = _find_video(res)
        if not (b64 or uri):
            raise RuntimeError("Veo operation done but carried no video payload")
        if not _write_video(b64, uri, out, None):
            raise RuntimeError("Veo payload could not be written (uri=" + str(uri)[:120] + ")")
        R.record(R.AgentCall("A09_video_production", "video", R.MODELS["video"],
                             True, round(time.time() - started, 2),
                             transport="vertex"))
        R.record_stage("A09_video_production", "ok", "rendered " + out.name,
                       outputs=[str(out)])
        return str(out)

    raise RuntimeError("Veo did not finish within " + str(int(timeout_s)) + "s")


# --------------------------------------------------------------------------
# The cycle
# --------------------------------------------------------------------------

def _assets_wanted(directive: Optional[str]) -> dict[str, bool]:
    """Which assets a directive is actually asking for.

    "Make a post about health factor" asked for a post, and the cycle also
    spent a Veo render and a nano-banana-pro meme on it. Naming one asset now
    means that asset: a directive that says post gets copy and a still, one
    that says video gets a video, one that says meme gets a meme. A directive
    naming none — and every autonomous run — still produces everything.
    """
    d = " " + " ".join(str(directive or "").lower().split()) + " "
    if not d.strip():
        return {"visual": True, "video": True, "meme": True}

    asked = {
        "visual": any(w in d for w in (" post", " thread", " tweet", " visual",
                                       " image", " graphic", " linkedin",
                                       " reddit", " carousel")),
        "video": any(w in d for w in (" video", " clip", " reel", " motion",
                                      " animation")),
        "meme": " meme" in d,
    }
    # Nothing named: the founder described a subject, not a format.
    if not any(asked.values()):
        return {"visual": True, "video": True, "meme": True}
    # A video or a meme still needs the copy it is built from. The video is
    # also built FROM the visual now — Veo builds the poster out of the empty
    # ground — so asking for a video makes the visual too.
    asked["visual"] = asked["visual"] or asked["video"] or not asked["meme"]
    return asked


def run_cycle(directive: Optional[str] = None, *, with_video: bool = True,
              run_id: Optional[str] = None) -> dict[str, Any]:
    from pipeline.gtm_orchestration.intelligence_provider import IntelligenceProvider
    from pipeline.gtm_orchestration.gtm_strategist import GTMStrategist
    from pipeline.gtm_orchestration.content_creator import ContentCreator
    from pipeline.gtm_creative.creative_director_system import CreativeDirectorSystem
    from pipeline.gtm_creative.creative_validator import CreativeValidator
    from pipeline.gtm_content.channel_reviewer import ChannelReviewer
    from pipeline.gtm_machines.machine_library import GTMMachineLibrary
    from pipeline.gtm_campaigns.campaign_selector import CampaignSelector
    from pipeline.gtm_os.telegram_packet import TelegramPacketBuilder

    rid = R.set_run(run_id or R.new_run_id())
    try:
        _claim_lock(rid)
    except AlreadyRunning as exc:
        print("  [skip] " + str(exc))
        return {"run_id": rid, "status": "skipped_locked", "reason": str(exc)}
    t0 = time.time()
    print("=" * 70)
    print("GTM AUTONOMOUS CYCLE  " + rid)
    print("=" * 70)

    summary: dict[str, Any] = {
        "run_id": rid,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "directive": directive,
        "status": "running",
    }

    try:
        ip = IntelligenceProvider()

        # A01 — Intelligence Scout
        from pipeline.gtm_os.live_scout import scout
        signals = _stage("A01_intelligence_scout",
                         lambda: scout(limit=14),
                         detail="scanned live sources", self_recorded=True)
        if not signals:
            raise CycleAbort("no market signals available")

        # A02b — the market reading. Runs against harvest.json rather than the
        # fourteen `scout` returns, because the harvest holds everything the
        # scrape found and that is what the Scraped Intelligence view shows.
        # Reading a ranked subset would grade five signals and leave twenty
        # unread beside them.
        def read_market():
            import json as _json
            from pipeline.gtm_os.market_analyst import analyse
            try:
                raw = (R.RUNS_DIR / rid / "harvest.json").read_text(encoding="utf-8")
                rows = _json.loads(raw).get("signals") or []
            except Exception:                       # noqa: BLE001 — boundary
                rows = signals
            return analyse(rows, run_id=rid)

        reading = _stage("A02_market_analyst", read_market,
                         detail="read the harvest", self_recorded=True)
        if isinstance(reading, dict) and reading.get("landscape"):
            summary["landscape"] = reading["landscape"]

        # What this directive actually asked for. Naming "post" should not
        # also spend a Veo render and a meme.
        wanted = _assets_wanted(directive)
        summary["assets_requested"] = wanted

        # A02 — Opportunity Selector
        def pick():
            if directive:
                # A directive IS the subject. This used to substring-search the
                # directive's first 40 characters inside scraped headlines —
                # "make a post on vanna of liquidation and " never appears in a
                # news headline, so it always fell through to signals[0] and
                # the run proceeded on an unrelated scraped topic while
                # reporting that it had honoured the directive.
                return _directive_signal(directive, signals)
            return _select_signal(signals)
        signal = _stage("A02_opportunity_selector", pick,
                        detail="chose a signal to pursue")
        summary["signal"] = str(signal.headline)
        summary["signal_source_type"] = str(signal.source_type)
        summary["signal_source"] = str(getattr(signal, "source", "") or "")
        summary["signal_observed_at"] = str(signal.observed_at)
        SIGNALS.clear()
        SIGNALS.extend(signals)
        summary["candidate_signals"] = [
            {"headline": str(s.headline)[:160], "source_type": str(s.source_type),
             "observed_at": str(s.observed_at)[:19]}
            for s in signals[:14]
        ]
        if SELECTION:
            summary["selection"] = dict(SELECTION)

        # A03 — GTM Strategist
        strategist = GTMStrategist(intelligence_provider=ip)
        strategy = _stage("A03_gtm_strategist",
                          lambda: strategist.evaluate_and_formulate_strategy(signal),
                          detail="formulated strategy")
        summary["action_status"] = strategy.action_status
        summary["machine"] = strategy.gtm_machine_id
        summary["pillar"] = strategy.narrative_pillar
        summary["strategy_reasoning"] = [str(r)[:300] for r in (strategy.reasoning or [])][:10]
        summary["problem"] = str(strategy.problem)[:600]
        summary["opportunity"] = str(strategy.strategic_opportunity)[:600]
        summary["audience"] = str(strategy.audience_segment)[:200]
        summary["proof_claims"] = [str(c)[:240] for c in (strategy.proof or [])][:10]
        _emit_strategy(strategy, signal)

        # A03 declining is correct behaviour — its default posture is
        # rejection. When A02 chose the subject itself, trying the runners-up
        # is right: the other fifteen signals A01 gathered are all equally
        # valid candidates and one of them may be usable.
        #
        # When the FOUNDER named the subject it is not. Asking for a post
        # about a Stellar partnership and receiving one about tokenised
        # lending is the substitution this whole engine is built to refuse —
        # the run reported success over a topic nobody asked for. If a
        # directive is declined, that decline is the answer, and it is
        # reported with A03's reason so the directive can be rephrased.
        if directive and strategy.action_status != "ACTION":
            summary["status"] = strategy.action_status
            summary["reason"] = (
                "A03 declined the founder directive and no substitute was "
                "made: " + str(strategy.no_action_rationale
                                or strategy.kill_rationale or "")[:400])
            R.record_decision("A03_gtm_strategist", "declined", {
                "signal": str(signal.headline)[:200],
                "verdict": strategy.action_status,
                "rationale": summary["reason"][:400],
                "note": "directive honoured; no scraped topic substituted",
            })
            for skipped in ("A04_machine_library", "A05_campaign_engine",
                            "A06_channel_adapter", "A07_creative_director",
                            "A08_visual_synthesis", "A09_video_production",
                            "A10_reviewer_firewall", "A11_dispatch_worker",
                            "A12_telegram_gateway", "A14_motion_director",
                            "A15_creative_judge"):
                R.record_stage(skipped, "skipped",
                               "directive declined by A03")
            return _finish(summary, t0, rid)

        attempts = 1
        tried = {str(signal.headline)}
        # The runner-ups must respect topic memory too. Walking raw SIGNALS
        # here re-selected a subject A02 had just suppressed — the retry
        # quietly undid the no-repeat rule it was meant to work alongside.
        from pipeline.gtm_os import topic_memory as _TM
        fresh_pool, recent_pool = _TM.split_fresh(SIGNALS)
        # Novelty first, but relevance wins over novelty when the alternative
        # is producing nothing: a subject covered four cycles ago beats an
        # off-domain listicle A03 will decline anyway.
        retry_pool = fresh_pool + recent_pool
        while strategy.action_status != "ACTION" and attempts < 3:
            nxt = next((s for s in retry_pool if str(s.headline) not in tried), None)
            if nxt is None:
                break
            tried.add(str(nxt.headline))
            attempts += 1
            print("  [retry] A03 said " + str(strategy.action_status)
                  + "; trying next signal (" + str(attempts) + "/3)")
            signal = nxt
            strategy = _stage(
                "A03_gtm_strategist",
                lambda s=nxt: strategist.evaluate_and_formulate_strategy(s),
                detail="formulated strategy on runner-up signal")
            summary["signal"] = str(nxt.headline)[:300]
            summary["signal_source_type"] = str(nxt.source_type)
            summary["action_status"] = strategy.action_status
            summary["machine"] = strategy.gtm_machine_id
            summary["pillar"] = strategy.narrative_pillar
            summary["strategy_reasoning"] = [
                str(r)[:300] for r in (strategy.reasoning or [])][:10]
            summary["problem"] = str(strategy.problem)[:600]
            summary["opportunity"] = str(strategy.strategic_opportunity)[:600]
            summary["audience"] = str(strategy.audience_segment)[:200]
            summary["proof_claims"] = [str(c)[:240] for c in (strategy.proof or [])][:10]
            _emit_strategy(strategy, nxt)
            # Record the subject actually pursued, not just A02's first pick,
            # or a retried topic never enters the memory and can repeat.
            _TM.remember(str(nxt.headline), rid)
        summary["strategy_attempts"] = attempts

        if strategy.action_status != "ACTION":
            summary["status"] = strategy.action_status
            summary["reason"] = (strategy.no_action_rationale
                                 or strategy.kill_rationale or "")
            for skipped in ("A04_machine_library", "A05_campaign_engine",
                            "A06_channel_adapter", "A07_creative_director",
                            "A08_visual_synthesis", "A09_video_production",
                            "A10_reviewer_firewall", "A11_dispatch_worker",
                            "A12_telegram_gateway", "A14_motion_director",
                            "A15_creative_judge"):
                R.record_stage(skipped, "skipped",
                               "strategy returned " + strategy.action_status)
            return _finish(summary, t0, rid)

        # A04 — Machine Library
        # The machine's standing with the founder goes on A04's line, so the
        # dashboard shows whether a learned preference was followed.
        try:
            from pipeline.gtm_learning.preferences import posteriors as _post
            _mp = _post("machine").get(str(strategy.gtm_machine_id))
            from pipeline.gtm_learning.preferences import record_text as _rt
            _rec = (" · founder: " + _rt(_mp)) if _mp else " · not yet reviewed"
        except Exception:                           # noqa: BLE001 — boundary
            _rec = ""
        machine = _stage("A04_machine_library",
                         lambda: GTMMachineLibrary().get_machine(strategy.gtm_machine_id),
                         detail="verified machine " + str(strategy.gtm_machine_id) + _rec)
        if machine is not None:
            summary["machine_name"] = str(getattr(machine, "name", ""))
            summary["machine_evidence"] = [
                str(x) for x in (getattr(machine, "independent_campaign_examples", []) or [])][:4]
            summary["machine_sources"] = [
                str(x) for x in (getattr(machine, "source_references", []) or [])][:4]

        # A05 — Campaign & Series Engine
        selection = _stage("A05_campaign_engine",
                           lambda: CampaignSelector().select_structural_vehicle(strategy),
                           detail="selected campaign vehicle")

        # A06 — Content Creator / Channel Adapter
        content_pkg = _stage(
            "A06_channel_adapter",
            lambda: ContentCreator().create_content_package(
                strategy, campaign_id=getattr(selection, "spec_id", None)),
            detail="generated channel posts")
        summary["posts"] = {
            k: {"hook": str(getattr(v, "hook", ""))[:300],
                "copy": str(getattr(v, "copy", ""))[:4000]}
            for k, v in (content_pkg.channel_posts or {}).items()
        }

        # A07 — Creative Director System
        blueprint = _stage(
            "A07_creative_director",
            lambda: CreativeDirectorSystem().compile_master_blueprint(strategy, content_pkg),
            detail="art-directed the campaign")
        summary["visual_concept"] = str(blueprint.visual_metaphor.concept)[:600]
        R.record_decision("A07_creative_director", "directed", {
            "concept": str(blueprint.visual_metaphor.concept)[:400],
            "metaphor": str(getattr(blueprint.visual_metaphor, "family", ""))[:120],
        })
        # Store the generated prompts. When an asset comes back wrong the first
        # question is what was actually asked for, and that was unrecoverable.
        _fs = getattr(blueprint, "format_specs", {}) or {}
        summary["prompts"] = {
            k: str(getattr(v, "compiled_prompt", ""))[:1500]
            for k, v in _fs.items()
        }

        # A08 — Visual Synthesis Engine (nano banana)
        visual = None if not wanted["visual"] else _stage("A08_visual_synthesis",
                        lambda: render_visual(strategy, content_pkg, blueprint, rid,
                              str(signal.headline)),
                        required=False, self_recorded=True)
        if visual:
            summary["visual_path"] = visual.get("path") or visual.get("filename")
            summary["visual_archetype"] = visual.get("archetype")
            summary["visual_renderer"] = visual.get("renderer", "code_set")
            if visual.get("visual_review"):
                summary["visual_review"] = visual["visual_review"]
            if visual.get("poster_brief"):
                summary["poster_brief"] = visual["poster_brief"][:2000]
            if visual.get("poster_layout"):
                summary["poster_layout"] = visual["poster_layout"]
            summary["visual_why"] = visual.get("why")
            summary["visual_public_url"] = visual.get("public_url")

        # Meme — same agent, nano banana pro
        if not wanted["meme"]:
            R.record_stage("A08_visual_synthesis", "skipped",
                           "meme not requested by this directive")
        meme = None if not wanted["meme"] else _stage("A08_visual_synthesis",
                      lambda: render_meme(blueprint, rid, strategy, content_pkg),
                      required=False,
                      detail="rendered the meme", self_recorded=True)
        if meme:
            summary["meme_path"] = meme

        # A09 — Video Production Engine (Veo 3.1)
        if with_video and not wanted["video"]:
            R.record_stage("A09_video_production", "skipped",
                           "video not requested by this directive")
        if with_video and wanted["video"]:
            video = _stage("A09_video_production",
                           lambda: render_video(summary, rid),
                           required=False, self_recorded=True)
            if video:
                summary["video_path"] = video
        else:
            R.record_stage("A09_video_production", "skipped",
                           "video disabled for this run (--no-video)")

        # A07 again — the creative director judges what was actually made.
        # Until this existed nothing looked at the produced assets: A08 checked
        # resolution and corner luminance, A09 checked only that an MP4 came
        # back, and neither could tell whether the image was about Vanna.
        def judge():
            from pipeline.gtm_os.creative_judge import judge_assets
            return judge_assets(summary, rid)

        creative_verdict = _stage("A15_creative_judge", judge,
                                  required=False, self_recorded=True)
        if creative_verdict:
            summary["creative_review"] = creative_verdict
            summary["creative_verdict"] = creative_verdict.get("overall")
            R.record_decision("A15_creative_judge", "judged", {
                "overall": creative_verdict.get("overall"),
                "copy_verdict": creative_verdict.get("copy_verdict"),
                "assets": [
                    {"asset": k, "verdict": v.get("verdict"),
                     "critique": str(v.get("critique") or "")[:300]}
                    for k, v in creative_verdict.items()
                    if isinstance(v, dict) and v.get("verdict")
                ],
            })

        # A10 — Pre-Delivery Reviewer Firewall
        def review():
            channel_verdict = ChannelReviewer().review_channel_adaptation(content_pkg)
            slop_verdict = CreativeValidator().validate_blueprint(
                blueprint, raw_post_copy=content_pkg.channel_posts["x"].copy)
            return channel_verdict, slop_verdict
        verdicts = _stage("A10_reviewer_firewall", review,
                          detail="ran the pre-delivery firewalls")
        channel_verdict, creative_verdict = verdicts
        # A judge whose rejection changes nothing is decoration. A creative
        # REJECT blocks the run the same way a channel or slop failure does.
        creative_rejected = str(summary.get("creative_verdict") or "").upper() == "REJECT"
        passed = bool(channel_verdict.approved and creative_verdict.approved
                      and not creative_rejected)
        summary["review_passed"] = passed
        # Every reason the gate can block for, not two of them. A run was
        # recorded review_blocked with blocked_claims and slop both empty and
        # the creative verdict SHIP — the cause was a channel issue, which
        # these notes did not carry, so the dashboard showed a block with no
        # reason at all.
        summary["review_notes"] = {
            "blocked_claims": list(getattr(channel_verdict, "blocked_unsupported_claims", []) or []),
            "channel_issues": dict(getattr(channel_verdict, "channel_issues", {}) or {}),
            "claim_provenance": bool(getattr(channel_verdict, "claim_provenance_verified", True)),
            "distinctness": getattr(channel_verdict, "distinctness_score", None),
            "slop": list(getattr(creative_verdict, "slop_violations", []) or []),
            "validator": (None if getattr(creative_verdict, "approved", True)
                          else str(getattr(creative_verdict, "reasoning", ""))[:300]),
            "creative": summary.get("creative_verdict"),
        }
        R.record_decision("A10_reviewer_firewall",
                          "reviewed" if passed else "declined", {
            "passed": passed,
            "blocked_claims": summary["review_notes"]["blocked_claims"][:6],
            "slop": summary["review_notes"]["slop"][:6],
            "creative": summary.get("creative_verdict"),
        })

        # A11 — Approved Dispatch Worker. It dispatches only what a human has
        # approved, and no human has seen this yet, so it is correctly idle.
        R.record_stage("A11_dispatch_worker", "skipped",
                       "awaiting human approval; dispatch never runs unprompted")

        # A12 — Telegram Gateway
        # A12 builds the packet AND delivers it. Building alone left the
        # documented terminus of the system unreachable: the cycle assembled a
        # review packet and put it on disk, where no human was looking.
        packet = _stage(
            "A12_telegram_gateway",
            lambda: TelegramPacketBuilder.build_packet(
                signal=signal, strategy=strategy, claims=strategy.claims,
                machine=strategy.gtm_machine_id, campaign=selection,
                content_pkg=content_pkg, creative_brief=blueprint,
                review_result=None),
            required=False, detail="built the human review packet")
        if packet is not None:
            summary["packet_built"] = True

            def deliver():
                from pipeline.gtm_os.telegram_packet import TelegramPacketBuilder
                from pipeline.gtm_os.telegram_sender import send_review
                md = None
                try:
                    md = TelegramPacketBuilder.render_telegram_markdown(packet)
                except Exception:                   # noqa: BLE001 — boundary
                    pass                            # fall back to our own text
                return send_review(summary, rid, markdown=md)

            delivery = _stage("A12_telegram_gateway", deliver,
                              required=False, self_recorded=True)
            if delivery:
                summary["review_delivery"] = delivery

        # A13 — Closed-Loop Learning Engine
        # Self-recorded: A13 writes what it learned ("learned from N founder
        # decisions…" / "no founder decisions yet…"), and the wrapper's
        # generic line after it was what the dashboard showed instead.
        _stage("A13_learning_engine", lambda: _run_learning(summary), required=False,
               self_recorded=True)

        summary["status"] = "completed" if passed else "review_blocked"
        return _finish(summary, t0, rid)

    except CycleAbort as exc:
        summary["status"] = "aborted"
        summary["reason"] = str(exc)
        return _finish(summary, t0, rid)
    except Exception as exc:                        # noqa: BLE001 — boundary
        summary["status"] = "failed"
        summary["reason"] = type(exc).__name__ + ": " + str(exc)
        summary["traceback"] = traceback.format_exc()[-2000:]
        return _finish(summary, t0, rid)
    finally:
        _release_lock()


SELECTION: dict = {}
# Every signal A01 gathered this cycle. The Ideas Panel proposes from
# the ones A02 did not choose, which were previously thrown away.
SIGNALS: list = []


def _directive_signal(directive: str, signals):
    """Turn a founder directive into the subject the cycle pursues.

    The directive is authoritative: if the founder asks for liquidation and
    health factor, that is the post, regardless of what today's scrape found.
    Scraped signals are still useful as supporting evidence, so the closest
    one by word overlap is attached — but it never replaces the subject.
    """
    from pipeline.gtm_orchestration.schemas import MarketSignal

    # A directive is phrased as an instruction — "make a post on vanna of
    # liquidation and health factor". That string becomes the signal headline
    # and is interpolated into copy and visuals, so the instruction wrapper is
    # stripped first: otherwise a hook reads "The hidden math behind make a
    # post on vanna of...".
    text = " ".join(str(directive).split())
    text = re.sub(
        r"^(?:please\s+)?(?:can you\s+)?"
        r"(?:make|write|draft|create|generate|do|build|give me|prepare|"
        r"explain|show|cover|tell me about)\s+"
        r"(?:me\s+)?(?:a|an|the)?\s*"
        r"(?:post|thread|article|piece|content|video|meme|visual)?\s*"
        r"(?:on|about|for|of|re)?\s+",
        "", text, flags=re.I).strip()
    # "vanna of liquidation and health factor" -> "liquidation and health
    # factor". Only when a possessive-style connector follows: stripping it
    # unconditionally turned "vanna with partnership with stellar" into the
    # fragment "with partnership with stellar", which A03 then read as a
    # generic partnership shout-out and correctly declined.
    text = re.sub(r"^(?:vanna(?:'s)?|for vanna)\s+(?:of|on|about)\s+", "",
                  text, flags=re.I).strip()
    # Any preposition left stranded at the front is an artefact of stripping,
    # never part of the subject.
    text = re.sub(r"^(?:with|of|on|about|for|re)\s+", "", text, flags=re.I).strip()
    text = text or " ".join(str(directive).split())
    # Cut at a word, not mid-word. At 280 characters a directive ending "make
    # the post highly saveable and shareable" reached every agent as "...and
    # sh" — the founder's format requirement was the part that got lost.
    if len(text) > 600:
        text = text[:600].rsplit(" ", 1)[0]

    # Support is matched on SUBJECT words only. Every word of four letters or
    # more used to count, as a substring, so "explain", "crypto", "simple"
    # and "understand" matched "What is liquidation in crypto?" to a request
    # about LIQUIDITY. That headline was then handed to A03 as the related
    # signal, and A03 wrote about liquidation. Instruction and format words
    # are not the subject; whole words only.
    _NOT_SUBJECT = {
        "create", "make", "write", "draft", "post", "posts", "thread", "twitter",
        "educational", "explain", "explaining", "explains", "simple", "language",
        "audience", "understand", "understands", "understanding", "concept",
        "technical", "problem", "works", "work", "matters", "matter", "fits",
        "picture", "highly", "saveable", "shareable", "vanna", "vannas",
        "crypto", "defi", "users", "user", "people", "that", "this", "with",
        "into", "about", "their", "them", "they", "what", "your", "have",
        "should", "could", "would", "also", "more", "most", "very", "just",
        "like", "want", "need", "show", "shows", "does", "make", "made",
    }
    words = {w for w in re.findall(r"[a-z]{4,}", text.lower())} - _NOT_SUBJECT

    def overlap(s) -> int:
        head = set(re.findall(r"[a-z]{4,}", str(getattr(s, "headline", "")).lower()))
        return len(words & head)

    support = max(signals, key=overlap, default=None) if signals else None
    if support is not None and overlap(support) == 0:
        support = None

    R.record_decision("A02_opportunity_selector", "chose", {
        "chosen": text,
        "why": "founder directive — the subject was given, not selected",
        "chosen_source": "FOUNDER_DIRECTIVE",
        "candidates": len(signals),
        "supporting_signal": str(getattr(support, "headline", "")) if support else None,
    })

    now = datetime.now(timezone.utc).isoformat()
    return MarketSignal(
        signal_id="SIG-DIRECTIVE-" + datetime.now(timezone.utc).strftime("%H%M%S"),
        headline=text,
        description=(
            "FOUNDER DIRECTIVE. The founder has asked for a post on this "
            "subject; it is an instruction, not a news signal to be judged "
            "for newsworthiness. Find Vanna's architectural angle on it. "
            "Subject: " + text
            + (" — possibly related market signal (context only; it does "
               "not change the subject): " + str(support.headline)[:200]
               if support is not None else "")
        )[:1400],
        market_category="LENDING",
        entities_involved=["Vanna"],
        observed_metric_change="FOUNDER_DIRECTIVE",
        source="founder-directive",
        source_root="founder",
        dataset="directive",
        source_type="LIVE_OBSERVED",
        record_id="SIG-DIRECTIVE",
        observed_at=now,
        data_as_of=now[:10],
        confidence="HIGH",
        evidence_status="OBSERVED",
    )


def _emit_strategy(strategy, signal) -> None:
    """Publish A03's verdict to the live journal as soon as it has one."""
    R.record_decision(
        "A03_gtm_strategist",
        "formulated" if strategy.action_status == "ACTION" else "declined",
        {
            "signal": str(getattr(signal, "headline", ""))[:200],
            "verdict": strategy.action_status,
            "pillar": strategy.narrative_pillar,
            "machine": strategy.gtm_machine_id,
            "audience": str(strategy.audience_segment)[:200],
            "problem": str(strategy.problem)[:400],
            "opportunity": str(strategy.strategic_opportunity)[:400],
            "reasoning": [str(r)[:300] for r in (strategy.reasoning or [])][:6],
            "rationale": str(strategy.no_action_rationale
                             or strategy.kill_rationale or "")[:400],
        })


def _select_signal(signals):
    """A02: judge which signal is worth a campaign, with reasons for the rest."""
    from pipeline.gtm_os import topic_memory as TM

    # Subjects covered in the last few cycles are removed from the candidate
    # set rather than discouraged in the prompt. A02 was not misbehaving — it
    # reasoned over the same candidates each run and correctly picked the same
    # winner, which is how 32 of 41 runs became the same Blend v2 topic. A
    # candidate that is absent cannot be chosen; an instruction can be ignored.
    fresh, stale = TM.split_fresh(signals)
    suppressed = len(stale)
    if fresh:
        signals = fresh
    else:
        # Everything is stale — a narrow scrape day. Proceed on the full set
        # rather than skipping the run, and say so in the record.
        suppressed = 0

    # Widening the sources took the candidate list from ~13 to ~26, and a
    # rejection note for every one of them overran the output budget — the
    # model was cut off mid-string and the run aborted on unparseable JSON.
    # Cap what is shown, cap how many rejections are asked for, and give the
    # reply room.
    signals = signals[:16]

    listing = "\n".join(
        "- [" + str(i) + "] " + str(s.headline)[:140]
        + "  (source: " + str(s.source_type) + ")"
        for i, s in enumerate(signals))
    system = (
        "You select which market signal Vanna should build a campaign on. "
        "Vanna is composable credit infrastructure on Stellar Soroban testnet. "
        "Prefer a signal where Vanna has a specific architectural answer over "
        "one that is merely popular.\n"
        "Never choose a signal that is primarily token-price movement, price "
        "targets, market-cap or trading speculation. Vanna is on testnet and "
        "cannot assert live TVL or price, so A03 rejects those outright and "
        "the cycle produces nothing — pick a mechanism, risk, architecture or "
        "incident story instead.\n"
        "Return strict JSON and keep every rationale under 30 words.")
    # What the founder approved and killed before. Empty until a run has been
    # reviewed; after that the choice leans toward subjects that worked.
    try:
        from pipeline.gtm_learning.preferences import prompt_block as _learned
        record = _learned(for_agent="A02")
    except Exception:                               # noqa: BLE001 — boundary
        record = ""
    data = R.brain_json(
        (record + "\n\n" if record else "")
        + "CANDIDATE SIGNALS\n" + listing + "\n\n"
        'Return {"index": int, "why": str, "rejected": [{"index": int, "why": str}]}\n\n'
        "Include at most 6 entries in rejected — the closest runners-up, not "
        "every candidate. Keep each why under 30 words.",
        agent="A02_opportunity_selector", role="reasoning", system=system,
        temperature=0.2, max_output_tokens=3072)
    idx = int(data.get("index", 0))
    if not 0 <= idx < len(signals):
        idx = 0
    # The rejections are the interesting half of a selection and were being
    # thrown away: "why not the other eleven" is what makes the choice
    # inspectable rather than an arbitrary index.
    SELECTION.clear()
    SELECTION.update({
        "chosen": str(signals[idx].headline)[:200],
        "chosen_source": str(signals[idx].source_type),
        "why": str(data.get("why") or "")[:600],
        "rejected": [
            {"headline": str(signals[int(r.get("index", -1))].headline)[:160]
                         if 0 <= int(r.get("index", -1)) < len(signals) else "?",
             "why": str(r.get("why") or "")[:300]}
            for r in (data.get("rejected") or [])[:8]
            if isinstance(r, dict)
        ],
        "candidates": len(signals),
        # Inspectable: how many subjects were held back as recently covered,
        # so a narrow cycle reads as "the scrape was thin" rather than "the
        # selector keeps choosing the same thing".
        "suppressed_as_recent": suppressed,
        "recently_covered": [
            str(getattr(s, "headline", s))[:120] for s in stale[:6]],
    })
    TM.remember(str(signals[idx].headline), R.current_run())
    # Emit now, so a live view can show what A02 chose and turned down while
    # A03 is still working. Previously this only reached summary.json at the
    # end of the run.
    R.record_decision("A02_opportunity_selector", "chose", dict(SELECTION))
    return signals[idx]


def _run_learning(summary: Optional[dict] = None):
    """A13: coach, then adjust pattern weights and read the adjustment.

    The engine on its own is a group-by and a weight nudge — it can tell that
    PAT_01 moved from 1.0 to 1.15 but not whether that is a real signal or two
    lucky posts. Declaring A13 model-backed while it made no model call was one
    of the rows the dashboard could not honestly fill, so the judgement step is
    real: the model reads the adjustments and says what it would change.
    """
    from pipeline.gtm_learning.learning_engine import LearningEngine
    from pipeline.gtm_learning import preferences as P

    # The Coach first: it studies the founder's new decisions (writing why an
    # approved poster or clip worked, or the rule a kill implies) and this
    # run's own assets against the judges' notes, so the rules and examples
    # the next run reads already include what this one taught.
    coach_line = ""
    try:
        from pipeline.gtm_learning import coach as C
        studied = C.learn_from_decisions()
        new_rules = C.review_run(summary or {}) if summary else []
        parts = []
        if studied.get("studied"):
            parts.append(str(studied["studied"]) + " founder decision(s) studied")
        if studied.get("notes"):
            parts.append(str(studied["notes"]) + " exemplar note(s) written")
        if studied.get("rules") or new_rules:
            parts.append(str(studied.get("rules", 0) + len(new_rules)) + " rule(s) learned")
        if parts:
            coach_line = " | coach: " + ", ".join(parts)
        if new_rules:
            R.record_decision("A16_coach", "coach_rules", {"rules": new_rules})
        from pipeline.gtm_creative.creative_rules import learned_rules
        R.record_stage("A16_coach", "ok",
                       (", ".join(parts) if parts else "reviewed the run, nothing new to teach")
                       + " | " + str(len(learned_rules())) + " learned rules active")
    except Exception as exc:                        # noqa: BLE001 — boundary
        coach_line = " | coach failed: " + str(exc)[:80]
        R.record_stage("A16_coach", "degraded", "coach failed: " + str(exc)[:160])

    # The founder's decisions are the reward that exists today; post metrics
    # come later. The snapshot is what A03, A06 and A07 read on the next run.
    snap = P.snapshot()
    learned = None
    rend = snap.get("visual_renderers") or {}
    rated = sum(int(p.get("n", 0)) for p in rend.values())
    rend_line = coach_line
    if rated:
        lead = max(rend, key=lambda k: rend[k]["mean"])
        rend_line += (" | visuals: " + lead + " preferred ("
                     + ", ".join(k + " " + str(v["mean"]) for k, v in rend.items())
                     + "; " + str(rated) + " rated)")
    try:
        from pipeline.gtm_creative.veo_video import _rows as _vrows
        _vr = _vrows()
        if _vr:
            rend_line += (" | videos: " + str(len(_vr)) + " rated, "
                          + str(sum(1 for r in _vr if r.get("score", 0) >= 0.7))
                          + " approved as Veo examples")
    except Exception:                               # noqa: BLE001 — boundary
        pass
    if snap["reviewed_runs"]:
        v = snap["verdicts"]
        best = {d: max(ps.items(), key=lambda kv: kv[1]["mean"])[0]
                for d, ps in snap["dimensions"].items() if ps}
        learned = {"reviewed_runs": snap["reviewed_runs"], "verdicts": v,
                   "leading": best, "retired": snap["retired"]}
        R.record_stage(
            "A13_learning_engine", "ok",
            "learned from " + str(snap["reviewed_runs"]) + " founder decisions ("
            + ", ".join(k + " " + str(n) for k, n in v.items()) + ")"
            + (" | leading archetype " + str(best.get("visual_archetype"))
               if best.get("visual_archetype") else "")
            + (" | retired " + ", ".join(sum(snap["retired"].values(), []))
               if any(snap["retired"].values()) else "")
            + rend_line)
        R.record_decision("A13_learning_engine", "preferences", learned)
    else:
        R.record_stage("A13_learning_engine", "ok",
                       "no run decisions yet — approve, revise or kill a run"
                       + rend_line)

    adjustments = LearningEngine().process_feedback_loop()
    rows = []
    for a in adjustments:
        rows.append({
            "pattern": getattr(a, "pattern_id", None) or getattr(a, "campaign_id", "?"),
            "from": getattr(a, "previous_weight", None),
            "to": getattr(a, "new_weight", None),
            "reason": str(getattr(a, "rationale", ""))[:300],
        })

    if not rows:
        # No post metrics yet — the stage line above already says what was
        # learned from founder decisions, so this adds nothing more.
        return {"adjustments": 0, "verdict": None, "preferences": learned}

    verdict = R.brain_json(
        "PATTERN WEIGHT ADJUSTMENTS MADE THIS CYCLE\n"
        + json.dumps(rows, default=str)[:3000] + "\n\n"
        'Return {"trustworthy": bool, "why": str, '
        '"recommended_next_test": str, "sample_size_concern": bool}',
        agent="A13_learning_engine", role="reasoning",
        system=("You audit a marketing feedback loop. Weight changes driven by "
                "a handful of posts are noise, not learning. Say so plainly "
                "when the sample is too small to support the adjustment."),
        temperature=0.2, max_output_tokens=1024)
    return {"adjustments": len(rows), "verdict": verdict, "preferences": learned}


def _finish(summary: dict, t0: float, rid: str) -> dict:
    summary["duration_s"] = round(time.time() - t0, 2)
    summary["ended_at"] = datetime.now(timezone.utc).isoformat()

    d = RUNS_DIR / rid
    d.mkdir(parents=True, exist_ok=True)

    calls = []
    cf = d / "calls.jsonl"
    if cf.exists():
        for line in cf.read_text(encoding="utf-8").splitlines():
            if line.strip():
                calls.append(json.loads(line))
    # calls.jsonl also carries deterministic work — A08 records the drawn
    # lockup there so the journal shows every step, with model=None and
    # transport="deterministic". Those are not model calls: counting them
    # inflated model_calls, and the dashboard's spend view read them back as
    # a model literally named "unknown".
    def _is_model_call(c: dict) -> bool:
        return bool(c.get("model")) and c.get("transport") != "deterministic"

    model_calls = [c for c in calls if _is_model_call(c)]
    summary["model_calls"] = len(model_calls)
    summary["model_calls_ok"] = sum(1 for c in model_calls if c.get("ok"))
    summary["input_tokens"] = sum(c.get("input_tokens", 0) for c in model_calls)
    summary["output_tokens"] = sum(c.get("output_tokens", 0) for c in model_calls)
    summary["models_used"] = sorted({c["model"] for c in model_calls})
    # Per model, not just the union of names. A run's cost cannot be computed
    # from a total token count and a list of models: an image or video call
    # reports no tokens and is billed per call, so the two media models that
    # account for ~97% of a full run's spend were invisible to any arithmetic
    # done downstream. This is the tally the rate table is applied to.
    by_model: dict[str, dict[str, int]] = {}
    for c in model_calls:
        m = by_model.setdefault(str(c["model"]),
                                {"calls": 0, "input_tokens": 0, "output_tokens": 0})
        m["calls"] += 1
        m["input_tokens"] += int(c.get("input_tokens") or 0)
        m["output_tokens"] += int(c.get("output_tokens") or 0)
    summary["spend_by_model"] = by_model
    # Kept separate rather than dropped: the deterministic steps are real work
    # and the journal should still say they happened.
    summary["deterministic_steps"] = len(calls) - len(model_calls)

    stages = []
    sf = d / "stages.jsonl"
    if sf.exists():
        for line in sf.read_text(encoding="utf-8").splitlines():
            if line.strip():
                stages.append(json.loads(line))
    # Last write per agent wins, so a stage that recovered is not reported by
    # its first attempt.
    by_agent = {}
    for s in stages:
        prior = by_agent.get(s["agent"])
        merged = dict(s)
        if prior:
            # `_stage` writes a row after the agent may already have written
            # its own with the artifact paths attached. Last-write-wins alone
            # discards those outputs, which is why the dashboard had a rendered
            # PNG on disk and no link to it.
            outs = list(prior.get("outputs") or []) + list(s.get("outputs") or [])
            seen, uniq = set(), []
            for o in outs:
                if o not in seen:
                    seen.add(o); uniq.append(o)
            merged["outputs"] = uniq
            # An agent's own status wins over the wrapper's.
            #
            # `_stage` writes "ok" whenever the callable returns without
            # raising, but an agent can return normally having degraded — A06
            # falls back to deterministic synthesis when its model call fails
            # and records that itself. Last-write-wins then overwrote
            # "degraded" with "ok", so a silent degradation reported as
            # success. That is precisely the failure this whole rebuild
            # existed to remove, reintroduced by the wrapper.
            RANK = {"ok": 0, "skipped": 0, "degraded": 1, "failed": 2}
            if RANK.get(prior.get("status"), 0) > RANK.get(s.get("status"), 0):
                merged["status"] = prior["status"]
                merged["detail"] = (str(prior.get("detail", ""))
                                    + " | later stage reported "
                                    + str(s.get("status")))
        by_agent[s["agent"]] = merged
    summary["agents"] = [by_agent.get(a, {"agent": a, "name": R.AGENT_NAMES[a],
                                          "status": "never_ran"})
                         for a in R.AGENT_ROLES]
    summary["agents_ran"] = sum(1 for a in summary["agents"]
                                if a.get("status") in ("ok", "degraded"))

    (d / "summary.json").write_text(json.dumps(summary, indent=2, default=str),
                                    encoding="utf-8")

    try:
        publish_panels(summary, rid)
    except Exception as exc:                        # noqa: BLE001 — boundary
        # A panel write must never take down a finished run.
        print("  [warn] panel publish failed: " + str(exc)[:160])

    # Push to GCS. The deployed dashboard has no access to this filesystem, so
    # without this it renders a working system as an empty one. A push failure
    # is reported and ignored: the run is already complete and its assets are
    # already on disk.
    try:
        from pipeline.gtm_os.state_sync import push_all
        sync = push_all(rid, summary)
        summary["state_sync"] = sync
        n = (sync.get("run") or {}).get("objects", 0)
        print("  [sync] " + str(n) + " object(s) to GCS"
              if n else "  [sync] nothing pushed: "
              + str((sync.get("run") or {}).get("reason", "")))
        (d / "summary.json").write_text(
            json.dumps(summary, indent=2, default=str), encoding="utf-8")
    except Exception as exc:                        # noqa: BLE001 — boundary
        print("  [warn] state sync failed: " + str(exc)[:160])
    print("-" * 70)
    print("status          : " + str(summary["status"]))
    print("agents ran      : " + str(summary["agents_ran"]) + "/13")
    print("model calls     : " + str(summary["model_calls_ok"]) + "/"
          + str(summary["model_calls"]) + " ok")
    print("models used     : " + ", ".join(summary["models_used"]))
    print("duration        : " + str(summary["duration_s"]) + "s")
    return summary


# --------------------------------------------------------------------------
# Panel feeds — each agent's output in the section that shows it
# --------------------------------------------------------------------------

PANELS_DIR = STATE_DIR / "panels"


def _panel_write(name: str, key: str, entry: dict, keep: int = 24) -> None:
    """Prepend one entry to a dashboard panel file.

    The Crypto Memes and Ideas panels were fed only by their own scheduler
    jobs, so a GTM cycle could render a meme with nano banana pro and select a
    topic with A02 and neither appeared in the section named after it. The
    agents' own output now lands in the panel a user would look for it in.
    """
    PANELS_DIR.mkdir(parents=True, exist_ok=True)
    path = PANELS_DIR / name
    try:
        doc = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    except Exception:                               # noqa: BLE001 — boundary
        doc = {}
    items = [i for i in (doc.get(key) or []) if isinstance(i, dict)]
    items = [i for i in items if i.get("id") != entry.get("id")]
    items.insert(0, entry)
    doc[key] = items[:keep]
    doc["generated"] = datetime.now(timezone.utc).isoformat()
    doc["total_" + key] = len(doc[key])

    # The panels render their headline counts from these fields, not from the
    # list length, so a file written without them shows "0 Memes" above a full
    # grid. Recompute rather than leaving whatever the last writer left.
    if key == "memes":
        for level in ("low", "medium", "high"):
            doc[level + "_risk_count"] = sum(
                1 for i in doc[key] if str(i.get("risk", "")).lower() == level)
    if key == "ideas":
        doc["runnable_today_count"] = sum(
            1 for i in doc[key] if i.get("runnable_today"))
        doc["blocked_count"] = sum(
            1 for i in doc[key] if not i.get("runnable_today"))
    path.write_text(json.dumps(doc, indent=2, default=str), encoding="utf-8")


def publish_panels(summary: dict, rid: str) -> None:
    """Fan the cycle's outputs out to the panels that display them."""
    sel = summary.get("selection") or {}

    # Ideas Panel <- A02's selection and what it turned down
    if sel or summary.get("signal"):
        _panel_write("ideas.json", "ideas", {
            "id": rid + "-idea",
            "type": "GTM_CYCLE",
            "hook": (summary.get("posts", {}).get("x", {}) or {}).get("hook")
                    or str(summary.get("signal") or "")[:200],
            "rationale": sel.get("why") or str(summary.get("opportunity") or "")[:400],
            "pattern_ref": summary.get("machine"),
            # IdeasView renders both of these. They were absent, so every card
            # showed an empty provenance row under a real idea.
            "trend_link": summary.get("signal_source") or None,
            "pattern_source": (
                (summary.get("machine_name") or summary.get("machine") or "")
                + (" — observed in " + ", ".join(summary["machine_evidence"])
                   if summary.get("machine_evidence") else "")) or None,
            "source_type": summary.get("signal_source_type"),
            "audience_segment": summary.get("audience"),
            "objection_addressed": str(summary.get("problem") or "")[:300],
            "claims_gate": "PASS" if summary.get("review_passed") else "BLOCKED",
            "runnable_today": bool(summary.get("review_passed")),
            "blocked_by": None if summary.get("review_passed")
                          else str(summary.get("review_notes") or "")[:200],
            "effort": "AUTONOMOUS",
            "rejected": sel.get("rejected") or [],
            "run_id": rid,
            "visual_url": (pathlib.Path(str(summary["visual_path"])).name
                           if summary.get("visual_path") else None),
        })

    # Ideas Panel <- proposals from the signals this cycle did NOT use.
    #
    # Without this the panel is a log: one entry per finished run, so "24
    # ideas" meant "24 posts already made" and there was nothing to decide.
    # A01 gathers ~26 signals and A02 uses one; these are the other 25.
    try:
        from pipeline.gtm_os.idea_proposer import propose

        unused = [s for s in SIGNALS
                  if str(getattr(s, "headline", "")) != str(summary.get("signal") or "")]
        for prop in propose(unused, rid):
            _panel_write("ideas.json", "ideas", prop, keep=40)
    except Exception as exc:                        # noqa: BLE001 — boundary
        print("  [warn] idea proposals skipped: " + str(exc)[:160])

    # Crypto Memes <- A08's nano banana pro render
    if summary.get("meme_path"):
        _panel_write("memes.json", "memes", {
            "id": rid + "-meme",
            "format": "IMAGE",
            "reference": summary.get("pillar") or summary.get("signal"),
            "reference_url": None,
            "vanna_angle": str(summary.get("opportunity") or "")[:300],
            "copy": (summary.get("posts", {}).get("x", {}) or {}).get("hook", ""),
            "visual_spec": str(summary.get("visual_concept") or "")[:400],
            "claims_gate": "PASS" if summary.get("review_passed") else "BLOCKED",
            "risk": "LOW",
            "risk_reason": "Generated from a claim-gated strategy; no rendered text in frame.",
            "freshness": "LIVE",
            "model": R.MODELS["meme"],
            "run_id": rid,
            "visual_url": pathlib.Path(str(summary["meme_path"])).name,
        })


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Run one autonomous GTM cycle")
    ap.add_argument("--directive", default=None,
                    help="founder directive; omit for fully autonomous selection")
    ap.add_argument("--no-video", action="store_true",
                    help="skip Veo 3.1 (faster, cheaper)")
    a = ap.parse_args()
    out = run_cycle(a.directive, with_video=not a.no_video)
    sys.exit(0 if out.get("status") in ("completed", "review_blocked",
                                        "NO_ACTION", "KILL") else 1)
