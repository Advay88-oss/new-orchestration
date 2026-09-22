"""Strict Pydantic schemas for the Vanna GTM Orchestration Operating System.

Enforces boundaries between:
  MarketSignal -> ClaimEvidence -> GTMStrategy -> ContentBrief -> ContentPackage -> CreativeBrief -> ReviewResult -> ExecutionTrace
"""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field


# ── LEVEL 1: MARKET SIGNAL ───────────────────────────────────────────────────
class MarketSignal(BaseModel):
    """Normalized market intelligence unit retaining full provenance."""
    signal_id: str
    headline: str
    description: str
    market_category: str
    entities_involved: List[str] = Field(default_factory=list)
    observed_metric_change: Optional[str] = None
    source: str
    source_root: Optional[str] = None
    dataset: Optional[str] = None
    # Archival sources (the Brain DB) and live sources are distinguished here
    # rather than blurred: A01 now scouts real feeds, and a strategist choosing
    # between "observed on Reddit this morning" and "recorded in the whitespace
    # DB a fortnight ago" needs to be able to tell which is which.
    source_type: Literal[
        # archival — Brain DB
        "DEFILLAMA_SNAPSHOT",
        "SOCIAL_CORPUS",
        "COMPETITOR_DOSSIER",
        "PATTERNS_DB",
        "WHITESPACE_DB",
        "INTERNAL_KNOWLEDGE",
        "USER_DIRECTIVE",
        # live — A01 scout
        "PRIMARY_NEWS_OBSERVED",
        "REDDIT_COMMUNITY_OBSERVED",
        "DOCS_BLOG_OBSERVED",
        "TELEGRAM_ANNOUNCEMENT_OBSERVED",
        "X_POST_OBSERVED",
        "LIVE_OBSERVED",
        # an archival signal re-served alongside live ones
        "ARCHIVE",
    ]
    record_id: str
    observed_at: str
    data_as_of: Optional[str] = None
    confidence: Literal["HIGH", "MEDIUM", "LOW"]
    evidence_status: Literal["OBSERVED", "INFERRED", "UNKNOWN", "INSUFFICIENT", "NOT_OBSERVED"]


# ── LEVEL 2: CLAIM RECORD & EVIDENCE CLASSIFICATION ──────────────────────────
ClaimType = Literal[
    "VANNA_FACT",
    "COMPETITOR_FACT",
    "COMPARATIVE_CLAIM",
    "WHITESPACE_INFERENCE",
    "MARKETING_OPPORTUNITY"
]

ClaimEvidenceStatus = Literal[
    "OBSERVED",
    "DERIVED",
    "INFERRED",
    "INSUFFICIENT",
    "UNKNOWN",
    "NOT_OBSERVED"
]

ClaimAction = Literal[
    "USE",
    "USE_AS_INFERENCE",
    "DO_NOT_USE",
    "REQUIRES_VERIFICATION"
]


class ClaimRecord(BaseModel):
    """Atomic claim with strict ontological type and verification status."""
    claim_id: str
    text: str
    claim_type: ClaimType
    evidence_status: ClaimEvidenceStatus
    evidence_refs: List[str] = Field(default_factory=list)
    confidence: Literal["HIGH", "MEDIUM", "LOW"]
    source_records: List[str] = Field(default_factory=list)
    calculation_method: Optional[str] = None
    action: ClaimAction
    rationale: str


# ── LEVEL 3: GTM MACHINE ELIGIBILITY ─────────────────────────────────────────
class GTMMachineEligibility(BaseModel):
    """Empirical verification contract for GTM machine selection."""
    machine_id: str
    eligibility_status: Literal["ELIGIBLE", "INSUFFICIENT_EVIDENCE", "PROHIBITED"]
    evidence_count: int
    independent_campaign_count: int
    independent_player_count: int
    evidence_refs: List[str] = Field(default_factory=list)
    confidence: Literal["HIGH", "MEDIUM", "LOW"]
    selection_reason: str


# ── LEVEL 4: GTM STRATEGY CONTRACT ───────────────────────────────────────────
class GTMStrategy(BaseModel):
    """Strategy contract deciding WHAT and WHY with multi-state gate."""
    strategy_id: str
    action_status: Literal["ACTION", "NO_ACTION", "HUMAN_REVIEW_REQUIRED", "KILL"]
    decision_reason_class: Optional[str] = None
    no_action_rationale: Optional[str] = None
    kill_rationale: Optional[str] = None
    human_review_rationale: Optional[str] = None
    objective: str
    audience_segment: str
    problem: str
    market_context: str
    strategic_opportunity: str
    narrative_pillar: str
    positioning: str
    proof: List[str] = Field(default_factory=list)
    claims: List[ClaimRecord] = Field(default_factory=list)
    cta: str
    channel: str
    content_type: str
    gtm_machine_id: str
    machine_eligibility: Optional[GTMMachineEligibility] = None
    reasoning: List[str] = Field(default_factory=list)
    evidence: List[Dict[str, Any]] = Field(default_factory=list)
    title: Optional[str] = None


