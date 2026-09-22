"""Publication gate.

Two independent checks, both required to pass:

1. **Vocabulary rules** — the existing `claim_safety_gate.py` blacklist. It is a
   genuinely well-built compliance filter (fails closed to its builtins) and it
   reliably stops "guaranteed", "risk-free", "TVL" and exclamation marks. Its
   only flaw was being sold as a claim checker when it is a word filter — and
   never being invoked by the production runner at all.

2. **Claim entailment** — from `verify.py`. This is the check that catches an
   invented number, which no blacklist can.

The gate sees the ENTIRE asset — hook, body, thread, and every string rendered
into the visual. The old path submitted only `body`, so numbers printed on the
image bypassed compliance completely.
"""
from __future__ import annotations

import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Sequence

from .contracts import Claim, CopyDraft, GateDecision, StageResult, VisualSpec, degraded, digest, ok

REPO = Path(__file__).resolve().parents[1]
LEGACY_GATE = REPO / "pipeline" / "scripts" / "claim_safety_gate.py"

# Minimal in-process mirror of the legacy hard prohibitions, used when the
# legacy script cannot be invoked. Deliberately strict: a gate that cannot run
# its full ruleset must not become permissive.
FALLBACK_RULES: tuple[tuple[str, str], ...] = (
    (r"\bguarantee(d|s)?\b", "guarantee language"),
    (r"\brisk[- ]free\b", "risk-free claim"),
    (r"\bcan'?t lose\b", "loss-impossible claim"),
    (r"\bTVL\b|\btotal value locked\b", "TVL reference"),
    (r"\bairdrop\b|\$VANNA\b|\bpoints program\b", "token/airdrop reference"),
    (r"\blive on (mainnet|Optimism|Arbitrum|Base)\b", "mainnet-live claim"),
    (r"\baudited\b|\binsurance\b|\bmultisig\b", "security assurance claim"),
    (r"\byou should buy\b|\bfinancial advice\b", "investment advice"),
    (r"\bbetter than (Gearbox|Aave|Morpho|Compound)\b", "unsubstantiated comparison"),
    (r"\b(revolutionary|game[- ]changing|next[- ]gen|seamlessly)\b", "hype register"),
    (r"!", "exclamation mark"),
    (r"\b(compliant|licensed|regulated)\b", "regulatory claim"),
    (r"\bproduction[- ]grade\b|\b99\.9% uptime\b", "reliability claim"),
    (r"\bcase study\b|\btestimonial\b|\btrusted by \d", "fabricated proof"),
)


def _legacy_rules(text: str) -> tuple[list[str], str] | None:
    """Run the existing gate script if it is available. Returns (violations, source)."""
    if not LEGACY_GATE.exists():
        return None
    try:
        proc = subprocess.run(
            [sys.executable, str(LEGACY_GATE), "--text", text],
            capture_output=True, text=True, timeout=45,
            encoding="utf-8", errors="replace",
        )
    except Exception:
        return None
    if proc.returncode not in (0, 1):
        return None
    out = (proc.stdout or "") + (proc.stderr or "")
    # The script prints rule ids for violations; absence of a clean PASS is
    # treated as unknown rather than as a pass.
    if "PASS" in out.upper() and "FAIL" not in out.upper():
        return [], "legacy:claim_safety_gate"
    hits = re.findall(r"\b([PTRV]\d{2}[\w-]*)", out)
    if hits:
        return sorted(set(hits)), "legacy:claim_safety_gate"
    return None


def _fallback_rules(text: str) -> list[str]:
    violations = []
    for pattern, label in FALLBACK_RULES:
        if re.search(pattern, text, flags=re.IGNORECASE):
            violations.append(label)
    return violations


def collect_surfaces(draft: CopyDraft, spec: VisualSpec | None) -> str:
    """Every readable string in the asset — not just `body`."""
    parts = [draft.hook, draft.body, *draft.thread]
    if spec is not None:
        parts += [spec.headline, spec.subhead or "", *(b.text for b in spec.blocks)]
        if spec.disclaimer:
            parts.append(spec.disclaimer)
    return "\n".join(p for p in parts if p)


def run_gate(draft: CopyDraft, spec: VisualSpec | None,
             verified_claims: Sequence[Claim]) -> StageResult[GateDecision]:
    started = time.time()
    surface = collect_surfaces(draft, spec)
    ih = digest(surface)

    legacy = _legacy_rules(surface)
    if legacy is not None:
        violations, source = legacy
    else:
        violations, source = _fallback_rules(surface), "builtin-fallback"

    blocking = [c for c in verified_claims if c.blocks_publication]
    passed = not violations and not blocking

    decision = GateDecision(
        passed=passed,
        blocking_claims=list(blocking),
        rule_violations=violations,
        rules_source=source,
    )

    if source == "builtin-fallback" and legacy is None and LEGACY_GATE.exists():
        # The full ruleset exists but could not be executed. Say so — a partial
        # gate reporting a clean pass is exactly the failure mode being removed.
        return degraded("gate", decision, started,
                        "full ruleset unavailable; evaluated with builtin fallback only",
                        input_hash=ih)

    return ok("gate", decision, started, input_hash=ih,
              tool_calls=[source])
