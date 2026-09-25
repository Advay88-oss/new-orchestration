"""The creative rulebook, and the rules the Coach learns.

`creative-rules.md` holds the founder's rules — what he explained, again and
again, across three days of corrections. `learned-rules.md` holds the rules
the Coach (A13) derives from runs: a fault seen in a poster or clip, its
cause, and the rule that prevents it. Both are loaded on every run by the
Motion Director, the image agent and the judges.

Learned rules are text the agents read, never code: they can tighten what is
asked for and what is rejected, and the founder can edit or delete any line.
"""
from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path

KNOWLEDGE = Path(__file__).resolve().parents[1] / "brain" / "knowledge"
RULES = KNOWLEDGE / "creative-rules.md"
LEARNED = KNOWLEDGE / "learned-rules.md"
MAX_LEARNED = 40

_HEADER = (
    "# Learned creative rules\n\n"
    "Written by the Coach (A13) from what it saw in runs: each line is a fault, "
    "its cause and the rule that prevents it. Loaded on every run with "
    "`creative-rules.md`. Edit or delete any line; the Coach will not re-add a "
    "rule already here.\n\n"
)


def founder_rules() -> str:
    try:
        return RULES.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


def learned_rules() -> list[str]:
    try:
        return [l[2:].strip() for l in LEARNED.read_text(encoding="utf-8").splitlines()
                if l.startswith("- ")]
    except FileNotFoundError:
        return []


def block(*, max_chars: int = 5000) -> str:
    """Both rulebooks as prompt text: the founder's first, then the learned."""
    learned = learned_rules()
    text = founder_rules()
    if learned:
        text += "\n\n## Learned from past runs (Coach)\n" + "\n".join("- " + r for r in learned)
    return text[:max_chars]


def _key(rule: str) -> set[str]:
    return {w for w in re.findall(r"[a-z]{4,}", rule.lower())}


def add_learned(rule: str, *, source: str) -> bool:
    """Append a rule unless one very like it is already there."""
    rule = " ".join(str(rule).split()).strip(" -")
    if len(rule) < 20:
        return False
    k = _key(rule)
    for existing in learned_rules() + founder_rules().splitlines():
        e = _key(existing)
        if e and len(k & e) / max(1, len(k | e)) > 0.55:
            return False
    lines = learned_rules() + [rule + " (" + source + ", "
                               + datetime.now(timezone.utc).strftime("%Y-%m-%d") + ")"]
    LEARNED.write_text(_HEADER + "\n".join("- " + l for l in lines[-MAX_LEARNED:]) + "\n",
                       encoding="utf-8")
    return True
