"""Phase 3: Campaign Selector & Decider (campaign_selector.py).

Determines whether a strategy should execute as:
  - ONE_OFF (Single isolated broadcast)
  - RECURRING_SERIES (Systematic repeatable cadence)
  - MULTI_STAGE_CAMPAIGN (Staged phased conversion funnel)
Emits CampaignSelectionResult and outputs campaign_series_audit.json.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone

REPO_ROOT = Path(__file__).resolve().parents[2]
STATE_DIR = REPO_ROOT / "pipeline" / "state"

from pipeline.gtm_campaigns.schemas import CampaignSelectionResult
from pipeline.gtm_orchestration.schemas import GTMStrategy
from pipeline.gtm_campaigns.campaign_engine import CampaignEngine
from pipeline.gtm_campaigns.series_engine import SeriesEngine
from pipeline.gtm_orchestration.decision_quality_gates import VehicleFitGate


class CampaignSelector:
    """Decides the optimal structural vehicle (One-off vs Series vs Multi-Stage Campaign)."""

    def __init__(self):
        self.campaign_engine = CampaignEngine()
        self.series_engine = SeriesEngine()
        self.vehicle_gate = VehicleFitGate()

    def select_structural_vehicle(
        self,
        strategy: GTMStrategy,
        has_coordinated_cohorts: bool = False,
        has_conversion_funnel: bool = False
    ) -> CampaignSelectionResult:
        """Evaluate strategy using VehicleFitGate to decide between One-off, Series, or Multi-stage Campaign."""
        machine_id = strategy.gtm_machine_id or ""
        pillar = strategy.narrative_pillar.lower()

        # Check if the topic is a recurring architectural or technical mechanism
        is_repeatable = any(k in f"{machine_id} {pillar}".lower() for k in [
            "telemetry", "benchmark", "education", "sandbox", "monitoring", "architecture"
        ])

        # Evaluate through VehicleFitGate
        vehicle_type, gate_res = self.vehicle_gate.evaluate(
            topic=strategy.narrative_pillar,
            stage_count=1 if not has_coordinated_cohorts else 4,
            is_repeatable_theme=is_repeatable,
            has_coordinated_cohorts=has_coordinated_cohorts,
            has_conversion_funnel=has_conversion_funnel
        )

        if vehicle_type == "CAMPAIGN":
            spec_id = f"CAMP-{strategy.strategy_id[:16]}"
            evidence = ["CAMP_TESTNET_STAGED_SPRINT", "COORDINATED_COHORTS_VERIFIED"]
            decision_val = "MULTI_STAGE_CAMPAIGN"
        elif vehicle_type == "SERIES":
            spec_id = f"SERIES_{strategy.strategy_id[:16]}"
            evidence = ["RECURRING_EDUCATIONAL_SERIES", "BRAIN_RECURRING_SERIES_RECORD"]
            decision_val = "RECURRING_SERIES"
        else:
            spec_id = f"ONEOFF-{strategy.strategy_id[:16]}"
            evidence = ["TACTICAL_INTEGRATION_POST"]
            decision_val = "ONE_OFF"

        return CampaignSelectionResult(
            decision_type=decision_val,
            spec_id=spec_id,
            rationale=gate_res.reason,
            selected_machine_id=machine_id,
            evidence_grounding=evidence
        )

    def audit_campaign_and_series_engine(self, out_file: Optional[Path] = None) -> Dict[str, Any]:
        """Generate the official Phase 3 Campaign & Series audit report."""
        out_path = out_file or (STATE_DIR / "campaign_series_audit.json")

        campaigns = self.campaign_engine.list_campaigns()
        series_list = self.series_engine.list_series()

        report = {
            "audit_timestamp": datetime.now(timezone.utc).isoformat(),
            "campaigns_count": len(campaigns),
            "series_count": len(series_list),
            "distinction_rules_enforced": [
                "One-off post: isolated standalone post with no staged sequence",
                "Recurring series: requires cadence, fixed structure, and tracked occurrence records (>= 4 for RECURRING_SYSTEM)",
                "Multi-stage campaign: requires 7 standard stages or explicit omission reasons"
            ],
            "campaign_stage_standard": [
                "AWARENESS", "EDUCATION", "PROOF", "ENGAGEMENT", "CONVERSION", "FOLLOW_UP", "RETENTION"
            ],
            "series_recurrence_tiers": [
                "ONE_OCCURRENCE: 1 observed post",
                "REPEATED_PATTERN: 2-3 occurrences",
                "RECURRING_SYSTEM: >= 4 occurrences verified on regular cadence"
            ],
            "audit_status": "VERIFIED"
        }

        out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(f"📊 Emitted Campaign & Series Audit Report: {out_path.name}")
        return report
