"""Strict Pydantic schemas for Phase 6 Autonomous GTM Operating System & Phase 7 Human Approval.

Defines:
  - 17 explicit state transitions
  - Traceable state transition records with confidence and actors
  - Full Telegram human approval packet with complete strategic explainability
"""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field

OSState = Literal[
    "INGESTED",
    "EVIDENCE_VALIDATED",
    "STRATEGY_CREATED",
    "NO_ACTION",
    "HUMAN_REVIEW_REQUIRED",
    "KILLED",
    "MACHINE_SELECTED",
    "CAMPAIGN_CREATED",
    "CONTENT_CREATED",
    "CREATIVE_CREATED",
    "REVIEWED",
    "WAITING_FOR_HUMAN",
    "APPROVED",
    "PUBLISHED",
    "PERFORMANCE_PENDING",
    "LEARNING_COMPLETE",
    "FAILED"
]


class OSStateTransition(BaseModel):
    """Immutable transition record in the lifecycle state machine."""
    transition_id: str
    from_state: OSState
    to_state: OSState
    timestamp: str
    actor: str
    reason: str
    input_references: List[str] = Field(default_factory=list)
    output_references: List[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
    error_information: Optional[str] = None


class FullHumanApprovalPacket(BaseModel):
    """Complete Telegram founder decision card with end-to-end explainability."""
    packet_id: str
    why_this_signal: str
    why_this_audience: str
    strategic_objective: str
    selected_machine: Dict[str, Any]
    campaign_or_series_context: Dict[str, Any]
    claims_used: List[Dict[str, str]]
    evidence_links: List[str]
    unsupported_claims_rejected: List[str] = Field(default_factory=list)
    content_variants: Dict[str, Any]
    creative_concept: Dict[str, Any]
    reviewer_score: int
    confidence_dimensions: Dict[str, float]
    known_limitations: List[str]
    expected_cta: str
    exact_action_requested: str
    available_actions: List[str] = Field(
        default_factory=lambda: [
            "APPROVE", "REVISE", "REGENERATE", "KILL", "REQUEST_EVIDENCE", "REJECT_MACHINE", "PAUSE_CAMPAIGN"
        ]
    )
