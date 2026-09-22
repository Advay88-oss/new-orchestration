"""Evidence store with provenance.

The audit found `pipeline/state/scraped_social_posts.jsonl` was not scraped at
all — it was a hand-written `SEED_POSTS` list with invented engagement counts and
profile URLs posing as post URLs, written to a file whose name asserted it was
observed data. Downstream agents read fiction labelled as observation.

Here, evidence can only enter through `record()`, which requires a locator and a
timestamp, and every piece keeps the snippet it was derived from so a claim can
be re-checked against the exact text that supported it.
"""
from __future__ import annotations

import hashlib
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Iterator

from .contracts import Evidence

REPO = Path(__file__).resolve().parents[1]
STORE_PATH = Path(os.environ.get("VANNA_EVIDENCE", REPO / "state" / "evidence.jsonl"))


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def evidence_id(source_name: str, snippet: str) -> str:
    h = hashlib.sha256(f"{source_name}|{snippet}".encode("utf-8")).hexdigest()[:12]
    return f"EV-{h}"


class EvidenceStore:
    """Append-only. Re-recording identical evidence is a no-op, not a duplicate —
    the old performance ledger had one test record repeated 44 times and counted
    all 44 as independent observations."""

    def __init__(self, path: Path | None = None) -> None:
        self.path = path or STORE_PATH
        self._cache: dict[str, Evidence] | None = None

    def _load(self) -> dict[str, Evidence]:
        if self._cache is not None:
            return self._cache
        items: dict[str, Evidence] = {}
        if self.path.exists():
            with self.path.open(encoding="utf-8") as fh:
                for line in fh:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        ev = Evidence(**json.loads(line))
                        items[ev.id] = ev
                    except Exception:
                        continue          # a bad row is skipped, never guessed at
        self._cache = items
        return items

    def record(self, *, snippet: str, source_name: str, kind: str,
               source_url: str | None = None, observed_at: str | None = None) -> Evidence:
        snippet = snippet.strip()
        if not snippet:
            raise ValueError("evidence requires a non-empty snippet")
        ev = Evidence(
            id=evidence_id(source_name, snippet),
            snippet=snippet[:2000],
            source_url=source_url,
            source_name=source_name,
            observed_at=observed_at or now_iso(),
            kind=kind,  # type: ignore[arg-type]
        )
        store = self._load()
        if ev.id in store:
            return store[ev.id]
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(ev.model_dump(), ensure_ascii=False) + "\n")
            fh.flush()
            os.fsync(fh.fileno())
        store[ev.id] = ev
        return ev

    def get(self, ev_id: str) -> Evidence | None:
        return self._load().get(ev_id)

    def all(self) -> list[Evidence]:
        return list(self._load().values())

    def __len__(self) -> int:
        return len(self._load())

    def search(self, query: str, limit: int = 8) -> list[Evidence]:
        """Lexical overlap retrieval.

        Deliberately simple and deliberately *not* a similarity threshold that
        quietly returns something for every query: a query with no token overlap
        returns nothing, so the verifier sees 'no evidence' rather than a weak
        match it might rationalise into support.
        """
        terms = {t for t in _tokens(query) if len(t) > 2}
        if not terms:
            return []
        scored: list[tuple[float, Evidence]] = []
        for ev in self._load().values():
            ev_terms = set(_tokens(ev.snippet + " " + ev.source_name))
            overlap = terms & ev_terms
            if not overlap:
                continue
            # favour rarer, longer tokens and numeric agreement
            score = sum(1.5 if any(ch.isdigit() for ch in t) else 1.0 for t in overlap)
            scored.append((score / len(terms), ev))
        scored.sort(key=lambda p: p[0], reverse=True)
        return [ev for _, ev in scored[:limit]]

    def fresh(self, max_age_days: float) -> list[Evidence]:
        cutoff = time.time() - max_age_days * 86400
        out = []
        for ev in self._load().values():
            try:
                ts = datetime.fromisoformat(ev.observed_at).timestamp()
            except Exception:
                continue
            if ts >= cutoff:
                out.append(ev)
        return out


def _tokens(text: str) -> Iterator[str]:
    cur = []
    for ch in text.lower():
        if ch.isalnum() or ch == ".":
            cur.append(ch)
        elif cur:
            yield "".join(cur)
            cur = []
    if cur:
        yield "".join(cur)


def ingest_signals(store: EvidenceStore, signals: Iterable) -> list[Evidence]:
    """Turn ingested signals into evidence, preserving their locators.

    The kind is derived from where the signal came from, not assumed. An onchain
    reading is located by source + timestamp and has no URL; calling it
    `scraped` would either fail validation or, worse, imply a web source that
    does not exist.
    """
    out = []
    for s in signals:
        text = f"{s.title}. {s.summary}".strip()
        if not text or text == ".":
            continue
        if s.source_name.startswith("onchain:"):
            kind = "onchain"
        elif s.source_url:
            kind = "scraped"
        else:
            kind = "manual"
        out.append(store.record(
            snippet=text, source_name=s.source_name, kind=kind,
            source_url=s.source_url, observed_at=s.observed_at,
        ))
    return out
