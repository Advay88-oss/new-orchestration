"""
Tier 0b: Fallible Network Collector with Retries, Disk Cache, and PARTIAL Degradation.
Separated from Tier 0 (pure deterministic code).
Handles external HTTP probes, API requests, and rate-limiting gracefully.
"""

import time
import json
import hashlib
import urllib.request
import urllib.error
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

REPO_ROOT = Path("D:/new orchestration")
CACHE_DIR = REPO_ROOT / "pipeline" / "gtm_engine" / "registry" / "cache" / "network"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

DEFAULT_TIMEOUT = 10.0
MAX_RETRIES = 3
INITIAL_BACKOFF = 1.0


def _get_cache_path(url: str) -> Path:
    url_hash = hashlib.sha256(url.encode("utf-8")).hexdigest()
    return CACHE_DIR / f"{url_hash}.json"


def fetch_with_retry_and_cache(
    url: str,
    headers: Optional[Dict[str, str]] = None,
    timeout: float = DEFAULT_TIMEOUT,
    max_retries: int = MAX_RETRIES,
    use_cache: bool = True,
    cache_ttl_hours: int = 24
) -> Dict[str, Any]:
    """
    Fetch URL with exponential backoff retry and local disk caching.
    Propagates status: 'SUCCESS' | 'PARTIAL' | 'FAILED' | 'CACHED'.
    """
    cache_file = _get_cache_path(url)
    
    # 1. Check disk cache
    if use_cache and cache_file.exists():
        try:
            cached_data = json.loads(cache_file.read_text(encoding="utf-8"))
            cached_at = cached_data.get("cached_at", 0)
            if time.time() - cached_at < cache_ttl_hours * 3600:
                return {
                    "status": "CACHED",
                    "url": url,
                    "status_code": cached_data.get("status_code", 200),
                    "data": cached_data.get("data", ""),
                    "is_partial": False,
                    "error": None
                }
        except Exception:
            pass

    # 2. Network execution with retries
    req_headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) GTMIntelligence/1.0"}
    if headers:
        req_headers.update(headers)

    req = urllib.request.Request(url, headers=req_headers)
    backoff = INITIAL_BACKOFF
    last_error = None

    for attempt in range(max_retries):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                raw_bytes = resp.read()
                data_str = raw_bytes.decode("utf-8", errors="ignore")
                status_code = resp.status
                
                # Cache response
                cache_payload = {
                    "cached_at": time.time(),
                    "url": url,
                    "status_code": status_code,
                    "data": data_str
                }
                cache_file.write_text(json.dumps(cache_payload), encoding="utf-8")

                return {
                    "status": "SUCCESS",
                    "url": url,
                    "status_code": status_code,
                    "data": data_str,
                    "is_partial": False,
                    "error": None
                }
        except urllib.error.HTTPError as e:
            last_error = f"HTTP {e.code}: {e.reason}"
            if e.code in (429, 500, 502, 503, 504):
                time.sleep(backoff)
                backoff *= 2.0
            else:
                # Fatal client error (e.g. 404, 403)
                break
        except Exception as e:
            last_error = str(e)
            time.sleep(backoff)
            backoff *= 2.0

    # 3. Graceful degradation: Return PARTIAL if stale cache exists, otherwise FAILED
    if cache_file.exists():
        try:
            stale = json.loads(cache_file.read_text(encoding="utf-8"))
            return {
                "status": "PARTIAL",
                "url": url,
                "status_code": stale.get("status_code", 200),
                "data": stale.get("data", ""),
                "is_partial": True,
                "error": f"Live fetch failed ({last_error}). Using stale cached data."
            }
        except Exception:
            pass

    return {
        "status": "FAILED",
        "url": url,
        "status_code": None,
        "data": "",
        "is_partial": True,
        "error": last_error
    }
