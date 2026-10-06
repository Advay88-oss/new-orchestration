"""The one door the dashboard uses for brand-brain actions.

Profile edits, Notion, inspiration brands and competitor analysis used to be
four separate Python commands. The dashboard starts this module, which calls
the same functions the brain already uses. The MCP server exposes the matching
reads (list_outcomes, list_rejected_posters).

    python -m pipeline.brand_brain.mcp_call profile|approve|save ...
    python -m pipeline.brand_brain.mcp_call notion <notion_oauth args>
    python -m pipeline.brand_brain.mcp_call inspiration <inspiration args>
    python -m pipeline.brand_brain.mcp_call competitors <analyzer args>
    python -m pipeline.brand_brain.mcp_call outcomes [--tenant=]

Each call appends one line to pipeline/state/brain_actions.jsonl: the tenant,
the action and when. Arguments that carry a token or a profile are not written.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
AUDIT = REPO / "pipeline" / "state" / "brain_actions.jsonl"


def audit(action: str, tenant: str = "", ok: bool = True) -> None:
    AUDIT.parent.mkdir(parents=True, exist_ok=True)
    row = {"at": datetime.now(timezone.utc).isoformat(), "action": action,
           "tenant": tenant or None, "ok": ok}
    with AUDIT.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row) + "\n")


def _tenant_flag(argv: list[str]) -> str:
    flagged = next((x.split("=", 1)[1] for x in argv if x.startswith("--tenant=")),
                   next((argv[i + 1] for i, x in enumerate(argv[:-1]) if x == "--tenant"), ""))
    if flagged:
        return flagged
    # inspiration add|refresh|remove <tenant> <arg>
    if argv and argv[0] == "inspiration" and len(argv) > 2:
        return argv[2]
    return ""


def main(argv: list[str]) -> int:
    cmd = argv[0] if argv else ""
    tenant = _tenant_flag(argv)
    try:
        code = _run(argv)
    except SystemExit as exc:
        code = exc.code if isinstance(exc.code, int) else 1
        audit(cmd or "overview", tenant, code == 0)
        raise
    except Exception:
        audit(cmd or "overview", tenant, False)
        raise
    audit(cmd or "overview", tenant, code == 0)
    return code


def _run(argv: list[str]) -> int:
    cmd = argv[0] if argv else ""
    if cmd in ("profile", "approve", "save", "search", "overview", "tenants"):
        from pipeline.brand_brain.dashboard import main as dash
        return dash(argv)
    if cmd == "outcomes":
        from pipeline.brand_brain.client import Brain, current_tenant
        tenant = _tenant_flag(argv) or current_tenant()
        sys.stdout.write(json.dumps({"ok": True, "outcomes": Brain(tenant).outcomes(100)},
                                    ensure_ascii=False, default=str))
        return 0
    if cmd == "notion":
        from pipeline.brand_brain.notion_oauth import main as notion
        notion(argv[1:])
        return 0
    if cmd == "inspiration":
        from pipeline.brand_brain.inspiration import main as inspiration
        return inspiration(argv[1:])
    if cmd == "competitors":
        from pipeline.brand_brain.analyzer import competitors_main
        competitors_main(argv[1:])
        return 0
    sys.stdout.write(json.dumps({"ok": False, "error": "unknown brain action " + cmd}))
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
