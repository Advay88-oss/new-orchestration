#!/usr/bin/env python3
"""Vanna Visual Reference Principles (pipeline/creative_memory/visual_reference_principles.py).

Defines HOW TO THINK about Vanna approved visual references rather than WHAT TO DRAW.
Extracts:
  - Core design principles (hierarchy, negative space, technical clarity, restraint)
  - Content-to-visual mapping rules (architecture, data, product, risk, ecosystem)
  - Anti-patterns and overfitted cliches to deliberately avoid
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class VisualReferencePrinciple:
    reference_id: str
    title: str
    content_intent: str
    why_it_works: str
    information_hierarchy: str
    composition_principles: List[str]
    visual_metaphor_principles: List[str]
    typography_role: str
    negative_space_usage: str
    contrast_and_depth: str
    technical_clarity: str
    brand_principles: List[str]
    overfitted_cliches_to_avoid: List[str]


# Canonical reference principles extracted from the founder's approved visual quality bar
VANNA_VISUAL_REFERENCE_PRINCIPLES: Dict[str, VisualReferencePrinciple] = {
    "REF_BLEND_COMPOSABILITY": VisualReferencePrinciple(
        reference_id="REF_BLEND_COMPOSABILITY",
        title="Blend Protocol Composability & SmartAccount Routing",
        content_intent="Ecosystem / Composability / Multi-Venue Routing",
        why_it_works=(
            "Uses a singular, clean relationship metaphor where sovereign user collateral "
            "routes into external lending venues without capital leakage. Strong focal clarity, "
            "calibrated visual weight, and deliberate breathing room."
        ),
        information_hierarchy="Primary destination anchor -> routing relationship -> mathematical fee/efficiency proof.",
        composition_principles=[
            "One dominant focal anchor rather than competing visual elements.",
            "Asymmetrical tension resolving into stable institutional balance.",
            "At least 60% negative space so technical relationships are legible in 2 seconds."
        ],
        visual_metaphor_principles=[
            "Use spatial conduit, structural convergence, or modular dock metaphors.",
            "Visual metaphor must directly illustrate how capital multiplies across boundaries."
        ],
        typography_role="Minimal status tags (Plus Jakarta Sans / JetBrains Mono) that clarify without cluttering.",
        negative_space_usage="Generous, calm negative space that communicates institutional confidence.",
        contrast_and_depth="Crisp optical separation between foreground components and the deep background void.",
        technical_clarity="Immediate comprehension of the relationship within 2 to 3 seconds of viewing.",
        brand_principles=[
            "Official Vanna brand badge in top-left with proper clear space.",
            "Subtle ambient bloom (#471485 / #5E0D46) as environmental lighting, never as garish neon decoration.",
            "35mm analog film grain for premium hardware texture."
        ],
        overfitted_cliches_to_avoid=[
            "Three identical purple cubes connected with arrows.",
            "Horizontal 3-column layout (Wallet -> Cube -> Lattice).",
            "Lavender processor chips with neon pins.",
            "Generic connected nodes that look like a generic Web3 flowchart."
        ]
    ),
    "REF_SUBSECOND_SOLVENCY": VisualReferencePrinciple(
        reference_id="REF_SUBSECOND_SOLVENCY",
        title="Sub-Second Solvency & 1.10x Liquidation Floor",
        content_intent="Risk / Security / Solvency Architecture",
        why_it_works=(
            "Conveys mathematical protection and containment through physical caustics and threshold deflection. "
            "The visual proves safety before liquidation occurs without resorting to alarmist red warning boxes."
        ),
        information_hierarchy="Protective threshold barrier -> incoming force vector -> deflected trajectory.",
        composition_principles=[
            "Threshold division: clear optical boundary separating the protected zone from the hazard zone.",
            "Directional motion vector demonstrating dynamic deflection.",
            "Focal illumination centered on the barrier mechanism."
        ],
        visual_metaphor_principles=[
            "Hydro-dynamic dampening, optical refraction prism, magnetic deflection field, or structural bulkhead.",
            "Must convey that risk is localized and quarantined, never shared."
        ],
        typography_role="Key parameter callout (e.g. '1.10x floor', '~320ms') positioned as an engineered coordinate stamp.",
        negative_space_usage="Atmospheric negative space emphasizing isolation and containment.",
        contrast_and_depth="Deep chiaroscuro with precise specular highlights on the barrier surface.",
        technical_clarity="The viewer immediately grasps: 'force hits barrier, force redirects, capital survives.'",
        brand_principles=[
            "Clean institutional finish; zero cartoonish shields or padlocks.",
            "Controlled coral accent (#FC5457) reserved strictly for risk/hazard thresholds.",
            "Mint green (#38EF7D) reserved strictly for solvency confirmation."
        ],
        overfitted_cliches_to_avoid=[
            "Microchip with coral pins and 3 squircle cards.",
            "Alarmist red warning banners.",
            "Centered glowing sphere deflected by an arrow."
        ]
    ),
    "REF_YIELD_STACKING": VisualReferencePrinciple(
        reference_id="REF_YIELD_STACKING",
        title="LP Capital Efficiency & Dynamic Rate Model",
        content_intent="Market Data / Capital Efficiency / Yield Stacking",
        why_it_works=(
            "Translates polynomial rate curves and stacked yield layers into an intuitive spatial or physical structure. "
            "Numbers are supported by structural volume rather than flat spreadsheet tables."
        ),
        information_hierarchy="Aggregate yield foundation -> dynamic rate layer -> liquidation penalty distribution.",
        composition_principles=[
            "Vertical or tiered spatial accumulation demonstrating compounding value.",
            "Clean grid alignment reflecting algorithmic precision.",
            "Uncluttered horizon line providing scale."
        ],
        visual_metaphor_principles=[
            "Layered strata, celestial gravitational orbital resonance, precision mechanical gear train, or editorial data rail.",
            "Must convey that yield is mathematically derived from utility, not speculative inflation."
        ],
        typography_role="Data metrics presented with clear optical scale (large numerals, restrained units).",
        negative_space_usage="Open vertical canvas allowing the tiered structure to rise cleanly.",
        contrast_and_depth="Subtle gradient lighting that reveals layer boundaries through edge illumination.",
        technical_clarity="Immediate understanding of how dual revenue streams combine to multiply LP return.",
        brand_principles=[
            "Strict color harmony: deep obsidian base with electric cyan and royal violet.",
            "No cheap gold coins, no upward green cartoon arrows, no stock candlestick charts."
        ],
        overfitted_cliches_to_avoid=[
            "Stack of 3 generic purple 3D blocks.",
            "Floating dollar signs or golden tokens.",
            "Flat spreadsheet cards floating in a void."
        ]
    )
}


# Content-Specific Creative Treatment Matrix
CONTENT_TREATMENT_MAPPING = {
    "technical_architecture": {
        "recommended_treatments": [
            "refined technical illustration",
            "spatial containment metaphor",
            "architectural blueprint with dimension rails",
            "isometric sectional cutaway",
            "system state transition diagram"
        ],
        "primary_focus": "Structural state isolation, contract boundaries, modular sandboxes.",
        "avoid_aesthetics": ["cinematic movie poster", "neon disco glow", "generic 3D cubes"]
    },
    "product_value_proposition": {
        "recommended_treatments": [
            "designed product interface integration",
            "tactile terminal mockup with perspective camera choreography",
            "dual-state comparison (legacy vs composable)",
            "operational cockpit with live status chips"
        ],
        "primary_focus": "Tactile utility, user workflow, atomic execution, speed.",
        "avoid_aesthetics": ["abstract cosmic particles", "flat rectangular card in a void"]
    },
    "market_data_insight": {
        "recommended_treatments": [
            "editorial data visualization",
            "information-led typography and metric composition",
            "statistical data matrix with calibrated hierarchy",
            "kinetic rate curve with coordinate callouts"
        ],
        "primary_focus": "TVL growth, volume, yield curves, fixed fee guarantees.",
        "avoid_aesthetics": ["cinematic 3D render without data", "stock crypto candlestick chart"]
    },
    "risk_security_concept": {
        "recommended_treatments": [
            "physical containment and pressure metaphor",
            "hydro-dynamic shock absorption",
            "optical deflection caustics",
            "watertight bulkhead structural metaphor"
        ],
        "primary_focus": "1.10x floor, bad debt quarantine, sub-second liquidation prevention.",
        "avoid_aesthetics": ["cartoon padlocks", "alarmist red warning sirens", "purple cubes"]
    },
    "ecosystem_integration": {
        "recommended_treatments": [
            "ecosystem relationship visualization",
            "atomic protocol handshake",
            "modular liquidity infrastructure dock",
            "cross-protocol capital bridge"
        ],
        "primary_focus": "Blend b-tokens, Soroswap AMM, Stellar Soroban Protocol 20.",
        "avoid_aesthetics": ["floating 3D logos without connection", "spiderweb network nodes"]
    }
}
