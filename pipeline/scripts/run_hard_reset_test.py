#!/usr/bin/env python3
"""Run Hard Reset Test across all 6 primitives."""

import json
from pathlib import Path
import sys

# Ensure local scripts are importable
scripts_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(scripts_dir))

from render_visual import render
from art_director import ARCHETYPE_RULES

content = {
    "headline": "Up to 10x leverage.\nZero contagion.",
    "subhead": "SmartAccount sandboxes compartmentalize risk upfront. One liquidation never imperils your book.",
    "category": "CAPITAL ARCHITECTURE // STELLAR SOROBAN",
    "hero_stat": "10x",
    "source": "docs.vanna.finance • 14 Audited Smart Contracts",
    "tag": "STELLAR SOROBAN // TESTNET LIVE"
}

archetypes = [
    "editorial_manifesto",
    "technical_architecture",
    "data_visualization",
    "product_system_diagram",
    "asymmetric_hero_composition",
    "cinematic_minimal"
]

results = {}
out_dir = Path("pipeline/state/hard_reset_renders")
out_dir.mkdir(parents=True, exist_ok=True)

for arc in archetypes:
    out_png = out_dir / f"primitive_{arc}.png"
    out_html = out_dir / f"primitive_{arc}.html"
    print(f"Rendering {arc}...")
    render(content, out_png, keep_html=out_html, forced_layout=arc)
    
    desc = ARCHETYPE_RULES[arc]["description"]
    focus = ARCHETYPE_RULES[arc]["best_for"][0]
    
    results[arc] = {
        "primitive": arc,
        "png": str(out_png),
        "bytes": out_png.stat().st_size,
        "composition": ARCHETYPE_RULES[arc]["composition"],
        "primary_focal": ARCHETYPE_RULES[arc]["primary_focal"],
        "art_direction_rationale": f"Employs {desc} Designed specifically for narrative focus on {focus}."
    }

out_json = out_dir / "test_results.json"
out_json.write_text(json.dumps(results, indent=2), encoding="utf-8")

print("\n--- ALL 6 PRIMITIVES RENDERED SUCCESSFULLY ---")
print(json.dumps(results, indent=2))
