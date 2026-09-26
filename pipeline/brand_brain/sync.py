"""Keeping a tenant's brain fresh from its live sources.

A source spec with a `sync` block is fetched on a schedule and re-ingested
incrementally (only changed chunks re-embed). Today that is a docs site that
publishes an `llms.txt` index (docs.vanna.finance serves every page as
markdown), and the tenant's Notion workspace (notion_sync.py).

Run start calls `sync_if_stale`, which does nothing unless the last sync is
older than the source's max age — documentation moves on a release cadence,
not per run.
"""
from __future__ import annotations

import re
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Optional

from pipeline.brand_brain import onboard as O
from pipeline.brand_brain.client import current_tenant

REPO = Path(__file__).resolve().parents[2]
USER_AGENT = "brand-brain-sync/1.0 (+internal research)"


class SyncError(RuntimeError):
    pass


def _get(url: str, host: str, forbidden: tuple[str, ...], timeout: float = 25.0) -> str:
    h = urllib.parse.urlparse(url).netloc.lower()
    if h in forbidden:
        raise SyncError(h + " is not a claim source")
    if h != host:
        raise SyncError("refusing to fetch " + h)
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "replace")


def sync_llms_txt(s: dict) -> dict[str, Any]:
    """Fetch the pages an llms.txt index lists into the source's cache dir."""
    host = s["host"]
    forbidden = tuple(s.get("forbidden_hosts", []))
    cache = REPO / s["cache_dir"]
    cache.mkdir(parents=True, exist_ok=True)
    link = re.compile(r"https://" + re.escape(host) + r"/[A-Za-z0-9/_\-.]+\.md")
    try:
        pages = list(dict.fromkeys(link.findall(_get(s["index_url"], host, forbidden))))
    except Exception as exc:                        # noqa: BLE001 — boundary
        return {"ok": False, "error": str(exc)[:200], "pages": 0}
    prefixes = tuple(s.get("prefixes", []))
    targets = [p for p in pages if not prefixes
               or p.replace("https://" + host, "").startswith(prefixes)] or pages
    targets = targets[:int(s.get("max_pages", 40))]

    def one(url: str) -> bool:
        try:
            body = _get(url, host, forbidden)
        except Exception:                           # noqa: BLE001 — boundary
            return False
        name = url.replace("https://" + host + "/", "").removesuffix(".md").replace("/", "__") + ".md"
        (cache / name).write_text(body, encoding="utf-8")
        return True

    with ThreadPoolExecutor(max_workers=6) as pool:
        got = sum(1 for ok in pool.map(one, targets) if ok)
    return {"ok": got > 0, "pages": got, "listed": len(pages)}


def sync(tenant: Optional[str] = None) -> dict[str, Any]:
    t = tenant or current_tenant()
    spec = O.spec(t)
    out: dict[str, Any] = {}
    for s in spec.get("sync", []):
        if s["kind"] == "llms_txt":
            out[s["name"]] = sync_llms_txt(s)
        elif s["kind"] == "notion":
            out[s["name"]] = _notion(t, s)
    out["ingest"] = O.ingest_knowledge(t)
    from pipeline.brand_brain.client import Brain
    Brain(t).meta("last_sync", str(time.time()))
    return out


def _notion(tenant: str, s: dict) -> dict[str, Any]:
    try:
        from pipeline.brand_brain.notion_sync import sync as notion_sync
        return notion_sync(tenant, authority=int(s.get("authority", 2)))
    except Exception as exc:                        # noqa: BLE001 — the other sources still sync
        return {"ok": False, "error": str(exc)[:200]}


def sync_if_stale(tenant: Optional[str] = None) -> dict[str, Any]:
    t = tenant or current_tenant()
    from pipeline.brand_brain.client import Brain
    # A Notion webhook marked this tenant: sync Notion now, whatever the age.
    try:
        if Brain(t).meta("notion_dirty"):
            spec = O.spec(t)
            s = next((x for x in spec.get("sync", []) if x["kind"] == "notion"), {"authority": 2})
            return {"ok": True, "notion": _notion(t, s)}
    except Exception:                               # noqa: BLE001 — fall through to the age check
        pass
    try:
        spec = O.spec(t)
        max_age = min([int(s.get("max_age_s", 86400)) for s in spec.get("sync", [])] or [86400])
        last = float(Brain(t).meta("last_sync") or 0)
    except Exception as exc:                        # noqa: BLE001 — boundary
        return {"ok": False, "error": str(exc)[:200]}
    if time.time() - last < max_age:
        return {"ok": True, "fresh": True, "age_h": int((time.time() - last) / 3600)}
    return sync(t)
