"""docs.vanna.finance as the live knowledge source.

The facts ledger in `files/08` cites "Live docs" as the source for almost every
Tier A fact. This module goes and gets them, so the evidence store holds what
the documentation says *today* rather than what was true when someone last
transcribed it.

The site publishes an `llms.txt` index and serves every page as markdown, so no
HTML scraping or heuristics are involved: the index is authoritative and each
page arrives as prose.

Two source rules are inherited from the knowledge pack and enforced here:

  * `docs.vanna.finance` is authoritative. Claims may be verified against it.
  * `vanna.finance` — the marketing site — is NOT a valid claim source. The
    pack says so explicitly ("it is a vision site"), and this module will not
    fetch from it.

Claims are extracted by `core.research`, the same LLM extractor used for
competitors, so a documentation claim carries the same provenance as any other:
a subject, a verbatim supporting quote, and the URL it came from.
"""
from __future__ import annotations

import re
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from typing import Iterable

from .evidence import EvidenceStore
from .research import extract_claims

INDEX_URL = "https://docs.vanna.finance/llms.txt"
DOCS_HOST = "docs.vanna.finance"
FORBIDDEN_HOSTS = ("vanna.finance",)          # bare marketing host — see docstring

USER_AGENT = "vanna-gtm-pipeline/1.0 (+internal research)"
TIMEOUT_S = 30.0

# Pages whose content is mechanism rather than UI walkthrough. These are where
# the checkable facts live; the "click here to connect your wallet" guides carry
# almost none and mostly add retrieval noise.
FACTUAL_PREFIXES = (
    "/learn/",
    "/developers/contracts/",
    "/developers/architecture",
    "/developers/math-reference",
    "/developers/deployed-contracts",
    "/guides/margin/health-factor",
    "/guides/margin/liquidation",
    "/guides/how-vanna-works",
)

_MD_LINK = re.compile(r"https://docs\.vanna\.finance/[A-Za-z0-9/_\-.]+\.md")


class DocsError(RuntimeError):
    pass


def _get(url: str) -> str:
    # `urllib.request` has no urlparse; the guard silently passed every URL.
    host = urllib.parse.urlparse(url).netloc.lower()
    if host in FORBIDDEN_HOSTS:
        raise DocsError(
            f"{host} is not a valid claim source — the knowledge pack marks the "
            f"marketing site a vision site. Use {DOCS_HOST}.")
    if host != DOCS_HOST:
        raise DocsError(f"refusing to fetch {host}; this module reads {DOCS_HOST} only")
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT_S) as r:
            return r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as exc:
        raise DocsError(f"HTTP {exc.code} for {url}") from exc
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise DocsError(f"transport error for {url}: {exc}") from exc


def list_pages() -> list[str]:
    """Every documentation page URL, from the site's own index."""
    body = _get(INDEX_URL)
    seen: list[str] = []
    for m in _MD_LINK.finditer(body):
        u = m.group(0)
        if u not in seen:
            seen.append(u)
    if not seen:
        raise DocsError(f"{INDEX_URL} listed no .md pages")
    return seen


def factual_pages(pages: Iterable[str] | None = None) -> list[str]:
    pages = list(pages or list_pages())
    out = [p for p in pages
           if any(p.replace(f"https://{DOCS_HOST}", "").startswith(pref)
                  for pref in FACTUAL_PREFIXES)]
    return out or pages


_LEAD = re.compile(r"^>\s*##\s*Documentation Index.*?(?=^#)", re.S | re.M)


def fetch_page(url: str) -> tuple[str, str]:
    """Return (title, prose) for one documentation page."""
    body = _get(url)
    # Every page is prefixed with the same index banner; it is navigation, and
    # leaving it in would have the extractor see the same block on every page.
    body = _LEAD.sub("", body)
    m = re.search(r"^#\s+(.+)$", body, re.M)
    title = m.group(1).strip() if m else url.rsplit("/", 1)[-1]
    return title, body


def ingest_docs(
    store: EvidenceStore | None = None,
    *,
    pages: Iterable[str] | None = None,
    max_pages: int = 24,
    workers: int = 4,
) -> dict:
    """Fetch documentation pages and load their claims as evidence."""
    store = store or EvidenceStore()
    before = len(store)
    targets = factual_pages(pages)[:max_pages]
    observed = datetime.now(timezone.utc).isoformat()

    def one(url: str) -> tuple[str, list[dict] | None, str | None]:
        try:
            title, prose = fetch_page(url)
        except DocsError as exc:
            return url, None, str(exc)
        try:
            claims = extract_claims(
                entity_id="Vanna",
                url=url,
                page_title=title,
                content=prose,
                observed_at=observed,
                source_type="official_docs",
                confidence=0.95,        # the pack names live docs authoritative
            )
        except Exception as exc:        # noqa: BLE001 — boundary
            return url, None, f"extraction failed: {exc}"
        return url, claims, None

    results: list[tuple[str, list[dict] | None, str | None]] = []
    with ThreadPoolExecutor(max_workers=workers) as pool:
        results = list(pool.map(one, targets))

    recorded = 0
    failures: list[str] = []
    for url, claims, err in results:
        if err or claims is None:
            failures.append(f"{url}: {err}")
            continue
        for c in claims:
            store.record(
                snippet=f"Vanna docs: {c['claim']}",
                source_name="vanna-docs:live",
                kind="docs",
                source_url=c["source_url"],
                observed_at=c["observed_at"],
            )
            recorded += 1

    return {
        "pages_listed": len(list(pages or [])) or None,
        "pages_fetched": len(targets) - len(failures),
        "pages_failed": len(failures),
        "claims_recorded": recorded,
        "evidence_before": before,
        "evidence_after": len(store),
        "failures": failures[:5],
    }


if __name__ == "__main__":
    import json

    print(json.dumps(ingest_docs(), indent=2))
