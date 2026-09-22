#!/usr/bin/env python3
"""Generates 2 Creative-First Institutional Posts using Gemini 3.1 Pro standards.

Enforces:
  1. Creative visual metaphor first (not text-heavy; 100% textless abstract geometric art).
  2. Brand palette: Obsidian #07020D with #471485 violet (bottom-left) and #5E0D46 fuchsia (top-right).
  3. No generic AI slop (no floating concentric rings, no stock HUDs).
  4. Humanized copy following the 34-point Humanizer guidelines.
  5. Full verification through the pre-delivery Reviewer Agent.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

STATE_DIR = REPO_ROOT / "pipeline" / "state"
STATE_DIR.mkdir(parents=True, exist_ok=True)

from pipeline.scripts.gemini_flash_image import generate_gemini_image
from pipeline.reviewer.reviewer import review_asset_package

posts = [
    {
        "id": "creative_post1_deflection",
        "title": "Sub-Second Liquidation Deflection",
        "copy": (
            "In an EVM liquidation cascade, gas spikes to 150 gwei while your rebalance transaction sits pending in the mempool.\n\n"
            "Vanna eliminates front-running liquidations with sub-second off-chain telemetry on Stellar Soroban:\n\n"
            "Mercury streams ledger events in ~320ms. When a position approaches 1.25× Net Health Factor, our Risk Guardian executes an automated rebalance inside your SmartAccount sandbox.\n\n"
            "Execution gas is fixed at 0.00014 XLM. No mempool bidding wars. No liquidation fee penalty.\n\n"
            "test.stellar.vanna.finance"
        ),
        "prompt": (
            "High-end, institutional creative visual metaphor for financial deflection and risk containment. "
            "Canvas: Deep obsidian void (#07020D) with soft ambient electric royal violet bloom (#471485) emerging from bottom-left and warm fuchsia-magenta glow (#5E0D46) emerging from top-right, subtle analog film grain texture. "
            "Subject: A sleek, precision-milled matte black architectural monolith with glowing lavender (#A387FF) and electric cyan (#22D3C4) refractive internal channels. "
            "Visual action: An incoming sharp trajectory beam of light strikes a magnetic deflection barrier and gracefully curves away into a stable, illuminated parallel orbit, avoiding a subtle dark crimson risk boundary. "
            "Composition: Minimalist, asymmetric composition with generous negative space, sophisticated studio rim lighting, tactile glass and obsidian materials, cinematic depth of field. "
            "Strict negative constraints: Absolutely NO text, NO numbers, NO letters, NO words, NO floating holographic HUDs, NO generic glowing spheres, NO concentric rings, NO stock crypto icons."
        ),
        "image_file": "vanna_creative_post1_deflection.png",
        "brief": {
            "content_category": "PRODUCT",
            "layout_archetype": "visual metaphor",
            "visual_metaphor": "Precision architectural deflection barrier redirecting an incoming trajectory beam into a secure parallel orbit",
            "focal_object": "Monolithic obsidian deflection prism with cyan and lavender refractive channels",
            "headline": "Sub-Second Risk Deflection"
        }
    },
    {
        "id": "creative_post2_compartment",
        "title": "Compartmentalized SmartAccount Sandboxes",
        "copy": (
            "When an exotic asset depegs in a shared lending pool, every depositor absorbs a haircut—even if you only supplied USDC.\n\n"
            "Vanna isolates risk at the contract instance level with dedicated SmartAccount sandboxes on Stellar Soroban:\n\n"
            "LPs deposit into core LendingPools, but borrowers execute within isolated smart contract instances.\n\n"
            "If an unexpected deficit occurs in an account, it stays quarantined in that contract sandbox. It cannot drain other user accounts or compromise core pool reserves.\n\n"
            "docs.vanna.finance"
        ),
        "prompt": (
            "High-end, institutional creative visual metaphor for modular compartmentalization and zero contagion. "
            "Canvas: Deep obsidian void (#07020D) with soft ambient electric royal violet bloom (#471485) in bottom-left and warm fuchsia-magenta glow (#5E0D46) in top-right, subtle analog film grain texture. "
            "Subject: Three precision-crafted geometric glass and obsidian vault chambers arranged in an asymmetric architectural balance. "
            "Visual action: One chamber on the far edge securely seals a contained crimson-coral internal fracture within thick, flawless frosted-glass barrier walls. The central and foreground chambers remain pristine, illuminated with calm lavender and cyan light, completely untouched and isolated from the adjacent fracture. "
            "Composition: Elegant high-end industrial design, heavy solid materials, dramatic architectural studio lighting, sharp reflections on dark polished ground, generous negative space. "
            "Strict negative constraints: Absolutely NO text, NO typography, NO numbers, NO labels, NO floating spheres, NO concentric circles, NO stock blockchain icons."
        ),
        "image_file": "vanna_creative_post2_compartment.png",
        "brief": {
            "content_category": "PRODUCT",
            "layout_archetype": "visual metaphor",
            "visual_metaphor": "Three monolithic glass-and-obsidian chambers where one safely contains a sealed crimson fracture while adjacent chambers remain completely pristine",
            "focal_object": "Architectural array of isolated modular containment chambers",
            "headline": "Compartmentalized Solvency Sandboxes"
        }
    }
]

def main():
    results = []
    for p in posts:
        img_path = STATE_DIR / p["image_file"]
        print(f"\n▶ Generating Creative Visual for {p['title']}...")
        generate_gemini_image(p["prompt"], str(img_path), project="vanna-mcp", location="global", model="gemini-3.1-flash-image")
        print(f"✅ Image generated: {img_path.name}")

        print("▶ Running Pre-Delivery Reviewer Agent...")
        review = review_asset_package(p["copy"], img_path, art_spec=p["brief"], run_id=f"audit-{p['id']}")
        print(f"   Review Decision: {review['reviewer_decision']}")
        print(f"   Overall Score:   {review['overall_visual_score']}/100")
        print(f"   Visual Score:    {review.get('visual_score', 0)}/100")
        print(f"   Brand Score:     {review.get('brand_score', 0)}/100")
        print(f"   Content Score:   {review.get('content_score', 0)}/100")
        print(f"   Failures:        {review.get('critical_failures', [])}")

        results.append({
            "id": p["id"],
            "title": p["title"],
            "copy": p["copy"],
            "image_file": p["image_file"],
            "review": review
        })

    out_file = STATE_DIR / "creative_posts_audit.json"
    out_file.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"\n✅ All creative posts generated and audited: {out_file.name}")

if __name__ == "__main__":
    main()
