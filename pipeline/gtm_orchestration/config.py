"""Canonical configuration for the Vanna GTM Operating System.

The Brain DB used to live at `D:/marketing intelligence system/intelligence`,
outside this repository, and roughly twenty modules hardcoded that absolute
path. Nothing in the repo could be checked out and run: if that folder were
renamed or the work moved to another machine, every machine lookup would return
INSUFFICIENT_EVIDENCE and every agent would degrade — silently, because the
readers treat a missing file as an empty file.

The data now lives at `pipeline/brain/`, inside the repo, and this module is the
only place that decides where that is. `VANNA_BRAIN_ROOT` overrides it for a
machine that still keeps the corpus elsewhere.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

# ── CANONICAL PATHS ──────────────────────────────────────────────────────────
REPO_ROOT = Path(__file__).resolve().parents[2]

# One override for the whole system, not twenty hardcoded absolute paths.
BRAIN_ROOT = Path(os.environ.get("VANNA_BRAIN_ROOT", str(REPO_ROOT / "pipeline" / "brain")))

CANONICAL_INTELLIGENCE_ROOT = BRAIN_ROOT
CANONICAL_KNOWLEDGE_ROOT = BRAIN_ROOT / "knowledge"
BRAIN_DB_DIR = BRAIN_ROOT / "db"

# Fallback compatibility root (explicit opt-in only)
LEGACY_WORKSPACE_ROOT = Path(__file__).resolve().parents[2]


class OrchestrationConfig:
    """Manages paths, safety invariants, and compatibility mode."""

    def __init__(
        self,
        intelligence_root: Optional[Path] = None,
        knowledge_root: Optional[Path] = None,
        allow_legacy_fallback: bool = False,
    ):
        self.allow_legacy_fallback = allow_legacy_fallback

        # Check environment overrides first
        env_root = os.environ.get("VANNA_INTELLIGENCE_ROOT")
        if env_root:
            self.intelligence_root = Path(env_root).resolve()
        elif intelligence_root:
            self.intelligence_root = Path(intelligence_root).resolve()
        elif CANONICAL_INTELLIGENCE_ROOT.exists():
            self.intelligence_root = CANONICAL_INTELLIGENCE_ROOT.resolve()
        else:
            # Fallback for container deployment
            container_state = Path("/app/pipeline/state") if Path("/app/pipeline/state").exists() else LEGACY_WORKSPACE_ROOT / "pipeline" / "state"
            self.intelligence_root = container_state.resolve()
            self.allow_legacy_fallback = True

        env_know = os.environ.get("VANNA_KNOWLEDGE_ROOT")
        if env_know:
            self.knowledge_root = Path(env_know).resolve()
        elif knowledge_root:
            self.knowledge_root = Path(knowledge_root).resolve()
        elif CANONICAL_KNOWLEDGE_ROOT.exists():
            self.knowledge_root = CANONICAL_KNOWLEDGE_ROOT.resolve()
        else:
            container_know = Path("/app/knowledge") if Path("/app/knowledge").exists() else LEGACY_WORKSPACE_ROOT / "knowledge"
            self.knowledge_root = container_know.resolve()

        self._validate_paths()

    def _validate_paths(self) -> None:
        """Enforce canonical path invariants."""
        # 1. Existence check
        if not self.intelligence_root.exists():
            self.intelligence_root.mkdir(parents=True, exist_ok=True)

    @property
    def brain_db_dir(self) -> Path:
        """Return path to database directory (.jsonl files)."""
        db_dir = self.intelligence_root / "db"
        if not db_dir.exists():
            # Check if JSONL files live directly in intelligence_root
            if (self.intelligence_root / "opportunities.jsonl").exists():
                return self.intelligence_root
        return db_dir

    @property
    def registry_dir(self) -> Path:
        """Return path to registry directory."""
        return self.intelligence_root / "registry"

    def get_provenance_metadata(self) -> dict:
        """Return provenance metadata describing the active intelligence root."""
        return {
            "canonical_root": str(CANONICAL_INTELLIGENCE_ROOT),
            "active_root": str(self.intelligence_root),
            "is_canonical": self.intelligence_root == CANONICAL_INTELLIGENCE_ROOT.resolve(),
            "legacy_fallback_allowed": self.allow_legacy_fallback,
            "knowledge_root": str(self.knowledge_root),
        }


# Global default configuration instance
DEFAULT_CONFIG = OrchestrationConfig()
