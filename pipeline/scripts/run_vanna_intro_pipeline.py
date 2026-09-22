#!/usr/bin/env python3
"""Generates the Vanna Introduction Video using:
  1. Video Scriptwriter (decides narrative, hook, voiceover, beats)
  2. Video Art Director (decides cinematic visual metaphor & exact Veo 3.1 prompt)
  3. Google Veo 3.1 (veo-3.1-fast-generate-preview) for photorealistic AI video synthesis
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

STATE_DIR = REPO_ROOT / "pipeline" / "state"
STATE_DIR.mkdir(parents=True, exist_ok=True)

# 1. Rollback old test file if present
old_test_video = STATE_DIR / "vanna_art_directed_video.mp4"
if old_test_video.exists():
    old_test_video.unlink()
    print("🧹 Rollback: Removed previous 2D test video.")

# 2. Agent 1: Video Scriptwriter for Vanna Introduction
scriptwriter_output = {
    "campaign": {
        "title": "Introducing Vanna Protocol",
        "objective": "Official Protocol Introduction: Composable Credit Infrastructure on Stellar Soroban",
        "target_audience": "DeFi builders, liquidity providers, institutional crypto allocators"
    },
    "core_message": "Vanna introduces composable credit to Stellar Soroban: dedicated on-chain SmartAccount sandboxes, 10x capital efficiency, and sub-second liquidation defense.",
    "hook": "Traditional DeFi lending forces you to choose between capital drag and catastrophic shared-pool liquidations.",
    "narrative_arc": (
        "For years, DeFi borrowers have been trapped in monolithic liquidity pools where bad debt is socialized "
        "and slow block times trigger painful liquidation penalties. Vanna changes the paradigm: dedicated smart contract "
        "sandboxes that isolate user positions, programmatic leverage across Stellar's native DEX and lending protocols, "
        "and sub-second automated risk defense."
    ),
    "scenes": [
        {
            "scene_id": 1,
            "title": "The Monolithic Liquidity Problem",
            "duration": 4.0,
            "voiceover": "Traditional DeFi lending forces all capital into shared pools. When one position breaks, everyone takes a haircut.",
            "on_screen_text": "MONOLITHIC POOLS // SHARED CONTAGION",
            "narrative_purpose": "Establish the systemic risk of legacy lending protocols."
        },
        {
            "scene_id": 2,
            "title": "Introducing Vanna SmartAccounts",
            "duration": 4.0,
            "voiceover": "Meet Vanna: Composable credit infrastructure on Stellar Soroban. Your capital is quarantined in dedicated on-chain sandboxes.",
            "on_screen_text": "VANNA PROTOCOL // ISOLATED SMARTACCOUNTS",
            "narrative_purpose": "Introduce Vanna's core structural differentiator: isolated risk sandboxes."
        },
        {
            "scene_id": 3,
            "title": "10x Composable Capital Expansion",
            "duration": 4.0,
            "voiceover": "Deposit once. Unlock up to 10x margin to deploy atomically across Blend lending and Aquarius liquidity pools.",
            "on_screen_text": "10X LEVERAGE // COMPOSABLE ROUTING",
            "narrative_purpose": "Showcase atomic yield harvesting across the Stellar ecosystem."
        },
        {
            "scene_id": 4,
            "title": "Sub-Second Risk Guardian Defense",
            "duration": 3.0,
            "voiceover": "Sub-second event monitoring defends your position before liquidation can strike. Test live at vanna.finance.",
            "on_screen_text": "VANNA.FINANCE // TESTNET IS LIVE",
            "narrative_purpose": "Institutional call to action and solvency certainty."
        }
    ],
    "ending_cta": {
        "headline": "LAUNCH TESTNET",
        "url": "test.stellar.vanna.finance"
    }
}

script_path = STATE_DIR / "VANNA_INTRO_SCRIPT.json"
script_path.write_text(json.dumps(scriptwriter_output, indent=2), encoding="utf-8")
print(f"✅ AGENT 1 (SCRIPTWRITER): Generated {script_path.name}")

# 3. Agent 2: Video Art Director for Vanna Introduction
art_director_output = {
    "project": "Vanna Official Introduction",
    "creative_thesis": "Visualizing sovereign credit architecture through monolithic obsidian vaults and laser-precise refractive conduits.",
    "brand_system": {
        "palette": {
            "obsidian": "#07020D",
            "royal_violet": "#471485",
            "fuchsia_magenta": "#5E0D46",
            "lavender": "#A387FF",
            "cyan": "#22D3C4"
        },
        "aesthetic": "Ultra-premium, cinematic, institutional, tactile materials, 35mm film grain, vast negative space."
    },
    "hero_veo_scene": {
        "scene_name": "Vanna Introduction Hero Visual",
        "concept": "Sovereign architectural monoliths resting in a deep cosmic obsidian void, channeling crystalline laser conduits of lavender and electric cyan.",
        "camera": "Slow cinematic wide tracking dolly pulling back to reveal three monumental frosted-glass and obsidian vaults, with volumetric violet and magenta light blooms reflecting off a mirror-polished floor.",
        "materials": "Matte obsidian composite, optical leaded crystal with subtle caustics, dark polished liquid floor, fine 35mm film grain.",
        "negative_constraints": [
            "no text", "no words", "no letters", "no floating 3D coins", "no cartoon characters",
            "no cheap neon grids", "no generic glowing spheres", "no stock crypto symbols"
        ],
        "veo_31_prompt": (
            "Cinematic masterwork 4K video. An expansive, atmospheric obsidian void (#07020D) with tactile 35mm analog film grain. "
            "A monumental, precision-milled architectural monolith composed of matte black stone and ultra-clear refractive crystal glass. "
            "Glowing internal conduits of soft lavender (#A387FF) and electric cyan (#22D3C4) pulse calmly within the central core. "
            "Volumetric royal violet bloom (#471485) emerges from the bottom-left corner, while a warm fuchsia-magenta atmospheric glow (#5E0D46) "
            "radiates across the upper-right. The structure rests upon a mirror-polished dark obsidian floor with gentle, photorealistic reflections. "
            "Smooth, slow, cinematic camera dolly backwards and tilting slightly upward. High-end studio rim lighting, pristine optical caustics, "
            "supreme architectural restraint, quiet institutional authority. Absolutely zero text, zero typography, zero logos, zero floating spheres."
        )
    }
}

art_path = STATE_DIR / "VANNA_INTRO_ART_DIRECTION.json"
art_path.write_text(json.dumps(art_director_output, indent=2), encoding="utf-8")
print(f"✅ AGENT 2 (ART DIRECTOR): Generated {art_path.name}")

print("\n[VEO 3.1 PROMPT PREPARED BY ART DIRECTOR]:")
print(art_director_output["hero_veo_scene"]["veo_31_prompt"])
