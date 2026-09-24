"""Phase 4: Channel Adaptation Reviewer (channel_reviewer.py).

Audits cross-platform distinctness, claim provenance, and platform compliance:
  1. Distinctness: Prohibits copy-paste shortening (asserts structural divergence).
  2. Claim Provenance: Verifies every post carries source claims and evidence refs.
  3. Channel Invariants: Enforces Reddit disclosures, X brevity, LinkedIn institutional tone.
Emits channel_adaptation_audit.json.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone

REPO_ROOT = Path(__file__).resolve().parents[2]
STATE_DIR = REPO_ROOT / "pipeline" / "state"

from pipeline.gtm_content.schemas import ChannelAdaptationPackage, ChannelReviewVerdict


class ChannelReviewer:
    """Audits multi-channel packages before they reach the creative or approval gates."""

    def review_channel_adaptation(
        self,
        package: ChannelAdaptationPackage,
        out_audit_file: Optional[Path] = None
    ) -> ChannelReviewVerdict:
        """Evaluate distinctness, claim coverage, and channel constraints."""
        posts = package.channel_posts
        blocked_claims: List[str] = []
        channel_issues: Dict[str, List[str]] = {}

        # 1. Distinctness Check (Compare X vs LinkedIn vs Reddit lengths and word overlap)
        x_copy = posts.get("x", None)
        li_copy = posts.get("linkedin", None)
        rd_copy = posts.get("reddit", None)

        if not (x_copy and li_copy and rd_copy):
            return ChannelReviewVerdict(
                package_id=package.package_id,
                approved=False,
                distinctness_score=0,
                claim_provenance_verified=False,
                blocked_unsupported_claims=["Missing one or more required distribution channels (X, LinkedIn, Reddit)"],
                channel_issues={"global": ["Incomplete channel coverage"]},
                reasoning="Package must adapt to all three core distribution channels."
            )

        # Word set divergence calculation
        words_x = set(x_copy.copy.lower().split())
        words_li = set(li_copy.copy.lower().split())
        words_rd = set(rd_copy.copy.lower().split())

        overlap_x_li = len(words_x.intersection(words_li)) / max(1, len(words_x.union(words_li)))
        overlap_li_rd = len(words_li.intersection(words_rd)) / max(1, len(words_li.union(words_rd)))
        
        # Distinctness score: higher when platforms have diverse vocabulary and structures
        distinctness_score = int(100 - (overlap_x_li * 35 + overlap_li_rd * 35))

        # 2. Check for Prohibited Strings Across All Channels
        prohibited_terms = [
            "aave of stellar", "mainnet live", "uncontested first-mover", "zero competitors exist", "pivotal moment"
        ]
        for ch_name, p in posts.items():
            ch_issues: List[str] = []
            text_lower = p.copy.lower()
            for bad in prohibited_terms:
                if bad in text_lower:
                    blocked_claims.append(f"Channel {ch_name.upper()} contains prohibited assertion: '{bad}'")
                    ch_issues.append(f"Prohibited term: '{bad}'")

            # 3. Channel Specific Constraints
            if ch_name == "x":
                # X copy ships as a thread, so the whole body is not one tweet.
                # The limit was 800, which the adapter met by cutting copy
                # mid-sentence; once it stopped cutting, every explainer was
                # blocked here with nothing in the run notes to say why. The
                # ceiling now matches the adapter's own (channel_adapter.X_MAX),
                # and the lead — the hook, which is what appears alone — is
                # held to one tweet.
                if len(p.copy) > 1600:
                    ch_issues.append(f"X thread copy exceeds 1600 characters ({len(p.copy)} chars)")
                if len(p.hook or "") > 280:
                    ch_issues.append(f"X hook exceeds one tweet ({len(p.hook)} chars)")
            elif ch_name == "reddit":
                if "disclosure" not in text_lower and "testnet" not in text_lower:
                    ch_issues.append("Reddit post lacks required builder testnet disclosure")
                if not p.discussion_question:
                    ch_issues.append("Reddit post missing community discussion question")
            elif ch_name == "linkedin":
                if "failure modes" not in text_lower and "architecture" not in text_lower:
                    ch_issues.append("LinkedIn post lacks institutional architecture framing")

            if ch_issues:
                channel_issues[ch_name] = ch_issues

        # 4. Claim Provenance Check
        has_provenance = all(len(p.source_claims) > 0 and len(p.exact_evidence_refs) > 0 for p in posts.values())

        approved = distinctness_score >= 60 and len(blocked_claims) == 0 and len(channel_issues) == 0 and has_provenance

        verdict = ChannelReviewVerdict(
            package_id=package.package_id,
            approved=approved,
            distinctness_score=distinctness_score,
            claim_provenance_verified=has_provenance,
            blocked_unsupported_claims=blocked_claims,
            channel_issues=channel_issues,
            reasoning=(
                f"Channel adaptation successfully verified across X, LinkedIn, and Reddit. "
                f"Distinctness score: {distinctness_score}/100. All claims backed by provenance refs."
                if approved else f"Channel adaptation rejected due to: {blocked_claims or channel_issues}"
            )
        )

        out_path = out_audit_file or (STATE_DIR / "channel_adaptation_audit.json")
        audit_data = {
            "audit_timestamp": datetime.now(timezone.utc).isoformat(),
            "package_id": package.package_id,
            "approved": verdict.approved,
            "distinctness_score": verdict.distinctness_score,
            "claim_provenance_verified": verdict.claim_provenance_verified,
            "channels_audited": list(posts.keys()),
            "blocked_claims_count": len(blocked_claims),
            "reasoning": verdict.reasoning
        }
        out_path.write_text(json.dumps(audit_data, indent=2), encoding="utf-8")
        print(f"📊 Emitted Channel Adaptation Audit Report: {out_path.name}")
        return verdict
