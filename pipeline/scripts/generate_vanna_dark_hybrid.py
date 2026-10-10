#!/usr/bin/env python3
"""Generates Vanna Dark Hybrid Post images using PIL and Vanna Visual Design System."""

import os
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

REPO_ROOT = Path(__file__).resolve().parents[2]
ARTIFACT_DIR = Path(r"C:\Users\Advay Anand\.gemini\antigravity-ide\brain\80729ef2-1bee-4fb4-a4fb-6c2dd56f63e3")
PUBLIC_DIR = REPO_ROOT / "hermes-mission" / "public"
PUBLIC_DIR.mkdir(parents=True, exist_ok=True)

def generate_vanna_hybrid_image(title: str, metric: str, subtext: str, footer: str, filename: str):
    # 1. Canvas 1200x1200 with Void Dark background (#090A0F)
    img = Image.new("RGB", (1200, 1200), (9, 10, 15))
    draw = ImageDraw.Draw(img)

    # 2. Dual Vanna Ambient Blooms (#471485 & #5E0D46)
    # Deep Purple bloom top-center
    for r in range(550, 0, -15):
        draw.ellipse([(600 - r, 320 - r), (600 + r, 320 + r)], fill=(71, 20, 133))

    # Fuchsia/Magenta bloom bottom-right
    for r in range(450, 0, -20):
        draw.ellipse([(1050 - r, 1050 - r), (1050 + r, 1050 + r)], fill=(94, 13, 70))

    # 3. Cybernetic / Stipple Halftone Matrix Grid Lines (Dark Engraving Pattern)
    for y in range(0, 1200, 36):
        draw.line([(0, y), (1200, y)], fill=(18, 22, 35), width=1)
    for x in range(0, 1200, 36):
        draw.line([(x, 0), (x, 1200)], fill=(18, 22, 35), width=1)

    # 4. Floating Obsidian Frosted Glass Rectangular Card (Centered)
    card_rect = [(160, 260), (1040, 940)]
    # Card background fill (Dark Glass)
    draw.rectangle(card_rect, fill=(15, 17, 26), outline=(56, 239, 125), width=3)
    # Inner subtle accent border
    draw.rectangle([(172, 272), (1028, 928)], outline=(71, 20, 133), width=2)

    # 5. Vanna Hybrid Typography
    try:
        font_title = ImageFont.truetype("arial.ttf", 36)
        font_metric = ImageFont.truetype("georgia.ttf", 84)
        font_sub = ImageFont.truetype("arial.ttf", 32)
        font_foot = ImageFont.truetype("arial.ttf", 26)
    except Exception:
        font_title = font_metric = font_sub = font_foot = ImageFont.load_default()

    # Draw Header
    draw.text((360, 350), title.upper(), fill=(148, 163, 184), font=font_title)
    # Draw High-Contrast Metric (Solvency Mint #38EF7D)
    draw.text((280, 480), metric, fill=(56, 239, 125), font=font_metric)
    # Draw Subtext
    draw.text((320, 680), subtext.upper(), fill=(226, 232, 240), font=font_sub)
    # Draw Footer
    draw.text((380, 810), footer.upper(), fill=(94, 163, 184), font=font_foot)

    # Save to public and artifact directories
    out_artifact = ARTIFACT_DIR / filename
    out_public = PUBLIC_DIR / filename
    img.save(out_artifact, quality=95)
    img.save(out_public, quality=95)
    print(f"✅ Generated {filename} successfully!")

def main():
    generate_vanna_hybrid_image(
        title="AUTONOMOUS YIELD",
        metric="$10,000,000",
        subtext="IN ROUTED LIQUIDITY DEPOSITS",
        footer="POWERED BY vanna + base",
        filename="vanna_dark_hybrid_post_1.png"
    )
    generate_vanna_hybrid_image(
        title="RISK & SOLVENCY ENGINE",
        metric="1.10x FLOOR",
        subtext="SUB-SECOND LIQUIDATION DEFLECTION",
        footer="POWERED BY VANNA SECURITY LAYER",
        filename="vanna_dark_hybrid_post_2.png"
    )
    generate_vanna_hybrid_image(
        title="ECOSYSTEM COMPOSABILITY",
        metric="vanna × Base",
        subtext="AUTONOMOUS MULTI-VENUE ROUTING",
        footer="INTEGRATED PROTOCOL SUITE",
        filename="vanna_dark_hybrid_post_3.png"
    )

if __name__ == "__main__":
    main()
