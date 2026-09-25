"""Brain CLI.

    python -m pipeline.brand_brain init vanna             create + fill tenant #1
    python -m pipeline.brand_brain ingest vanna           re-ingest knowledge (incremental)
    python -m pipeline.brand_brain images vanna           caption + embed new images
    python -m pipeline.brand_brain competitors vanna      rebuild competitor patterns
    python -m pipeline.brand_brain stats vanna
    python -m pipeline.brand_brain search vanna "health factor liquidation"
    python -m pipeline.brand_brain refs vanna "isolated margin accounts"
    python -m pipeline.brand_brain profile vanna
    python -m pipeline.brand_brain approve vanna VERSION
"""
from __future__ import annotations

import json
import sys

from pipeline.brand_brain import onboard as O
from pipeline.brand_brain.client import Brain


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(__doc__)
        return 1
    cmd, tenant, rest = argv[0], argv[1], argv[2:]
    if cmd == "init":
        out = O.init(tenant)
    elif cmd == "ingest":
        out = O.ingest_knowledge(tenant)
    elif cmd == "images":
        out = O.ingest_images(tenant)
    elif cmd == "competitors":
        out = O.build_competitor_patterns(tenant)
    elif cmd == "stats":
        out = Brain(tenant).stats()
    elif cmd == "search":
        out = [{k: (v[:220] if isinstance(v, str) else v) for k, v in r.items() if k != "parent"}
               for r in Brain(tenant).search_knowledge(" ".join(rest), k=6)]
    elif cmd == "refs":
        out = Brain(tenant).get_visual_refs(" ".join(rest), n=4)
    elif cmd == "profile":
        out = Brain(tenant).get_brand_profile()
    elif cmd == "approve":
        Brain(tenant).approve_profile(int(rest[0]))
        out = Brain(tenant).profile_versions()
    else:
        print(__doc__)
        return 1
    print(json.dumps(out, indent=2, ensure_ascii=False, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
