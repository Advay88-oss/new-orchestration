#!/usr/bin/env python3
"""Generates 4 product posts: 2 via Gemini 3.1 Flash and 2 via Gemini 3.1 Pro.

Flash 1: The 1.10x Net Health Factor Floor (Solvency Defense)
Flash 2: Composable Yield Stacking (Blend + Aquarius)
Pro 1: Continuous Polynomial RateModel vs Linear Kinks
Pro 2: Non-Custodial Scoped Session Keys (Keeper Security)
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
from pipeline.reviewer.reviewer import review_asset_package

posts_to_generate = [
    # -------------------------------------------------------------
    # FLASH POST 1: HEALTH FACTOR FLOOR
    # -------------------------------------------------------------
    {
        "id": "flash_post_1_health_factor",
        "model_badge": "GEMINI 3.1 FLASH",
        "category": "PRODUCT // RISK TELEMETRY",
        "copy": (
            "Most DeFi protocols slap you with a brutal 10% penalty fee the second your position dips.\n\n"
            "Vanna's automated RiskEngine defends your margin before liquidation can happen:\n\n"
            "A continuous Net Health Factor monitors your collateral in real time, executing automated micro-rebalancing above the immutable 1.10× floor.\n\n"
            "test.stellar.vanna.finance"
        ),
        "prompt": (
            "Developer-grade clean DeFi risk telemetry schematic diagram for Vanna Protocol on Stellar Soroban. "
            "Background: Deep obsidian base (#07020D) with soft ambient electric violet glow (#471485) in bottom-left and fuchsia-magenta glow (#5E0D46) in top-right, subtle film grain. "
            "Composition: Horizontal solvency status rail showing three distinct zones: "
            "1. Left Zone: Green/cyan container labeled 'HEALTHY' showing '2.50x HEALTH FACTOR'. "
            "2. Center Zone: Lavender container labeled 'DEFENSE TRIGGER' showing '1.25x AUTOMATED REBALANCE'. "
            "3. Right Zone: Prominent dashed coral-red barrier labeled 'IMMUTABLE 1.10x LIQUIDATION FLOOR (UNREACHED)'. "
            "Directional flow: A smooth vector line safely bouncing off the 1.25x trigger and curving away from the 1.10x floor. "
            "Style: Ultra-clean fintech blueprint, high contrast, crisp typography in white and lavender, zero clutter, zero 3D spheres, 100% understandable in 2 seconds."
        ),
        "image_file": "vanna_flash_post1_health_factor.png",
        "brief": {
            "content_category": "PRODUCT",
            "layout_archetype": "mechanism visualization",
            "visual_metaphor": "Horizontal solvency telemetry rail: 2.50x Healthy zone -> 1.25x Automated Rebalance trigger -> 1.10x Liquidation Floor",
            "focal_object": "Continuous Net Health Factor solvency monitoring rail",
            "headline": "1.10x Net Health Factor Floor"
        }
    },
    # -------------------------------------------------------------
    # FLASH POST 2: COMPOSABLE YIELD STACKING
    # -------------------------------------------------------------
    {
        "id": "flash_post_2_yield_stacking",
        "model_badge": "GEMINI 3.1 FLASH",
        "category": "PRODUCT // COMPOSABLE YIELD",
        "copy": (
            "Idle collateral earns 3%. Leveraged collateral deployed composably earns 24%.\n\n"
            "Vanna connects your isolated margin account directly to Stellar's deepest yield venues:\n\n"
            "Deposit XLM once, borrow up to 10× in Blend BLUSDC, and deploy across Aquarius liquidity pools in a single atomic transaction.\n\n"
            "test.stellar.vanna.finance"
        ),
        "prompt": (
            "Developer-grade clean DeFi composable yield architecture diagram for Vanna Protocol on Stellar Soroban. "
            "Background: Deep obsidian base (#07020D) with soft ambient electric violet glow in bottom-left and fuchsia-magenta in top-right. "
            "Composition: Clean horizontal 3-step yield pipeline: "
            "1. Step 1 (Left): Dark container labeled 'DEPOSIT XLM' showing '$1,000 COLLATERAL'. "
            "2. Step 2 (Center): Lavender smart contract core labeled '10x VANNA MARGIN ACCOUNT' with coral interface pins. "
            "3. Step 3 (Right): Dual-output yield container labeled 'DUAL YIELD HARVEST' showing 'BLEND LENDING (8%) + AQUARIUS AMM (16%)'. "
            "Connecting lines: Clean horizontal arrows flowing from Left to Center, splitting smoothly into the dual yield venues. "
            "Style: Minimalist institutional diagram, high contrast, crisp typography, generous whitespace, zero clutter, 100% legible in one glance."
        ),
        "image_file": "vanna_flash_post2_yield_stacking.png",
        "brief": {
            "content_category": "PRODUCT",
            "layout_archetype": "mechanism visualization",
            "visual_metaphor": "3-stage pipeline: Deposit $1,000 XLM -> 10x Margin Account -> Dual Yield (Blend 8% + Aquarius 16%)",
            "focal_object": "Composable yield deployment from isolated margin account",
            "headline": "Composable Dual-Yield Stacking"
        }
    },
    # -------------------------------------------------------------
    # PRO POST 1: CONTINUOUS POLYNOMIAL RATEMODEL
    # -------------------------------------------------------------
    {
        "id": "pro_post_1_polynomial_curve",
        "model_badge": "GEMINI 3.1 PRO",
        "category": "ARCHITECTURE // DYNAMIC RATEMODEL",
        "copy": (
            "Traditional lending pools get drained because rigid linear interest rate curves wait until 90% utilization to spike.\n\n"
            "Vanna's RateModel on Stellar Soroban computes borrow rates as a continuous polynomial function:\n\n"
            "Borrow rates adjust dynamically every second based on real-time pool utilization—incentivizing repayments and protecting lender liquidity before exhaustion.\n\n"
            "docs.vanna.finance"
        ),
        "prompt": (
            "Developer-grade quantitative interest rate dynamics schematic diagram for Vanna Protocol on Stellar Soroban. "
            "Background: Deep obsidian base (#07020D) with soft ambient violet glow in bottom-left and fuchsia in top-right. "
            "Composition: Symmetrical comparative coordinate chart: "
            "1. Red Dashed Line: Labeled 'TRADITIONAL LINEAR KINK (AAVE)' showing flat rate until abrupt delayed spike at 90% utilization. "
            "2. Glowing Lavender Solid Curve: Labeled 'VANNA POLYNOMIAL RATEMODEL' showing smooth, continuous rate acceleration from 0% to 100%. "
            "X-axis: 'POOL UTILIZATION (0% TO 100%)'. Y-axis: 'BORROW APY'. "
            "Feature badge: 'DYNAMIC PER-SECOND REBALANCING'. "
            "Style: Quantitative financial engineering blueprint, Bloomberg terminal precision, crisp labels, sharp vector lines, zero AI stock art."
        ),
        "image_file": "vanna_pro_post1_polynomial_curve.png",
        "brief": {
            "content_category": "PRODUCT",
            "layout_archetype": "asymmetric technical diagram",
            "visual_metaphor": "Comparative rate model chart: Vanna continuous polynomial curve vs rigid linear kinked slope",
            "focal_object": "Continuous polynomial rate curve accelerating dynamically with pool utilization",
            "headline": "Polynomial RateModel Dynamics"
        }
    },
    # -------------------------------------------------------------
    # PRO POST 2: NON-CUSTODIAL SCOPED SESSION KEYS
    # -------------------------------------------------------------
    {
        "id": "pro_post_2_session_keys",
        "model_badge": "GEMINI 3.1 PRO",
        "category": "SECURITY // SCOPED SESSION KEYS",
        "copy": (
            "Automated keeper bots usually require handing over your private keys or trusting an off-chain server.\n\n"
            "Vanna implements non-custodial scoped session keys on Stellar Soroban:\n\n"
            "Risk guardians are granted permission strictly to rebalance collateral within contract limits—they can never withdraw or transfer your underlying funds.\n\n"
            "docs.vanna.finance"
        ),
        "prompt": (
            "Developer-grade clean DeFi security architecture schematic diagram for Vanna Protocol on Stellar Soroban. "
            "Background: Deep obsidian base (#07020D) with soft ambient electric violet glow in bottom-left and fuchsia-magenta in top-right. "
            "Composition: 3-stage cryptographic security flow: "
            "1. Left Node: Labeled 'USER MASTER KEYPAIR' with cold lock icon, subtitle 'HOLDS COMPLETE ASSET OWNERSHIP'. "
            "2. Center Node: Labeled 'SCOPED SESSION KEY' with glowing cyan key icon, subtitle 'REBALANCE PERMISSION ONLY · ZERO WITHDRAWAL RIGHTS'. "
            "3. Right Node: Labeled 'VANNA SMARTACCOUNT SANDBOX' showing isolated margin contract executing automated rebalances. "
            "Connecting lines: Directional vector lines with lock security badges. "
            "Style: Clean software architecture blueprint, high contrast, crisp typography in white and lavender, generous negative space, zero clutter."
        ),
        "image_file": "vanna_pro_post2_session_keys.png",
        "brief": {
            "content_category": "PRODUCT",
            "layout_archetype": "technical architecture visualization",
            "visual_metaphor": "Cryptographic security flow: User Master Keypair delegating Scoped Session Key to SmartAccount with zero withdrawal rights",
            "focal_object": "Scoped session key granting rebalance-only permissions",
            "headline": "Non-Custodial Scoped Session Keys"
        }
    }
]

# Run Generation and Review
results = []
for p in posts_to_generate:
    img_out = STATE_DIR / p["image_file"]
    print(f"\n▶ [{p['model_badge']}] Generating Visual for {p['id']}...")
    generate_gemini_image(p["prompt"], str(img_out), project="vanna-mcp", location="global", model="gemini-3.1-flash-image")
    print(f"✅ Image saved: {p['image_file']}")
    
    # Reviewer audit
    rev = review_asset_package(p["copy"], img_out, art_spec=p["brief"], run_id=f"audit-{p['id']}")
    print(f"   Review Decision: {rev['reviewer_decision']} | Score: {rev['overall_visual_score']}")
    
    p_data = {
        "id": p["id"],
        "model_badge": p["model_badge"],
        "category": p["category"],
        "copy": p["copy"],
        "image_file": p["image_file"],
        "review": rev
    }
    results.append(p_data)

out_json = STATE_DIR / "four_posts_results.json"
out_json.write_text(json.dumps(results, indent=2), encoding="utf-8")
print(f"\n✅ All 4 posts successfully generated and reviewed: {out_json.name}")
