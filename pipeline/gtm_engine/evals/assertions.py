"""
GTM Intelligence Engine - Multi-layer Assertion Suite (L0, L1, L3).
Deterministic before probabilistic: all checks run 100% in Python code.
"""

import re
import json
from typing import Dict, Any, List, Set, Tuple, Optional
from pipeline.gtm_engine.interceptors.url_validator import validate_records_urls_sync
from pipeline.gtm_engine.interceptors.promotion import VALID_PATTERN_TYPES

# -----------------------------------------------------------------------------
# Canonical Enums from System Prompt
# -----------------------------------------------------------------------------

MARKET_CATEGORIES = {
    "LENDING", "SPOT_AMM_DEX", "DEX_AGGREGATOR", "PERPETUALS", "OPTIONS_DERIVATIVES",
    "LIQUID_STAKING", "RESTAKING", "YIELD", "YIELD_TRADING", "STABLECOINS",
    "SYNTHETIC_DOLLAR", "BRIDGES", "CROSS_CHAIN", "RWA", "RWA_LENDING",
    "BASIS_TRADING", "PREDICTION_MARKETS", "ASSET_MANAGEMENT", "BTCFI",
    "MEV_BLOCK_BUILDING", "CDP", "OTHER",
}

SELECTION_BUCKETS = {
    "MARKET_LEADER", "FAST_GROWING", "MARKETING_LEADER", "CATEGORY_INNOVATOR", "RESEARCH_RELEVANT",
}

CONTENT_CATEGORIES = {
    "PRODUCT", "ECOSYSTEM", "MARKET_INTELLIGENCE", "METRICS_PROOF", "EDUCATION",
    "NARRATIVE_THESIS", "TOKEN_ECONOMICS", "GOVERNANCE", "TRUST_RISK",
    "FOUNDER_HUMAN", "COMMUNITY", "CAMPAIGN", "OTHER",
}

VALID_SUBCATEGORIES = {
    "PRODUCT": {
        "NEW_PRODUCT", "NEW_FEATURE", "NEW_CHAIN", "NEW_ASSET", "NEW_MARKET",
        "NEW_CAPABILITY", "PRODUCT_UPGRADE", "PRODUCT_TUTORIAL",
    },
    "ECOSYSTEM": {
        "INTEGRATION", "PARTNERSHIP", "PARTNER_SPOTLIGHT", "ECOSYSTEM_MILESTONE",
        "BUILDER_ANNOUNCEMENT", "CROSS_PROMOTION",
    },
    "MARKET_INTELLIGENCE": {
        "MARKET_UPDATE", "WEEKLY_REPORT", "DAILY_DATA", "ASSET_ANALYSIS",
        "TRADER_POSITIONING", "MARKET_THESIS",
    },
    "METRICS_PROOF": {
        "TVL_MILESTONE", "VOLUME_MILESTONE", "USERS", "DEPOSITS", "REVENUE",
        "GROWTH", "PERFORMANCE", "ADOPTION",
    },
    "EDUCATION": {
        "BEGINNER", "PRODUCT_EDU", "CATEGORY_EDU", "STRATEGY_EDU", "TECHNICAL_EDU", "HOW_IT_WORKS",
    },
    "NARRATIVE_THESIS": {
        "MARKET_PROBLEM", "INDUSTRY_TREND", "FUTURE_THESIS", "CATEGORY_CREATION", "POSITIONING",
    },
    "TOKEN_ECONOMICS": {
        "TOKEN_UPDATE", "BUYBACK", "BURN", "STAKING", "GOVERNANCE_ECONOMICS", "INCENTIVES",
    },
    "GOVERNANCE": {
        "PROPOSAL", "VOTE", "GOVERNANCE_UPDATE", "TREASURY", "DECISION",
    },
    "TRUST_RISK": {
        "SECURITY", "AUDIT", "INCIDENT", "RISK_UPDATE", "TRANSPARENCY", "PROOF_OF_RESERVES",
    },
    "FOUNDER_HUMAN": {
        "FOUNDER_THESIS", "FOUNDER_COMMENTARY", "INTERVIEW", "PODCAST", "EVENT", "PERSONAL_AMPLIFICATION",
    },
    "COMMUNITY": {
        "COMMUNITY_SPOTLIGHT", "UGC", "MEME", "AMA", "CONTEST", "COMMUNITY_CALL",
    },
    "CAMPAIGN": {
        "PRODUCT_CAMPAIGN", "INCENTIVE_CAMPAIGN", "QUEST", "TRADING_COMPETITION",
        "SEASONAL", "LAUNCH_CAMPAIGN", "NARRATIVE_CAMPAIGN",
    },
    "OTHER": {"OTHER"},
}

