"""Phase 8.2: Contextual Multi-Armed Bandit Router (bandit_router.py).

Implements:
  - UCB1 (Upper Confidence Bound) + epsilon-greedy exploration.
  - Human feedback reward modifier:
      APPROVE    = +0.25
      REVISE     = -0.15
      REGENERATE = -0.30
      KILL       = -0.60
  - State persistence:
      pipeline/state/rl_bandit_history.jsonl (Trials log)
      pipeline/state/rl_model_routing_policy.json (Policy arms & learned weights)
"""

from __future__ import annotations

import json
import math
import random
from pathlib import Path
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

REPO_ROOT = Path(__file__).resolve().parents[2]
STATE_DIR = REPO_ROOT / "pipeline" / "state"
STATE_DIR.mkdir(parents=True, exist_ok=True)

from pipeline.gtm_rl.schemas import (
    BanditTrial, ModelPolicyArm, TaskType, HumanDecision, CriticEvaluation
)


class BanditRouter:
    """Contextual multi-armed bandit routing tasks to optimal models based on empirical rewards."""

    HUMAN_MODIFIERS = {
        "APPROVE": 0.25,
        "REVISE": -0.15,
        "REGENERATE": -0.30,
        "KILL": -0.60,
        "PENDING": 0.0
    }

    def __init__(
        self,
        history_file: Optional[Path] = None,
        policy_file: Optional[Path] = None,
        epsilon: float = 0.20,
        ucb_c: float = 0.50
    ):
        self.history_file = history_file or (STATE_DIR / "rl_bandit_history.jsonl")
        self.policy_file = policy_file or (STATE_DIR / "rl_model_routing_policy.json")
        self.epsilon = epsilon
        self.ucb_c = ucb_c
        self.arms: Dict[str, ModelPolicyArm] = {}
        self._load_policy()

    def _make_arm_key(self, task_type: str, model_id: str) -> str:
        return f"{task_type}::{model_id}"

    def _load_policy(self) -> None:
        if self.policy_file.exists():
            try:
                data = json.loads(self.policy_file.read_text(encoding="utf-8"))
                for k, v in data.items():
                    self.arms[k] = ModelPolicyArm(**v)
            except Exception:
                pass

    def _save_policy(self) -> None:
        serialized = {k: v.model_dump() for k, v in self.arms.items()}
        self.policy_file.write_text(json.dumps(serialized, indent=2), encoding="utf-8")

    def get_or_create_arm(self, task_type: TaskType, model_id: str) -> ModelPolicyArm:
        key = self._make_arm_key(task_type, model_id)
        if key not in self.arms:
            self.arms[key] = ModelPolicyArm(
                task_type=task_type,
                model_id=model_id,
                trials_count=0,
                total_reward=0.0,
                average_reward=0.50,  # Neutral prior
                ucb_score=1.50,       # High initial optimism for exploration
                last_updated=datetime.now(timezone.utc).isoformat()
            )
        return self.arms[key]

    def select_model(
        self,
        task_type: TaskType,
        candidate_models: List[str]
    ) -> Tuple[str, bool, float]:
        """Selects a model using epsilon-greedy + UCB1.
        Returns: (selected_model_id, is_exploring, expected_reward)
        """
        if not candidate_models:
            raise ValueError("No candidate models provided to bandit.")

        # Epsilon-exploration: uniformly explore a candidate to discover new strengths
        if random.random() < self.epsilon:
            chosen = random.choice(candidate_models)
            arm = self.get_or_create_arm(task_type, chosen)
            return chosen, True, arm.average_reward

        # Exploitation: pick candidate with highest UCB score
        best_model = candidate_models[0]
        best_ucb = -1.0
        best_q = 0.50

        # Calculate total trials for this task_type
        total_task_trials = sum(
            arm.trials_count for key, arm in self.arms.items() if arm.task_type == task_type
        )

        for m in candidate_models:
            arm = self.get_or_create_arm(task_type, m)
            if arm.trials_count == 0:
                ucb = 2.0  # Unexplored arm bonus
            else:
                exploration_bonus = self.ucb_c * math.sqrt(math.log(max(1, total_task_trials + 1)) / arm.trials_count)
                ucb = arm.average_reward + exploration_bonus

            arm.ucb_score = round(ucb, 4)
            if ucb > best_ucb:
                best_ucb = ucb
                best_model = m
                best_q = arm.average_reward

        self._save_policy()
        return best_model, False, best_q

    def record_trial(
        self,
        brief_id: str,
        brief_title: str,
        task_type: TaskType,
        model_id: str,
        provider: str,
        prompt: str,
        output: str,
        latency: float,
        cost: float,
        critic_eval: CriticEvaluation,
        human_decision: HumanDecision = "PENDING"
    ) -> BanditTrial:
        """Records trial in history and updates policy arm statistics."""
        modifier = self.HUMAN_MODIFIERS.get(human_decision, 0.0)
        final_reward = round(max(0.0, min(1.0, critic_eval.base_reward + modifier)), 3)

        trial_id = f"TRIAL-{task_type[:3].upper()}-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')[:18]}"

        trial = BanditTrial(
            trial_id=trial_id,
            brief_id=brief_id,
            brief_title=brief_title,
            task_type=task_type,
            model_id=model_id,
            provider=provider,
            prompt_used=prompt,
            output_content=output,
            latency_seconds=round(latency, 3),
            cost_usd=round(cost, 6),
            critic_eval=critic_eval,
            human_decision=human_decision,
            human_reward_modifier=modifier,
            final_reward=final_reward,
            timestamp=datetime.now(timezone.utc).isoformat()
        )

        # Append to JSONL history
        with open(self.history_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(trial.model_dump()) + "\n")

        # Update policy arm
        arm = self.get_or_create_arm(task_type, model_id)
        arm.trials_count += 1
        arm.total_reward += final_reward
        arm.average_reward = round(arm.total_reward / arm.trials_count, 3)
        arm.last_updated = datetime.now(timezone.utc).isoformat()

        self._save_policy()
        return trial

    def apply_human_feedback(
        self,
        trial_id: str,
        decision: HumanDecision
    ) -> Optional[BanditTrial]:
        """Applies human feedback to an existing trial and updates the arm policy."""
        if not self.history_file.exists():
            return None

        lines = self.history_file.read_text(encoding="utf-8").splitlines()
        updated_trials = []
        target_trial = None

        for line in lines:
            if not line.strip():
                continue
            d = json.loads(line)
            if d.get("trial_id") == trial_id:
                old_modifier = d.get("human_reward_modifier", 0.0)
                new_modifier = self.HUMAN_MODIFIERS.get(decision, 0.0)
                base_r = d["critic_eval"]["base_reward"]
                new_final = round(max(0.0, min(1.0, base_r + new_modifier)), 3)

                d["human_decision"] = decision
                d["human_reward_modifier"] = new_modifier
                d["final_reward"] = new_final
                target_trial = BanditTrial(**d)
                updated_trials.append(json.dumps(d))

                # Update arm statistics with delta
                delta = new_final - (base_r + old_modifier)
                key = self._make_arm_key(target_trial.task_type, target_trial.model_id)
                if key in self.arms:
                    arm = self.arms[key]
                    arm.total_reward += delta
                    arm.average_reward = round(arm.total_reward / max(1, arm.trials_count), 3)
                    arm.last_updated = datetime.now(timezone.utc).isoformat()
            else:
                updated_trials.append(line)

        if target_trial:
            self.history_file.write_text("\n".join(updated_trials) + "\n", encoding="utf-8")
            self._save_policy()

        return target_trial

    def get_routing_policy_summary(self) -> Dict[str, Any]:
        """Returns the learned policy preferences across task types."""
        summary = {}
        for key, arm in self.arms.items():
            if arm.task_type not in summary:
                summary[arm.task_type] = []
            summary[arm.task_type].append({
                "model_id": arm.model_id,
                "trials": arm.trials_count,
                "average_reward_Q": arm.average_reward,
                "ucb_score": arm.ucb_score
            })

        for tt in summary:
            summary[tt].sort(key=lambda x: x["average_reward_Q"], reverse=True)

        return summary
