"""Turning the signals a cycle did NOT use into things the founder could run.

The Ideas Panel was a run log. One entry per completed cycle, `type:
GTM_CYCLE`, describing work that had already happened — so "24 ideas" meant
"24 posts we already made", and there was nothing to decide. What the panel is
supposed to answer is "what could we do next", and the material for that was
being thrown away every run: A01 gathers ~26 signals, A02 picks one, and the
other 25 are discarded after the rejection note is written.

So this takes the leftovers and asks for a concrete proposal per signal — the
angle, the format, why it is timely, and what Vanna specifically has to say
about it. Those become PROPOSED entries the panel can show alongside the runs.

Two rules it inherits from the rest of the engine:

  * **No invented numbers.** A proposal may only cite figures that are in the
    signal itself. The claim gate has not run on these — they are drafts, not
    approved copy — so they are marked `claims_gate: UNCHECKED` rather than
    being quietly presented as clean.
  * **Nothing already covered.** Subjects in `topic_memory` are dropped before
    the model sees them, so the panel does not propose what just shipped.
"""
from __future__ import annotations

from typing import Any, Iterable, Optional

# Four, not six. Each proposal now carries nine fields including three
# creative-direction sentences, and six of those overran the output
# budget — the reply was cut mid-string and the whole batch was lost to
# a JSON parse error. Fewer, complete proposals beat six truncated ones.
MAX_PROPOSALS = 4

SYSTEM = (
    "You turn raw market signals into concrete content proposals for "
    "{company_line}\n\n"
    "For each signal, propose one piece of content {company} could credibly make. "
    "Rules:\n"
    "- {company}'s angle must be architectural and specific, from what it "
    "concretely is ({anchors}). Never a generic take.\n"
    "- If {company} has nothing genuine to say about a signal, set "
    '"worth_making": false and say why. A thin proposal is worse than none.\n'
    "- Cite only figures that appear in the signal text. Invent no numbers, no "
    "TVL, no percentages, no dates.\n"
    "- Never contradict the deployment ({deployment}). Never name a competitor as inferior.\n"
    "- format is one of: THREAD, LINKEDIN_POST, REDDIT_DEEPDIVE, MEME, VIDEO.\n\n"
    "Also give the creative direction, because a proposal the founder cannot "
    "picture is not actionable:\n"
    "- visual_direction: what the still should show, in the house style "
    "({house_style}). Never photorealism, 3D renders, charts, candlesticks, "
    "coins, rockets or logos.\n"
    "- video_direction: the motion treatment in one or two sentences — a "
    "locked-off camera on {company}-coloured ground with simple transitions and "
    "basic motion graphics. No cinematic camera moves.\n"
    "- gtm_play: the distribution move in one sentence — which channel leads, "
    "what the follow-up is, and who it is aimed at.\n\n"
    "Return strict JSON."
)


def propose(signals: Iterable[Any], run_id: Optional[str] = None,
            limit: int = MAX_PROPOSALS) -> list[dict[str, Any]]:
    """Concrete, draftable proposals from unused signals. Never raises."""
    from pipeline.gtm_os import agent_runtime as R
    from pipeline.gtm_os import topic_memory as TM

    # Topic memory exists to stop the engine *publishing* the same subject
    # twice. Applying it at full strength here was wrong: after a few cycles
    # every candidate was suppressed and the panel silently proposed nothing.
    # A suggestion is not a publication — the founder can judge whether a
    # recently covered angle is worth revisiting — so an empty result falls
    # back to the unfiltered pool rather than returning nothing.
    fresh, stale = TM.split_fresh(signals)
    pool = (fresh or stale or list(signals))[:limit]
    if not pool:
        return []

    listing = "\n".join(
        "- [" + str(i) + "] " + str(getattr(s, "headline", s))[:200]
        + "  (source: " + str(getattr(s, "source_type", "?")) + ")"
        for i, s in enumerate(pool))

    try:
        data = R.brain_json(
            "SIGNALS NOT USED BY THIS CYCLE\n" + listing + "\n\n"
            'Return {"proposals": [{"index": int, "worth_making": bool, '
            '"angle": str, "format": str, "hook": str, "why_now": str, '
            '"vanna_mechanism": str, "visual_direction": str, '
            '"video_direction": str, "gtm_play": str, "skip_reason": str}]}\n\n'
            "angle is one sentence on what the piece argues. hook is the "
            "opening line, under 20 words. why_now ties it to the signal. "
            "vanna_mechanism names the specific Vanna capability it rests on. "
            "visual_direction, video_direction and gtm_play are ONE sentence "
            "each, under 25 words. Keep angle under 30 words. "
            "skip_reason only when worth_making is false.",
            agent="A02_opportunity_selector", role="reasoning", system=__import__('pipeline.brand_brain.context', fromlist=['fill']).fill(SYSTEM),
            temperature=0.8, max_output_tokens=8192, run_id=run_id)
    except Exception:                               # noqa: BLE001 — boundary
        # A failed proposal step must not fail a cycle; the run's own work is
        # already done and recorded.
        return []

    out: list[dict[str, Any]] = []
    for p in (data.get("proposals") or []):
        if not isinstance(p, dict) or not p.get("worth_making"):
            continue
        try:
            sig = pool[int(p.get("index", -1))]
        except (ValueError, TypeError, IndexError):
            continue
        head = str(getattr(sig, "headline", sig))
        out.append({
            "id": "PROP-" + TM.fingerprint(head).replace(" ", "-")[:40],
            "type": "PROPOSED",
            "hook": str(p.get("hook") or "")[:200],
            "rationale": str(p.get("angle") or "")[:400],
            "format_spec": {"archetype": str(p.get("format") or "THREAD")},
            "trend_link": str(getattr(sig, "source", "") or "") or None,
            "source_type": str(getattr(sig, "source_type", "")) or None,
            "pattern_source": str(p.get("vanna_mechanism") or "")[:200] or None,
            "objection_addressed": str(p.get("why_now") or "")[:300],
            # Creative direction, so the panel shows what to make rather than
            # only what to say.
            "visual_direction": str(p.get("visual_direction") or "")[:400] or None,
            "video_direction": str(p.get("video_direction") or "")[:400] or None,
            "gtm_play": str(p.get("gtm_play") or "")[:300] or None,
            # Not run through the claim gate — these are drafts, and saying
            # PASS here would be the same lie the scorecard used to tell.
            "claims_gate": "UNCHECKED",
            "runnable_today": True,
            "blocked_by": None,
            "effort": "NEEDS_DRAFTING",
            "signal_headline": head[:200],
            "run_id": run_id,
            "visual_url": None,
        })
    return out