# ── LEVEL 5: CONTENT BRIEF ───────────────────────────────────────────────────
class ContentBrief(BaseModel):
    """Bridge contract between Strategy and Content Creation."""
    brief_id: str
    strategy_id: str
    purpose: str
    audience: str
    funnel_stage: str
    category: str
    format: str
    narrative: str
    hook_strategy: str
    proof_points: List[str] = Field(default_factory=list)
    call_to_action: str
    claims_to_enforce: List[ClaimRecord] = Field(default_factory=list)
    claims_prohibited: List[str] = Field(default_factory=list)


# ── LEVEL 6: PLATFORM POSTS & CONTENT PACKAGE ─────────────────────────────────
class PlatformPost(BaseModel):
    """Platform-specific rendered copy adapted natively."""
    platform: Literal["X", "LinkedIn", "Reddit"]
    format: str
    hook: str
    body: str
    proof: List[str] = Field(default_factory=list)
    cta: str


class ContentPackage(BaseModel):
    """Complete multi-channel content payload derived strictly from Strategy."""
    package_id: str
    strategy_id: str
    core_message: str
    content_category: str
    funnel_stage: str
    platforms: Dict[str, PlatformPost]
    claims: List[ClaimRecord] = Field(default_factory=list)
    source_evidence: List[Dict[str, Any]] = Field(default_factory=list)


# ── LEVEL 7: CREATIVE BRIEF ───────────────────────────────────────────────────
class CreativeBrief(BaseModel):
    """Visual directorate blueprint derived strictly from communication objective."""
    creative_id: str
    strategy_id: str
    creative_thesis: str
    visual_concept: str
    visual_metaphor: str
    composition: str
    environment: str
    materials: str
    camera: str
    lighting: str
    motion: str
    typography: Dict[str, str] = Field(default_factory=dict)
    brand_system: Dict[str, Any] = Field(default_factory=dict)
    negative_constraints: List[str] = Field(default_factory=list)
    generation_format: Literal["static_vector", "static_image", "video_veo31"]
    generator_instructions: Dict[str, Any] = Field(default_factory=dict)


# ── LEVEL 8: REVIEW RESULT ───────────────────────────────────────────────────
class ReviewResult(BaseModel):
    """Authoritative quality and safety gate verdict."""
    review_id: str
    approved: bool
    verdict: Literal["PASS", "REVISE", "REJECT", "KILL"]
    score: int
    critical_failures: List[str] = Field(default_factory=list)
    brand_issues: List[str] = Field(default_factory=list)
    technical_issues: List[str] = Field(default_factory=list)
    copy_issues: List[str] = Field(default_factory=list)
    creative_issues: List[str] = Field(default_factory=list)
    required_fixes: List[str] = Field(default_factory=list)
    route_to_agent: Optional[Literal["GTMStrategist", "ContentCreator", "CreativeDirector", "BrandGuardian"]] = None
    reasoning: str


# ── LEVEL 9: TRACE & CONFIDENCE MATRIX ────────────────────────────────────────
class ConfidenceMatrix(BaseModel):
    """Separates strategic truth confidence from creative/visual polish."""
    intelligence_confidence: float = Field(ge=0.0, le=1.0)
    evidence_confidence: float = Field(ge=0.0, le=1.0)
    strategy_confidence: float = Field(ge=0.0, le=1.0)
    content_quality: float = Field(ge=0.0, le=1.0)
    creative_quality: float = Field(ge=0.0, le=1.0)
    claim_safety: float = Field(ge=0.0, le=1.0)
    reviewer_score: int = Field(ge=0, le=100)


class StageTrace(BaseModel):
    """Individual execution stage inside the trace."""
    stage: Literal["intelligence", "claim_gate", "strategy", "content", "creative", "review", "approval"]
    status: Literal["SUCCESS", "FAILED", "RETRY", "SKIPPED", "NO_ACTION", "HUMAN_REVIEW_REQUIRED", "KILL", "WAITING_FOR_HUMAN"]
    started_at: str
    completed_at: str
    input_data: Dict[str, Any] = Field(default_factory=dict)
    output_data: Dict[str, Any] = Field(default_factory=dict)
    agent: str
    model: str
    errors: List[str] = Field(default_factory=list)


class ExecutionTrace(BaseModel):
    """Complete end-to-end lifecycle log."""
    trace_id: str
    run_id: str
    overall_status: Literal["SUCCESS", "FAILED", "NO_ACTION", "HUMAN_REVIEW_REQUIRED", "KILL", "WAITING_FOR_HUMAN"]
    stages: List[StageTrace] = Field(default_factory=list)
    confidence_matrix: Optional[ConfidenceMatrix] = None
    provenance_chain: List[Dict[str, Any]] = Field(default_factory=list)
    human_review_packet: Optional[Dict[str, Any]] = None
    performance_metadata: Dict[str, Any] = Field(
        default_factory=lambda: {
            "campaign_id": None,
            "content_id": None,
            "platform": None,
            "impressions": None,      # null != 0
            "engagements": None,      # null != 0
            "clicks": None,           # null != 0
            "conversions": None,      # null != 0
            "measured_at": None,
        }
    )