CADENCES = {
    "daily", "weekly", "biweekly", "monthly", "quarterly", "annual",
    "event_triggered", "per_partner", "per_asset", "continuous", "periodic", "UNKNOWN",
}

PURPOSES = {
    "AWARENESS", "ACTIVATION", "ACQUISITION", "RETENTION", "TRUST", "AUTHORITY",
    "SOCIAL_PROOF", "LEGITIMACY", "EDUCATION", "ENGAGEMENT", "CONVERSION", "REACTIVATION",
}

CTAS = {
    "USE_PRODUCT", "DEPOSIT", "BORROW", "TRADE", "MINT", "STAKE", "LP", "VOTE",
    "SUBSCRIBE", "READ", "APPLY", "INTEGRATE", "CONTACT", "PARTICIPATE", "AMPLIFY", "NONE", "IMPLICIT",
}

CHANNELS = {
    "OWNED_BLOG", "GOVERNANCE_FORUM", "NEWSLETTER", "DOCS", "TELEGRAM", "X",
    "PODCAST", "PRESS", "APP_STORE", "OTHER",
}

EVIDENCE_TIERS = {"OBSERVED", "INFERRED", "UNKNOWN"}

REQUIRED_ENVELOPE_FIELDS = [
    "phase", "scope", "status", "records", "unknowns", "contradictions",
    "warnings", "sources_visited", "next_phase_ready", "blocker",
]

CAUSAL_REGEX = re.compile(
    r"\b(drove|caused|resulted in|led to \d|increased .*? by|boosted .*? by)\b",
    re.IGNORECASE,
)


class AssertionViolation:
    def __init__(self, layer: str, rule: str, message: str, record: Optional[Dict[str, Any]] = None):
        self.layer = layer
        self.rule = rule
        self.message = message
        self.record = record

    def to_dict(self) -> Dict[str, Any]:
        return {
            "layer": self.layer,
            "rule": self.rule,
            "message": self.message,
            "record_type": self.record.get("record_type") if self.record else None,
        }

    def __repr__(self):
        return f"[{self.layer}] {self.rule}: {self.message}"


# -----------------------------------------------------------------------------
# Layer 0 · Schema Validation (Free)
# -----------------------------------------------------------------------------

