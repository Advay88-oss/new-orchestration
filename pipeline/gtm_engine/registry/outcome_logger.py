"""
Outcome Logger & Founder Decision Gradient Engine.
Captures human approvals, rejections, edit diffs, and notes per pattern/draft,
creating a permanent feedback loop so the Writer and Critic agents learn founder preferences.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional

REPO_ROOT = Path("D:/new orchestration")
DECISION_LOG_FILE = REPO_ROOT / "pipeline" / "gtm_engine" / "registry" / "founder_decisions.jsonl"
DECISION_LOG_FILE.parent.mkdir(parents=True, exist_ok=True)


def log_founder_decision(
    pattern_ref: str,
    campaign_id: str,
    decision: str,  # "APPROVED" | "APPROVED_WITH_EDITS" | "REJECTED" | "REVISE_REQUESTED"
    original_draft: str,
    final_draft: Optional[str] = None,
    founder_note: Optional[str] = None,
    edit_diff: Optional[str] = None,
    published_url: Optional[str] = None,
    metrics_48h: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Log founder decision with timestamp and learning feedback."""
    valid_decisions = {"APPROVED", "APPROVED_WITH_EDITS", "REJECTED", "REVISE_REQUESTED"}
    if decision not in valid_decisions:
        raise ValueError(f"Invalid decision: {decision}. Must be one of {valid_decisions}")

    record = {
        "logged_at": datetime.now(timezone.utc).isoformat(),
        "pattern_ref": pattern_ref,
        "campaign_id": campaign_id,
        "decision": decision,
        "founder_note": founder_note or "",
        "edit_diff": edit_diff or "",
        "original_draft_length": len(original_draft),
        "final_draft_length": len(final_draft) if final_draft else len(original_draft),
        "published_url": published_url,
        "metrics_48h": metrics_48h or {}
    }

    with open(DECISION_LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

    print(f"✅ Logged founder decision: {decision} for pattern '{pattern_ref}' in campaign '{campaign_id}'")
    return record


def get_decision_history(pattern_ref: Optional[str] = None):
    """Retrieve decision history to guide prompt context."""
    if not DECISION_LOG_FILE.exists():
        return []
    records = []
    with open(DECISION_LOG_FILE, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rec = json.loads(line)
                if pattern_ref is None or rec.get("pattern_ref") == pattern_ref:
                    records.append(rec)
    return records
