"""Lifecycle Trace Logger for Vanna GTM Orchestration.

Manages ExecutionTrace lifecycle, records stage transitions, validates contract schemas,
calculates the multidimensional ConfidenceMatrix, and builds claim-level provenance chains.
"""

from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone

from pipeline.gtm_orchestration.schemas import ExecutionTrace, StageTrace, ConfidenceMatrix


class TraceLogger:
    """Manages persistent execution traces across all agent boundaries."""

    def __init__(self, output_dir: Optional[Path] = None):
        self.output_dir = output_dir or (Path(__file__).resolve().parents[2] / "pipeline" / "state")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.trace_id = f"TRACE-{uuid.uuid4().hex[:12].upper()}"
        self.run_id = f"RUN-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}"
        self.stages: List[StageTrace] = []
        self.provenance_chain: List[Dict[str, Any]] = []

    def record_stage(
        self,
        stage: str,
        status: str,
        started_at: str,
        completed_at: str,
        input_data: Dict[str, Any],
        output_data: Dict[str, Any],
        agent: str,
        model: str,
        errors: Optional[List[str]] = None
    ) -> StageTrace:
        """Log a completed or failed stage into the trace."""
        st = StageTrace(
            stage=stage,
            status=status,
            started_at=started_at,
            completed_at=completed_at,
            input_data=input_data,
            output_data=output_data,
            agent=agent,
            model=model,
            errors=errors or []
        )
        self.stages.append(st)
        return st

    def add_provenance(self, item: Dict[str, Any]) -> None:
        """Append an intelligence or factual source to the provenance chain."""
        self.provenance_chain.append(item)

    def assemble_human_review_packet(
        self,
        strategy_dict: Dict[str, Any],
        content_dict: Optional[Dict[str, Any]] = None,
        creative_dict: Optional[Dict[str, Any]] = None,
        review_dict: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Compile complete explanation for the human founder on Telegram."""
        content_dict = content_dict or {}
        creative_dict = creative_dict or {}
        review_dict = review_dict or {}

        claims_raw = content_dict.get("claims", strategy_dict.get("claims", []))
        claims_summary = []
        for c in claims_raw:
            if isinstance(c, dict):
                claims_summary.append({
                    "claim_id": c.get("claim_id"),
                    "text": c.get("text"),
                    "type": c.get("claim_type"),
                    "evidence_status": c.get("evidence_status"),
                    "action": c.get("action")
                })
            else:
                claims_summary.append({"text": str(c)})

        return {
            "decision_status": strategy_dict.get("action_status"),
            "decision_reason_class": strategy_dict.get("decision_reason_class"),
            "why_this_strategy": strategy_dict.get("strategic_opportunity"),
            "why_this_audience": strategy_dict.get("audience_segment"),
            "why_this_narrative": strategy_dict.get("narrative_pillar"),
            "kill_or_review_rationale": strategy_dict.get("kill_rationale") or strategy_dict.get("human_review_rationale") or strategy_dict.get("no_action_rationale"),
            "evidence_supporting": strategy_dict.get("evidence", []),
            "claims_evaluated": claims_summary,
            "content_summary": {
                "x_hook": content_dict.get("platforms", {}).get("x", {}).get("hook"),
                "platforms": list(content_dict.get("platforms", {}).keys())
            } if content_dict else None,
            "creative_concept": {
                "thesis": creative_dict.get("creative_thesis"),
                "visual_metaphor": creative_dict.get("visual_metaphor"),
                "format": creative_dict.get("generation_format")
            } if creative_dict else None,
            "reviewer_verdict": {
                "approved": review_dict.get("approved"),
                "score": review_dict.get("score"),
                "reasoning": review_dict.get("reasoning")
            } if review_dict else None,
            "actions_available": ["APPROVE_AND_DISPATCH", "REVISE_COPY", "REGENERATE_CREATIVE", "KILL"]
        }

    def compute_confidence_matrix(
        self,
        strategy_dict: Dict[str, Any],
        review_dict: Optional[Dict[str, Any]] = None
    ) -> ConfidenceMatrix:
        """Calculate the multidimensional confidence matrix separating strategy truth from creative polish."""
        claims = strategy_dict.get("claims", [])
        blocked = sum(1 for c in claims if isinstance(c, dict) and c.get("action") == "DO_NOT_USE")
        observed = sum(1 for c in claims if isinstance(c, dict) and c.get("evidence_status") == "OBSERVED")
        total_claims = max(1, len(claims))

        evidence_conf = max(0.0, min(1.0, (observed / total_claims) - (blocked * 0.4)))
        strat_conf = 0.95 if strategy_dict.get("action_status") == "ACTION" else 0.50

        rev_score = review_dict.get("score", 0) if review_dict else 0
        claim_safety = 1.0 if blocked == 0 and strategy_dict.get("action_status") != "KILL" else 0.0

        return ConfidenceMatrix(
            intelligence_confidence=0.90 if strategy_dict.get("evidence") else 0.50,
            evidence_confidence=round(evidence_conf, 2),
            strategy_confidence=round(strat_conf, 2),
            content_quality=0.92 if strategy_dict.get("action_status") == "ACTION" else 0.0,
            creative_quality=0.90 if strategy_dict.get("action_status") == "ACTION" else 0.0,
            claim_safety=round(claim_safety, 2),
            reviewer_score=rev_score
        )

    def finalize_trace(
        self,
        overall_status: str,
        strategy_dict: Optional[Dict[str, Any]] = None,
        review_dict: Optional[Dict[str, Any]] = None,
        human_packet: Optional[Dict[str, Any]] = None
    ) -> ExecutionTrace:
        """Save and return the final ExecutionTrace."""
        matrix = None
        if strategy_dict:
            matrix = self.compute_confidence_matrix(strategy_dict, review_dict)

        trace = ExecutionTrace(
            trace_id=self.trace_id,
            run_id=self.run_id,
            overall_status=overall_status,
            stages=self.stages,
            confidence_matrix=matrix,
            provenance_chain=self.provenance_chain,
            human_review_packet=human_packet,
            performance_metadata={
                "campaign_id": None,
                "content_id": None,
                "platform": None,
                "impressions": None,    # Explicit null != 0
                "engagements": None,    # Explicit null != 0
                "clicks": None,         # Explicit null != 0
                "conversions": None,    # Explicit null != 0
                "measured_at": None
            }
        )

        trace_path = self.output_dir / "execution_trace.json"
        trace_path.write_text(trace.model_dump_json(indent=2), encoding="utf-8")
        return trace
