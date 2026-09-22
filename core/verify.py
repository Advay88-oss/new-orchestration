"""Claim extraction and entailment verification.

The old claim gate was a 32-pattern word blacklist. It blocked "guaranteed" and
"TVL" but passed, with zero violations:

    "Vanna's credit utilization grew 340% last quarter and our partnership with
     the Stellar Development Foundation routes $1.2B of institutional flow."

It could not detect a fabricated number because it had no concept of a fact.
This module replaces vocabulary matching with two steps the industry treats as
the standard for systems that publish factual claims:

1. **Extraction** — decompose copy into atomic, individually checkable claims.
2. **Entailment** — for each claim, retrieve evidence and ask whether the
   evidence *wholly* entails it. Partial support is not support: right entity,
   wrong number is `refuted`, not `verified`.

A claim with no retrieved evidence is `unsupported` — the verdict the blacklist
could never reach, and the one that catches invention.
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Sequence

from .contracts import Claim, Evidence, StageResult, degraded, digest, ok
from .evidence import EvidenceStore
from .llm import LLMClient, LLMError, wrap_untrusted

REPO = Path(__file__).resolve().parents[1]
CACHE_PATH = Path(os.environ.get("VANNA_VERIFY_CACHE",
                                 REPO / "state" / "verification_cache.jsonl"))

EXTRACT_PROMPT_VERSION = "extract-claims/v1"
VERIFY_PROMPT_VERSION = "verify-claim/v1"

EXTRACT_SCHEMA = {
    "type": "object",
    "properties": {
        "claims": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "text": {"type": "string"},
                    "kind": {
                        "type": "string",
                        "enum": ["vanna_fact", "competitor_fact", "comparative",
                                 "inference", "creative"],
                    },
                },
                "required": ["text", "kind"],
            },
        }
    },
    "required": ["claims"],
}

EXTRACT_SYSTEM = """You decompose marketing copy into atomic, checkable claims.

Rules:
- One assertion per claim. Split compound sentences.
- Preserve numbers, entity names and units EXACTLY as written. Never round,
  normalise or correct them — the point is to check what was actually written.
- Classify each claim:
  vanna_fact      a factual assertion about Vanna's product, metrics or status
  competitor_fact a factual assertion about another protocol or the market
  comparative     an explicit comparison between Vanna and something else
  inference       a reasoned conclusion presented as analysis, not measurement
  creative        metaphor, framing, rhetorical question, or opinion with no
                  checkable factual content
- Rhetorical framing is `creative`. A sentence containing any number, date,
  percentage, product capability or named entity is NOT creative.
- Return every claim. Missing one is worse than splitting too finely."""

VERIFY_SCHEMA = {
    "type": "object",
    "properties": {
        "verdict": {"type": "string", "enum": ["entailed", "contradicted", "not_supported"]},
        "evidence_id": {"type": "string"},
        "reason": {"type": "string"},
        "confidence": {"type": "number"},
    },
    "required": ["verdict", "reason", "confidence"],
}

VERIFY_SYSTEM = """You decide whether supplied evidence entails a claim.

Return `entailed` ONLY if the evidence states, or unambiguously implies, the
WHOLE claim — every entity, number, unit and timeframe in it.

Partial correctness is NOT entailment. If the claim says "320ms" and the
evidence says "sub-second", that is `not_supported`. If the claim says 340% and
the evidence says 34%, that is `contradicted`. If the evidence is about a
different entity or period, that is `not_supported`.

If the evidence does not address the claim at all, return `not_supported`.
Never reason from your own background knowledge — only the supplied evidence
counts. You are not being asked whether the claim is plausible, or whether it is
true in general. You are being asked whether THIS evidence proves it.

