#!/usr/bin/env python3
"""Generates 5 distinct demo visuals using Gemini 3.1 Flash Image (Nano Banana).

Demonstrates the new Creative Director pipeline:
  1. 10-Question Creative Reasoning
  2. Multi-Concept Exploration & Selection
  3. Nano Banana Creative Reasoning Packet Prompting
  4. Live generation via gemini-3.1-flash-image on Google Cloud Model Garden
  5. Brand finish compositing (Official Vanna Badge + Typography)
"""

import json
import os
import shutil
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

STATE_DIR = REPO_ROOT / "pipeline" / "state"
PUBLIC_DIR = REPO_ROOT / "hermes-mission" / "public"
STATE_DIR.mkdir(parents=True, exist_ok=True)
PUBLIC_DIR.mkdir(parents=True, exist_ok=True)

from pipeline.gtm_creative.visual_creative_director import VisualCreativeDirector
from pipeline.gtm_creative.visual_pipeline_engine import VisualPipelineEngine
from pipeline.scripts.gemini_flash_image import generate_gemini_image

DEMO_BRIEFS = [
    {
        "id": "DEMO_01_TECH_ARCH",
        "title": "State Isolation & SmartAccount Sandboxes",
        "content_type": "technical_architecture",
        "directive": "Isolated Soroban SmartAccount contract sandboxes eliminating shared lending pool contagion",
        "audience": "A3 Soroban Protocol Builders & Institutional Architects",
        "claim": "14 Dedicated Sandboxes · 0 Pooled Contagion"
    },
    {
        "id": "DEMO_02_PRODUCT_VALUE",
        "title": "Tactile 10x Margin Terminal",
        "content_type": "product_value_proposition",
        "directive": "Tactile decentralized terminal executing 10x composable margin into Blend b-token vaults in 1 click",
        "audience": "Active Margin Traders & Blend Depositors",
        "claim": "10x Margin Multiplier · 1-Click Execution"
    },
    {
        "id": "DEMO_03_MARKET_DATA",
        "title": "Sovereign Gas Fee Benchmark",
        "content_type": "market_data_insight",
        "directive": "Fixed 0.00014 XLM gas fee benchmark on Soroban vs EVM priority auction volatility spikes",
        "audience": "Quantitative Arbitrageurs & High-Frequency Traders",
        "claim": "0.00014 XLM Fixed Gas · Zero Priority Spikes"
    },
    {
        "id": "DEMO_04_RISK_SECURITY",
        "title": "1.10x Solvency Defense Horizon",
        "content_type": "risk_security_concept",
        "directive": "Deterministic 1.10x health factor protective floor deflecting liquidation cascades before 100% wipeouts",
        "audience": "DeFi Allocators & Risk-Averse Yield Seekers",
        "claim": "1.10x Health Factor Floor · ~320ms Mercury Telemetry"
    },
    {
        "id": "DEMO_05_ECOSYSTEM_INTEG",
        "title": "Blend & Soroswap Liquidity Confluence",
        "content_type": "ecosystem_integration",
        "directive": "Seamless cross-protocol liquidity routing uniting Vanna margin with Blend Protocol and Soroswap AMM",
        "audience": "Stellar Ecosystem Developers & LPs",
        "claim": "$148M Blend Liquidity · Soroswap AMM Swaps"
    }
]

def main():
    print("=" * 80)
    print("🎨 GENERATING 5 DEMO VISUALS USING GEMINI 3.1 FLASH IMAGE (NANO BANANA)")
    print("=" * 80)

    director = VisualCreativeDirector()
    engine = VisualPipelineEngine()
    
    outputs = []
    
    for idx, b in enumerate(DEMO_BRIEFS):
        print(f"\n[{idx+1}/5] DIRECTING & GENERATING: {b['id']} ({b['content_type']})")
        print(f"     Title: {b['title']}")
        print(f"     Directive: \"{b['directive']}\"")
        
        # 1. Creative Director Reasoning & Concept Selection
        dossier = director.direct_visual_asset(
            brief_title=b["title"],
            content_type=b["content_type"],
            directive=b["directive"],
            audience=b["audience"],
            key_claim=b["claim"],
            recent_fingerprints=[]
        )
        
        winner = dossier["selected_concept"]
        nano_packet = dossier["nano_banana_packet"]
        fp = dossier["fingerprint"]
        
        print(f"\n   📝 Selected Concept: \"{winner['concept_title']}\"")
        print(f"   💡 Visual Metaphor: {winner['visual_metaphor']}")
        print(f"   🏛️ Aesthetic Style: {winner['treatment_style']}")
        
        raw_png = STATE_DIR / f"{b['id']}_raw.png"
        final_state_png = STATE_DIR / f"{b['id']}_nano_banana.png"
        final_public_png = PUBLIC_DIR / f"{b['id']}_nano_banana.png"
        
        # 2. Call Nano Banana (gemini-3.1-flash-image) with the Reasoning Packet Prompt
        print(f"\n   ▶ Invoking Model Garden gemini-3.1-flash-image...")
        generate_gemini_image(
            prompt=nano_packet["image_model_prompt"],
            output_path=raw_png,
            project="vanna-mcp",
            location="global",
            model="gemini-3.1-flash-image"
        )
        
        # 3. Composite Brand Finish (Vanna Badge + Clean Typography)
        print(f"   ▶ Applying Vanna Brand Badge and Typography Finish...")
        engine._composite_brand_finish(
            raw_path=raw_png,
            out_path=final_state_png,
            concept=winner,
            key_claim=b["claim"],
            content_type=b["content_type"]
        )
        
        # Sync to public directory
        if PUBLIC_DIR.exists():
            shutil.copy(str(final_state_png), str(final_public_png))
            
        print(f"   ✅ Finished Visual: {final_public_png.name} ({final_public_png.stat().st_size:,} bytes)")
        
        outputs.append({
            "brief": b,
            "winner": winner,
            "nano_packet": nano_packet,
            "file_path": str(final_public_png),
            "file_size": final_public_png.stat().st_size
        })

    print("\n" + "=" * 80)
    print("🎉 ALL 5 NANO BANANA DEMOS SUCCESSFULLY GENERATED!")
    print("=" * 80)
    for o in outputs:
        print(f"- {o['brief']['title']}: {o['file_path']} ({o['file_size']:,} bytes)")

if __name__ == "__main__":
    main()