def validate_l0_schema(envelope: Dict[str, Any]) -> List[AssertionViolation]:
    """Validate JSON envelope, required fields, enum validity, and L4 cadence isolation."""
    violations: List[AssertionViolation] = []

    # 1. Envelope required fields
    for field in REQUIRED_ENVELOPE_FIELDS:
        if field not in envelope:
            violations.append(AssertionViolation("L0", "ENVELOPE_FIELD_MISSING", f"Missing envelope field '{field}'"))

    if envelope.get("status") not in ("COMPLETE", "PARTIAL", "BLOCKED"):
        violations.append(AssertionViolation("L0", "INVALID_STATUS", f"Invalid status: '{envelope.get('status')}'"))

    records = envelope.get("records", [])
    if not isinstance(records, list):
        violations.append(AssertionViolation("L0", "RECORDS_NOT_LIST", "envelope['records'] must be a list"))
        return violations

    for idx, r in enumerate(records):
        if not isinstance(r, dict):
            violations.append(AssertionViolation("L0", "RECORD_NOT_DICT", f"Record at index {idx} is not an object"))
            continue

        r_type = r.get("record_type")
        if not r_type:
            violations.append(AssertionViolation("L0", "RECORD_TYPE_MISSING", f"Record at index {idx} missing 'record_type'"))
            continue

        # Check evidence_tier enum
        if "evidence_tier" in r and r["evidence_tier"] not in EVIDENCE_TIERS:
            violations.append(AssertionViolation("L0", "INVALID_EVIDENCE_TIER", f"Record {idx} invalid evidence_tier: {r['evidence_tier']}", r))

        # Check market_category
        cat = r.get("category")
        if cat and cat not in MARKET_CATEGORIES:
            violations.append(AssertionViolation("L0", "INVALID_MARKET_CATEGORY", f"Invalid market_category: '{cat}'", r))

        # Check selection_bucket
        bucket = r.get("selection_bucket")
        if bucket and bucket not in SELECTION_BUCKETS:
            violations.append(AssertionViolation("L0", "INVALID_SELECTION_BUCKET", f"Invalid selection_bucket: '{bucket}'", r))

        # Check content_category & L4 violation (cadence in category)
        c_cat = r.get("content_category")
        if c_cat:
            if c_cat in CADENCES:
                violations.append(AssertionViolation(
                    "L0", "L4_CADENCE_IN_CONTENT_CATEGORY",
                    f"Law L4 violation: cadence value '{c_cat}' used as content_category",
                    r
                ))
            elif c_cat not in CONTENT_CATEGORIES:
                violations.append(AssertionViolation("L0", "INVALID_CONTENT_CATEGORY", f"Invalid content_category: '{c_cat}'", r))

        # Check subcategory validity against parent
        sub_cat = r.get("subcategory")
        if sub_cat and c_cat in VALID_SUBCATEGORIES:
            if sub_cat not in VALID_SUBCATEGORIES[c_cat]:
                violations.append(AssertionViolation(
                    "L0", "INVALID_SUBCATEGORY",
                    f"Subcategory '{sub_cat}' is not valid for parent category '{c_cat}'",
                    r
                ))

        # Check cadence attribute
        cadence = r.get("cadence")
        if cadence and cadence not in CADENCES:
            violations.append(AssertionViolation("L0", "INVALID_CADENCE", f"Invalid cadence: '{cadence}'", r))

        # Check pattern_type
        p_type = r.get("pattern_type")
        if p_type and p_type not in VALID_PATTERN_TYPES:
            violations.append(AssertionViolation("L0", "INVALID_PATTERN_TYPE", f"Invalid pattern_type: '{p_type}'", r))

        # Check purpose
        for purp in r.get("purpose", []):
            if purp not in PURPOSES:
                violations.append(AssertionViolation("L0", "INVALID_PURPOSE", f"Invalid purpose: '{purp}'", r))

        # Check cta
        cta = r.get("cta")
        if cta and cta not in CTAS:
            violations.append(AssertionViolation("L0", "INVALID_CTA", f"Invalid cta: '{cta}'", r))

        # Check channel
        ch = r.get("channel")
        if ch and ch not in CHANNELS:
            violations.append(AssertionViolation("L0", "INVALID_CHANNEL", f"Invalid channel: '{ch}'", r))

    return violations


# -----------------------------------------------------------------------------
# Layer 1 · Numeric Truth Verification (Code-first invariant)
# -----------------------------------------------------------------------------

