"""Agent 01 — Intelligence Scout, live.

A01 used to read `opportunities.jsonl` and `posts.jsonl` out of the Brain DB and
stamp every signal `observed_at="2026-09-10T17:09:00Z"` — a fixed string in the
source. So the "Intelligence Scout & Parallel Stream Daemon" scanned nothing,
and every cycle for twelve days selected from the same frozen list while
reporting HIGH confidence on a date that never moved.

This module actually goes and looks: crypto news feeds, Google News, GDELT,
protocol docs and blogs, Reddit, Telegram channels and DefiLlama, in
parallel, each with its own timeout. Every source is a free public feed or
API, so the scrape runs anywhere — no browser bridge. Two rules:

  * **A source that fails contributes nothing.** It does not contribute a
    plausible-looking cached signal. The collector's Reddit fallback used to
    invent a post with a fabricated loss figure and hand it over as observed.

  * **Live and archival signals are labelled differently.** Brain DB signals
    are still useful — they carry the whitespace analysis — but they are marked
    `ARCHIVE` with their real age, so the selector can tell a thing that
    happened today from a thing recorded a fortnight ago.
"""
from __future__ import annotations

import hashlib
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from typing import Any, Callable

from pipeline.gtm_orchestration.schemas import MarketSignal
from pipeline.gtm_os import agent_runtime as R

AGENT = "A01_intelligence_scout"
SOURCE_TIMEOUT_S = 45.0

# Which news query produced each Google News signal, for this process's last
# scrape. The query is an arm A01 learns on (`gtm_learning.source_learning`)
# and the signal id does not carry it.
QUERY_OF: dict[str, str] = {}


LIVE_TYPES = {
    "PRIMARY_NEWS_OBSERVED", "REDDIT_COMMUNITY_OBSERVED", "DOCS_BLOG_OBSERVED",
    "TELEGRAM_ANNOUNCEMENT_OBSERVED", "X_POST_OBSERVED", "LIVE_OBSERVED",
}


def _source_type(value) -> str:
    """Keep a declared live type; anything else becomes the generic one."""
    v = str(value or "").upper()
    return v if v in LIVE_TYPES else "LIVE_OBSERVED"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


_SOURCE_TAG = re.compile(r"^\s*\[[^\]]{2,60}\]\s*")


def _clean_headline(text: str) -> str:
    """Drop the collector's provenance prefix.

    Collectors prepend "[Market News] ", "[Reddit r/Stellar] ", "[Blend
    Protocol Docs] " so a human scanning the list can see where a signal came
    from. It is a label, not part of the headline — and it flowed straight
    through A02 and A03 into the published hook, which shipped as "The hidden
    math behind [Blend Protocol Docs] Blend v2 pool architecture...". The
    source is already carried in `source_type` and `source`.
    """
    cleaned = _SOURCE_TAG.sub("", str(text or "")).strip()
    # Google News appends the publisher: "... and how positions die - Crypto
    # News". That suffix rode through A02 and A03 into the hook, which
    # shipped as "The hidden math behind DeFi Lending Is Modularizing: ... -
    # Tiger Research Reports." The publisher is already in `source`.
    # Publishers appear as a proper name ("Blockworks", "Tiger Research
    # Reports") or as a bare domain ("visa.com"), so both shapes are matched.
    cleaned = re.sub(r"\s+[-–—]\s+([A-Z][\w.&' ]{2,40}|[\w-]+\.(com|io|org|xyz|net|co))$",
                     "", cleaned).strip()
    return cleaned


# Protocols and firms worth recognising by name in a headline — the tenant's
# `known_entities`, from its brand profile. Matched case-insensitively on
# word boundaries so "Aave" does not fire on "have".
def _known() -> list[str]:
    from pipeline.brand_brain import context as C
    return list(C.profile().get("known_entities") or [])


def _entities(raw: dict[str, Any], headline: str) -> list[str]:
    """Which companies and protocols a signal is actually about.

    Every live signal used to be stamped `["soroban", "stellar", "defi"]` —
    the same three strings regardless of content — so the field could not
    answer "whose news is this", which is exactly what the Scraped
    Intelligence view needs. Collectors that already know the answer (the
    DefiLlama protocol, the X handle, the feed name) are believed; otherwise
    the headline is matched against known names.
    """
    data = raw.get("data") or {}
    named: list[str] = []
    for key in ("protocol", "handle", "entity", "name", "source_name"):
        v = data.get(key) or raw.get(key)
        if v:
            named.append(str(v))

    low = str(headline).lower()
    for k in _known():
        if re.search(r"\b" + re.escape(k.lower()) + r"\b", low):
            named.append(k)

    # Preserve order, drop duplicates case-insensitively.
    out, seen = [], set()
    for n in named:
        if n.lower() not in seen:
            seen.add(n.lower())
            out.append(n)
    return out[:6] or ["(unattributed)"]


