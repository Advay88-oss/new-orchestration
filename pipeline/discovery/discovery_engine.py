"""Autonomous Discovery Engine (discovery_engine.py).

Implements the permanent Discovery Mode rules:
  A1: Exclude what is already covered (seen sets)
  A2: Rotate discovery axis (code-driven rotation)
  A3: Strict evidence schema & derived_by tracking
  A4: Real-time HTTP HEAD link verification & quarantine
  A5: Discovery ledger sync to registry/discovery_log.jsonl
"""

from __future__ import annotations

import json
import os
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
from pipeline.gtm_orchestration.config import BRAIN_DB_DIR, BRAIN_ROOT, CANONICAL_KNOWLEDGE_ROOT

REPO_ROOT = Path("D:/new orchestration")
REGISTRY_DIR = REPO_ROOT / "registry"
DISCOVERY_LOG = REGISTRY_DIR / "discovery_log.jsonl"
SNAPSHOT_PATH = REGISTRY_DIR / "defillama_snapshot.json"
BRAIN_DB_DIR = BRAIN_DB_DIR

AXES = ["mechanism", "chain", "category_adjacent", "size_band", "recency", "publishing"]

SUB_AXIS_CHAINS = ["stellar", "solana", "base", "sui", "ton", "aptos", "cosmos"]
SUB_AXIS_CATEGORIES = [
    "Collateral Markets", "Secondary Debt Markets", "Basis Trading",
    "RWA Lending", "Synthetics", "Interest Rate Derivatives"
]
SUB_AXIS_SIZE_BANDS = ["<5M", "5-50M", "50-200M", "200M-1B"]
SUB_AXIS_RECENCY = ["6m", "12m", "24m"]


def load_all_registry_players() -> Set[str]:
    """Loads all player_ids already documented across the workspace and canonical Brain DB."""
    seen: Set[str] = set()

    # 1. Workspace registry files
    if REGISTRY_DIR.exists():
        for f in REGISTRY_DIR.glob("*.jsonl"):
            try:
                for line in f.read_text(encoding="utf-8").splitlines():
                    if line.strip():
                        rec = json.loads(line)
                        pid = rec.get("player_id") or rec.get("entity_id")
                        if pid:
                            seen.add(pid.lower().strip())
            except Exception:
                pass

    # 2. Canonical Brain DB
    if BRAIN_DB_DIR.exists():
        for f in BRAIN_DB_DIR.glob("*.jsonl"):
            try:
                for line in f.read_text(encoding="utf-8").splitlines():
                    if line.strip():
                        rec = json.loads(line)
                        pid = rec.get("player_id") or rec.get("entity_id")
                        if pid:
                            seen.add(pid.lower().strip())
            except Exception:
                pass

    # 3. Competitor docs if present
    comp_dir = REPO_ROOT / "pipeline" / "system1_extracted" / "okf" / "competitors"
    if comp_dir.exists():
        for f in comp_dir.glob("*.md"):
            if f.name != "index.md":
                seen.add(f.stem.lower().strip())

    return seen


def read_discovery_log() -> List[Dict[str, Any]]:
    """Reads the discovery log ledger."""
    if not DISCOVERY_LOG.exists():
        return []
    records = []
    for line in DISCOVERY_LOG.read_text(encoding="utf-8").splitlines():
        if line.strip():
            try:
                records.append(json.loads(line.strip()))
            except Exception:
                pass
    return records


