"""Pydantic schemas for the Vanna GTM Reinforcement Learning & Bandit Routing Loop.

Enforces:
  - Multi-dimensional measurable critic evaluation (10 dimensions).
  - Explicit tracking of latency, cost, and tokens.
  - Human feedback reward signals (APPROVE: +0.25, REVISE: -0.15, REGENERATE: -0.30, KILL: -0.60).
  - Contextual UCB policy tracking per (task_type, model_id).
"""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field

TaskType = Literal[
    "x_post",
    "linkedin_post",
    "reddit_post",
    "product_visual",
    "technical_schematic",
    "editorial_visual"
]

HumanDecision = Literal[
    "APPROVE",
    "REVISE",
    "REGENERATE",
    "KILL",
    "PENDING"
]


class CriticEvaluation(BaseModel):
    """Measurable evaluation across 10 distinct quality dimensions."""
    strategic_alignment: float = Field(ge=0.0, le=1.0)
    content_quality: float = Field(ge=0.0, le=1.0)
    hook_strength: float = Field(ge=0.0, le=1.0)
    audience_fit: float = Field(ge=0.0, le=1.0)
    claim_safety: float = Field(ge=0.0, le=1.0)
    visual_quality: float = Field(ge=0.0, le=1.0)
    originality: float = Field(ge=0.0, le=1.0)
    brand_fit: float = Field(ge=0.0, le=1.0)
    platform_suitability: float = Field(ge=0.0, le=1.0)
    overall_quality: float = Field(ge=0.0, le=1.0)
    failure_reasons: List[str] = Field(default_factory=list)
    base_reward: float = Field(ge=0.0, le=1.0)


class BanditTrial(BaseModel):
    """Complete record of an individual model generation trial in the Arena."""
    trial_id: str
    brief_id: str
    brief_title: str
    task_type: TaskType
    model_id: str
    provider: str
    prompt_used: str
    output_content: str
    latency_seconds: float
    cost_usd: float
    critic_eval: CriticEvaluation
    human_decision: HumanDecision = "PENDING"
    human_reward_modifier: float = 0.0
    final_reward: float
    timestamp: str


class ModelPolicyArm(BaseModel):
    """Policy statistics for a single (task_type, model_id) arm."""
    task_type: TaskType
    model_id: str
    trials_count: int = 0
    total_reward: float = 0.0
    average_reward: float = 0.0  # Q-value
    ucb_score: float = 0.0
    last_updated: str
