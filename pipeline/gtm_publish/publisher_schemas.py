"""Phase 7: Publisher Schemas for Autonomous Dispatch.

Defines the data contracts for transitioning from WAITING_FOR_HUMAN -> APPROVED -> PUBLISHED.
Supports live API connections and deterministic sandbox/staging modes.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field

ChannelType = Literal["X", "LinkedIn", "Reddit"]
PublishStatus = Literal["PENDING", "SUCCESS", "FAILED", "SKIPPED"]
ExecutionMode = Literal["LIVE", "SIMULATED_TESTNET", "DRY_RUN"]


class ChannelContentPayload(BaseModel):
    """Payload to be dispatched to a single social channel."""
    channel: ChannelType
    title: Optional[str] = None
    copy: str
    media_paths: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    target_community: Optional[str] = None  # e.g., 'r/defi' or 'r/Stellar' for Reddit


class PublishRequest(BaseModel):
    """Comprehensive request to publish an approved package."""
    request_id: str
    packet_id: str
    run_id: str
    campaign_id: Optional[str] = None
    pattern_id: Optional[str] = "PAT_01_TECHNICAL_TELEMETRY"
    approved_by: str = "FOUNDER_APPROVAL"
    approved_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    channels: List[ChannelContentPayload]
    mode: ExecutionMode = "SIMULATED_TESTNET"


class ChannelPublishReceipt(BaseModel):
    """Immutable receipt for an individual channel dispatch."""
    receipt_id: str
    request_id: str
    channel: ChannelType
    status: PublishStatus
    post_id: Optional[str] = None
    canonical_url: Optional[str] = None
    published_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    latency_ms: float = 0.0
    error_message: Optional[str] = None
    raw_response: Dict[str, Any] = Field(default_factory=dict)


class BatchPublishResult(BaseModel):
    """Aggregated batch result across all channels."""
    batch_id: str
    request_id: str
    overall_status: Literal["ALL_PUBLISHED", "PARTIALLY_PUBLISHED", "FAILED"]
    receipts: List[ChannelPublishReceipt]
    total_channels: int
    successful_channels: int
    completed_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    lifecycle_state: str = "PUBLISHED"
