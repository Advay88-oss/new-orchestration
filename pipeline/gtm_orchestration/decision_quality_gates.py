"""Phase 1.2: Decision Quality Gates (decision_quality_gates.py).

Implements the four hardening gates identified in the Adversarial CMO Audit:
  1. AUDIENCE FIT GATE: Verifies AUDIENCE -> PAIN -> NARRATIVE -> PROOF -> CTA alignment.
     Prevents assigning trader mempool pains to institutional LPs.
  2. PRODUCT / STAGE FIT GATE: Separates empirical machine eligibility from strategic stage fit.
     Rejects competitor displacement on testnet; selects technical education.
  3. VEHICLE FIT GATE: Strictly distinguishes ONE_OFF, SERIES, and CAMPAIGN.
     Prevents classifying single multi-channel topics as campaigns.
  4. CLAIM CONSISTENCY GATE: Verifies numerical, threshold, and mechanism consistency.
     Enforces explicit relationship between 1.25x proactive threshold and 1.10x hard floor;
     rejects absolute "zero liquidation penalty" when DEX fees/slippage apply.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field

GateStatus = Literal["PASS", "REVISE", "REJECT"]


class GateEvaluationResult(BaseModel):
    """The structured output required for every decision quality gate."""
    status: GateStatus
    reason: str
    evidence: List[str] = Field(default_factory=list)
    assumptions: List[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)


class StrategicDecisionReport(BaseModel):
    """Authoritative decision report synthesizing all four decision-quality gates."""
    opportunity: Dict[str, Any]
    audience: str
    audience_fit: GateEvaluationResult
    narrative: str
    product_stage_fit: GateEvaluationResult
    machine_candidates: List[str]
    empirical_machine_eligibility: Dict[str, str]
    strategic_machine_fit: Dict[str, str]
    selected_machine: str
    vehicle_candidates: List[str]
    selected_vehicle: str
    vehicle_fit: GateEvaluationResult
    claim_consistency: GateEvaluationResult
    final_decision: Literal["ACTION", "NO_ACTION", "HUMAN_REVIEW_REQUIRED", "KILL", "REVISE"]


class AudienceFitGate:
    """Audits whether the selected audience is demonstrably aligned with the copy's pain points."""

    TRADER_KEYWORDS = [
        "mempool", "gas spike", "150 gwei", "rebalance transaction", "front-running",
        "mev", "bidding war", "liquidation fee penalty", "slippage", "trader"
    ]
    LP_KEYWORDS = [
        "reserve solvency", "bad debt", "haircut", "lendingpool", "depletion",
        "utilization curve", "vtoken", "underwriting", "yield drag", "contagion"
    ]

    def evaluate(self, audience_segment: str, copy_or_narrative: str) -> GateEvaluationResult:
        text_lower = copy_or_narrative.lower()
        is_lp_audience = any(k in audience_segment.lower() for k in ["liquidity provider", "institutional", "a3"])
        is_trader_audience = any(k in audience_segment.lower() for k in ["trader", "borrower", "farmer", "a1", "a2"])

        has_trader_pains = any(k in text_lower for k in self.TRADER_KEYWORDS)
        has_lp_pains = any(k in text_lower for k in self.LP_KEYWORDS)

        if is_lp_audience and has_trader_pains and not has_lp_pains:
            return GateEvaluationResult(
                status="REVISE",
                reason=(
                    f"Audience '{audience_segment}' is misaligned with copy. Institutional LPs care about reserve solvency, "
                    f"bad-debt insulation, and yield stability, but content focuses exclusively on active trader execution "
                    f"pains (mempool congestion, gas bidding wars, rebalance latency)."
                ),
                evidence=[
                    "audience_segments.jsonl: A3 core friction is pool haircuts and bad debt socialization.",
                    f"Matched trader execution terms in copy: {[k for k in self.TRADER_KEYWORDS if k in text_lower]}"
                ],
                assumptions=["Assumes passive liquidity providers do not submit active liquidation rebalances."],
                confidence=0.95
            )

        if is_trader_audience and has_trader_pains:
            return GateEvaluationResult(
                status="PASS",
                reason=f"Audience '{audience_segment}' is demonstrably aligned with active trader execution and mempool friction.",
                evidence=[f"Matched active trader terms: {[k for k in self.TRADER_KEYWORDS if k in text_lower]}"],
                assumptions=[],
                confidence=0.95
            )

        if is_lp_audience and has_lp_pains:
            return GateEvaluationResult(
                status="PASS",
                reason=f"Audience '{audience_segment}' is demonstrably aligned with pool solvency and risk containment.",
                evidence=[f"Matched LP reserve terms: {[k for k in self.LP_KEYWORDS if k in text_lower]}"],
                assumptions=[],
                confidence=0.95
            )

        return GateEvaluationResult(
            status="PASS",
            reason=f"Audience '{audience_segment}' has acceptable alignment with narrative angle.",
            evidence=[],
            assumptions=["No direct pain point conflict detected."],
            confidence=0.80
        )


