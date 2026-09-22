#!/usr/bin/env python3
"""Multi-Model Visual Generation Showcase for Vanna Protocol.

Generates 2 completely new Vanna topics using diverse models:
  Post A: "Delta-Neutral Basis Yield" -> Generated via Nano Banana (gemini-2.5-flash-image)
  Post B: "Polynomial RateModel vs Linear Slopes" -> Generated via Gemini 3.1 Flash Image
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

from pipeline.scripts.gemini_flash_image import generate_gemini_image
from pipeline.scripts.nano_banana import gen as generate_nano_banana
from pipeline.reviewer.reviewer import review_asset_package

# =========================================================================
# POST A: DELTA-NEUTRAL FUNDING ARBITRAGE (Nano Banana / gemini-2.5-flash-image)
# =========================================================================
post_a_copy = (
    "Chasing funding rates manually across fragmented CEXs leaves you exposed to execution slippage and liquidation wicks.\n\n"
    "Vanna executes automated delta-neutral basis farming from a single isolated margin account on Stellar Soroban:\n\n"
    "Long spot on Soroswap, hedge short exposure, and harvest continuous funding yield with zero directional market risk.\n\n"
    "test.stellar.vanna.finance"
)

post_a_prompt = (
    "Developer-grade DeFi quantitative trading schematic diagram for Vanna Protocol. "
    "Background: Deep obsidian base (#07020D) with subtle ambient electric violet glow (#471485) in bottom-left and fuchsia-magenta glow (#5E0D46) in top-right, subtle film grain. "
    "Composition: Horizontal delta-neutral basis arbitrage flow: "
    "1. Top leg: Long Spot Position (+1.0 Delta). "
    "2. Bottom leg: Short Hedge Position (-1.0 Delta). "
    "3. Center convergence: Labeled 'NET ZERO DELTA EXPOSURE', resolving into a steady horizontal profit stream labeled '18% APR FUNDING HARVEST (USDC)'. "
    "Style: Minimalist financial engineering blueprint, clean vector lines, high contrast, crisp typography in lavender and white, zero 3D spheres, zero clutter."
)

img_a_path = STATE_DIR / "vanna_nanobanana_delta_neutral.png"
print("▶ Generating Post A via Nano Banana (gemini-2.5-flash-image)...")
generate_nano_banana(post_a_prompt, str(img_a_path))
print(f"✅ Post A image saved to: {img_a_path.name}")

# =========================================================================
# POST B: POLYNOMIAL RATEMODEL (Gemini 3.1 Flash Image)
# =========================================================================
post_b_copy = (
    "Traditional lending protocols use rigid linear interest curves that fail during sudden liquidity crunches.\n\n"
    "Vanna's RateModel on Stellar Soroban implements a continuous polynomial function:\n\n"
    "Borrow rates adjust dynamically per second as pool utilization climbs—protecting lender liquidity and penalizing over-leverage before pools exhaust.\n\n"
    "docs.vanna.finance"
)

post_b_prompt = (
    "Developer-grade DeFi interest rate dynamics schematic diagram for Vanna Protocol on Stellar Soroban. "
    "Background: Deep obsidian base (#07020D) with soft ambient electric violet glow in bottom-left and fuchsia-magenta in top-right. "
    "Composition: Comparative mathematical coordinate chart showing two contrasting borrow rate curves: "
    "1. Muted red dashed line: Labeled 'TRADITIONAL LINEAR KINK (AAVE MODEL)', showing flat response until sudden delayed spike. "
    "2. Glowing lavender solid curve: Labeled 'VANNA POLYNOMIAL RATEMODEL', showing smooth exponential rate acceleration across 0% to 100% pool utilization. "
    "X-axis: 'POOL UTILIZATION (0% TO 100%)'. Y-axis: 'BORROW APY'. "
    "Key callout box: 'DYNAMIC PER-SECOND REBALANCING'. "
    "Style: Quantitative financial engineering chart, Bloomberg terminal precision, crisp labels, razor-thin vector lines, zero AI stock art."
)

img_b_path = STATE_DIR / "vanna_gemini31_polynomial_ratemodel.png"
print("\n▶ Generating Post B via Gemini 3.1 Flash Image...")
generate_gemini_image(post_b_prompt, str(img_b_path), project="vanna-mcp", location="global", model="gemini-3.1-flash-image")
print(f"✅ Post B image saved to: {img_b_path.name}")

# =========================================================================
# REVIEWER AUDIT
# =========================================================================
print("\n=== RUNNING REVIEWER AGENT AUDIT ===")

brief_a = {
    "content_category": "PRODUCT",
    "layout_archetype": "mechanism visualization",
    "visual_metaphor": "Delta-neutral basis arbitrage: opposing long/short vectors resolving into zero delta net yield",
    "focal_object": "Net zero delta convergence producing funding yield",
    "headline": "Delta-Neutral Basis Farming"
}
res_a = review_asset_package(post_a_copy, img_a_path, art_spec=brief_a, run_id="multimodel-post-a-nanobanana")
print(f"Post A (Nano Banana) Review: {res_a['reviewer_decision']} | Score: {res_a['overall_visual_score']}")

brief_b = {
    "content_category": "PRODUCT",
    "layout_archetype": "asymmetric technical diagram",
    "visual_metaphor": "Comparative rate model chart: Vanna continuous polynomial curve vs rigid linear kinked slope",
    "focal_object": "Continuous polynomial rate curve accelerating dynamically with pool utilization",
    "headline": "Polynomial RateModel Dynamics"
}
res_b = review_asset_package(post_b_copy, img_b_path, art_spec=brief_b, run_id="multimodel-post-b-gemini31")
print(f"Post B (Gemini 3.1) Review: {res_b['reviewer_decision']} | Score: {res_b['overall_visual_score']}")
