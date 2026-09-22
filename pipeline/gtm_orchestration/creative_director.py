"""Phase 1D: Creative Director Agent.

Derives visual metaphors strictly from the communication objective and strategy.
Enforces Vanna brand system (#07020D obsidian void, #471485 violet, #5E0D46 fuchsia).
Prohibits generic AI slop (no floating spheres, no Tron neon grids, no random crypto coins).
Emits the authoritative CreativeBrief contract.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone

from pipeline.gtm_orchestration.schemas import GTMStrategy, ContentPackage, CreativeBrief


VANNA_BRAND_SYSTEM = {
    "palette": {
        "obsidian_void": "#07020D",
        "royal_violet_bloom": "#471485",
        "fuchsia_magenta_bloom": "#5E0D46",
        "lavender_accent": "#A387FF",
        "coral_risk": "#FC5457",
        "cyan_telemetry": "#22D3C4",
        "neutral_white": "#FFFFFF"
    },
    "typography": {
        "primary_sans": "Plus Jakarta Sans",
        "monospace": "JetBrains Mono"
    },
    "surface": "35mm analog film grain, quiet institutional authority, generous negative space"
}

FORBIDDEN_VISUAL_SLOP = [
    "generic glowing spheres with concentric rings",
    "random neon grid floors or Tron aesthetic",
    "floating 3D cubes with no architectural purpose",
    "flying golden crypto coins or cartoon dollar signs",
    "generic stock crypto dashboards or candlestick charts",
    "holographic sci-fi HUDs with meaningless decorative numbers",
    "unmotivated particle storms or lens flare spam",
    "excessive purple/pink neon glow everywhere"
]


class CreativeDirector:
    """Creative Director agent: turns abstract financial mechanics into physical/optical metaphors."""

    def __init__(self, brand_system: Optional[Dict[str, Any]] = None):
        self.brand_system = brand_system or VANNA_BRAND_SYSTEM

    def direct_creative_concept(
        self,
        strategy: GTMStrategy,
        content_package: ContentPackage,
        format_target: str = "video_veo31"
    ) -> CreativeBrief:
        """Synthesize a complete creative brief and generator-specific payload."""
        if strategy.action_status in ["NO_ACTION", "KILL"]:
            raise ValueError(f"Creative Director cannot create a visual brief for a {strategy.action_status} strategy.")

        # Derive visual metaphor from the core narrative pillar:
        if "sub-second" in strategy.narrative_pillar.lower() or "telemetry" in strategy.narrative_pillar.lower():
            thesis = "Visualizing sub-second risk deflection and liquidation avoidance through precision optical caustics."
            concept = "An incoming telemetry beam entering an obsidian refractive prism and safely arcing into a stable horizontal orbit."
            metaphor = "Optical deflection: incoming market volatility redirected smoothly away from the hazard boundary."
            environment = "Expansive dark obsidian void with muted ambient violet and fuchsia gradient blooms in distant corners."
            materials = "Matte black stone, optical leaded crystal glass, and subtle specular reflections on a satin floor."
            camera = "Slow cinematic dolly pushing forward into the central prism then holding steady on the deflected arc."
            lighting = "Subtle, restrained studio lighting. No harsh blinding spotlights, no chaotic smoke."
            motion = "Laminar beam acceleration smoothly transitioning into a stable, peaceful horizontal orbit."
        else:
            thesis = "Visualizing state isolation and zero-contagion through modular architectural containment chambers."
            concept = "Three monolithic glass-and-obsidian vault chambers where one safely contains an internal fracture while peers stay pristine."
            metaphor = "Compartmentalized blast-radius: localized risk quarantined at the contract instance level."
            environment = "Minimalist virtual stage with 35mm film grain on deep #07020D void."
            materials = "Precision-milled dark obsidian, frosted barrier glass, and calm internal luminescence."
            camera = "Slow, elegant camera crane up / tilt down settling on the secure modular architecture."
            lighting = "Clean studio rim lighting defining chamber bevels with soft lavender and cyan ambient washes."
            motion = "Permanent architectural stillness with gentle 0.5Hz breathing luminescence inside vaults."

        # Generator Instructions Tailored to Target
        generator_instructions = {
            "target_model": "veo-3.1-generate-001" if format_target == "video_veo31" else "gemini-3.1-flash-image",
            "prompt": (
                f"Minimalist luxury product motion design video. The official Vanna geometric logo glyph and VANNA wordmark "
                f"are centered in an expansive, tranquil obsidian void (#07020D). Extremely subtle, soft, restrained studio lighting. "
                f"The folded geometric ribbon glyph has a quiet, gentle breathing internal glow of soft coral and lavender, "
                f"with delicate, matte chamfered edge highlights. The clean white VANNA typography remains razor-sharp and steady. "
                f"The camera executes a very slow, smooth, elegant cinematic pull-back across a clean, dark satin floor with faint, "
                f"muted reflections. Muted, soft ambient violet (#471485) and fuchsia (#5E0D46) tones stay gracefully in the far background. "
                f"Tactile 35mm film grain, supreme visual calm, quiet institutional confidence. Photorealistic architectural polish."
            ),
            "aspect_ratio": "16:9",
            "duration_seconds": 8 if format_target == "video_veo31" else 0,
            "conditioning_image": "vanna_logo_hero_canvas.png"
        }

        return CreativeBrief(
            creative_id=f"CR-{strategy.strategy_id}",
            strategy_id=strategy.strategy_id,
            creative_thesis=thesis,
            visual_concept=concept,
            visual_metaphor=metaphor,
            composition="Cinematic 16:9 widescreen with generous negative space (>75%) framing the central hero subject.",
            environment=environment,
            materials=materials,
            camera=camera,
            lighting=lighting,
            motion=motion,
            typography={
                "headline_font": "Plus Jakarta Sans",
                "telemetry_font": "JetBrains Mono"
            },
            brand_system=self.brand_system,
            negative_constraints=FORBIDDEN_VISUAL_SLOP,
            generation_format=format_target,
            generator_instructions=generator_instructions
        )
