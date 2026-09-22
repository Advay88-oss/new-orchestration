#!/usr/bin/env python3
"""Loop A — Research Collector.

Executes collection across owned blogs, governance forums, newsletters, and docs.
Wires content_cache.cache_lookup before network fetches and content_cache.cache_store after.
Returns structured status objects distinguishing skips from failures.
"""

from __future__ import annotations

import os
import sys
import urllib.request
from pathlib import Path
from typing import Any, Dict, Optional

REPO_ROOT = Path(os.environ.get("VANNA_ROOT", Path(__file__).resolve().parents[2]))
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from pipeline.scripts.content_cache import cache_lookup, cache_store, classification_view


def fetch_raw_body(url: str, timeout: float = 10.0) -> str:
    """Fetches raw page content over HTTP with standard headers."""
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) VannaScout/2.0"}
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", errors="replace")


def collect_artefact(candidate: Dict[str, Any]) -> Dict[str, Any]:
    """Collects an artefact while enforcing strict content-hash cache discipline.
    
    Returns structured status object:
    - SKIP: already fresh, no network call
    - RECLASSIFY: schema older, using stored raw
    - FETCHED: fresh fetch completed and cached
    - FETCH_FAILED: network error
    """
    url = candidate.get("url", "")
    
    # CALL SITE 1: cache_lookup before fetch
    action, cached_payload = cache_lookup(candidate)
    
    if action == "SKIP":
        return {
            "status": "SKIP",
            "url": url,
            "artefact": None
        }
        
    if action == "RECLASSIFY":
        return {
            "status": "RECLASSIFY",
            "url": url,
            "artefact": cached_payload
        }
        
    # ACTION == 'FETCH': Perform network request
    try:
        raw_text = fetch_raw_body(url)
    except Exception as e:
        return {
            "status": "FETCH_FAILED",
            "url": url,
            "artefact": None,
            "error": str(e)
        }
        
    # CALL SITE 2: cache_store after fetch
    cache_store(candidate, raw_text)
    
    return {
        "status": "FETCHED",
        "url": url,
        "artefact": {
            **candidate,
            "raw_text": raw_text,
            "classification_view": classification_view(raw_text)
        }
    }


if __name__ == "__main__":
    if len(sys.argv) > 1:
        test_candidate = {
            "url": sys.argv[1],
            "published_date": "2026-09-13",
            "channel": "OWNED_BLOG"
        }
        res = collect_artefact(test_candidate)
        print(f"Status: {res['status']}, URL: {res['url']}")
    else:
        print("Usage: python source_collector.py <url>")