def validate_l1_numerics(
    records: List[Dict[str, Any]],
    truth_categories: Optional[Dict[str, Dict[str, Any]]] = None,
    tolerance: float = 0.05,
) -> List[AssertionViolation]:
    """
    Cross-check every model-adjacent figure against the code snapshot.
    Deterministic, free, and catches the failure mode URL checks miss.
    """
    if not truth_categories:
        return []

    violations: List[AssertionViolation] = []

    for idx, r in enumerate(records):
        if r.get("record_type") != "MARKET_CATEGORY":
            continue

        cat_raw = r.get("category_raw")
        if not cat_raw:
            violations.append(AssertionViolation(
                "L1", "CATEGORY_RAW_MISSING",
                f"Record {idx} missing 'category_raw'. Required for deterministic verification.",
                r
            ))
            continue

        if cat_raw not in truth_categories:
            violations.append(AssertionViolation(
                "L1", "CATEGORY_NOT_IN_API",
                f"Category '{cat_raw}' was not found in live aggregator API snapshot.",
                r
            ))
            continue

        actual_stats = truth_categories[cat_raw]
        for field in ("tvl_usd", "protocol_count"):
            claimed = r.get(field)
            actual = actual_stats.get(field)
            if claimed in (None, "UNKNOWN") or actual is None:
                continue
            drift = abs(claimed - actual) / max(actual, 1)
            if drift > tolerance:
                violations.append(AssertionViolation(
                    "L1", "NUMERIC_FABRICATION",
                    f"Numeric drift on category '{cat_raw}' field '{field}': claimed={claimed}, actual={actual} (drift {drift:.1%}). Must come from code.",
                    r
                ))

    return violations

def validate_l1_invariants(
    envelope: Dict[str, Any],
    known_players: Optional[Set[str]] = None,
    known_artefacts: Optional[Set[str]] = None,
    check_live_urls: bool = True,
) -> Tuple[List[AssertionViolation], Dict[str, Any]]:
    """
    Validate invariants:
    - Evidence discipline (OBSERVED requires source_url; INFERRED requires inference_basis)
    - URL resolution & circuit breaker (Fix 4)
    - Promotion arithmetic consistency (L5)
    - Orphan record checks
    - No causal claims regex (L12)
    """
    violations: List[AssertionViolation] = []
    records = envelope.get("records", [])
    known_players = known_players or set()
    known_artefacts = known_artefacts or set()

    for idx, r in enumerate(records):
        r_str = json.dumps(r)

        # 1. No causal claims (L12)
        causal_match = CAUSAL_REGEX.search(r_str)
        if causal_match:
            violations.append(AssertionViolation(
                "L1", "CAUSAL_CLAIM_FORBIDDEN",
                f"Law L12 violation: causal phrase '{causal_match.group(0)}' found in record {idx}",
                r
            ))

        # 2. Evidence discipline (L3)
        ev_tier = r.get("evidence_tier")
        if ev_tier == "OBSERVED":
            s_url = r.get("source_url")
            s_urls = r.get("source_urls", [])
            has_url = (s_url and s_url not in ("UNKNOWN", "NONE", "")) or bool(s_urls)
            if not has_url:
                violations.append(AssertionViolation(
                    "L1", "OBSERVED_WITHOUT_URL",
                    f"Record {idx} has tier OBSERVED but no valid source_url",
                    r
                ))
        elif ev_tier == "INFERRED":
            if not r.get("inference_basis"):
                violations.append(AssertionViolation(
                    "L1", "INFERRED_WITHOUT_BASIS",
                    f"Record {idx} has tier INFERRED but missing inference_basis",
                    r
                ))

        # 3. Promotion arithmetic (L5)
        p_type = r.get("pattern_type")
        inst_count = r.get("instance_count")
        if inst_count is not None:
            if p_type == "ONE_OFF" and inst_count != 1:
                violations.append(AssertionViolation(
                    "L1", "PROMOTION_ARITHMETIC_ERROR",
                    f"ONE_OFF must have instance_count == 1, got {inst_count}",
                    r
                ))
            elif p_type == "REPEATED_PATTERN" and inst_count not in (2, 3):
                violations.append(AssertionViolation(
                    "L1", "PROMOTION_ARITHMETIC_ERROR",
                    f"REPEATED_PATTERN must have instance_count in (2, 3), got {inst_count}",
                    r
                ))
            elif p_type in ("RECURRING_SERIES", "CORE_MARKETING_SYSTEM") and inst_count < 4:
                violations.append(AssertionViolation(
                    "L1", "PROMOTION_ARITHMETIC_ERROR",
                    f"{p_type} requires instance_count >= 4, got {inst_count}",
                    r
                ))

            # Matching artefact ids count
            inst_artefact_ids = r.get("instance_artefact_ids")
            if inst_artefact_ids and len(inst_artefact_ids) != inst_count:
                violations.append(AssertionViolation(
                    "L1", "ARTEFACT_COUNT_MISMATCH",
                    f"instance_artefact_ids len ({len(inst_artefact_ids)}) != instance_count ({inst_count})",
                    r
                ))

        # 4. Orphan detection
        p_id = r.get("player_id")
        if p_id and known_players and p_id not in known_players and r.get("record_type") not in ("PLAYER_SELECTION", "PLAYER_PROFILE"):
            violations.append(AssertionViolation(
                "L1", "ORPHAN_PLAYER_RECORD",
                f"Record {idx} references player_id '{p_id}' not found in known players",
                r
            ))

    # 5. Live URL verification
    url_metrics = {}
    if check_live_urls and records:
        val_res = validate_records_urls_sync(records)
        url_metrics = val_res.get("metrics", {})
        if val_res.get("should_halt_run"):
            violations.append(AssertionViolation(
                "L1", "URL_RESOLUTION_CIRCUIT_BREAKER",
                val_res.get("halt_reason", "URL resolution below threshold")
            ))
        for q_rec in val_res.get("quarantined_records", []):
            violations.append(AssertionViolation(
                "L1", "RECORD_URL_DEAD",
                f"Record quarantined due to unresolvable URL: {q_rec.get('quarantine_reason')}",
                q_rec
            ))

    return violations, url_metrics


