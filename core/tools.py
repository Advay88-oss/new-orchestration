"""The toolbox agents actually reach for.

The point of giving a writing agent tools is that it can find out whether a
sentence will survive verification *before* it submits it. Until now the
copywriter received a fixed block of evidence and guessed; a claim that widened
a fact by one adjective ("all rounding" -> "every calculation") was only caught
two stages later, and the whole run was blocked at the gate.

`check_claim` closes that loop. It runs the same entailment check the pipeline
runs, against the same evidence store, with the same prompt version — so an
agent that checks its own claims and revises the failing ones is not guessing
what the verifier wants, it is asking it.
"""
from __future__ import annotations

from typing import Any

from .agent import Tool
from .contracts import Claim
from .evidence import EvidenceStore
from .llm import LLMClient
from .verify import VerificationCache, verify_claim


def search_evidence_tool(store: EvidenceStore) -> Tool:
    def run(query: str, limit: int = 6) -> dict[str, Any]:
        hits = store.search(query, limit=max(1, min(int(limit), 10)))
        return {
            "query": query,
            "found": len(hits),
            "evidence": [
                {
                    "id": h.id,
                    "text": h.snippet[:400],
                    "source": h.source_name,
                    "observed_at": h.observed_at[:10],
                }
                for h in hits
            ],
            # Saying this plainly stops an agent inventing support when the
            # store is simply thin on a subject.
            "note": "No results means the evidence store has nothing on this. "
                    "Do not write the claim." if not hits else "",
        }

    return Tool(
        name="search_evidence",
        description=(
            "Search Vanna's evidence store (live documentation, the facts "
            "ledger, competitor research, onchain readings). Returns evidence "
            "ids you can cite and check against."
        ),
        parameters={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "What you need evidence about."},
                "limit": {"type": "integer", "description": "Max results, 1-10."},
            },
            "required": ["query"],
        },
        fn=run,
    )


def check_claim_tool(store: EvidenceStore, client: LLMClient,
                     cache: VerificationCache | None = None) -> Tool:
    cache = cache or VerificationCache()

    def run(claim: str, kind: str = "vanna_fact") -> dict[str, Any]:
        c = verify_claim(Claim(text=claim, kind=kind), store, client, cache)
        verdict = {
            "claim": claim,
            "status": c.status,
            "source_id": c.source_id,
            "confidence": c.confidence,
            "would_block_publication": c.blocks_publication,
        }
        if c.status == "verified":
            verdict["advice"] = "Safe to write as stated."
        elif c.status == "refuted":
            verdict["advice"] = ("The evidence contradicts this. Do not write it; "
                                 "search for what the evidence actually says.")
        elif c.status == "unsupported":
            verdict["advice"] = (
                "No evidence entails this as written. Usually the sentence is "
                "wider than the fact: drop added intensifiers, consequences or "
                "scope, or search for a fact that supports it directly.")
        else:
            verdict["advice"] = "Not a factual claim, or the checker was unavailable."
        return verdict

    return Tool(
        name="check_claim",
        description=(
            "Check whether one sentence would pass verification against the "
            "evidence store. Use this on every factual sentence BEFORE "
            "submitting. It is the same check the pipeline runs afterwards."
        ),
        parameters={
            "type": "object",
            "properties": {
                "claim": {"type": "string", "description": "One atomic factual sentence."},
                "kind": {
                    "type": "string",
                    "enum": ["vanna_fact", "competitor_fact", "comparative",
                             "inference", "creative"],
                },
            },
            "required": ["claim"],
        },
        fn=run,
    )


def voice_tool(store: EvidenceStore) -> Tool:
    def run(topic: str) -> dict[str, Any]:
        hits = [h for h in store.search(topic, limit=12)
                if h.source_name.startswith("vanna-voice")][:3]
        return {
            "topic": topic,
            "guidance": [{"source": h.source_name, "text": h.snippet[:700]} for h in hits],
            "note": "Voice guidance describes how to say things. It is never "
                    "evidence that a claim is true.",
        }

    return Tool(
        name="get_voice",
        description=(
            "Retrieve Vanna's narrative and brand-voice guidance for a topic — "
            "arcs, positioning, channel conventions. Use it for how to say "
            "something, never as support for a fact."
        ),
        parameters={
            "type": "object",
            "properties": {"topic": {"type": "string"}},
            "required": ["topic"],
        },
        fn=run,
    )


def writing_toolbox(store: EvidenceStore, client: LLMClient,
                    cache: VerificationCache | None = None) -> list[Tool]:
    return [
        search_evidence_tool(store),
        check_claim_tool(store, client, cache),
        voice_tool(store),
    ]
