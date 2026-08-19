#!/usr/bin/env python3
"""Export the claim-safety gate's built-in rule sets to an OKF v0.2 bundle.

The gate's rules were written as Python literals. This dumps them to
`okf/rules/*.md` so a new company can be onboarded by editing markdown instead
of editing the gate, which is the highest-risk manual step in white-labelling.

Run once per gate change. Patterns are emitted verbatim — never hand-transcribe
a regex.

    python pipeline/scripts/okf_export_rules.py [--bundle okf] [--check]

--check exits non-zero if the bundle differs from the built-ins, so CI can
catch a gate edit that was never exported.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import asdict
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "pipeline" / "scripts"))

import claim_safety_gate as gate  # noqa: E402

# Which built-in list goes to which concept document.
SETS = [
    {
        "attr": "HARD_PROHIBITIONS",
        "file": "hard-prohibitions.md",
        "type": "Claim Rule Set",
        "title": "Hard prohibitions",
        "description": "Claims that are false at this company's stage and must never be published.",
        "tags": ["safety", "blocking", "stage"],
        "body": (
            "Derived from the company's overriding constraint. Every rule here "
            "descends from [/company/constraint.md](/company/constraint.md) — if "
            "that constraint changes, this file is the first thing to rewrite.\n\n"
            "For another company, replace these wholesale. A rule that names a "
            "concept the new company does not have is dead weight, and worse, it "
            "creates the impression the gate is configured when it is not."
        ),
    },
    {
        "attr": "TIER_F",
        "file": "tier-f-unsupported.md",
        "type": "Claim Rule Set",
        "title": "Unsupported and tier-inflated facts",
        "description": "Facts stated at a higher confidence than the facts ledger supports.",
        "tags": ["safety", "blocking", "facts"],
        "body": (
            "These catch a claim that exists in the ledger but is being stated "
            "more strongly than its tier allows — a Tier C roadmap item written "
            "in the present tense, or a Tier B fact stated without its "
            "qualifier. See [/facts/tier-b-qualified.md](/facts/tier-b-qualified.md) "
            "and [/facts/tier-c-future.md](/facts/tier-c-future.md)."
        ),
    },
    {
        "attr": "RETIRED",
        "file": "retired-claims.md",
        "type": "Claim Rule Set",
        "title": "Retired positioning",
        "description": "Claims that were once safe and became false when the market moved.",
        "tags": ["safety", "blocking", "competitive"],
        "body": (
            "The most perishable rule set, and the one most likely to be wrong "
            "for another company. These exist because a competitor shipped "
            "something that invalidated a claim this company used to make; see "
            "[/facts/retired.md](/facts/retired.md) for the underlying facts and "
            "when each was retired.\n\n"
            "**For a new company this set is almost certainly empty at first.** "
            "That is correct. It fills up as the market moves."
        ),
    },
    {
        "attr": "VOICE",
        "file": "voice.md",
        "type": "Claim Rule Set",
        "title": "Voice prohibitions",
        "description": "Brand-voice patterns that are rejected regardless of factual accuracy.",
        "tags": ["voice", "style"],
        "body": (
            "The most portable rule set in the bundle. Generic hype, hedging and "
            "filler read badly for almost any company, so most of these survive a "
            "re-branding unchanged. Review rather than rewrite."
        ),
    },
]


def flags_to_names(flags: int) -> list[str]:
    """Render re module flags as portable names rather than an integer."""
    names = []
    for name in ("IGNORECASE", "MULTILINE", "DOTALL", "VERBOSE"):
        if flags & getattr(re, name):
            names.append(name)
    return names


def rule_to_dict(rule) -> dict:
    d = asdict(rule)
    d["flags"] = flags_to_names(d.get("flags", 0))
    # Emit in a stable, readable key order.
    return {
        "id": d["id"],
        "severity": d["severity"],
        "pattern": d["pattern"],
        "why": d["why"],
        "fix": d["fix"],
        "flags": d["flags"],
    }


def render(spec: dict) -> str:
    rules = [rule_to_dict(r) for r in getattr(gate, spec["attr"])]
    front = {
        "type": spec["type"],
        "title": spec["title"],
        "description": spec["description"],
        "tags": spec["tags"],
        "status": "stable",
        "generated": {
            "by": "process:okf_export_rules",
            "at": "2026-08-10T00:00:00Z",
        },
        "sources": [
            {
                "id": "gate-builtin",
                "resource": "/pipeline/scripts/claim_safety_gate.py",
                "title": f"claim_safety_gate.{spec['attr']}",
            }
        ],
        "rule_count": len(rules),
        "rules": rules,
    }
    fm = yaml.safe_dump(front, sort_keys=False, allow_unicode=True, width=100)
    return (
        f"---\n{fm}---\n\n"
        f"# {spec['title']}\n\n"
        f"{spec['body']}\n\n"
        f"## How these are applied\n\n"
        f"Each entry is a regular expression evaluated against the draft body. A "
        f"match at severity `block` exits the gate non-zero and the draft never "
        f"reaches a human reviewer. `warn` is recorded and does not stop the run.\n\n"
        f"`pattern` is the regex verbatim; `flags` are `re` module flag names. "
        f"`why` is shown to the agent that wrote the draft, and `fix` tells it what "
        f"to write instead — a rule without a usable `fix` produces a strategist "
        f"that retries the same mistake.\n\n"
        f"## Editing\n\n"
        f"Change a pattern here and the gate picks it up on its next run; there is "
        f"no build step. **Then prove it**: write a string that must be blocked and "
        f"confirm it is.\n\n"
        f"```bash\n"
        f"python pipeline/scripts/claim_safety_gate.py --text \"a claim that must block\"\n"
        f"```\n"
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--bundle", type=Path, default=REPO / "okf")
    ap.add_argument("--check", action="store_true",
                    help="exit 1 if the bundle is out of date instead of writing")
    args = ap.parse_args()

    out_dir = args.bundle / "rules"
    out_dir.mkdir(parents=True, exist_ok=True)

    stale = []
    for spec in SETS:
        text = render(spec)
        path = out_dir / spec["file"]
        if args.check:
            if not path.exists() or path.read_text(encoding="utf-8") != text:
                stale.append(str(path.relative_to(REPO)))
        else:
            path.write_text(text, encoding="utf-8")
            print(f"wrote {path.relative_to(REPO)}  ({len(getattr(gate, spec['attr']))} rules)")

    if args.check:
        if stale:
            print("OKF rules bundle is out of date with the gate:")
            for s in stale:
                print(f"  {s}")
            print("Re-run: python pipeline/scripts/okf_export_rules.py")
            return 1
        print("OKF rules bundle matches the gate.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
