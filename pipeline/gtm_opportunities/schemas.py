"""Strict Pydantic schemas for Phase 9 Opportunity-Driven Execution.

Enforces transparent, deterministic multi-factor opportunity scoring:
  Final Score = (Relevance*0.2 + Evidence*0.2 + Audience*0.15 + Strategy*0.15 + Machine*0.15 + Conversion*0.15)
                - (RiskPenalty + SaturationPenalty) + NoveltyBonus
"""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field

OpportunityStatus = Literal[
    "ELIGIBLE",
    "HUMAN_REVIEW_REQUIRED",
    "BLOCKED",
    "SATURATED"
]

SelectorDecision = Literal[
    "TOP_OPPORTUNITY",
    "NO_SUITABLE_OPPORTUNITY",
    "HUMAN_REVIEW_REQUIRED",
    "BLOCKED_OPPORTUNITY"
]


class ScoredOpportunity(BaseModel):
    """Transparently scored GTM opportunity with explicit factors."""
    opportunity_id: str
    title: str
    marketing_angle: str
    relevance_score: float = Field(ge=0.0, le=1.0)
    urgency_score: float = Field(ge=0.0, le=1.0)
    evidence_confidence: float = Field(ge=0.0, le=1.0)
    audience_fit: float = Field(ge=0.0, le=1.0)
    strategic_fit: float = Field(ge=0.0, le=1.0)
    machine_eligibility_score: float = Field(ge=0.0, le=1.0)
    conversion_potential: float = Field(ge=0.0, le=1.0)
    risk_penalty: float = Field(ge=0.0, le=1.0)
    novelty_bonus: float = Field(ge=0.0, le=1.0)
    saturation_penalty: float = Field(ge=0.0, le=1.0)
    final_score: float
    status: OpportunityStatus
    ranking_explanation: str
    raw_record: Dict[str, Any] = Field(default_factory=dict)


class OpportunitySelectionOutcome(BaseModel):
    """The authoritative decision from the opportunity selector."""
    decision_status: SelectorDecision
    selected_opportunity: Optional[ScoredOpportunity] = None
    candidate_rankings: List[ScoredOpportunity]
    ranking_rationale: str
    timestamp: str
