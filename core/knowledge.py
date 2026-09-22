"""Vanna's own documentation as evidence — with the tier discipline enforced.

Until now the evidence store held competitor research and a few onchain
readings, so a claim about Vanna's own mechanism — the 1.1x health-factor
floor, per-account contract isolation, the rate model — could never be
verified, and the gate blocked almost everything. The facts were written down;
they were simply never loaded.

**The tiers are the whole point, and they are not decoration.**
`files/08-facts-ledger-and-claim-safety.md` defines six:

    A  Verified            state plainly
    B  Design/architecture state as how it works; qualify with "on testnet"
    C  Illustrative/demo   MUST be labelled an example — never a result
    D  Roadmap             future tense only, never present
    E  Internal only       NEVER appears in external content
    F  Unverified/stale    do not use until a human confirms

Only **A and B** become verifiable evidence. Loading C or D would let the
verifier entail a present-tense claim from a mock-up or a plan. Loading E would
put internal strategy into a public post — the one failure that cannot be taken
back. So this module reads all six and admits two.

Narrative documents (arcs, brand voice, positioning) are loaded separately as
`manual` evidence for *voice*, never as support for a factual claim: they say
how to say things, not what is true.
"""
from __future__ import annotations

import re
from pathlib import Path

from .contracts import Evidence
from .evidence import EvidenceStore

REPO = Path(__file__).resolve().parents[1]
FILES_DIR = REPO / "files"
OKF_DIR = REPO / "pipeline" / "system1_extracted" / "okf"
LEDGER = FILES_DIR / "08-facts-ledger-and-claim-safety.md"

# Tiers that may support a factual claim. The rest are read and deliberately
# not admitted; see the module docstring.
QUOTABLE_TIERS = ("A", "B")

_TIER_HEADING = re.compile(r"^###\s*Tier\s+([A-F])\b(.*)$", re.M)
_TABLE_ROW = re.compile(r"^\|\s*(?!Fact\b)(?!-)(.+?)\s*\|\s*(.+?)\s*\|\s*$", re.M)


def parse_ledger(text: str | None = None) -> dict[str, list[tuple[str, str]]]:
    """Return {tier letter: [(fact, source), ...]} from the facts ledger."""
    if text is None:
        if not LEDGER.exists():
            return {}
        text = LEDGER.read_text(encoding="utf-8")

    out: dict[str, list[tuple[str, str]]] = {}
    headings = list(_TIER_HEADING.finditer(text))
    for i, h in enumerate(headings):
        tier = h.group(1)
        start = h.end()
        end = headings[i + 1].start() if i + 1 < len(headings) else len(text)
        section = text[start:end]

        rows: list[tuple[str, str]] = []

        # Tier A and C are tables (| fact | source |); B, D, E and F are bullet
        # lists. Reading only one shape silently dropped whole tiers — including
        # every Tier B mechanism, which is most of what the product actually
        # does today.
        for m in _TABLE_ROW.finditer(section):
            fact = _clean(m.group(1))
            source = _clean(m.group(2))
            if not fact or set(fact) <= set("-| "):
                continue
            if fact.lower() in ("fact", "claim", "item", "content"):
                continue
            rows.append((fact, source))

        for line in section.splitlines():
            s = line.strip()
            if not s.startswith(("- ", "* ")):
                continue
            fact = _clean(s[2:])
            if len(fact) < 12:
                continue
            rows.append((fact, f"files/08 Tier {tier}"))

        if rows:
            out.setdefault(tier, []).extend(rows)
    return out


def _clean(s: str) -> str:
    s = re.sub(r"\*\*(.+?)\*\*", r"\1", s or "")      # bold
    s = re.sub(r"`(.+?)`", r"\1", s)                   # code spans
    s = re.sub(r"\[(.+?)\]\([^)]*\)", r"\1", s)        # links
    return re.sub(r"\s+", " ", s).strip()


