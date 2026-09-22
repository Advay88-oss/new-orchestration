#!/usr/bin/env python3
"""Run 2 & Run 3: Full End-to-End Content Loop & Outcome Logging.
1. Ingests PAT_CRISIS_SOLVENCY from patterns.jsonl.
2. Runs writer -> skeptic -> claim gate -> template select -> render.
3. Outputs draft text + rendered 1080x1080 card.
4. Logs outcome to registry and verifies pattern attachment.
"""

import json
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "pipeline" / "scripts"))

from content_loop import run_content_loop
from outcome_logger import log_outcome, get_status, get_stats, PATTERNS_FILE
from autonomous_orchestrator import call_vertex

# Wrap call_vertex for content_loop
def model_fn(system_instruction: str, prompt: str, tier: str = "strong") -> str:
    return call_vertex(system_instruction, prompt, temperature=0.3 if tier == "strong" else 0.1)

# BRIEF based on PAT_CRISIS_SOLVENCY
brief = {
    "pattern_id": "PAT_CRISIS_SOLVENCY",
    "content_category": "TRUST_RISK",
    "headline": "Liquidation triggers at 1.1, not 1.0.",
    "hero_value": "1.10x",
    "hero_label": "health factor floor",
    "support": "The 10% gap is what pays for slippage and oracle lag.",
    "footer": "docs.vanna.finance"
}

print("=== RUN 2: Executing Content Loop ===")
res = run_content_loop(brief, model_fn, human_approved=True)

print("\n--- DRAFT TEXT ---")
draft_text = res["draft"].get("post_text") or res["draft"].get("headline")
print(draft_text)

print("\n--- RENDERED ASSET ---")
img_path = res["image_path"]
print(f"Path: {img_path}")
print(f"Size: {Path(img_path).stat().st_size} bytes")

print("\n=== RUN 3: Logging Outcome Live ===")
outcome = log_outcome(
    pattern_ref="PAT_CRISIS_SOLVENCY",
    decision="APPROVED_WITH_EDITS",
    edit_diff="- abstract solvency theory\n+ exact 1.10x liquidation floor math",
    founder_note="Approved. Clear focus on the 10% safety buffer paying for oracle latency.",
    published_url="https://x.com/VannaProtocol/status/testnet-solvency-01"
)

# Verify pattern record attachment in patterns.jsonl
attached_pat = None
with open(PATTERNS_FILE, "r", encoding="utf-8") as f:
    for line in f:
        if not line.strip(): continue
        p = json.loads(line)
        if p.get("id") == "PAT_CRISIS_SOLVENCY" or p.get("name") == "Crisis Solvency and Liquidation Stress Retrospective" or p.get("pattern_id") == "PAT_CRISIS_SOLVENCY":
            attached_pat = p
            break

print("\n--- ATTACHED PATTERN IN REGISTRY ---")
if attached_pat:
    print(f"Pattern ID: {attached_pat.get('id') or attached_pat.get('pattern_id')}")
    print(f"Status: {attached_pat.get('status')}")
    print(f"Decision Stats: {attached_pat.get('decision_stats')}")
    print(f"Latest Evidence: {attached_pat.get('performance_evidence', [])[-1]}")
else:
    print("Pattern not found in file")
