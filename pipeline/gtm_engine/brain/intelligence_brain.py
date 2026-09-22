"""
GTM Intelligence Brain - Programmatic Query Interface (Phase 18).
The primary interface for downstream GTM, campaign, and content agents to query
verified market intelligence, competitor machines, and evidence graphs.
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional

DB_DIR = Path("D:/new orchestration/pipeline/gtm_engine/brain/db")


def _read_jsonl(filename: str) -> List[Dict[str, Any]]:
    filepath = DB_DIR / filename
    if not filepath.exists():
        return []
    records = []
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


class IntelligenceBrain:
    """The central intelligence engine for Vanna's GTM ecosystem."""

    def __init__(self, db_dir: Path = DB_DIR):
        self.db_dir = db_dir

    # Level 1: Market Categories
    def query_markets(self, category_id: Optional[str] = None) -> List[Dict[str, Any]]:
        records = _read_jsonl("markets.jsonl")
        if category_id:
            return [r for r in records if r.get("category_id") == category_id.upper()]
        return records

    # Level 2: Players
    def query_players(
        self,
        category: Optional[str] = None,
        bucket: Optional[str] = None,
        player_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        records = _read_jsonl("players.jsonl")
        if player_id:
            return [r for r in records if r.get("player_id") == player_id.lower()]
        if category:
            records = [r for r in records if r.get("market_category") == category.upper()]
        if bucket:
            records = [r for r in records if r.get("selection_bucket") == bucket.upper()]
        return records

    # Level 3: Products
    def query_products(
        self,
        player_id: Optional[str] = None,
        product_category: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        records = _read_jsonl("products.jsonl")
        if player_id:
            records = [r for r in records if r.get("player_id") == player_id.lower()]
        if product_category:
            records = [r for r in records if r.get("product_category") == product_category.upper()]
        return records

    # Level 4 & 5: Content Corpus & Posts
    def query_posts(
        self,
        player_id: Optional[str] = None,
        content_category: Optional[str] = None,
        content_subcategory: Optional[str] = None,
        evidence_status: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        records = _read_jsonl("posts.jsonl")
        if player_id:
            records = [r for r in records if r.get("player_id") == player_id.lower()]
        if content_category:
            records = [r for r in records if r.get("content_category") == content_category.upper()]
        if content_subcategory:
            records = [r for r in records if r.get("content_subcategory") == content_subcategory.upper()]
        if evidence_status:
            records = [r for r in records if r.get("evidence_status") == evidence_status.upper()]
        return records

    # Level 6: Patterns
    def query_patterns(
        self,
        category: Optional[str] = None,
        pattern_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        records = _read_jsonl("patterns.jsonl")
        if pattern_id:
            return [r for r in records if r.get("pattern_id") == pattern_id.upper()]
        if category:
            return [r for r in records if category.upper() in r.get("market_categories", [])]
        return records

    # Level 7: Recurring Series
    def query_series(
        self,
        player_id: Optional[str] = None,
        cadence: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        records = _read_jsonl("recurring_series.jsonl")
        if player_id:
            records = [r for r in records if r.get("player_id") == player_id.lower()]
        if cadence:
            records = [r for r in records if r.get("cadence") == cadence.upper()]
        return records

    # Level 8: Campaigns
    def query_campaigns(
        self,
        player_id: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        records = _read_jsonl("campaigns.jsonl")
        if player_id:
            records = [r for r in records if r.get("player_id") == player_id.lower()]
        if status:
            records = [r for r in records if r.get("status") == status.upper()]
        return records

    # Level 9: GTM Machines
    def query_gtm_machines(self, machine_id: Optional[str] = None) -> List[Dict[str, Any]]:
        records = _read_jsonl("gtm_machines.jsonl")
        if machine_id:
            return [r for r in records if r.get("machine_id") == machine_id.upper()]
        return records

    # Level 10: Whitespace & Opportunities
    def query_whitespace(self, market_category: Optional[str] = None) -> List[Dict[str, Any]]:
        records = _read_jsonl("whitespace.jsonl")
        if market_category:
            return [r for r in records if r.get("market_category") == market_category.upper()]
        return records

    def query_opportunities(self, priority: Optional[str] = None) -> List[Dict[str, Any]]:
        records = _read_jsonl("opportunities.jsonl")
        if priority:
            return [r for r in records if r.get("priority") == priority.upper()]
        return records

    # Level 11: Evidence Graph
    def query_evidence(self, claim_id: Optional[str] = None) -> List[Dict[str, Any]]:
        graph_file = self.db_dir / "evidence_graph.json"
        if not graph_file.exists():
            return []
        data = json.loads(graph_file.read_text(encoding="utf-8"))
        nodes = data.get("nodes", [])
        if claim_id:
            return [n for n in nodes if n.get("claim_id") == claim_id.upper()]
        return nodes

    # Level 12: Learning & Outcome Feedback Loop
    def record_execution_outcome(self, outcome_record: Dict[str, Any]) -> bool:
        """Record the actual performance of a published GTM campaign post."""
        feedback_file = self.db_dir / "execution_feedback.jsonl"
        with open(feedback_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(outcome_record, ensure_ascii=False) + "\n")
        return True

    def get_learning_loop_summary(self) -> Dict[str, Any]:
        records = _read_jsonl("execution_feedback.jsonl")
        return {
            "total_executions_tracked": len(records),
            "recent_lessons": [r.get("strategic_learning_lesson") for r in records[-5:] if r.get("strategic_learning_lesson")],
            "active_intelligence_signals": [r.get("updated_intelligence_signal") for r in records[-5:] if r.get("updated_intelligence_signal")],
        }
