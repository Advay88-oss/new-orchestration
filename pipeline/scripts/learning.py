#!/usr/bin/env python3
"""Shared helpers for the content learning loop.

The loop: Create -> Publish -> Measure -> Analyse -> Learn -> Improve.

Design decision that keeps it safe across companies (OKF V6 isolation):
learnings are ABSTRACT features only — hook type, format, platform, theme
bucket, timing — plus aggregate engagement numbers. They carry NO tenant's
proprietary claims or copy. So a pattern learned on Auri can safely reinforce
Vanna's strategy: "question hooks outperform statements" transfers; "gold is
non-custodial" never leaves Auri.

Stores live in pipeline/state/learning/:
  performance.jsonl  — one row per published post (own content), with features + engagement
  competitive.jsonl  — competitor signals (from the trend scout), with features + engagement
  patterns.json      — the derived cross-company knowledge base
  INSIGHTS.md        — human-readable current learnings, injected into generation
"""

from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
STORE = REPO / "pipeline" / "state" / "learning"
PERF = STORE / "performance.jsonl"
COMP = STORE / "competitive.jsonl"
PATTERNS = STORE / "patterns.json"
INSIGHTS = STORE / "INSIGHTS.md"

# Competitor / own handles that mark a "comparison" hook
_COMPARE = re.compile(
    r"\b(vs\.?|versus|everyone|nobody|no one|unlike|instead of|"
    r"wealthsimple|onegold|coinbase|nexo|ledn|glint|kinesis|morpho|aave|gearbox|"
    r"banks?|etf)\b", re.I)
_CONTRARIAN = re.compile(r"\b(nobody|no one|everyone|the only|isn'?t|not just|until now)\b", re.I)
_NUMBER = re.compile(r"\d")


def hook_type(text: str) -> str:
    """Classify a hook by its rhetorical shape — the reusable, cross-company signal."""
    t = (text or "").strip()
    if not t:
        return "none"
    if t.rstrip().endswith("?"):
        return "question"
    if _COMPARE.search(t):
        return "comparison"
    if _CONTRARIAN.search(t):
        return "contrarian"
    if _NUMBER.search(t):
        return "stat-led"
    return "statement"


def theme_bucket(topic: str, text: str = "") -> str:
    """Coarse, company-neutral theme so patterns aggregate across brands."""
    s = f"{topic} {text}".lower()
    pairs = [
        ("security", ["hijack", "exploit", "secure", "custod", "keys", "risk", "liquidat"]),
        ("infrastructure", ["infrastructure", "api", "rails", "system", "developer", "b2b", "platform"]),
        ("regulation", ["fca", "regulat", "framework", "licens", "compliance"]),
        ("competitive", ["vs", "everyone", "nobody", "only", "beat", "warehouse"]),
        ("efficiency", ["efficien", "unified", "collateral", "leverage", "margin"]),
        ("credit", ["borrow", "credit", "loan", "lend", "3.75"]),
        ("trust", ["non-custodial", "attested", "allocated", "proof", "vault"]),
    ]
    for name, kws in pairs:
        if any(k in s for k in kws):
            return name
    return topic.split()[0].lower() if topic else "general"


def features(*, tenant: str, platform: str, topic: str, hook: str,
             fmt: str = "stat-card", arc: str = "") -> dict:
    """The feature vector attached to every measured item. Abstract, shareable."""
    return {
        "tenant": tenant,
        "platform": platform,
        "hook_type": hook_type(hook),
        "theme": theme_bucket(topic, hook),
        "format": fmt,
        "arc": arc,
        "has_number": bool(_NUMBER.search(hook or "")),
        "hook_words": len((hook or "").split()),
    }


def ensure_store() -> None:
    STORE.mkdir(parents=True, exist_ok=True)


def learning_brief() -> str:
    """The Improve step: the current learnings, as a short brief to inject into
    generation. Empty string if nothing has been learned yet, so callers can
    append it unconditionally. This is what closes the loop — the generator
    reads it and biases toward what is working."""
    if not INSIGHTS.exists():
        return ""
    import json as _json
    md = INSIGHTS.read_text(encoding="utf-8")
    # Pull just the "Recommended biases" section — the actionable part.
    marker = "## Recommended biases"
    brief = md[md.index(marker):] if marker in md else ""
    top = ""
    if PATTERNS.exists():
        try:
            p = _json.loads(PATTERNS.read_text(encoding="utf-8"))
            hooks = ", ".join(f"{r['value']} ({r['avg']})" for r in p["market"]["by_hook_type"][:3])
            themes = ", ".join(f"{r['value']} ({r['avg']})" for r in p["market"]["by_theme"][:3])
            top = (f"\nMarket engagement by hook type: {hooks}. "
                   f"By theme: {themes}. (higher = better)\n")
        except Exception:
            pass
    if not brief and not top:
        return ""
    return ("\n\n---\n\n# LEARNED SIGNAL (bias toward this, never over the safety gate)\n"
            f"{top}{brief}")


if __name__ == "__main__":
    import sys
    if "--brief" in sys.argv:
        print(learning_brief() or "(no learnings yet)")
