"""Phase 5: Creative Director System (creative_director_system.py).

Produces structured visual blueprints (CompleteCreativeBlueprint) derived strictly
from strategic communication objectives and channel packages.
Enforces that raw posts NEVER reach media generators directly.
Compiles format-specific specifications for Vector Schematics, Static Images, and Veo 3.1 Videos.
"""

from __future__ import annotations

from pipeline.brand_brain import context as _C
from pipeline.brand_brain.context import facts_block as _prompt_block
from pipeline.gtm_os.agent_runtime import (
    brain_json as _brain_json, BrainError as _BrainError, record_stage as _record_stage,
)

import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone

from pipeline.gtm_orchestration.schemas import GTMStrategy, ContentPackage
from pipeline.gtm_creative.schemas import (
    VisualMetaphorSpec, CreativeFormatSpec, CompleteCreativeBlueprint
)

FORBIDDEN_CRYPTO_SLOP = [
    "random floating coins",
    "glowing spheres with concentric rings",
    "tron neon grids",
    "meaningless abstract nodes",
    "generic stock arrows",
    "random 3d objects with no architectural purpose",
    "decorative dashboards with fake numbers",
    "excessive purple pink neon glow",
    "fake product ui with unverified buttons",
    "unmotivated gradients",
    "text heavy infographic layouts"
]

def _brand_tokens() -> dict:
    """The tenant's palette, from its brand profile."""
    return _C.palette()


_AGENT = "A07_creative_director"


def _lead_hook(content_package) -> str:
    """The X hook, if the package has one. Used only to steer art direction."""
    try:
        posts = getattr(content_package, "channel_posts", {}) or {}
        for key in ("x", "X", "linkedin"):
            if key in posts:
                return str(getattr(posts[key], "hook", "") or "")[:300]
    except Exception:
        pass
    return ""


