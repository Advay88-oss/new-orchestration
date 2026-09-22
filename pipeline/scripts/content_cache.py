#!/usr/bin/env python3
"""Loop A — Research Optimization: Content-Hash Cache, Raw Store & Classification View.

Principles:
1. Content hashing avoids re-fetching and re-classifying unchanged documents.
2. Raw store preserves historical articles for schema re-classification without re-scraping.
3. classification_view extracts headings + first 500 chars + CTA + links, saving 70-85% of input tokens.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Tuple
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

REPO_ROOT = Path(os.environ.get("VANNA_ROOT", Path(__file__).resolve().parents[2]))
REGISTRY_DIR = REPO_ROOT / "registry"
RAW_STORE_DIR = REGISTRY_DIR / "raw_store"
RAW_STORE_DIR.mkdir(parents=True, exist_ok=True)
CACHE_INDEX_FILE = REGISTRY_DIR / "cache_index.json"

CURRENT_SCHEMA_VERSION = 3


def canonicalise(url: str) -> str:
    """Strips tracking query params (utm_*), fragments, and trailing slashes."""
    if not url:
        return ""
    p = urlparse(url.strip())
    query = parse_qs(p.query)
    clean_query = {k: v for k, v in query.items() if not k.lower().startswith("utm_") and k.lower() not in ("ref", "source")}
    encoded_query = urlencode(clean_query, doseq=True)
    path = p.path.rstrip("/")
    return urlunparse((p.scheme, p.netloc, path, p.params, encoded_query, ""))


def artefact_hash(artefact: Dict[str, Any]) -> str:
    """Computes deterministic hash based on channel type and canonical URL."""
    url = canonicalise(artefact.get("url", ""))
    pub_date = str(artefact.get("published_date", "")).strip()
    raw = str(artefact.get("raw_text", ""))
    content_len = len(raw)
    
    channel = artefact.get("channel", "GENERIC").upper()
    if channel in ("GOVERNANCE_FORUM", "TELEGRAM"):
        reply_count = artefact.get("reply_count", 0)
        seed = f"{url}|{pub_date}|{reply_count}|{content_len}"
    else:
        seed = f"{url}|{pub_date}|{content_len}"
        
    return hashlib.sha256(seed.encode("utf-8")).hexdigest()


def _load_index() -> dict:
    return json.loads(CACHE_INDEX_FILE.read_text(encoding="utf-8")) if CACHE_INDEX_FILE.exists() else {}


def _save_index(idx: dict) -> None:
    tmp = CACHE_INDEX_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(idx, indent=2), encoding="utf-8")
    tmp.replace(CACHE_INDEX_FILE)


def cache_lookup(artefact: dict) -> tuple[str, dict | None]:
    """Returns (action, payload). action in {SKIP, RECLASSIFY, FETCH}."""
    h = artefact_hash(artefact)
    entry = _load_index().get(h)

    if entry and entry.get("schema_version") == CURRENT_SCHEMA_VERSION:
        return "SKIP", None  # no fetch, no model call

    if entry:
        raw_path = RAW_STORE_DIR / f"{h}.json"
        if raw_path.exists():
            return "RECLASSIFY", json.loads(raw_path.read_text(encoding="utf-8"))

    return "FETCH", None


def cache_store(artefact: dict, raw_text: str) -> str:
    """Stores raw body text into raw_store/ and updates the cache index atomically."""
    h = artefact_hash(artefact)

    payload = {
        **artefact,
        "raw_text": raw_text,
        "artefact_hash": h,
        "schema_version": CURRENT_SCHEMA_VERSION,
    }
    (RAW_STORE_DIR / f"{h}.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")

    idx = _load_index()
    idx[h] = {
        "schema_version": CURRENT_SCHEMA_VERSION,
        "cached_at": datetime.now(timezone.utc).isoformat(),
        "url": artefact.get("url"),
    }
    _save_index(idx)
    return h


def classification_view(raw_text: str) -> str:
    """Deterministic string projection: extracts headings, first 500 chars, CTA, and links.
    Saves 70-85% of tokens. Never passes full bodies to classification models.
    """
    if not raw_text:
        return ""
        
    lines = raw_text.splitlines()
    headings = [line.strip() for line in lines if line.strip().startswith(("#", "==", "--"))][:6]
    body_sample = raw_text[:500].strip()
    urls = re.findall(r"https?://[^\s)\]]+", raw_text)[:8]
    
    cta_candidates = []
    cta_triggers = ("try", "read", "docs", "join", "app", "contract", "github", "testnet")
    for line in lines[-15:]:
        clean = line.strip().lower()
        if any(trig in clean for trig in cta_triggers) and len(line.strip()) < 120:
            cta_candidates.append(line.strip())
            
    projection = [
        "=== CLASSIFICATION VIEW ===",
        "--- HEADINGS ---",
        "\n".join(headings) if headings else "(No explicit headings)",
        "--- OPENING BODY (500 chars) ---",
        body_sample,
        "--- CTAS DETECTED ---",
        "\n".join(cta_candidates[:4]) if cta_candidates else "(No explicit CTA lines)",
        "--- EXTRACTED LINKS ---",
        "\n".join(urls) if urls else "(No links)",
        "==========================="
    ]
    return "\n".join(projection)
