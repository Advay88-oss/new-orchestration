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

It fails closed. Every text that will be seen is checked — the X post, the
LinkedIn and Reddit posts, and the words drawn on the poster — and when the
model calls or the gate itself cannot run, the run is blocked with that
reason rather than passed unchecked: a model outage must never be the way a
banned claim gets through.
"""
from __future__ import annotations

from typing import Any, Optional

AGENT = "A10_reviewer_firewall"


_PLATFORM = {"x": "x", "linkedin": "linkedin", "reddit": "reddit", "poster": "x"}


def _gate(text: str, platform: str = "x") -> list[dict]:
    """BLOCK violations of the deterministic claim gate. Raises when the gate
    cannot run: the caller blocks on that, it does not pass."""
    from pipeline.brand_brain import context as C
    from pipeline.scripts.claim_safety_gate import check
    v = check(text, platform=platform, require_testnet=bool(C.disclosure()))
    return [x for x in (v.get("violations") or []) if str(x.get("severity", "")).upper() == "BLOCK"]


def _gate_all(texts: dict[str, str]) -> tuple[list[dict], list[str]]:
    """The gate over every text. Returns (violations, blocked lines)."""
    found: list[dict] = []
    blocked: list[str] = []
    for where, text in texts.items():
        if not text.strip():
            continue
        try:
            hits = _gate(text, _PLATFORM.get(where, "x"))
        except Exception as exc:                    # noqa: BLE001 — fail closed, with the reason
            blocked.append("claim gate could not run on the " + where + " text: "
                           + type(exc).__name__ + ": " + str(exc)[:160])
            continue
        for g in hits:
            found.append({**g, "where": where})
            blocked.append("claim gate " + str(g.get("rule") or "") + " (" + where + "): "
                           + str(g.get("matched") or "") + " — " + str(g.get("fix") or ""))
    return found, blocked


def poster_words(brief: str) -> str:
    """The lines of a poster brief that are drawn as text on the image."""
    keep = ("headline", "subtitle", "footer", "label", "labels", "caption", "tagline", "callout")
    return "\n".join(line.split(":", 1)[1].strip() for line in str(brief or "").splitlines()
                     if ":" in line and line.split(":", 1)[0].strip().lower() in keep)


def _figures(text: str) -> set[str]:
    """Numbers as written, normalised (1,000 -> 1000; 0.10% -> 0.1%)."""
    import re
    out = set()
    for m in re.finditer(r"\d[\d,]*(?:\.\d+)?\s*%?", text or ""):
        n = m.group(0).replace(",", "").replace(" ", "")
        pct = n.endswith("%")
        n = n.rstrip("%")
        if "." in n:
            n = n.rstrip("0").rstrip(".")
        out.add(n + ("%" if pct else ""))
    return out


def check_copy(hook: str, copy: str, *, run_id: Optional[str] = None,
               channels: Optional[dict[str, str]] = None, poster: str = "") -> dict[str, Any]:
    """`channels`: the other channels' posts by name (linkedin, reddit);
    `poster`: the words drawn on the poster (poster_words())."""
    from pipeline.brand_brain import context as C
    from pipeline.gtm_os import agent_runtime as R

    texts = {"x": (hook + "\n\n" + copy).strip()}
    for k, v in (channels or {}).items():
        if k != "x" and str(v or "").strip():
            texts[k] = str(v).strip()
    if str(poster or "").strip():
        texts["poster"] = str(poster).strip()
    text = "\n\n".join(("[" + k.upper() + "]\n" + v) for k, v in texts.items())
    gate, gate_blocked = _gate_all(texts)
    name = C.company_name()
    try:
        ex = R.brain_json(
            "From this post, list every FACTUAL claim it makes about " + name + " or its "
            "product — capabilities, mechanisms, numbers, integrations, deployment, "
            "partners. Skip opinions, questions and framing. Quote each claim in a few "
            "words of your own.\n\nPOST (every channel, and the words on its poster):\n" + text[:6000]
            + '\n\nReturn JSON: {"claims": [str]} (at most 8).',
            agent=AGENT, role="reasoning", temperature=0.0, max_output_tokens=1024,
            system="You extract checkable factual claims precisely.", run_id=run_id)
        claims = [str(c)[:240] for c in (ex.get("claims") or []) if str(c).strip()][:8]
    except Exception as exc:                        # noqa: BLE001 — fail closed
        err = "claim extraction failed: " + str(exc)[:160]
        return {"ok": False, "error": err, "claims": [], "gate": gate, "checked": list(texts),
                "blocked": gate_blocked + ["fact check could not run (" + err + "); blocked until it can"]}

    evidence: dict[int, list[dict]] = {}
    for i, c in enumerate(claims):
        # Proof comes from documents, not from the profile that states the claim.
        evidence[i] = C.evidence_hits(c, k=4, max_authority=3)
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
        except Exception as exc:                    # noqa: BLE001 — fail closed
            err = "fact judgement failed: " + str(exc)[:160]
            return {"ok": False, "error": err, "claims": [{"claim": c} for c in claims], "gate": gate,
                    "checked": list(texts),
                    "blocked": gate_blocked + ["fact check could not run (" + err + "); blocked until it can"]}
        for i, c in enumerate(claims):
            r = by_i.get(i, {})
            v = str(r.get("verdict") or "UNSUPPORTED").upper()
            ev = next((h for h in evidence[i] if h["id"] == r.get("evidence_id")), None)
            # Prices and fees go stale and are the costliest to get wrong: a
            # claim supported by a pricing passage passes only if every figure
            # in it appears in that passage exactly, whatever the judge said.
            if v == "SUPPORTED" and ev and ev.get("content_type") == "pricing":
                missing = [n for n in _figures(c) if n not in _figures(ev["text"])]
                if missing:
                    v = "CONTRADICTED"
                    r = {**r, "why": "pricing figure not in the pricing source as written: " + ", ".join(missing)}
            judged.append({"claim": c, "verdict": v, "why": str(r.get("why") or "")[:200],
                           "source": ev["source"] if ev else None, "url": ev.get("url") if ev else None,
                           "section": ev["section"] if ev else None})
    blocked = [j["verdict"].lower() + ": " + j["claim"] + (" — " + j["why"] if j["why"] else "")
               for j in judged if j["verdict"] in ("UNSUPPORTED", "CONTRADICTED")]
    blocked += gate_blocked
    return {"ok": True, "claims": judged, "blocked": blocked, "gate": gate, "checked": list(texts),
            "supported": sum(1 for j in judged if j["verdict"] == "SUPPORTED")}