_PUBLISHER = re.compile(
    r"\s+[-–—]\s+([A-Z][\w.&' ]{2,40}|[\w-]+\.(?:com|io|org|xyz|net|co))$")


def _publisher(text: str) -> str:
    """The outlet named at the end of a news headline, if there is one.

    Google News links are `news.google.com` redirects, so the domain says
    nothing about who published the story — but the headline ends with the
    outlet's name. Capturing it before it is stripped is the only place that
    information survives.
    """
    m = _PUBLISHER.search(_SOURCE_TAG.sub("", str(text or "")).strip())
    return m.group(1).strip() if m else ""


def _signal_from_raw(raw: dict[str, Any]) -> MarketSignal | None:
    """Convert a collector row into a MarketSignal, or skip it."""
    original = raw.get("headline") or raw.get("title") or ""
    headline = _clean_headline(original)
    publisher = _publisher(original)
    if len(headline) < 12:
        return None

    ts = str(raw.get("timestamp") or _now())
    sid = str(raw.get("signal_id")
              or "SIG-LIVE-" + hashlib.md5(headline.encode()).hexdigest()[:10])
    src = str(raw.get("source") or "")
    data = raw.get("data") or {}
    desc = str(data.get("insight") or data.get("summary") or data.get("title")
               or raw.get("description") or headline)

    return MarketSignal(
        signal_id=sid,
        headline=headline[:300],
        description=desc[:900],
        market_category=str(raw.get("market_category") or "LENDING"),
        entities_involved=list(raw.get("entities_involved")
                               or _entities(raw, headline)),
        observed_metric_change=str(raw.get("observed_metric_change") or "LIVE_SIGNAL"),
        source=src or "live-collector",
        # The outlet, not the literal string "live". The Scraped Intelligence
        # view groups and labels by this, so a hardcoded value made every row
        # read "live ↗" with no indication of who said it. The headline's
        # own suffix is preferred over the domain, because Google News links
        # are redirects that all resolve to news.google.com.
        source_root=publisher or _domain(src) or "live",
        dataset=str(raw.get("derivation_provenance") or "live"),
        source_type=_source_type(raw.get("source_type")),
        record_id=sid,
        observed_at=ts,
        data_as_of=ts[:10],
        confidence=str(raw.get("confidence") or "MEDIUM"),
        evidence_status="OBSERVED",
    )


