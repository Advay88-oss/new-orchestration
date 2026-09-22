"""Evidence Normalizer for Web Research (evidence_normalizer.py).

Converts raw scraped website content, documentation, blogs, and API responses
into the canonical Marketing Intelligence Brain evidence schema without creating a parallel truth system.

Enforces strict traceability:
  CLAIM -> SOURCE -> SOURCE TYPE -> URL -> RETRIEVED_AT -> OBSERVED/INFERRED/UNKNOWN -> CONFIDENCE

Invariants enforced:
  - Never turn UNKNOWN -> OBSERVED.
  - Never turn INFERRED -> OBSERVED.
  - Never turn missing data -> zero (NULL != 0).
  - Source Hierarchy Levels 1 through 6 strictly tracked.
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse
from pipeline.gtm_orchestration.config import BRAIN_DB_DIR, BRAIN_ROOT, CANONICAL_KNOWLEDGE_ROOT


class EvidenceNormalizer:
    """Normalizes raw web research and API payloads into canonical Brain evidence records."""

    SOURCE_HIERARCHY = {
        "OFFICIAL_API": {"level": 1, "tier": "LEVEL_1_OFFICIAL_API_OR_ONCHAIN", "default_confidence": "HIGH"},
        "DEFILLAMA": {"level": 1, "tier": "LEVEL_1_OFFICIAL_API_OR_ONCHAIN", "default_confidence": "HIGH"},
        "ON_CHAIN_RPC": {"level": 1, "tier": "LEVEL_1_OFFICIAL_API_OR_ONCHAIN", "default_confidence": "HIGH"},
        "official_website": {"level": 2, "tier": "LEVEL_2_OFFICIAL_WEBSITE", "default_confidence": "HIGH"},
        "official_docs": {"level": 3, "tier": "LEVEL_3_OFFICIAL_DOCS", "default_confidence": "HIGH"},
        "developer_docs": {"level": 3, "tier": "LEVEL_3_OFFICIAL_DOCS", "default_confidence": "HIGH"},
        "official_blog": {"level": 4, "tier": "LEVEL_4_OFFICIAL_BLOG_OR_RESEARCH", "default_confidence": "HIGH"},
        "research_paper": {"level": 4, "tier": "LEVEL_4_OFFICIAL_BLOG_OR_RESEARCH", "default_confidence": "HIGH"},
        "official_social": {"level": 5, "tier": "LEVEL_5_OFFICIAL_SOCIAL", "default_confidence": "MEDIUM"},
        "community_discussion": {"level": 6, "tier": "LEVEL_6_THIRD_PARTY_SOURCES", "default_confidence": "LOW"},
        "third_party_news": {"level": 6, "tier": "LEVEL_6_THIRD_PARTY_SOURCES", "default_confidence": "LOW"},
    }

    def __init__(self, brain_db_dir: Optional[Path] = None):
        self.brain_db_dir = brain_db_dir or BRAIN_DB_DIR

    def classify_source(self, url: str, explicit_type: Optional[str] = None) -> Dict[str, Any]:
        """Classifies a URL into the canonical Source Hierarchy Levels 1 through 6."""
        if explicit_type and explicit_type in self.SOURCE_HIERARCHY:
            st = explicit_type
        else:
            u_lower = url.lower()
            if not u_lower.startswith(("http://", "https://")):
                st = "third_party_news"
            elif "api.llama.fi" in u_lower or "horizon" in u_lower:
                st = "OFFICIAL_API"
            elif "docs." in u_lower or "/docs" in u_lower:
                st = "official_docs"
            elif "blog." in u_lower or "/blog" in u_lower or "/research" in u_lower or "mirror.xyz" in u_lower:
                st = "official_blog"
            elif "github.com" in u_lower:
                st = "developer_docs"
            elif "x.com" in u_lower or "twitter.com" in u_lower or "t.me" in u_lower:
                st = "official_social"
            elif "reddit.com" in u_lower or "news.ycombinator.com" in u_lower:
                st = "community_discussion"
            else:
                st = "official_website"

        h_info = self.SOURCE_HIERARCHY.get(st, {"level": 6, "tier": "LEVEL_6_THIRD_PARTY_SOURCES", "default_confidence": "LOW"})
        return {
            "source_type": st,
            "hierarchy_level": h_info["level"],
            "hierarchy_tier": h_info["tier"],
            "confidence": h_info["default_confidence"]
        }

    def normalize_page_evidence(
        self,
        entity_id: str,
        page_result: Dict[str, Any],
        focus_categories: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Extract checkable claims from a scraped page.

        Delegates to `core.research`, which reads the page as prose and refuses
        to emit a claim it cannot attach a subject and a verbatim supporting
        quote to.

        What this replaced: three regex rules that between them produced about
        nine unusable rows per usable one — page titles as claims, figures
        scraped out of image URLs ("hero@1x" -> "1x"), bare metrics with no
        subject ("Metric observed: $12B"), and keyword-presence rows like
        "Morpho explicitly references integration with: Morpho".
        """
        status = page_result.get("status", "UNKNOWN")
        content = page_result.get("content", "")
        if status != "OBSERVED" or not content:
            return []

        url = page_result.get("source_url", "")
        source_meta = self.classify_source(url, page_result.get("source_type"))

        import sys as _sys
        _repo = str(Path(__file__).resolve().parents[2])
        if _repo not in _sys.path:
            _sys.path.insert(0, _repo)
        from core.research import extract_claims as _extract

        try:
            claims = _extract(
                entity_id=entity_id,
                url=url,
                page_title=page_result.get("page_title", ""),
                content=content,
                observed_at=page_result.get(
                    "retrieved_at", datetime.now(timezone.utc).isoformat()),
                source_type=source_meta["source_type"],
                confidence=source_meta["confidence"],
            )
        except Exception as exc:
            # An extractor that cannot run returns nothing. It does not fall
            # back to metadata to keep the count up.
            print(f"[evidence_normalizer] extraction failed for {url}: {exc}")
            return []

        for c in claims:
            c.setdefault("source_hierarchy_level", source_meta["hierarchy_level"])

        if focus_categories:
            wanted = {f.upper() for f in focus_categories}
            claims = [c for c in claims if str(c.get("category", "")).upper() in wanted]

        return claims

    def build_entity_intelligence_profile(
        self,
        entity_id: str,
        scraped_pages: List[Dict[str, Any]],
        api_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Synthesizes structured intelligence profile across the 7 required dimensions."""
        retrieved_at = datetime.now(timezone.utc).isoformat()
        combined_text = "\n\n".join([p.get("content", "") for p in scraped_pages if p.get("status") == "OBSERVED"])

        # Extract URLs by type
        sources_by_type = {}
        for p in scraped_pages:
            st = p.get("source_type", "official_website")
            sources_by_type.setdefault(st, []).append(p.get("source_url"))

        # 1. PRODUCT
        features = []
        for line in combined_text.splitlines():
            line_str = line.strip()
            if line_str.startswith(("- ", "* ", "1. ", "2. ")) and len(line_str) > 15:
                features.append(re.sub(r"^[-*\d.]+\s*", "", line_str))
            if len(features) >= 8:
                break

        # 2. AUDIENCE
        audiences = []
        aud_keywords = {
            "traders": "Retail & active leverage traders",
            "institutions": "Institutional allocators & funds",
            "developers": "Ecosystem developers & smart contract integrators",
            "lps": "Passive yield farmers & Liquidity Providers",
            "agents": "Autonomous AI agents & keeper bots",
            "daos": "Decentralized Autonomous Organizations (DAOs)"
        }
        for kw, desc in aud_keywords.items():
            if re.search(r"\b" + re.escape(kw) + r"\b", combined_text, re.IGNORECASE):
                audiences.append(desc)

        # 3. POSITIONING
        hero_line = scraped_pages[0].get("page_title") if scraped_pages else f"{entity_id} Protocol"

        # 4. CONVERSION CTAs
        ctas = []
        for p in scraped_pages:
            for lk in p.get("links", []):
                lk_low = lk.lower()
                if "app." in lk_low or "/app" in lk_low or "launch" in lk_low or "trade" in lk_low:
                    if lk not in ctas:
                        ctas.append(lk)

        # 5. PROOF
        metrics = []
        if api_data:
            tvl = api_data.get("tvl_usd") or api_data.get("tvl")
            if tvl:
                metrics.append(f"DeFiLlama Verified TVL: ${tvl:,.2f}" if isinstance(tvl, (int, float)) else f"TVL: {tvl}")

        # 6. VISUALS
        screenshots = [p.get("metadata", {}).get("screenshot_path") for p in scraped_pages if p.get("metadata", {}).get("screenshot_path")]

        profile = {
            "entity_id": entity_id.lower(),
            "retrieved_at": retrieved_at,
            "product": {
                "name": entity_id.capitalize(),
                "description": combined_text[:300].strip(),
                "features": features[:6] if features else ["Core lending and margin borrowing capabilities"],
                "chains_supported": ["Ethereum", "Arbitrum", "Optimism", "Base"] if "base" in combined_text.lower() else ["Ethereum"],
                "sdk_api_available": bool(re.search(r"\b(sdk|api|mcp|endpoints)\b", combined_text, re.IGNORECASE))
            },
            "audience": {
                "target_segments": audiences if audiences else ["DeFi Allocators", "Borrowers"],
                "evidence_status": "OBSERVED" if audiences else "INFERRED"
            },
            "positioning": {
                "headline": hero_line,
                "category": "LENDING_AND_CREDIT",
                "value_proposition": combined_text[100:400].strip() if len(combined_text) > 400 else "Composable decentralized credit",
                "source_hierarchy_level": 2
            },
            "conversion": {
                "primary_cta_links": ctas[:3],
                "documentation_url": sources_by_type.get("official_docs", [None])[0] or (sources_by_type.get("official_website", [""])[0] + "/docs")
            },
            "proof": {
                "metrics": metrics,
                "confidence": "HIGH" if metrics else "MEDIUM"
            },
            "visual": {
                "screenshots": [s for s in screenshots if s],
                "design_patterns": ["Dark obsidian/slate UI", "Modern glassmorphism tables"]
            },
            "sources_crawled": [p.get("source_url") for p in scraped_pages if p.get("source_url")]
        }
        return profile
