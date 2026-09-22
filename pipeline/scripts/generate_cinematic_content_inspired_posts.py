#!/usr/bin/env python3
"""Generates 2 Cinematic, Content-Inspired Visuals for Vanna Protocol.

Directly inspired by the visual language of vanna_editorial_1_to_10_expansion.png:
  - Deep obsidian void (#07020D) with 35mm analog film grain texture.
  - Dual volumetric ambient blooms: electric royal violet (#471485) at bottom-left, fuchsia-magenta (#5E0D46) at top-right.
  - Razor-sharp, ultra-thin geometric vector lines in luminescent lavender and cyan.
  - Vast, confident negative space and quiet architectural authority.
  - Zero text clutter, zero AI badges, zero stock spheres with concentric rings.
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
        "id": "cinematic_post1_subsecond_stream",
        "title": "Sub-Second Liquidation Deflection",
        "copy": (
            "In an EVM liquidation cascade, gas spikes to 150 gwei while your rebalance transaction sits pending in the mempool.\n\n"
            "Vanna eliminates front-running liquidations with sub-second off-chain telemetry on Stellar Soroban:\n\n"
            "Mercury streams ledger events in ~320ms. When a position approaches 1.25× Net Health Factor, our Risk Guardian executes an automated rebalance inside your SmartAccount sandbox.\n\n"
            "Execution gas is fixed at 0.00014 XLM. No mempool bidding wars. No liquidation fee penalty.\n\n"
            "test.stellar.vanna.finance"
        ),
        "prompt": (
            "Cinematic, ultra-minimalist institutional visual diagram inspired by frontier AI research and advanced DeFi architecture. "
            "Backdrop: Deep textured obsidian void (#07020D) with tactile 35mm analog film grain, illuminated diagonally by an atmospheric electric violet wash (#471485) in the bottom-left and a subtle warm fuchsia bloom (#5E0D46) in the upper-right corner. "
            "Subject & Visual Flow: Flowing horizontally across expansive negative space, a razor-thin, luminous vector beam (in soft lavender #A387FF and pure white) represents an incoming telemetry event stream. "
            "The stream encounters an exquisite, ultra-delicate crystalline threshold lens. At the exact inflection point, the path gracefully refracts and bifurcates into an upward-curving parabolic arc of electric cyan (#22D3C4), settling into a calm, perfectly stable horizontal trajectory. "
            "Below the deflection point, a faint, dotted crimson vector line marks an avoided lower hazard boundary that remains completely untouched. "
            "Details: Decorated with microscopic, razor-sharp telemetry tick marks, delicate linear brackets, and tiny circular terminal nodes. Vast negative space, supreme restraint, zero text, zero typography, zero labels, zero generic floating spheres."
        ),
        "image_file": "vanna_cinematic_post1_subsecond.png",
        "brief": {
            "content_category": "PRODUCT",
            "layout_archetype": "visual metaphor",
            "visual_metaphor": "Horizontal telemetry beam refracting through a crystalline threshold lens and arcing into a stable cyan orbit away from an avoided hazard boundary",
            "focal_object": "Sub-second deflection lens and ascending parabolic vector trajectory",
            "headline": "Sub-Second Liquidation Deflection"
        }
    },
    {
        "id": "cinematic_post2_sandbox_containment",
        "title": "Compartmentalized SmartAccount Sandboxes",
        "copy": (
            "When an exotic asset depegs in a shared lending pool, every depositor absorbs a haircut—even if you only supplied USDC.\n\n"
            "Vanna isolates risk at the contract instance level with dedicated SmartAccount sandboxes on Stellar Soroban:\n\n"
            "LPs deposit into core LendingPools, but borrowers execute within isolated smart contract instances.\n\n"
            "If an unexpected deficit occurs in an account, it stays quarantined in that contract sandbox. It cannot drain other user accounts or compromise core pool reserves.\n\n"
            "docs.vanna.finance"
        ),
        "prompt": (
            "Cinematic, ultra-minimalist institutional architecture visual inspired by frontier system topology and advanced cryptographic security. "
            "Backdrop: Deep textured obsidian void (#07020D) with fine 35mm film grain, framed by soft ambient electric violet glow (#471485) in the bottom-left and a rich fuchsia-magenta atmospheric wash (#5E0D46) in the upper-right. "
            "Subject: An ethereal topological system layout suspended in vast dark space. A continuous, horizontal baseline axis of pure white/lavender light runs across the top, representing the core liquidity reserve. "
            "Suspended beneath the axis are three distinct, isolated wireframe modular chambers rendered with razor-thin vector lines: "
            "1. The first two chambers are completely pristine, emitting a serene, stable ambient glow in calm lavender (#A387FF) and mint-cyan (#22D3C4), completely tranquil and unaffected. "
            "2. The third chamber securely quarantines a sharp, internal geometric fracture glowing in intense crimson-coral (#FC5457), entirely sealed within thick, double-layered frosted boundary planes. The fracture does not leak or touch the adjacent chambers or the core axis above. "
            "Details: Precision engineering aesthetics, micro-scale coordinate tick marks, delicate brackets, immense negative space, quiet authority, zero text, zero typography, zero words, zero stock icons."
        ),
        "image_file": "vanna_cinematic_post2_sandboxes.png",
        "brief": {
            "content_category": "PRODUCT",
            "layout_archetype": "visual metaphor",
            "visual_metaphor": "Three isolated wireframe modular chambers suspended beneath a core reserve axis, where one chamber strictly quarantines a crimson deficit fracture while adjacent chambers remain pristine in lavender and cyan",
            "focal_object": "Topological array of isolated containment chambers",
            "headline": "Compartmentalized Solvency Sandboxes"
        }
    }
]

def main():
    results = []
    for p in posts:
        img_path = STATE_DIR / p["image_file"]
        print(f"\n▶ Generating Cinematic Visual for {p['title']}...")
        generate_gemini_image(p["prompt"], str(img_path), project="vanna-mcp", location="global", model="gemini-3.1-flash-image")
        print(f"✅ Generated: {img_path.name}")

        print("▶ Running Pre-Delivery Reviewer Agent...")
        review = review_asset_package(p["copy"], img_path, art_spec=p["brief"], run_id=f"audit-{p['id']}")
        print(f"   Review Decision: {review['reviewer_decision']}")
        print(f"   Overall Score:   {review['overall_visual_score']}/100")
        print(f"   Failures:        {review.get('critical_failures', [])}")

        results.append({
            "id": p["id"],
            "title": p["title"],
            "copy": p["copy"],
            "image_file": p["image_file"],
            "review": review
        })

    out_file = STATE_DIR / "cinematic_posts_audit.json"
    out_file.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"\n✅ All cinematic posts generated and audited: {out_file.name}")

if __name__ == "__main__":
    main()
