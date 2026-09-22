"""
Promotion logic for GTM Intelligence Engine.
Deterministic implementation of Law L5 (Arithmetic, not judgement).
"""

from typing import List

# Updated pattern_type enum with REPEATED_PATTERN_HIGH_COUNT
VALID_PATTERN_TYPES = {
    "ONE_OFF",
    "REPEATED_PATTERN",
    "REPEATED_PATTERN_HIGH_COUNT",
    "RECURRING_SERIES",
    "CORE_MARKETING_SYSTEM",
    "CAMPAIGN",
    "CATEGORY_WIDE_MECHANISM",
}


def derive_pattern_type(
    instances: int,
    has_cadence: bool,
    is_named: bool,
    is_campaign: bool,
    formats: List[str],
    periods: int,
    has_strategic_purpose: bool,
) -> str:
    """
    Derive pattern_type strictly following Law L5:
    - is_campaign -> CAMPAIGN
    - instances == 1 -> ONE_OFF
    - instances in (2, 3) -> REPEATED_PATTERN
    - instances >= 4 and not (has_cadence and is_named) -> REPEATED_PATTERN_HIGH_COUNT
    - instances >= 4, has_cadence, is_named, multi-format, multi-period, strategic purpose -> CORE_MARKETING_SYSTEM
    - instances >= 4, has_cadence, is_named -> RECURRING_SERIES
    """
    if is_campaign:
        return "CAMPAIGN"
    if instances <= 0:
        raise ValueError(f"instances must be >= 1, got {instances}")
    if instances == 1:
        return "ONE_OFF"
    if instances in (2, 3):
        return "REPEATED_PATTERN"

    # instances >= 4 below this line
    if not (has_cadence and is_named):
        # Distinct label. NEVER collapse a high-count pattern into the 2-3 bucket.
        return "REPEATED_PATTERN_HIGH_COUNT"
    if len(formats) > 1 and periods > 1 and has_strategic_purpose:
        return "CORE_MARKETING_SYSTEM"
    return "RECURRING_SERIES"
