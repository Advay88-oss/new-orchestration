"""Thin programmatic adapter for the installed OpenCLI Browser Bridge scraper.

Exposes normalized scraping and browser automation operations without business logic:
  - extract_page()
  - research_url()
  - extract_metadata()
  - follow_links()
  - capture_page()
  - crawl_domain()

Returns structured evidence dicts adhering to the canonical evidence schema.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin, urlparse


class WebResearchTool:
    """Thin adapter invoking the installed OpenCLI Browser Bridge extension."""

    def __init__(self, session_prefix: str = "vanna_research"):
        import shutil
        self.session_prefix = session_prefix
        self.opencli_bin = shutil.which("opencli") or "opencli"

    def _run_cli(self, args: List[str], timeout: float = 30.0) -> subprocess.CompletedProcess:
        """Executes opencli subprocess with error handling and shell=True on Windows."""
        cmd = [self.opencli_bin] + args
        return subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            encoding="utf-8",
            errors="replace"
        )

    def extract_page(
        self,
        url: str,
        wait_seconds: int = 3,
        timeout: float = 30.0
    ) -> Dict[str, Any]:
        """Extracts text content and markdown from a single web page."""
        retrieved_at = datetime.now(timezone.utc).isoformat()
        try:
            args = [
                "web", "read",
                "--url", url,
                "--wait", str(wait_seconds),
                "--stdout", "true"
            ]
            res = self._run_cli(args, timeout=timeout)
            
            if res.returncode != 0 or not res.stdout.strip():
                return {
                    "source_url": url,
                    "source_type": self._infer_source_type(url),
                    "retrieved_at": retrieved_at,
                    "page_title": "",
                    "content": "",
                    "links": [],
                    "metadata": {"error": res.stderr.strip() or "Empty stdout"},
                    "evidence": [],
                    "status": "SCRAPE_FAILED"
                }

            raw_text = res.stdout.strip()
            # Clean possible npm update banners from opencli output
            clean_text = re.sub(r"Update available:.*", "", raw_text, flags=re.DOTALL).strip()

            # Detect common browser DNS/resolution error pages
            error_patterns = [
                "ERR_NAME_NOT_RESOLVED", "DNS_PROBE_", "ERR_CONNECTION_REFUSED",
                "ERR_CONNECTION_TIMED_OUT", "404 Not Found", "Page not found"
            ]
            if any(ep in clean_text for ep in error_patterns) or len(clean_text) < 20:
                return {
                    "source_url": url,
                    "source_type": self._infer_source_type(url),
                    "retrieved_at": retrieved_at,
                    "page_title": "",
                    "content": "",
                    "links": [],
                    "metadata": {"error": "Browser navigation error or empty page"},
                    "evidence": [],
                    "status": "SCRAPE_FAILED"
                }

            # Extract title if available from markdown heading # Title
            title_match = re.search(r"^#\s+(.+)$", clean_text, re.MULTILINE)
            title = title_match.group(1).strip() if title_match else urlparse(url).netloc

            # Extract raw links
            links = self._extract_links_from_markdown(clean_text, url)

            return {
                "source_url": url,
                "source_type": self._infer_source_type(url),
                "retrieved_at": retrieved_at,
                "page_title": title,
                "content": clean_text,
                "links": links,
                "metadata": {
                    "content_length": len(clean_text),
                    "link_count": len(links),
                    "engine": "opencli_browser_bridge"
                },
                "evidence": [],
                "status": "OBSERVED"
            }
        except subprocess.TimeoutExpired:
            return {
                "source_url": url,
                "source_type": self._infer_source_type(url),
                "retrieved_at": retrieved_at,
                "page_title": "",
                "content": "",
                "links": [],
                "metadata": {"error": f"Timeout after {timeout}s"},
                "evidence": [],
                "status": "SCRAPE_FAILED"
            }
        except Exception as e:
            return {
                "source_url": url,
                "source_type": self._infer_source_type(url),
                "retrieved_at": retrieved_at,
                "page_title": "",
                "content": "",
                "links": [],
                "metadata": {"error": str(e)},
                "evidence": [],
                "status": "SCRAPE_FAILED"
            }

    def capture_page(
        self,
        url: str,
        output_path: str,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Loads a page in the browser session and takes a visual PNG screenshot."""
        sid = session_id or f"{self.session_prefix}_snap"
        retrieved_at = datetime.now(timezone.utc).isoformat()
        try:
            # 1. Open URL in session
            open_res = self._run_cli(["browser", sid, "open", url, "--window", "background"], timeout=20.0)
            if open_res.returncode != 0:
                return {
                    "source_url": url,
                    "screenshot_path": None,
                    "retrieved_at": retrieved_at,
                    "status": "SCRAPE_FAILED",
                    "error": open_res.stderr.strip()
                }

            # Wait briefly for render
            time.sleep(2)

            # 2. Capture screenshot
            snap_res = self._run_cli(["browser", sid, "screenshot", output_path], timeout=20.0)
            
            # 3. Release lease
            self._run_cli(["browser", sid, "close"], timeout=10.0)

            saved = Path(output_path).exists()
            return {
                "source_url": url,
                "screenshot_path": output_path if saved else None,
                "retrieved_at": retrieved_at,
                "status": "OBSERVED" if saved else "SCRAPE_FAILED",
                "error": None if saved else snap_res.stderr.strip()
            }
        except Exception as e:
            try:
                self._run_cli(["browser", sid, "close"], timeout=5.0)
            except Exception:
                pass
            return {
                "source_url": url,
                "screenshot_path": None,
                "retrieved_at": retrieved_at,
                "status": "SCRAPE_FAILED",
                "error": str(e)
            }

    def follow_links(
        self,
        base_url: str,
        allowed_paths: Optional[List[str]] = None,
        max_links: int = 5
    ) -> List[str]:
        """Discovers and filters target links from a page."""
        page_data = self.extract_page(base_url)
        if page_data.get("status") != "OBSERVED":
            return []

        links = page_data.get("links", [])
        base_domain = urlparse(base_url).netloc

        filtered: List[str] = []
        for link in links:
            parsed = urlparse(link)
            # Only keep same-domain or subdomains
            if parsed.netloc and parsed.netloc != base_domain and not parsed.netloc.endswith(f".{base_domain}"):
                continue

            path = parsed.path.lower()
            if allowed_paths:
                if any(p.lower() in path for p in allowed_paths):
                    if link not in filtered:
                        filtered.append(link)
            else:
                if link not in filtered:
                    filtered.append(link)

            if len(filtered) >= max_links:
                break

        return filtered

    def extract_metadata(self, url: str) -> Dict[str, Any]:
        """Extracts metadata headers, page title, and structure."""
        page_res = self.extract_page(url, wait_seconds=2)
        if page_res.get("status") != "OBSERVED":
            return {"source_url": url, "status": "SCRAPE_FAILED", "metadata": {}}

        content = page_res.get("content", "")
        headings = re.findall(r"^(#{1,3})\s+(.+)$", content, re.MULTILINE)
        
        return {
            "source_url": url,
            "page_title": page_res.get("page_title"),
            "domain": urlparse(url).netloc,
            "heading_structure": [h[1] for h in headings[:10]],
            "content_length": len(content),
            "status": "OBSERVED"
        }

    def research_url(
        self,
        url: str,
        capture_screenshot: bool = False,
        screenshot_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """Full research operation extracting content, links, and optional screenshot."""
        data = self.extract_page(url)
        if capture_screenshot and screenshot_path and data.get("status") == "OBSERVED":
            snap = self.capture_page(url, screenshot_path)
            data["metadata"]["screenshot_path"] = snap.get("screenshot_path")
        return data

    def crawl_domain(
        self,
        start_url: str,
        max_pages: int = 5,
        priority_paths: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Bounded crawling within a single domain up to max_pages."""
        results: List[Dict[str, Any]] = []
        visited = set()
        queue = [start_url]

        priority_paths = priority_paths or ["/product", "/docs", "/blog", "/research", "/ecosystem", "/about"]

        while queue and len(results) < max_pages:
            current_url = queue.pop(0)
            if current_url in visited:
                continue
            visited.add(current_url)

            page_data = self.extract_page(current_url)
            results.append(page_data)

            if page_data.get("status") == "OBSERVED":
                # Find downstream candidate links
                discovered_links = self.follow_links(
                    current_url,
                    allowed_paths=priority_paths,
                    max_links=max_pages
                )
                for lk in discovered_links:
                    if lk not in visited and lk not in queue:
                        queue.append(lk)

        return results

    def _infer_source_type(self, url: str) -> str:
        """Infers source hierarchy classification from URL structure."""
        url_lower = url.lower()
        if "docs." in url_lower or "/docs" in url_lower:
            return "official_docs"
        if "blog." in url_lower or "/blog" in url_lower or "/research" in url_lower:
            return "official_blog"
        if "github.com" in url_lower:
            return "developer_docs"
        if "twitter.com" in url_lower or "x.com" in url_lower:
            return "official_social"
        if "reddit.com" in url_lower:
            return "community_discussion"
        return "official_website"

    def _extract_links_from_markdown(self, markdown: str, base_url: str) -> List[str]:
        """Extracts normalized absolute links from markdown text."""
        raw_links = re.findall(r"\[.*?\]\((https?://[^\s\)]+|/[^\s\)]+)\)", markdown)
        seen = set()
        normalized = []
        for rk in raw_links:
            full_url = urljoin(base_url, rk)
            # Filter anchor-only or mailto links
            if full_url.startswith("http") and full_url not in seen:
                seen.add(full_url)
                normalized.append(full_url)
        return normalized
