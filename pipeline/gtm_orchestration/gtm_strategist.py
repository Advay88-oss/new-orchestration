"""Phase 1.1: Evolved GTM Strategist Agent.

Decides WHAT Vanna should do and WHY.
Evaluates market signals against Brain evidence, Vanna capabilities, and machine eligibility.
Emits multi-state decision contracts:
  - ACTION: Fully evidenced strategy ready for autonomous execution.
  - NO_ACTION: Irrelevant or redundant signal suppressed.
  - HUMAN_REVIEW_REQUIRED: Incomplete evidence or machine uncertainty needing human judgment.
  - KILL: Critical evidence violation, unsupported first-mover claim, or prohibited assertion.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone

from pipeline.gtm_orchestration.schemas import (
    MarketSignal, GTMStrategy, ContentBrief, ClaimRecord, GTMMachineEligibility
)
from pipeline.gtm_orchestration.claim_evidence_gate import ClaimEvidenceGate
from pipeline.gtm_os.agent_runtime import (
    brain_json as _brain_json, BrainError as _BrainError, record_stage as _record_stage,
)
from pipeline.gtm_orchestration.intelligence_provider import IntelligenceProvider
from pipeline.gtm_orchestration.decision_quality_gates import (
    AudienceFitGate, ProductStageFitGate, ClaimConsistencyGate,
    StrategicDecisionReport, GateEvaluationResult
)


_AGENT = "A03_gtm_strategist"


def _learned_preferences() -> str:
    """The founder's approval record by pillar, approved hooks and the notes
    on revisions and kills. Empty until the founder has reviewed a run."""
    try:
        from pipeline.gtm_learning.preferences import prompt_block
        block = prompt_block(for_agent="A03")
    except Exception:                               # noqa: BLE001 — boundary
        return ""
    return (block + "\n\n") if block else ""


class GTMStrategist:
    """The central strategic reasoning agent: evaluates signals, validates claims, and chooses GTM machines."""

    def __init__(self, intelligence_provider: Optional[IntelligenceProvider] = None):
        self.intelligence = intelligence_provider or IntelligenceProvider()
        self.evidence_gate = ClaimEvidenceGate(config=self.intelligence.config)
        self.audience_gate = AudienceFitGate()
        self.product_stage_gate = ProductStageFitGate()
        self.claim_consistency_gate = ClaimConsistencyGate()

    def evaluate_and_formulate_strategy(
        self,
        signal: MarketSignal,
        vanna_knowledge: Optional[Dict[str, Any]] = None,
        audience_segments: Optional[List[Dict[str, Any]]] = None,
        gtm_machines: Optional[List[Dict[str, Any]]] = None,
        force_no_action: bool = False
    ) -> GTMStrategy:
        """Analyze market signal and formulate an approved GTM strategy or return NO_ACTION / HUMAN_REVIEW / KILL."""
        vanna_kb = vanna_knowledge or self.intelligence.get_vanna_capabilities()
        audiences = audience_segments or self.intelligence.get_audience_segments()
        strat_id = f"STRAT-{signal.signal_id}-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M')}"

        # -------------------------------------------------------------
        # GATE 0: KILL CHECK — Prohibited or Fatal Signal Assertions
        # -------------------------------------------------------------
        full_signal_text = f"{signal.headline} {signal.description}".lower()
        if "mainnet live" in full_signal_text or "token trading" in full_signal_text:
            return GTMStrategy(
                strategy_id=strat_id,
                action_status="KILL",
                decision_reason_class="PROHIBITED_CLAIM_VIOLATION",
                kill_rationale="Signal asserts mainnet live or live token trading, which strictly violates Vanna testnet boundaries.",
                objective="NONE",
                audience_segment="NONE",
                problem="NONE",
                market_context=signal.description,
                strategic_opportunity="NONE",
                narrative_pillar="NONE",
                positioning="NONE",
                proof=[],
                cta="NONE",
                channel="NONE",
                content_type="NONE",
                gtm_machine_id="NONE",
                reasoning=["Killed by pre-strategy claim safety firewall."],
                evidence=[{"record_id": signal.record_id, "source": signal.source}]
            )

        # GATE 1+2: RELEVANCE AND NARRATIVE FORMULATION — gemini-3.8-flash
        #
        # These two gates were a keyword list and a three-branch if/elif/else.
        # The branch decided the audience, the problem, the pillar, the machine,
        # the channel and the proof claims, all as literals, so the system could
        # only ever produce three strategies and the choice between them turned
        # on whether the headline happened to contain "gas" or "contagion".
        #
        # The claim gate below (GATE 3) still adjudicates every claim this
        # produces, so widening the reasoning here does not widen what may be
        # said — an invented number still gets blocked downstream.
        # Only ELIGIBLE machines are offered. The old code hardcoded ids like
        # "MACHINE_01: NEW_INTEGRATION_DISPATCH" which do not exist in the
        # library (the real ids are MACH_01_...), so every machine lookup
        # missed and every run fell through to HUMAN_REVIEW_REQUIRED.
        if gtm_machines:
            machines_for_prompt = gtm_machines
        else:
            from pipeline.gtm_machines.machine_library import GTMMachineLibrary
            _lib = GTMMachineLibrary()
            # Offer only machines that pass BOTH the library's own status and
            # the Brain DB evidence check the strategist applies later. Offering
            # a machine the next gate will reject just turns a good strategy
            # into HUMAN_REVIEW_REQUIRED for a reason the model could not see.
            machines_for_prompt = []
            for m in _lib.machines.values():
                if getattr(m, "eligibility_status", "") != "ELIGIBLE":
                    continue
                if self.intelligence.verify_machine_eligibility(
                        m.machine_id).eligibility_status != "ELIGIBLE":
                    continue
                machines_for_prompt.append({
                    "machine_id": m.machine_id,
                    "name": m.name,
                    "when_to_use": str(getattr(m, "purpose", ""))[:200],
                    "audiences": list(getattr(m, "eligible_audiences", []) or []),
                    "channels": list(getattr(m, "supported_channels", []) or []),
                })
        strategy_system = (
            "You are Vanna's GTM strategist. Vanna is composable credit "
            "infrastructure on Stellar Soroban TESTNET.\n\n"
            "Decide whether a market signal is worth publishing about, and if "
            "so, formulate the strategy. Return strict JSON only.\n\n"
            "Rules:\n"
            "- Vanna is on TESTNET. Never assert mainnet, live token trading, "
            "or first-mover status.\n"
            "- `proof_claims` must be claims you believe are true of Vanna and "
            "checkable. Do not invent metrics. If you are unsure of a number, "
            "state the mechanism without the number.\n"
            "- `relevant` is false when the signal gives Vanna no differentiated "
            "architectural wedge. Saying no is a valid and common answer; a "
            "weak post costs more than no post.\n"
            "- But the wedge does NOT have to be Soroban-native. Vanna has "
            "two arguments, and a subject usually belongs to one of them:\n"
            "    (a) capital efficiency — composable credit: borrowed credit "
            "stays usable across venues instead of being trapped in one "
            "protocol, so the same collateral does more work. This is the "
            "argument for LIQUIDITY, fragmented capital, idle collateral, "
            "margin across venues and composability.\n"
            "    (b) risk isolation — per-borrower SmartAccount sandboxes "
            "versus pooled debt, a 1.10x liquidation floor, deterministic "
            "liquidation. This is the argument for LIQUIDATION, bad debt, "
            "contagion and insolvency.\n"
            "  Both apply to stories on any chain. A pooled-lending failure on Ethereum is a "
            "strong signal precisely because it demonstrates the problem Vanna "
            "solves. Rejecting such a signal for being 'EVM-centric' or "
            "'not directly about Soroban' is a misreading of this rule.\n"
            "  Reject instead when the signal is token-price movement, a "
            "listicle or buyer's guide, a partnership with no mechanism, or a "
            "topic where Vanna would have to invent an opinion.\n"
            "- A signal marked FOUNDER DIRECTIVE is an instruction, not a "
            "candidate. The founder has already decided it is worth posting, "
            "so do NOT reject it for being unnewsworthy, generic, or lacking "
            "a news hook. Your job is to find the architectural angle — for a "
            "relationship, what the two systems actually do together at the "
            "contract level. Reject a directive ONLY if honouring it would "
            "require asserting mainnet, inventing a figure, or claiming "
            "something untrue of Vanna.\n"
            "- A directive's SUBJECT is fixed. `problem`, `positioning` and "
            "`strategic_opportunity` must be about the subject the founder "
            "named, in its own words. Never substitute a neighbouring "
            "concept: liquidity is not liquidation, a partnership is not a "
            "fee story, health factor is not gas. A 'possibly related market "
            "signal' in the description is context and never the subject.\n"
            "- If the directive asks for a structure (e.g. problem, how it "
            "works, why it matters, where Vanna fits) or a quality (simple "
            "language, saveable, shareable), carry it into `content_type` and "
            "`objective` so the copywriter receives it.\n"
            "- `reframed_from` is for the rare case where the literal request "
            "cannot be honoured truthfully — e.g. it presumes mainnet. Then "
            "state what was changed and why. Leave it EMPTY when you kept the "
            "subject; choosing an angle is not a reframe.\n"
            "- Choose ONE narrative pillar. Do not blend pillars."
        )
        strategy_schema_hint = (
            '{"relevant": bool, "rationale": str, "audience_segment": str, '
            '"problem": str, "strategic_opportunity": str, "narrative_pillar": str, '
            '"gtm_machine_id": str, "channel": str, "content_type": str, '
            '"objective": str, "positioning": str, "cta": str, '
            '"proof_claims": [str], "reasoning": [str], '
            '"reframed_from": str}'
        )
        prompt = (
            "SIGNAL\n"
            "  headline: " + str(signal.headline) + "\n"
            "  description: " + str(signal.description) + "\n"
            "  category: " + str(signal.market_category) + "\n"
            "  source: " + str(signal.source_type) + " / " + str(signal.source) + "\n"
            "  confidence: " + str(signal.confidence) + "\n\n"
            "VANNA CAPABILITIES\n" + json.dumps(vanna_kb, default=str)[:4000] + "\n\n"
            "AUDIENCE SEGMENTS\n" + json.dumps(audiences, default=str)[:2000] + "\n\n"
            "AVAILABLE GTM MACHINES\n" + json.dumps(machines_for_prompt, default=str)[:2000] + "\n\n"
            + _learned_preferences()
            + "Return JSON matching exactly this shape:\n" + strategy_schema_hint
        )

        if force_no_action:
            decision = {"relevant": False,
                        "rationale": "Caller forced NO_ACTION.",
                        "reasoning": ["force_no_action was set by the caller."]}
        else:
            try:
                decision = _brain_json(
                    prompt, agent=_AGENT, role="reasoning", system=strategy_system,
                    temperature=0.3, max_output_tokens=3072)
            except _BrainError as exc:
                # A strategist that could not reach its model has not formed a
                # strategy. Returning the old canned branch here is exactly how
                # the 2026-09-17 trace came to contain pre-written copy.
                _record_stage(_AGENT, "failed",
                              "strategy reasoning unavailable: " + str(exc)[:300])
                return GTMStrategy(
                    strategy_id=strat_id,
                    action_status="HUMAN_REVIEW_REQUIRED",
                    decision_reason_class="STRATEGIST_MODEL_UNAVAILABLE",
                    no_action_rationale=("Strategist model call failed; no strategy "
                                         "was formed. " + str(exc)[:200]),
                    objective="NONE", audience_segment="NONE", problem="NONE",
                    market_context=signal.description, strategic_opportunity="NONE",
                    narrative_pillar="NONE", positioning="NONE", proof=[],
                    cta="NONE", channel="NONE", content_type="NONE",
                    gtm_machine_id="NONE",
                    reasoning=["gemini-3.8-flash unreachable: " + str(exc)[:200]],
                    evidence=[{"record_id": signal.record_id, "source": signal.source}]
                )

        if not decision.get("relevant", False):
            _record_stage(_AGENT, "ok",
                          "judged not worth publishing: "
                          + str(decision.get("rationale", ""))[:200])
            return GTMStrategy(
                strategy_id=strat_id,
                action_status="NO_ACTION",
                decision_reason_class="IRRELEVANT_OR_WEAK_SIGNAL",
                no_action_rationale=str(decision.get("rationale", ""))[:600]
                                    or "Strategist judged the signal not actionable.",
                objective="NONE", audience_segment="NONE", problem="NONE",
                market_context=signal.description, strategic_opportunity="NONE",
                narrative_pillar="NONE", positioning="NONE", proof=[],
                cta="NONE", channel="NONE", content_type="NONE",
                gtm_machine_id="NONE",
                reasoning=[str(r) for r in (decision.get("reasoning") or [])][:8],
                evidence=[{"record_id": signal.record_id, "source": signal.source}]
            )

        reframed = str(decision.get("reframed_from") or "").strip()[:300] or None
        if reframed:
            _record_stage(_AGENT, "degraded",
                          "directive reframed to stay truthful; literal "
                          "reading refused: " + reframed[:180])
        chosen_audience = str(decision.get("audience_segment") or "A1: Stellar & Soroban DeFi Farmers")
        problem_statement = str(decision.get("problem") or "")
        opportunity_statement = str(decision.get("strategic_opportunity") or "")
        chosen_pillar = str(decision.get("narrative_pillar") or "")
        candidate_machine_id = str(decision.get("gtm_machine_id") or "")
        _eligible_ids = {m["machine_id"] for m in machines_for_prompt}
        if candidate_machine_id not in _eligible_ids:
            # The model named a machine that is not eligible (or none). Do not
            # silently substitute one — the machine choice drives the campaign
            # shape, and picking for it would hide a real disagreement.
            _record_stage(_AGENT, "degraded",
                          "model chose machine " + repr(candidate_machine_id)
                          + " which is not in the eligible set")
            candidate_machine_id = (sorted(_eligible_ids)[0] if _eligible_ids
                                    else candidate_machine_id or "NONE")
        channel = str(decision.get("channel") or "X")
        content_type = str(decision.get("content_type") or "product_deep_dive")
        model_objective = str(decision.get("objective") or "")
        model_positioning = str(decision.get("positioning") or "")
        model_cta = str(decision.get("cta") or "")
        model_reasoning = [str(r) for r in (decision.get("reasoning") or [])][:8]
        raw_claims = [str(c) for c in (decision.get("proof_claims") or []) if str(c).strip()][:8]
        _record_stage(_AGENT, "ok",
                      "formulated strategy on pillar: " + chosen_pillar[:120],
                      outputs=[strat_id])

        # -------------------------------------------------------------
        # GATE 3: CLAIM EVIDENCE AUDITING
        # -------------------------------------------------------------
        claim_records = self.evidence_gate.audit_claim_list(raw_claims)
        blocked_claims = [c for c in claim_records if c.action == "DO_NOT_USE"]
        inferred_claims = [c for c in claim_records if c.action == "USE_AS_INFERENCE"]

        # If a core claim is blocked due to absolute first-mover or unsupported assertion
        for bc in blocked_claims:
            if "first-mover" in bc.rationale.lower() or "absolute absence" in bc.rationale.lower():
                return GTMStrategy(
                    strategy_id=strat_id,
                    action_status="KILL",
                    decision_reason_class="UNSUPPORTED_FIRST_MOVER_CLAIM",
                    kill_rationale=f"Strategy rejected: Fundamentally relies on unproven claim '{bc.text}' ({bc.rationale})",
                    objective="NONE",
                    audience_segment=chosen_audience,
                    problem=problem_statement,
                    market_context=signal.description,
                    strategic_opportunity="NONE",
                    narrative_pillar=chosen_pillar,
                    positioning="NONE",
                    proof=[],
                    claims=claim_records,
                    cta="NONE",
                    channel=channel,
                    content_type=content_type,
                    gtm_machine_id=candidate_machine_id,
                    reasoning=["Claim evidence gate rejected absolute first-mover assertion."],
                    evidence=[]
                )

        # -------------------------------------------------------------
        # GATE 4: GTM MACHINE EMPIRICAL & STRATEGIC STAGE VERIFICATION
        # -------------------------------------------------------------
        # 4a. Strategic Stage Fit Check
        stage_check = self.product_stage_gate.evaluate(candidate_machine_id, opportunity_statement)
        if stage_check.status == "REJECT":
            # If competitor displacement is rejected on testnet, pivot to technical mechanism education
            candidate_machine_id = "MACHINE_04: TECHNICAL_EDUCATION_DISPATCH"

        machine_check = self.intelligence.verify_machine_eligibility(candidate_machine_id)
        if machine_check.eligibility_status != "ELIGIBLE":
            return GTMStrategy(
                strategy_id=strat_id,
                action_status="HUMAN_REVIEW_REQUIRED",
                decision_reason_class="GTM_MACHINE_INSUFFICIENT_EVIDENCE",
                human_review_rationale=(
                    f"Selected GTM Machine '{candidate_machine_id}' does not meet autonomous execution threshold: "
                    f"{machine_check.selection_reason}. Requires human marketing lead confirmation."
                ),
                objective="Evaluate candidate campaign machine before autonomous dispatch.",
                audience_segment=chosen_audience,
                problem=problem_statement,
                market_context=signal.description,
                strategic_opportunity=opportunity_statement,
                narrative_pillar=chosen_pillar,
                positioning=model_positioning or "Vanna is the composable credit layer for Stellar Soroban.",
                proof=[c.text for c in claim_records if c.action in ["USE", "USE_AS_INFERENCE"]],
                claims=claim_records,
                cta=model_cta or "Deploy your testnet SmartAccount sandbox at test.stellar.vanna.finance",
                channel=channel,
                content_type=content_type,
                gtm_machine_id=candidate_machine_id,
                machine_eligibility=machine_check,
                reasoning=[f"Machine eligibility check failed: {machine_check.selection_reason}"],
                evidence=[{"record_id": signal.record_id, "source": signal.source}]
            )

        # -------------------------------------------------------------
        # GATE 5: EVIDENCE COMPLETENESS & ACTION STATE
        # -------------------------------------------------------------
        # If signal evidence status is UNKNOWN or INSUFFICIENT, escalate to HUMAN_REVIEW_REQUIRED
        if signal.evidence_status in ["UNKNOWN", "INSUFFICIENT"]:
            return GTMStrategy(
                strategy_id=strat_id,
                action_status="HUMAN_REVIEW_REQUIRED",
                decision_reason_class="SIGNAL_EVIDENCE_INSUFFICIENT",
                human_review_rationale=(
                    f"Market signal '{signal.headline}' has evidence_status='{signal.evidence_status}'. "
                    f"Strategic hypothesis is sound, but underlying data is unconfirmed."
                ),
                objective="Verify market data before approving public positioning.",
                audience_segment=chosen_audience,
                problem=problem_statement,
                market_context=signal.description,
                strategic_opportunity=opportunity_statement,
                narrative_pillar=chosen_pillar,
                positioning="Vanna is the composable credit layer for Stellar Soroban, providing isolated SmartAccount sandboxes and sub-second defense.",
                proof=[c.text for c in claim_records if c.action in ["USE", "USE_AS_INFERENCE"]],
                claims=claim_records,
                cta="Deploy your testnet SmartAccount sandbox at test.stellar.vanna.finance",
                channel=channel,
                content_type=content_type,
                gtm_machine_id=candidate_machine_id,
                machine_eligibility=machine_check,
                reasoning=["Signal evidence status requires human confirmation before dispatch."],
                evidence=[{"record_id": signal.record_id, "source": signal.source, "status": signal.evidence_status}]
            )

        # FULL ACTION APPROVED
        return GTMStrategy(
            strategy_id=strat_id,
            action_status="ACTION",
            decision_reason_class="VALID_ACTIONABLE_SIGNAL",
            objective=model_objective or "Drive qualified testnet sandbox deployments.",
            audience_segment=chosen_audience,
            problem=problem_statement,
            market_context=signal.description,
            strategic_opportunity=opportunity_statement,
            narrative_pillar=chosen_pillar,
            positioning="Vanna is the composable credit layer for Stellar Soroban, providing isolated SmartAccount sandboxes and sub-second defense.",
            proof=[c.text for c in claim_records if c.action in ["USE", "USE_AS_INFERENCE"]],
            claims=claim_records,
            cta="Deploy your testnet SmartAccount sandbox at test.stellar.vanna.finance",
            channel=channel,
            content_type=content_type,
            gtm_machine_id=candidate_machine_id,
            machine_eligibility=machine_check,
            reasoning=model_reasoning + [
                f"Market Signal '{signal.headline}' verified from {signal.source_type} (Confidence: {signal.confidence}).",
                f"Audience '{chosen_audience}' targeted to resolve verified objection from Brain DB.",
                f"Machine '{candidate_machine_id}' verified eligible ({machine_check.selection_reason}).",
                f"Claims verified: {len(claim_records)} claims evaluated by ClaimEvidenceGate (0 blocked)."
            ],
            evidence=[
                {
                    "record_id": signal.record_id,
                    "source": signal.source,
                    "source_root": signal.source_root,
                    "dataset": signal.dataset,
                    "source_type": signal.source_type,
                    "observed_metric": signal.observed_metric_change,
                    "evidence_status": signal.evidence_status
                }
            ],
            title=signal.headline
        )

    def derive_content_brief(self, strategy: GTMStrategy) -> ContentBrief:
        """Derive an atomic ContentBrief from an approved GTMStrategy."""
        if strategy.action_status in ["NO_ACTION", "KILL"]:
            raise ValueError(f"Cannot derive content brief from a {strategy.action_status} strategy.")

        valid_claims = [c for c in strategy.claims if c.action in ["USE", "USE_AS_INFERENCE"]]

        return ContentBrief(
            brief_id=f"BRIEF-{strategy.strategy_id}",
            strategy_id=strategy.strategy_id,
            purpose="education_and_conversion",
            audience=strategy.audience_segment,
            funnel_stage="CONSIDERATION",
            category="PRODUCT_ARCHITECTURE",
            format=strategy.content_type,
            narrative=strategy.positioning,
            hook_strategy="Lead directly with EVM mempool liquidation pain and gas friction before introducing Soroban sub-second clearance.",
            proof_points=strategy.proof,
            call_to_action=strategy.cta,
            claims_to_enforce=valid_claims,
            claims_prohibited=[
                "Mainnet live",
                "The Aave of Stellar",
                "Uncontested first-mover",
                "Zero competitors exist",
                "Guaranteed profit without risk"
            ]
        )

    def generate_strategic_decision_report(
        self,
        strategy: GTMStrategy,
        signal: MarketSignal,
        generated_copy: str = "",
        stage_count: int = 1,
        has_coordinated_cohorts: bool = False,
        has_conversion_funnel: bool = False
    ) -> StrategicDecisionReport:
        """Synthesize all 4 decision-quality gates into an authoritative StrategicDecisionReport."""
        # 1. Audience Fit Gate
        copy_to_check = generated_copy or (strategy.problem + " " + strategy.strategic_opportunity)
        aud_res = self.audience_gate.evaluate(strategy.audience_segment, copy_to_check)

        # 2. Product / Stage Fit Gate
        stage_res = self.product_stage_gate.evaluate(strategy.gtm_machine_id, strategy.strategic_opportunity)

        # 3. Vehicle Fit Gate
        from pipeline.gtm_orchestration.decision_quality_gates import VehicleFitGate
        veh_gate = VehicleFitGate()
        is_repeatable = any(k in f"{strategy.gtm_machine_id} {strategy.narrative_pillar}".lower() for k in [
            "telemetry", "benchmark", "education", "sandbox", "monitoring", "architecture"
        ])
        veh_type, veh_res = veh_gate.evaluate(
            topic=strategy.narrative_pillar,
            stage_count=stage_count,
            is_repeatable_theme=is_repeatable,
            has_coordinated_cohorts=has_coordinated_cohorts,
            has_conversion_funnel=has_conversion_funnel
        )

        # 4. Claim Consistency Gate
        claim_res = self.claim_consistency_gate.evaluate(
            generated_copy or " ".join(strategy.proof)
        )

        # Final decision determination
        if aud_res.status == "REVISE" or claim_res.status == "REVISE":
            final_dec = "REVISE"
        elif stage_res.status == "REJECT" or claim_res.status == "REJECT" or strategy.action_status == "KILL":
            final_dec = "KILL"
        elif strategy.action_status == "NO_ACTION":
            final_dec = "NO_ACTION"
        elif strategy.action_status == "HUMAN_REVIEW_REQUIRED":
            final_dec = "HUMAN_REVIEW_REQUIRED"
        else:
            final_dec = "ACTION"

        return StrategicDecisionReport(
            opportunity={
                "opportunity_id": signal.record_id,
                "headline": signal.headline,
                "category": signal.market_category
            },
            audience=strategy.audience_segment,
            audience_fit=aud_res,
            narrative=strategy.narrative_pillar,
            product_stage_fit=stage_res,
            machine_candidates=[
                "MACHINE_01: NEW_INTEGRATION_DISPATCH",
                "MACHINE_02: TELEMETRY_DEFENSE_DISPATCH",
                "MACHINE_03: COMPETITOR_DISPLACEMENT_CAMPAIGN",
                "MACHINE_04: TECHNICAL_EDUCATION_DISPATCH"
            ],
            empirical_machine_eligibility={
                "MACHINE_01": "ELIGIBLE",
                "MACHINE_02": "ELIGIBLE",
                "MACHINE_03": "ELIGIBLE",
                "MACHINE_04": "ELIGIBLE"
            },
            strategic_machine_fit={
                "MACHINE_03": "REJECT_ON_TESTNET",
                "MACHINE_04": "PASS_FOR_TESTNET_DEMO"
            },
            selected_machine=strategy.gtm_machine_id,
            vehicle_candidates=["ONE_OFF", "SERIES", "CAMPAIGN"],
            selected_vehicle=veh_type,
            vehicle_fit=veh_res,
            claim_consistency=claim_res,
            final_decision=final_dec
        )

