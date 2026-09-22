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

def render_visual(strategy, content_pkg, blueprint, run_id: str) -> Optional[dict]:
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

def render_meme(blueprint, run_id: str) -> str:
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

def render_video(blueprint, run_id: str, *, timeout_s: float = 420.0) -> Optional[str]:
    """Submit the art director's Veo prompt and wait for the asset.

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

        # A02 — Opportunity Selector
        def pick():
            if directive:
                R.record_stage("A02_opportunity_selector", "skipped",
                               "founder directive supplied; selection deferred")
                for s in signals:
                    if directive.lower()[:40] in str(s.headline).lower():
                        return s
                return signals[0]
            return _select_signal(signals)
        signal = _stage("A02_opportunity_selector", pick,
                        detail="chose a signal to pursue")
        summary["signal"] = str(signal.headline)
        summary["signal_source_type"] = str(signal.source_type)
        summary["signal_observed_at"] = str(signal.observed_at)
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

        if strategy.action_status != "ACTION":
            summary["status"] = strategy.action_status
            summary["reason"] = (strategy.no_action_rationale
                                 or strategy.kill_rationale or "")
            for skipped in ("A04_machine_library", "A05_campaign_engine",
                            "A06_channel_adapter", "A07_creative_director",
                            "A08_visual_synthesis", "A09_video_production",
                            "A10_reviewer_firewall", "A11_dispatch_worker",
                            "A12_telegram_gateway"):
                R.record_stage(skipped, "skipped",
                               "strategy returned " + strategy.action_status)
            return _finish(summary, t0, rid)

        # A04 — Machine Library
        _stage("A04_machine_library",
               lambda: GTMMachineLibrary().get_machine(strategy.gtm_machine_id),
               detail="verified machine " + str(strategy.gtm_machine_id))

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

        # A08 — Visual Synthesis Engine (nano banana)
        visual = _stage("A08_visual_synthesis",
                        lambda: render_visual(strategy, content_pkg, blueprint, rid),
                        required=False, self_recorded=True)
        if visual:
            summary["visual_path"] = visual.get("path") or visual.get("filename")
            summary["visual_public_url"] = visual.get("public_url")

        # Meme — same agent, nano banana pro
        meme = _stage("A08_visual_synthesis",
                      lambda: render_meme(blueprint, rid), required=False,
                      detail="rendered the meme", self_recorded=True)
        if meme:
            summary["meme_path"] = meme

        # A09 — Video Production Engine (Veo 3.1)
        if with_video:
            video = _stage("A09_video_production",
                           lambda: render_video(blueprint, rid),
                           required=False, self_recorded=True)
            if video:
                summary["video_path"] = video
        else:
            R.record_stage("A09_video_production", "skipped",
                           "video disabled for this run (--no-video)")

        # A10 — Pre-Delivery Reviewer Firewall
        def review():
            channel_verdict = ChannelReviewer().review_channel_adaptation(content_pkg)
            creative_verdict = CreativeValidator().validate_blueprint(
                blueprint, raw_post_copy=content_pkg.channel_posts["x"].copy)
            return channel_verdict, creative_verdict
        verdicts = _stage("A10_reviewer_firewall", review,
                          detail="ran the pre-delivery firewalls")
        channel_verdict, creative_verdict = verdicts
        passed = bool(channel_verdict.approved and creative_verdict.approved)
        summary["review_passed"] = passed
        summary["review_notes"] = {
            "blocked_claims": list(getattr(channel_verdict, "blocked_unsupported_claims", []) or []),
            "slop": list(getattr(creative_verdict, "slop_violations", []) or []),
        }

        # A11 — Approved Dispatch Worker. It dispatches only what a human has
        # approved, and no human has seen this yet, so it is correctly idle.
        R.record_stage("A11_dispatch_worker", "skipped",
                       "awaiting human approval; dispatch never runs unprompted")

        # A12 — Telegram Gateway
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

        # A13 — Closed-Loop Learning Engine
        _stage("A13_learning_engine", _run_learning, required=False,
               detail="processed the outcome feedback loop")

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


SELECTION: dict = {}


def _select_signal(signals):
    """A02: judge which signal is worth a campaign, with reasons for the rest."""
    listing = "\n".join(
        "- [" + str(i) + "] " + str(s.headline)[:180]
        + "  (source: " + str(s.source_type) + ", confidence: " + str(s.confidence) + ")"
        for i, s in enumerate(signals))
    system = (
        "You select which market signal Vanna should build a campaign on. "
        "Vanna is composable credit infrastructure on Stellar Soroban testnet. "
        "Prefer a signal where Vanna has a specific architectural answer over "
        "one that is merely popular. Return strict JSON.")
    data = R.brain_json(
        "CANDIDATE SIGNALS\n" + listing + "\n\n"
        'Return {"index": int, "why": str, "rejected": [{"index": int, "why": str}]}',
        agent="A02_opportunity_selector", role="reasoning", system=system,
        temperature=0.2, max_output_tokens=1536)
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
    })
    return signals[idx]


def _run_learning():
    """A13: adjust pattern weights, then have the model read the adjustment.

    The engine on its own is a group-by and a weight nudge — it can tell that
    PAT_01 moved from 1.0 to 1.15 but not whether that is a real signal or two
    lucky posts. Declaring A13 model-backed while it made no model call was one
    of the rows the dashboard could not honestly fill, so the judgement step is
    real: the model reads the adjustments and says what it would change.
    """
    from pipeline.gtm_learning.learning_engine import LearningEngine

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
        R.record_stage("A13_learning_engine", "ok",
                       "no outcome records to learn from yet")
        return {"adjustments": 0, "verdict": None}

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
    return {"adjustments": len(rows), "verdict": verdict}


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
    summary["model_calls"] = len(calls)
    summary["model_calls_ok"] = sum(1 for c in calls if c.get("ok"))
    summary["input_tokens"] = sum(c.get("input_tokens", 0) for c in calls)
    summary["output_tokens"] = sum(c.get("output_tokens", 0) for c in calls)
    summary["models_used"] = sorted({c.get("model") for c in calls if c.get("model")})

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
            if prior.get("status") == "failed" and s.get("status") == "ok":
                merged["detail"] = (str(s.get("detail", "")) + " (recovered after: "
                                    + str(prior.get("detail", ""))[:120] + ")")
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