# -----------------------------------------------------------------------------
# Layer 3 · UNKNOWN Rate Monitor (Inverted Eval - Scoped to Model Fields)
# -----------------------------------------------------------------------------

MODEL_FIELDS = {
    "definition", "trend", "trend_basis",
    "selection_rationale", "pair_contrast_hypothesis",
    "what_it_is", "problem_solved", "customer",
    "business_model", "current_positioning",
    "hook_type", "proof_type", "pattern_template",
}


def evaluate_l3_unknown_rate(envelope: Dict[str, Any]) -> Tuple[float, int, List[AssertionViolation]]:
    """
    Monitor UNKNOWN rate strictly across model-written fields (Item 5).
    Code-derived fields are never UNKNOWN; including them dilutes the signal.
    Assert 0.05 < unknown_rate < 0.40.
    Alert if < 0.05 (suspect complete data fabrication).
    Alert if > 0.40 (broken collection / prompt degradation).
    """
    records = envelope.get("records", [])
    if not records:
        return 0.0, 0, []

    total_fields = 0
    unknown_fields = 0
    violations: List[AssertionViolation] = []

    for r in records:
        for k, v in r.items():
            if k not in MODEL_FIELDS:
                continue
            total_fields += 1
            if v in (None, "", "UNKNOWN") or (isinstance(v, dict) and any(val in (None, "", "UNKNOWN") for val in v.values())):
                unknown_fields += 1

    rate = (unknown_fields / total_fields) if total_fields > 0 else 0.0

    # Only evaluate alert thresholds if at least 10 model fields were checked
    # Phase 1 mandates definitions for all categories by gate rule; lower bound applies to research phases (>= 3)
    phase = envelope.get("phase", 1)
    if total_fields >= 10:
        if rate < 0.05 and phase > 1:
            violations.append(AssertionViolation(
                "L3", "SUSPECT_FABRICATION_ZERO_UNKNOWN",
                f"Model-generated UNKNOWN rate {rate:.1%} ({unknown_fields}/{total_fields} fields) is below 5%. "
                f"Zero or near-zero UNKNOWNs indicates plausible fabrication rather than genuine collection."
            ))
        elif rate > 0.40:
            violations.append(AssertionViolation(
                "L3", "COLLECTION_FAILURE_HIGH_UNKNOWN",
                f"Model-generated UNKNOWN rate {rate:.1%} ({unknown_fields}/{total_fields} fields) exceeds 40%. "
                f"Model is failing to generate or classify required fields."
            ))

    return rate, total_fields, violations


