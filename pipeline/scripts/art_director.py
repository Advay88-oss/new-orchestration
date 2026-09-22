#!/usr/bin/env python3
"""Vanna Visual Art Director — True Creative Direction Layer.

Before rendering, Art Director decides:
  1. narrative: core message and market tension
  2. composition_family: chosen from 7 defined families
  3. visual_metaphor: narrative-specific concept (not generic decorative shapes)
  4. focal_object: central physical/visual anchor
  5. visual_hierarchy: ordered prominence of elements
  6. typography_hierarchy: dominant hook, supporting line, zero large paragraphs
  7. accent_usage: Vanna Obsidian (#08070C), Lavender (#A387FF), Coral (#FC5457), micro-Cyan
  8. cta: clean destination (vanna.finance or test.stellar.vanna.finance)
  9. what_should_not_be_shown: negative prompt constraints (no spheres with rings, no badges, no UI cards)
"""

from __future__ import annotations

import json
import sys
from typing import Any, Dict, List, Optional

# The 7 Art-Directed Composition Families
COMPOSITION_FAMILIES = {
    "cinematic_metaphor": {
        "name": "cinematic object / metaphor",
        "description": "Single dominant physical/cryptographic metaphor with dramatic lighting and physical materiality.",
        "best_for": ["autonomous_risk", "security_boundary", "capital_protection"]
    },
    "editorial_hero": {
        "name": "editorial typography + hero visual",
        "description": "Asymmetric editorial layout pairing massive negative space with a focused visual anchor.",
        "best_for": ["narrative_thesis", "brand_genesis", "market_critique"]
    },
    "technical_architecture": {
        "name": "technical architecture visualization",
        "description": "Blueprint/isometric topological schematic showing execution sandboxes and liquidity paths.",
        "best_for": ["margin_accounts", "composability", "soroban_contracts"]
    },
    "system_diagram": {
        "name": "system diagram",
        "description": "Relational vector flow showing inputs, multiplier mechanisms, and protected outputs.",
        "best_for": ["credit_routing", "liquidity_pools", "settlement"]
    },
    "data_visual": {
        "name": "data-driven visual",
        "description": "Quantitative threshold manifold (volatility surface, Greeks envelope, solvency ratio).",
        "best_for": ["greeks_hedging", "health_factor", "liquidation_floor"]
    },
    "statement_poster": {
        "name": "statement poster",
        "description": "High-conviction typography-forward poster with intense contrast and subtle structural geometry.",
        "best_for": ["manifesto", "category_redefinition"]
    },
    "comparison_equilibrium": {
        "name": "comparison / before-vs-after",
        "description": "Dual-state structural tension (fragmented silos vs unified lattice equilibrium).",
        "best_for": ["isolated_vs_unified", "overcollateralization_contrast"]
    }
}

NEGATIVE_PROMPT_CONSTRAINTS = [
    "No generic spheres with concentric rings (overused AI crypto cliché)",
    "No AI implementation labels ('Gemini 3.1 Flash Image', 'AI Generated', 'Model Garden')",
    "No generic crypto dashboard UI (no toggle switches, mock price charts, faux cards)",
    "No tabular data rows or 3-row/4-row infographic cards",
    "No Canva-style layout (no generic pill badges, colored text highlights, or clip art)",
    "No pastel blue/pink gradients or generic SaaS landing page aesthetics",
    "No text inside the generated image unless explicitly art-directed as minimal typography",
    "No literal golden coins, padlocks, or cheesy financial symbols"
]


