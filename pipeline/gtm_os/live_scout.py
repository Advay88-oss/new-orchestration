"""Agent 01 — Intelligence Scout, live.

A01 used to read `opportunities.jsonl` and `posts.jsonl` out of the Brain DB and
stamp every signal `observed_at="2026-09-10T17:09:00Z"` — a fixed string in the
source. So the "Intelligence Scout & Parallel Stream Daemon" scanned nothing,
and every cycle for twelve days selected from the same frozen list while
reporting HIGH confidence on a date that never moved.

This module actually goes and looks: Google News, protocol docs and blogs,
Reddit RSS, Telegram web mirrors and the X bridge, in parallel, each with its
own timeout. Two rules:

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
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from typing import Any, Callable

from pipeline.gtm_orchestration.schemas import MarketSignal
from pipeline.gtm_os import agent_runtime as R

AGENT = "A01_intelligence_scout"
SOURCE_TIMEOUT_S = 45.0


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


def _signal_from_raw(raw: dict[str, Any]) -> MarketSignal | None:
    """Convert a collector row into a MarketSignal, or skip it."""
    headline = str(raw.get("headline") or raw.get("title") or "").strip()
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
                               or ["soroban", "stellar", "defi"]),
        observed_metric_change=str(raw.get("observed_metric_change") or "LIVE_SIGNAL"),
        source=src or "live-collector",
        source_root="live",
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

    c = SocialAndDocsCollector()
    sources: dict[str, Callable[[], list[dict]]] = {
        "google_news": lambda: c.collect_google_news_signals(limit=limit_per_source),
        "docs_blogs": lambda: c.collect_docs_and_blog_signals(),
        "reddit": lambda: c.collect_reddit_signals(limit=limit_per_source),
        "telegram": lambda: c.collect_telegram_signals(),
        "twitter": lambda: c.collect_twitter_signals(limit=2),
    }

    report: dict[str, Any] = {}
    signals: list[MarketSignal] = []
    seen: set[str] = set()

    with ThreadPoolExecutor(max_workers=len(sources)) as pool:
        futures = {pool.submit(fn): name for name, fn in sources.items()}
        for fut in as_completed(futures, timeout=SOURCE_TIMEOUT_S * 2):
            name = futures[fut]
            try:
                rows = fut.result(timeout=SOURCE_TIMEOUT_S) or []
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
                signals.append(sig)
                kept += 1
            report[name] = {"ok": True, "signals": kept}

    return signals, report


def scout(limit: int = 12, *, include_archive: bool = True) -> list[MarketSignal]:
    """A01's output: live signals first, archival ones behind them.

    The archival signals are kept because they carry whitespace analysis the
    live feeds do not, but they are re-stamped with `ARCHIVE_` source types so
    nothing downstream mistakes a fortnight-old record for today's news.
    """
    live, report = collect_live()

    ok_sources = [k for k, v in report.items() if v.get("ok") and v.get("signals")]
    failed = {k: v.get("error", "no signals") for k, v in report.items()
              if not v.get("ok") or not v.get("signals")}

    detail = ("live: " + str(len(live)) + " signals from "
              + (", ".join(sorted(ok_sources)) or "no source"))
    if failed:
        detail += " | quiet/failed: " + ", ".join(sorted(failed))

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
    return out[:limit]


if __name__ == "__main__":
    import json

    sigs, rep = collect_live()
    print(json.dumps(rep, indent=2))
    for s in sigs[:12]:
        print(" -", s.source_type, "|", s.headline[:100])
