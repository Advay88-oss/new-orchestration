#!/usr/bin/env python3
"""Validate an OKF v0.2 bundle, and check it is usable by this pipeline.

Two levels, deliberately separate:

  Conformance (OKF §11) — errors. A bundle conforms if every non-reserved .md
  file has parseable YAML frontmatter carrying a non-empty `type`, and reserved
  filenames follow their structures. Per §11 a consumer must NOT reject a
  bundle for unknown types, unknown keys, broken links or missing index files,
  so none of those are errors here.

  Pipeline readiness — warnings. Things this particular pipeline needs in order
  to run for a company. A bundle can conform perfectly and still be useless to
  us; that is a warning, not a spec violation.

    python pipeline/scripts/okf_validate.py [--bundle okf] [--strict]

--strict makes readiness warnings exit non-zero too. Use it in CI before a
company's first live run.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from okf_loader import Bundle, RESERVED, parse_frontmatter, default_bundle_path  # noqa: E402

LINK = re.compile(r"\[[^\]]*\]\((/[^)]+\.md)\)")

# What this pipeline needs before it can run a company.
REQUIRED_TYPES = {
    "Overriding Constraint": "the one rule that outranks everything; the gate and every persona depend on it",
    "Narrative Arc": "the strategists have nothing to argue without these",
    "Claim Rule Set": "without rules the safety gate is inert",
    "Content Topic": "the conductor selects a topic per run from these",
    "Channel": "nothing knows where to publish or who approves",
}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--bundle", type=Path, default=None)
    ap.add_argument("--strict", action="store_true")
    args = ap.parse_args()

    root = args.bundle or default_bundle_path()
    errors: list[str] = []
    warnings: list[str] = []

    print(f"bundle: {root}")

    # --- conformance -------------------------------------------------------
    if not root.is_dir():
        print(f"ERROR  no bundle at {root}")
        return 1

    index = root / "index.md"
    version = None
    if index.exists():
        front, _ = parse_frontmatter(index.read_text(encoding="utf-8"))
        version = front.get("okf_version")
        extra = set(front) - {"okf_version"}
        if extra:
            errors.append(f"/index.md carries frontmatter beyond okf_version (§8): {sorted(extra)}")
    else:
        warnings.append("no root /index.md — legal, but agents lose progressive disclosure")

    if version:
        print(f"okf_version: {version}")
    else:
        warnings.append("root index.md declares no okf_version (§12)")

    try:
        bundle = Bundle.load(root)
    except ValueError as e:
        print(f"ERROR  {e}")
        return 1

    print(f"concepts: {len(bundle)}")

    # Reserved-file structure: index.md entries should be a bullet list.
    for idx in root.rglob("index.md"):
        rel = "/" + idx.relative_to(root).as_posix()
        text = idx.read_text(encoding="utf-8")
        if rel != "/index.md":
            fm, _ = parse_frontmatter(text)
            if fm:
                errors.append(f"{rel}: non-root index.md must not carry frontmatter (§8)")
        if not re.search(r"^\s*\*\s+\[", text, re.M):
            warnings.append(f"{rel}: no `* [Title](url) - description` entries (§8)")

    # --- pipeline readiness ------------------------------------------------
    present = bundle.types()
    for t, why in REQUIRED_TYPES.items():
        if t not in present:
            warnings.append(f"no `{t}` concept — {why}")

    n_arcs = len(bundle.arcs())
    if 0 < n_arcs < 3:
        warnings.append(f"{n_arcs} narrative arc(s); the debate design expects 3 opposed positions")

    rules = bundle.rules()
    if not rules:
        warnings.append("0 safety rules — the gate will fall back to its built-ins, "
                        "which are the PREVIOUS company's rules")
    else:
        seen: dict[str, int] = {}
        for r in rules:
            seen[r.id] = seen.get(r.id, 0) + 1
        dupes = [k for k, v in seen.items() if v > 1]
        if dupes:
            warnings.append(f"duplicate rule ids: {dupes}")
        for r in rules:
            try:
                re.compile(r.pattern)
            except re.error as e:
                errors.append(f"rule {r.id}: uncompilable pattern ({e})")
            if not r.fix:
                warnings.append(f"rule {r.id}: no `fix` — the strategist is told no and not what to write instead")

    constraint = bundle.constraint()
    if constraint and constraint.trust != "human-reviewed":
        warnings.append(f"overriding constraint is `{constraint.trust}` — "
                        "a machine-written constraint should be signed off by a human")

    # Broken links are tolerated by the spec but worth surfacing.
    known = {c.path for c in bundle} | {
        "/" + p.relative_to(root).as_posix() for p in root.rglob("*.md") if p.name in RESERVED
    }
    for c in bundle:
        for target in LINK.findall(c.body):
            if target.startswith("/files/") or target.startswith("/pipeline/") or target.startswith("/design-references/"):
                continue          # deliberate references out of the bundle
            if target not in known:
                warnings.append(f"{c.path}: link to missing concept {target}")

    # --- report ------------------------------------------------------------
    print(f"types: " + ", ".join(f"{k} x{v}" for k, v in present.items()))
    print(f"rules: {len(rules)}")

    if errors:
        print(f"\n{len(errors)} conformance ERROR(s):")
        for e in errors:
            print(f"  ERROR  {e}")
    if warnings:
        print(f"\n{len(warnings)} readiness warning(s):")
        for w in warnings:
            print(f"  WARN   {w}")
    if not errors and not warnings:
        print("\nconforms to OKF v0.2 and is ready for a live run")
    elif not errors:
        print("\nconforms to OKF v0.2; see warnings before a live run")

    if errors:
        return 1
    if warnings and args.strict:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
