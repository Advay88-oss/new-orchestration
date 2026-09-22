"""Phase 8.1: Measurable Critic & Reward Engine (critic.py).

Evaluates model outputs across 10 measurable dimensions:
  1. Strategic alignment
  2. Content quality
  3. Hook strength
  4. Audience fit
  5. Claim safety
  6. Visual quality
  7. Originality
  8. Brand fit
  9. Platform suitability
  10. Overall quality

Computes a normalized reward R in [0.0, 1.0] and captures failure reasons.
Do NOT invent scores just to declare a winner.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional
from pipeline.gtm_rl.schemas import CriticEvaluation, TaskType


class ContentCritic:
    """Rigorous, objective critic evaluating candidate outputs against measurable criteria."""

    PROHIBITED_TERMS = [
        "aave of stellar", "mainnet live", "live token", "guaranteed profit",
        "zero risk", "uncontested first-mover", "uncontested monopoly"
    ]
    AI_CLICHES = [
        "testament", "pivotal moment", "crucial role", "evolving landscape",
        "beacon", "tapestry", "delve", "game-changer", "groundbreaking"
    ]

    def evaluate_text_output(
        self,
        output_text: str,
        brief: Dict[str, Any],
        task_type: TaskType
    ) -> CriticEvaluation:
        """Evaluate a text output across the 10 measurable dimensions."""
        text_lower = output_text.lower()
        failures = []

        # 1. Claim Safety (Hard gate)
        found_prohibited = [p for p in self.PROHIBITED_TERMS if p in text_lower]
        has_testnet_disclosure = "testnet" in text_lower or "test." in text_lower
        if found_prohibited:
            claim_safety = 0.20
            failures.append(f"Contains prohibited claim: {found_prohibited}")
        elif not has_testnet_disclosure:
            claim_safety = 0.60
            failures.append("Missing explicit testnet disclosure.")
        else:
            claim_safety = 1.00

        # Check threshold consistency: 1.10x floor vs 1.25x proactive
        if "1.25" in text_lower and "liquidation floor" in text_lower:
            claim_safety = min(claim_safety, 0.40)
            failures.append("Falsely claimed 1.25x as the liquidation floor (canonical is 1.10x).")

        # 2. Hook Strength
        first_line = output_text.strip().split("\n")[0]
        has_question_opener = first_line.endswith("?")
        has_pain_point = any(w in first_line.lower() for w in ["mempool", "gas", "cascade", "haircut", "broken", "lock", "fail", "penalty", "borrow"])
        if len(first_line) > 140:
            hook_strength = 0.65
            failures.append("Hook is too long (> 140 chars for first line).")
        elif has_pain_point:
            hook_strength = 0.95
        elif has_question_opener:
            hook_strength = 0.75
        else:
            hook_strength = 0.80

        # 3. Audience Fit
        target_audience = brief.get("audience", "").lower()
        is_trader = "trader" in target_audience or "a2" in target_audience or "farmer" in target_audience
        is_lp = "liquidity provider" in target_audience or "a3" in target_audience
        has_trader_terms = any(t in text_lower for t in ["gas", "mempool", "rebalance", "150 gwei", "slippage", "bots"])
        has_lp_terms = any(t in text_lower for t in ["haircut", "bad debt", "solvency", "lendingpool", "reserves", "contagion"])

        if is_trader and has_trader_terms:
            audience_fit = 0.96
        elif is_lp and has_lp_terms and not has_trader_terms:
            audience_fit = 0.96
        elif is_lp and has_trader_terms and not has_lp_terms:
            audience_fit = 0.60
            failures.append("Assigned trader mempool execution pains to passive institutional LP audience.")
        else:
            audience_fit = 0.85

        # 4. Strategic Alignment
        required_proof = brief.get("proof", [])
        proof_matches = sum(1 for p in required_proof if any(term in text_lower for term in p.lower().split()[:3]))
        proof_ratio = proof_matches / max(1, len(required_proof))
        strategic_alignment = round(0.70 + (0.30 * proof_ratio), 2)

        # 5. Content Quality & Density
        word_count = len(output_text.split())
        has_specific_numbers = bool(re.search(r"\d+(\.\d+)?(x|%|xlm|ms|usdc)?", text_lower))
        if word_count < 15:
            content_quality = 0.50
            failures.append("Output is truncated or too brief (< 15 words).")
        elif word_count > 120 and task_type == "x_post":
            content_quality = 0.75
            failures.append("X post is too wordy (> 120 words).")
        elif has_specific_numbers:
            content_quality = 0.94
        else:
            content_quality = 0.82

        # 6. Originality & Anti-Cliché
        found_cliches = [c for c in self.AI_CLICHES if c in text_lower]
        if found_cliches:
            originality = max(0.50, 0.90 - (len(found_cliches) * 0.15))
            failures.append(f"Contains AI buzzword clichés: {found_cliches}")
        else:
            originality = 0.95

        # 7. Brand Fit & Voice
        has_vanna_mention = "vanna" in text_lower
        has_soroban_mention = "soroban" in text_lower or "stellar" in text_lower
        if has_vanna_mention and has_soroban_mention:
            brand_fit = 0.98
        elif has_vanna_mention:
            brand_fit = 0.88
        else:
            brand_fit = 0.60
            failures.append("Does not identify Vanna Protocol.")

        # 8. Platform Suitability
        char_count = len(output_text)
        if task_type == "x_post":
            platform_suitability = 0.95 if char_count <= 280 else (0.85 if char_count <= 500 else 0.65)
            if char_count > 500:
                failures.append("Exceeds standard X post length.")
        elif task_type == "linkedin_post":
            platform_suitability = 0.95 if char_count >= 250 else 0.75
        else:
            platform_suitability = 0.90

        # 9. Visual Quality (N/A for pure text -> default 0.90)
        visual_quality = 0.90

        # 10. Overall Quality & Base Reward Calculation
        # Weighted composite:
        # 0.20 Strategic + 0.15 Content + 0.15 Hook + 0.15 Audience + 0.15 Safety + 0.10 Brand + 0.10 Originality
        base_reward = round(
            (strategic_alignment * 0.20) +
            (content_quality * 0.15) +
            (hook_strength * 0.15) +
            (audience_fit * 0.15) +
            (claim_safety * 0.15) +
            (brand_fit * 0.10) +
            (originality * 0.10),
            3
        )
        overall_quality = base_reward

        return CriticEvaluation(
            strategic_alignment=strategic_alignment,
            content_quality=content_quality,
            hook_strength=hook_strength,
            audience_fit=audience_fit,
            claim_safety=claim_safety,
            visual_quality=visual_quality,
            originality=originality,
            brand_fit=brand_fit,
            platform_suitability=platform_suitability,
            overall_quality=overall_quality,
            failure_reasons=failures,
            base_reward=base_reward
        )
