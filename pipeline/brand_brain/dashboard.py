"""What the dashboard's Brand Brain view shows, as one JSON document.

    python -m pipeline.brand_brain.dashboard overview [tenant]
    python -m pipeline.brand_brain.dashboard search "query" [tenant]

Read-only. The view never writes to the brain; profile approval stays a
deliberate founder action (`python -m pipeline.brand_brain approve`).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from pipeline.brand_brain import store as S
from pipeline.brand_brain.client import Brain, current_tenant

REPO = Path(__file__).resolve().parents[2]
RUNS = REPO / "pipeline" / "state" / "gtm_runs"


def _latest_harvest() -> dict[str, Any]:
    for d in sorted(RUNS.glob("GTM-*"), reverse=True):
        f = d / "harvest.json"
        if f.exists():
            try:
                h = json.loads(f.read_text(encoding="utf-8"))
                return {"run_id": d.name, "scraped_at": h.get("scraped_at"),
                        "sources": h.get("sources") or {}, "total": h.get("total_signals")}
            except Exception:                       # noqa: BLE001 — try the one before
                continue
    return {}


def overview(tenant: str) -> dict[str, Any]:
    if not S.exists(tenant):
        return {"ok": False, "error": "no brain for tenant " + tenant
                + " — run: python -m pipeline.brand_brain init " + tenant}
    b = Brain(tenant)
    p = b.get_brand_profile()
    with b._db() as con:
        images = [dict(r) for r in con.execute(
            "SELECT id, path, kind, caption, style_tags, score FROM images ORDER BY kind, score DESC")]
    for im in images:
        im["style_tags"] = json.loads(im["style_tags"] or "[]")
    try:
        from pipeline.gtm_learning.source_learning import posteriors
        record = {k: v for k, v in posteriors().items() if ":" not in k}
    except Exception:                               # noqa: BLE001 — boundary
        record = {}
    try:
        from pipeline.gtm_learning.analyst_accuracy import record as acc
        accuracy = acc()
    except Exception:                               # noqa: BLE001 — boundary
        accuracy = {}
    return {
        "ok": True,
        "tenant": tenant,
        "tenants": S.tenants(),
        "stats": b.stats(),
        "profile": {
            "version": p.get("_version"), "status": p.get("_status"),
            "company": p.get("company", {}),
            "voice": {k: (p.get("voice") or {}).get(k) for k in ("tone", "do", "dont", "cta")},
            "palette": (p.get("visual") or {}).get("palette", {}),
            "palette_candidates": (p.get("visual") or {}).get("palette_candidates", []),
            "fonts": (p.get("visual") or {}).get("fonts", {}),
            "true_figures": (p.get("claims") or {}).get("true_figures", []),
            "partners": p.get("partners", {}),
            "competitors": [c.get("name") for c in p.get("competitors", [])],
            "pillars": p.get("pillars", []),
            "open_questions": p.get("open_questions", []),
        },
        "versions": b.profile_versions(),
        "whats_new": b.get_whats_new(None, 20),
        "competitor_patterns": b.get_competitor_patterns(None, 30),
        "images": images,
        "sources": {"last_scrape": _latest_harvest(), "record": record},
        "analyst_accuracy": accuracy,
    }


def search(query: str, tenant: str) -> dict[str, Any]:
    if not S.exists(tenant):
        return {"ok": False, "error": "no brain for tenant " + tenant}
    hits = Brain(tenant).search_knowledge(query, k=8)
    for h in hits:
        h["text"] = h["text"][:900]
        h["parent"] = (h.get("parent") or "")[:600] or None
    return {"ok": True, "query": query, "hits": hits}


def profile_version(version: int | None, tenant: str) -> dict[str, Any]:
    """One profile version in full (the newest when no version is given)."""
    b = Brain(tenant)
    with b._db() as con:
        row = (con.execute("SELECT * FROM profile_versions WHERE version=?", (version,)).fetchone()
               if version else
               con.execute("SELECT * FROM profile_versions ORDER BY version DESC LIMIT 1").fetchone())
    if not row:
        return {"ok": False, "error": "no such version"}
    return {"ok": True, "version": row["version"], "status": row["status"], "note": row["note"],
            "profile": json.loads(row["profile"])}


def approve(version: int, tenant: str) -> dict[str, Any]:
    """The founder's approval of one version; its facts are re-indexed."""
    from pipeline.brand_brain.onboard import index_profile
    b = Brain(tenant)
    if not any(v["version"] == version for v in b.profile_versions()):
        return {"ok": False, "error": "no such version"}
    b.approve_profile(version, note="approved on the dashboard")
    return {"ok": True, "approved": version, "reindexed": index_profile(tenant)}


def save(path: str, note: str, tenant: str) -> dict[str, Any]:
    """An edited profile, saved as a new DRAFT (approval is a separate step)."""
    from pipeline.brand_brain.onboard import index_profile
    prof = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(prof, dict) or not isinstance(prof.get("company"), dict):
        return {"ok": False, "error": "a profile needs at least a 'company' object"}
    v = Brain(tenant).save_profile(prof, status="draft", source="dashboard edit", note=note[:300])
    return {"ok": True, "version": v, "reindexed": index_profile(tenant)}


def main(argv: list[str]) -> int:
    # "--tenant=<id>" anywhere selects the tenant; the rest is positional.
    tenant = next((x.split("=", 1)[1] for x in argv if x.startswith("--tenant=")), None) or current_tenant()
    argv = [x for x in argv if not x.startswith("--tenant=")]
    cmd = argv[0] if argv else "overview"
    if cmd == "profile":
        out = profile_version(int(argv[1]) if len(argv) > 1 and argv[1].isdigit() else None, tenant)
        sys.stdout.write(json.dumps(out, ensure_ascii=False, default=str))
        return 0
    if cmd == "approve":
        out = approve(int(argv[1]), tenant)
        sys.stdout.write(json.dumps(out, ensure_ascii=False, default=str))
        return 0
    if cmd == "save":
        out = save(argv[1], argv[2] if len(argv) > 2 else "", tenant)
        sys.stdout.write(json.dumps(out, ensure_ascii=False, default=str))
        return 0
    if cmd == "search":
        out = search(argv[1] if len(argv) > 1 else "", argv[2] if len(argv) > 2 else tenant)
    elif cmd == "tenants":
        out = {"ok": True, "tenants": S.tenants()}
    else:
        out = overview(argv[1] if len(argv) > 1 else tenant)
    sys.stdout.write(json.dumps(out, ensure_ascii=False, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
