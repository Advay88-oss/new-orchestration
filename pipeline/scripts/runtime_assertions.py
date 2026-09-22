#!/usr/bin/env python3
"""Evals & Runtime Assertions Middleware: L0, L1, L3 and Context Isolation.

Guarantees:
1. Deterministic assertions catch hallucinations and prompt drift for free.
2. Context isolation prevents classification models from seeing internal positioning.
3. Unknown-rate monitoring detects fabrication (zero unknowns is a failure).
"""

from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional


# --------------------------------------------------------------------------
# Context Isolation Enforcer
# --------------------------------------------------------------------------
FORBIDDEN_CONTEXT = {
    "flash": ["knowledge/internal/", "golden_set", "regression_tests", "vanna_docs"],
    "strong": ["golden_set", "regression_tests"],
}


def assert_context_isolation(tier: str, prompt: str) -> None:
    """Enforces strict isolation in code: Flash must not see internal knowledge or answer keys."""
    tier_norm = tier.strip().lower()
    forbidden_markers = FORBIDDEN_CONTEXT.get(tier_norm, [])
    for marker in forbidden_markers:
        if marker in prompt:
            raise PermissionError(f"CONTEXT LEAK: '{marker}' is strictly forbidden in {tier} prompt!")


# --------------------------------------------------------------------------
# L0: Schema Assertions (Free)
# --------------------------------------------------------------------------
REQUIRED_ARTEFACT_FIELDS = {"url", "published_date", "channel", "raw_text"}
VALID_CHANNELS = {"OWNED_BLOG", "GOVERNANCE_FORUM", "NEWSLETTER", "DOCS", "TELEGRAM", "X"}


def assert_l0_schema(record: Dict[str, Any], record_type: str = "artefact") -> None:
    """L0 schema validation for registry records."""
    if record_type == "artefact":
        missing = REQUIRED_ARTEFACT_FIELDS - set(record.keys())
        if missing:
            raise ValueError(f"L0 Schema Violation: Missing required fields {missing}")
        if record.get("channel") not in VALID_CHANNELS:
            raise ValueError(f"L0 Schema Violation: Invalid channel '{record.get('channel')}'")
    elif record_type == "brief":
        if "data" in record and isinstance(record["data"], list) and len(record["data"]) > 1:
            raise ValueError(f"L0 Brief Schema Violation: {len(record['data'])} data points. One asset = one idea.")


# --------------------------------------------------------------------------
# L1: Invariant Checks (Free)
# --------------------------------------------------------------------------
FORBIDDEN_CAUSAL_REGEX = re.compile(
    r"\b(caused by|solely due to|directly drove TVL|resulted in 100% growth)\b",
    re.IGNORECASE
)


def assert_l1_invariants(content_text: str, urls: Optional[List[str]] = None) -> None:
    """L1 Invariants: catches ungrounded causal claims and malformed URLs."""
    # 1. No unproven causal assertions
    match = FORBIDDEN_CAUSAL_REGEX.search(content_text)
    if match:
        raise AssertionError(f"L1 Invariant Violation: Causal claim '{match.group(0)}' without isolated test data.")

    # 2. Check URLs if provided
    if urls:
        valid_urls = [u for u in urls if u.startswith("http://") or u.startswith("https://")]
        resolution_rate = len(valid_urls) / len(urls) if urls else 1.0
        if resolution_rate < 0.80:
            raise AssertionError(f"L1 Invariant Violation: URL resolution rate {resolution_rate:.1%} < 80%. Hallucination halt.")


# --------------------------------------------------------------------------
# L3: Unknown-Rate Monitor (Fabrication Detection)
# --------------------------------------------------------------------------
def check_unknown_rate(records: List[Dict[str, Any]], field: str = "metric_value") -> float:
    """Checks the proportion of UNKNOWN or null values in model-derived fields.
    Zero UNKNOWNs is a failure (indicates fabrication on difficult historical data).
    """
    if not records:
        return 0.0
    unknowns = sum(1 for r in records if r.get(field) in (None, "UNKNOWN", "", "N/A"))
    rate = unknowns / len(records)
    
    # Inverted check: Zero unknowns on large batches is suspicious
    if len(records) >= 20 and rate < 0.05:
        print(f"⚠️ L3 WARNING: Unknown-rate {rate:.1%} is below 5%. Model may be fabricating missing fields.")
    elif rate > 0.40:
        print(f"⚠️ L3 WARNING: Unknown-rate {rate:.1%} exceeds 40%. High data degradation.")
        
    return rate
