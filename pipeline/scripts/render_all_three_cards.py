#!/usr/bin/env python3
"""Test 2: Render all three locked templates through the validated engine.
1. single_stat (TRUST_RISK -> data_visualization)
2. architecture (PRODUCT -> technical_architecture)
3. statement (NARRATIVE_THESIS -> editorial_manifesto)
"""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "pipeline" / "scripts"))

from render_visual import render

OUT_DIR = REPO_ROOT / "pipeline" / "state" / "three_cards"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# 1. Single Stat Brief
brief_stat = {
    "content_category": "TRUST_RISK",
    "headline": "Liquidation triggers at 1.1, not 1.0.",
    "hero": {"value": "1.10x", "label": "health factor floor"},
    "support": "The 10% gap is what pays for slippage and oracle lag.",
    "footer": "docs.vanna.finance"
}
out_stat = OUT_DIR / "card_single_stat.png"
render(brief_stat, out_stat)
print(f"Rendered single_stat: {out_stat.name} ({out_stat.stat().st_size} bytes)")

# 2. Architecture Brief
brief_arch = {
    "content_category": "PRODUCT",
    "headline": "Isolated SmartAccounts. Dedicated sandboxes.",
    "hero": {"value": "10x", "label": "leverage capacity"},
    "support": "Capital deploys directly to Blend and Aquarius without pooled contagion.",
    "footer": "docs.vanna.finance"
}
out_arch = OUT_DIR / "card_architecture.png"
render(brief_arch, out_arch)
print(f"Rendered architecture: {out_arch.name} ({out_arch.stat().st_size} bytes)")

# 3. Statement Brief
brief_stmt = {
    "content_category": "NARRATIVE_THESIS",
    "headline": "Credit should not stop at one protocol.",
    "hero": {"value": "Soroban", "label": "native primitive"},
    "support": "True composability turns static collateral into active yield.",
    "footer": "docs.vanna.finance"
}
out_stmt = OUT_DIR / "card_statement.png"
render(brief_stmt, out_stmt)
print(f"Rendered statement: {out_stmt.name} ({out_stmt.stat().st_size} bytes)")
