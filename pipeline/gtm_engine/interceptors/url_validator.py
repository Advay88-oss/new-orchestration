"""
Split URL validation for GTM Intelligence Engine (Fix 4).
- Record-level: Quarantines records with confirmed dead URLs without dropping valid records.
- Run-level: Circuit breaker that halts the run if resolution rate drops below 80%.
- Concurrency capped async verification with 5s timeout.
- Timeouts treated as UNKNOWN/transient, NOT confirmed dead.
"""

import asyncio
import urllib.request
import urllib.error
from typing import List, Dict, Any, Tuple, Set
import logging

logger = logging.getLogger("gtm_engine.url_validator")


class URLCheckResult:
    RESOLVED = "RESOLVED"
    DEAD = "DEAD"
    UNKNOWN = "UNKNOWN"  # timeouts, connection drops, SSL errors


def _check_url_sync(url: str, timeout: float = 5.0) -> Tuple[str, int]:
    """Synchronous HTTP HEAD check with GET fallback."""
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) GTMIntelligence/1.0"}
    try:
        req = urllib.request.Request(url, headers=headers, method="HEAD")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            code = resp.getcode()
            if 200 <= code < 400:
                return URLCheckResult.RESOLVED, code
            return URLCheckResult.DEAD, code
    except urllib.error.HTTPError as e:
        # Some servers block HEAD, try small range GET before declaring dead
        if e.code in (403, 405):
            try:
                get_req = urllib.request.Request(url, headers=headers, method="GET")
                with urllib.request.urlopen(get_req, timeout=timeout) as get_resp:
                    get_code = get_resp.getcode()
                    if 200 <= get_code < 400:
                        return URLCheckResult.RESOLVED, get_code
            except Exception:
                pass
        return URLCheckResult.DEAD, e.code
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        # Network errors, timeouts, or DNS resolution timeouts are UNKNOWN, NOT confirmed dead
        return URLCheckResult.UNKNOWN, 0
    except Exception:
        return URLCheckResult.UNKNOWN, 0


async def check_url_async(
    url: str,
    semaphore: asyncio.Semaphore,
    timeout: float = 5.0,
) -> Tuple[str, str, int]:
    """Check a single URL asynchronously with concurrency control."""
    loop = asyncio.get_running_loop()
    async with semaphore:
        status, code = await loop.run_in_executor(None, _check_url_sync, url, timeout)
        return url, status, code


async def validate_records_urls(
    records: List[Dict[str, Any]],
    concurrency_limit: int = 10,
    timeout: float = 5.0,
    run_threshold: float = 0.80,
) -> Dict[str, Any]:
    """
    Validate all URLs across all records.
    Returns:
    {
        "clean_records": [...],
        "quarantined_records": [...],
        "metrics": {
            "total_urls": int,
            "resolved_count": int,
            "dead_count": int,
            "unknown_count": int,
            "resolution_rate": float,
        },
        "should_halt_run": bool,
        "halt_reason": str | None
    }
    """
    # 1. Collect all distinct URLs
    url_to_records: Dict[str, List[int]] = {}
    for idx, record in enumerate(records):
        urls: Set[str] = set()
        # Single source_url field
        s_url = record.get("source_url")
        if s_url and s_url not in ("UNKNOWN", "NONE", ""):
            urls.add(s_url)
        # Array of source_urls
        for u in record.get("source_urls", []):
            if u and u not in ("UNKNOWN", "NONE", ""):
                urls.add(u)
        # Products list URLs
        for prod in record.get("products", []):
            pu = prod.get("source_url")
            if pu and pu not in ("UNKNOWN", "NONE", ""):
                urls.add(pu)

        for u in urls:
            url_to_records.setdefault(u, []).append(idx)

    total_urls = len(url_to_records)
    if total_urls == 0:
        return {
            "clean_records": records,
            "quarantined_records": [],
            "metrics": {
                "total_urls": 0,
                "resolved_count": 0,
                "dead_count": 0,
                "unknown_count": 0,
                "resolution_rate": 1.0,
            },
            "should_halt_run": False,
            "halt_reason": None,
        }

    # 2. Check all URLs concurrently with semaphore
    semaphore = asyncio.Semaphore(concurrency_limit)
    tasks = [check_url_async(u, semaphore, timeout) for u in url_to_records.keys()]
    results = await asyncio.gather(*tasks)

    url_status_map: Dict[str, str] = {}
    resolved_count = 0
    dead_count = 0
    unknown_count = 0

    for url, status, code in results:
        url_status_map[url] = status
        if status == URLCheckResult.RESOLVED:
            resolved_count += 1
        elif status == URLCheckResult.DEAD:
            dead_count += 1
        elif status == URLCheckResult.UNKNOWN:
            unknown_count += 1

    # In resolution rate calculation:
    # We measure resolved / total_urls. Timeouts are non-resolutions but not dead.
    resolution_rate = resolved_count / total_urls if total_urls > 0 else 1.0

    # 3. Record-level quarantine
    clean_records: List[Dict[str, Any]] = []
    quarantined_records: List[Dict[str, Any]] = []

    for idx, record in enumerate(records):
        # Find if this record has any confirmed dead URLs
        rec_urls = [u for u, idxs in url_to_records.items() if idx in idxs]
        dead_for_record = [u for u in rec_urls if url_status_map.get(u) == URLCheckResult.DEAD]

        if dead_for_record:
            rec_copy = dict(record)
            rec_copy["evidence_tier"] = "UNKNOWN"
            rec_copy["quarantine_reason"] = f"unresolvable: {dead_for_record}"
            quarantined_records.append(rec_copy)
        else:
            clean_records.append(record)

    # 4. Run-level circuit breaker
    should_halt = False
    halt_reason = None
    if total_urls >= 5 and resolution_rate < run_threshold:
        should_halt = True
        halt_reason = (
            f"URL resolution rate {resolution_rate:.1%} is below {run_threshold:.0%} threshold "
            f"({resolved_count}/{total_urls} resolved, {dead_count} dead). "
            f"Halting run: model may be hallucinating sources."
        )

    return {
        "clean_records": clean_records,
        "quarantined_records": quarantined_records,
        "metrics": {
            "total_urls": total_urls,
            "resolved_count": resolved_count,
            "dead_count": dead_count,
            "unknown_count": unknown_count,
            "resolution_rate": resolution_rate,
        },
        "should_halt_run": should_halt,
        "halt_reason": halt_reason,
    }


def validate_records_urls_sync(
    records: List[Dict[str, Any]],
    concurrency_limit: int = 10,
    timeout: float = 5.0,
    run_threshold: float = 0.80,
) -> Dict[str, Any]:
    """Synchronous helper that runs validate_records_urls in an event loop."""
    return asyncio.run(validate_records_urls(records, concurrency_limit, timeout, run_threshold))
