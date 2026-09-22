"""
Contradictions interceptor for GTM Intelligence Engine (Law L11).
Cross-phase verification: detects conflicts between newly emitted records and PRIOR_STATE.
Emits CONTRADICTION records with resolution: "PENDING_HUMAN".
Never silently overwrites, never averages.
"""

from typing import List, Dict, Any, Tuple, Optional, Callable
import json
import logging

logger = logging.getLogger("gtm_engine.contradictions")


def materially_differs(new_record: Dict[str, Any], prior_record: Dict[str, Any]) -> bool:
    """
    Determine if new_record conflicts with prior_record on key substantive fields.
    Ignore metadata/timestamp differences.
    """
    # Key fields to compare by record_type
    key_fields = [
        "pattern_type",
        "cadence",
        "current_positioning",
        "early_positioning",
        "dominant_objection_derived",
        "hook_type",
        "proof_type",
        "evidence_tier",
    ]
    
    for field in key_fields:
        if field in new_record and field in prior_record:
            val_new = new_record[field]
            val_prior = prior_record[field]
            if val_new != "UNKNOWN" and val_prior != "UNKNOWN" and val_new != val_prior:
                return True
                
    # Subcategory check within same category
    if new_record.get("content_category") == prior_record.get("content_category"):
        sub_new = new_record.get("subcategory")
        sub_prior = prior_record.get("subcategory")
        if sub_new and sub_prior and sub_new != sub_prior and sub_new != "UNKNOWN" and sub_prior != "UNKNOWN":
            return True

    return False


def create_contradiction_record(
    new_record: Dict[str, Any],
    prior_record: Dict[str, Any],
    conflict_summary: str,
    phase: int,
) -> Dict[str, Any]:
    """Emit a canonical CONTRADICTION record."""
    return {
        "record_type": "CONTRADICTION",
        "phase": phase,
        "player_id": new_record.get("player_id") or prior_record.get("player_id"),
        "field_or_topic": conflict_summary,
        "prior_state": {
            "record_type": prior_record.get("record_type"),
            "values": {k: v for k, v in prior_record.items() if k in ["pattern_type", "cadence", "content_category", "subcategory", "current_positioning", "source_url"]},
        },
        "new_state": {
            "record_type": new_record.get("record_type"),
            "values": {k: v for k, v in new_record.items() if k in ["pattern_type", "cadence", "content_category", "subcategory", "current_positioning", "source_url"]},
        },
        "resolution": "PENDING_HUMAN",
        "status": "UNRESOLVED",
    }


def check_contradictions(
    new_records: List[Dict[str, Any]],
    prior_state: List[Dict[str, Any]],
    phase: int,
    judge_fn: Optional[Callable[[List[Tuple[Dict[str, Any], Dict[str, Any]]]], List[Dict[str, Any]]]] = None,
) -> List[Dict[str, Any]]:
    """
    Batched per phase.
    Finds conflicting candidates between new_records and prior_state.
    If judge_fn is provided (Strong-tier model), delegates semantic judgment.
    Otherwise uses deterministic rule-based candidate filtering.
    """
    if not new_records or not prior_state:
        return []

    candidates: List[Tuple[Dict[str, Any], Dict[str, Any]]] = []

    for n in new_records:
        player_n = n.get("player_id")
        if not player_n:
            continue
        for p in prior_state:
            player_p = p.get("player_id")
            if player_n != player_p:
                continue

            # Compare if both are about the same content category or positioning
            same_cat = n.get("content_category") and n.get("content_category") == p.get("content_category")
            same_type = n.get("record_type") == p.get("record_type")

            if (same_cat or same_type) and materially_differs(n, p):
                candidates.append((n, p))

    if not candidates:
        return []

    # If Strong-tier model judge is provided, execute single batched call
    if judge_fn is not None:
        try:
            return judge_fn(candidates)
        except Exception as e:
            logger.error(f"Strong-tier contradiction judge call failed: {e}")
            # Fall back to deterministic generation
            pass

    # Deterministic fallback record generation
    contradictions = []
    for n, p in candidates:
        summary = f"Conflict on player '{n.get('player_id')}' in record_type '{n.get('record_type')}'"
        contradictions.append(create_contradiction_record(n, p, summary, phase))

    return contradictions
