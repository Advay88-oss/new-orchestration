"""Agent 06 — Content Creator.

**This module used to contain the posts.**

Every line of the X thread, the LinkedIn article and the Reddit breakdown was a
string literal in `create_content_package`, with `brief.call_to_action` and
`brief.proof_points` interpolated into fixed sentences. The 2026-09-17 run
trace (`pipeline/state/full_live_gtm_run_trace.json`) contains "150 gwei",
"0.00014 XLM", "320ms" and "mempool" because they were typed here, not because
a model wrote them — so a run could report CONTENT_CREATED having generated
nothing, and the output was identical for every signal the system ever saw.

`ChannelAdapter` already did this job properly: it calls gemini-3.8-flash,
carries claim provenance per post, and splits threads. There is no reason for
two content creators, and the one that cannot fail is the dangerous one. This
module now delegates to it and keeps its own signature so existing callers
(`gtm_orchestrator.py`) do not change.
"""
from __future__ import annotations

from typing import Optional

from pipeline.gtm_orchestration.schemas import ContentBrief, ContentPackage, GTMStrategy
from pipeline.gtm_content.channel_adapter import ChannelAdapter
from pipeline.gtm_os.agent_runtime import record_stage as _record_stage

_AGENT = "A06_channel_adapter"


class ContentCreator:
    """Thin delegation to ChannelAdapter, kept for call-site compatibility."""

    def __init__(self, adapter: Optional[ChannelAdapter] = None):
        self.adapter = adapter or ChannelAdapter()

    def create_content_package(
        self,
        strategy: GTMStrategy,
        brief: Optional[ContentBrief] = None,
        campaign_id: Optional[str] = None,
    ) -> ContentPackage:
        """Generate platform-native posts for X, LinkedIn and Reddit."""
        if strategy.action_status in ("NO_ACTION", "KILL"):
            raise ValueError(
                "Content Creator cannot draft content for a "
                f"{strategy.action_status} strategy.")

        package = self.adapter.adapt_strategy_to_channels(
            strategy,
            campaign_id=campaign_id or getattr(brief, "campaign_id", None)
            or strategy.strategy_id,
        )
        _record_stage(_AGENT, "ok",
                      "generated posts via ChannelAdapter for "
                      + str(strategy.strategy_id),
                      outputs=[getattr(package, "package_id", "")])
        return package
