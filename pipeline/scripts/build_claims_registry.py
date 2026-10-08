"""Build registry/claims.jsonl from the facts ledger, so there is one source.

The registry used to be written by hand. It drifted into the previous
product (EVM derivatives, a Prop Dashboard) and banned facts the ledger lists
as Tier A, such as the 14 Soroban contracts. Now the ledger
(files/08-facts-ledger-and-claim-safety.md) is the only place a claim is
decided, and this script derives the registry from it:

    Tier A  VERIFIED      action USE     state plainly
    Tier B  DESIGN        action USE     how it works, on testnet
    Tier C  ILLUSTRATIVE  action LABEL   only labelled as an example
    Tier D  ROADMAP       action FUTURE  future tense only
    Tier E  INTERNAL      action BLOCK   never published
    Tier F  UNVERIFIED    action BLOCK   stale or unverified
    §3      PROHIBITED    action BLOCK   the hard prohibitions

Each row: {id, tier, ledger_tier, action, claim, text, source}. `text` is
the same as `claim` (the reviewer reads `text`).

    python -m pipeline.scripts.build_claims_registry           # write it
    python -m pipeline.scripts.build_claims_registry --check   # exit 1 if out of date

pipeline/tests/test_claims_registry.py runs the check, so a ledger edit
without a rebuild fails the tests.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LEDGER = ROOT / "files" / "08-facts-ledger-and-claim-safety.md"
REGISTRY = ROOT / "registry" / "claims.jsonl"

TIERS = {
    "A": ("VERIFIED", "USE"), "B": ("DESIGN", "USE"), "C": ("ILLUSTRATIVE", "LABEL"),
    "D": ("ROADMAP", "FUTURE"), "E": ("INTERNAL", "BLOCK"), "F": ("UNVERIFIED", "BLOCK"),
}


def _plain(text: str) -> str:
    """Markdown emphasis and code marks off; one line."""
    t = re.sub(r"\*\*|__|`", "", text)
    return " ".join(t.split()).strip()


def parse(ledger: str) -> list[dict]:
    rows: list[dict] = []
    tier = None                                     # "A".."F", "P" for §3, None outside
    counts: dict[str, int] = {}
    for line in ledger.splitlines():
        h = re.match(r"^###\s+Tier\s+([A-F])\b", line)
        if h:
            tier = h.group(1)
            continue
        if re.match(r"^##\s+3\.\s+Hard prohibitions", line):
            tier = "P"
            continue
        if line.startswith("## ") or line.startswith("### "):
            tier = None
            continue
        if tier is None:
            continue
        claim, source = "", ""
        if line.startswith("|"):
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if not cells or set(cells[0]) <= {"-", " ", ":"} or cells[0] in ("Fact", "Item", "Content"):
                continue
            claim = cells[0]
            source = cells[1] if len(cells) > 1 else ""
        elif re.match(r"^\s*(?:-|\d+\.)\s+", line):
            claim = re.sub(r"^\s*(?:-|\d+\.)\s+", "", line)
        else:
            continue
        claim = _plain(claim)
        if not claim:
            continue
        counts[tier] = counts.get(tier, 0) + 1
        if tier == "P":
            name, action, label = "PROHIBITED", "BLOCK", "§3"
        else:
            name, action = TIERS[tier]
            label = "Tier " + tier
        rows.append({
            "id": "CLM-" + tier + "%02d" % counts[tier],
            "tier": name, "ledger_tier": tier, "action": action,
            "claim": claim, "text": claim,
            "source": "files/08 " + label + (" · " + _plain(source) if source else ""),
        })
    return rows


def build() -> str:
    rows = parse(LEDGER.read_text(encoding="utf-8"))
    return "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--check", action="store_true", help="exit 1 when the registry is out of date")
    a = ap.parse_args(argv)
    want = build()
    have = REGISTRY.read_text(encoding="utf-8") if REGISTRY.exists() else ""
    if a.check:
        if want != have:
            print("registry/claims.jsonl is out of date with the facts ledger; run "
                  "python -m pipeline.scripts.build_claims_registry", file=sys.stderr)
            return 1
        print("registry/claims.jsonl matches the facts ledger")
        return 0
    REGISTRY.write_text(want, encoding="utf-8")
    n = want.count("\n")
    print("wrote " + str(n) + " claims to " + str(REGISTRY.relative_to(ROOT)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
