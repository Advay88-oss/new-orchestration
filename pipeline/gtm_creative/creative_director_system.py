"""Phase 5: Creative Director System (creative_director_system.py).

Produces structured visual blueprints (CompleteCreativeBlueprint) derived strictly
from strategic communication objectives and channel packages.
Enforces that raw posts NEVER reach media generators directly.
Compiles format-specific specifications for Vector Schematics, Static Images, and Veo 3.1 Videos.
"""

from __future__ import annotations

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

VANNA_CANONICAL_BRAND_TOKENS = {
    "obsidian_canvas": "#07020D",
    "electric_violet_bloom": "#471485",
    "fuchsia_magenta_bloom": "#5E0D46",
    "vanna_lavender": "#A387FF",
    "coral_risk_accent": "#FC5457",
    "cyan_telemetry": "#22D3C4",
    "film_grain": "35mm analog grain, zero digital banding",
    "negative_space_ratio": "Minimum 75% uninterrupted obsidian void"
}


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

        # Art-direct the visual for THIS strategy — gemini-3.8-flash.
        #
        # This was an if/else on whether the pillar contained "sub-second", so
        # the entire system had exactly two visuals and two Veo prompts, both
        # typed in full below. Every campaign on a telemetry pillar got the
        # identical prism shot; everything else got the identical logo pull-back.
        #
        # FORBIDDEN_CRYPTO_SLOP stays a deterministic constraint appended to the
        # prompt and re-applied to negative_elements: the model chooses the
        # image, it does not get to choose the brand rules.
        art_system = (
            "You are Vanna's creative director. Vanna is composable credit "
            "infrastructure on Stellar Soroban testnet. You art-direct one "
            "still image and one motion piece per campaign.\n\n"
            "House style, non-negotiable: expansive tranquil obsidian void "
            "(#07020D), 75%+ negative space, disciplined studio lighting, matte "
            "and optical materials, 35mm film grain, photorealistic "
            "architectural polish, quiet institutional confidence.\n\n"
            "Muted accents only: royal violet #471485, fuchsia #5E0D46.\n\n"
            "BANNED, always: " + ", ".join(FORBIDDEN_CRYPTO_SLOP) + ".\n"
            "Also banned: any rendered text, letterforms, numerals, logos or "
            "UI chrome inside the generated image.\n\n"
            "The metaphor must be a physical, filmable arrangement of objects "
            "and light that embodies the strategic claim. Not an illustration "
            "of a concept, not a diagram, not a screenshot. Return strict JSON."
        )
        art_prompt = (
            "STRATEGIC PILLAR\n  " + str(strategy.narrative_pillar) + "\n\n"
            "PROBLEM\n  " + str(strategy.problem) + "\n\n"
            "OPPORTUNITY\n  " + str(strategy.strategic_opportunity) + "\n\n"
            "AUDIENCE\n  " + str(strategy.audience_segment) + "\n\n"
            "POST HOOK\n  " + str(_lead_hook(content_package)) + "\n\n"
            "Return JSON exactly:\n"
            '{"thesis": str, "concept": str, "metaphor": str, '
            '"composition": str, "lighting": str, "materials": str, '
            '"veo_prompt": str, "vector_spec": str}\n\n'
            "veo_prompt: one paragraph, cinematic, describing camera move and "
            "light behaviour over 5-8 seconds. No text in frame.\n"
            "vector_spec: a 1200x675 schematic description for the deterministic "
            "renderer, which MAY carry labels since it is drawn, not generated.\n"
            "meme_prompt: a single square image for a developer-audience meme "
            "about this same argument. Dry and knowing rather than loud — the "
            "joke a Soroban engineer would make about the problem, not a "
            "reaction-image template. Still no rendered text in frame."
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
            if not (concept and veo_prompt):
                raise _BrainError("art direction missing concept or veo_prompt")
            _record_stage(_AGENT, "ok", "art-directed: " + concept[:160])
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
                    f"Developer-grade clean DeFi visual metaphor for Vanna Protocol. {concept} "
                    f"Background: Deep obsidian base (#07020D) with soft ambient electric violet glow (#471485) and fuchsia (#5E0D46). "
                    f"35mm film grain, high negative space, zero text, zero generic floating spheres, zero neon grids."
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
                conditioning_asset="vanna_logo_hero_canvas.png",
                compiled_prompt=veo_prompt
            )
        }

        return CompleteCreativeBlueprint(
            creative_id=cid,
            strategy_id=strategy.strategy_id,
            communication_objective=strategy.objective,
            visual_metaphor=metaphor_spec,
            brand_tokens=VANNA_CANONICAL_BRAND_TOKENS,
            typography_hierarchy={
                "headline": "Plus Jakarta Sans Bold 48px",
                "telemetry": "JetBrains Mono SemiBold 12px"
            },
            format_specs=formats,
            negative_constraints=FORBIDDEN_CRYPTO_SLOP,
            created_at=datetime.now(timezone.utc).isoformat()
        )
