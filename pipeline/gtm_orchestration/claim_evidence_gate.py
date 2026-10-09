"""Phase 1.1: Claim Evidence Gate (claim_evidence_gate.py).

Responsible for: "Does the Brain actually support this claim?"
Evaluates factual grounding across 5 claim types:
  - VANNA_FACT: Requires direct Vanna documentation evidence.
  - COMPETITOR_FACT: Requires observed competitor dossier evidence.
  - COMPARATIVE_CLAIM: Requires two-sided evidence for BOTH sides.
  - WHITESPACE_INFERENCE: Must remain an inference; never serialized as observed fact.
  - MARKETING_OPPORTUNITY: Strategic hypothesis; not presented as market certainty.

Strictly blocks unsupported first-mover claims:
  "No competitor exists", "Zero competitors on Stellar", "Uncontested first-mover".
Absence of observed evidence is NEVER converted into evidence of absence.
"""

from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional
from pathlib import Path

from pipeline.gtm_orchestration.config import DEFAULT_CONFIG
from pipeline.gtm_orchestration.schemas import ClaimRecord, ClaimType, ClaimEvidenceStatus, ClaimAction


# Universal First-Mover & Absolute Negative Patterns
FIRST_MOVER_PATTERNS = [
    r"\bzero existing\b",
    r"\buncontested first-mover\b",
    r"\bno competitor(?:s)? (?:exist|does|has|provides)\b",
    r"\bnobody (?:else )?(?:on|in) (?:the )?\w+\b",
    r"\bthe only protocol (?:that|to)\b",
    r"\bzero competition\b",
    r"\bfirst and only\b"
]

COMPARATIVE_TRIGGER_PATTERNS = [
    r"\bvs\b|\bversus\b",
    r"\bunlike\b",
    r"\bcompetitor(?:s)?\b",
    r"\btraditional (?:lending|defi|pools)\b",
    r"\bshared pools? (?:while|whereas|vs)\b"
]

def _brand():
    from pipeline.brand_brain import context as C
    return C


def _fact_triggers() -> list[str]:
    """What marks a claim as a claim about the company itself: its name, its
    product anchors, its partners, its true figures and its app host — all
    from the brand profile."""
    import re as _re
    C = _brand()
    words = [C.company_name()]
    words += [v.split(" — ")[0].split(" (")[0] for v in C.anchors().values()]
    words += list(C.partners())
    words += [f["value"] for f in C.true_figures()]
    host = str(C.profile().get("company", {}).get("app_url", "")).replace("https://", "")
    if host:
        words.append(host)
    return [r"\b" + _re.escape(w.lower()) + r"\b" for w in words if len(w) > 2]


def _competitor_names() -> list[str]:
    C = _brand()
    partners = {p.lower() for p in C.partners()}
    return [c.lower() for c in C.competitors() if c.lower() not in partners]


def _support(text: str, k: int = 3) -> tuple[Optional[dict], float, list[str]]:
    """The brain section that best supports `text`, its term overlap, and the
    refs of every section looked at. Proof comes from documents
    (context.evidence_hits), never from the profile that states the claim; a
    number in the claim must appear in the evidence exactly."""
    t_lower = text.lower()
    hits = _brand().evidence_hits(text, k=k, max_authority=3)
    terms = set(re.findall(r"[a-z0-9.]{4,}", t_lower))
    best, overlap = None, 0.0
    for h in hits:
        ht = set(re.findall(r"[a-z0-9.]{4,}", (h["text"] + " " + h["section"]).lower()))
        o = len(terms & ht) / max(1, len(terms))
        if o > overlap:
            best, overlap = h, o
    refs = [h["source"] + ":" + h["section"][:80] + (" " + h["url"] if h.get("url") else "")
            for h in hits]
    nums = re.findall(r"\d[\d,.]*\d|\d", t_lower)
    if best and nums:
        ev = " ".join(h["text"].lower() for h in hits)
        if not all(n in ev for n in nums):
            best = None
    return best, overlap, refs


def _players(path: Path) -> list[dict]:
    rows = []
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    rows.append(json.loads(line))
    return rows


