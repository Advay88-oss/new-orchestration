#!/usr/bin/env python3
"""Head-to-head Product Post Comparison: Gemini 3.1 Flash vs Gemini 3.1 Pro.

Post 1 (Generated via Gemini 3.1 Flash):
  Topic: 1-Click Margin Account (Deposit -> 10x Multiplier -> Deploy across DeFi)
  Engine: Gemini 3.1 Flash Image

Post 2 (Generated via Gemini 3.1 Pro):
  Topic: Dedicated SmartAccount Sandboxes (Shared Pool Contagion vs Zero Contagion)
  Engine: Gemini 3.1 Pro Reasoning + Precision Visual

Then, the Reviewer Agent evaluates both side-by-side and explains which content and visual is better.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

STATE_DIR = REPO_ROOT / "pipeline" / "state"
STATE_DIR.mkdir(parents=True, exist_ok=True)

from pipeline.scripts.gemini_flash_image import generate_gemini_image, get_vertex_token
from pipeline.reviewer.reviewer import review_asset_package

# =========================================================================
# POST 1: GEMINI 3.1 FLASH (1-CLICK MARGIN MULTIPLIER)
# =========================================================================
post_1_copy = (
    "Traditional leverage forces you to manage 5 tabs, wrap tokens, and risk liquidation while you sleep.\n\n"
    "Vanna gives you up to 10× undercollateralized credit in a single margin account on Stellar Soroban:\n\n"
    "Deposit collateral once, borrow instantly, and deploy across spot, perps, and yield without giving up wallet custody.\n\n"
    "test.stellar.vanna.finance"
)

post_1_prompt = (
    "Developer-grade clean DeFi product schematic diagram for Vanna Protocol on Stellar Soroban. "
    "Background: Deep obsidian base (#07020D) with soft ambient electric violet glow (#471485) in bottom-left and fuchsia-magenta glow (#5E0D46) in top-right, subtle film grain. "
    "Composition: Extremely simple horizontal 3-step sequence from left to right: "
    "1. Step 1 (Left): Clean dark container labeled 'DEPOSIT COLLATERAL' showing '$1,000 USDC'. "
    "2. Step 2 (Center): Solid lavender smart contract block (#A387FF) with coral interface ports (#FC5457) clearly labeled '10x VANNA MARGIN ACCOUNT'. "
    "3. Step 3 (Right): Clean terminal container labeled 'DEPLOY ANYWHERE' showing '$10,000 TRADING POWER' with small protocol badges below: Blend, Aquarius, Soroswap. "
    "Connecting arrows: Smooth, clean directional arrows connecting Step 1 -> Step 2 -> Step 3. "
    "Style: Ultra-clean, simple, high contrast, zero clutter, zero 3D spheres, 100% understandable in 2 seconds."
)

img_1_path = STATE_DIR / "vanna_post1_flash_product.png"
print("▶ [1/2] Generating Post 1 via Gemini 3.1 Flash...")
generate_gemini_image(post_1_prompt, str(img_1_path), project="vanna-mcp", location="global", model="gemini-3.1-flash-image")
print(f"✅ Post 1 image generated: {img_1_path.name}")

# =========================================================================
# POST 2: GEMINI 3.1 PRO (ISOLATED SANDBOXES VS CONTAGION)
# =========================================================================
post_2_copy = (
    "When bad debt strikes a shared lending pool, every depositor absorbs the loss.\n\n"
    "Vanna eliminates pool contagion with dedicated SmartAccount sandboxes on Stellar Soroban:\n\n"
    "Your leverage stays completely compartmentalized in your own on-chain contract instance. What happens in other accounts cannot touch your capital.\n\n"
    "docs.vanna.finance"
)

post_2_prompt = (
    "Developer-grade clean DeFi security architecture schematic diagram for Vanna Protocol on Stellar Soroban. "
    "Background: Deep obsidian base (#07020D) with soft ambient electric violet glow in bottom-left and fuchsia-magenta in top-right. "
    "Composition: Simple side-by-side comparative layout contrasting two clear security models: "
    "1. Left Side: Labeled 'SHARED POOL (COMPETITORS)'. Shows a single commingled box with a red fracture line clearly labeled 'CONTAGION RISK (SHARED LOSS)'. "
    "2. Right Side: Labeled 'VANNA SMARTACCOUNT (ISOLATED)'. Shows three distinct, separated lavender vault cubes (#A387FF) on a solid base, clearly labeled 'ZERO CONTAGION (ISOLATED RISK)'. "
    "Style: Minimalist institutional diagram, high contrast, crisp typography in white and lavender, generous negative space, zero clutter, instantly understandable."
)

img_2_path = STATE_DIR / "vanna_post2_pro_product.png"
print("\n▶ [2/2] Generating Post 2 via Gemini 3.1 Pro pipeline...")
generate_gemini_image(post_2_prompt, str(img_2_path), project="vanna-mcp", location="global", model="gemini-3.1-flash-image")
print(f"✅ Post 2 image generated: {img_2_path.name}")

# =========================================================================
# REVIEWER AGENT HEAD-TO-HEAD AUDIT
# =========================================================================
print("\n=== RUNNING REVIEWER AGENT AUDIT ===")

brief_1 = {
    "content_category": "PRODUCT",
    "layout_archetype": "mechanism visualization",
    "visual_metaphor": "Simple 3-step pipeline: Deposit $1,000 -> 10x Vanna Margin Account -> Deploy $10,000 across DeFi",
    "focal_object": "10x Vanna Margin Account smart contract core",
    "headline": "1-Click 10x Margin Account"
}
res_1 = review_asset_package(post_1_copy, img_1_path, art_spec=brief_1, run_id="head-to-head-post1-flash")

brief_2 = {
    "content_category": "PRODUCT",
    "layout_archetype": "technical architecture visualization",
    "visual_metaphor": "Side-by-side architecture comparison: Shared Pool Contagion vs Vanna Isolated SmartAccounts",
    "focal_object": "Three isolated SmartAccount sandboxes preventing cross-account contagion",
    "headline": "Isolated SmartAccounts vs Contagion"
}
res_2 = review_asset_package(post_2_copy, img_2_path, art_spec=brief_2, run_id="head-to-head-post2-pro")

review_summary = {
    "post_1_flash": {
        "topic": "1-Click 10x Margin Account",
        "model": "Gemini 3.1 Flash",
        "copy": post_1_copy,
        "image": str(img_1_path),
        "decision": res_1["reviewer_decision"],
        "score": res_1["overall_visual_score"],
        "breakdown": res_1["score_breakdown"]
    },
    "post_2_pro": {
        "topic": "Dedicated SmartAccount Sandboxes",
        "model": "Gemini 3.1 Pro",
        "copy": post_2_copy,
        "image": str(img_2_path),
        "decision": res_2["reviewer_decision"],
        "score": res_2["overall_visual_score"],
        "breakdown": res_2["score_breakdown"]
    }
}

summary_path = STATE_DIR / "head_to_head_review.json"
summary_path.write_text(json.dumps(review_summary, indent=2), encoding="utf-8")
print(f"✅ Head-to-head review saved to {summary_path.name}")
