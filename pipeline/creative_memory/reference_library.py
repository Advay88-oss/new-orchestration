#!/usr/bin/env python3
"""Vanna Creative Reference Library (pipeline/creative_memory/reference_library.py).

Defines the positive creative references approved by the founder:
  1. REF_41S_MASTER_FILM: 41s Master Product Film (quality bar, 5-act pacing, narrative intentionality)
  2. REF_VID_02_RISK_MANAGEMENT: Physical material metaphor, volumetric lighting, majestic orbital inertia
  3. REF_VID_03_AGENTIC_CREDIT: High-cadence kinetic editorial typography, authoritative speed, data rails
  4. REF_VID_04_LP_CAPITAL_EFFICIENCY: Interactive avionics cockpit, real product screen integration with camera tracking
  5. REF_DEFI_TRANSITION: Spatial and conceptual match-cut continuity, focal anchor persistence, dimensional expansion
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class CreativeReference:
    reference_id: str
    title: str
    what_works: str
    motion_principles: List[str]
    composition_principles: List[str]
    transition_principles: List[str]
    typography_principles: List[str]
    pacing: str
    visual_language: str
    product_integration: str
    strengths: List[str]
    limitations: List[str]


# The 5 Approved Vanna Reference Profiles
VANNA_CREATIVE_REFERENCES: Dict[str, CreativeReference] = {
    "REF_41S_MASTER_FILM": CreativeReference(
        reference_id="REF_41S_MASTER_FILM",
        title="41-Second Master Product Film",
        what_works=(
            "High-converting 5-act intentional narrative cadence (Problem -> Vanna Intro -> "
            "Solution -> Real Telemetry -> CTA). Every second has clear narrative purpose; "
            "information density is calibrated with zero idle frames. Symmetrical partnerships "
            "resolve into focused product claims."
        ),
        motion_principles=[
            "Continuous subtle forward momentum (camera push or gentle rotation) prevents static pauses.",
            "Secondary motion always guides the eye to the next visual reveal.",
            "Smooth spring physics with calculated damping curves (no linear easing)."
        ],
        composition_principles=[
            "Asymmetrical tension in problem scenes resolving into centered symmetrical balance in solution scenes.",
            "Golden-ratio framing for multi-column technical pipelines.",
            "Generous negative space around bold assertions so technical claims have room to breathe."
        ],
        transition_principles=[
            "Thematic and spatial match-cuts preserving optical axis continuity.",
            "Sub-bass sonic impacts paired with visual scale expansions.",
            "Dimensional zoom from abstract asset into real operational UI."
        ],
        typography_principles=[
            "Strict two-tier font hierarchy: Plus Jakarta Sans ExtraBold 64px for macro narrative assertions, "
            "paired with JetBrains Mono 14px for immutable on-chain telemetry.",
            "Spring-damped vertical entrance (translateY: 26px -> 0px) rather than arbitrary fades."
        ],
        pacing="Structured 5-act rhythm: 8s problem hook, 8s identity anchor, 9s solution pipeline, 8.5s telemetry proof, 7.5s resolution/CTA.",
        visual_language="Obsidian canvas (#07020D) with dual-point ambient bloom (#471485 violet / #5E0D46 magenta), high-contrast telemetry lines.",
        product_integration="Hybrid transition: shifts smoothly from high-level abstract finance into live HUD telemetry cards and verifiable testnet contract addresses.",
        strengths=[
            "Unmatched narrative authority and executive gravitas.",
            "Flawless synchronization between voiceover and visual reveals.",
            "High information density without visual clutter."
        ],
        limitations=[
            "Must NOT be copied as a rigid template; treating every video as a 5-act trailer dilutes focused deep-dives."
        ]
    ),
    "REF_VID_02_RISK_MANAGEMENT": CreativeReference(
        reference_id="REF_VID_02_RISK_MANAGEMENT",
        title="Video 2: The Guardian Mechanism (Physical Metaphor)",
        what_works=(
            "Communicates complex mathematical solvency without fake UI cards through pure physical/sculptural metaphor. "
            "Uses heavy material inertia and caustics to convey unshakeable institutional stability."
        ),
        motion_principles=[
            "Heavy physical momentum and material inertia.",
            "Majestic 360-degree orbital camera choreography around monolithic geometry.",
            "Gradual, controlled deceleration curves communicating unyielding defense."
        ],
        composition_principles=[
            "Low-key dramatic studio lighting with rim-light separation.",
            "Deep tunnel perspective with strong central focal point.",
            "Chiaroscuro contrast emphasizing structural resilience."
        ],
        transition_principles=[
            "Volumetric focus pulls through atmospheric haze.",
            "Luminance dissolution: hazard lines physically deflect away from a crystalline barrier."
        ],
        typography_principles=[
            "Minimalist, etched coordinates floating in 3D depth space.",
            "Subtle monospace parameter stamps anchored to physical surfaces."
        ],
        pacing="Measured, contemplative, cinematic (4.0s - 5.0s holds per scene) allowing material depth to register.",
        visual_language="Tactile dark obsidian, liquid caustics, emerald green #38EF7D and cyan #22D3C4 luminescence against deep void.",
        product_integration="Zero product screen: relies 100% on metaphorical physical phenomena to explain smart contract risk math.",
        strengths=[
            "Extraordinary visual craft and institutional prestige.",
            "Memorable physical metaphor that bypasses technical jargon."
        ],
        limitations=[
            "Does not teach the user how to click or use the live app interface."
        ]
    ),
    "REF_VID_03_AGENTIC_CREDIT": CreativeReference(
        reference_id="REF_VID_03_AGENTIC_CREDIT",
        title="Video 3: The Architect of Autonomous Credit (Kinetic Editorial)",
        what_works=(
            "Rapid typographic momentum and high-frequency intellectual stimulation. "
            "Authoritative kinetic typography communicates algorithmic speed and developer control."
        ),
        motion_principles=[
            "Snap-to-grid typographic entrances with zero motion blur.",
            "Linear streaming data rails and telemetry ticks.",
            "Staccato rhythmic cuts that synchronize with technical assertions."
        ],
        composition_principles=[
            "Asymmetrical peripheral data rails framing a locked frontal typographic center.",
            "High-density structural grids and architectural crosshairs."
        ],
        transition_principles=[
            "Abrupt lateral snap-cuts and high-contrast flash frames.",
            "Instantaneous text replacements on the musical or rhythmic beat."
        ],
        typography_principles=[
            "Variable-weight typography, oversized kinetic keywords, timestamped block numbers.",
            "Fixed gas fee stamps (0.00014 XLM) acting as immutable rhythmic anchors."
        ],
        pacing="High-speed, authoritative, staccato pacing (2.5s - 3.5s per beat), high information bandwidth.",
        visual_language="High-contrast stark monochrome with electric cyan #22D3C4 laser luminescence and structural grid overlays.",
        product_integration="Product UI is framed with dynamic 3D perspective tilt and kinetic bracket overlays rather than a flat card.",
        strengths=[
            "High energy, impossible to ignore, conveys developer horsepower and precision.",
            "Excels at communicating programmable protocols and agentic workflows."
        ],
        limitations=[
            "Can feel overwhelming if used for contemplative institutional risk topics."
        ]
    ),
    "REF_VID_04_LP_CAPITAL_EFFICIENCY": CreativeReference(
        reference_id="REF_VID_04_LP_CAPITAL_EFFICIENCY",
        title="Video 4: Precision Yield Control (Tactical Interface)",
        what_works=(
            "Frames the decentralized protocol as a high-precision avionics cockpit. "
            "Balances real application functionality with clean, responsive motion design and tracking callouts."
        ),
        motion_principles=[
            "Elastic spring physics for responsive UI state updates.",
            "Smooth virtual camera tracking that follows user interaction hotspots.",
            "Dynamic cursor choreography directing user attention."
        ],
        composition_principles=[
            "Elevated 3D perspective tilt with subtle glass reflections.",
            "Contextual callout brackets pinned to specific UI buttons and metrics."
        ],
        transition_principles=[
            "Spatial zoom into functional sub-modules (e.g. macro portfolio -> swap execution rail).",
            "Smooth cross-fades between interface states while maintaining camera trajectory."
        ],
        typography_principles=[
            "Crisp HUD telemetry callouts, count-up metric tickers, legible data hierarchy.",
            "Monospace tags (#38EF7D mint green) for active yields and liquidation thresholds."
        ],
        pacing="Methodical and educational (3.5s - 4.5s per scene), allowing viewers to comprehend real product utility.",
        visual_language="Refined Web3 dark mode, frosted glass backplates, glowing emerald and cyan status badges.",
        product_integration="Live product screen recordings treated as 3D physical objects in space with dynamic lighting and camera tracking.",
        strengths=[
            "High institutional trust; definitively proves the software is live and functional.",
            "Clear demonstration of real user benefits and workflow efficiency."
        ],
        limitations=[
            "Less abstract/philosophical; focuses specifically on software interaction."
        ]
    ),
    "REF_DEFI_TRANSITION": CreativeReference(
        reference_id="REF_DEFI_TRANSITION",
        title="The DeFi Part Transition (Match-Cut Morph)",
        what_works=(
            "Spatial and conceptual continuity across disparate visual domains. Instead of an arbitrary cut, "
            "an abstract geometric structure physically morphs or expands to reveal the underlying DeFi mechanism, "
            "preserving the viewer's eye-trace."
        ),
        motion_principles=[
            "Continuous motion vector: velocity and direction carry across the cut into the incoming scene.",
            "Morphing geometry: outward expansion of shapes reveals internal UI contents.",
            "Shared optical center keeps the viewer's gaze anchored."
        ],
        composition_principles=[
            "Aligned horizon lines and shared optical centers between outgoing and incoming scenes.",
            "Progressive disclosure: outer container dissolves while internal data persists."
        ],
        transition_principles=[
            "Match-cut with dimensional expansion.",
            "Typographic persistence: key metric values (e.g. '1.10x' or '0.00014 XLM') remain fixed in space while the environment transforms behind them.",
            "Cubic bezier easing (0.8s - 1.2s duration) ensuring fluid transformation."
        ],
        typography_principles=[
            "Persistent anchor metric: one key numerical datum bridges the transition.",
            "Seamless size and position interpolation across the boundary."
        ],
        pacing="Fluid, elastic transition pacing (0.8s - 1.2s) that eliminates visual jar.",
        visual_language="Hybrid bridge blending abstract 3D spatial materials with tactical dark-mode UI elements.",
        product_integration="The ultimate bridge between high-concept storytelling and real software execution.",
        strengths=[
            "Elevates video from a disconnected slideshow into a seamless cinematic experience.",
            "Maintains viewer orientation through complex financial logic."
        ],
        limitations=[
            "Requires precise spatial and thematic alignment between paired scenes."
        ]
    )
}


class ReferenceLibrary:
    """Provides access to positive creative references and manages reference blending."""

    def __init__(self, storage_dir: Optional[Path] = None):
        self.storage_dir = storage_dir or Path("pipeline/creative_memory")
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.references = VANNA_CREATIVE_REFERENCES

    def get_reference(self, reference_id: str) -> Optional[CreativeReference]:
        return self.references.get(reference_id)

    def list_references(self) -> List[CreativeReference]:
        return list(self.references.values())

    def blend_reference_principles(
        self,
        primary_ref_ids: List[str],
        narrative_intent: str,
        exclude_cliches: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Dynamically synthesizes motion, composition, transition, typography, and pacing

        principles from multiple positive references without copying any specific scene.
        """
        exclude = set(exclude_cliches or [])
        blended_motion = []
        blended_comp = []
        blended_transitions = []
        blended_typo = []
        blended_strengths = []
        applied_refs = []
        omitted_principles = []

        for ref_id in primary_ref_ids:
            ref = self.references.get(ref_id)
            if not ref:
                continue
            applied_refs.append(ref.title)
            blended_motion.extend(ref.motion_principles[:2])
            blended_comp.extend(ref.composition_principles[:2])
            blended_transitions.extend(ref.transition_principles[:2])
            blended_typo.extend(ref.typography_principles[:1])
            blended_strengths.extend(ref.strengths[:1])

            # Record what is intentionally NOT used from this reference
            if ref_id == "REF_41S_MASTER_FILM":
                omitted_principles.append("Intentionally NOT copying 41s 5-act rigid structure or coin rotation template.")
            elif ref_id == "REF_VID_02_RISK_MANAGEMENT":
                omitted_principles.append("Intentionally NOT using dark obsidian monolith if narrative calls for real product proof.")
            elif ref_id == "REF_VID_03_AGENTIC_CREDIT":
                omitted_principles.append("Intentionally NOT using chaotic flash cuts; preserving legibility.")
            elif ref_id == "REF_VID_04_LP_CAPITAL_EFFICIENCY":
                omitted_principles.append("Intentionally NOT using flat screen recording without camera choreography.")

        return {
            "applied_references": applied_refs,
            "narrative_intent": narrative_intent,
            "synthesized_motion_principles": list(dict.fromkeys(blended_motion))[:4],
            "synthesized_composition_principles": list(dict.fromkeys(blended_comp))[:4],
            "synthesized_transition_principles": list(dict.fromkeys(blended_transitions))[:4],
            "synthesized_typography_principles": list(dict.fromkeys(blended_typo))[:3],
            "intentionally_omitted_principles": omitted_principles,
            "blending_rationale": (
                f"Blended {len(applied_refs)} references to serve '{narrative_intent}' "
                f"while enforcing distinct creative identity."
            )
        }

    def export_library_markdown(self) -> str:
        """Exports the reference library as a formatted markdown document."""
        md = ["# Vanna Creative Reference Library\n"]
        md.append("Extracted design principles from the 5 positive references approved by the founder:\n")
        for ref_id, ref in self.references.items():
            md.append(f"## {ref.title} (`{ref.reference_id}`)\n")
            md.append(f"**What Works:** {ref.what_works}\n")
            md.append(f"**Visual Language:** {ref.visual_language}\n")
            md.append(f"**Pacing:** {ref.pacing}\n")
            md.append(f"**Product Integration:** {ref.product_integration}\n")
            md.append("\n### Motion Principles:")
            for p in ref.motion_principles:
                md.append(f"- {p}")
            md.append("\n### Composition Principles:")
            for p in ref.composition_principles:
                md.append(f"- {p}")
            md.append("\n### Transition Principles:")
            for p in ref.transition_principles:
                md.append(f"- {p}")
            md.append("\n### Typography Principles:")
            for p in ref.typography_principles:
                md.append(f"- {p}")
            md.append("\n### Strengths & Limitations:")
            md.append(f"- **Strengths:** {'; '.join(ref.strengths)}")
            md.append(f"- **Limitations:** {'; '.join(ref.limitations)}")
            md.append("\n---\n")
        return "\n".join(md)
