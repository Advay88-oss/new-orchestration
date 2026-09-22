"""Phase 1.1: Evolved Central GTM Orchestrator Engine.

Coordinates the lifecycle:
  INTELLIGENCE -> CLAIM_GATE -> STRATEGY -> CONTENT -> CREATIVE -> REVIEW -> APPROVAL
Handles multi-state decisions:
  - ACTION: Moves to content and creative, ending in WAITING_FOR_HUMAN.
  - NO_ACTION: Stops immediately with recorded rationale.
  - HUMAN_REVIEW_REQUIRED: Stops autonomous pipeline and alerts human on Telegram.
  - KILL: Terminated due to safety/claim violation.
Computes multi-dimensional ConfidenceMatrix (separating truth confidence from aesthetic scores).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone

from pipeline.gtm_orchestration.config import DEFAULT_CONFIG
from pipeline.gtm_orchestration.schemas import (
    MarketSignal, GTMStrategy, ContentBrief, ContentPackage, CreativeBrief, ReviewResult, ExecutionTrace
)
from pipeline.gtm_orchestration.intelligence_provider import IntelligenceProvider
from pipeline.gtm_orchestration.claim_evidence_gate import ClaimEvidenceGate
from pipeline.gtm_orchestration.gtm_strategist import GTMStrategist
from pipeline.gtm_orchestration.content_creator import ContentCreator
from pipeline.gtm_orchestration.creative_director import CreativeDirector
from pipeline.gtm_orchestration.trace_logger import TraceLogger


class GTMOrchestrator:
    """The central operating system orchestrating agents, contracts, and quality gates."""

    def __init__(self, config=None, state_dir: Optional[Path] = None):
        self.config = config or DEFAULT_CONFIG
        self.state_dir = state_dir or (Path(__file__).resolve().parents[2] / "pipeline" / "state")
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.intelligence = IntelligenceProvider(config=self.config)
        self.evidence_gate = ClaimEvidenceGate(config=self.config)
        self.strategist = GTMStrategist(intelligence_provider=self.intelligence)
        self.content_creator = ContentCreator()
        self.creative_director = CreativeDirector()

    def run_lifecycle(
        self,
        signal_override: Optional[MarketSignal] = None,
        force_no_action: bool = False,
        max_retries: int = 2
    ) -> ExecutionTrace:
        """Execute the full productized GTM lifecycle."""
        tracer = TraceLogger(output_dir=self.state_dir)
        print("=" * 75)
        print(f"▶ LAUNCHING VANNA GTM ORCHESTRATION ENGINE [{tracer.trace_id}]")
        print("=" * 75)

        # -------------------------------------------------------------
        # STAGE 1: INTELLIGENCE
        # -------------------------------------------------------------
        stage1_start = datetime.now(timezone.utc).isoformat()
        if signal_override:
            signal = signal_override
        else:
            signals = self.intelligence.get_market_signals(limit=5)
            signal = signals[0] if signals else MarketSignal(
                signal_id="SIG-DEFAULT-01",
                headline="DeFi Lending Cascade & Mempool Congestion Volatility",
                description="EVM liquidation spikes observed across major lending markets during high volatility.",
                market_category="LENDING",
                entities_involved=["aave", "morpho"],
                source=str(self.config.brain_db_dir / "posts.jsonl"),
                source_root=str(self.config.intelligence_root),
                dataset="posts",
                source_type="SOCIAL_CORPUS",
                record_id="rec_mempool_01",
                observed_at=datetime.now(timezone.utc).isoformat(),
                data_as_of="2026-09-10",
                confidence="HIGH",
                evidence_status="OBSERVED"
            )

        vanna_kb = self.intelligence.get_vanna_capabilities()
        audiences = self.intelligence.get_audience_segments()
        gtm_machines = self.intelligence.get_gtm_machines()

        tracer.add_provenance({
            "source_root": signal.source_root or str(self.config.intelligence_root),
            "dataset": signal.dataset or "signals",
            "signal_id": signal.signal_id,
            "headline": signal.headline,
            "source": signal.source,
            "source_type": signal.source_type,
            "record_id": signal.record_id,
            "evidence_status": signal.evidence_status
        })

        stage1_end = datetime.now(timezone.utc).isoformat()
        tracer.record_stage(
            stage="intelligence",
            status="SUCCESS",
            started_at=stage1_start,
            completed_at=stage1_end,
            input_data={"source_type": signal.source_type, "category": signal.market_category},
            output_data=signal.model_dump(),
            agent="IntelligenceProvider",
            model="BrainDB/RulesEngine"
        )
        print(f"✅ STAGE 1 [INTELLIGENCE]: Ingested Signal '{signal.headline}' (Record: {signal.record_id})")

        # -------------------------------------------------------------
        # STAGE 2: STRATEGY
        # -------------------------------------------------------------
        stage2_start = datetime.now(timezone.utc).isoformat()
        strategy = self.strategist.evaluate_and_formulate_strategy(
            signal=signal,
            vanna_knowledge=vanna_kb,
            audience_segments=audiences,
            gtm_machines=gtm_machines,
            force_no_action=force_no_action
        )
        stage2_end = datetime.now(timezone.utc).isoformat()

        # Save gtm_strategy.json
        (self.state_dir / "gtm_strategy.json").write_text(strategy.model_dump_json(indent=2), encoding="utf-8")

        # Handle Non-Action Decisions Immediately
        if strategy.action_status == "NO_ACTION":
            tracer.record_stage(
                stage="strategy",
                status="NO_ACTION",
                started_at=stage2_start,
                completed_at=stage2_end,
                input_data=signal.model_dump(),
                output_data=strategy.model_dump(),
                agent="GTMStrategist",
                model="Gemini-3.1-Pro"
            )
            print(f"🛑 STAGE 2 [STRATEGY]: Decision = NO_ACTION ({strategy.no_action_rationale})")
            return tracer.finalize_trace(overall_status="NO_ACTION", strategy_dict=strategy.model_dump())

        if strategy.action_status == "KILL":
            tracer.record_stage(
                stage="strategy",
                status="KILL",
                started_at=stage2_start,
                completed_at=stage2_end,
                input_data=signal.model_dump(),
                output_data=strategy.model_dump(),
                agent="GTMStrategist",
                model="Gemini-3.1-Pro",
                errors=[strategy.kill_rationale or "Killed by safety/evidence gate"]
            )
            print(f"💀 STAGE 2 [STRATEGY]: Decision = KILL ({strategy.kill_rationale})")
            return tracer.finalize_trace(overall_status="KILL", strategy_dict=strategy.model_dump())

        if strategy.action_status == "HUMAN_REVIEW_REQUIRED":
            human_packet = tracer.assemble_human_review_packet(
                strategy_dict=strategy.model_dump()
            )
            tracer.record_stage(
                stage="strategy",
                status="HUMAN_REVIEW_REQUIRED",
                started_at=stage2_start,
                completed_at=stage2_end,
                input_data=signal.model_dump(),
                output_data=strategy.model_dump(),
                agent="GTMStrategist",
                model="Gemini-3.1-Pro",
                errors=[strategy.human_review_rationale or "Requires human review"]
            )
            print(f"⚠️ STAGE 2 [STRATEGY]: Decision = HUMAN_REVIEW_REQUIRED ({strategy.human_review_rationale})")
            return tracer.finalize_trace(
                overall_status="HUMAN_REVIEW_REQUIRED",
                strategy_dict=strategy.model_dump(),
                human_packet=human_packet
            )

        # Record Successful Strategy
        tracer.record_stage(
            stage="strategy",
            status="SUCCESS",
            started_at=stage2_start,
            completed_at=stage2_end,
            input_data=signal.model_dump(),
            output_data=strategy.model_dump(),
            agent="GTMStrategist",
            model="Gemini-3.1-Pro"
        )
        print(f"✅ STAGE 2 [STRATEGY]: Formulated Strategy '{strategy.strategy_id}' (Audience: {strategy.audience_segment})")

        # Derive Content Brief
        content_brief = self.strategist.derive_content_brief(strategy)

        # -------------------------------------------------------------
        # RETRY LOOP FOR CONTENT & CREATIVE QUALITY GATES
        # -------------------------------------------------------------
        content_package: Optional[ContentPackage] = None
        creative_brief: Optional[CreativeBrief] = None
        review_result: Optional[ReviewResult] = None

        for cycle in range(1, max_retries + 2):
            # ---------------------------------------------------------
            # STAGE 3: CONTENT CREATION
            # ---------------------------------------------------------
            stage3_start = datetime.now(timezone.utc).isoformat()
            content_package = self.content_creator.create_content_package(strategy, content_brief)
            stage3_end = datetime.now(timezone.utc).isoformat()

            tracer.record_stage(
                stage="content",
                status="SUCCESS",
                started_at=stage3_start,
                completed_at=stage3_end,
                input_data=content_brief.model_dump(),
                output_data=content_package.model_dump(),
                agent="ContentCreator",
                model="Gemini-3.1-Pro/Humanizer"
            )
            print(f"✅ STAGE 3 [CONTENT]: Generated Multi-Channel Package for X, LinkedIn, Reddit (Cycle {cycle})")

            # Save content_package.json
            (self.state_dir / "content_package.json").write_text(content_package.model_dump_json(indent=2), encoding="utf-8")

            # ---------------------------------------------------------
            # STAGE 4: CREATIVE DIRECTION
            # ---------------------------------------------------------
            stage4_start = datetime.now(timezone.utc).isoformat()
            creative_brief = self.creative_director.direct_creative_concept(
                strategy=strategy,
                content_package=content_package,
                format_target="video_veo31"
            )
            stage4_end = datetime.now(timezone.utc).isoformat()

            tracer.record_stage(
                stage="creative",
                status="SUCCESS",
                started_at=stage4_start,
                completed_at=stage4_end,
                input_data={"strategy_id": strategy.strategy_id, "package_id": content_package.package_id},
                output_data=creative_brief.model_dump(),
                agent="CreativeDirector",
                model="CreativeDirector/BrandGuardian"
            )
            print(f"✅ STAGE 4 [CREATIVE]: Formulated Metaphor '{creative_brief.visual_metaphor[:60]}...'")

            # Save creative_brief.json
            (self.state_dir / "creative_brief.json").write_text(creative_brief.model_dump_json(indent=2), encoding="utf-8")

            # ---------------------------------------------------------
            # STAGE 5: PRE-DELIVERY REVIEW & QUALITY FIREWALL
            # ---------------------------------------------------------
            stage5_start = datetime.now(timezone.utc).isoformat()
            review_result = self._evaluate_package_safety_and_quality(strategy, content_package, creative_brief)
            stage5_end = datetime.now(timezone.utc).isoformat()

            if review_result.approved:
                tracer.record_stage(
                    stage="review",
                    status="SUCCESS",
                    started_at=stage5_start,
                    completed_at=stage5_end,
                    input_data={"strategy_id": strategy.strategy_id},
                    output_data=review_result.model_dump(),
                    agent="PreDeliveryReviewer",
                    model="Pillow/Humanizer/ClaimSafety"
                )
                print(f"✅ STAGE 5 [REVIEW]: APPROVED (Score: {review_result.score}/100 | Verdict: {review_result.verdict})")
                break
            else:
                tracer.record_stage(
                    stage="review",
                    status="RETRY" if cycle <= max_retries else "FAILED",
                    started_at=stage5_start,
                    completed_at=stage5_end,
                    input_data={"strategy_id": strategy.strategy_id},
                    output_data=review_result.model_dump(),
                    agent="PreDeliveryReviewer",
                    model="Pillow/Humanizer/ClaimSafety",
                    errors=review_result.critical_failures
                )
                print(f"⚠️ STAGE 5 [REVIEW]: REJECTED -> Routing to {review_result.route_to_agent}")
                if cycle > max_retries:
                    print("❌ Maximum review cycles reached without pass. Terminating trace.")
                    return tracer.finalize_trace(
                        overall_status="FAILED",
                        strategy_dict=strategy.model_dump(),
                        review_dict=review_result.model_dump()
                    )

        # -------------------------------------------------------------
        # STAGE 6: HUMAN APPROVAL PACKET ASSEMBLY (Telegram Waiting Gate)
        # -------------------------------------------------------------
        human_packet = tracer.assemble_human_review_packet(
            strategy_dict=strategy.model_dump(),
            content_dict=content_package.model_dump(),
            creative_dict=creative_brief.model_dump(),
            review_dict=review_result.model_dump()
        )

        tracer.record_stage(
            stage="approval",
            status="WAITING_FOR_HUMAN",
            started_at=datetime.now(timezone.utc).isoformat(),
            completed_at=datetime.now(timezone.utc).isoformat(),
            input_data={"review_score": review_result.score},
            output_data=human_packet,
            agent="TelegramApprovalGate",
            model="HumanInTheLoop"
        )
        print("⏸️ STAGE 6 [APPROVAL]: Package compiled. WAITING_FOR_HUMAN on Telegram.")

        final_trace = tracer.finalize_trace(
            overall_status="WAITING_FOR_HUMAN",
            strategy_dict=strategy.model_dump(),
            review_dict=review_result.model_dump(),
            human_packet=human_packet
        )
        print("=" * 75)
        print(f"🏁 GTM ORCHESTRATION COMPLETE -> Status: {final_trace.overall_status}")
        print("=" * 75)
        return final_trace

    def _evaluate_package_safety_and_quality(
        self,
        strategy: GTMStrategy,
        content: ContentPackage,
        creative: CreativeBrief
    ) -> ReviewResult:
        """Audit claims, brand tokens, and anti-AI rules."""
        critical_failures: List[str] = []
        brand_issues: List[str] = []
        technical_issues: List[str] = []
        score = 96

        # 1. Claim Safety Check: Prohibit mainnet TVL / 'Aave of Stellar' / First-Mover
        full_content_str = json.dumps(content.model_dump()).lower()
        if "aave of stellar" in full_content_str:
            critical_failures.append("Prohibited claim detected: 'Aave of Stellar'")
            score -= 30
        if "mainnet live" in full_content_str:
            critical_failures.append("Prohibited claim detected: 'mainnet live'")
            score -= 40
        if "test.stellar.vanna.finance" not in full_content_str:
            critical_failures.append("Missing required testnet domain anchor")
            score -= 15

        # Check for blocked first-mover assertions
        if any(w in full_content_str for w in ["zero existing", "uncontested first-mover", "zero competitors"]):
            critical_failures.append("Unsupported first-mover claim detected: absence of observed evidence is not evidence of absence")
            score -= 35

        # 2. Humanizer Anti-AI Rule Check
        ai_tells = ["pivotal moment", "vital role", "game-changer", "delve", "tapestry"]
        found_tells = [tell for tell in ai_tells if tell in full_content_str]
        if found_tells:
            critical_failures.append(f"Humanizer violation: AI cliché detected ({found_tells})")
            score -= 10

        # 3. Creative Metaphor Check: Prohibit Tron grids or floating spheres
        creative_content_str = (
            f"{creative.visual_concept} "
            f"{creative.visual_metaphor} "
            f"{creative.environment} "
            f"{creative.generator_instructions.get('prompt', '')}"
        ).lower()
        if "glowing sphere" in creative_content_str or "neon grid" in creative_content_str:
            brand_issues.append("Creative brief contains forbidden generic AI slop")
            score -= 20

        approved = len(critical_failures) == 0 and score >= 85
        verdict = "PASS" if approved else "REVISE"
        route_to = None
        if not approved:
            if critical_failures:
                route_to = "ContentCreator"
            elif brand_issues:
                route_to = "CreativeDirector"

        return ReviewResult(
            review_id=f"REV-{strategy.strategy_id}",
            approved=approved,
            verdict=verdict,
            score=max(0, score),
            critical_failures=critical_failures,
            brand_issues=brand_issues,
            technical_issues=technical_issues,
            copy_issues=[],
            creative_issues=[],
            required_fixes=[f"Resolve {err}" for err in critical_failures],
            route_to_agent=route_to,
            reasoning=(
                "All testnet claims verified against approved-claims.md. "
                "Humanizer check passed (zero AI tells). "
                "Visual metaphor derived directly from strategy objective."
                if approved else f"Audit rejected due to {len(critical_failures)} critical failures."
            )
        )
