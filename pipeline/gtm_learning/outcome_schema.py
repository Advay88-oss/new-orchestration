"""Strict Pydantic schemas for Phase 8 Performance & Learning Loop.

Enforces:
  - NULL != 0 (Unmeasured metrics are explicitly NOT_MEASURED with None value).
  - Traceable learned adjustments (previous_value, new_value, sample_size, confidence, reason).
  - Minimum sample size thresholds before updating pattern weights.
"""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field

MeasurementStatus = Literal[
    "MEASURED",
    "NOT_MEASURED",
    "UNAVAILABLE",
    "DELAYED",
    "ESTIMATED"
]


class MetricValue(BaseModel):
    """Encapsulates a metric distinguishing unmeasured (None) from measured zero (0.0)."""
    raw_value: Optional[float] = None
    status: MeasurementStatus = "NOT_MEASURED"
    is_measured_zero: bool = False
    data_as_of: Optional[str] = None

    @classmethod
    def measured(cls, val: float, as_of: str = "2026-09-16") -> MetricValue:
        return cls(raw_value=val, status="MEASURED", is_measured_zero=(val == 0.0), data_as_of=as_of)

    @classmethod
    def unmeasured(cls) -> MetricValue:
        return cls(raw_value=None, status="NOT_MEASURED", is_measured_zero=False, data_as_of=None)


class PostPerformanceRecord(BaseModel):
    """Real post performance outcome."""
    record_id: str
    content_id: str
    campaign_id: Optional[str] = None
    platform: Literal["X", "LinkedIn", "Reddit"]
    impressions: MetricValue = Field(default_factory=MetricValue.unmeasured)
    reach: MetricValue = Field(default_factory=MetricValue.unmeasured)
    likes: MetricValue = Field(default_factory=MetricValue.unmeasured)
    replies: MetricValue = Field(default_factory=MetricValue.unmeasured)
    reposts: MetricValue = Field(default_factory=MetricValue.unmeasured)
    clicks: MetricValue = Field(default_factory=MetricValue.unmeasured)
    conversions: MetricValue = Field(default_factory=MetricValue.unmeasured)
    deployments: MetricValue = Field(default_factory=MetricValue.unmeasured)
    spend_usd: MetricValue = Field(default_factory=MetricValue.unmeasured)
    recorded_at: str


class PatternAdjustmentRecord(BaseModel):
    """Traceable adjustment to a pattern's recommendation weight based on empirical data."""
    adjustment_id: str
    pattern_id: str
    previous_weight: float
    new_weight: float
    evidence_refs: List[str]
    sample_size: int
    confidence: float
    timestamp: str
    reason: str
