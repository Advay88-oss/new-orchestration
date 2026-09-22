"""Competitor claim extraction.

Replaces three regex rules that produced roughly nine junk rows for every
usable one:

  TITLE        `"{page_title} — official title on {domain}"` — page metadata
               dressed as a claim. Always noise.
  METRIC       a regex for `\\d+(M|B|K|x|%|...)` run over *raw* page text, so it
               matched inside image URLs (`hero@1x` -> "1x",
               `evcop6xwrqrpqrf9` -> "6x"). When its "enclosing sentence"
               pattern failed it emitted `"Metric observed: $12B"` — a figure
               with no subject, which no verifier can check against anything.
  INTEGRATION  keyword presence anywhere on the page, which is how
               `"Morpho explicitly references integration with: Morpho"` was
               produced.

The replacement does two things regex cannot: it reads the page as prose, and
it refuses to emit a claim it cannot attach a subject to. Every claim keeps the
URL and timestamp it came from, so the entailment verifier can re-check it.
"""
from __future__ import annotations

import hashlib
import re
from datetime import datetime, timezone
from typing import Any

from .llm import LLMClient, LLMError, wrap_untrusted
from .models import client_for

EXTRACT_VERSION = "research-claims/v1"

CATEGORIES = ("POSITIONING", "PRODUCT", "PROOF", "PRICING", "RISK", "INTEGRATION")

SCHEMA = {
    "type": "object",
    "properties": {
        "claims": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "claim": {"type": "string"},
                    "category": {"type": "string", "enum": list(CATEGORIES)},
                    "metric": {"type": "string"},
                    "quote": {"type": "string"},
                },
                "required": ["claim", "category", "quote"],
            },
        }
    },
    "required": ["claims"],
}

SYSTEM = """You extract checkable factual claims about one company from a page
of its own content.

A claim must be a COMPLETE STATEMENT with an explicit subject. "Metric
observed: $12B" is not a claim — $12B of what? "Gearbox reports $12B in
cumulative trading volume" is.

Rules:
- One assertion per claim. Split compound sentences.
- Copy figures EXACTLY as the page states them, with their units and their
  subject. Never round, convert, or infer a unit.
- `quote` must be the verbatim span from the page that supports the claim. If
  you cannot find one, do not emit the claim.
- Do NOT emit: page titles, navigation labels, cookie notices, button text,
  image filenames, URLs, or anything whose meaning depends on layout.
- Do NOT emit a claim that the company "references" or "mentions" something.
  Presence of a word on a page is not a claim about the product.
- A page with no substantive claims returns an empty list. That is a correct
  answer and far more useful than filler.

Categories:
  POSITIONING  what the company says it is or who it is for
  PRODUCT      a capability, mechanism or architectural property
  PROOF        a measured figure, milestone or named customer
  PRICING      fees, rates, costs
  RISK         a stated limitation, risk control or safeguard
  INTEGRATION  a named, specific integration with another protocol"""


# Markdown images/links, bare URLs, and code fences carry figures that are not
# prose ("hero@1x"), which is exactly what the old regex tripped on.
_IMG = re.compile(r"!\[[^\]]*\]\([^)]*\)")
_LINK = re.compile(r"\[([^\]]*)\]\([^)]*\)")
_URL = re.compile(r"https?://\S+")
_FENCE = re.compile(r"```.*?```", re.S)
_WS = re.compile(r"[ \t]+")


def clean_page(content: str, max_chars: int = 12000) -> str:
    """Strip the parts of a scraped page that are not prose."""
    t = _FENCE.sub(" ", content or "")
    t = _IMG.sub(" ", t)
    t = _LINK.sub(r"\1", t)          # keep link text, drop the target
    t = _URL.sub(" ", t)
    lines = []
    for line in t.splitlines():
        s = _WS.sub(" ", line).strip()
        if len(s) < 25:
            continue                  # nav items, labels, isolated numbers
        if s.count("|") > 2:
            continue                  # table chrome
        letters = sum(ch.isalpha() for ch in s)
        if letters < len(s) * 0.55:
            continue                  # mostly punctuation, ids or digits
        lines.append(s)
    return "\n".join(lines)[:max_chars]


def _claim_id(entity: str, text: str) -> str:
    h = hashlib.md5(f"{entity}|{text}".encode("utf-8")).hexdigest()[:8]
    return f"CLM_{entity.upper()}_{h}"


def extract_claims(
    entity_id: str,
    url: str,
    page_title: str,
    content: str,
    *,
    observed_at: str | None = None,
    source_type: str = "official_website",
    confidence: float = 0.8,
    client: LLMClient | None = None,
) -> list[dict[str, Any]]:
    """Extract checkable claims from one scraped page.

    Returns [] on an empty or unusable page, and on model failure. An empty list
    is the honest outcome: the previous extractor guaranteed output by falling
    back to metadata, which is why 72 claims contained roughly 10 usable ones.
    """
    prose = clean_page(content)
    if len(prose) < 200:
        return []

    observed_at = observed_at or datetime.now(timezone.utc).isoformat()
    if client is None:
        client, _ = client_for("reasoning")

    prompt = (
        f"COMPANY: {entity_id}\n"
        f"PAGE: {page_title or '(untitled)'}\n\n"
        f"{wrap_untrusted('page content', prose)}\n\n"
        "Extract the checkable claims."
    )

    try:
        data, _ = client.complete_json(
            prompt, schema=SCHEMA, system=SYSTEM,
            prompt_version=EXTRACT_VERSION, temperature=0.0,
            max_output_tokens=8192,
        )
    except LLMError:
        return []

    out: list[dict[str, Any]] = []
    seen: set[str] = set()

    for raw in data.get("claims", []):
        text = str(raw.get("claim") or "").strip()
        quote = str(raw.get("quote") or "").strip()
        if not text or not quote:
            continue
        if _is_metadata(text):
            continue
        # The quote must actually be on the page. A model that invents its
        # supporting span has invented the claim.
        if _normalise(quote)[:60] not in _normalise(prose):
            continue
        key = _normalise(text)
        if key in seen:
            continue
        seen.add(key)

        claim: dict[str, Any] = {
            "claim_id": _claim_id(entity_id, text),
            "entity_id": entity_id.lower(),
            "claim": text,
            "category": raw.get("category", "PRODUCT"),
            "supporting_quote": quote[:400],
            "source_type": source_type,
            "source_url": url,
            "source_record_id": url,
            "observed_at": observed_at,
            "data_as_of": observed_at[:10],
            "evidence_status": "OBSERVED",
            "confidence": confidence,
            "extractor": EXTRACT_VERSION,
        }
        metric = str(raw.get("metric") or "").strip()
        if metric:
            claim["metric_extracted"] = metric
        out.append(claim)

    return out


_METADATA = re.compile(
    r"^\s*(official title|page title|home\b|menu\b|navigation|cookie|sign in|log in)",
    re.I,
)


def _is_metadata(text: str) -> bool:
    if _METADATA.search(text):
        return True
    if "official title on" in text.lower():
        return True
    # "X references/mentions Y" is presence, not a claim about the product.
    return bool(re.search(r"\b(references|mentions)\b.*\b(integration|compatibilit)", text, re.I))


def _normalise(s: str) -> str:
    return re.sub(r"\s+", " ", s or "").strip().lower()
