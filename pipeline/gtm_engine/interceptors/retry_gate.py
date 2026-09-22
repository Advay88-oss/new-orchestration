"""
Bounded Revise-and-Recheck Retry Loop for Claim & Positioning Gates.
Replaces binary halting with iterative revision loops (budget: max 2 retries).
"""

import json
from typing import Dict, Any, Callable, Tuple

MAX_RETRIES = 2

def run_bounded_review_loop(
    initial_draft: str,
    writer_revise_fn: Callable[[str, list[str]], str],
    critic_check_fn: Callable[[str], Tuple[bool, list[str]]],
    max_retries: int = MAX_RETRIES
) -> Dict[str, Any]:
    """
    Executes a bounded retry loop:
    1. Critic evaluates draft.
    2. If valid -> APPROVED.
    3. If invalid -> feeds exact violations back to Writer for targeted revision.
    4. Halts and escalates to human only if budget exhausted.
    """
    current_draft = initial_draft
    history = []

    for attempt in range(max_retries + 1):
        is_valid, violations = critic_check_fn(current_draft)
        
        step_log = {
            "attempt": attempt,
            "is_valid": is_valid,
            "violations": violations,
            "draft_snapshot": current_draft[:120] + "..." if len(current_draft) > 120 else current_draft
        }
        history.append(step_log)

        if is_valid:
            return {
                "final_status": "APPROVED",
                "final_draft": current_draft,
                "total_attempts": attempt + 1,
                "history": history
            }

        if attempt < max_retries:
            print(f"⚠️ Gate flagged {len(violations)} violations on attempt {attempt}. Triggering targeted revision...")
            current_draft = writer_revise_fn(current_draft, violations)
        else:
            print(f"❌ Gate budget exhausted ({max_retries} retries). Escalating to BLOCKED_PENDING_HUMAN.")

    return {
        "final_status": "BLOCKED_PENDING_HUMAN",
        "final_draft": current_draft,
        "total_attempts": max_retries + 1,
        "history": history,
        "unresolved_violations": violations
    }
