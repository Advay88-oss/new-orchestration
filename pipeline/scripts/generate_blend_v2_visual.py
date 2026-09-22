#!/usr/bin/env python3
"""Generates a high-craft visual asset for OPP_BLEND_V2_COMPOSABLE_LEVERAGE:
- Textless abstract geometric physical metaphor for composable credit expansion into Blend v2 pools.
- Vanna brand tokens: deep obsidian #07020D, electric royal violet #471485, fuchsia-magenta #5E0D46.
- 100% textless, zero labels, zero AI slop.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path("D:/new orchestration")
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

STATE_DIR = REPO_ROOT / "pipeline" / "state"
OUT_IMG = STATE_DIR / "vanna_visual_blend_v2_composable.png"

from pipeline.scripts.gemini_flash_image import generate_gemini_image

prompt = (
    "A museum-grade, high-craft abstract geometric product visualization of composable financial liquidity expansion. "
    "Background: An infinite, ultra-deep obsidian black void (#07020D) with two soft, diffuse ambient volumetric gradient blooms: "
    "an electric royal violet (#471485) light bloom radiating from the lower-left corner, and a warm, radiant fuchsia-magenta (#5E0D46) "
    "light bloom softly diffusing from the upper-right corner. "
    "Central subject: A monolithic, precision-cut smoked glass optical prism floating weightlessly at an oblique three-quarter angle. "
    "A single laser-sharp, razor-thin white coherent energy filament enters the left facet of the prism. "
    "Inside the crystal, it refracts and multiplies into ten parallel, perfectly ordered, radiant cyan and lavender laser filaments "
    "that emerge from the right facet and branch into two interlocking geometric torus rings made of dark brushed titanium. "
    "High-contrast studio lighting, sharp specular highlights on the beveled glass facets, subtle 35mm analog film grain across the image. "
    "Strictly ZERO text, ZERO numbers, ZERO letters, ZERO coins, ZERO generic spheres with rings. "
    "At least 75% dark negative space. Ultra-clean architectural fine-art composition."
)

print("▶ Generating Blend v2 Composable Credit visual via gemini-3.1-flash-image...")
generate_gemini_image(prompt, OUT_IMG, project="vanna-mcp", location="global", model="gemini-3.1-flash-image")
print(f"✅ Generated Visual: {OUT_IMG.name} ({OUT_IMG.stat().st_size:,} bytes)")
