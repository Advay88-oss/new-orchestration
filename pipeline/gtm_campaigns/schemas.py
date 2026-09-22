"""Strict Pydantic schemas for Campaigns, Series, and Staged Execution (Phase 3).

Distinguishes:
  - One-off content
  - Recurring series (systematic content loop)
  - Multi-stage campaign (phased timeline with conversion funnel)
"""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field


CampaignStageType = Literal[
    "AWARENESS",
    "EDUCATION",
    "PROOF",
    "ENGAGEMENT",
    "CONVERSION",
    "FOLLOW_UP",
    "RETENTION"
]

CampaignStatus = Literal[
    "DRAFT",
    "ACTIVE",
    "PAUSED",
    "KILLED",
    "COMPLETED"
]

RecurrenceTier = Literal[
    "ONE_OCCURRENCE",       # Single observed post
    "REPEATED_PATTERN",     # 2-3 occurrences observed
    "RECURRING_SYSTEM"      # >= 4 regular cadence occurrences verified
]


class CampaignStage(BaseModel):
    """Individual stage inside a multi-week campaign."""
    stage_number: int
    stage_type: CampaignStageType
    stage_name: str
    functional_objective: str
    target_channel: str
    content_format: str
    evidence_status: Literal["OBSERVED", "DERIVED", "NOT_OBSERVED"]
    source_url_ref: Optional[str] = None
    omission_reason: Optional[str] = None
    status: Literal["PENDING", "ACTIVE", "COMPLETED", "SKIPPED"] = "PENDING"


class CampaignSpec(BaseModel):
    """Complete multi-stage campaign specification."""
    campaign_id: str
    machine_id: str
    campaign_name: str
    strategic_objective: str
    target_audience: str
    core_narrative: str
    call_to_action: str
    start_date: str
    end_date: Optional[str] = None
    status: CampaignStatus = "DRAFT"
    stages: List[CampaignStage]
    omitted_stages: Dict[str, str] = Field(default_factory=dict)
    approval_state: Literal["PENDING_HUMAN_APPROVAL", "APPROVED", "REJECTED"] = "PENDING_HUMAN_APPROVAL"
    created_at: str


class SeriesOccurrence(BaseModel):
    """Individual real occurrence in a recurring series."""
    occurrence_id: str
    occurrence_number: int
    published_date: str
    content_id: str
    verified_url: Optional[str] = None
    input_data_summary: str


class SeriesSpec(BaseModel):
    """Repeatable systematic content loop."""
    series_id: str
    series_name: str
    cadence: Literal["WEEKLY", "BIWEEKLY", "MONTHLY"]
    trigger: str
    input_data_source: str
    fixed_structure: List[str]
    variable_fields: List[str]
    visual_template_type: str
    recurrence_tier: RecurrenceTier
    occurrences: List[SeriesOccurrence] = Field(default_factory=list)
    created_at: str


class CampaignSelectionResult(BaseModel):
    """Decision between One-off, Series, or Multi-stage Campaign."""
    decision_type: Literal["ONE_OFF", "RECURRING_SERIES", "MULTI_STAGE_CAMPAIGN"]
    spec_id: str
    rationale: str
    selected_machine_id: str
    evidence_grounding: List[str] = Field(default_factory=list)