def direct_art_for_narrative(
    narrative: str,
    copy_text: str,
    topic: str = "autonomous_risk"
) -> Dict[str, Any]:
    """Generates a complete ArtDirectionSpec tailored to the specific narrative.
    Derives the visual metaphor from what the narrative actually means, not generic decoration.
    """
    narrative_lower = narrative.lower() + " " + copy_text.lower()

    # Determine composition family & narrative metaphor
    if any(k in narrative_lower for k in ["asleep", "03:00", "03:14", "crash", "guardian", "volatility", "unstable", "protect"]):
        family = "cinematic_metaphor"
        visual_metaphor = (
            "A dense, serene crystalline margin core anchored in deep space, completely unaffected "
            "while violent red and violet market turbulence waves strike an invisible parabolic deflection shield outside. "
            "Capital remains in tranquil equilibrium while external chaos is intercepted."
        )
        focal_object = "Deflection shield intercepting violent external market turbulence around a protected core"
        composition = "Off-center right focal anchor with intense left-to-right deflection vectors"
        visual_hierarchy = [
            "1. Deflected volatility shockwaves (coral-pink kinetic turbulence)",
            "2. Parabolic deflection perimeter (luminous lavender force boundary)",
            "3. Calm, illuminated crystalline core (protected capital in equilibrium)",
            "4. Deep obsidian void (#08070C) maintaining high contrast"
        ]
        hook_phrase = "Autonomous protection while you sleep."

    elif any(k in narrative_lower for k in ["silo", "fragment", "walls you in", "unified", "offset"]):
        family = "comparison_equilibrium"
        visual_metaphor = (
            "Dual-state tension: on the left, fragile disconnected blocks cracking under stress; "
            "on the right, an interconnected radiant multi-tier lattice distributing load dynamically in perfect balance."
        )
        focal_object = "Interconnected multi-tier credit lattice absorbing cross-market drawdowns"
        composition = "Side-by-side contrast with high-energy central connection"
        visual_hierarchy = [
            "1. Radiant interconnected lattice nodes (Vanna Lavender)",
            "2. Stress distribution vectors in dynamic tension",
            "3. Disconnected dormant blocks in dull matte grey"
        ]
        hook_phrase = "Unified margin sets you free."

    elif any(k in narrative_lower for k in ["10x", "multiplier", "circuit", "borrow", "blend"]):
        family = "technical_architecture"
        visual_metaphor = (
            "An isometric cryptographic circuit where collateral deposits enter a tiered amplification chamber, "
            "sealing into an enclosed smart contract vault with a razor-thin health factor laser rail beneath."
        )
        focal_object = "Stepped leverage amplifier with sealed vault containment"
        composition = "Isometric perspective flowing diagonally from input node to protected vault"
        visual_hierarchy = [
            "1. Stepped leverage chamber",
            "2. Sealed margin vault",
            "3. Laser health factor horizon"
        ]
        hook_phrase = "Up to 10× undercollateralized margin."

    else:
        family = "editorial_hero"
        visual_metaphor = (
            "An asymmetric hypercube vault floating in an obsidian void with internal laser amplification vectors."
        )
        focal_object = "Asymmetric crystalline vault"
        composition = "65/35 right-weighted asymmetry with intentional void"
        visual_hierarchy = [
            "1. Crystalline prism facets",
            "2. Outer containment nodes",
            "3. Expansive negative space"
        ]
        hook_phrase = "Credit that composes."

    spec = {
        "narrative": narrative,
        "composition_family": family,
        "family_details": COMPOSITION_FAMILIES[family],
        "visual_metaphor": visual_metaphor,
        "focal_object": focal_object,
        "composition": composition,
        "visual_hierarchy": visual_hierarchy,
        "typography_hierarchy": {
            "dominant_hook": hook_phrase,
            "supporting_line": "Vanna keeps your position alive 24/7 without taking wallet custody.",
            "max_rendered_words": 12,
            "rendered_text_policy": "Zero clutter. Dominant visual speaks; tweet text explains."
        },
        "accent_usage": {
            "foundation": (
                "Deep obsidian #07020D base with dual-point atmospheric gradient blooms: "
                "rich electric royal violet (#471485) blooming in the bottom-left corner and "
                "warm fuchsia-magenta (#5E0D46) radiating in the top-right corner, with subtle film grain"
            ),
            "primary_accent": "#A387FF (Vanna Lavender/Violet)",
            "secondary_accent": "#FC5457 (Coral-pink neon shockwave/boundary)",
            "technical_highlight": "#22D3C4 (Micro-cyan only for telemetry nodes, < 5% area)"
        },
        "cta": "vanna.finance",
        "what_should_not_be_shown": NEGATIVE_PROMPT_CONSTRAINTS
    }
    return spec


def compile_image_prompt(art_spec: Dict[str, Any]) -> str:
    """Translates the ArtDirectorSpec into an optimized prompt for Gemini 3.1 Flash Image.
    Strictly enforces the visual metaphor, the exact dual-point ambient gradient background, and negative constraints.
    """
    prompt = (
        f"Art-directed crypto protocol architectural visual for Vanna Protocol. "
        f"Background Canvas: Exact Vanna dual-point ambient gradient background — deep obsidian base (#07020D) "
        f"with an intense electric royal violet bloom (#471485) glowing upward in the bottom-left corner and "
        f"a warm fuchsia-magenta bloom (#5E0D46) radiating in the top-right corner, seamless exponential falloff, "
        f"and subtle analog film grain texture. "
        f"Composition: {art_spec['composition']}. "
        f"Focal Subject: {art_spec['visual_metaphor']} "
        f"Lighting & Accents: Crisp luminous Vanna lavender linework ({art_spec['accent_usage']['primary_accent']}) "
        f"with high-contrast coral-pink highlights ({art_spec['accent_usage']['secondary_accent']}). "
        f"Aesthetic: Institutional financial engineering art inspired by Morpho and Gearbox. "
        f"Negative Constraints: Completely text-free. Zero typography, zero words, zero numbers, "
        f"zero spheres with concentric rings, zero UI boxes, zero cards, zero Canva elements, zero mock price charts."
    )
    return prompt


if __name__ == "__main__":
    test_narrative = (
        "Most leveraged positions fail because crypto crashes while you are asleep. "
        "Vanna provides autonomous risk protection without giving up wallet custody."
    )
    spec = direct_art_for_narrative(test_narrative, test_narrative)
    print("=== ART DIRECTOR SPEC ===")
    print(json.dumps(spec, indent=2))
    print("\n=== COMPILED IMAGE PROMPT ===")
    print(compile_image_prompt(spec))
