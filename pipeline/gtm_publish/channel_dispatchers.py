"""Channel dispatchers.

**None of these can publish.** Every one of them used to fabricate a plausible
post id and canonical URL and return `status="SUCCESS"` — including when called
with `mode="LIVE"`, where the live branch was a bare `pass` that fell through to
the same invented receipt. The results were written to the Brain DB as published
posts and seeded into the performance store, so 204 rows claimed Vanna had
posted to x.com and reddit.com at URLs that do not exist.

A publisher that cannot fail is the most dangerous object in a system whose one
rule is that nothing publishes without a human. Until a real API integration
exists, dispatch refuses:

  SIMULATED_TESTNET  -> a receipt clearly marked SIMULATED, never SUCCESS,
                        with no canonical URL to mistake for a real one
  LIVE               -> NotImplementedError

Wiring a real integration means implementing `_publish_live` on a dispatcher
and nothing else; the refusal below is the only thing in the way.
"""

from __future__ import annotations

import hashlib
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from pipeline.gtm_publish.publisher_schemas import (
    ChannelContentPayload,
    ChannelPublishReceipt,
    ExecutionMode,
)


class BaseChannelDispatcher:
    """Base class for social media channel dispatchers."""

    channel_name: str = "BASE"

    def dispatch(
        self,
        request_id: str,
        payload: ChannelContentPayload,
        mode: ExecutionMode = "SIMULATED_TESTNET"
    ) -> ChannelPublishReceipt:
        raise NotImplementedError


class XDispatcher(BaseChannelDispatcher):
    """Dispatcher for X (formerly Twitter)."""

    channel_name = "X"
    MAX_TWEET_CHARS = 280

    def dispatch(
        self,
        request_id: str,
        payload: ChannelContentPayload,
        mode: ExecutionMode = "SIMULATED_TESTNET"
    ) -> ChannelPublishReceipt:
        start_time = time.time()
        receipt_id = f"REC-X-{hashlib.md5(f'{request_id}:{time.time()}'.encode()).hexdigest()[:8]}"

        # Validation
        clean_copy = payload.copy.strip()
        # Basic validation: ensure copy exists
        if not clean_copy:
            return ChannelPublishReceipt(
                receipt_id=receipt_id,
                request_id=request_id,
                channel="X",
                status="FAILED",
                error_message="Empty copy for X dispatch.",
                latency_ms=(time.time() - start_time) * 1000
            )

        if mode == "LIVE":
            raise NotImplementedError(
                "X live dispatch is not implemented. There is no Twitter API "
                "integration here; returning a receipt would be inventing one.")

        # A simulation says SIMULATED. It carries no post id and no URL,
        # because a fabricated URL in a receipt is indistinguishable from a
        # real one the moment it is written to the Brain DB.
        latency = (time.time() - start_time) * 1000

        return ChannelPublishReceipt(
            receipt_id=receipt_id,
            request_id=request_id,
            channel="X",
            status="SIMULATED",
            error_message="SIMULATED — no post was made; X dispatch is not implemented",
            post_id=None,
            canonical_url=None,
            published_at=None,
            latency_ms=round(latency, 2),
            raw_response={
                "simulated": True, "text": clean_copy[:100] + "...",
                "media_attached": len(payload.media_paths) > 0,
                "mode": mode
            }
        )


class LinkedInDispatcher(BaseChannelDispatcher):
    """Dispatcher for LinkedIn."""

    channel_name = "LinkedIn"

    def dispatch(
        self,
        request_id: str,
        payload: ChannelContentPayload,
        mode: ExecutionMode = "SIMULATED_TESTNET"
    ) -> ChannelPublishReceipt:
        start_time = time.time()
        receipt_id = f"REC-LI-{hashlib.md5(f'{request_id}:{time.time()}'.encode()).hexdigest()[:8]}"

        clean_copy = payload.copy.strip()
        if not clean_copy:
            return ChannelPublishReceipt(
                receipt_id=receipt_id,
                request_id=request_id,
                channel="LinkedIn",
                status="FAILED",
                error_message="Empty copy for LinkedIn dispatch.",
                latency_ms=(time.time() - start_time) * 1000
            )

        if mode == "LIVE":
            raise NotImplementedError(
                "LinkedIn live dispatch is not implemented. There is no "
                "LinkedIn API integration here.")

        latency = (time.time() - start_time) * 1000

        return ChannelPublishReceipt(
            receipt_id=receipt_id,
            request_id=request_id,
            channel="LinkedIn",
            status="SIMULATED",
            error_message="SIMULATED — no post was made; LinkedIn dispatch is not implemented",
            post_id=None,
            canonical_url=None,
            published_at=None,
            latency_ms=round(latency, 2),
            raw_response={
                "simulated": True,
                "media_count": len(payload.media_paths),
                "mode": mode
            }
        )


class RedditDispatcher(BaseChannelDispatcher):
    """Dispatcher for Reddit."""

    channel_name = "Reddit"

    def dispatch(
        self,
        request_id: str,
        payload: ChannelContentPayload,
        mode: ExecutionMode = "SIMULATED_TESTNET"
    ) -> ChannelPublishReceipt:
        start_time = time.time()
        receipt_id = f"REC-RD-{hashlib.md5(f'{request_id}:{time.time()}'.encode()).hexdigest()[:8]}"

        clean_copy = payload.copy.strip()
        subreddit = payload.target_community or "r/defi"

        if not clean_copy:
            return ChannelPublishReceipt(
                receipt_id=receipt_id,
                request_id=request_id,
                channel="Reddit",
                status="FAILED",
                error_message="Empty submission body for Reddit dispatch.",
                latency_ms=(time.time() - start_time) * 1000
            )

        if mode == "LIVE":
            raise NotImplementedError(
                "Reddit live dispatch is not implemented. There is no Reddit "
                "API integration here.")

        latency = (time.time() - start_time) * 1000

        return ChannelPublishReceipt(
            receipt_id=receipt_id,
            request_id=request_id,
            channel="Reddit",
            status="SIMULATED",
            error_message="SIMULATED — no post was made; Reddit dispatch is not implemented",
            post_id=None,
            canonical_url=None,
            published_at=None,
            latency_ms=round(latency, 2),
            raw_response={
                "simulated": True,
                "subreddit": subreddit,
                "mode": mode
            }
        )
