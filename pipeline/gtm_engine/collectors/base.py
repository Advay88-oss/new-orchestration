"""
Base Channel Adapter interface for GTM Intelligence Engine (Part 1).
Extensible multi-channel abstraction: Owned Blog, Governance Forum, Newsletter, Docs, Telegram, X.
"""

from abc import ABC, abstractmethod
from datetime import date
from typing import List, Dict, Any, Optional


class ChannelAdapter(ABC):
    channel: str  # Matches canonical `channel` enum: OWNED_BLOG, GOVERNANCE_FORUM, NEWSLETTER, DOCS, TELEGRAM, X

    @abstractmethod
    def discover(self, player: Dict[str, Any]) -> List[str]:
        """Candidate URLs/handles for this player. No network guarantee."""
        pass

    @abstractmethod
    def probe(self, candidates: List[str]) -> List[Dict[str, Any]]:
        """Confirm which candidates actually exist using HTTP HEAD/GET validation."""
        pass

    @abstractmethod
    def collect(self, confirmed: List[str], since: date) -> List[Dict[str, Any]]:
        """Return ARTEFACT records. Must never raise — return [] and log on error."""
        pass

    def health(self) -> Dict[str, Any]:
        """{available: bool, reason: str} — checked before every run."""
        return {"available": True, "reason": "adapter_ready"}