class ClaimEvidenceGate:
    """Pre-strategic and pre-editorial evidence firewall."""

    def __init__(self, config=None):
        self.config = config or DEFAULT_CONFIG
        self.brain_db = self.config.brain_db_dir
        self.knowledge_root = self.config.knowledge_root

    def classify_claim_type(self, text: str) -> ClaimType:
        """Classify the claim into exactly one ontological type."""
        t_lower = text.lower()

        # 1. Check for comparative framing first
        for pat in COMPARATIVE_TRIGGER_PATTERNS:
            if re.search(pat, t_lower):
                return "COMPARATIVE_CLAIM"

        for pat in FIRST_MOVER_PATTERNS:
            if re.search(pat, t_lower):
                return "COMPARATIVE_CLAIM"

        # 2. Check for whitespace inference
        if any(w in t_lower for w in ["whitespace", "market gap", "unexploited", "uncontested", "first-mover"]):
            return "WHITESPACE_INFERENCE"

        # 3. Check for strategic marketing opportunity
        if any(w in t_lower for w in ["opportunity", "positioning", "narrative", "angle", "should position"]):
            return "MARKETING_OPPORTUNITY"

        # 4. Check for competitor-specific facts or claims about external protocols
        if any(re.search(r"\b" + re.escape(comp) + r"\b", t_lower) for comp in _competitor_names()) \
           or any(k in t_lower for k in ["competitor", "market share", "protocol has", "protocol provides", "ghostprotocol"]):
            return "COMPETITOR_FACT"

        # 5. Check for Vanna facts
        for pat in _fact_triggers():
            if re.search(pat, t_lower):
                return "VANNA_FACT"

        return "MARKETING_OPPORTUNITY"

    def evaluate_claim(self, text: str, claim_id: Optional[str] = None) -> ClaimRecord:
        """Perform deep evidence verification against Brain DB and knowledge bases."""
        cid = claim_id or f"CLM-{abs(hash(text)) % 1000000:06d}"
        t_lower = text.lower()
        ctype = self.classify_claim_type(text)

        # ── RULE 1: BLOCK UNSUPPORTED FIRST-MOVER CLAIMS ──────────────────────
        is_first_mover = any(re.search(pat, t_lower) for pat in FIRST_MOVER_PATTERNS)
        if is_first_mover:
            return ClaimRecord(
                claim_id=cid,
                text=text,
                claim_type="COMPARATIVE_CLAIM",
                evidence_status="INSUFFICIENT",
                evidence_refs=[str(self.brain_db / "whitespace.jsonl")],
                confidence="LOW",
                source_records=["WHITESPACE_INFERENCE_ONLY"],
                calculation_method="Absence of observed evidence in current database cannot prove zero competitors exist across entire ecosystem.",
                action="DO_NOT_USE",
                rationale=(
                    "REJECTED BY EVIDENCE GATE: Claim asserts absolute absence of competition ('zero existing' / 'uncontested first-mover'). "
                    "A whitespace inference in the Brain only records what has been observed; it does not constitute an exhaustive global market census."
                )
            )

        # ── RULE 2: COMPARATIVE CLAIMS REQUIRE TWO-SIDED EVIDENCE ─────────────
        if ctype == "COMPARATIVE_CLAIM":
            has_vanna_side = any(re.search(pat, t_lower) for pat in _fact_triggers())
            has_competitor_side = (any(k in t_lower for k in ["shared pool", "pooled", "traditional", "legacy"])
                                   or any(c in t_lower for c in _competitor_names()))

            if not (has_vanna_side and has_competitor_side):
                return ClaimRecord(
                    claim_id=cid,
                    text=text,
                    claim_type=ctype,
                    evidence_status="INSUFFICIENT",
                    evidence_refs=[],
                    confidence="LOW",
                    source_records=[],
                    action="DO_NOT_USE",
                    rationale="Comparative claim lacks verifiable evidence on one of the comparison axes."
                )

            # Both sides are named; now each is looked up. This used to return
            # HIGH / USE with fixed source ids ("DOCS_VANNA_FINANCE",
            # "PLAYERS_DB_AAVE_MORPHO") and no lookup at all.
            best, overlap, refs = _support(text)
            named = [c for c in _competitor_names() if c in t_lower]
            players_file = self.brain_db / "players.jsonl"
            profiled = {str(p.get("player_id", "")).lower() for p in _players(players_file)}
            missing = [c for c in named if c not in profiled]
            if not (best and overlap >= 0.4):
                return ClaimRecord(
                    claim_id=cid, text=text, claim_type=ctype,
                    evidence_status="INSUFFICIENT", evidence_refs=refs, confidence="LOW",
                    source_records=[],
                    calculation_method="Brand brain search on the company side; best term overlap " + str(round(overlap, 2)),
                    action="USE_AS_INFERENCE",
                    rationale="The company side of the comparison is not stated in the brain's documents; keep it as framing.")
            if missing:
                return ClaimRecord(
                    claim_id=cid, text=text, claim_type=ctype,
                    evidence_status="UNKNOWN", evidence_refs=refs, confidence="LOW",
                    source_records=[best["id"]],
                    action="REQUIRES_VERIFICATION",
                    rationale="The competitor side (" + ", ".join(missing) + ") has no profile in the brain.")
            return ClaimRecord(
                claim_id=cid, text=text, claim_type=ctype,
                evidence_status="DERIVED",
                evidence_refs=refs + ([str(players_file)] if named else []),
                confidence="MEDIUM",
                source_records=[best["id"]] + ["PLAYER_PROFILE_" + c.upper() for c in named],
                calculation_method="Company side: brand brain search, term overlap " + str(round(overlap, 2))
                                   + ("; competitor side: player profiles" if named else "; competitor side: generic"),
                action="USE" if named else "USE_AS_INFERENCE",
                rationale=("Company side supported by " + best["source"] + " · " + best["section"][:80]
                           + ("; competitor side observed in its profile." if named
                              else "; the other side is a generic alternative, so the contrast stays framing.")))

        # ── RULE 3: COMPANY FACTS REQUIRE GROUND TRUTH IN THE BRAND BRAIN ─────
        # The evidence is the brain's best matching sections, with their
        # sources. A claim whose words the brain does not carry is kept as an
        # inference, not asserted; A10's fact check judges every claim that
        # reaches the copy against the same brain.
        if ctype == "VANNA_FACT":
            if any(p in t_lower for p in ["mainnet live", "live mainnet", "real tvl", "token trading"]):
                return ClaimRecord(
                    claim_id=cid,
                    text=text,
                    claim_type=ctype,
                    evidence_status="NOT_OBSERVED",
                    evidence_refs=[],
                    confidence="LOW",
                    source_records=["BRAND_PROFILE_DEPLOYMENT"],
                    action="DO_NOT_USE",
                    rationale="REJECTED: contradicts the deployment in the brand profile.")
            # A number in the claim must appear, exactly, in its evidence: an
            # invented figure shares every other word with a real section.
            best, overlap, refs = _support(text)
            if best and overlap >= 0.4:
                return ClaimRecord(
                    claim_id=cid,
                    text=text,
                    claim_type=ctype,
                    evidence_status="OBSERVED",
                    evidence_refs=refs,
                    confidence="HIGH" if best["authority"] <= 2 else "MEDIUM",
                    source_records=[best["id"]],
                    calculation_method="Brand brain hybrid search; term overlap " + str(round(overlap, 2)),
                    action="USE",
                    rationale="Supported by " + best["source"] + " · " + best["section"][:80])
            return ClaimRecord(
                claim_id=cid,
                text=text,
                claim_type=ctype,
                evidence_status="INSUFFICIENT",
                evidence_refs=refs,
                confidence="LOW",
                source_records=[],
                calculation_method="Brand brain hybrid search; best term overlap " + str(round(overlap, 2)),
                action="USE_AS_INFERENCE",
                rationale="The brand brain does not state this directly; keep it as framing, not fact.")

        # ── RULE 4: WHITESPACE INFERENCES MUST REMAIN INFERENCES ──────────────
        if ctype == "WHITESPACE_INFERENCE":
            return ClaimRecord(
                claim_id=cid,
                text=text,
                claim_type=ctype,
                evidence_status="INFERRED",
                evidence_refs=[],
                confidence="LOW",
                source_records=[],
                action="USE_AS_INFERENCE",
                rationale="Valid strategic hypothesis; must be framed as an inference, never as an empirical market census."
            )

        # ── RULE 5: COMPETITOR FACTS REQUIRE OBSERVED EVIDENCE ────────────────
        if ctype == "COMPETITOR_FACT":
            players_file = self.brain_db / "players.jsonl"
            players = _players(players_file)

            matched_players = [p["player_id"] for p in players if p["player_id"] in t_lower]
            if matched_players:
                return ClaimRecord(
                    claim_id=cid,
                    text=text,
                    claim_type=ctype,
                    evidence_status="OBSERVED",
                    evidence_refs=[str(players_file)],
                    confidence="HIGH",
                    source_records=[f"PLAYER_PROFILE_{p.upper()}" for p in matched_players],
                    action="USE",
                    rationale=f"Observed in verified competitor profile for {', '.join(matched_players)}."
                )
            else:
                return ClaimRecord(
                    claim_id=cid,
                    text=text,
                    claim_type=ctype,
                    evidence_status="UNKNOWN",
                    evidence_refs=[],
                    confidence="LOW",
                    source_records=[],
                    action="REQUIRES_VERIFICATION",
                    rationale="Competitor mentioned has no corresponding profile in Brain DB."
                )

        # Default Marketing Opportunity
        return ClaimRecord(
            claim_id=cid,
            text=text,
            claim_type=ctype,
            evidence_status="DERIVED",
            evidence_refs=[],
            confidence="LOW",
            source_records=[],
            action="USE_AS_INFERENCE",
            rationale="A positioning angle, not a fact; nothing was looked up, so it is framing only."
        )

    def audit_claim_list(self, claims: List[str]) -> List[ClaimRecord]:
        """Audit a batch of claims and return structured records."""
        return [self.evaluate_claim(c, f"CLM-{i+1:03d}") for i, c in enumerate(claims)]
