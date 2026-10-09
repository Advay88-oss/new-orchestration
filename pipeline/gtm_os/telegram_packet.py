"""Phase 7: Human Approval Telegram Decision Packet Builder (telegram_packet.py).

Compiles the decision card for Telegram:
  - Why this signal?
  - Why this audience?
  - Strategic objective & GTM machine
  - The gate's verdict and, on a block, why
  - Claims used and unsupported claims left out
  - Creative concept
  - The editorial judge's score, when one scored the run
  - Buttons: Approve (only when the gate passed), Revise, Kill

Every number on the card is measured or left out. The card used to print a
fixed 95/100 and fixed confidences on every run, a blocked one included,
because the cycle passes no review object.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pipeline.gtm_os.schemas import FullHumanApprovalPacket


def _md(s: Any) -> str:
    """Escape the four characters legacy Telegram Markdown treats as markup."""
    return "".join("\\" + ch if ch in "_*`[" else ch for ch in str(s))


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
        """Assemble the FullHumanApprovalPacket.

        `review_result` is a dict {"score": int|None, "passed": bool,
        "blocking": [str]} or an object with a `score`; None means unreviewed.
        """
        claims_used = [
            {"claim": c.text, "type": c.claim_type, "status": c.evidence_status}
            for c in strategy.claims if getattr(c, "action", "") in ["USE", "USE_AS_INFERENCE"]
        ]
        unsupported = [
            f"{c.text} ({c.rationale})"
            for c in strategy.claims if getattr(c, "action", "") == "DO_NOT_USE"
        ]

        conf_dict: Dict[str, float] = {}
        if confidence_matrix:
            for key, attr in (("intelligence", "intelligence_confidence"),
                              ("evidence", "evidence_confidence"),
                              ("strategy", "strategy_confidence"),
                              ("creative", "creative_quality"),
                              ("claim_safety", "claim_safety")):
                v = getattr(confidence_matrix, attr, None)
                if isinstance(v, (int, float)):
                    conf_dict[key] = float(v)

        review = review_result if isinstance(review_result, dict) else {
            "score": getattr(review_result, "score", None)}
        score = review.get("score")
        score = int(score) if isinstance(score, (int, float)) else None
        channels = [str(ch) for ch in (getattr(content_pkg, "channel_posts", None) or {})]

        from pipeline.brand_brain.context import profile
        deployment = str(profile().get("company", {}).get("deployment", "") or "")

        return FullHumanApprovalPacket(
            packet_id=f"THP-{strategy.strategy_id[:16]}",
            why_this_signal=f"Signal '{signal.headline}' from {signal.source_type} (Confidence: {signal.confidence})",
            why_this_audience=f"Targeting {strategy.audience_segment} to address: {strategy.problem}",
            strategic_objective=strategy.objective,
            selected_machine={
                "machine_id": machine.machine_id if hasattr(machine, "machine_id") else strategy.gtm_machine_id,
                "name": getattr(machine, "name", None) or str(strategy.gtm_machine_id or "—"),
                "status": getattr(machine, "eligibility_status", None) or "—",
            },
            campaign_or_series_context={
                "type": getattr(campaign, "decision_type", None) or "—",
                "id": getattr(campaign, "spec_id", None) or getattr(campaign, "campaign_id", None) or "—",
                "rationale": getattr(campaign, "rationale", None) or "",
            },
            claims_used=claims_used,
            evidence_links=[e.get("source") for e in strategy.evidence if isinstance(e, dict) and e.get("source")],
            unsupported_claims_rejected=unsupported,
            content_variants={
                ch: getattr(p, "hook", "") for ch, p in (getattr(content_pkg, "channel_posts", None) or {}).items()
            },
            creative_concept={
                "thesis": getattr(creative_brief, "creative_thesis", ""),
                "metaphor": getattr(creative_brief, "visual_metaphor", {}).metaphor if hasattr(getattr(creative_brief, "visual_metaphor", None), "metaphor") else getattr(creative_brief, "visual_metaphor", "")
            },
            reviewer_score=score,
            confidence_dimensions=conf_dict,
            gate_passed=review.get("passed"),
            blocking=[str(x) for x in review.get("blocking") or []],
            known_limitations=["Deployment: " + deployment] if deployment else [],
            expected_cta=strategy.cta,
            exact_action_requested=(
                "Revise or kill: the gate blocked these drafts." if review.get("passed") is False
                else "Approve the " + ", ".join(channels) + " drafts for posting by hand." if channels
                else "Review the drafts."),
            available_actions=["APPROVE", "REVISE", "KILL"] if review.get("passed") is not False
            else ["REVISE", "KILL"],
        )

    @staticmethod
    def render_telegram_markdown(packet: FullHumanApprovalPacket) -> str:
        """Render the packet as legacy Telegram Markdown. Only measured numbers are shown."""
        from pipeline.brand_brain.context import company_name
        machine = packet.selected_machine
        lines = [
            f"🔔 *{_md(company_name().upper())} REVIEW* `{packet.packet_id}`\n",
            f"🎯 *Objective:* {_md(packet.strategic_objective)}",
            f"👥 *Audience:* {_md(packet.why_this_audience)}",
            f"⚙️ *GTM Machine:* {_md(machine.get('name'))} ({_md(machine.get('status'))})\n",
        ]
        if packet.gate_passed is not None:
            lines.append("🛡 *Gate:* " + ("passed" if packet.gate_passed else "BLOCKED"))
            for reason in packet.blocking[:4]:
                lines.append("  • " + _md(reason[:200]))
        if packet.claims_used:
            lines.append("📜 *Claims used:*")
            for c in packet.claims_used[:3]:
                lines.append(f"  • {_md(c.get('claim'))} [{_md(c.get('status'))}]")
        if packet.unsupported_claims_rejected:
            lines.append("\n🚫 *Unsupported claims left out:*")
            for u in packet.unsupported_claims_rejected[:2]:
                lines.append("  • " + _md(u))
        lines.append(f"\n🎨 *Creative metaphor:* {_md(packet.creative_concept.get('metaphor') or '—')}")
        lines.append("⭐ *Editorial judge:* " + (f"{packet.reviewer_score}/100" if packet.reviewer_score is not None
                                               else "not scored this run"))
        if packet.confidence_dimensions:
            lines.append("📊 *Confidence:* " + " | ".join(
                f"{_md(k)} {v:.2f}" for k, v in packet.confidence_dimensions.items()))
        lines.extend([
            f"\n🔗 *Call to action:* {_md(packet.expected_cta)}",
            f"❓ *Asked:* {_md(packet.exact_action_requested)}\n",
            "*Buttons:* " + " · ".join(a.title() for a in packet.available_actions),
        ])
        return "\n".join(lines)
