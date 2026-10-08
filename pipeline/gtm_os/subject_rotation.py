"""Which product page the automatic clock posts about next.

Scraped headlines were changing, and the strategist still wrote Blend and
Aquarius, because that is the profile's first argument. The GitHub pages
already in the brain name other mechanisms. The clock takes the page that
has not been the subject lately and makes that the post.

A founder directive is left alone. This only applies when the clock chooses.
"""
from __future__ import annotations

import json
import re
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


# Docs pages in the brain that explain the product (public guides and
# learn pages). Snippets, the home page and repo tooling are not subjects.
_DOC_PAGE = re.compile(r"((?:Vanna_docs|Solana_Docs)/(?:guides|learn)/[A-Za-z0-9_/.-]+\.mdx?)")


def doc_subjects(tenant: Optional[str] = None, limit: int = 200) -> list[dict[str, Any]]:
    """One subject per public docs page in the brain, with what that page says.
    Code files and commit messages are not subjects: the facts ledger keeps
    private repos and contract source out of posts."""
    try:
        from pipeline.brand_brain.client import Brain
        brain = Brain(tenant) if tenant else Brain()
        with brain._db() as con:
            rows = con.execute("SELECT section, title, url, text FROM chunks WHERE source = 'github' "
                               "AND (deleted IS NULL OR deleted = 0)").fetchall()
    except Exception:                               # noqa: BLE001 — the fixed pages still rotate
        return []
    pages: dict[str, list[str]] = {}
    for r in rows:
        r = dict(r)
        hay = " ".join(str(r.get(k) or "") for k in ("section", "title", "url"))
        m = _DOC_PAGE.search(hay)
        if m:
            pages.setdefault(m.group(1), []).append(" ".join(str(r.get("text") or "").split()))
    out = []
    for path, texts in sorted(pages.items())[:limit]:
        solana = path.startswith("Solana_Docs")
        name = path.rsplit("/", 1)[-1].rsplit(".", 1)[0].replace("-", " ")
        excerpt = " ".join(texts)[:1400]
        out.append({
            "id": "doc:" + path,
            "text": ("The subject is the docs page '" + name + "' (" + path + "). Explain the one thing this "
                     "page lets a user do or understand, using only what it says: " + excerpt + " "
                     + ("Solana devnet fork only; do not mention Stellar, Blend, Aquarius or 1.10x."
                        if solana else
                        "Stellar testnet only. Do not make Blend, Aquarius, SmartAccount isolation or the "
                        "1.10x floor the subject unless this page is about them.")),
        })
    return out


def pool(tenant: Optional[str] = None) -> list[dict[str, Any]]:
    """The fixed product pages, then every docs page."""
    return SUBJECTS + doc_subjects(tenant)


def next_subject() -> dict[str, Any]:
    """The page that has gone longest without a post (never used ones first)."""
    subjects = pool()
    used = [str(r.get("id")) for r in _load()]
    fresh = [s for s in subjects if s["id"] not in used]
    if fresh:
        # Not always the first: a page from a different area than the last post.
        last = used[0].split("/")[1] if used and "/" in used[0] else ""
        other = [s for s in fresh if ("/" not in s["id"]) or s["id"].split("/")[1] != last]
        return (other or fresh)[0]
    for sid in reversed(used):
        hit = next((s for s in subjects if s["id"] == sid), None)
        if hit:
            return hit
    return SUBJECTS[0]


def others(current_id: str) -> list[dict[str, Any]]:
    """The remaining pages, if the first one is declined."""
    used = {str(r.get("id")) for r in _load()}
    rest = [s for s in pool() if s["id"] != current_id]
    return [s for s in rest if s["id"] not in used] + [s for s in rest if s["id"] in used]


def remember(subject_id: str, run_id: Optional[str] = None) -> None:
    try:
        rows = [r for r in _load() if r.get("id") != subject_id]
        rows.insert(0, {"id": subject_id, "run_id": run_id})
        STATE.parent.mkdir(parents=True, exist_ok=True)
        STATE.write_text(json.dumps(rows[:80], indent=2), encoding="utf-8")
    except Exception:                               # noqa: BLE001 — must not fail a run
        pass
