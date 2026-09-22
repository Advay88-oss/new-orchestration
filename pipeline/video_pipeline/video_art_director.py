#!/usr/bin/env python3
"""Agent 2: VIDEO ART DIRECTOR (video_art_director.py)

Role: Decides EXACTLY how every scene should be visually constructed.
Input:
  - VIDEO_SCRIPT.json
  - Vanna brand system
  - Available visual capabilities
  - Previous video feedback
Output:
  - Scene-by-scene visual blueprints with tailored Veo prompts, camera choreography, and anti-slop constraints.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# Strict Vanna Brand Architecture Constants
VANNA_BRAND_SYSTEM = {
    "palette": {
        "obsidian_base": "#07020D",
        "royal_violet_bloom": "#471485",
        "fuchsia_magenta_bloom": "#5E0D46",
        "lavender_accent": "#A387FF",
        "coral_accent": "#FC5457",
        "cyan_telemetry": "#22D3C4",
        "crisp_white": "#FFFFFF",
    },
    "typography": {
        "primary_sans": "Plus Jakarta Sans",
        "monospace_telemetry": "JetBrains Mono",
    },
    "texture": "Subtle 35mm analog film grain, high negative space, zero digital banding",
}

FORBIDDEN_VISUAL_PATTERNS = [
    "generic glowing spheres with concentric rings",
    "random neon grid floors or Tron aesthetic",
    "floating 3D cubes with no architectural purpose",
    "flying golden crypto coins or cartoon dollar signs",
    "generic stock crypto dashboards or candlestick charts",
    "holographic sci-fi HUDs with meaningless decorative numbers",
    "unmotivated particle storms or lens flare spam",
]


class VideoArtDirector:
    """Art Director agent: Translates script messages into physical/architectural visual metaphors."""

    def __init__(self, brand_system: Optional[Dict[str, Any]] = None):
        self.brand_system = brand_system or VANNA_BRAND_SYSTEM

    def direct_visuals(self, script: Dict[str, Any]) -> Dict[str, Any]:
        """Produce full visual specifications and Veo prompts for each scene."""
        scenes = script.get("scenes", [])
        art_directed_scenes: List[Dict[str, Any]] = []

        for s in scenes:
            scene_id = s.get("scene_id", 1)
            name = s.get("name", "")

            if scene_id == 1:
                # Scene 1: The Mempool Bottleneck
                visual_spec = {
                    "scene_id": 1,
                    "duration": s.get("duration_seconds", 4.0),
                    "narrative_purpose": s.get("narrative_purpose", ""),
                    "visual_concept": "Turbulent, congested congestion field in deep obsidian space representing mempool queue drag.",
                    "composition": "Cinematic wide 16:9, asymmetric camera framing looking down a narrowing geometric corridor.",
                    "camera": "Slow cinematic dolly pushing forward into a congested narrow choke-point.",
                    "motion": "Heavy, sluggish particle vectors crawling slowly through viscous dark fluid, signaling delay and friction.",
                    "lighting": "Low-key dramatic studio lighting; ominous crimson (#FC5457) warning reflections along obsidian walls.",
                    "color": "Obsidian base #07020D with deep violet shadows (#471485) and warning coral-red accents (#FC5457).",
                    "typography": "JetBrains Mono uppercase 12px supertitle with Plus Jakarta Sans 48px bold headline.",
                    "assets": ["corridor_mesh", "congested_vector_particles", "status_bracket"],
                    "negative_constraints": FORBIDDEN_VISUAL_PATTERNS + ["happy lighting", "generic crypto coins", "stock arrows"],
                    "veo_prompt": (
                        "Cinematic high-end architectural visualization of financial friction and network congestion. "
                        "A sleek, minimalist matte obsidian corridor (#07020D) in deep space. Glowing sluggish energy filaments "
                        "crawl through a narrowing geometric choke-point with visible drag. Subtle ominous crimson-coral ambient rim light (#FC5457). "
                        "35mm film grain, cinematic depth of field, slow forward dolly movement, photorealistic tactile glass and dark stone materials, "
                        "zero text, zero logos, zero floating spheres."
                    ),
                }

            elif scene_id == 2:
                # Scene 2: Sub-Second Ingestion Stream
                visual_spec = {
                    "scene_id": 2,
                    "duration": s.get("duration_seconds", 4.0),
                    "narrative_purpose": s.get("narrative_purpose", ""),
                    "visual_concept": "High-velocity laminar beam of coherent telemetry light breaking through the congestion void.",
                    "composition": "Horizontal linear tracking shot following a fast, pristine beam from left to right across vast negative space.",
                    "camera": "High-speed tracking shot matching the velocity of the telemetry beam, then slowing to enter a precision lens.",
                    "motion": "Instantaneous laminar velocity transition (~320ms acceleration), perfectly smooth and coherent.",
                    "lighting": "Prismatic refraction along the edges of the beam; electric cyan (#22D3C4) and soft lavender (#A387FF) luminescence.",
                    "color": "Obsidian #07020D base, royal violet #471485 bloom bottom-left, electric cyan #22D3C4 core beam.",
                    "typography": "High-contrast monospace telemetry readouts at 80% opacity in top-left corner.",
                    "assets": ["coherent_laser_beam", "telemetry_pulse_node", "refraction_plane"],
                    "negative_constraints": FORBIDDEN_VISUAL_PATTERNS + ["pixelated lines", "cheap rainbow gradients"],
                    "veo_prompt": (
                        "Cinematic high-speed tracking shot of an ultra-thin, coherent laser beam of electric cyan (#22D3C4) "
                        "and soft lavender (#A387FF) slicing cleanly through an expansive dark obsidian void (#07020D). "
                        "Smooth laminar optical motion without turbulence. Soft royal violet bloom (#471485) emerging from lower-left. "
                        "35mm analog film texture, high optical realism, anamorphic lens flare, calm mathematical precision, "
                        "zero text, zero floating tokens."
                    ),
                }

            elif scene_id == 3:
                # Scene 3: Autonomous Defense Clearance
                visual_spec = {
                    "scene_id": 3,
                    "duration": s.get("duration_seconds", 4.0),
                    "narrative_purpose": s.get("narrative_purpose", ""),
                    "visual_concept": "Precision optical deflection: the beam strikes a crystalline threshold prism and arcs gracefully into a secure orbit.",
                    "composition": "Centered monolithic prism with asymmetric parabolic vector trajectory arcing upward away from a faint lower boundary.",
                    "camera": "Subtle orbital camera rotation around the deflection lens as the beam cleanly redirects.",
                    "motion": "Impactless deflection: the beam enters the prism and bends instantaneously into a tranquil horizontal path.",
                    "lighting": "Specular glint at the moment of deflection; deep fuchsia-magenta bloom (#5E0D46) in top-right.",
                    "color": "Electric cyan (#22D3C4) trajectory curving safely above a muted crimson-coral (#FC5457) avoided hazard line.",
                    "typography": "Crisp status tags displaying 1.25x trigger and 1.10x unreached floor.",
                    "assets": ["crystalline_deflection_prism", "parabolic_vector_path", "hazard_boundary_line"],
                    "negative_constraints": FORBIDDEN_VISUAL_PATTERNS + ["explosions", "shattering glass", "stock shield icons"],
                    "veo_prompt": (
                        "Cinematic architectural macro shot of a precision-cut transparent crystalline prism suspended in deep space. "
                        "A sharp glowing beam of cyan light strikes the prism and refracts smoothly upward into a stable, peaceful horizontal orbit, "
                        "completely avoiding a faint red boundary plane below. Rich fuchsia-magenta atmospheric glow (#5E0D46) in upper-right. "
                        "Fine film grain, beautiful optical caustics, slow elegant camera pan, high-end studio lighting, zero text, zero badges."
                    ),
                }

            else:
                # Scene 4: Isolated Solvency Terminal
                visual_spec = {
                    "scene_id": 4,
                    "duration": s.get("duration_seconds", 3.0),
                    "narrative_purpose": s.get("narrative_purpose", ""),
                    "visual_concept": "Three modular obsidian and frosted glass vault chambers resting securely in tranquil equilibrium.",
                    "composition": "Stable, symmetrical architectural composition with vast negative space and reflective obsidian floor.",
                    "camera": "Slow, majestic crane up / tilt down, settling on the secure modular architecture.",
                    "motion": "Static architectural permanence; gentle breathing ambient glow from within the isolated chambers.",
                    "lighting": "Clean rim lighting defining the chamber bevels; serene lavender and cyan ambient washes.",
                    "color": "Deep obsidian base #07020D with calm lavender #A387FF and mint-cyan #22D3C4 interior radiance.",
                    "typography": "Vanna protocol wordmark and clean call-to-action typography.",
                    "assets": ["modular_sandbox_chambers", "reflective_floor_plane", "vanna_monogram"],
                    "negative_constraints": FORBIDDEN_VISUAL_PATTERNS + ["floating coins", "fireworks", "pulsing circles"],
                    "veo_prompt": (
                        "Cinematic wide architectural shot of three minimalist, monolithic glass and dark obsidian vaults (#07020D) "
                        "resting upon a mirror-polished dark floor. The vaults glow softly from within with serene lavender (#A387FF) "
                        "and mint-cyan (#22D3C4) light. Perfect calm, quiet architectural authority, atmospheric violet haze. "
                        "35mm film grain, slow cinematic crane-up movement, studio rim lighting, zero text, zero logos, photorealistic."
                    ),
                }

            art_directed_scenes.append(visual_spec)

        return {
            "campaign": script.get("campaign", {}),
            "creative_thesis": "Visualizing risk deflection and modular containment through precision optical and architectural physics.",
            "brand_system": self.brand_system,
            "scenes": art_directed_scenes,
            "global_negative_constraints": FORBIDDEN_VISUAL_PATTERNS,
        }


def generate_art_direction(script: Dict[str, Any], out_path: Optional[Path] = None) -> Dict[str, Any]:
    ad = VideoArtDirector()
    art_plan = ad.direct_visuals(script)
    if out_path:
        out_path = Path(out_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(art_plan, indent=2), encoding="utf-8")
        print(f"✅ VIDEO ART DIRECTOR: Generated {out_path.name}")
    return art_plan
