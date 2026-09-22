#!/usr/bin/env python3
"""RETIRED — shim onto the v2 pipeline.

The original is preserved verbatim at `run_autonomous_gtm_master.legacy.py`.
It is kept for reference only and must not be run: the 2026-09-21 audit found
that of its thirteen "agents", ten were rule tables or literal dicts, it never
invoked the claim-safety gate, it wrote fabricated receipt URLs and a hardcoded
`delivered_to_telegram: True`, and it accounted for spend by inventing token
counts from wall-clock time.

Everything that called this file now runs `core.pipeline`, which declares which
stages are agents, journals every stage, and cannot report a success it did not
achieve.

    python -m core.pipeline --directive "..."      # direct
    python -m core.worker                          # queue-driven (preferred)
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from core.pipeline import run_pipeline  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description="RETIRED shim -> core.pipeline")
    ap.add_argument("--directive", type=str, default="")
    ap.add_argument("--continuous", action="store_true",
                    help="not supported here; use a supervised worker instead")
    ap.add_argument("--interval", type=int, default=3600)
    a = ap.parse_args()

    if a.continuous:
        print("[retired] --continuous is not supported. A bare in-process loop has no\n"
              "          supervisor, so the schedule dies silently with the process.\n"
              "          Run `python -m core.worker` under Task Scheduler/systemd instead.",
              file=sys.stderr)
        return 2

    print("[retired] run_autonomous_gtm_master.py now delegates to core.pipeline; "
          "the original is at run_autonomous_gtm_master.legacy.py", file=sys.stderr)
    summary = run_pipeline(a.directive)
    print(json.dumps(summary, indent=2, default=str))
    return 0 if summary.get("status") in ("ok", "degraded") else 1


if __name__ == "__main__":
    raise SystemExit(main())