class CreativeDirectorSystem:
    """The master visual director deriving physical/optical metaphors from strategy."""

    def compile_master_blueprint(
        self,
        strategy: GTMStrategy,
        content_package: ContentPackage
    ) -> CompleteCreativeBlueprint:
        """Derive the complete multi-format creative blueprint."""
        if strategy.action_status in ["NO_ACTION", "KILL"]:
            raise ValueError(f"Creative director cannot run on a {strategy.action_status} strategy.")

        cid = f"CCB-{strategy.strategy_id[:16]}-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M')}"
        pillar_lower = strategy.narrative_pillar.lower()

        # Ground the art direction in what Vanna actually is.
        #
        # The previous version told the model the metaphor must be "a physical,
        # filmable arrangement of objects and light... not a diagram", and it
        # obeyed: it produced beautiful optical glassware that could have
        # advertised a wristwatch. Nothing in frame said Soroban, Blend, a
        # SmartAccount or a health factor, so the visual and the video carried
        # none of the argument the post was making.
        #
        # The house style stays. What changes is that the subject matter is now
        # required to BE the mechanism, named, using the anchors below.
        knowledge = _prompt_block(
            " ".join([str(strategy.narrative_pillar), str(strategy.problem)])[:400],
            excerpts=6)
        anchors = "\n".join("  - " + k + ": " + v for k, v in _C.anchors().items())
        name = _C.company_name()
        pal = _C.palette()
        deployment = str(_C.profile().get("company", {}).get("deployment", ""))

        art_system = (
            "You are " + name + "'s creative director. " + _C.company_line() + " "
            "You art-direct one still image, one meme and one motion piece per "
            "campaign.\n\n"

            "THE SUBJECT IS THE MECHANISM.\n"
            "Every asset must depict " + name + "'s actual architecture using these "
            "concrete anchors. An abstract composition of glass and light that "
            "does not show the mechanism is a failed brief, however beautiful:\n"
            + anchors + "\n\n"

            "Build the image from real, identifiable things taken from those "
            "anchors: the units, ratios, flows and thresholds they name. A viewer "
            "who knows the domain should recognise what is being described. A "
            "viewer who does not should still see structure, not decoration.\n\n"

            "HOUSE STYLE: " + _C.house_style() + ". Palette: "
            + ", ".join(k + " " + v for k, v in pal.items()) + ".\n\n"

            "NEVER DEPICT: " + _C.prohibited_visual() + ".\n"
            "Never render text, letterforms, numerals, logos or UI chrome "
            "inside a generated image — the models cannot spell, and a "
            "misspelt figure is a false claim. Express quantity through "
            "physical proportion instead.\n"
            "Never contradict the deployment: " + deployment + "\n\n"

            "Return strict JSON."
        )

        art_prompt = (
            knowledge + "\n\n"
            "----\n\n"
            "THIS CAMPAIGN\n"
            "  pillar:      " + str(strategy.narrative_pillar) + "\n"
            "  problem:     " + str(strategy.problem) + "\n"
            "  opportunity: " + str(strategy.strategic_opportunity) + "\n"
            "  audience:    " + str(strategy.audience_segment) + "\n"
            "  post hook:   " + str(_lead_hook(content_package)) + "\n\n"
            "Art-direct it. Return JSON exactly:\n"
            '{"thesis": str, "concept": str, "metaphor": str, '
            '"composition": str, "lighting": str, "materials": str, '
            '"mechanism_shown": str, "anchors_used": [str], '
            '"veo_prompt": str, "vector_spec": str, "meme_prompt": str}\n\n'
            "mechanism_shown: name the " + _C.company_name() + " mechanism the image depicts, in "
            "one sentence. If you cannot name one, the concept is decoration "
            "and you must redo it.\n"
            "anchors_used: which of the product anchors appear in frame. At "
            "least two.\n"
            "veo_prompt: one paragraph for an 8-second cinematic shot that "
            "SHOWS this mechanism happening over time — a threshold approached "
            "and defended, a position routed out and returning, one unit "
            "sealing while its neighbours stay untouched. Describe camera move "
            "and light behaviour. No text in frame. Not an ambient mood piece.\n"
            "vector_spec: a 1200x675 schematic for the deterministic renderer, "
            "which MAY carry labels since it is drawn rather than generated.\n"
            "meme_prompt: one square image, dry and knowing — the joke an "
            "engineer in this domain would make about this problem. Still grounded in "
            "the mechanism, still no text in frame."
        )

        try:
            art = _brain_json(art_prompt, agent=_AGENT, role="reasoning",
                              system=art_system, temperature=0.75,
                              max_output_tokens=6144)
            thesis = str(art.get("thesis") or "").strip()
            concept = str(art.get("concept") or "").strip()
            metaphor = str(art.get("metaphor") or "").strip()
            composition = str(art.get("composition") or "").strip()
            lighting = str(art.get("lighting") or "").strip()
            materials = str(art.get("materials") or "").strip()
            veo_prompt = str(art.get("veo_prompt") or "").strip()
            vector_spec = str(art.get("vector_spec") or "").strip()
            meme_prompt = str(art.get("meme_prompt") or "").strip()
            mechanism_shown = str(art.get("mechanism_shown") or "").strip()
            anchors_used = [str(a) for a in (art.get("anchors_used") or [])][:6]
            if not mechanism_shown or len(anchors_used) < 2:
                # The brief asks for these precisely so decoration cannot pass.
                raise _BrainError(
                    "art direction named no mechanism or fewer than two product "
                    "anchors; that is a decorative concept, not a brief")
            if not (concept and veo_prompt):
                raise _BrainError("art direction missing concept or veo_prompt")
            _record_stage(_AGENT, "ok",
                          "art-directed: " + mechanism_shown[:120]
                          + " | anchors: " + ", ".join(anchors_used))
        except _BrainError as exc:
            # No canned fallback. A creative director that could not reach its
            # model has not directed anything, and shipping the old hardcoded
            # prism shot under a new strategy is how two visuals came to stand
            # in for every campaign this system ever ran.
            _record_stage(_AGENT, "failed", "art direction unavailable: " + str(exc)[:300])
            raise

        metaphor_spec = VisualMetaphorSpec(
            thesis=thesis,
            concept=concept,
            metaphor=metaphor,
            composition=composition,
            lighting=lighting,
            materials=materials,
            negative_elements=FORBIDDEN_CRYPTO_SLOP
        )

        # Compile format-specific payloads
        formats: Dict[str, CreativeFormatSpec] = {
            "STATIC_VECTOR": CreativeFormatSpec(
                format_type="STATIC_VECTOR",
                dimensions="1200x675",
                compiled_prompt=vector_spec
            ),
            "STATIC_IMAGE": CreativeFormatSpec(
                format_type="STATIC_IMAGE",
                dimensions="1200x675",
                compiled_prompt=(
                    f"Developer-grade clean visual metaphor for {name}. {concept} "
                    f"Palette: {', '.join(k + ' ' + v for k, v in pal.items())}. "
                    f"High negative space, zero text, zero generic floating spheres, zero neon grids."
                )
            ),
            "MEME_IMAGE": CreativeFormatSpec(
                format_type="MEME_IMAGE",
                dimensions="1024x1024",
                compiled_prompt=meme_prompt or concept
            ),
            "VEO_VIDEO_31": CreativeFormatSpec(
                format_type="VEO_VIDEO_31",
                dimensions="1280x720",
                framerate=24,
                duration_seconds=8,
                conditioning_asset=str(_C.logo_path().name if _C.logo_path() else ""),
                compiled_prompt=veo_prompt
            )
        }

        return CompleteCreativeBlueprint(
            creative_id=cid,
            strategy_id=strategy.strategy_id,
            communication_objective=strategy.objective,
            visual_metaphor=metaphor_spec,
            brand_tokens=_brand_tokens(),
            typography_hierarchy={
                "headline": _C.fonts().get("display", "") + " Bold 48px",
                "telemetry": _C.fonts().get("mono", "") + " SemiBold 12px"
            },
            format_specs=formats,
            negative_constraints=FORBIDDEN_CRYPTO_SLOP,
            created_at=datetime.now(timezone.utc).isoformat()
        )