Set evidence_id to the id of the single piece that best supports or contradicts
the claim, or leave it empty if none is relevant."""


def extract_claims(text: str, client: LLMClient) -> StageResult[list[Claim]]:
    """Decompose copy into atomic claims."""
    started = time.time()
    ih = digest(text)
    if not text.strip():
        return ok("extract", [], started, input_hash=ih)

    try:
        data, resp = client.complete_json(
            f"Decompose this copy into atomic claims.\n\n{wrap_untrusted('copy', text)}",
            schema=EXTRACT_SCHEMA,
            system=EXTRACT_SYSTEM,
            prompt_version=EXTRACT_PROMPT_VERSION,
            temperature=0.0,
            max_output_tokens=8192,
        )
    except LLMError as exc:
        # We cannot verify what we cannot decompose. Degrading here means the
        # gate will block on "claims unknown" rather than wave the copy through.
        return degraded("extract", None, started,
                        f"extraction failed: {exc}", input_hash=ih)

    claims = []
    for raw in data.get("claims", []):
        t = (raw.get("text") or "").strip()
        if t:
            claims.append(Claim(text=t, kind=raw.get("kind", "vanna_fact"), status="unverified"))

    return ok("extract", claims, started, input_hash=ih,
              model=resp.model, prompt_version=resp.prompt_version,
              input_tokens=resp.input_tokens, output_tokens=resp.output_tokens,
              cost_usd=resp.cost_usd or 0.0, cost_known=resp.pricing_known, attempts=resp.attempts)


class VerificationCache:
    """Memoises verdicts by (claim, evidence set, prompt version).

    Entailment judgements are not perfectly stable even at temperature 0 — the
    same claim was observed both `verified` and `unsupported` across runs during
    development. For a gate that blocks publication, flapping is a defect: a true
    claim must not be blocked at random, and a run must be reproducible.

    Caching makes a given (claim, evidence, prompt-version) triple resolve to one
    verdict forever. Changing the prompt version invalidates the cache, which is
    what makes prompt changes auditable rather than invisible.
    """

    def __init__(self, path: Path | None = None) -> None:
        self.path = path or CACHE_PATH
        self._data: dict[str, dict] | None = None

    def _load(self) -> dict[str, dict]:
        if self._data is None:
            self._data = {}
            if self.path.exists():
                with self.path.open(encoding="utf-8") as fh:
                    for line in fh:
                        line = line.strip()
                        if line:
                            try:
                                rec = json.loads(line)
                                self._data[rec["key"]] = rec
                            except Exception:
                                continue
        return self._data

    @staticmethod
    def key(claim_text: str, evidence_ids: Sequence[str]) -> str:
        return digest([claim_text, sorted(evidence_ids), VERIFY_PROMPT_VERSION])

    def get(self, key: str) -> dict | None:
        return self._load().get(key)

    def put(self, key: str, payload: dict) -> None:
        rec = {"key": key, "prompt_version": VERIFY_PROMPT_VERSION, **payload}
        self._load()[key] = rec
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")


def verify_claim(claim: Claim, store: EvidenceStore, client: LLMClient,
                 cache: "VerificationCache | None" = None) -> Claim:
    """Check one claim against retrieved evidence. Returns an updated Claim."""
    if claim.kind == "creative":
        # Nothing factual to check; it is allowed through by design.
        return claim.model_copy(update={"status": "unverified", "method": "creative-exempt"})

    candidates: Sequence[Evidence] = store.search(claim.text, limit=6)
    if not candidates:
        return claim.model_copy(update={
            "status": "unsupported",
            "method": "retrieval/no-candidates",
            "confidence": 1.0,
        })

    cache_key = VerificationCache.key(claim.text, [e.id for e in candidates])
    cached = cache.get(cache_key) if cache else None

    if cached is not None:
        data = cached
    else:
        block = "\n\n".join(
            f"[{e.id}] source={e.source_name} observed_at={e.observed_at}\n{e.snippet}"
            for e in candidates
        )
        prompt = (
            f"CLAIM:\n{claim.text}\n\n"
            f"{wrap_untrusted('evidence', block)}\n\n"
            "Does the evidence entail the whole claim?"
        )
        try:
            data, resp = client.complete_json(
                prompt, schema=VERIFY_SCHEMA, system=VERIFY_SYSTEM,
                prompt_version=VERIFY_PROMPT_VERSION, temperature=0.0,
                max_output_tokens=4096,
            )
        except LLMError as exc:
            # A verifier that cannot run must not return "verified".
            return claim.model_copy(update={
                "status": "unverified",
                "method": f"verifier-unavailable: {exc}"[:200],
                "confidence": 0.0,
            })
        # Self-consistency on the blocking direction only. Entailment judgements
        # flap on borderline claims; freezing a random negative would block true
        # copy and teach the operator to ignore the gate. A second independent
        # judgement is cheap because it runs only when we are about to block.
        if data.get("verdict") != "entailed":
            try:
                second, _ = client.complete_json(
                    prompt, schema=VERIFY_SCHEMA, system=VERIFY_SYSTEM,
                    prompt_version=VERIFY_PROMPT_VERSION, temperature=0.0,
                    max_output_tokens=4096,
                )
                if second.get("verdict") == "entailed":
                    # The judgements disagree. Do not silently pick one —
                    # surface it for a human and record that it was contested.
                    data = {
                        "verdict": "not_supported",
                        "evidence_id": second.get("evidence_id"),
                        "reason": f"CONTESTED: first={data.get('verdict')} "
                                  f"second=entailed. {second.get('reason', '')}",
                        "confidence": 0.5,
                        "contested": True,
                    }
            except LLMError:
                pass          # one judgement stands; it is the strict one

        if cache:
            cache.put(cache_key, {
                "claim": claim.text,
                "verdict": data.get("verdict"),
                "evidence_id": data.get("evidence_id"),
                "reason": data.get("reason"),
                "confidence": data.get("confidence"),
                "contested": data.get("contested", False),
                "model": resp.model,
            })

    verdict = data.get("verdict", "not_supported")
    ev_id = (data.get("evidence_id") or "").strip() or None
    ev = store.get(ev_id) if ev_id else None
    conf = float(data.get("confidence", 0.0) or 0.0)
    conf = min(max(conf, 0.0), 1.0)

    if verdict == "entailed" and ev is not None:
        return claim.model_copy(update={
            "status": "verified",
            "source_id": ev.id,
            "source_url": ev.source_url,
            "observed_at": ev.observed_at,
            "method": f"entailment/{VERIFY_PROMPT_VERSION}",
            "confidence": conf,
        })
    if verdict == "contradicted":
        return claim.model_copy(update={
            "status": "refuted",
            "source_id": ev.id if ev else None,
            "source_url": ev.source_url if ev else None,
            "method": f"entailment/{VERIFY_PROMPT_VERSION}",
            "confidence": conf,
        })
    # entailed-but-no-evidence-id is treated as unsupported: a verification with
    # no locator cannot be re-checked, so it does not count.
    return claim.model_copy(update={
        "status": "unsupported",
        "method": f"entailment/{VERIFY_PROMPT_VERSION}",
        "confidence": conf,
    })


def verify_claims(claims: list[Claim], store: EvidenceStore, client: LLMClient,
                  cache: VerificationCache | None = None) -> StageResult[list[Claim]]:
    started = time.time()
    ih = digest([c.text for c in claims])
    cache = cache if cache is not None else VerificationCache()

    # Count cache hits so the dashboard can distinguish "this agent reused a
    # recorded verdict" from "this agent never reasoned at all". Both show zero
    # model calls; only one of them is a problem.
    before = len(cache._load())
    out = [verify_claim(c, store, client, cache) for c in claims]
    fresh = len(cache._load()) - before
    cached = max(0, len([c for c in out if c.kind != "creative"]) - fresh)

    unavailable = [c for c in out if c.method and c.method.startswith("verifier-unavailable")]
    if unavailable:
        return degraded("verify", out, started,
                        f"{len(unavailable)}/{len(out)} claims could not be verified "
                        f"(verifier unavailable)", input_hash=ih,
                        tool_calls=[f"entailment x{fresh}", f"verification-cache x{cached}"])
    return ok("verify", out, started, input_hash=ih,
              prompt_version=VERIFY_PROMPT_VERSION,
              tool_calls=([f"entailment x{fresh}"] if fresh else [])
                         + ([f"verification-cache x{cached}"] if cached else []))


def report(claims: list[Claim]) -> dict:
    """Counts for the dashboard. Derived, never stored separately."""
    by = {"verified": 0, "unverified": 0, "unsupported": 0, "refuted": 0}
    for c in claims:
        by[c.status] = by.get(c.status, 0) + 1
    return {
        "total": len(claims),
        "by_status": by,
        "blocking": [c.text for c in claims if c.blocks_publication],
    }