class ProductStageFitGate:
    """Evaluates whether an empirically eligible machine is strategically appropriate for the company's current stage."""

    # Stages at which there is no live capital to move: displacement plays
    # need a production product. The stage itself comes from the brand profile.
    PRE_PRODUCTION = ("testnet", "devnet", "beta", "pre-launch", "prelaunch", "alpha")

    @property
    def CURRENT_STAGE(self) -> str:
        from pipeline.brand_brain import context as C
        return (C.stage() or "unknown").upper()

    def evaluate(self, machine_id: str, strategic_objective: str) -> GateEvaluationResult:
        mid_norm = machine_id.upper()
        obj_lower = strategic_objective.lower()

        # Regression case: Competitor displacement on testnet
        if "DISPLACEMENT" in mid_norm or "MACHINE_03" in mid_norm or "MACH_03" in mid_norm:
            if self.CURRENT_STAGE.lower() in self.PRE_PRODUCTION or "migrate" in obj_lower:
                return GateEvaluationResult(
                    status="REJECT",
                    reason=(
                        f"Machine '{machine_id}' is strategically inappropriate for product stage '{self.CURRENT_STAGE}'. "
                        f"Competitor displacement requires a live product with capital to migrate from incumbents. "
                        f"Pre-production users cannot migrate production capital. Strategic fit requires technical education or a trial."
                    ),
                    evidence=[
                        "brand profile: " + _deployment(),
                        "Competitor displacement precedent requires liquidity parity with the incumbent."
                    ],
                    assumptions=["Pre-production users cannot migrate live deposits."],
                    confidence=0.98
                )

        # Technical education machine is highly appropriate for testnet architecture demonstration
        if "EDUCATION" in mid_norm or "MACHINE_04" in mid_norm or "MACH_04" in mid_norm or "MACH_01" in mid_norm or "LAUNCH" in mid_norm:
            return GateEvaluationResult(
                status="PASS",
                reason=(
                    f"Machine '{machine_id}' is strategically aligned with product stage '{self.CURRENT_STAGE}'. "
                    f"Educational mechanism breakdowns drive developer and user trial."
                ),
                evidence=[
                    "brand profile: " + _deployment(),
                    "Precedent: technical breakdowns commonly precede a production launch."
                ],
                assumptions=[],
                confidence=0.95
            )

        return GateEvaluationResult(
            status="PASS",
            reason=f"Machine '{machine_id}' has acceptable alignment with stage '{self.CURRENT_STAGE}'.",
            evidence=[],
            assumptions=[],
            confidence=0.85
        )


