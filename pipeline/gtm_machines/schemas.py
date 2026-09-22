"""Strict Pydantic schemas for GTM Machine Library (Phase 2).

Separates:
  - observed_behavior: empirically verified in competitor campaigns
  - inferred_mechanism: analytical deduction of why it worked
  - proposed_vanna_adaptation: specific Vanna protocol application
Enforces empirical thresholds before autonomous selection.
"""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field


class MachineStage(BaseModel):
    """Individual stage inside a multi-stage GTM machine."""
    stage_number: int
    stage_name: str
    purpose: str
    expected_content_type: str
    required_evidence_status: Literal["OBSERVED", "DERIVED", "INFERRED", "NOT_OBSERVED"]
    source_url_ref: Optional[str] = None


class GTMMachineDefinition(BaseModel):
    """Complete machine specification with empirical evidence backing."""
    machine_id: str
    name: str
    purpose: str
    category: str
    eligible_objectives: List[str] = Field(default_factory=list)
    eligible_audiences: List[str] = Field(default_factory=list)
    
    # ── EVIDENCE DISCIPLINE ───────────────────────────────────────────────────
    eligibility_status: Literal["ELIGIBLE", "INSUFFICIENT_EVIDENCE", "PROHIBITED"]
    minimum_evidence_threshold: int = 1
    observed_campaign_count: int
    observed_player_count: int
    independent_campaign_examples: List[str] = Field(default_factory=list)
    source_references: List[str] = Field(default_factory=list)
    confidence: Literal["HIGH", "MEDIUM", "LOW"]
    
    # ── THREE-WAY KNOWLEDGE SEPARATION ────────────────────────────────────────
    observed_behavior: str
    inferred_mechanism: str
    proposed_vanna_adaptation: str
    
    # ── EXECUTION SPECIFICATIONS ──────────────────────────────────────────────
    required_stages: List[MachineStage]
    supported_channels: List[str] = Field(default_factory=list)
    expected_cta_types: List[str] = Field(default_factory=list)
    disallowed_use_cases: List[str] = Field(default_factory=list)
    known_limitations: str


class MachineAuditReport(BaseModel):
    """Summary report of the GTM Machine Library audit."""
    audit_timestamp: str
    total_machines_evaluated: int
    eligible_machines_count: int
    insufficient_evidence_count: int
    prohibited_machines_count: int
    machines_summary: List[Dict[str, Any]]
    threshold_rules_enforced: List[str]
