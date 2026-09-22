"""
Context Isolation Enforcer for Multi-Tier Model Invocations.
Guarantees that sensitive evaluation benchmarks and internal positioning
never leak into inappropriate model prompts.
"""

FORBIDDEN_IN_CONTEXT = {
    "flash": [
        "knowledge/internal/",
        "golden_set",
        "regression_tests",
        "vanna_docs"
    ],
    "strong": [
        "golden_set",
        "regression_tests"
    ],
}


def assert_context_isolation(tier: str, prompt_text: str) -> None:
    """
    Assert that the prompt contains no forbidden contextual markers for the given tier.
    Raises AssertionError immediately if a leak is detected.
    """
    tier_clean = tier.lower().strip()
    forbidden = FORBIDDEN_IN_CONTEXT.get(tier_clean, [])

    for marker in forbidden:
        if marker in prompt_text:
            raise AssertionError(
                f"CONTEXT LEAK: '{marker}' found in {tier} prompt. "
                f"Quarantine violation. Model call blocked."
            )