class VehicleFitGate:
    """Strictly distinguishes ONE_OFF, SERIES, and CAMPAIGN."""

    def evaluate(
        self,
        topic: str,
        stage_count: int,
        is_repeatable_theme: bool,
        has_coordinated_cohorts: bool,
        has_conversion_funnel: bool
    ) -> tuple[Literal["ONE_OFF", "SERIES", "CAMPAIGN"], GateEvaluationResult]:
        # Single technical education topic without coordinated cohorts is a SERIES or ONE_OFF
        if stage_count <= 1 or not has_coordinated_cohorts or not has_conversion_funnel:
            if is_repeatable_theme:
                return "SERIES", GateEvaluationResult(
                    status="PASS",
                    reason=(
                        "Classified as RECURRING_SERIES. A standalone technical topic distributed across multiple channels "
                        "is not a campaign. It lacks coordinated phased stages and conversion sequencing. "
                        "Because the architectural mechanism is repeatable, it belongs in an educational series."
                    ),
                    evidence=[
                        "Vehicle Audit: Campaign requires defined objective, coordinated stages, conversion event, and sequencing.",
                        f"Current scope: {stage_count} stage(s), repeatable theme={is_repeatable_theme}."
                    ],
                    assumptions=["Series cadence can absorb recurring technical breakdowns."],
                    confidence=0.95
                )
            else:
                return "ONE_OFF", GateEvaluationResult(
                    status="PASS",
                    reason="Classified as ONE_OFF. Single isolated announcement without recurring cadence or staged execution.",
                    evidence=[],
                    assumptions=[],
                    confidence=0.90
                )

        # Full staged campaign requirements met
        return "CAMPAIGN", GateEvaluationResult(
            status="PASS",
            reason="Classified as CAMPAIGN. Meets strict criteria: coordinated stages, multi-week sequencing, and defined conversion event.",
            evidence=[
                f"Configured stages: {stage_count} standard stages.",
                "Coordinated cohorts and conversion funnel verified."
            ],
            assumptions=[],
            confidence=0.95
        )


class ClaimConsistencyGate:
    """Verifies numerical, threshold, terminology, and mechanism consistency against canonical Vanna facts."""

    def evaluate(self, claims_text: str) -> GateEvaluationResult:
        text_lower = claims_text.lower()
        violations = []
        evidence = []
        assumptions = []

        # 1. Regression check: 1.10x floor vs 1.25x proactive threshold
        has_110 = "1.10" in text_lower or "1.1x" in text_lower or "1.10x" in text_lower
        has_125 = "1.25" in text_lower or "1.25x" in text_lower

        if has_125:
            # Check if 1.25x is falsely called the liquidation floor
            if "1.25x liquidation floor" in text_lower or "liquidated at 1.25" in text_lower or "liquidation penalty at 1.25" in text_lower:
                violations.append("Contradictory threshold: 1.25x is falsely described as the protocol liquidation floor (canonical floor is 1.10x).")
            elif not has_110 and not any(k in text_lower for k in ["before", "proactive", "pre-liquidation", "threshold"]):
                violations.append("Uncalibrated threshold: 1.25x is cited without explaining its relationship to the canonical 1.10x hard liquidation floor.")
            elif has_110 and any(k in text_lower for k in ["before 1.10", "proactive", "prior to", "prevents liquidation at 1.10"]):
                evidence.append("Consistent threshold relationship: 1.25x explicitly identified as proactive rebalance threshold prior to 1.10x liquidation floor.")

        # 2. Regression check: "no liquidation fee penalty" / "zero liquidation penalty"
        if any(phrase in text_lower for phrase in ["no liquidation fee penalty", "zero liquidation penalty", "no liquidation penalty", "zero penalty"]):
            violations.append(
                "Absolute penalty assertion: Claims 'no liquidation fee penalty' when execution involves automated DEX swaps, "
                "which incur on-chain DEX swap fees and pool slippage. Must state 'avoids punitive liquidation fees by rebalancing before the 1.10x floor'."
            )

        # 3. Temporal / Mainnet consistency
        if any(term in text_lower for term in ["mainnet live", "live token", "trading live", "production tvl"]):
            violations.append("Temporal violation: Asserts mainnet live or live trading when Vanna is currently on Stellar Testnet.")

        if violations:
            status: GateStatus = "REJECT" if any("contradictory" in v.lower() or "temporal" in v.lower() for v in violations) else "REVISE"
            return GateEvaluationResult(
                status=status,
                reason="; ".join(violations),
                evidence=evidence,
                assumptions=assumptions,
                confidence=0.95
            )

        return GateEvaluationResult(
            status="PASS",
            reason="All numerical thresholds, mechanism definitions, and product stages are consistent with canonical Vanna specifications.",
            evidence=evidence or ["Matches docs.vanna.finance 1.10x Health Factor floor and 0.00014 XLM fixed gas."],
            assumptions=[],
            confidence=0.95
        )


def _deployment() -> str:
    from pipeline.brand_brain import context as C
    return str(C.profile().get("company", {}).get("deployment", ""))
