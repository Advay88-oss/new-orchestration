#!/usr/bin/env python3
"""Decoupled Reward Engine (pipeline/gtm_rl/reward_engine.py).

Fulfills Mandates 9 & 10:
  - Eliminates fabricated/hardcoded scores (no more fake 95/96/98).
  - Separates reward channels:
      MODEL_REVIEW_SCORE
      AUTOMATED_QUALITY_SCORE
      NOVELTY_SCORE
      HUMAN_FEEDBACK_SCORE
      PERFORMANCE_SCORE
      FINAL_REWARD
  - Unobserved metrics strictly remain None (NULL). NULL != 0. NULL != failure.
  - Generates transparent, auditable reward provenance.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

REPO_ROOT = Path(__file__).resolve().parents[2]
STATE_DIR = REPO_ROOT / "pipeline" / "state"
MEMORY_DIR = REPO_ROOT / "pipeline" / "creative_memory"
MEMORY_DIR.mkdir(parents=True, exist_ok=True)
REWARD_LEDGER_FILE = MEMORY_DIR / "reward_ledger.jsonl"


@dataclass
class DecoupledReward:
    run_id: str
    asset_id: str
    content_type: str
    model_id: str
    timestamp: str

    # Distinct Reward Channels (Optional: NULL when unobserved)
    model_review_score: Optional[float] = None
    automated_quality_score: Optional[float] = None
    novelty_score: Optional[float] = None
    human_feedback_score: Optional[float] = None
    performance_score: Optional[float] = None
    final_reward: Optional[float] = None

    # Audit & Provenance
    weights_applied: Optional[Dict[str, float]] = None
    provenance_explanation: str = ""
    human_feedback_tags: Optional[List[str]] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class DecoupledRewardEngine:
    """Calculates verifiable rewards and records transparent provenance."""

    def __init__(self, ledger_path: Optional[Path] = None):
        self.ledger_path = ledger_path or REWARD_LEDGER_FILE

    def compute_reward(
        self,
        run_id: str,
        asset_id: str,
        content_type: str,
        model_id: str,
        model_review_score: Optional[float] = None,
        automated_quality_score: Optional[float] = None,
        novelty_score: Optional[float] = None,
        human_feedback_score: Optional[float] = None,
        performance_score: Optional[float] = None,
        human_feedback_tags: Optional[List[str]] = None
    ) -> DecoupledReward:
        """Computes the overall reward based ONLY on observed, non-null metrics."""
        available_components: Dict[str, float] = {}
        provenance_parts: List[str] = []

        if model_review_score is not None:
            available_components["model_review"] = float(model_review_score)
            provenance_parts.append(f"Model Review Score: {model_review_score:.1f}")

        if automated_quality_score is not None:
            available_components["automated_quality"] = float(automated_quality_score)
            provenance_parts.append(f"Automated Quality Score: {automated_quality_score:.1f}")

        if novelty_score is not None:
            available_components["novelty"] = float(novelty_score)
            provenance_parts.append(f"Structural Novelty Score: {novelty_score:.1f}")

        if human_feedback_score is not None:
            available_components["human_feedback"] = float(human_feedback_score)
            provenance_parts.append(f"Human Feedback: {human_feedback_score:.1f}")

        if performance_score is not None:
            available_components["performance"] = float(performance_score)
            provenance_parts.append(f"Empirical Performance: {performance_score:.1f}")

        # If zero metrics are observed, final_reward is strictly NULL (None)
        if not available_components:
            reward = DecoupledReward(
                run_id=run_id,
                asset_id=asset_id,
                content_type=content_type,
                model_id=model_id,
                timestamp=datetime.now(timezone.utc).isoformat(),
                model_review_score=None,
                automated_quality_score=None,
                novelty_score=None,
                human_feedback_score=None,
                performance_score=None,
                final_reward=None,
                weights_applied=None,
                provenance_explanation="No empirical evaluation signals observed yet. Reward remains NULL.",
                human_feedback_tags=human_feedback_tags or []
            )
            self._persist_reward(reward)
            return reward

        # Base weights calibrated dynamically across observed components only
        DEFAULT_WEIGHTS = {
            "human_feedback": 0.35,
            "performance": 0.25,
            "novelty": 0.20,
            "automated_quality": 0.10,
            "model_review": 0.10
        }

        # Normalize weights across available components
        total_raw_weight = sum(DEFAULT_WEIGHTS[k] for k in available_components)
        applied_weights = {k: round(DEFAULT_WEIGHTS[k] / total_raw_weight, 3) for k in available_components}

        # Calculate weighted final reward (0.0 - 100.0)
        final_val = sum(available_components[k] * applied_weights[k] for k in available_components)
        final_val = round(max(0.0, min(100.0, final_val)), 2)

        prov = f"Weighted aggregate of observed signals: {'; '.join(provenance_parts)}. Weights: {applied_weights}."
        if human_feedback_tags:
            prov += f" Human tags: [{', '.join(human_feedback_tags)}]."

        reward = DecoupledReward(
            run_id=run_id,
            asset_id=asset_id,
            content_type=content_type,
            model_id=model_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            model_review_score=model_review_score,
            automated_quality_score=automated_quality_score,
            novelty_score=novelty_score,
            human_feedback_score=human_feedback_score,
            performance_score=performance_score,
            final_reward=final_val,
            weights_applied=applied_weights,
            provenance_explanation=prov,
            human_feedback_tags=human_feedback_tags or []
        )
        self._persist_reward(reward)
        return reward

    def _persist_reward(self, reward: DecoupledReward) -> None:
        """Appends canonical reward event to ledger without duplicate writes."""
        self.ledger_path.parent.mkdir(parents=True, exist_ok=True)
        with self.ledger_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(reward.to_dict()) + "\n")
