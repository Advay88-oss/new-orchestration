"""Phase 7: Central Approved Dispatch Worker (approved_dispatch_worker.py).

Executes the transition from WAITING_FOR_HUMAN -> APPROVED -> PUBLISHED.
Dispatches multi-channel content to X, LinkedIn, and Reddit.
Persists immutable records into canonical DB and initializes closed-loop performance tracking.
"""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from pipeline.gtm_publish.publisher_schemas import (
    BatchPublishResult,
    ChannelPublishReceipt,
    PublishRequest,
)
from pipeline.gtm_publish.channel_dispatchers import (
    LinkedInDispatcher,
    RedditDispatcher,
    XDispatcher,
)
from pipeline.gtm_learning.outcome_schema import MetricValue, PostPerformanceRecord
from pipeline.gtm_learning.performance_store import PerformanceStore
from pipeline.gtm_storage.atomic_store import AtomicJsonlStore
from pipeline.gtm_orchestration.config import BRAIN_DB_DIR, BRAIN_ROOT, CANONICAL_KNOWLEDGE_ROOT

REPO_ROOT = Path("D:/new orchestration")
DB_POSTS_FILE = BRAIN_DB_DIR / "posts.jsonl"
STATE_DIR = REPO_ROOT / "pipeline" / "state"
STATE_POSTS_FILE = STATE_DIR / "posts_published.jsonl"


class ApprovedDispatchWorker:
    """Dispatches approved marketing content across verified channels."""

    def __init__(self, performance_store: Optional[PerformanceStore] = None):
        self.dispatchers = {
            "X": XDispatcher(),
            "LinkedIn": LinkedInDispatcher(),
            "Reddit": RedditDispatcher(),
        }
        self.performance_store = performance_store or PerformanceStore()
        self.db_posts_store = AtomicJsonlStore(DB_POSTS_FILE)
        self.state_posts_store = AtomicJsonlStore(STATE_POSTS_FILE)

    def execute_publish(self, request: PublishRequest) -> BatchPublishResult:
        """Executes multi-channel dispatch for an approved packet."""
        batch_id = f"BATCH-{int(time.time())}"
        receipts: List[ChannelPublishReceipt] = []

        print(f"\n🚀 DISPATCH WORKER: Initiating publish batch {batch_id} for request {request.request_id}...")
        print(f"   Mode: {request.mode} | Approved by: {request.approved_by}")

        for channel_payload in request.channels:
            dispatcher = self.dispatchers.get(channel_payload.channel)
            if not dispatcher:
                print(f"⚠️ DISPATCH WORKER: Unsupported channel '{channel_payload.channel}', skipping.")
                continue

            print(f"   ▶ Dispatching to {channel_payload.channel}...")
            receipt = dispatcher.dispatch(request.request_id, channel_payload, mode=request.mode)
            receipts.append(receipt)

            if receipt.status == "SUCCESS":
                print(f"   ✅ {channel_payload.channel} published: {receipt.canonical_url} ({receipt.latency_ms}ms)")
                # Persist to canonical DB posts.jsonl
                self._record_published_post(request, receipt, channel_payload)
                # Seed performance store with unmeasured metrics (NULL != 0)
                self._seed_performance_record(request, receipt)
            else:
                print(f"   ❌ {channel_payload.channel} dispatch failed: {receipt.error_message}")

        success_count = sum(1 for r in receipts if r.status == "SUCCESS")
        overall = "ALL_PUBLISHED" if success_count == len(receipts) else ("PARTIALLY_PUBLISHED" if success_count > 0 else "FAILED")

        batch_result = BatchPublishResult(
            batch_id=batch_id,
            request_id=request.request_id,
            overall_status=overall,
            receipts=receipts,
            total_channels=len(request.channels),
            successful_channels=success_count,
            lifecycle_state="PUBLISHED" if overall in ("ALL_PUBLISHED", "PARTIALLY_PUBLISHED") else "FAILED"
        )

        return batch_result

    def _record_published_post(
        self,
        request: PublishRequest,
        receipt: ChannelPublishReceipt,
        payload: Any
    ) -> None:
        """Appends the post to both state and canonical DB posts.jsonl."""
        post_record = {
            "post_id": receipt.post_id,
            "channel": receipt.channel,
            "run_id": request.run_id,
            "campaign_id": request.campaign_id,
            "pattern_id": request.pattern_id,
            "canonical_url": receipt.canonical_url,
            "copy": payload.copy,
            "media_paths": payload.media_paths,
            "published_at": receipt.published_at,
            "status": "PUBLISHED",
            "mode": request.mode
        }

        # Canonical DB
        self.db_posts_store.append(post_record)

        # Local state DB
        self.state_posts_store.append(post_record)

    def _seed_performance_record(
        self,
        request: PublishRequest,
        receipt: ChannelPublishReceipt
    ) -> None:
        """Seeds performance tracking record with unmeasured status (NULL != 0)."""
        perf_rec = PostPerformanceRecord(
            record_id=f"PERF-{receipt.post_id}",
            content_id=receipt.post_id or f"CONTENT-{receipt.receipt_id}",
            campaign_id=request.pattern_id,
            platform=receipt.channel,
            impressions=MetricValue.unmeasured(),
            reach=MetricValue.unmeasured(),
            likes=MetricValue.unmeasured(),
            replies=MetricValue.unmeasured(),
            reposts=MetricValue.unmeasured(),
            clicks=MetricValue.unmeasured(),
            conversions=MetricValue.unmeasured(),
            deployments=MetricValue.unmeasured(),
            spend_usd=MetricValue.unmeasured(),
            recorded_at=datetime.now(timezone.utc).isoformat()
        )
        self.performance_store.record_performance(perf_rec)
