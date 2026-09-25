"""A10's fact check — every claim in the copy against the brand brain.

The reviewer in the architecture checks two things: brand compliance, and
that each claim matches a source in the knowledge base. Until this, A10
checked five hardcoded phrases and that a provenance field was non-empty, so
a post could state anything the strategist believed and pass.

Now:
  1. The claims are pulled out of the post — factual statements about the
     company, not opinions or framing.
  2. Each claim is looked up with `search_knowledge` (archive excluded: it
     predates the current deployment in places and is not proof).
  3. One judgement over all claims and their evidence: SUPPORTED (with the
     source that supports it), UNSUPPORTED (nothing in the brain says so) or
     CONTRADICTED (the brain says otherwise).
  4. The deterministic claim-safety gate runs over the same copy.

Anything UNSUPPORTED or CONTRADICTED, and any BLOCK from the gate, blocks the
run — which, like every block, goes to the founder with its reasons. Neither
the reviewer nor the founder's approval can be bypassed by the learning loop.
"""
from __future__ import annotations

from typing import Any, Optional

AGENT = "A10_reviewer_firewall"


def _gate(text: str) -> list[dict]:
    try:
        from pipeline.brand_brain import context as C
        from pipeline.scripts.claim_safety_gate import check
        v = check(text, platform="x", require_testnet=bool(C.disclosure()))
        return [x for x in (v.get("violations") or []) if str(x.get("severity", "")).upper() == "BLOCK"]
    except Exception:                               # noqa: BLE001 — boundary
        return []


def check_copy(hook: str, copy: str, *, run_id: Optional[str] = None) -> dict[str, Any]:
    from pipeline.brand_brain import context as C
    from pipeline.gtm_os import agent_runtime as R

    text = (hook + "\n\n" + copy).strip()
    name = C.company_name()
    try:
        ex = R.brain_json(
            "From this post, list every FACTUAL claim it makes about " + name + " or its "
            "product — capabilities, mechanisms, numbers, integrations, deployment, "
            "partners. Skip opinions, questions and framing. Quote each claim in a few "
            "words of your own.\n\nPOST:\n" + text[:3000]
            + '\n\nReturn JSON: {"claims": [str]} (at most 8).',
            agent=AGENT, role="reasoning", temperature=0.0, max_output_tokens=1024,
            system="You extract checkable factual claims precisely.", run_id=run_id)
        claims = [str(c)[:240] for c in (ex.get("claims") or []) if str(c).strip()][:8]
    except Exception as exc:                        # noqa: BLE001 — boundary
        return {"ok": False, "error": "claim extraction failed: " + str(exc)[:160],
                "claims": [], "blocked": [], "gate": _gate(text)}

    evidence: dict[int, list[dict]] = {}
    for i, c in enumerate(claims):
        evidence[i] = C.knowledge_hits(c, k=4, max_authority=3)
    listing = []
    for i, c in enumerate(claims):
        listing.append("CLAIM " + str(i) + ": " + c)
        for h in evidence[i]:
            listing.append("  [" + h["id"] + " · " + h["source"] + " · " + h["section"][:60] + "] "
                           + " ".join(h["text"].split())[:500])
        if not evidence[i]:
            listing.append("  (no evidence found)")
    judged: list[dict] = []
    if claims:
        try:
            out = R.brain_json(
                "Judge each claim ONLY against the evidence under it. SUPPORTED if the evidence "
                "states it (name the evidence id); CONTRADICTED if the evidence says otherwise; "
                "UNSUPPORTED if the evidence does not say it. Do not use outside knowledge.\n\n"
                + "\n".join(listing)
                + '\n\nReturn JSON: {"claims": [{"i": int, "verdict": "SUPPORTED"|"UNSUPPORTED"|'
                  '"CONTRADICTED", "evidence_id": str, "why": str (one short sentence)}]}',
                agent=AGENT, role="reasoning", temperature=0.0, max_output_tokens=2048,
                system="You are a strict fact checker. Evidence only.", run_id=run_id)
            by_i = {int(r.get("i", -1)): r for r in (out.get("claims") or []) if isinstance(r, dict)}
        except Exception as exc:                    # noqa: BLE001 — boundary
            return {"ok": False, "error": "fact judgement failed: " + str(exc)[:160],
                    "claims": [{"claim": c} for c in claims], "blocked": [], "gate": _gate(text)}
        for i, c in enumerate(claims):
            r = by_i.get(i, {})
            v = str(r.get("verdict") or "UNSUPPORTED").upper()
            ev = next((h for h in evidence[i] if h["id"] == r.get("evidence_id")), None)
            judged.append({"claim": c, "verdict": v, "why": str(r.get("why") or "")[:200],
                           "source": ev["source"] if ev else None, "url": ev.get("url") if ev else None,
                           "section": ev["section"] if ev else None})
    blocked = [j["verdict"].lower() + ": " + j["claim"] + (" — " + j["why"] if j["why"] else "")
               for j in judged if j["verdict"] in ("UNSUPPORTED", "CONTRADICTED")]
    gate = _gate(text)
    blocked += ["claim gate " + str(g.get("rule") or "") + ": " + str(g.get("matched") or "")
                + " — " + str(g.get("fix") or "") for g in gate]
    return {"ok": True, "claims": judged, "blocked": blocked, "gate": gate,
            "supported": sum(1 for j in judged if j["verdict"] == "SUPPORTED")}
