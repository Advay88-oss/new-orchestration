"""Move synthetic rows out of the evidence the agents read.

Rows that were never observed — the made-up "liquidation telemetry" signal,
TVL readings that were the seeded cache values, the fixed gas figure on
Horizon fee rows, and posts marked PUBLISHED by a testnet simulation — were
stored next to real evidence with source_type PRIMARY_SOURCE_OBSERVED and
confidence HIGH. They go to a quarantine file beside the store, each with the
reason, so nothing is lost and nothing synthetic is read as fact.

    python -m pipeline.scripts.quarantine_evidence            # report only
    python -m pipeline.scripts.quarantine_evidence --apply    # rewrite the stores

Idempotent: a second run finds nothing to move.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "brain" / "db" / "evidence.jsonl"
PUBLISHED = ROOT / "state" / "posts_published.jsonl"

# The values the old code seeded its cache with; a row carrying one exactly
# reported the seed, not a reading.
_SEEDED = ("149772668.26", "1202219.0")


def _why(row: dict) -> Optional[str]:
    text = json.dumps(row)
    if str(row.get("signal_id", "")).startswith("SIG-MEV-DEFENSE") or "Flashbots Telemetry" in text:
        return "synthetic liquidation-telemetry signal (fixed figures, never observed)"
    if row.get("derivation_provenance") == "CACHED_SNAPSHOT" or any(v in text for v in _SEEDED):
        return "seeded cache value reported as a reading"
    if "SIMULAT" in text.upper():
        return "simulated testnet record, not a real publication"
    return None


def _clean(row: dict) -> dict:
    data = row.get("data")
    if isinstance(data, dict):
        # A constant the poller added to every live fee reading.
        for k in ("deterministic_gas_xlm", "soroban_protocol_version", "composable_layer", "routing_type"):
            data.pop(k, None)
    return row


def run(path: Path, apply: bool) -> dict:
    if not path.exists():
        return {"file": str(path), "missing": True}
    keep, moved, cleaned = [], [], 0
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        why = _why(row)
        if why:
            moved.append({**row, "_quarantined": why,
                          "_quarantined_at": datetime.now(timezone.utc).isoformat()})
            continue
        before = json.dumps(row, sort_keys=True)
        row = _clean(row)
        cleaned += before != json.dumps(row, sort_keys=True)
        keep.append(row)
    if apply and (moved or cleaned):
        from pipeline.ops.atomic import write_text
        q = path.with_name(path.stem + "_quarantine.jsonl")
        with q.open("a", encoding="utf-8") as f:
            for r in moved:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        write_text(path, "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in keep))
    return {"file": str(path), "kept": len(keep), "moved": len(moved), "cleaned": cleaned,
            "reasons": sorted({m["_quarantined"] for m in moved})}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    for p in (EVIDENCE, PUBLISHED):
        print(json.dumps(run(p, args.apply)))


if __name__ == "__main__":
    main()
