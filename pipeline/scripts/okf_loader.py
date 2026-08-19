#!/usr/bin/env python3
"""Read an Open Knowledge Format (OKF) v0.2 bundle.

One bundle holds everything company-specific: the overriding constraint, the
narrative arcs, the facts ledger, the safety rules, the taxonomy, competitors,
brand and channels. Point the pipeline at a different bundle and it runs for a
different company.

    from okf_loader import Bundle
    b = Bundle.load("okf")
    b.constraint()                  # the one rule that outranks everything
    b.rules()                       # gate rules, ready to evaluate
    b.concepts("Narrative Arc")     # every arc
    b.taxonomy()                    # content pillars

Spec: https://github.com/GoogleCloudPlatform/knowledge-catalog/tree/main/okf

Deliberately tolerant, per OKF §11: a consumer must not reject a bundle for
unknown types, unknown frontmatter keys, broken links or missing index files.
Only two things are fatal — unparseable frontmatter and a missing `type`.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterator

try:
    import yaml
    _HAVE_YAML = True
except ImportError:                                     # pragma: no cover
    _HAVE_YAML = False

RESERVED = {"index.md", "log.md"}
_FM = re.compile(r"\A---\s*\n(.*?)\n---\s*\n?(.*)\Z", re.S)


# --------------------------------------------------------------------------
# Minimal frontmatter fallback
# --------------------------------------------------------------------------

def _mini_yaml(text: str) -> dict:
    """Parse the flat subset of YAML this bundle needs when PyYAML is absent.

    Handles `key: value`, one level of `- item` lists and simple nested
    mappings. Anything more complex returns the raw string, which is enough to
    keep `type` readable so validation still works.
    """
    out: dict[str, Any] = {}
    key = None
    for raw in text.splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip())
        line = raw.strip()
        if line.startswith("- ") and key:
            out.setdefault(key, [])
            if isinstance(out[key], list):
                out[key].append(line[2:].strip().strip("'\""))
            continue
        if ":" in line and indent == 0:
            k, _, v = line.partition(":")
            key = k.strip()
            v = v.strip().strip("'\"")
            out[key] = v if v else None
    return out


def parse_frontmatter(text: str) -> tuple[dict, str]:
    m = _FM.match(text)
    if not m:
        return {}, text
    raw, body = m.group(1), m.group(2)
    if _HAVE_YAML:
        try:
            data = yaml.safe_load(raw) or {}
        except yaml.YAMLError as e:
            raise ValueError(f"unparseable YAML frontmatter: {e}") from e
    else:
        data = _mini_yaml(raw)
    if not isinstance(data, dict):
        raise ValueError("frontmatter is not a mapping")
    return data, body


# --------------------------------------------------------------------------
# Concepts
# --------------------------------------------------------------------------

@dataclass
class Concept:
    path: str                      # bundle-relative, e.g. /rules/voice.md
    type: str
    front: dict = field(default_factory=dict)
    body: str = ""

    @property
    def title(self) -> str:
        return self.front.get("title") or Path(self.path).stem

    @property
    def status(self) -> str:
        """OKF §5: absent status means stable."""
        return self.front.get("status") or "stable"

    @property
    def trust(self) -> str:
        """OKF §5 trust tiers, derived from `verified`."""
        v = self.front.get("verified")
        if not v:
            return "unverified"
        entries = v if isinstance(v, list) else [v]
        for e in entries:
            by = (e or {}).get("by", "") if isinstance(e, dict) else str(e)
            if str(by).startswith("human:"):
                return "human-reviewed"
        return "machine-confirmed"

    def get(self, key: str, default=None):
        return self.front.get(key, default)


@dataclass
class GateRule:
    """Mirrors claim_safety_gate.Rule so loaded rules drop straight in."""
    id: str
    severity: str
    pattern: str
    why: str
    fix: str
    flags: int = re.IGNORECASE


_FLAG_NAMES = {"IGNORECASE", "MULTILINE", "DOTALL", "VERBOSE"}


def _flags_from(names) -> int:
    if not names:
        return 0
    if isinstance(names, int):
        return names
    if isinstance(names, str):
        names = [names]
    out = 0
    for n in names:
        if n in _FLAG_NAMES:
            out |= getattr(re, n)
    return out


# --------------------------------------------------------------------------
# Bundle
# --------------------------------------------------------------------------

class Bundle:
    def __init__(self, root: Path, concepts: list[Concept], version: str | None):
        self.root = root
        self._concepts = concepts
        self.okf_version = version

    # ---- loading ----

    @classmethod
    def load(cls, root: str | Path) -> "Bundle":
        root = Path(root)
        if not root.is_dir():
            raise FileNotFoundError(f"no OKF bundle at {root}")

        version = None
        index = root / "index.md"
        if index.exists():
            front, _ = parse_frontmatter(index.read_text(encoding="utf-8"))
            version = front.get("okf_version")

        concepts: list[Concept] = []
        for path in sorted(root.rglob("*.md")):
            if path.name in RESERVED:
                continue
            rel = "/" + path.relative_to(root).as_posix()
            try:
                front, body = parse_frontmatter(path.read_text(encoding="utf-8"))
            except ValueError as e:
                raise ValueError(f"{rel}: {e}") from e
            # A file with NO frontmatter block at all is plain content (a script,
            # a note, a trace) living inside the bundle — not a concept. Skip it,
            # so content files can never break rule/palette loading at runtime.
            # (okf_validate.py still flags these strictly for §11 conformance.)
            if not front:
                continue
            ctype = (front.get("type") or "").strip()
            if not ctype:
                # Frontmatter present but no type is a real authoring mistake.
                raise ValueError(f"{rel}: frontmatter present but missing required `type` field (OKF §11)")
            concepts.append(Concept(path=rel, type=ctype, front=front, body=body))

        return cls(root, concepts, version)

    # ---- querying ----

    def __iter__(self) -> Iterator[Concept]:
        return iter(self._concepts)

    def __len__(self) -> int:
        return len(self._concepts)

    def concepts(self, ctype: str | None = None) -> list[Concept]:
        if ctype is None:
            return list(self._concepts)
        return [c for c in self._concepts if c.type == ctype]

    def one(self, ctype: str) -> Concept | None:
        found = self.concepts(ctype)
        return found[0] if found else None

    def at(self, path: str) -> Concept | None:
        return next((c for c in self._concepts if c.path == path), None)

    def types(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for c in self._concepts:
            counts[c.type] = counts.get(c.type, 0) + 1
        return dict(sorted(counts.items()))

    # ---- typed accessors ----

    def constraint(self) -> Concept | None:
        """The one rule that outranks every other instruction."""
        return self.one("Overriding Constraint")

    def rules(self, include_deprecated: bool = False) -> list[GateRule]:
        """Every safety rule across every rule set, ready for the gate."""
        out: list[GateRule] = []
        for c in self.concepts("Claim Rule Set"):
            if c.status == "deprecated" and not include_deprecated:
                continue
            for r in c.get("rules") or []:
                if not isinstance(r, dict) or not r.get("pattern"):
                    continue
                out.append(GateRule(
                    id=r.get("id", "unnamed"),
                    severity=r.get("severity", "BLOCK"),
                    pattern=r["pattern"],
                    why=r.get("why", ""),
                    fix=r.get("fix", ""),
                    flags=_flags_from(r.get("flags")),
                ))
        return out

    def arcs(self) -> list[Concept]:
        return self.concepts("Narrative Arc")

    @staticmethod
    def _ordered(concepts: list[Concept]) -> list[Concept]:
        """Sort by an explicit `order` field, falling back to title.

        marketing_config.json cared about order (the anti-repetition logic walks
        the taxonomy), and rglob returns files alphabetically, so an explicit
        `order` is what keeps a generated config identical to the hand-written
        one.
        """
        return sorted(concepts, key=lambda c: (c.get("order", 10_000), c.title))

    def taxonomy(self) -> list[dict]:
        """Content pillars, in the shape marketing_config.json used."""
        out = []
        for c in self._ordered(self.concepts("Content Topic")):
            out.append({
                "topic": c.get("topic") or Path(c.path).stem,
                "angle": c.get("angle") or c.title,
                "description": c.get("description") or "",
            })
        return out

    def competitors(self) -> list[dict]:
        out = []
        for c in self._ordered(self.concepts("Competitor")):
            out.append({
                "name": c.title,
                "x_handle": c.get("x_handle") or "",
                "specialty": c.get("description") or "",
            })
        return out

    def research_config(self) -> dict:
        """subreddits, search_keywords and scrape settings."""
        c = self.one("Research Config")
        if not c:
            return {"subreddits": [], "search_keywords": [], "settings": {}}
        return {
            "subreddits": c.get("subreddits") or [],
            "search_keywords": c.get("search_keywords") or [],
            "settings": c.get("settings") or {},
        }

    def marketing_config(self) -> dict:
        """The whole marketing_config.json, assembled from the bundle."""
        rc = self.research_config()
        return {
            "competitors": self.competitors(),
            "subreddits": rc["subreddits"],
            "search_keywords": rc["search_keywords"],
            "taxonomy": self.taxonomy(),
            "settings": rc["settings"],
        }

    def brand(self) -> dict:
        c = self.one("Brand Palette")
        return dict(c.front) if c else {}

    def channels(self) -> list[Concept]:
        return self.concepts("Channel")

    def facts(self, tier: str | None = None) -> list[Concept]:
        found = self.concepts("Facts Ledger")
        if tier:
            found = [c for c in found if str(c.get("tier", "")).upper() == tier.upper()]
        return found


# --------------------------------------------------------------------------

def default_bundle_path() -> Path:
    """`OKF_BUNDLE` if set, else `okf/` beside the repository root."""
    import os
    env = os.environ.get("OKF_BUNDLE")
    if env:
        return Path(env)
    return Path(__file__).resolve().parents[2] / "okf"


if __name__ == "__main__":
    import json
    b = Bundle.load(default_bundle_path())
    print(json.dumps({
        "root": str(b.root),
        "okf_version": b.okf_version,
        "concepts": len(b),
        "types": b.types(),
        "rules": len(b.rules()),
        "constraint": (b.constraint().title if b.constraint() else None),
    }, indent=2))
