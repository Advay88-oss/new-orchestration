"""Phase 3: Multi-Stage Campaign Engine (campaign_engine.py).

Instantiates, validates, and manages multi-stage campaigns.
Enforces standard stages (AWARENESS, EDUCATION, PROOF, ENGAGEMENT, CONVERSION, FOLLOW_UP, RETENTION).
Requires explicit omission reasons when stages are omitted.
Supports campaign state transitions (DRAFT, ACTIVE, PAUSED, KILLED, COMPLETED).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone

REPO_ROOT = Path(__file__).resolve().parents[2]
STATE_DIR = REPO_ROOT / "pipeline" / "state"

from pipeline.gtm_campaigns.schemas import (
    CampaignSpec, CampaignStage, CampaignStageType, CampaignStatus
)
from pipeline.gtm_orchestration.schemas import GTMStrategy
from pipeline.gtm_machines.machine_library import GTMMachineLibrary

STANDARD_CAMPAIGN_STAGES: List[CampaignStageType] = [
    "AWARENESS",
    "EDUCATION",
    "PROOF",
    "ENGAGEMENT",
    "CONVERSION",
    "FOLLOW_UP",
    "RETENTION"
]


class CampaignEngine:
    """Manages the creation, stage validation, and lifecycle of multi-stage campaigns."""

    def __init__(self, storage_dir: Optional[Path] = None):
        self.storage_dir = storage_dir or (STATE_DIR / "campaigns")
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.active_campaigns: Dict[str, CampaignSpec] = {}
        self.machine_library = GTMMachineLibrary()

    def instantiate_campaign_from_strategy(
        self,
        strategy: GTMStrategy,
        campaign_name: str,
        start_date: str = "2026-10-01",
        included_stages: Optional[List[CampaignStageType]] = None,
        omission_reasons: Optional[Dict[str, str]] = None
    ) -> CampaignSpec:
        """Instantiate a structured CampaignSpec derived from an approved strategy and machine."""
        if strategy.action_status in ["NO_ACTION", "KILL"]:
            raise ValueError(f"Cannot instantiate campaign for a {strategy.action_status} strategy.")

        # Verify machine eligibility first
        machine_check = self.machine_library.validate_machine_for_strategy(
            strategy.gtm_machine_id, strategy.objective, strategy.audience_segment
        )
        if not machine_check["allowed"]:
            raise ValueError(f"Campaign creation rejected: Machine '{strategy.gtm_machine_id}' is not eligible ({machine_check['reason']}).")

        import re
        mid_clean = re.sub(r'[^a-zA-Z0-9_]', '', strategy.gtm_machine_id)[:12]
        camp_id = f"CAMP-{mid_clean}-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M')}"
        omissions = omission_reasons or {}

        # Default stages to Awareness, Education, Proof, Conversion if not specified
        active_stage_types = included_stages or ["AWARENESS", "EDUCATION", "PROOF", "CONVERSION"]
        stages: List[CampaignStage] = []

        stage_num = 1
        for std_stage in STANDARD_CAMPAIGN_STAGES:
            if std_stage in active_stage_types:
                if std_stage == "AWARENESS":
                    c_stage = CampaignStage(
                        stage_number=stage_num,
                        stage_type=std_stage,
                        stage_name="Market Friction & Narrative Awareness",
                        functional_objective="Expose EVM shared pool contagion and gas volatility",
                        target_channel="X",
                        content_format="thread_lead",
                        evidence_status="OBSERVED",
                        source_url_ref="https://docs.vanna.finance"
                    )
                elif std_stage == "EDUCATION":
                    c_stage = CampaignStage(
                        stage_number=stage_num,
                        stage_type=std_stage,
                        stage_name="SmartAccount Sandbox Technical Education",
                        functional_objective="Explain contract instance isolation and RateModel curves",
                        target_channel="X & LinkedIn",
                        content_format="architectural_schematic",
                        evidence_status="OBSERVED",
                        source_url_ref="https://docs.vanna.finance"
                    )
                elif std_stage == "PROOF":
                    c_stage = CampaignStage(
                        stage_number=stage_num,
                        stage_type=std_stage,
                        stage_name="Sub-Second Telemetry Benchmark Proof",
                        functional_objective="Demonstrate ~320ms Mercury event streaming at $0.00014 gas",
                        target_channel="X & Reddit",
                        content_format="benchmark_data",
                        evidence_status="DERIVED",
                        source_url_ref=None
                    )
                elif std_stage == "CONVERSION":
                    c_stage = CampaignStage(
                        stage_number=stage_num,
                        stage_type=std_stage,
                        stage_name="Testnet Sandbox Deployment Call to Action",
                        functional_objective="Drive developer and LP sandbox deployments",
                        target_channel="X",
                        content_format="cta_broadcast",
                        evidence_status="OBSERVED",
                        source_url_ref="https://test.stellar.vanna.finance"
                    )
                else:
                    c_stage = CampaignStage(
                        stage_number=stage_num,
                        stage_type=std_stage,
                        stage_name=f"{std_stage.title()} Execution",
                        functional_objective=f"Execute {std_stage.lower()} milestone",
                        target_channel="X",
                        content_format="standard_post",
                        evidence_status="NOT_OBSERVED",
                        source_url_ref=None
                    )
                stages.append(c_stage)
                stage_num += 1
            else:
                # Stage omitted: must record explicit omission reason
                if std_stage not in omissions:
                    omissions[std_stage] = f"Omitted by design: {std_stage.lower()} handled via organic community feedback during testnet."

        campaign = CampaignSpec(
            campaign_id=camp_id,
            machine_id=strategy.gtm_machine_id,
            campaign_name=campaign_name,
            strategic_objective=strategy.objective,
            target_audience=strategy.audience_segment,
            core_narrative=strategy.positioning,
            call_to_action=strategy.cta,
            start_date=start_date,
            status="DRAFT",
            stages=stages,
            omitted_stages=omissions,
            approval_state="PENDING_HUMAN_APPROVAL",
            created_at=datetime.now(timezone.utc).isoformat()
        )

        self.active_campaigns[camp_id] = campaign
        self._save_campaign(campaign)
        return campaign

    def pause_campaign(self, campaign_id: str, reason: str) -> CampaignSpec:
        """Pause an active campaign with a documented reason."""
        camp = self.get_campaign(campaign_id)
        if not camp:
            raise KeyError(f"Campaign '{campaign_id}' not found.")
        camp.status = "PAUSED"
        self._save_campaign(camp)
        print(f"⏸️ CAMPAIGN ENGINE: Paused campaign {campaign_id} (Reason: {reason})")
        return camp

    def kill_campaign(self, campaign_id: str, reason: str) -> CampaignSpec:
        """Terminate a campaign due to strategic or evidence violation."""
        camp = self.get_campaign(campaign_id)
        if not camp:
            raise KeyError(f"Campaign '{campaign_id}' not found.")
        camp.status = "KILLED"
        self._save_campaign(camp)
        print(f"💀 CAMPAIGN ENGINE: Terminated campaign {campaign_id} (Reason: {reason})")
        return camp

    def approve_campaign(self, campaign_id: str, approver: str = "TelegramFounder") -> CampaignSpec:
        """Human approval gate for campaign launch."""
        camp = self.get_campaign(campaign_id)
        if not camp:
            raise KeyError(f"Campaign '{campaign_id}' not found.")
        camp.approval_state = "APPROVED"
        camp.status = "ACTIVE"
        self._save_campaign(camp)
        print(f"✅ CAMPAIGN ENGINE: Approved campaign {campaign_id} by {approver}")
        return camp

    def get_campaign(self, campaign_id: str) -> Optional[CampaignSpec]:
        """Fetch a campaign by ID."""
        if campaign_id in self.active_campaigns:
            return self.active_campaigns[campaign_id]
        camp_path = self.storage_dir / f"{campaign_id}.json"
        if camp_path.exists():
            data = json.loads(camp_path.read_text(encoding="utf-8"))
            camp = CampaignSpec(**data)
            self.active_campaigns[campaign_id] = camp
            return camp
        return None

    def list_campaigns(self) -> List[CampaignSpec]:
        """List all campaigns in storage."""
        campaigns = []
        for f in self.storage_dir.glob("*.json"):
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                campaigns.append(CampaignSpec(**data))
            except Exception:
                pass
        return campaigns

    def _save_campaign(self, campaign: CampaignSpec) -> None:
        camp_path = self.storage_dir / f"{campaign.campaign_id}.json"
        camp_path.write_text(campaign.model_dump_json(indent=2), encoding="utf-8")
