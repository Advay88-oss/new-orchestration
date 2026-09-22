"""Phase 5: Metaphor Diversity & Concept Family Manager (metaphor_registry.py).

Prevents repetitive visual concepts across consecutive production runs.
Tracks physical concept families:
  1. OPTICAL_REFRACTION: Prisms, spectral filaments, collimated lasers, optical filters.
  2. HYDRODYNAMIC_CONTAINMENT: Laminar flow, pressurized channels, fluid isolation gates.
  3. GYROSCOPIC_EQUILIBRIUM: Dual-axis gimbals, inertial counterweights, dynamic fulcrums.
  4. ELECTROMAGNETIC_DEFLECTION: Magnetic flux barriers, inductive solenoids, plasma shields.
  5. ARCHITECTURAL_MONOLITHIC: Obsidian chambers, hermetic pressure bulkheads, seismic dampers.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

REPO_ROOT = Path("D:/new orchestration")
STATE_DIR = REPO_ROOT / "pipeline" / "state"
REGISTRY_FILE = STATE_DIR / "metaphor_registry.jsonl"

from pipeline.gtm_storage.atomic_store import AtomicJsonlStore


class MetaphorEntry(BaseModel):
    entry_id: str
    concept_family: str
    headline_hook: str
    visual_metaphor: str
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class MetaphorDiversityManager:
    """Ensures consecutive creative blueprints rotate across distinct physical metaphor families."""

    CONCEPT_FAMILIES = [
        "OPTICAL_REFRACTION",
        "HYDRODYNAMIC_CONTAINMENT",
        "GYROSCOPIC_EQUILIBRIUM",
        "ELECTROMAGNETIC_DEFLECTION",
        "ARCHITECTURAL_MONOLITHIC"
    ]

    def __init__(self, registry_file: Optional[Path] = None):
        self.store = AtomicJsonlStore(registry_file or REGISTRY_FILE)

    def select_next_metaphor_family(self) -> str:
        """Selects the least recently used concept family to guarantee visual novelty."""
        recent_entries = self.store.read_all()[-10:]
        recent_families = [e.get("concept_family") for e in recent_entries]

        for fam in self.CONCEPT_FAMILIES:
            if fam not in recent_families:
                return fam

        # If all have been used, pick the one furthest in the past
        for fam in reversed(self.CONCEPT_FAMILIES):
            if fam != recent_families[-1]:
                return fam

        return self.CONCEPT_FAMILIES[0]

    def record_metaphor(
        self,
        concept_family: str,
        headline: str,
        metaphor_text: str
    ) -> MetaphorEntry:
        """Records a newly generated metaphor into persistent history."""
        entry_id = f"MET-{int(datetime.now(timezone.utc).timestamp())}"
        entry = MetaphorEntry(
            entry_id=entry_id,
            concept_family=concept_family,
            headline_hook=headline,
            visual_metaphor=metaphor_text
        )
        self.store.append(entry.model_dump())
        return entry