def collect_live(limit_per_source: int = 5) -> tuple[list[MarketSignal], dict[str, Any]]:
    """Run every live source in parallel. Returns (signals, per-source report)."""
    from pipeline.intelligence_stream.social_and_docs_collector import SocialAndDocsCollector

    from pipeline.intelligence_stream import source_config

    c = SocialAndDocsCollector()

    # A rotating slice of the query list, not one fixed string. The single
    # hardcoded query ("stellar soroban defi") returned near-identical
    # headlines every cycle and was the largest single cause of the engine
    # re-selecting the same topic 32 runs out of 41.
    #
    # Which slice is learned: three queries by their record (A02's grades of
    # what each one brought back, and the founder's decisions), one always at
    # random so a query with a poor record still gets looked at.
    try:
        from pipeline.gtm_learning.source_learning import pick_queries
        queries = pick_queries(list(source_config.load().get("news_queries") or []), 4)
    except Exception:                               # noqa: BLE001 — boundary
        queries = []
    queries = queries or source_config.news_queries(4)
    QUERY_OF.clear()

    def _news() -> list[dict]:
        out: list[dict] = []
        for q in queries:
            try:
                for row in c.collect_google_news_signals(
                        query=q, limit=max(2, limit_per_source // 2)) or []:
                    if isinstance(row, dict):
                        row["_query"] = q
                    out.append(row)
            except Exception:                       # noqa: BLE001 — boundary
                continue
        return out

    sources: dict[str, Callable[[], list[dict]]] = {
        "google_news": _news,
        "docs_blogs": lambda: c.collect_docs_and_blog_signals(),
        "reddit": lambda: c.collect_reddit_signals(limit=limit_per_source),
        "telegram": lambda: c.collect_telegram_signals(),
        "news_feeds": lambda: c.collect_news_feed_signals(),
        "twitter": lambda: c.collect_x_signals(),
        "gdelt": lambda: c.collect_gdelt_signals(queries),
        # Measured rather than editorial: TVL moves every day, so this source
        # produces genuinely new signals even in a week when nobody publishes.
        "defillama": lambda: c.collect_defillama_signals(),
        "defillama_hacks": lambda: c.collect_defillama_hacks(),
    }

    report: dict[str, Any] = {}
    signals: list[MarketSignal] = []
    seen: set[str] = set()

    # Not a `with` block: its exit joins every worker, so one hung source held
    # the whole scrape past the deadline the deadline was there to enforce.
    pool = ThreadPoolExecutor(max_workers=len(sources))
    futures = {pool.submit(fn): name for name, fn in sources.items()}
    try:
        for fut in as_completed(futures, timeout=SOURCE_TIMEOUT_S * 2):
            name = futures[fut]
            try:
                rows = fut.result() or []
            except Exception as exc:                # noqa: BLE001 — boundary
                report[name] = {"ok": False,
                                "error": (type(exc).__name__ + ": " + str(exc))[:200],
                                "signals": 0}
                continue

            kept = 0
            for raw in rows:
                sig = _signal_from_raw(raw if isinstance(raw, dict) else {})
                if sig is None:
                    continue
                key = sig.headline.lower()[:90]
                if key in seen:
                    continue
                seen.add(key)
                if isinstance(raw, dict) and raw.get("_query"):
                    QUERY_OF[sig.signal_id] = raw["_query"]
                signals.append(sig)
                kept += 1
            report[name] = {"ok": True, "signals": kept}
    except TimeoutError:
        # as_completed raises out of the loop, not per future. Uncaught, one
        # slow source failed A01 outright and discarded what the other five
        # had already returned. The slow one fails alone, like any other.
        for fut, name in futures.items():
            if name not in report:
                report[name] = {"ok": False,
                                "error": "timed out after %.0fs" % (SOURCE_TIMEOUT_S * 2),
                                "signals": 0}
    finally:
        pool.shutdown(wait=False, cancel_futures=True)

    return signals, report


def scout(limit: int = 12, *, include_archive: bool = True) -> list[MarketSignal]:
    """A01's output: live signals first, archival ones behind them.

    The archival signals are kept because they carry whitespace analysis the
    live feeds do not, but they are re-stamped with `ARCHIVE_` source types so
    nothing downstream mistakes a fortnight-old record for today's news.
    """
    # One stamp for the whole scrape, so every row in the harvest agrees on
    # when it was pulled.
    scraped_at = datetime.now(timezone.utc).isoformat()
    live, report = collect_live()

    ok_sources = [k for k, v in report.items() if v.get("ok") and v.get("signals")]
    failed = {k: v.get("error", "no signals") for k, v in report.items()
              if not v.get("ok") or not v.get("signals")}

    detail = ("live: " + str(len(live)) + " signals from "
              + (", ".join(sorted(ok_sources)) or "no source"))
    if failed:
        detail += " | quiet/failed: " + ", ".join(sorted(failed))
    try:
        from pipeline.gtm_learning.source_learning import record_text
        detail += " | " + record_text(3)
    except Exception:                               # noqa: BLE001 — boundary
        pass

    out = list(live)

    if include_archive:
        try:
            from pipeline.gtm_orchestration.intelligence_provider import IntelligenceProvider
            archive = IntelligenceProvider().get_market_signals(limit=limit)
            for s in archive:
                key = s.headline.lower()[:90]
                if any(key == x.headline.lower()[:90] for x in out):
                    continue
                out.append(s.model_copy(update={
                    "source_type": "ARCHIVE",
                    "dataset": str(s.source_type),
                    "confidence": "MEDIUM",
                }))
        except Exception as exc:                    # noqa: BLE001 — boundary
            detail += " | archive unavailable: " + str(exc)[:120]

    status = "ok" if live else ("degraded" if out else "failed")
    if not live:
        detail = "NO LIVE SIGNALS — " + detail
    R.record_stage(AGENT, status, detail,
                   outputs=[s.signal_id for s in out[:10]])

    _write_harvest(out, report, scraped_at)
    # The full harvest is recorded above; what goes forward to A02 is ranked,
    # so the strongest candidates are the ones it actually sees. The ranking
    # is learned — the keyword score plus each source's record — with ~30% of
    # the slots reserved outside it, so no source can be learned out of view.
    try:
        from pipeline.gtm_learning.source_learning import forward, record_text
        chosen = forward(out, limit, _relevance, QUERY_OF)
        R.record_decision(AGENT, "source_learning", {
            "record": record_text(), "queries": sorted(set(QUERY_OF.values())),
            "forwarded": [s.signal_id for s in chosen]})
        return chosen
    except Exception:                               # noqa: BLE001 — boundary
        return rank_for_relevance(out)[:limit]


# The tenant's domain. A signal touching these is one it can say something
# architectural about; a signal touching none of them is not.
def _relevant() -> list[str]:
    """The tenant's domain terms (its profile's `relevance_terms`)."""
    from pipeline.brand_brain import context as C
    return C.relevance_terms()

# SEO listicles and buyer-guide content. These rank well in news search and
# are worthless to a B2B infrastructure protocol: A03 declined three in a row
# ("Best Perp DEX 2026", "Best Decentralized Crypto Exchanges") and the cycle
# produced nothing. Penalised rather than dropped, so a listicle can still
# surface on a quiet day if nothing better exists.
_LISTICLE = (
    "best ", "top 10", "top 5", "complete comparison", "comparison of",
    "ultimate guide", "buyer", "review 2026", "ranked", " vs ", "cheapest",
    "how to buy", "price prediction", "bulls eye", "price target",
)


def rank_for_relevance(signals: list[MarketSignal]) -> list[MarketSignal]:
    """Order signals by how much Vanna can actually say about them.

    A01 is deterministic by design, so this is scoring, not judgement — A02
    still chooses, and still sees a mixed list. It only changes which
    candidates reach it first.
    """
    return sorted(signals, key=_relevance, reverse=True)


def _relevance(s: MarketSignal) -> float:
    text = (str(s.headline) + " " + str(getattr(s, "description", ""))).lower()
    hits = sum(1 for k in _relevant() if k in text)
    penalty = sum(3 for k in _LISTICLE if k in text)
    # A measured on-chain move beats an opinion piece about the same topic.
    measured = 2 if str(s.source_type) == "PRIMARY_ONCHAIN_OBSERVED" else 0
    archive = -4 if str(s.source_type).startswith("ARCHIVE") else 0
    return hits + measured + archive - penalty


def _write_harvest(signals: list[MarketSignal], report: dict, scraped_at: str) -> None:
    """The full record of what this scrape brought back, and from where.

    The run summary keeps only a headline, a type and a date for each
    candidate, so everything that answers "where did this come from, whose
    news is it, and when did we pull it" was thrown away the moment A02 chose
    a winner. That is exactly what the Scraped Intelligence view needs to
    show. Written per run, next to the journal.

    Never raises: a missing harvest file must not fail a cycle.
    """
    import json

    rid = R.current_run()
    if not rid:
        return
    try:
        rows = []
        for s in signals:
            rows.append({
                "signal_id": s.signal_id,
                "headline": s.headline,
                "source_type": str(s.source_type),
                "source": getattr(s, "source", "") or "",
                # The publisher/domain, so the view can group by who said it.
                "source_root": getattr(s, "source_root", None)
                               or _domain(getattr(s, "source", "") or ""),
                # The companies and protocols named in the signal.
                "entities": list(getattr(s, "entities_involved", []) or []),
                "market_category": getattr(s, "market_category", None),
                "metric_change": getattr(s, "observed_metric_change", None),
                "confidence": str(getattr(s, "confidence", "")),
                # When the event happened vs when we pulled it — different
                # things, and the view shows both.
                "observed_at": str(getattr(s, "observed_at", "")),
                "scraped_at": scraped_at,
                # The news query that found it — an arm A01 learns on.
                "query": QUERY_OF.get(s.signal_id),
            })

        d = R.RUNS_DIR / rid
        d.mkdir(parents=True, exist_ok=True)
        (d / "harvest.json").write_text(json.dumps({
            "run_id": rid,
            "scraped_at": scraped_at,
            "sources": report,
            "total_signals": len(rows),
            "signals": rows,
        }, indent=2, default=str), encoding="utf-8")
    except Exception:                               # noqa: BLE001 — boundary
        pass


def _domain(url: str) -> str:
    m = re.match(r"https?://([^/]+)", str(url or ""))
    return (m.group(1).replace("www.", "") if m else "")


if __name__ == "__main__":
    import json

    sigs, rep = collect_live()
    print(json.dumps(rep, indent=2))
    for s in sigs[:12]:
        print(" -", s.source_type, "|", s.headline[:100])
