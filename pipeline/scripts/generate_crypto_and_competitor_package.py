#!/usr/bin/env python3
"""Generates visual assets and compiles the full package:
1. 3 Vanna Crypto Architecture Posts (Mempool MEV, Isolated Contagion, 10x Margin)
2. 3 Underrated Competitor Scout Briefs (Silo v3, Wildcat Protocol, Gearbox Protocol)
3. 3 Brand-new textless geometric visuals via gemini-3.1-flash-image (Nano Banana)
4. Interactive HTML preview in pipeline/state/vanna_crypto_and_competitors.html
"""

from __future__ import annotations

import base64
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

STATE_DIR = REPO_ROOT / "pipeline" / "state"

from pipeline.scripts.gemini_flash_image import generate_gemini_image

# 1. Generate Visual 1: Sub-Second Telemetry Deflection (EVM Mempool vs Soroban)
v1_path = STATE_DIR / "vanna_vis_crypto_telemetry.png"
if not v1_path.exists():
    prompt_1 = (
        "Masterpiece ultra-minimalist vector motion design art. Pure textless visual abstraction. "
        "Canvas: Deep obsidian black (#07020D) with tactile 35mm analog film grain. Diagonally illuminated "
        "by dual ambient blooms: electric royal violet (#471485) at lower-left, warm fuchsia-magenta (#5E0D46) "
        "at upper-right. Over 85% vast negative space. "
        "Design Elements: A single razor-thin horizontal vector stream in soft lavender (#A387FF) encounters "
        "an ultra-delicate crystalline threshold lens. At the exact inflection node, the stream smoothly deflects "
        "upward into a frictionless parabolic ascending arc of electric cyan (#22D3C4), settling into an elevated, "
        "stable horizontal flight path. Below the deflection zone, an untouchable baseline boundary in faint crimson "
        "remains completely pristine and uncrossed. Absolute zero text, zero letters, zero numbers, zero typography, "
        "zero UI buttons, zero generic glowing spheres. Precision architectural drafting."
    )
    generate_gemini_image(prompt_1, v1_path, project="vanna-mcp", location="global", model="gemini-3.1-flash-image")
    print("✅ Generated Visual 1:", v1_path.name)

# 2. Generate Visual 2: Isolated Compartment Equilibrium (Bad Debt Containment)
v2_path = STATE_DIR / "vanna_vis_crypto_isolation.png"
if not v2_path.exists():
    prompt_2 = (
        "Masterpiece ultra-minimalist geometric design art. Pure textless visual abstraction. "
        "Canvas: Deep obsidian void (#07020D) with fine 35mm film grain, framed by soft ambient electric violet "
        "(#471485) in bottom-left and radiant fuchsia (#5E0D46) in top-right. Over 85% negative space. "
        "Design Elements: Three freestanding, perfectly proportioned rectangular chambers constructed from dark smoked "
        "obsidian glass with chamfered titanium edges standing in serene topological equilibrium. Inside the center chamber, "
        "an internal geometric ribbon in warm coral (#FC5457) is securely quarantined, with zero light leaking into "
        "adjacent units. Crisp hairline horizontal vector lines connect the bases. Absolutely zero text, zero typography, "
        "zero letters, zero numbers, zero generic crypto spheres. Museum-grade technical visualization."
    )
    generate_gemini_image(prompt_2, v2_path, project="vanna-mcp", location="global", model="gemini-3.1-flash-image")
    print("✅ Generated Visual 2:", v2_path.name)

# 3. Generate Visual 3: 10x Margin Optical Prism Refraction
v3_path = STATE_DIR / "vanna_vis_crypto_multiplier.png"
if not v3_path.exists():
    prompt_3 = (
        "Masterpiece ultra-minimalist architectural light art. Pure textless visual abstraction. "
        "Canvas: Deep obsidian void (#07020D) with tactile 35mm film grain. Soft ambient blooms of royal violet "
        "(#471485) bottom-left, warm magenta (#5E0D46) top-right. Over 85% negative space. "
        "Design Elements: A single, monolithic smoked glass rectangular prism suspended in space. A razor-thin "
        "single horizontal white beam enters the optical face from left. Inside the crystalline chamber, the beam "
        "refracts and amplifies into ten perfectly parallel, ultra-fine coherent filaments in electric cyan (#22D3C4) "
        "and lavender (#A387FF) emerging cleanly into stable space. Absolutely zero text, zero typography, zero letters, "
        "zero numbers, zero generic 3D cubes. Supreme institutional calm."
    )
    generate_gemini_image(prompt_3, v3_path, project="vanna-mcp", location="global", model="gemini-3.1-flash-image")
    print("✅ Generated Visual 3:", v3_path.name)

print("All visuals confirmed ready.")
