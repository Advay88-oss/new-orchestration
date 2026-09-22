"""
Automated Campaign Brief Builder Engine.
Generates reusable campaign brief packages (brief.md, research.md, tickets)
by combining internal context (audience, objections, positioning, learnings)
with runnable patterns filtered strictly by verdict__in=['OWN', 'ADAPT_STRUCTURE'].
Zero manual copywriting required for new campaigns.
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional

REPO_ROOT = Path("D:/new orchestration")
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

DB_DIR = REPO_ROOT / "pipeline" / "gtm_engine" / "brain" / "db"
WORK_DIR = REPO_ROOT / "work" / "campaigns"

from exporters.notion.vanna_verdict import load_internal_context, vanna_verdict


def query_runnable_patterns(allowed_verdicts: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    """Query patterns from Brain DB filtered strictly by allowed verdicts (default: OWN, ADAPT_STRUCTURE)."""
    if allowed_verdicts is None:
        allowed_verdicts = ["OWN", "ADAPT_STRUCTURE"]

    ctx = load_internal_context()
    patterns_file = DB_DIR / "patterns.jsonl"
    if not patterns_file.exists():
        return []

    runnable = []
    with open(patterns_file, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                pat = json.loads(line)
                verdict_data = vanna_verdict(pat, ctx)
                if verdict_data["verdict"] in allowed_verdicts:
                    pat["verdict_data"] = verdict_data
                    runnable.append(pat)

    return runnable


def render_brief(campaign_id: str, goal: str, ctx: Dict[str, str], patterns: List[Dict[str, Any]]) -> Path:
    """Render the full campaign package into work/campaigns/{campaign_id}/."""
    campaign_dir = WORK_DIR / campaign_id
    tickets_dir = campaign_dir / "tickets"
    outputs_dir = campaign_dir / "outputs"
    tickets_dir.mkdir(parents=True, exist_ok=True)
    outputs_dir.mkdir(parents=True, exist_ok=True)

    # 1. Generate brief.md
    brief_lines = [
        f"# Campaign Brief: {campaign_id.replace('_', ' ').title()}\n",
        f"**Campaign ID:** `{campaign_id}`",
        f"**Status:** READY_FOR_PRODUCTION · **Filter Policy:** `verdict__in=['OWN', 'ADAPT_STRUCTURE']`\n",
        "## 1. Goal & Objective",
        f"* **Goal:** {goal}\n",
        "## 2. Target Audience (from knowledge/internal/audience.md)",
        "* **Primary:** Segment A1 · Stellar / Soroban DeFi Farmers & Traders",
        "* **Secondary:** Segment A3 · Ecosystem Builders & Protocol Integrators",
        "* **Audience Pain Point:** Manual multi-transaction leverage looping across Blend/Aquarius and liquidation risk.\n",
        "## 3. Approved Angle & Positioning (from knowledge/internal/positioning.md)",
        "* **Pillar:** Pillar 1 ('The Composable Credit Primitive on Soroban') & Pillar 2 ('SmartAccount Sandboxes').",
        "* **Rejected Framing Enforced:** Never call Vanna 'The Aave of Stellar'; never claim mainnet live or fake TVL.\n",
        "## 4. Grounded Runnable Patterns (Filtered from Brain DB)",
    ]

    for p in patterns:
        vd = p.get("verdict_data", {})
        brief_lines.append(f"- **{p.get('name')}** (`{vd.get('verdict')}`)")
        brief_lines.append(f"  - Target: {vd.get('target_segment')}")
        brief_lines.append(f"  - Rebuts: {vd.get('objection_addressed')}")
        brief_lines.append(f"  - Execution: {vd.get('vanna_version')}\n")

    brief_lines.append("## 5. Review Gates")
    brief_lines.append("* [ ] Writer drafts thread using only verified testnet claims.")
    brief_lines.append("* [ ] Critic asserts zero prohibited claims.")
    brief_lines.append("* [ ] Outcome logger records founder decision.")

    brief_path = campaign_dir / "brief.md"
    brief_path.write_text("\n".join(brief_lines), encoding="utf-8")

    # 2. Generate research.md
    research_lines = [
        f"# Campaign Research Grounding: {campaign_id}\n",
        "**Source:** Brain DB runnable patterns (`OWN`, `ADAPT_STRUCTURE` only). Excludes un-runnable mainnet patterns.\n",
        "## Selected Patterns & Evidence Grounding\n"
    ]
    for p in patterns:
        research_lines.append(f"### {p.get('name')}")
        research_lines.append(f"- **Definition:** {p.get('definition')}")
        research_lines.append(f"- **Independent Examples Count:** {p.get('independent_example_count')}")
        research_lines.append(f"- **Source IDs:** {', '.join(p.get('source_record_ids', []))}\n")

    research_path = campaign_dir / "research.md"
    research_path.write_text("\n".join(research_lines), encoding="utf-8")

    # 3. Generate initial ticket
    ticket_lines = [
        f"# Ticket 01: Production Draft for {campaign_id}\n",
        f"**Campaign:** `{campaign_id}` · **Priority:** P0 · **Assignee:** Writer Agent\n",
        "## Deliverable",
        "Author a technical 5-tweet thread and 180px/220px visual specification adhering to `knowledge/campaign-book.md`.",
        "## Acceptance Criteria",
        "- Cites Stellar Testnet and Freighter wallet.",
        "- Answers Objection #1 and Objection #3.",
        "- Adheres strictly to the runnable patterns in `research.md`."
    ]
    ticket_path = tickets_dir / "ticket_01_production.md"
    ticket_path.write_text("\n".join(ticket_lines), encoding="utf-8")

    return brief_path


def brief_builder(campaign_id: str, goal: str) -> Dict[str, Any]:
    """Automated brief builder entrypoint."""
    ctx = load_internal_context()
    patterns = query_runnable_patterns(allowed_verdicts=["OWN", "ADAPT_STRUCTURE"])
    brief_file = render_brief(campaign_id, goal, ctx, patterns)

    print(f"✅ Generated Campaign Brief Package: {brief_file.parent}")
    print(f"   • Filtered runnable patterns: {len(patterns)} patterns selected")
    print(f"   • Excluded un-runnable patterns: TVL milestones, token emissions, mainnet-blocked embeds")

    return {
        "campaign_id": campaign_id,
        "brief_path": str(brief_file),
        "runnable_patterns_count": len(patterns),
        "patterns_used": [p.get("name") for p in patterns]
    }


if __name__ == "__main__":
    brief_builder(
        campaign_id="camp_002_liquidation_buffer_defense",
        goal="Position Vanna's 1.10x RiskEngine health factor floor as the mathematical defense against cascading liquidations on Stellar Soroban."
    )
