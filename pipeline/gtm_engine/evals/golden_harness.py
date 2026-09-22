"""
L2 Golden Set Evaluation Harness for GTM Intelligence Engine.
Hard constraint: golden_set.jsonl and regression_tests.jsonl NEVER enter model context.
They are read by this harness only as the ground-truth answer key.
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional


REQUIRED_WINDOW = {"start": "2026-06-02", "end": "2026-09-02"}


def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    """Load JSONL file safely."""
    records = []
    if not path.exists():
        return records
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def run_golden_eval(
    agent_output: Dict[str, Any],
    golden_records: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Run diff between agent output records and ground-truth golden set.
    Weights series precision above recall.
    Excludes or soft-scores ambiguous enum mappings.
    """
    # 1. Pinned window check
    agent_window = agent_output.get("window")
    if agent_window != REQUIRED_WINDOW:
        raise ValueError(
            f"Evaluation window mismatch! Agent window: {agent_window}, expected: {REQUIRED_WINDOW}. "
            "Window must match exactly or comparison is noise."
        )

    agent_records = agent_output.get("records", [])

    # Index by (player_id, series_name/pattern_id)
    golden_patterns = [r for r in golden_records if r.get("record_type") == "PATTERN"]
    agent_patterns = [r for r in agent_records if r.get("record_type") == "PATTERN"]

    total_golden = len(golden_patterns)
    total_agent = len(agent_patterns)

    if total_golden == 0:
        return {"error": "Golden set contains zero PATTERN records"}

    # Agreement counters
    category_matches = 0
    category_total = 0
    subcategory_matches = 0
    subcategory_total = 0
    pattern_type_matches = 0
    pattern_type_total = 0
    cadence_matches = 0
    cadence_total = 0

    # Build lookup for golden by signature or player+series
    golden_map = {}
    for g in golden_patterns:
        key = (g.get("player_id"), g.get("series_name") or g.get("pattern_template", "")[:30])
        golden_map[key] = g

    # Precision & recall counters for RECURRING_SERIES
    golden_series_keys = {
        (g.get("player_id"), g.get("series_name")): g
        for g in golden_patterns
        if g.get("pattern_type") == "RECURRING_SERIES" and g.get("series_name") not in (None, "NONE", "")
    }

    agent_series_keys = {
        (a.get("player_id"), a.get("series_name")): a
        for a in agent_patterns
        if a.get("pattern_type") == "RECURRING_SERIES" and a.get("series_name") not in (None, "NONE", "")
    }

    true_positive_series = 0
    false_positive_series = 0

    for a_key, a_rec in agent_series_keys.items():
        if a_key in golden_series_keys:
            true_positive_series += 1
        else:
            # Overclaiming one-off or non-series as a series
            false_positive_series += 1

    series_precision = (
        true_positive_series / (true_positive_series + false_positive_series)
        if (true_positive_series + false_positive_series) > 0
        else 1.0
    )

    series_recall = (
        true_positive_series / len(golden_series_keys)
        if len(golden_series_keys) > 0
        else 1.0
    )

    # Detailed field agreement
    for a_rec in agent_patterns:
        key = (a_rec.get("player_id"), a_rec.get("series_name") or a_rec.get("pattern_template", "")[:30])
        g_rec = golden_map.get(key)
        if not g_rec:
            continue

        # Check ambiguous enum mapping
        is_ambiguous = g_rec.get("enum_mapping_confidence") == "AMBIGUOUS"

        # Content category
        category_total += 1
        if a_rec.get("content_category") == g_rec.get("content_category"):
            category_matches += 1
        elif is_ambiguous:
            category_matches += 0.5  # Soft-score ambiguous mappings

        # Subcategory
        subcategory_total += 1
        if a_rec.get("subcategory") == g_rec.get("subcategory"):
            subcategory_matches += 1
        elif is_ambiguous:
            subcategory_matches += 0.5

        # Pattern type (arithmetic)
        pattern_type_total += 1
        if a_rec.get("pattern_type") == g_rec.get("pattern_type"):
            pattern_type_matches += 1

        # Cadence
        cadence_total += 1
        if a_rec.get("cadence") == g_rec.get("cadence"):
            cadence_matches += 1

    cat_agreement = category_matches / category_total if category_total > 0 else 1.0
    sub_agreement = subcategory_matches / subcategory_total if subcategory_total > 0 else 1.0
    pat_agreement = pattern_type_matches / pattern_type_total if pattern_type_total > 0 else 1.0
    cad_agreement = cadence_matches / cadence_total if cadence_total > 0 else 1.0

    return {
        "content_category_agreement": cat_agreement,   # target >= 90%
        "subcategory_agreement": sub_agreement,        # target >= 75%
        "pattern_type_agreement": pat_agreement,       # target >= 95%
        "series_recall": series_recall,                # target >= 80%
        "series_precision": series_precision,          # target >= 95% (weighted highest)
        "cadence_agreement": cad_agreement,            # target >= 85%
        "targets_met": {
            "content_category": cat_agreement >= 0.90,
            "subcategory": sub_agreement >= 0.75,
            "pattern_type": pat_agreement >= 0.95,
            "series_recall": series_recall >= 0.80,
            "series_precision": series_precision >= 0.95,
            "cadence": cad_agreement >= 0.85,
        },
    }
