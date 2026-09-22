#!/usr/bin/env python3
"""Live Execution Runner for Web Research against Gearbox, Morpho, and Derive."""

import json
import os
import sys
import time
from pathlib import Path

# Add repo root to python path
REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from pipeline.research.web_researcher import WebResearcher, ResearchPlan

OUTPUT_DIR = REPO_ROOT / "pipeline" / "state" / "research_runs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

ENTITIES = [
    {
        "entity": "Gearbox",
        "slug": "gearbox",
        "objectives": [
            "understand product", "understand positioning", "identify target users",
            "identify integrations", "identify proof points"
        ],
        "sources": ["official website", "docs", "blog"]
    },
    {
        "entity": "Morpho",
        "slug": "morpho",
        "objectives": [
            "understand product", "understand positioning", "identify target users",
            "identify integrations", "identify proof points"
        ],
        "sources": ["official website", "docs", "blog"]
    },
    {
        "entity": "Derive",
        "slug": "derive",
        "objectives": [
            "understand product", "understand positioning", "identify target users",
            "identify integrations", "identify proof points"
        ],
        "sources": ["official website", "docs", "blog"]
    }
]


def run_live(target_entity: str | None = None):
    researcher = WebResearcher()
    results = []

    print("=" * 80)
    print("🚀 EXECUTING LIVE PRODUCTION RESEARCH (NO MOCKS, NO FIXTURES)")
    print("=" * 80)

    entities_to_run = ENTITIES
    if target_entity:
        matched = [e for e in ENTITIES if e["entity"].lower() == target_entity.lower() or e["slug"].lower() == target_entity.lower()]
        if matched:
            entities_to_run = matched
        else:
            entities_to_run = [{
                "entity": target_entity,
                "slug": target_entity.lower().replace(" ", "-"),
                "objectives": ["understand product", "understand positioning", "identify target users", "identify proof points"],
                "sources": ["official website", "docs"]
            }]

    for item in entities_to_run:
        plan = ResearchPlan(
            entity=item["entity"],
            defillama_slug=item["slug"],
            research_objectives=item["objectives"],
            required_sources=item["sources"],
            max_pages_per_domain=3,
            max_research_time_sec=60
        )
        t0 = time.time()
        res = researcher.execute_research_plan(plan)
        res["duration"] = round(time.time() - t0, 2)
        results.append(res)

        # Save run artifact
        out_file = OUTPUT_DIR / f"{res['run_id']}.json"
        out_file.write_text(json.dumps(res, indent=2), encoding="utf-8")
        print(f"📄 Saved Run Artifact: {out_file.name}")

    summary_file = OUTPUT_DIR / "live_research_summary.json"
    summary_file.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"\n✅ Researched {len(entities_to_run)} entities. Summary saved to {summary_file.name}")
    return results


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--entity", type=str, default=None, help="Target entity to scrape")
    args = parser.parse_args()
    run_live(args.entity)
