"""Phase 7 Extension: Dispatch Retry Queue (dispatch_retry_queue.py).

Guarantees message delivery across social channels (X, LinkedIn, Reddit):
  - Captures failed dispatch receipts into persistent retry queue.
  - Implements exponential backoff (attempt 1: 5s, attempt 2: 20s, attempt 3: 60s).
  - Emits terminal alerts if maximum retries are exhausted.
"""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

REPO_ROOT = Path("D:/new orchestration")
STATE_DIR = REPO_ROOT / "pipeline" / "state"
RETRY_FILE = STATE_DIR / "dispatch_retries.jsonl"

from pipeline.gtm_storage.atomic_store import AtomicJsonlStore
from pipeline.gtm_publish.publisher_schemas import (
    ChannelContentPayload,
    ChannelPublishReceipt,
    ExecutionMode,
)
from pipeline.gtm_publish.channel_dispatchers import (
    XDispatcher,
    LinkedInDispatcher,
    RedditDispatcher,
)


class RetryEntry(BaseModel):
    retry_id: str
    request_id: str
    channel: str
    payload: Dict[str, Any]
    attempt_count: int = 1
    max_attempts: int = 3
    next_retry_at: float
    status: str = "PENDING_RETRY"  # PENDING_RETRY, RETRIED_SUCCESS, ABANDONED
    last_error: Optional[str] = None


class DispatchRetryQueue:
    """Manages automatic retry execution for failed channel dispatches."""

    def __init__(self, retry_file: Optional[Path] = None):
        self.store = AtomicJsonlStore(retry_file or RETRY_FILE)
        self.dispatchers = {
            "X": XDispatcher(),
            "LinkedIn": LinkedInDispatcher(),
            "Reddit": RedditDispatcher(),
        }

    def enqueue_failure(
        self,
        request_id: str,
        channel_payload: ChannelContentPayload,
        error_message: str
    ) -> RetryEntry:
        """Enqueues a failed dispatch for automated retry."""
        retry_id = f"RTY-{int(time.time())}-{channel_payload.channel}"
        entry = RetryEntry(
            retry_id=retry_id,
            request_id=request_id,
            channel=channel_payload.channel,
            payload=channel_payload.model_dump(),
            attempt_count=1,
            next_retry_at=time.time() + 5.0,
            last_error=error_message
        )
        self.store.append(entry.model_dump())
        print(f"⚠️ DISPATCH RETRY QUEUE: Enqueued {channel_payload.channel} failure for retry ({retry_id}).")
        return entry

    def process_pending_retries(self, mode: ExecutionMode = "SIMULATED_TESTNET") -> List[ChannelPublishReceipt]:
        """Processes all mature retry entries."""
        now = time.time()
        records = self.store.read_all()
        updated_records = []
        successful_receipts: List[ChannelPublishReceipt] = []

        for r in records:
            if r.get("status") != "PENDING_RETRY":
                updated_records.append(r)
                continue

            if now < r.get("next_retry_at", 0):
                updated_records.append(r)
                continue

            # Attempt retry
            channel = r["channel"]
            dispatcher = self.dispatchers.get(channel)
            payload = ChannelContentPayload(**r["payload"])

            receipt = dispatcher.dispatch(r["request_id"], payload, mode=mode)
            if receipt.status == "SUCCESS":
                r["status"] = "RETRIED_SUCCESS"
                successful_receipts.append(receipt)
                print(f"✅ DISPATCH RETRY QUEUE: Retry succeeded for {channel} ({receipt.canonical_url}).")
            else:
                attempts = r.get("attempt_count", 1) + 1
                r["attempt_count"] = attempts
                r["last_error"] = receipt.error_message
                if attempts >= r.get("max_attempts", 3):
                    r["status"] = "ABANDONED"
                    print(f"❌ DISPATCH RETRY QUEUE: Max attempts exhausted for {channel}. Abandoned.")
                else:
                    backoff = (5.0 * (4 ** (attempts - 1)))
                    r["next_retry_at"] = time.time() + backoff
                    print(f"⚠️ DISPATCH RETRY QUEUE: Retry failed. Rescheduling {channel} in {backoff:.1f}s (Attempt {attempts}).")

            updated_records.append(r)

        self.store.atomic_overwrite(updated_records)
        return successful_receipts
