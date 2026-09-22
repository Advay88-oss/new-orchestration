#!/usr/bin/env python3
"""Dedicated verification script for the Art-Directed Post Generation System.

Runs the exact narrative:
  "Most leveraged positions fail because crypto crashes while you are asleep.
   Vanna provides autonomous risk protection without giving up wallet custody."

Executes:
  1. Art Director (creates narrative-specific visual metaphor & constraints)
  2. Visual Generation (Google Model Garden gemini-3.1-flash-image)
  3. Final Reviewer Gate (inspects copy + actual PNG pixels across 10 criteria)
"""

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from pipeline.scripts.art_director import direct_art_for_narrative, compile_image_prompt
from pipeline.reviewer.reviewer import orchestrate_post_lifecycle


def run():
    narrative = (
        "Most leveraged positions fail because crypto crashes while you are asleep. "
        "Vanna provides autonomous risk protection without giving up wallet custody."
    )
    tweet = (
        "Most leveraged positions don't fail because the trade was bad. "
        "They fail because crypto crashes at 03:00 AM while you're asleep.\n\n"
        "Vanna's autonomous risk guardians run beneath scoped session keys to protect your Net Health Factor 24/7.\n\n"
        "Up to 10× margin on Stellar Soroban—automated liquidation defense without surrendering wallet custody.\n\n"
        "vanna.finance"
    )

    res = orchestrate_post_lifecycle(narrative, tweet, run_id="vanna-art-directed-final")
    print("\n--- FINAL TEST EXECUTION RESULT ---")
    print(json.dumps(res, indent=2))
    return res


if __name__ == "__main__":
    run()
