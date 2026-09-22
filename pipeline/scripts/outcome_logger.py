#!/usr/bin/env python3
"""Loop C — Feedback: Outcome Logger.

Captures founder / reviewer decisions on content and attaches them directly
to the pattern in the registry. Closes the loop so future content selects proven patterns.
"""

from __future__ import annotations

import argparse
import datetime
import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

REPO_ROOT = Path(os.environ.get("VANNA_ROOT", Path(__file__).resolve().parents[2]))
REGISTRY_DIR = REPO_ROOT / "registry"
REGISTRY_DIR.mkdir(parents=True, exist_ok=True)
OUTCOMES_FILE = REGISTRY_DIR / "outcomes.jsonl"
PATTERNS_FILE = REPO_ROOT / "pipeline" / "gtm_engine" / "brain" / "db" / "patterns.jsonl"
PATTERNS_FILE.parent.mkdir(parents=True, exist_ok=True)


def get_status(pattern_ref: str) -> str:
    """Returns the current status of a pattern from patterns.jsonl."""
    if not PATTERNS_FILE.exists():
        return "NOT_FOUND"
    with open(PATTERNS_FILE, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            pat = json.loads(line)
            if pat.get("id") == pattern_ref or pat.get("name") == pattern_ref or pat.get("pattern_id") == pattern_ref:
                return pat.get("status", "UNKNOWN")
    return "NOT_FOUND"


def get_stats(pattern_ref: str) -> dict:
    """Returns the decision_stats object of a pattern from patterns.jsonl."""
    if not PATTERNS_FILE.exists():
        return {}
    with open(PATTERNS_FILE, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            pat = json.loads(line)
            if pat.get("id") == pattern_ref or pat.get("name") == pattern_ref or pat.get("pattern_id") == pattern_ref:
                return pat.get("decision_stats", {})
    return {}


def log_outcome(
    pattern_ref: str,
    decision: str,
    edit_diff: Optional[str] = None,
    founder_note: Optional[str] = None,
    published_url: Optional[str] = None,
    campaign_id: Optional[str] = None,
    original_draft_length: Optional[int] = None,
    final_draft_length: Optional[int] = None,
    metrics_48h: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Logs an editorial decision directly to outcomes.jsonl and updates pattern stats atomically."""
    decision_norm = decision.strip().upper()
    valid_decisions = {"APPROVED", "APPROVED_WITH_EDITS", "REJECTED"}
    if decision_norm not in valid_decisions:
        raise ValueError(f"Invalid decision '{decision}'. Must be one of {valid_decisions}")

    record = {
        "logged_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "pattern_ref": pattern_ref,
        "campaign_id": campaign_id or "daily_dispatch",
        "decision": decision_norm,
        "founder_note": founder_note or "",
        "edit_diff": edit_diff or "",
        "original_draft_length": original_draft_length,
        "final_draft_length": final_draft_length,
        "published_url": published_url,
        "metrics_48h": metrics_48h or {},
    }

    # 1. Append to outcomes.jsonl
    with open(OUTCOMES_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")

    # 2. Update pattern in patterns.jsonl with atomic write
    patterns = []
    pattern_found = False
    if PATTERNS_FILE.exists():
        with open(PATTERNS_FILE, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    patterns.append(json.loads(line))

    for pat in patterns:
        if pat.get("id") == pattern_ref or pat.get("name") == pattern_ref or pat.get("pattern_id") == pattern_ref:
            pattern_found = True
            evidence_list = pat.setdefault("performance_evidence", [])
            evidence_list.append({
                "decision": decision_norm,
                "logged_at": record["logged_at"],
                "founder_note": record["founder_note"],
                "published_url": record["published_url"],
            })
            
            n = len(evidence_list)
            approved = sum(1 for e in evidence_list if e["decision"] == "APPROVED")
            edited = sum(1 for e in evidence_list if e["decision"] == "APPROVED_WITH_EDITS")
            rejected = sum(1 for e in evidence_list if e["decision"] == "REJECTED")

            pat["decision_stats"] = {
                "n": n,
                "approved": approved,
                "edited": edited,
                "rejected": rejected,
                "edit_rate": round(edited / n, 2) if n else None,
                "reject_rate": round(rejected / n, 2) if n else None,
            }

            if n < 5:
                pat["status"] = "INSUFFICIENT_SAMPLE"  # no verdict before 5
            elif rejected / n > 0.5:
                pat["status"] = "WEAK"
            elif edited / n > 0.7:
                pat["status"] = "NEEDS_BETTER_BRIEF"   # pattern is fine, brief is not
            elif approved / n > 0.6:
                pat["status"] = "STRONG"
            else:
                pat["status"] = "MIXED"

    if not pattern_found:
        # Create initial record for this pattern if not present
        evidence_list = [{
            "decision": decision_norm,
            "logged_at": record["logged_at"],
            "founder_note": record["founder_note"],
            "published_url": record["published_url"],
        }]
        n = 1
        approved = 1 if decision_norm == "APPROVED" else 0
        edited = 1 if decision_norm == "APPROVED_WITH_EDITS" else 0
        rejected = 1 if decision_norm == "REJECTED" else 0
        new_pat = {
            "id": pattern_ref,
            "name": pattern_ref,
            "status": "INSUFFICIENT_SAMPLE",
            "performance_evidence": evidence_list,
            "decision_stats": {
                "n": n,
                "approved": approved,
                "edited": edited,
                "rejected": rejected,
                "edit_rate": round(edited / n, 2),
                "reject_rate": round(rejected / n, 2),
            }
        }
        patterns.append(new_pat)

    # Atomic write via temporary file
    tmp = PATTERNS_FILE.with_suffix(".tmp")
    tmp.write_text("\n".join(json.dumps(p) for p in patterns) + "\n", encoding="utf-8")
    tmp.replace(PATTERNS_FILE)  # atomic on same filesystem

    return record


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Log editorial outcomes directly into the registry.")
    parser.add_argument("--pattern", required=True, help="Pattern ID or reference")
    parser.add_argument("--decision", required=True, choices=["APPROVED", "APPROVED_WITH_EDITS", "REJECTED"])
    parser.add_argument("--note", default="", help="Founder or reviewer rationale")
    parser.add_argument("--diff", default="", help="Edit diff (- old + new)")
    parser.add_argument("--url", default=None, help="Published X post URL if approved")
    args = parser.parse_args()

    log_outcome(
        pattern_ref=args.pattern,
        decision=args.decision,
        edit_diff=args.diff,
        founder_note=args.note,
        published_url=args.url,
    )
