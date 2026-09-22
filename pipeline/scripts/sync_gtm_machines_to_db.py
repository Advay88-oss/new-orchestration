#!/usr/bin/env python3
"""Syncs all 10 GTM Machines from the authoritative library into the canonical database table.
Fixes Blocker 6 (Database Desynchronization).
"""

from __future__ import annotations

import json
from pathlib import Path
import sys

REPO_ROOT = Path("D:/new orchestration")
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

DB_MACHINES_FILE = BRAIN_DB_DIR / "gtm_machines.jsonl"

from pipeline.gtm_machines.machine_library import GTMMachineLibrary
from pipeline.gtm_orchestration.config import BRAIN_DB_DIR, BRAIN_ROOT, CANONICAL_KNOWLEDGE_ROOT

def sync_machines():
    print("▶ Syncing authoritative GTM Machines to canonical DB...")
    lib = GTMMachineLibrary()
    machines = lib.list_machines()

    lines = []
    for m in machines:
        data = m.model_dump()
        lines.append(json.dumps(data))

    DB_MACHINES_FILE.parent.mkdir(parents=True, exist_ok=True)
    DB_MACHINES_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"✅ Successfully synchronized {len(machines)} GTM machines to {DB_MACHINES_FILE}.")

if __name__ == "__main__":
    sync_machines()
