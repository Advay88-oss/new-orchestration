#!/usr/bin/env python3
"""Write a permanent GTM trace for a post — how the GTM was applied at generation time.

The trace freezes the state that shaped the post (coordinates, learned signal,
gate result, doctrine rules) at the moment it was generated, so "how was GTM
applied" stays checkable even after live signals change. This is the durable
record the manual traces were standing in for.

    OKF_BUNDLE=okf-auri python pipeline/scripts/gtm_trace.py --draft <draft.json> --tenant auri

The draft JSON should carry the coordinate fields (doctrine rule 5):
  audience, funnel_stage, objective, cta, campaign_type, arc, trend_id, final_hook, body
Missing fields are recorded as "UNSPECIFIED" rather than invented (honesty rule).
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(HERE))
import learning as L  # noqa: E402


def bundle_for(tenant: str) -> Path:
    okf_root = REPO / "okf" if (REPO / "okf").exists() else REPO / "pipeline" / "system1_extracted" / "okf"
    return okf_root if tenant == "vanna" else REPO / f"okf-{tenant}"


def gate(draft_body: str, bundle: Path) -> dict:
    import os
    tmp = REPO / "pipeline" / "state" / "drafts" / "_trace_gate.json"
    tmp.write_text(json.dumps({"text": draft_body, "platform": "x"}), encoding="utf-8")
    env = dict(os.environ, OKF_BUNDLE=str(bundle), PYTHONIOENCODING="utf-8")
    r = subprocess.run([sys.executable, str(HERE / "claim_safety_gate.py"), "--file", str(tmp)],
                       capture_output=True, text=True, env=env)
    try:
        return json.loads(r.stdout)
    except Exception:
        return {"pass": None, "rules_source": "ERROR", "rule_count": 0, "block_count": 0}


def field(d: dict, key: str) -> str:
    return str(d.get(key) or "UNSPECIFIED")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--draft", type=Path, required=True)
    ap.add_argument("--tenant", required=True)
    ap.add_argument("--launch", default="2026-launch")
    args = ap.parse_args()

    d = json.loads(args.draft.read_text(encoding="utf-8"))
    pid = d.get("id") or d.get("draft_id") or args.draft.stem
    bundle = bundle_for(args.tenant)
    body = d.get("final_body") or d.get("body", "")
    hook = d.get("final_hook") or ""

    g = gate(body, bundle)
    src = g.get("rules_source", "?")
    src_short = src.split("\\")[-1].split("/")[-1] if src not in ("builtin", "ERROR") else src

    # snapshot the learned signal AT generation time (frozen into the trace)
    brief = L.learning_brief().strip() or "(no learned signal at generation time)"
    hook_type = L.hook_type(hook)
    theme = L.theme_bucket(field(d, "arc"), hook)

    stamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    trace = f"""# GTM Trace — {pid}
_Frozen at generation time: {stamp}. This records how GTM was applied; it does
not change when live signals later change._

## Coordinates (doctrine rule 5 — every asset tagged)
- Audience: {field(d, 'audience')}
- Funnel stage: {field(d, 'funnel_stage')}
- Objective: {field(d, 'objective')}
- CTA: {field(d, 'cta')}
- Campaign type: {field(d, 'campaign_type')}
- Arc: {field(d, 'arc')}

## Grounding (doctrine rules 1-2 — real research, causal)
- Trend / source: {field(d, 'trend_id')}
- Hook: "{hook}"

## Learned signal applied (loop §6 -> INSIGHTS), frozen
- Hook type of this post: {hook_type}
- Theme of this post: {theme}
- Signal in effect at generation:
```
{brief}
```

## Gate (claim safety, per-tenant)
- pass: {g.get('pass')} | source: {src_short} | rules: {g.get('rule_count')} | blocks: {g.get('block_count')}

## Post body (as gated)
> {body}
"""

    out_dir = bundle / "launches" / args.launch / "traces"
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"trace-{pid}.md"
    out.write_text(trace, encoding="utf-8")
    print(f"wrote {out.relative_to(REPO)}")
    print(f"  {args.tenant} | gate {src_short} {g.get('rule_count')} rules, {g.get('block_count')} blocks | hook={hook_type} theme={theme}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