# -----------------------------------------------------------------------------
# Phase-Specific Gates
# -----------------------------------------------------------------------------

def validate_phase_1_gate(envelope: Dict[str, Any]) -> List[AssertionViolation]:
    """Phase 1 Gate: >= 12 categories, each with definition and snapshot_date."""
    violations: List[AssertionViolation] = []
    records = envelope.get("records", [])

    categories = [r for r in records if r.get("record_type") == "MARKET_CATEGORY"]
    if len(categories) < 12:
        violations.append(AssertionViolation(
            "GATE", "PHASE_1_GATE_FAIL",
            f"Phase 1 requires >= 12 MARKET_CATEGORY records, found {len(categories)}"
        ))

    for idx, c in enumerate(categories):
        if not c.get("definition"):
            violations.append(AssertionViolation(
                "GATE", "PHASE_1_GATE_FAIL",
                f"Category record {idx} ('{c.get('category')}') missing definition"
            ))
        if not c.get("snapshot_date"):
            violations.append(AssertionViolation(
                "GATE", "PHASE_1_GATE_FAIL",
                f"Category record {idx} ('{c.get('category')}') missing snapshot_date"
            ))
        if c.get("trend") == "UNKNOWN" and not c.get("trend_basis"):
            violations.append(AssertionViolation(
                "GATE", "PHASE_1_GATE_FAIL",
                f"Category record {idx} has trend UNKNOWN but missing trend_basis"
            ))

    return violations


# -----------------------------------------------------------------------------
# Master Assertion Evaluator
# -----------------------------------------------------------------------------

def run_all_assertions(
    envelope: Dict[str, Any],
    known_players: Optional[Set[str]] = None,
    known_artefacts: Optional[Set[str]] = None,
    check_live_urls: bool = True,
    truth_categories: Optional[Dict[str, Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """Run L0, L1 (including numeric verification), L3, and phase gate checks on an envelope."""
    phase = envelope.get("phase")

    l0_violations = validate_l0_schema(envelope)
    l1_violations, url_metrics = validate_l1_invariants(
        envelope, known_players, known_artefacts, check_live_urls
    )
    # L1 Numeric verification against code-derived aggregator truth
    l1_numeric_violations = validate_l1_numerics(
        envelope.get("records", []), truth_categories
    )
    l1_violations.extend(l1_numeric_violations)

    unknown_rate, model_fields_checked, l3_violations = evaluate_l3_unknown_rate(envelope)

    gate_violations = []
    if phase == 1:
        gate_violations = validate_phase_1_gate(envelope)

    all_violations = l0_violations + l1_violations + l3_violations + gate_violations

    return {
        "passed": len(all_violations) == 0,
        "phase": phase,
        "total_violations": len(all_violations),
        "violations": [v.to_dict() for v in all_violations],
        "url_metrics": url_metrics,
        "unknown_rate": unknown_rate,
        "model_fields_checked": model_fields_checked,
        "summary": {
            "L0_schema_errors": len(l0_violations),
            "L1_invariant_errors": len(l1_violations),
            "L1_numeric_errors": len(l1_numeric_violations),
            "L3_unknown_alerts": len(l3_violations),
            "gate_errors": len(gate_violations),
        },
    }
