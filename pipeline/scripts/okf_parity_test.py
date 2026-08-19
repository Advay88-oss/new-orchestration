#!/usr/bin/env python3
"""Prove the OKF-loaded rules behave identically to the gate's built-ins.

The gate is a safety control. Moving its rules out of Python and into a
knowledge pack is only safe if the two produce the same verdict on the same
input, so this asserts that rather than assuming it.

Also runs a must-block / must-pass suite, because a rule that has never blocked
anything has never been tested. Every company's bundle should extend
CORPUS with its own cases.

    python pipeline/scripts/okf_parity_test.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import claim_safety_gate as gate          # noqa: E402
from okf_loader import Bundle, default_bundle_path   # noqa: E402


def evaluate(rules, text: str) -> set[str]:
    """Rule ids that fire on this text, using the gate's own matching logic."""
    hits = set()
    for rule in rules:
        for match in re.finditer(rule.pattern, text, rule.flags):
            if match.group(0).strip():
                hits.add(rule.id)
                break
    return hits


# (text, must_block) — extend per company.
CORPUS: list[tuple[str, bool]] = [
    # Must block: the overriding constraint
    ("Vanna is now live on mainnet with $40M TVL.", True),
    ("Our contracts are audited and covered by a bug bounty.", True),
    ("The $VANNA airdrop is coming for early users.", True),
    ("Guaranteed risk-free returns, you can't lose.", True),
    ("You should invest now, this is a good investment.", True),
    ("Users earned returns of 14% last month.", True),
    # Must block: retired positioning
    ("Vanna is the only protocol with MCP support.", True),
    ("Nobody else is building agent credit scores.", True),
    # Must pass: accurate, constrained copy
    ("Vanna runs on Stellar testnet. Unified margin, illustrative example only.", False),
    ("Leverage is easy. Not getting liquidated is hard. On Stellar testnet.", False),
]


def main() -> int:
    builtin = gate.HARD_PROHIBITIONS + gate.TIER_F + gate.RETIRED + gate.VOICE
    path = default_bundle_path()

    try:
        okf = Bundle.load(path).rules()
    except Exception as e:
        print(f"FAIL  could not load OKF bundle at {path}: {e}")
        return 1

    failures = 0

    # 1. Same rules, same ids.
    print(f"built-in rules : {len(builtin)}")
    print(f"OKF rules      : {len(okf)}  (from {path})")
    b_ids, o_ids = {r.id for r in builtin}, {r.id for r in okf}
    if b_ids != o_ids:
        failures += 1
        print(f"FAIL  rule ids differ")
        print(f"      only built-in: {sorted(b_ids - o_ids)}")
        print(f"      only OKF     : {sorted(o_ids - b_ids)}")
    else:
        print(f"OK    rule ids identical ({len(b_ids)})")

    # 2. Patterns and flags survived the round-trip verbatim.
    by_id = {r.id: r for r in okf}
    drift = [r.id for r in builtin
             if r.id in by_id and (by_id[r.id].pattern != r.pattern
                                   or by_id[r.id].flags != r.flags)]
    if drift:
        failures += 1
        print(f"FAIL  pattern or flags drifted on: {drift}")
        print("      re-run: python pipeline/scripts/okf_export_rules.py")
    else:
        print("OK    every pattern and flag matches verbatim")

    # 3. Identical verdicts across the corpus.
    mismatched = []
    for text, _ in CORPUS:
        if evaluate(builtin, text) != evaluate(okf, text):
            mismatched.append(text[:52])
    if mismatched:
        failures += 1
        print(f"FAIL  verdicts differ on {len(mismatched)} input(s):")
        for t in mismatched:
            print(f"      {t!r}")
    else:
        print(f"OK    identical verdicts on all {len(CORPUS)} corpus inputs")

    # 4. The suite actually exercises the rules.
    print("\nmust-block / must-pass:")
    for text, must_block in CORPUS:
        hits = evaluate(okf, text)
        blocked = any(h for h in hits
                      if any(r.severity == gate.BLOCK for r in okf if r.id == h))
        ok = blocked == must_block
        if not ok:
            failures += 1
        want = "block" if must_block else "pass "
        got = "block" if blocked else "pass "
        rules_hit = ",".join(sorted(hits)) or "-"
        print(f"  [{'OK ' if ok else 'FAIL'}] want {want} got {got}  {text[:44]!r}  {rules_hit}")

    print()
    if failures:
        print(f"{failures} check(s) FAILED")
        return 1
    print("all checks passed — the OKF bundle is a faithful substitute for the built-ins")
    return 0


if __name__ == "__main__":
    sys.exit(main())
