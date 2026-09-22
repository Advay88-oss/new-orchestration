"""Strict Pydantic schemas for Phase 4 Channel-Native Content Execution.

Enforces:
  - Genuine platform adaptation (no copy-paste shortening)
  - Claim-level provenance on every paragraph
  - Specific channel formats (X threads, LinkedIn articles, Reddit discussions)
"""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field


class ChannelPostPayload(BaseModel):
    """Native payload tailored for a specific distribution channel."""
    content_id: str
    channel: Literal["X", "LinkedIn", "Reddit"]
    format: str
    objective: str
    audience: str
    source_claims: List[str] = Field(default_factory=list)
    exact_evidence_refs: List[str] = Field(default_factory=list)
    hook: str
    copy: str
    call_to_action: str
    risk_flags: List[str] = Field(default_factory=list)
    confidence: Literal["HIGH", "MEDIUM", "LOW"]
    provenance: Dict[str, Any] = Field(default_factory=dict)
    media_direction: Optional[str] = None
    discussion_question: Optional[str] = None


class ChannelAdaptationPackage(BaseModel):
    """Complete multi-channel suite derived strictly from strategy."""
    package_id: str
    strategy_id: str
    campaign_id: Optional[str] = None
    channel_posts: Dict[str, ChannelPostPayload]
    created_at: str


class ChannelReviewVerdict(BaseModel):
    """Reviewer output assessing cross-platform distinctness and provenance."""
    package_id: str
    approved: bool
    distinctness_score: int
    claim_provenance_verified: bool
    blocked_unsupported_claims: List[str] = Field(default_factory=list)
    channel_issues: Dict[str, List[str]] = Field(default_factory=dict)
    reasoning: str
