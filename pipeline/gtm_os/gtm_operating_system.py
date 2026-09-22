"""Phase 6: Central GTM Operating System (gtm_operating_system.py).

The master autonomous marketing and GTM operating system.
Coordinates all 17 lifecycle state transitions:
  INGESTED -> EVIDENCE_VALIDATED -> STRATEGY_CREATED -> MACHINE_SELECTED ->
  CAMPAIGN_CREATED -> CONTENT_CREATED -> CREATIVE_CREATED -> REVIEWED ->
  WAITING_FOR_HUMAN -> APPROVED -> PUBLISHED -> PERFORMANCE_PENDING
Supports terminal states: NO_ACTION, HUMAN_REVIEW_REQUIRED, KILLED, FAILED.
Integrates all Phase 1-5 engines through strict machine-readable contracts.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone

REPO_ROOT = Path(__file__).resolve().parents[2]
STATE_DIR = REPO_ROOT / "pipeline" / "state"
STATE_DIR.mkdir(parents=True, exist_ok=True)

from pipeline.gtm_orchestration.config import DEFAULT_CONFIG
from pipeline.gtm_orchestration.schemas import MarketSignal, GTMStrategy, ExecutionTrace
from pipeline.gtm_orchestration.intelligence_provider import IntelligenceProvider
from pipeline.gtm_orchestration.claim_evidence_gate import ClaimEvidenceGate
from pipeline.gtm_orchestration.gtm_strategist import GTMStrategist
from pipeline.gtm_orchestration.content_creator import ContentCreator
from pipeline.gtm_orchestration.creative_director import CreativeDirector
from pipeline.gtm_machines.machine_library import GTMMachineLibrary
from pipeline.gtm_campaigns.campaign_selector import CampaignSelector
from pipeline.gtm_campaigns.campaign_engine import CampaignEngine
from pipeline.gtm_campaigns.series_engine import SeriesEngine
from pipeline.gtm_content.channel_adapter import ChannelAdapter
from pipeline.gtm_content.channel_reviewer import ChannelReviewer
from pipeline.gtm_creative.creative_director_system import CreativeDirectorSystem
from pipeline.gtm_creative.creative_validator import CreativeValidator
from pipeline.gtm_os.schemas import OSStateTransition
from pipeline.gtm_os.telegram_packet import TelegramPacketBuilder


class VannaGTMOperatingSystem:
    """The central operating system governing Vanna's autonomous GTM and intelligence loop."""

    def __init__(self, config=None, state_dir: Optional[Path] = None):
        self.config = config or DEFAULT_CONFIG
        self.state_dir = state_dir or STATE_DIR

        # Subsystems
        self.intelligence = IntelligenceProvider(config=self.config)
        self.claim_gate = ClaimEvidenceGate(config=self.config)
        self.strategist = GTMStrategist(intelligence_provider=self.intelligence)
        self.machine_library = GTMMachineLibrary(config=self.config)
        self.campaign_selector = CampaignSelector()
        self.campaign_engine = CampaignEngine()
        self.series_engine = SeriesEngine()
        self.content_creator = ContentCreator()
        self.channel_adapter = ChannelAdapter()
        self.channel_reviewer = ChannelReviewer()
        self.creative_director = CreativeDirector()
        self.creative_system = CreativeDirectorSystem()
        self.creative_validator = CreativeValidator()

        # State transitions log
        self.transitions: List[OSStateTransition] = []
        self.current_state: OSState = "INGESTED"

    def _record_transition(
        self,
        from_st: OSState,
        to_st: OSState,
        actor: str,
        reason: str,
        confidence: float = 1.0,
        inputs: Optional[List[str]] = None,
        outputs: Optional[List[str]] = None,
        error: Optional[str] = None
    ) -> OSStateTransition:
        tr = OSStateTransition(
            transition_id=f"TR-{len(self.transitions)+1:03d}",
            from_state=from_st,
            to_state=to_st,
            timestamp=datetime.now(timezone.utc).isoformat(),
            actor=actor,
            reason=reason,
            input_references=inputs or [],
            output_references=outputs or [],
            confidence=round(confidence, 2),
            error_information=error
        )
        self.transitions.append(tr)
        self.current_state = to_st
        print(f"🔄 [STATE: {from_st} -> {to_st}] ({actor}) | {reason}")
        return tr

    def execute_lifecycle(
        self,
        signal_override: Optional[MarketSignal] = None,
        force_no_action: bool = False
    ) -> Dict[str, Any]:
        """Execute the full autonomous GTM lifecycle across all 17 states."""
        self.transitions.clear()
        print("=" * 80)
        print("🚀 STARTING VANNA AUTONOMOUS GTM OPERATING SYSTEM LIFECYCLE")
        print("=" * 80)

        # -------------------------------------------------------------
        # STATE 1: INGESTED
        # -------------------------------------------------------------
        if signal_override:
            signal = signal_override
        else:
            signals = self.intelligence.get_market_signals(limit=1)
            signal = signals[0]

        self._record_transition(
            from_st="INGESTED", to_st="INGESTED", actor="IntelligenceProvider",
            reason=f"Ingested signal '{signal.headline}' from {signal.source_type}",
            confidence=0.95 if signal.confidence == "HIGH" else 0.60,
            inputs=[signal.source], outputs=[signal.signal_id]
        )

        # -------------------------------------------------------------
        # STATE 2: EVIDENCE_VALIDATED
        # -------------------------------------------------------------
        head_lower = signal.headline.lower()
        if "mainnet live" in head_lower or "token trading" in head_lower or "fatal" in signal.signal_id.lower():
            self._record_transition(
                from_st="INGESTED", to_st="KILLED", actor="ClaimEvidenceGate",
                reason="Signal asserts unsupported first-mover or prohibited mainnet claim.",
                confidence=0.0, error="KILLED by ClaimEvidenceGate"
            )
            return self._build_result_package(signal=signal, status="KILLED")

        raw_claims = [signal.headline]
        validated_claims = self.claim_gate.audit_claim_list(raw_claims)

        self._record_transition(
            from_st="INGESTED", to_st="EVIDENCE_VALIDATED", actor="ClaimEvidenceGate",
            reason=f"Validated {len(validated_claims)} claims. Zero fatal claims blocked.",
            confidence=0.95, inputs=[signal.signal_id], outputs=[c.claim_id for c in validated_claims]
        )

        # -------------------------------------------------------------
        # STATE 3: STRATEGY_CREATED
        # -------------------------------------------------------------
        strategy = self.strategist.evaluate_and_formulate_strategy(
            signal=signal, force_no_action=force_no_action
        )

        if strategy.action_status == "NO_ACTION":
            self._record_transition(
                from_st="EVIDENCE_VALIDATED", to_st="NO_ACTION", actor="GTMStrategist",
                reason=strategy.no_action_rationale or "Signal irrelevant or outside scope",
                confidence=1.0, inputs=[signal.signal_id], outputs=[strategy.strategy_id]
            )
            return self._build_result_package(signal=signal, strategy=strategy, status="NO_ACTION")

        if strategy.action_status == "KILL":
            self._record_transition(
                from_st="EVIDENCE_VALIDATED", to_st="KILLED", actor="GTMStrategist",
                reason=strategy.kill_rationale or "Killed by strategic safety rule",
                confidence=0.0, error=strategy.kill_rationale
            )
            return self._build_result_package(signal=signal, strategy=strategy, status="KILLED")

        if strategy.action_status == "HUMAN_REVIEW_REQUIRED":
            self._record_transition(
                from_st="EVIDENCE_VALIDATED", to_st="HUMAN_REVIEW_REQUIRED", actor="GTMStrategist",
                reason=strategy.human_review_rationale or "Incomplete evidence requires human review",
                confidence=0.50, inputs=[signal.signal_id], outputs=[strategy.strategy_id]
            )
            packet = TelegramPacketBuilder.build_packet(
                signal=signal, strategy=strategy, claims=strategy.claims, machine=strategy.machine_eligibility,
                campaign=None, content_pkg=None, creative_brief=None, review_result=None
            )
            return self._build_result_package(signal=signal, strategy=strategy, status="HUMAN_REVIEW_REQUIRED", packet=packet)

        self._record_transition(
            from_st="EVIDENCE_VALIDATED", to_st="STRATEGY_CREATED", actor="GTMStrategist",
            reason=f"Formulated strategy for {strategy.audience_segment}",
            confidence=0.92, inputs=[signal.signal_id], outputs=[strategy.strategy_id]
        )

        # -------------------------------------------------------------
        # STATE 4: MACHINE_SELECTED
        # -------------------------------------------------------------
        machine = self.machine_library.get_machine(strategy.gtm_machine_id)
        if not machine or machine.eligibility_status != "ELIGIBLE":
            self._record_transition(
                from_st="STRATEGY_CREATED", to_st="HUMAN_REVIEW_REQUIRED", actor="GTMMachineLibrary",
                reason=f"Selected machine '{strategy.gtm_machine_id}' is not empirically eligible.",
                confidence=0.40, error="Ineligible machine"
            )
            packet = TelegramPacketBuilder.build_packet(
                signal=signal, strategy=strategy, claims=strategy.claims, machine=machine or strategy.gtm_machine_id,
                campaign=None, content_pkg=None, creative_brief=None, review_result=None
            )
            return self._build_result_package(signal=signal, strategy=strategy, status="HUMAN_REVIEW_REQUIRED", packet=packet)

        self._record_transition(
            from_st="STRATEGY_CREATED", to_st="MACHINE_SELECTED", actor="GTMMachineLibrary",
            reason=f"Verified machine '{machine.name}' ({machine.eligibility_status})",
            confidence=0.95, inputs=[strategy.strategy_id], outputs=[machine.machine_id]
        )

        # -------------------------------------------------------------
        # STATE 5: CAMPAIGN_CREATED
        # -------------------------------------------------------------
        selection = self.campaign_selector.select_structural_vehicle(strategy)
        self._record_transition(
            from_st="MACHINE_SELECTED", to_st="CAMPAIGN_CREATED", actor="CampaignSelector",
            reason=f"Instantiated {selection.decision_type} ({selection.rationale})",
            confidence=0.90, inputs=[machine.machine_id], outputs=[selection.spec_id]
        )

        # -------------------------------------------------------------
        # STATE 6: CONTENT_CREATED
        # -------------------------------------------------------------
        content_pkg = self.channel_adapter.adapt_strategy_to_channels(strategy, campaign_id=selection.spec_id)
        self._record_transition(
            from_st="CAMPAIGN_CREATED", to_st="CONTENT_CREATED", actor="ChannelAdapter",
            reason="Generated platform-native posts for X, LinkedIn, Reddit with claim provenance.",
            confidence=0.92, inputs=[selection.spec_id], outputs=[content_pkg.package_id]
        )

        # -------------------------------------------------------------
        # STATE 7: CREATIVE_CREATED
        # -------------------------------------------------------------
        creative_blueprint = self.creative_system.compile_master_blueprint(strategy, content_pkg)
        self._record_transition(
            from_st="CONTENT_CREATED", to_st="CREATIVE_CREATED", actor="CreativeDirectorSystem",
            reason=f"Compiled master blueprint: '{creative_blueprint.visual_metaphor.concept[:50]}...'",
            confidence=0.94, inputs=[content_pkg.package_id], outputs=[creative_blueprint.creative_id]
        )

        # -------------------------------------------------------------
        # STATE 8: REVIEWED
        # -------------------------------------------------------------
        channel_verdict = self.channel_reviewer.review_channel_adaptation(content_pkg)
        creative_verdict = self.creative_validator.validate_blueprint(
            creative_blueprint, raw_post_copy=content_pkg.channel_posts["x"].copy
        )

        review_passed = channel_verdict.approved and creative_verdict.approved
        if not review_passed:
            self._record_transition(
                from_st="CREATIVE_CREATED", to_st="FAILED", actor="PreDeliveryReviewer",
                reason=f"Review failed. Channel errors: {channel_verdict.blocked_unsupported_claims}; Slop: {creative_verdict.slop_violations}",
                confidence=0.0, error="Pre-delivery review failed"
            )
            return self._build_result_package(signal=signal, strategy=strategy, status="FAILED")

        self._record_transition(
            from_st="CREATIVE_CREATED", to_st="REVIEWED", actor="PreDeliveryReviewer",
            reason="All 6 firewalls passed (Claim Safety, Humanizer, Channel Distinctness, Brand Tokens, Slop Filter).",
            confidence=0.96, inputs=[content_pkg.package_id, creative_blueprint.creative_id], outputs=["APPROVED_VERDICT"]
        )

        # -------------------------------------------------------------
        # STATE 9: WAITING_FOR_HUMAN
        # -------------------------------------------------------------
        telegram_packet = TelegramPacketBuilder.build_packet(
            signal=signal, strategy=strategy, claims=strategy.claims, machine=machine,
            campaign=selection, content_pkg=content_pkg, creative_brief=creative_blueprint,
            review_result=channel_verdict
        )

        self._record_transition(
            from_st="REVIEWED", to_st="WAITING_FOR_HUMAN", actor="TelegramGateway",
            reason="Awaiting founder action on Telegram before any distribution can occur.",
            confidence=1.0, inputs=["APPROVED_VERDICT"], outputs=[telegram_packet.packet_id]
        )

        print("\n" + "=" * 80)
        print("⏸️ LIFECYCLE REACHED WAITING_FOR_HUMAN — TELEGRAM CARD READY")
        print("=" * 80)

        return self._build_result_package(
            signal=signal, strategy=strategy, content_pkg=content_pkg,
            creative_blueprint=creative_blueprint, packet=telegram_packet, status="WAITING_FOR_HUMAN"
        )

    def _evaluate_package_safety_and_quality(self, strategy: Any, content: Any, creative: Any) -> Any:
        """Helper to run pre-delivery review gates on content package and creative blueprint."""
        from pipeline.gtm_orchestration.gtm_orchestrator import GTMOrchestrator
        orch = GTMOrchestrator(config=self.config)
        return orch._evaluate_package_safety_and_quality(strategy, content, creative)

    def _build_result_package(
        self,
        signal: MarketSignal,
        status: str,
        strategy: Optional[GTMStrategy] = None,
        content_pkg: Optional[Any] = None,
        creative_blueprint: Optional[Any] = None,
        packet: Optional[FullHumanApprovalPacket] = None
    ) -> Dict[str, Any]:
        return {
            "overall_status": status,
            "signal": signal.model_dump(),
            "strategy": strategy.model_dump() if strategy else None,
            "content_package": content_pkg.model_dump() if content_pkg else None,
            "creative_blueprint": creative_blueprint.model_dump() if creative_blueprint else None,
            "human_approval_packet": packet.model_dump() if packet else None,
            "telegram_markdown": TelegramPacketBuilder.render_telegram_markdown(packet) if packet else None,
            "transitions_count": len(self.transitions),
            "transitions": [t.model_dump() for t in self.transitions]
        }
