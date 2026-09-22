"""
Content-type-aware hashing and artefact cache management for GTM Intelligence Engine (Fix 5).
- Canonicalises URLs (strips utm_*, fragments, trailing slashes).
- Dynamic hashing based on channel (mutable forums include reply_count and length).
- Schema versioning with re-classification vs re-fetch decision logic.
- 30-day staleness verification policy.
"""

import hashlib
import urllib.parse
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Tuple, Optional

CURRENT_SCHEMA_VERSION = 3


def canonicalise_url(url: str) -> str:
    """Strip UTM parameters, query tracking params, fragments, and trailing slashes."""
    if not url:
        return ""
    parsed = urllib.parse.urlparse(url)
    # Parse query params and strip tracking / analytics
    query_params = urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
    filtered_params = [
        (k, v) for k, v in query_params
        if not (k.lower().startswith("utm_") or k.lower() in ("ref", "source", "fbclid", "gclid"))
    ]
    new_query = urllib.parse.urlencode(sorted(filtered_params))
    # Normalize path (strip trailing slash if not root)
    path = parsed.path.rstrip("/") if parsed.path != "/" else "/"
    # Reassemble without fragment
    clean = urllib.parse.urlunparse((
        parsed.scheme.lower(),
        parsed.netloc.lower(),
        path,
        parsed.params,
        new_query,
        ""  # no fragment
    ))
    return clean


def artefact_hash(artefact: Dict[str, Any]) -> str:
    """
    Compute content-type-aware SHA256 hash.
    For mutable/append-only channels (GOVERNANCE_FORUM, TELEGRAM):
      hash = sha256(canonical_url | published_date | reply_count | content_length)
    For immutable channels:
      hash = sha256(canonical_url | published_date | content_length)
    """
    raw_url = artefact.get("url") or artefact.get("canonical_url", "")
    url = canonicalise_url(raw_url)
    date = str(artefact.get("published_date") or artefact.get("date", "UNKNOWN"))
    
    # Text length detection
    text = artefact.get("text") or artefact.get("raw_text") or ""
    content_length = artefact.get("content_length") or len(text)
    
    channel = artefact.get("channel", "OTHER").upper()
    if channel in ("GOVERNANCE_FORUM", "TELEGRAM", "DISCOURSE"):
        reply_count = artefact.get("reply_count", 0)
        payload = f"{url}|{date}|{reply_count}|{content_length}"
    else:
        payload = f"{url}|{date}|{content_length}"
        
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class CacheDecision:
    SKIP = "SKIP"                     # hash present & schema_version == CURRENT
    RECLASSIFY = "RECLASSIFY"         # hash present & schema_version < CURRENT (skip fetch, re-classify)
    FETCH_AND_CLASSIFY = "FETCH_AND_CLASSIFY" # hash absent (full fetch + classify)


def evaluate_cache_status(
    h: str,
    cached_entry: Optional[Dict[str, Any]],
    current_schema_version: int = CURRENT_SCHEMA_VERSION,
) -> str:
    """Determine whether to skip, re-classify from stored raw text, or re-fetch."""
    if not cached_entry:
        return CacheDecision.FETCH_AND_CLASSIFY

    entry_version = cached_entry.get("schema_version", 1)
    if entry_version >= current_schema_version:
        return CacheDecision.SKIP
    else:
        return CacheDecision.RECLASSIFY


def is_record_stale(cached_entry: Dict[str, Any], max_age_days: int = 30) -> bool:
    """Check if record's last_verified_at is older than max_age_days."""
    ts_str = cached_entry.get("last_verified_at") or cached_entry.get("fetched_at")
    if not ts_str:
        return True
    try:
        # Parse ISO string
        dt = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        return (now - dt) > timedelta(days=max_age_days)
    except Exception:
        return True


def create_cache_record(
    h: str,
    raw_html: str,
    raw_text: str,
    canonical_url: str,
    schema_version: int = CURRENT_SCHEMA_VERSION,
) -> Dict[str, Any]:
    """Create a structured cache record storing raw artefacts."""
    now_iso = datetime.now(timezone.utc).isoformat()
    return {
        "artefact_hash": h,
        "canonical_url": canonical_url,
        "schema_version": schema_version,
        "raw_html": raw_html,
        "raw_text": raw_text,
        "content_length": len(raw_text),
        "fetched_at": now_iso,
        "last_verified_at": now_iso,
    }
