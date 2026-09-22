"""Phase 9: Opportunity Selector & Decision Engine (opportunity_selector.py).

Reads opportunities directly from the canonical Brain DB (opportunities.jsonl).
Ranks candidates using a transparent, multi-factor scoring algorithm:
  - Relevance, Urgency, Evidence, Audience Fit, Strategic Fit, Machine Eligibility, Conversion
  - Risk Penalty, Saturation Penalty, Novelty Bonus
Avoids opaque LLM-only ranking.
Returns: TOP_OPPORTUNITY, NO_SUITABLE_OPPORTUNITY, HUMAN_REVIEW_REQUIRED, or BLOCKED_OPPORTUNITY.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone

REPO_ROOT = Path(__file__).resolve().parents[2]

from pipeline.gtm_orchestration.config import DEFAULT_CONFIG
from pipeline.gtm_opportunities.schemas import (
    ScoredOpportunity, OpportunitySelectionOutcome, SelectorDecision, OpportunityStatus
)


class OpportunitySelector:
    """Selects and ranks GTM opportunities transparently without manual topic injection."""

    def __init__(self, config=None):
        self.config = config or DEFAULT_CONFIG
        self.brain_db = self.config.brain_db_dir

    def _read_opportunities(self) -> List[Dict[str, Any]]:
        opps_file = self.brain_db / "opportunities.jsonl"
        if not opps_file.exists():
            return []
        records = []
        with open(opps_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    records.append(json.loads(line))
        return records

    def score_opportunity(self, raw_opp: Dict[str, Any]) -> ScoredOpportunity:
        """Score an individual opportunity against explicit dimensions."""
        opp_id = raw_opp.get("opportunity_id", "OPP-00")
        title = raw_opp.get("title", "")
        angle = raw_opp.get("marketing_angle", "")
        conf_val = raw_opp.get("confidence", "MEDIUM")
        confidence_str = str(conf_val).upper() if not isinstance(conf_val, (int, float)) else ("HIGH" if conf_val >= 0.8 else "MEDIUM")
        prohibited = raw_opp.get("prohibited_claims", [])

        # 1. Base Scores
        # Relevance: high if Soroban/credit/liquidation
        text_lower = f"{title} {angle} {raw_opp.get('vanna_fact', '')}".lower()
        relevance = 0.95 if any(k in text_lower for k in ["soroban", "credit", "sandbox", "liquidation", "blend"]) else 0.50

        # Evidence confidence
        evidence_conf = 0.95 if confidence_str == "HIGH" and raw_opp.get("vanna_source") else 0.50

        # Audience fit: targeted segments A1, A2, or A3
        audience_fit = 0.90 if "soroban" in text_lower or "borrower" in text_lower else 0.60

        # Strategic fit: aligns with Pillar 1, 2, or 3
        strategic_fit = 0.95 if any(k in text_lower for k in ["isolated", "smartaccount", "1.10x", "health factor", "composable"]) else 0.60

        # Machine eligibility score
        machine_score = 0.90 if any(k in text_lower for k in ["sandbox", "credit", "liquidation"]) else 0.50

        # Conversion potential
        conversion = 0.85 if "10x" in text_lower or "protects" in text_lower else 0.50

        # Penalties & Bonuses
        risk_penalty = 0.30 if any("mainnet" in p.lower() or "guarantee" in p.lower() for p in prohibited) else 0.05
        saturation_penalty = 0.10 if "apy" in text_lower and "loop" in text_lower else 0.0
        novelty_bonus = 0.10 if "smartaccount" in text_lower or "1.10x" in text_lower else 0.0

        # Final Formula
        base = (relevance * 0.20 + evidence_conf * 0.20 + audience_fit * 0.15 +
                strategic_fit * 0.15 + machine_score * 0.15 + conversion * 0.15)
        final_score = round(max(0.0, min(1.0, base - risk_penalty - saturation_penalty + novelty_bonus)), 2)

        # Status determination
        if any(phrase in text_lower for phrase in ["uncontested first-mover", "zero competitor", "only protocol"]):
            status: OpportunityStatus = "HUMAN_REVIEW_REQUIRED"
            explanation = "Contains unverified first-mover assertion; requires human review before autonomous selection."
        elif evidence_conf < 0.60:
            status: OpportunityStatus = "HUMAN_REVIEW_REQUIRED"
            explanation = "Evidence confidence is below threshold; unconfirmed market signal."
        elif final_score >= 0.70:
            status: OpportunityStatus = "ELIGIBLE"
            explanation = f"High strategic fit ({final_score:.2f}) with verified documentation backing."
        else:
            status: OpportunityStatus = "HUMAN_REVIEW_REQUIRED"
            explanation = f"Score ({final_score:.2f}) falls below autonomous threshold (0.70)."

        return ScoredOpportunity(
            opportunity_id=opp_id,
            title=title,
            marketing_angle=angle,
            relevance_score=relevance,
            urgency_score=0.85,
            evidence_confidence=evidence_conf,
            audience_fit=audience_fit,
            strategic_fit=strategic_fit,
            machine_eligibility_score=machine_score,
            conversion_potential=conversion,
            risk_penalty=risk_penalty,
            novelty_bonus=novelty_bonus,
            saturation_penalty=saturation_penalty,
            final_score=final_score,
            status=status,
            ranking_explanation=explanation,
            raw_record=raw_opp
        )

    def select_best_opportunity(self, candidate_records: Optional[List[Dict[str, Any]]] = None) -> OpportunitySelectionOutcome:
        """Score all candidates and return top opportunity or transparent non-selection state."""
        raw_candidates = candidate_records if candidate_records is not None else self._read_opportunities()

        if not raw_candidates:
            return OpportunitySelectionOutcome(
                decision_status="NO_SUITABLE_OPPORTUNITY",
                selected_opportunity=None,
                candidate_rankings=[],
                ranking_rationale="No candidate opportunities found in canonical Brain DB.",
                timestamp=datetime.now(timezone.utc).isoformat()
            )

        scored_list = [self.score_opportunity(opp) for opp in raw_candidates]
        scored_list.sort(key=lambda s: s.final_score, reverse=True)

        top = scored_list[0]
        if top.status == "BLOCKED":
            decision: SelectorDecision = "BLOCKED_OPPORTUNITY"
            selected = None
            rationale = f"Top opportunity '{top.title}' is blocked due to safety violations."
        elif top.status == "HUMAN_REVIEW_REQUIRED":
            decision: SelectorDecision = "HUMAN_REVIEW_REQUIRED"
            selected = top
            rationale = f"Top opportunity '{top.title}' scored {top.final_score}, but requires human review ({top.ranking_explanation})."
        elif top.final_score >= 0.70:
            decision: SelectorDecision = "TOP_OPPORTUNITY"
            selected = top
            rationale = f"Selected '{top.title}' with top score {top.final_score} ({top.ranking_explanation})."
        else:
            decision: SelectorDecision = "NO_SUITABLE_OPPORTUNITY"
            selected = None
            rationale = f"Highest score was {top.final_score}, which does not meet the autonomous threshold (0.70)."

        return OpportunitySelectionOutcome(
            decision_status=decision,
            selected_opportunity=selected,
            candidate_rankings=scored_list,
            ranking_rationale=rationale,
            timestamp=datetime.now(timezone.utc).isoformat()
        )

    def select_top_opportunities(
        self,
        limit: int = 3,
        require_diversity: bool = True,
        candidate_records: Optional[List[Dict[str, Any]]] = None
    ) -> List[ScoredOpportunity]:
        """Selects a diverse portfolio of top-ranking opportunities across multiple audience tracks."""
        raw_candidates = candidate_records if candidate_records is not None else self._read_opportunities()
        if not raw_candidates:
            return []

        scored_list = [self.score_opportunity(opp) for opp in raw_candidates]
        scored_list.sort(key=lambda s: s.final_score, reverse=True)

        selected: List[ScoredOpportunity] = []
        seen_audiences = set()
        seen_machines = set()

        for cand in scored_list:
            if cand.status == "BLOCKED" or cand.final_score < 0.60:
                continue

            aud = cand.raw_record.get("target_audience", "A2")
            mach = cand.raw_record.get("recommended_machine", "MACH_04")

            if require_diversity and len(selected) > 0:
                if aud in seen_audiences and mach in seen_machines and len(selected) < limit:
                    continue

            selected.append(cand)
            seen_audiences.add(aud)
            seen_machines.add(mach)

            if len(selected) >= limit:
                break

        return selected
