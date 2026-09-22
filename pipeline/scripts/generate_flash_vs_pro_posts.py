#!/usr/bin/env python3
"""Generates 2 posts comparing Gemini 3.1 Flash and Gemini 3.1 Pro in Vanna's Pipeline.

Post 1: The Two-Tier Intelligence Hierarchy (Flash Speed + Pro Reasoning)
Post 2: Latency vs Reasoning Depth (Benchmark Metrics & Architecture)
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

# =========================================================================
# POST 1: TWO-TIER MODEL HIERARCHY
# =========================================================================
post_1_copy = (
    "High-frequency DeFi protection cannot rely on a single AI model. "
    "Deep reasoning without speed causes liquidations; speed without mathematical rigor causes exploits.\n\n"
    "Vanna deploys a two-tier model hierarchy on Google Cloud:\n"
    "• Gemini 3.1 Pro: Deep quantitative solvency modeling and game-theoretic risk bounds.\n"
    "• Gemini 3.1 Flash: Real-time telemetry ingestion and sub-second defensive keeper triggers.\n\n"
    "Institutional credit defended by continuous AI consensus.\n\n"
    "docs.vanna.finance"
)

post_1_prompt = (
    "Developer-grade DeFi AI architecture schematic diagram for Vanna Protocol. "
    "Background: Deep obsidian base (#07020D) with subtle ambient electric violet glow (#471485) in bottom-left and fuchsia-magenta glow (#5E0D46) in top-right, subtle film grain. "
    "Composition: Vertical two-tier intelligence stack flowing into on-chain execution: "
    "1. Top Layer: Labeled 'GEMINI 3.1 PRO (FRONTIER REASONING CORE)'. Shows an illuminated deep violet hexagon with subtext 'QUANTITATIVE SOLVENCY PROOFS & POLYNOMIAL MODELING'. "
    "2. Downward Conduit: Labeled 'PRE-COMPUTED POLICY VECTOR'. "
    "3. Middle Layer: Labeled 'GEMINI 3.1 FLASH (SUB-SECOND EXECUTION SENTINEL)'. Shows a sharp glowing cyan processor block with subtext 'REAL-TIME TELEMETRY & SUB-300MS KEEPER TRIGGERS'. "
    "4. Bottom Target: Labeled 'VANNA ISOLATED SMARTACCOUNT (STELLAR SOROBAN)'. "
    "Style: High-contrast technical software blueprint, clean vector hairlines, crisp typography in white and lavender, zero 3D spheres, zero clutter."
)

img_1_path = STATE_DIR / "vanna_flash_vs_pro_tier_stack.png"
print("▶ Generating Post 1 visual via Gemini 3.1 Flash Image...")
generate_gemini_image(post_1_prompt, str(img_1_path), project="vanna-mcp", location="global", model="gemini-3.1-flash-image")
print(f"✅ Post 1 image saved to: {img_1_path.name}")

# =========================================================================
# POST 2: LATENCY VS REASONING DEPTH BENCHMARK
# =========================================================================
post_2_copy = (
    "When crypto crashes 15% in two minutes, model latency is the difference between solvency and bad debt.\n\n"
    "In Vanna's autonomous risk benchmarks:\n"
    "• Gemini 3.1 Flash: 320ms execution latency for real-time Soroban keeper triggers.\n"
    "• Gemini 3.1 Pro: Complex multi-variable solvency proofs and polynomial rate simulation.\n\n"
    "How Vanna balances sub-second liquidation defense with frontier quantitative reasoning.\n\n"
    "test.stellar.vanna.finance"
)

post_2_prompt = (
    "Developer-grade quantitative benchmark comparison diagram for Gemini 3.1 Flash vs Gemini 3.1 Pro in Vanna Protocol. "
    "Background: Deep obsidian base (#07020D) with soft ambient violet glow in bottom-left and fuchsia in top-right. "
    "Composition: Clean comparative benchmark metric card with two columns: "
    "1. Left Column: Labeled 'GEMINI 3.1 FLASH'. Metric: '320ms LATENCY'. Primary Strength: 'REAL-TIME TELEMETRY & RAPID KEEPER DISPATCH'. Role: 'HIGH-FREQUENCY GUARDIAN'. "
    "2. Right Column: Labeled 'GEMINI 3.1 PRO'. Metric: 'DEEP COGNITIVE DEPTH'. Primary Strength: 'POLYNOMIAL RATE & GAME-THEORETIC RISK PROOFS'. Role: 'QUANTITATIVE STRATEGIST'. "
    "Bottom banner: Labeled 'CONTINUOUS DUAL-MODEL CONSENSUS DEFENDING $10,000 MARGIN SANDBOXES'. "
    "Style: Minimalist financial analytics card, Bloomberg terminal precision, crisp labels, sharp vector lines, zero AI stock art."
)

img_2_path = STATE_DIR / "vanna_flash_vs_pro_benchmark.png"
print("\n▶ Generating Post 2 visual via Gemini 3.1 Flash Image...")
generate_gemini_image(post_2_prompt, str(img_2_path), project="vanna-mcp", location="global", model="gemini-3.1-flash-image")
print(f"✅ Post 2 image saved to: {img_2_path.name}")

# =========================================================================
# REVIEWER AUDIT
# =========================================================================
print("\n=== RUNNING REVIEWER AGENT AUDIT ===")

brief_1 = {
    "content_category": "PRODUCT",
    "layout_archetype": "technical architecture visualization",
    "visual_metaphor": "Two-tier AI intelligence stack: Gemini 3.1 Pro reasoning core feeding policies into Gemini 3.1 Flash real-time execution sentinel",
    "focal_object": "Two-tier model hierarchy defending Vanna SmartAccount",
    "headline": "Gemini 3.1 Flash vs Pro Hierarchy"
}
res_1 = review_asset_package(post_1_copy, img_1_path, art_spec=brief_1, run_id="review-flash-vs-pro-post1")
print(f"Post 1 Review: {res_1['reviewer_decision']} | Score: {res_1['overall_visual_score']}")

brief_2 = {
    "content_category": "PRODUCT",
    "layout_archetype": "asymmetric technical diagram",
    "visual_metaphor": "Benchmark comparison card contrasting Gemini 3.1 Flash 320ms latency against Gemini 3.1 Pro quantitative reasoning depth",
    "focal_object": "Comparative benchmark columns for Flash and Pro models",
    "headline": "Gemini 3.1 Latency vs Reasoning Benchmark"
}
res_2 = review_asset_package(post_2_copy, img_2_path, art_spec=brief_2, run_id="review-flash-vs-pro-post2")
print(f"Post 2 Review: {res_2['reviewer_decision']} | Score: {res_2['overall_visual_score']}")
