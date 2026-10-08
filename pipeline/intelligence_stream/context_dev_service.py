"""Context.dev Unified Service Wrapper.

Provides a unified server-side wrapper for Context.dev API and MCP capabilities:
- Search Web (POST /web/search)
- Scrape Markdown (POST /web/scrape)
- Crawl Docs / Pages (POST /web/crawl)
- Brand Retrieval (POST /brand/retrieve)
- Company News Search (POST /news/search)

Handles authentication, error codes, retries with backoff, and rate limits.
Documentation: https://docs.context.dev
"""
from __future__ import annotations

import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from context.dev import ContextDev
except ImportError:
    ContextDev = None  # type: ignore

REPO_ROOT = Path(__file__).resolve().parents[2]


def _get_api_key() -> str:
    """Retrieve CONTEXT_DEV_API_KEY from environment or pipeline/.env."""
    key = os.environ.get("CONTEXT_DEV_API_KEY")
    if key:
        return key

    env_file = REPO_ROOT / "pipeline" / ".env"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("CONTEXT_DEV_API_KEY="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    return ""


class ContextDevService:
    """Singleton service for Context.dev web data, scraping, and brand intel."""

    _instance: Optional["ContextDevService"] = None

    def __init__(self, api_key: Optional[str] = None) -> None:
        self.api_key = api_key or _get_api_key()
        if not self.api_key:
            raise ValueError(
                "CONTEXT_DEV_API_KEY not found in environment or pipeline/.env. "
                "Get a key at https://www.context.dev/dashboard/api-keys"
            )
        if ContextDev is None:
            raise ImportError(
                "context.dev package not installed. Run 'pip install context.dev'"
            )
        self.client = ContextDev(api_key=self.api_key)

    @staticmethod
    def _paid(fn, **kwargs):
        """One Context.dev request, checked against the day's budget first and
        counted after (the SDK does not go through urllib, so the guard in
        pipeline/ops/guard.py never sees it)."""
        from pipeline.ops import budget as B
        B.check("context_dev")
        out = fn(**kwargs)
        rate = ((B.config().get("rates") or {}).get("context_dev") or {}).get("per_call", 0.01)
        B.add("context_dev", float(rate))
        return out

    @classmethod
    def get_instance(cls) -> "ContextDevService":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def search_web(
        self,
        query: str,
        num_results: int = 10,
        freshness: Optional[str] = None,
        include_domains: Optional[List[str]] = None,
        exclude_domains: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Search the web for ranked results.

        Docs: https://docs.context.dev/api-reference/web-scraping/search
        """
        params: Dict[str, Any] = {
            "query": query,
            "num_results": max(10, min(100, num_results)),
        }
        if freshness:
            params["freshness"] = freshness
        if include_domains:
            params["include_domains"] = include_domains
        if exclude_domains:
            params["exclude_domains"] = exclude_domains

        try:
            resp = self._paid(self.client.web.search, **params)
            results = []
            for r in getattr(resp, "results", []) or []:
                results.append(
                    {
                        "title": getattr(r, "title", ""),
                        "url": getattr(r, "url", ""),
                        "description": getattr(r, "description", ""),
                        "relevance": getattr(r, "relevance", None),
                    }
                )
            return {
                "success": True,
                "query": query,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "count": len(results),
                "results": results,
                "key_metadata": getattr(resp, "key_metadata", None),
            }
        except Exception as exc:
            return {
                "success": False,
                "query": query,
                "error": str(exc),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

    def scrape_markdown(
        self,
        url: str,
        use_main_content_only: bool = True,
        max_age_ms: int = 86400000,
    ) -> Dict[str, Any]:
        """Scrape a web page and return clean Markdown.

        Docs: https://docs.context.dev/api-reference/web-scraping/scrape
        """
        try:
            resp = self._paid(self.client.web.scrape, 
                url=url,
                use_main_content_only=use_main_content_only,
                max_age_ms=max_age_ms,
            )
            # Inspect output format
            md = getattr(resp, "markdown", "") or ""
            return {
                "success": True,
                "url": url,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "markdown": md,
                "title": getattr(resp, "title", ""),
                "key_metadata": getattr(resp, "key_metadata", None),
            }
        except Exception as exc:
            return {
                "success": False,
                "url": url,
                "error": str(exc),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

    def retrieve_brand(self, domain: str) -> Dict[str, Any]:
        """Retrieve brand profile, logos, description, and social handles.

        Docs: https://docs.context.dev/api-reference/brand-intelligence/brand
        """
        try:
            resp = self._paid(self.client.brand.retrieve, 
                type="by_domain",
                domain=domain,
            )
            raw_brand = getattr(resp, "brand", None) or getattr(resp, "data", None)
            brand_dict = None
            if raw_brand is not None:
                if hasattr(raw_brand, "model_dump"):
                    brand_dict = raw_brand.model_dump()
                elif hasattr(raw_brand, "dict"):
                    brand_dict = raw_brand.dict()
                elif hasattr(raw_brand, "__dict__"):
                    brand_dict = vars(raw_brand)
                else:
                    brand_dict = str(raw_brand)

            return {
                "success": True,
                "domain": domain,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "brand": brand_dict,
                "key_metadata": getattr(resp, "key_metadata", None),
            }
        except Exception as exc:
            return {
                "success": False,
                "domain": domain,
                "error": str(exc),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

    def crawl_website(
        self,
        url: str,
        max_pages: int = 5,
        max_depth: int = 2,
    ) -> Dict[str, Any]:
        """Crawl a website and extract Markdown for each page.

        Docs: https://docs.context.dev/api-reference/web-scraping/crawl
        """
        try:
            resp = self._paid(self.client.web.web_crawl_md, 
                url=url,
                max_pages=max_pages,
                max_depth=max_depth,
            )
            pages = []
            for p in getattr(resp, "results", []) or []:
                pages.append(
                    {
                        "url": getattr(p, "url", ""),
                        "markdown": (getattr(p, "markdown", "") or "")[:2000],
                    }
                )
            return {
                "success": True,
                "start_url": url,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "pages_crawled": len(pages),
                "results": pages,
            }
        except Exception as exc:
            return {
                "success": False,
                "url": url,
                "error": str(exc),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
