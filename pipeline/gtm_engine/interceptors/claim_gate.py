"""
Claim gate interceptor for GTM Intelligence Engine (Law L8 & deterministic safety).
- Enforces Law L8: Vanna material strictly sealed in Phases 1-10 (emits WARNING if detected).
- Validates claim tiers in Phase 11 (VERIFIED | DESIGNED | ROADMAP | MOCK | RETIRED).
- Runs 100% in code; no model calls.
"""

import re
from typing import Dict, Any, List, Tuple

VANNA_REGEX = re.compile(r"\b(vanna|vanna\s+protocol|vanna_g1|vanna_c4)\b", re.IGNORECASE)
VALID_CLAIM_TIERS = {"VERIFIED", "DESIGNED", "ROADMAP", "MOCK", "RETIRED"}


def check_phase_claim_isolation(phase: int, content_text: str) -> Tuple[bool, List[str]]:
    """
    Enforce Law L8: In Phases 1-10, Vanna must not be mentioned or evaluated.
    Returns (is_compliant, warnings).
    """
    warnings = []
    if 1 <= phase <= 10:
        matches = VANNA_REGEX.findall(content_text)
        if matches:
            warnings.append(
                f"Law L8 Violation in Phase {phase}: Vanna material detected ({set(matches)}). "
                f"Vanna must remain sealed until Phase 11."
            )
            return False, warnings
    return True, warnings


def validate_subject_claims(claims: List[Dict[str, Any]]) -> List[str]:
    """Validate claim tier enums in Phase 11."""
    errors = []
    for idx, c in enumerate(claims):
        tier = c.get("tier")
        if tier not in VALID_CLAIM_TIERS:
            errors.append(f"Claim {idx} has invalid tier '{tier}'. Must be in {VALID_CLAIM_TIERS}")
        if not c.get("claim"):
            errors.append(f"Claim {idx} missing 'claim' text.")
    return errors
