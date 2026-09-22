#!/usr/bin/env python3
"""Generate all brand device deliverables, monochrome tests, banner, and in-feed 500px exports."""

import sys
from pathlib import Path
from PIL import Image

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "pipeline" / "scripts"))

from render_visual import render

OUT_DIR = REPO_ROOT / "pipeline" / "state" / "device_showcase"
OUT_DIR.mkdir(parents=True, exist_ok=True)

FEED_DIR = OUT_DIR / "in_feed_500px"
FEED_DIR.mkdir(parents=True, exist_ok=True)

# 1. Briefs
brief_stat = {
    "content_category": "TRUST_RISK",
    "headline": "Liquidation triggers at 1.1, not 1.0.",
    "hero": {"value": "1.10x", "label": "health factor floor"},
    "support": "The 10% gap is what pays for slippage and oracle lag.",
    "footer": "docs.vanna.finance"
}

brief_stmt = {
    "content_category": "NARRATIVE_THESIS",
    "headline": "Credit should not stop at one protocol.",
    "hero": {"value": "Soroban", "label": "native primitive"},
    "support": "True composability turns static collateral into active yield.",
    "footer": "docs.vanna.finance"
}

brief_arch = {
    "content_category": "PRODUCT",
    "headline": "Isolated SmartAccounts. Dedicated sandboxes.",
    "hero": {"value": "10x", "label": "leverage capacity"},
    "support": "Capital deploys directly to Blend and Aquarius without pooled contagion.",
    "footer": "docs.vanna.finance"
}

tasks = [
    # Lavender Accent 1080x1080
    ("card_single_stat.png", brief_stat, 1080, 1080, False),
    ("card_statement.png", brief_stmt, 1080, 1080, False),
    ("card_architecture.png", brief_arch, 1080, 1080, False),
    
    # Monochrome Glow 1080x1080
    ("card_single_stat_mono.png", brief_stat, 1080, 1080, True),
    ("card_statement_mono.png", brief_stmt, 1080, 1080, True),
    ("card_architecture_mono.png", brief_arch, 1080, 1080, True),
    
    # Wide Banner (1500x500)
    ("card_banner_1500x500.png", brief_stmt, 1500, 500, False),
    ("card_banner_1500x500_mono.png", brief_stmt, 1500, 500, True),
]

print("=== Rendering Brand Device Showcase ===")
for filename, brief, w, h, mono in tasks:
    out_path = OUT_DIR / filename
    render(brief, out_path, w=w, h=h, monochrome=mono)
    print(f"Generated: {filename} ({w}x{h}, mono={mono}) -> {out_path.stat().st_size} bytes")
    
    # Downscale to 500px width for in-feed legibility check
    img = Image.open(out_path)
    aspect = img.height / img.width
    feed_h = int(500 * aspect)
    feed_img = img.resize((500, feed_h), Image.Resampling.LANCZOS)
    feed_path = FEED_DIR / f"feed_{filename}"
    feed_img.save(feed_path, quality=95)
    print(f"  Downscaled feed preview: {feed_path.name} (500x{feed_h})")

print("\n=== All Deliverables Generated Successfully ===")
