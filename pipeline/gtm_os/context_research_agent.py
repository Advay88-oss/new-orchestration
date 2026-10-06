"""Vanna Protocol DeFi Marketing Intelligence — Context.dev Research Agent.

Gathers live intelligence on competitors, protocol products, and category content
using Context.dev APIs (search, scrape, crawl, and brand intelligence).
Outputs structured findings with timestamps, source URLs, and tactical implications
for Vanna's GTM engine.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from pipeline.intelligence_stream.context_dev_service import ContextDevService

REPO_ROOT = Path(__file__).resolve().parents[2]


class ContextResearchAgent:
    """Autonomous research scout using Context.dev."""

    def __init__(self) -> None:
        self.service = ContextDevService.get_instance()

    def research_competitor(
        self, competitor_name: str, domain: Optional[str] = None
    ) -> Dict[str, Any]:
        """Perform 360-degree research on a competitor.

        1. Brand identity and official links
        2. Latest announcements & product updates
        3. Tactical counter-plays for Vanna
        """
        now = datetime.now(timezone.utc).isoformat()
        findings: Dict[str, Any] = {
            "agent": "Vanna_Context_Research_Agent",
            "competitor": competitor_name,
            "timestamp": now,
            "domain": domain,
            "sources": [],
            "brand_profile": None,
            "key_developments": [],
            "vanna_tactical_implication": "",
        }

        # 1. Retrieve Brand Intelligence if domain provided
        if domain:
            brand_res = self.service.retrieve_brand(domain)
            if brand_res.get("success"):
                findings["brand_profile"] = brand_res.get("brand")
                findings["sources"].append(
                    {"type": "brand_api", "url": f"https://{domain}", "timestamp": now}
                )

        # 2. Search for recent product updates / protocol news
        query = f"{competitor_name} DeFi lending vaults leverage announcement 2026"
        search_res = self.service.search_web(query, num_results=10)
        if search_res.get("success"):
            for r in search_res.get("results", [])[:5]:
                findings["key_developments"].append(
                    {
                        "title": r.get("title"),
                        "url": r.get("url"),
                        "snippet": r.get("description"),
                        "relevance": r.get("relevance"),
                    }
                )
                findings["sources"].append(
                    {"type": "web_search", "url": r.get("url"), "timestamp": now}
                )

        # 3. Derive Vanna tactical counter
        dev_snippets = " ".join(
            [d.get("snippet", "") for d in findings["key_developments"]]
        ).lower()
        if "vault" in dev_snippets or "curator" in dev_snippets:
            findings["vanna_tactical_implication"] = (
                f"{competitor_name} is pushing curated modular vaults. Vanna should contrast "
                "curator governance lag with Vanna's sub-second Mercury risk telemetry on Soroban."
            )
        elif "restaking" in dev_snippets or "points" in dev_snippets:
            findings["vanna_tactical_implication"] = (
                f"{competitor_name} is compounding speculative restaking risk. Vanna should highlight "
                "isolated SmartAccount sandboxes where bad debt is strictly quarantined from pool depositors."
            )
        else:
            findings["vanna_tactical_implication"] = (
                f"Highlight Vanna's up to 10x composable margin and 1.1x Health Factor protection "
                f"against {competitor_name}'s liquidation overhead."
            )

        return findings

    def research_topic(self, topic: str) -> Dict[str, Any]:
        """Search and extract structured evidence for a DeFi topic/trend."""
        now = datetime.now(timezone.utc).isoformat()
        search_res = self.service.search_web(topic, num_results=10)

        items = []
        if search_res.get("success"):
            for r in search_res.get("results", []):
                items.append(
                    {
                        "title": r.get("title"),
                        "url": r.get("url"),
                        "evidence": r.get("description"),
                        "timestamp": now,
                    }
                )

        return {
            "topic": topic,
            "timestamp": now,
            "total_evidence_found": len(items),
            "evidence": items,
        }


def main() -> None:
    parser = argparse.ArgumentParser(description="Vanna Context.dev Research Agent")
    parser.add_argument("--competitor", type=str, help="Competitor name (e.g. 'Morpho Labs')")
    parser.add_argument("--domain", type=str, help="Competitor domain (e.g. 'morpho.org')")
    parser.add_argument("--topic", type=str, help="DeFi topic to research")
    args = parser.parse_args()

    agent = ContextResearchAgent()
    if args.competitor:
        result = agent.research_competitor(args.competitor, domain=args.domain)
        print(json.dumps(result, indent=2))
    elif args.topic:
        result = agent.research_topic(args.topic)
        print(json.dumps(result, indent=2))
    else:
        # Default test run
        result = agent.research_competitor("Morpho Labs", domain="morpho.org")
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
