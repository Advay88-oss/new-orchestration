"""What the engine has already talked about, so it stops repeating itself.

Across 41 runs the pipeline chose four distinct signals, and 32 of those runs
landed on the same one: Blend v2 pool architecture. Not because A02 is broken
— it reasons over the candidates and picks the strongest one, correctly, every
time. The inputs were the same each cycle, so the winner was too.

The fix is the one already used for visual archetypes and meme palettes: do
not instruct the model to vary, **remove the recent choices from the candidate
set**. A rule the model is asked to follow is a suggestion; a candidate that
is not in the list cannot be chosen.

Topics are matched on a normalised fingerprint rather than an exact string,
because "Blend v2 pool architecture formal verification" and "[Blend Protocol
Docs] Blend v2 pool architecture formal verification" are the same subject
wearing a different prefix — and both were being picked as if new.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Iterable, Optional

STATE_DIR = Path(__file__).resolve().parents[1] / "state"
RECENT_FILE = STATE_DIR / "recent_signals.json"

# How many past subjects are blocked.
#
# Tuned down from 6 after watching it starve the strategist. Vanna's domain is
# narrow — composable credit on Soroban — so blocking six subjects pushed the
# remaining candidates far enough off-topic that A03 declined three in a row
# and the cycle produced nothing. Three is enough to stop the "Blend pools
# every run" pattern while leaving relevant material to choose from.
#
# Novelty is a preference, not an absolute: producing nothing is worse than
# revisiting a subject from four cycles ago.
BLOCK_LAST = 3

# Kept longer than the block window so the panel can still show what has been
# covered without those entries suppressing anything.
KEEP = 40

_STOP = {
    "the", "a", "an", "and", "or", "for", "of", "to", "in", "on", "with",
    "is", "are", "its", "it", "as", "at", "by", "from", "new", "how", "why",
    "protocol", "docs", "blog", "update", "announcement", "official",
}


def fingerprint(headline: str) -> str:
    """A subject's identity, independent of how the source titled it.

    Source prefixes (`[Blend Protocol Docs] `), punctuation and filler words
    are dropped, and what remains is sorted — so two phrasings of one story
    collapse to the same key instead of reading as two separate topics.
    """
    s = re.sub(r"^\s*\[[^\]]{0,60}\]\s*", "", str(headline or "").lower())
    s = re.sub(r"[^a-z0-9\s]", " ", s)
    words = [w for w in s.split() if len(w) > 2 and w not in _STOP]
    return " ".join(sorted(set(words))[:8])


def _load() -> list[dict[str, Any]]:
    try:
        data = json.loads(RECENT_FILE.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except Exception:                               # noqa: BLE001 — boundary
        return []


def recent_fingerprints(n: int = BLOCK_LAST) -> set[str]:
    return {r.get("fp", "") for r in _load()[:n] if r.get("fp")}


def covered() -> list[dict[str, Any]]:
    """Everything covered so far, newest first — for the Ideas Panel."""
    return _load()


def remember(headline: str, run_id: Optional[str] = None) -> None:
    """Record a chosen subject. Never raises: this must not fail a run."""
    try:
        fp = fingerprint(headline)
        if not fp:
            return
        rows = [r for r in _load() if r.get("fp") != fp]
        rows.insert(0, {"fp": fp, "headline": str(headline)[:200], "run_id": run_id})
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        RECENT_FILE.write_text(json.dumps(rows[:KEEP], indent=2), encoding="utf-8")
    except Exception:                               # noqa: BLE001 — boundary
        pass


def split_fresh(signals: Iterable[Any]) -> tuple[list[Any], list[Any]]:
    """Partition signals into (not covered recently, covered recently).

    Returns both halves rather than filtering, because the stale ones are not
    worthless — they are what the Ideas Panel offers as "already covered", and
    they are the fallback when every candidate is stale.
    """
    blocked = recent_fingerprints()
    fresh, stale = [], []
    for s in signals:
        head = getattr(s, "headline", None) or (
            s.get("headline") if isinstance(s, dict) else str(s))
        (stale if fingerprint(head) in blocked else fresh).append(s)
    return fresh, stale
