"""Which product page the automatic clock posts about next.

Scraped headlines were changing, and the strategist still wrote Blend and
Aquarius, because that is the profile's first argument. The GitHub pages
already in the brain name other mechanisms. The clock takes the page that
has not been the subject lately and makes that the post.

A founder directive is left alone. This only applies when the clock chooses.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

STATE = Path(__file__).resolve().parents[1] / "state" / "recent_subjects.json"

# Order is the rotation. The first unused page is the next post.
# Wording stays inside what those GitHub pages state.
SUBJECTS: list[dict[str, Any]] = [
    {
        "id": "solana-margin",
        "text": (
            "A trader on Solana lends a stock token such as TSLAx, or a PreStock "
            "such as OPENAI, then borrows from one margin account to go long or "
            "short up to 5× through a Jupiter swap, with no funding rate. Say it "
            "is on the Solana devnet fork. One idea. Do not mention Stellar, "
            "Blend, Aquarius, SmartAccount, 10×, 1.10×, or XLM."
        ),
    },
    {
        "id": "solana-earn",
        "text": (
            "Supplying a stock token such as TSLAx on Solana earns the live "
            "borrow rate, while the same mint sitting in Kamino's xStocks market "
            "does not. Use only that sentence from the Solana earn page. Do not "
            "add an APY number. One idea. Do not mention Stellar, Blend, "
            "Aquarius, SmartAccount, or 10×."
        ),
    },
    {
        "id": "stellar-how",
        "text": (
            "Stellar testnet only. Explain the two connected sides from the "
            "how-vanna-works page: who supplies liquidity, and who borrows. Use "
            "only a mechanism that page states. One idea. Do not make Blend and "
            "Aquarius the subject. Do not mention Solana, xStocks, Jupiter, or 5×."
        ),
    },
    {
        "id": "stellar-floor",
        "text": (
            "Stellar testnet only. Each borrower has an isolated SmartAccount, "
            "and the liquidation floor is 1.10×. One idea. Do not make Blend and "
            "Aquarius the diagram. Do not mention Solana, xStocks, Jupiter, or 5×."
        ),
    },
]


def _load() -> list[dict[str, Any]]:
    try:
        data = json.loads(STATE.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except Exception:                               # noqa: BLE001 — first run
        return []


def next_subject() -> dict[str, Any]:
    """The product page that has gone longest without a post."""
    used = [str(r.get("id")) for r in _load()]
    for subject in SUBJECTS:
        if subject["id"] not in used[: len(SUBJECTS) - 1]:
            return subject
    return SUBJECTS[0]


def others(current_id: str) -> list[dict[str, Any]]:
    """The remaining pages, if the first one is declined."""
    return [s for s in SUBJECTS if s["id"] != current_id]


def remember(subject_id: str, run_id: Optional[str] = None) -> None:
    try:
        rows = [r for r in _load() if r.get("id") != subject_id]
        rows.insert(0, {"id": subject_id, "run_id": run_id})
        STATE.parent.mkdir(parents=True, exist_ok=True)
        STATE.write_text(json.dumps(rows[:12], indent=2), encoding="utf-8")
    except Exception:                               # noqa: BLE001 — must not fail a run
        pass
