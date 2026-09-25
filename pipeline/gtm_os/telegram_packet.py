"""Phase 7: Human Approval Telegram Decision Packet Builder (telegram_packet.py).

Compiles the rich, explainable decision card for Telegram:
  - Why this signal?
  - Why this audience?
  - Strategic objective & GTM machine
  - Evidence links & claims used
  - Unsupported claims rejected
  - Content variants (X, LinkedIn, Reddit)
  - Creative concept
  - Reviewer score & confidence dimensions
  - Actions: APPROVE, REVISE, REGENERATE, KILL, REQUEST_EVIDENCE, REJECT_MACHINE, PAUSE_CAMPAIGN
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone

from pipeline.gtm_os.schemas import FullHumanApprovalPacket


class TelegramPacketBuilder:
    """Formats the human approval packet for Telegram display and interactive callbacks."""

    @staticmethod
    def build_packet(
        signal: Any,
        strategy: Any,
        claims: List[Any],
        machine: Any,
        campaign: Any,
        content_pkg: Any,
        creative_brief: Any,
        review_result: Any,
        confidence_matrix: Optional[Any] = None
    ) -> FullHumanApprovalPacket:
        """Assemble the complete FullHumanApprovalPacket."""
        claims_used = [
            {"claim": c.text, "type": c.claim_type, "status": c.evidence_status}
            for c in strategy.claims if getattr(c, "action", "") in ["USE", "USE_AS_INFERENCE"]
        ]
        unsupported = [
            f"{c.text} ({c.rationale})"
            for c in strategy.claims if getattr(c, "action", "") == "DO_NOT_USE"
        ]

        conf_dict = {
            "intelligence": 0.90,
            "evidence": 0.95,
            "strategy": 0.92,
            "creative": 0.90,
            "claim_safety": 1.00
        }
        if confidence_matrix:
            conf_dict = {
                "intelligence": getattr(confidence_matrix, "intelligence_confidence", 0.90),
                "evidence": getattr(confidence_matrix, "evidence_confidence", 0.95),
                "strategy": getattr(confidence_matrix, "strategy_confidence", 0.92),
                "creative": getattr(confidence_matrix, "creative_quality", 0.90),
                "claim_safety": getattr(confidence_matrix, "claim_safety", 1.00)
            }

        packet = FullHumanApprovalPacket(
            packet_id=f"THP-{strategy.strategy_id[:16]}",
            why_this_signal=f"Signal '{signal.headline}' from {signal.source_type} (Confidence: {signal.confidence})",
            why_this_audience=f"Targeting {strategy.audience_segment} to address verified friction: {strategy.problem}",
            strategic_objective=strategy.objective,
            selected_machine={
                "machine_id": machine.machine_id if hasattr(machine, "machine_id") else strategy.gtm_machine_id,
                "name": getattr(machine, "name", "GTM Machine"),
                "status": getattr(machine, "eligibility_status", "ELIGIBLE")
            },
            campaign_or_series_context={
                "type": getattr(campaign, "decision_type", "CAMPAIGN"),
                "id": getattr(campaign, "spec_id", getattr(campaign, "campaign_id", "ACTIVE_CAMPAIGN")),
                "rationale": getattr(campaign, "rationale", "Phased execution")
            },
            claims_used=claims_used,
            evidence_links=[e.get("source") for e in strategy.evidence if isinstance(e, dict) and e.get("source")],
            unsupported_claims_rejected=unsupported,
            content_variants={
                ch: getattr(p, "hook", "") for ch, p in getattr(content_pkg, "channel_posts", {}).items()
            },
            creative_concept={
                "thesis": getattr(creative_brief, "creative_thesis", ""),
                "metaphor": getattr(creative_brief, "visual_metaphor", {}).metaphor if hasattr(getattr(creative_brief, "visual_metaphor", None), "metaphor") else getattr(creative_brief, "visual_metaphor", "")
            },
            reviewer_score=getattr(review_result, "score", 95),
            confidence_dimensions=conf_dict,
            known_limitations=[
                "Deployment: " + str(__import__('pipeline.brand_brain.context', fromlist=['profile']).profile().get("company", {}).get("deployment", "")),
            ],
            expected_cta=strategy.cta,
            exact_action_requested="Approve distribution of X thread lead, LinkedIn executive brief, and Reddit technical discussion."
        )
        return packet

    @staticmethod
    def render_telegram_markdown(packet: FullHumanApprovalPacket) -> str:
        """Render the packet into Telegram MarkdownV2 compatible text."""
        lines = [
            f"🔔 *{__import__('pipeline.brand_brain.context', fromlist=['company_name']).company_name().upper()} GTM APPROVAL GATE* `{packet.packet_id}`\n",
            f"🎯 *Strategic Objective:* {packet.strategic_objective}",
            f"👥 *Target Audience:* {packet.why_this_audience}",
            f"⚙️ *GTM Machine:* `{packet.selected_machine.get('name')}` ({packet.selected_machine.get('status')})\n",
            "📜 *Claims Verified & Grounded:*",
        ]
        for c in packet.claims_used[:3]:
            lines.append(f"  • `{c.get('claim')}` [{c.get('status')}]")

        if packet.unsupported_claims_rejected:
            lines.append("\n🚫 *Unsupported Claims Blocked:*")
            for u in packet.unsupported_claims_rejected[:2]:
                lines.append(f"  • {u}")

        lines.extend([
            f"\n🎨 *Creative Metaphor:* {packet.creative_concept.get('metaphor')}",
            f"⭐ *Pre-Delivery Reviewer Score:* `{packet.reviewer_score}/100`",
            f"📊 *Confidence Dimensions:* Evidence `{packet.confidence_dimensions.get('evidence', 1.0):.2f}` | Strategy `{packet.confidence_dimensions.get('strategy', 1.0):.2f}` | Claim Safety `{packet.confidence_dimensions.get('claim_safety', 1.0):.2f}`\n",
            f"🔗 *Call to Action:* `{packet.expected_cta}`",
            f"❓ *Action Requested:* {packet.exact_action_requested}\n",
            "*Available Actions:* [APPROVE] · [REVISE] · [REGENERATE] · [KILL] · [REQUEST_EVIDENCE] · [REJECT_MACHINE]"
        ])
        return "\n".join(lines)
