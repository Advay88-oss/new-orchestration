#!/usr/bin/env python3
"""Generate marketing_config.json from the OKF bundle.

The orchestrators read marketing_config.json. This makes the OKF bundle the
source of truth for it: edit the bundle's taxonomy, competitors or research
config, run this, and the orchestrators see the change — without either script
being rewritten.

    python pipeline/scripts/okf_sync_config.py            # write the config
    python pipeline/scripts/okf_sync_config.py --check    # CI: fail if stale

--check exits non-zero when the committed config differs from what the bundle
would produce, so a bundle edit that was never synced is caught.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from okf_loader import Bundle, default_bundle_path   # noqa: E402

REPO = HERE.parents[1]
CONFIG = REPO / "pipeline" / "config" / "marketing_config.json"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--bundle", type=Path, default=None)
    ap.add_argument("--out", type=Path, default=CONFIG)
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()

    root = args.bundle or default_bundle_path()
    bundle = Bundle.load(root)
    generated = bundle.marketing_config()
    text = json.dumps(generated, indent=2, ensure_ascii=False) + "\n"

    if args.check:
        if not args.out.exists():
            print(f"{args.out} does not exist")
            return 1
        current = args.out.read_text(encoding="utf-8")
        # Compare by value, not by formatting.
        if json.loads(current) != generated:
            print("marketing_config.json is stale relative to the OKF bundle.")
            print("Re-run: python pipeline/scripts/okf_sync_config.py")
            return 1
        print("marketing_config.json matches the OKF bundle.")
        return 0

    args.out.write_text(text, encoding="utf-8")
    try:
        shown = args.out.resolve().relative_to(REPO)
    except ValueError:
        shown = args.out
    print(f"wrote {shown} from {root}")
    print(f"  taxonomy   : {len(generated['taxonomy'])} topics")
    print(f"  competitors: {len(generated['competitors'])}")
    print(f"  subreddits : {len(generated['subreddits'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
