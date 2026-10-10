#!/usr/bin/env python3
"""Runner for Vanna Visual Pipeline Engine to generate Vanna Dark Hybrid Post designs."""

import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from pipeline.gtm_creative.visual_pipeline_engine import VisualPipelineEngine

def main():
    engine = VisualPipelineEngine()
    print("🚀 Running Vanna Visual Pipeline Engine with Vanna Dark Hybrid Theme...")

    # Post 1: Deposit / Yield Milestone
    res1 = engine.generate_art_directed_visual(
        brief_title="Vanna Yield Milestone $10M",
        content_type="market_data_insight",
        directive="Duo-Tone Vintage Engraving & Obsidian Card Hybrid Layout with $10,000,000 deposits",
        audience="DeFi LPs & Institutional Treasuries",
        key_claim="$10,000,000 in Autonomous Yield Routed",
        run_id="vanna_hybrid_post_1"
    )
    print(f"✅ Generated Post 1: {res1['filename']} ({res1['file_size_bytes']} bytes)")

    # Post 2: Solvency & Risk Containment
    res2 = engine.generate_art_directed_visual(
        brief_title="Vanna Sub-Second Solvency",
        content_type="risk_security_concept",
        directive="Woodcut Vault Engraving with Sub-Second Solvency text overlay",
        audience="Protocol Risk Officers & Auditors",
        key_claim="1.10x Liquidation Floor Enforced",
        run_id="vanna_hybrid_post_2"
    )
    print(f"✅ Generated Post 2: {res2['filename']} ({res2['file_size_bytes']} bytes)")

    # Post 3: Ecosystem Partnership
    res3 = engine.generate_art_directed_visual(
        brief_title="Vanna x Base Partnership",
        content_type="ecosystem_integration",
        directive="Concentric Rings Linocut Engraving with Vanna x Base Partnership Card",
        audience="Ecosystem Builders & Traders",
        key_claim="Vanna x Base Integration Live",
        run_id="vanna_hybrid_post_3"
    )
    print(f"✅ Generated Post 3: {res3['filename']} ({res3['file_size_bytes']} bytes)")

if __name__ == "__main__":
    main()