def next_axis() -> str:
    """Axis rotation is code, not judgment. Full cycle across canonical axes, then restart."""
    log = read_discovery_log()
    if not log:
        return "chain:stellar"  # Canonical first target

    used_top_axes = [r["discovery_axis"].split(":")[0] for r in log[-len(AXES):]]
    unused = [a for a in AXES if a not in used_top_axes]
    top_axis = unused[0] if unused else AXES[0]

    if top_axis == "chain":
        # Cycle through chains
        used_chains = [r["discovery_axis"].split(":")[1] for r in log if r["discovery_axis"].startswith("chain:")]
        unused_chains = [c for c in SUB_AXIS_CHAINS if c not in used_chains[-len(SUB_AXIS_CHAINS):]]
        ch = unused_chains[0] if unused_chains else SUB_AXIS_CHAINS[0]
        return f"chain:{ch}"

    if top_axis == "category_adjacent":
        used_cats = [r["discovery_axis"].split(":", 1)[1] for r in log if r["discovery_axis"].startswith("category_adjacent:")]
        unused_cats = [c for c in SUB_AXIS_CATEGORIES if c not in used_cats[-len(SUB_AXIS_CATEGORIES):]]
        cat = unused_cats[0] if unused_cats else SUB_AXIS_CATEGORIES[0]
        return f"category_adjacent:{cat}"

    return top_axis


def verify_url_head(url: str, timeout: float = 4.0) -> Tuple[bool, int, str]:
    """Verifies that a URL resolves with status < 400 using HTTP HEAD/GET."""
    if not url or not url.startswith(("http://", "https://")):
        return False, 0, "NO_URL"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) VannaDiscoveryProbe/2.0"
    }
    
    # Try HEAD first
    try:
        req = urllib.request.Request(url, headers=headers, method="HEAD")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            code = resp.status
            if code < 400:
                return True, code, "CONFIRMED_200"
    except urllib.error.HTTPError as e:
        if e.code < 400:
            return True, e.code, f"CONFIRMED_{e.code}"
        # Some servers reject HEAD with 403 or 405 but allow GET
        if e.code in (403, 405):
            pass
        else:
            return False, e.code, f"DEAD_{e.code}"
    except Exception:
        pass

    # Fallback to GET with Range 0-100 bytes
    try:
        req = urllib.request.Request(url, headers=dict(headers, Range="bytes=0-100"))
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            code = resp.status
            return (code < 400), code, f"CONFIRMED_{code}"
    except urllib.error.HTTPError as e:
        return (e.code < 400), e.code, f"STATUS_{e.code}"
    except Exception as e:
        return False, 0, f"DEAD_{str(e)[:30]}"


def assert_discovery_novelty(results: List[Dict[str, Any]], seen: Set[str], axis: str) -> List[Dict[str, Any]]:
    """Asserts that the discovery run surfaces players not already in the registry."""
    new = [r for r in results if r["player_id"].lower() not in seen]
    if not new:
        raise ValueError(
            f"Zero new players on axis '{axis}'. "
            "Axis exhausted or exclusion filter not applied."
        )
    return new


def assert_evidence_complete(records: List[Dict[str, Any]]) -> List[Tuple[str, str]]:
    """Asserts that all OBSERVED records carry sources and non-NOT_RELEVANT carry why_evidence."""
    bad = []
    for r in records:
        if r["evidence_tier"] == "OBSERVED" and not r.get("tvl_source"):
            bad.append((r["player_id"], "OBSERVED without source"))
        if r["relevance"] != "NOT_RELEVANT" and not r.get("why_evidence"):
            bad.append((r["player_id"], "relevance claimed without evidence"))
    return bad


def append_discovery_log(
    discovery_axis: str,
    candidates_screened: int,
    already_seen_excluded: int,
    new_players_found: int,
    relevant: int,
    urls_checked: int,
    urls_resolved: int,
    unknown_fields: int
) -> Dict[str, Any]:
    """Appends entry to registry/discovery_log.jsonl."""
    REGISTRY_DIR.mkdir(parents=True, exist_ok=True)
    entry = {
        "run_date": datetime.now(timezone.utc).isoformat(),
        "discovery_axis": discovery_axis,
        "candidates_screened": candidates_screened,
        "already_seen_excluded": already_seen_excluded,
        "new_players_found": new_players_found,
        "relevant": relevant,
        "urls_checked": urls_checked,
        "urls_resolved": urls_resolved,
        "unknown_fields": unknown_fields
    }
    with open(DISCOVERY_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")
    return entry
