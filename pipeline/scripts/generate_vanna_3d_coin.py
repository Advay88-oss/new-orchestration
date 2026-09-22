#!/usr/bin/env python3
"""Generates a tactile 3D physical Vanna coin image matching gx942fxmI0TsFYbX-2.mp4:
- Thick cylindrical coin in three-quarter perspective.
- Brushed copper, rose-gold, and terracotta metallic finish with micro-texture.
- Deeply debossed with the bold '10x' multiplier and Vanna geometric folded ribbon glyph.
- Glowing electric violet (#471485) and fuchsia-magenta (#5E0D46) rim light catching the bevel.
- Deep obsidian void background (#07020D) with subtle purple ambient underglow.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path("D:/new orchestration")
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

STATE_DIR = REPO_ROOT / "pipeline" / "state"
OUT_IMG = STATE_DIR / "vanna_3d_physical_coin.png"

from pipeline.scripts.gemini_flash_image import generate_gemini_image

prompt = (
    "A photorealistic, studio product macro shot of a single thick 3D physical cryptocurrency coin floating in three-quarter perspective, "
    "centered in frame against a deep obsidian black background (#07020D). "
    "The coin is crafted from heavy, fine-grain matte brushed copper, rose-gold, and terracotta metal with micro-textured surface and smooth beveled chamfer edges. "
    "Crisply stamped and debossed into the center of the coin face is the bold typographic '10x' multiplier glyph, seamlessly integrated with the Vanna folded geometric ribbon logo. "
    "Cinematic studio key lighting from the front-left, with a striking electric royal violet (#471485) and radiant fuchsia-magenta (#5E0D46) rim light "
    "gleaming intensely along the top-right curved edge and beveled rim. "
    "Subtle ambient purple gradient reflection beneath the coin. Pure black negative space on the left and right. "
    "Zero text other than '10x', zero floating clutter, zero generic spheres with rings. Commercial 3D Cinema 4D / Octane Render quality, 8K resolution."
)

print("▶ Generating 3D physical Vanna coin image via gemini-3.1-flash-image...")
generate_gemini_image(prompt, OUT_IMG, project="vanna-mcp", location="global", model="gemini-3.1-flash-image")
print(f"✅ Generated 3D Coin Image: {OUT_IMG.name} ({OUT_IMG.stat().st_size:,} bytes)")