def load_facts(store: EvidenceStore) -> dict[str, int]:
    """Load Tier A and B facts into the evidence store.

    Tier B snippets carry their qualifier inline, so a verifier checking
    "Vanna runs on Stellar Soroban" against a Tier B fact sees the testnet
    qualifier in the evidence text and can refuse an unqualified claim.
    """
    tiers = parse_ledger()
    counts = {"A": 0, "B": 0, "skipped": 0}

    for tier, rows in tiers.items():
        if tier not in QUOTABLE_TIERS:
            counts["skipped"] += len(rows)
            continue
        for fact, source in rows:
            if len(fact) < 12:
                continue
            snippet = fact if tier == "A" else f"{fact} (Tier B — design/architecture, on testnet)"
            store.record(
                snippet=f"Vanna: {snippet}",
                source_name=f"vanna-docs:tier-{tier.lower()}",
                kind="docs",
                source_url=f"file://files/08-facts-ledger-and-claim-safety.md#tier-{tier.lower()}",
                observed_at=_ledger_verified_at(),
            )
            counts[tier] += 1
    return counts


def _ledger_verified_at() -> str:
    """The ledger's own verification timestamp, not today's clock."""
    if LEDGER.exists():
        m = re.search(r"at:\s*'([0-9T:\-]+Z)'", LEDGER.read_text(encoding="utf-8"))
        if m:
            return m.group(1)
    return "2026-08-10T00:00:00Z"


# --------------------------------------------------------------------------
# Narrative documents — voice, not facts
# --------------------------------------------------------------------------

VOICE_DIRS = ("arcs", "brand", "channels", "positioning", "company", "rules")


def load_voice(store: EvidenceStore, max_chars: int = 1200) -> int:
    """Load narrative guidance as `manual` evidence.

    These are recorded so an agent can retrieve how Vanna talks about a subject.
    They are deliberately a different `kind` and a different source_name from
    the facts, so a claim cannot be 'verified' by a document that only describes
    tone.
    """
    if not OKF_DIR.exists():
        return 0
    n = 0
    for sub in VOICE_DIRS:
        d = OKF_DIR / sub
        if not d.exists():
            continue
        for f in sorted(d.glob("*.md")):
            body = _strip_frontmatter(f.read_text(encoding="utf-8"))
            body = re.sub(r"\s+", " ", body).strip()
            if len(body) < 120:
                continue
            store.record(
                snippet=body[:max_chars],
                source_name=f"vanna-voice:{sub}/{f.stem}",
                kind="manual",
                observed_at=_ledger_verified_at(),
            )
            n += 1
    return n


def _strip_frontmatter(text: str) -> str:
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            return text[end + 4:]
    return text


DOCS_STAMP = REPO / "state" / ".docs_refreshed"
DOCS_MAX_AGE_S = 86_400          # once a day


def refresh_docs_if_stale(store: EvidenceStore, max_age_s: int = DOCS_MAX_AGE_S) -> dict:
    """Pull docs.vanna.finance when the local copy is a day old.

    Refetching 24 pages on every run would add minutes and cost to each one for
    documentation that changes on a release cadence, so freshness is tracked by
    a stamp file. A failure here is returned, not raised: the run continues on
    the facts already in the store, and says the refresh was skipped.
    """
    import time

    try:
        age = time.time() - DOCS_STAMP.stat().st_mtime
        if age < max_age_s:
            return {"refreshed": False, "reason": f"last refresh {int(age / 3600)}h ago"}
    except FileNotFoundError:
        pass

    try:
        from .docs_source import ingest_docs
        result = ingest_docs(store)
        DOCS_STAMP.parent.mkdir(parents=True, exist_ok=True)
        DOCS_STAMP.write_text(str(time.time()), encoding="utf-8")
        return {"refreshed": True, **result}
    except Exception as exc:                       # noqa: BLE001 — boundary
        return {"refreshed": False, "reason": f"docs fetch failed: {exc}"[:200]}


def load_all(store: EvidenceStore | None = None, *, refresh_docs: bool = True) -> dict:
    store = store or EvidenceStore()
    before = len(store)
    facts = load_facts(store)
    voice = load_voice(store)
    docs = refresh_docs_if_stale(store) if refresh_docs else {"refreshed": False,
                                                             "reason": "disabled"}
    return {
        "live_docs": docs,
        "tier_a": facts.get("A", 0),
        "tier_b": facts.get("B", 0),
        "tiers_withheld": facts.get("skipped", 0),
        "voice_docs": voice,
        "evidence_before": before,
        "evidence_after": len(store),
    }


if __name__ == "__main__":
    import json

    print(json.dumps(load_all(), indent=2))
