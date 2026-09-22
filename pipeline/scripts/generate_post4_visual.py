#!/usr/bin/env python3
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from pipeline.scripts.gemini_flash_image import generate_gemini_image

prompt = (
    "Developer-grade DeFi architectural comparative schematic diagram for Vanna Protocol on Stellar Soroban. "
    "Background: Deep obsidian base (#07020D) with soft ambient electric violet glow (#471485) in bottom-left and fuchsia-magenta glow (#5E0D46) in top-right, subtle film grain. "
    "High-contrast horizontal comparative layout with two stacked rows: "
    "TOP ROW: Labeled 'TRADITIONAL EVM LENDING'. Shows a dark box with bold red text '40 DOLLAR GAS SPIKE', a delayed pipe labeled 'CONGESTED MEMPOOL', leading to a red status box labeled 'TRANSACTION DELAYED / LIQUIDATION RISK'. "
    "BOTTOM ROW: Labeled 'VANNA ON STELLAR SOROBAN'. Shows a dark box with bold white text 'SUB-CENT PREDICTABLE GAS (< 0.001 USD)', a direct arrow labeled 'INSTANT SOROBAN FINALITY', leading to a glowing cyan status box labeled 'POSITION SECURED'. "
    "Style: Clean vector line art, technical blueprint, high contrast, crisp typography, generous whitespace. Zero shell variables, zero typos."
)

output_path = REPO_ROOT / "pipeline" / "state" / "vanna_simple_post4_gas_comparison.png"
generate_gemini_image(prompt, str(output_path), project="vanna-mcp", location="global", model="gemini-3.1-flash-image")
print("Post 4 generated cleanly without shell interpolation.")
