"""Notion live sync — the architecture's Phase 3.

The brain stays fresh from the company's Notion without an agent ever reading
Notion: a background sync pulls what changed into the knowledge base and turns
real changes into dated What's new events.

  change detector  the Notion REST API (an internal integration token,
                   NOTION_TOKEN; the architecture's OAuth public integration
                   is the multi-tenant form of the same calls), pages sorted by
                   last_edited_time and fetched only when edited since the last
                   sync. Pages no longer shared or in the trash are tombstoned.
  clean + chunk    blocks rendered to markdown, heading-aware chunks; only the
                   chunks whose text changed are re-embedded.
  classifier       for each page that changed, the model compares the previous
                   text with the new one: feature_launch, factual_update or
                   noise (typos, internal todos). The first two become dated
                   What's new events; noise is not news.
  triggers         run start (`sync.sync_if_stale`), the daily cadence of that
                   check, and Notion webhooks (the dashboard's signed endpoint
                   marks the tenant for sync).

The first sync is a baseline: it imports everything and creates events only
for pages created in the last 14 days, so an initial import does not flood
What's new.

    python -m pipeline.brand_brain.notion_sync vanna
"""
from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable, Optional

from pipeline.brand_brain import store as S
from pipeline.brand_brain.chunking import chunk_markdown
from pipeline.brand_brain.client import Brain

API = "https://api.notion.com/v1/"
VERSION = "2022-06-28"
AGENT = "BRAIN_notion"


def _token() -> Optional[str]:
    from pipeline.intelligence_stream.social_and_docs_collector import _env
    return _env("NOTION_TOKEN")


class Notion:
    """The few Notion REST calls the sync needs. `http` is swappable for tests."""

    def __init__(self, token: str, http: Optional[Callable[[str, str, Optional[dict]], dict]] = None):
        self.token = token
        self.http = http or self._http

    def _http(self, method: str, path: str, body: Optional[dict]) -> dict:
        req = urllib.request.Request(API + path, method=method,
                                     data=json.dumps(body).encode() if body is not None else None,
                                     headers={"Authorization": "Bearer " + self.token,
                                              "Notion-Version": VERSION,
                                              "Content-Type": "application/json"})
        for attempt in range(4):
            try:
                with urllib.request.urlopen(req, timeout=30) as r:
                    return json.load(r)
            except urllib.error.HTTPError as e:
                if e.code == 429 and attempt < 3:       # rate limit: back off as told
                    time.sleep(float(e.headers.get("Retry-After") or 1.5))
                    continue
                raise
        raise RuntimeError("notion rate-limited")

    def pages(self) -> list[dict]:
        """Every page shared with the integration, most recently edited first."""
        out, cursor = [], None
        while True:
            body = {"filter": {"property": "object", "value": "page"}, "page_size": 100,
                    "sort": {"direction": "descending", "timestamp": "last_edited_time"}}
            if cursor:
                body["start_cursor"] = cursor
            r = self.http("POST", "search", body)
            out += r.get("results", [])
            if not r.get("has_more"):
                return out
            cursor = r.get("next_cursor")

    def blocks(self, block_id: str, depth: int = 0) -> list[dict]:
        out, cursor = [], None
        while True:
            q = "?page_size=100" + ("&start_cursor=" + cursor if cursor else "")
            r = self.http("GET", "blocks/" + block_id + "/children" + q, None)
            for b in r.get("results", []):
                out.append(b)
                if b.get("has_children") and depth < 3 and b.get("type") != "child_page":
                    b["_children"] = self.blocks(b["id"], depth + 1)
            if not r.get("has_more"):
                return out
            cursor = r.get("next_cursor")


def _text(rich: list[dict]) -> str:
    return "".join(t.get("plain_text", "") for t in rich or [])


def title_of(page: dict) -> str:
    for prop in (page.get("properties") or {}).values():
        if prop.get("type") == "title":
            return _text(prop.get("title")) or "Untitled"
    return "Untitled"


def to_markdown(blocks: list[dict], indent: str = "") -> str:
    lines = []
    for b in blocks:
        t = b.get("type", "")
        data = b.get(t) or {}
        txt = _text(data.get("rich_text"))
        if t == "heading_1":
            lines.append("\n# " + txt)
        elif t == "heading_2":
            lines.append("\n## " + txt)
        elif t == "heading_3":
            lines.append("\n### " + txt)
        elif t == "bulleted_list_item":
            lines.append(indent + "- " + txt)
        elif t == "numbered_list_item":
            lines.append(indent + "1. " + txt)
        elif t == "to_do":
            lines.append(indent + ("- [x] " if data.get("checked") else "- [ ] ") + txt)
        elif t == "quote":
            lines.append("> " + txt)
        elif t == "callout":
            lines.append("> " + txt)
        elif t == "code":
            lines.append("```\n" + txt + "\n```")
        elif t == "table_row":
            lines.append("| " + " | ".join(_text(c) for c in data.get("cells", [])) + " |")
        elif txt:
            lines.append(indent + txt)
        if b.get("_children"):
            lines.append(to_markdown(b["_children"], indent + "  "))
    return "\n".join(lines).strip()


def classify(title: str, before: str, after: str) -> dict[str, Any]:
    """feature_launch | factual_update | noise, with a one-line summary."""
    from pipeline.gtm_os import agent_runtime as R
    out = R.brain_json(
        "A page in the company's Notion changed. Classify the change.\n"
        "feature_launch: something new is available or shipped. factual_update: a fact, figure, "
        "partner, date or status changed. noise: wording, typos, formatting, internal todos, drafts.\n\n"
        "PAGE: " + title + "\n\nBEFORE:\n" + (before[:6000] or "(new page)") + "\n\nAFTER:\n" + after[:6000]
        + '\n\nReturn JSON: {"kind": "feature_launch"|"factual_update"|"noise", '
          '"title": str (under 12 words, what changed), "detail": str (one sentence, from the page only)}',
        agent=AGENT, role="reasoning", temperature=0.0, max_output_tokens=1024,
        system="You classify documentation changes strictly and invent nothing.")
    kind = str(out.get("kind") or "noise")
    return {"kind": kind if kind in ("feature_launch", "factual_update", "noise") else "noise",
            "title": str(out.get("title") or title)[:160], "detail": str(out.get("detail") or "")[:400]}


def sync(tenant: str, *, notion: Optional[Notion] = None, authority: int = 2,
         classify_fn: Callable[[str, str, str], dict] = classify) -> dict[str, Any]:
    token = _token()
    if notion is None:
        if not token:
            return {"ok": False, "error": "NOTION_TOKEN is not set (create an internal integration at "
                    "notion.so/my-integrations and share the pages with it)"}
        notion = Notion(token)
    brain = Brain(tenant, create=True)
    company = (brain.get_brand_profile().get("company") or {}).get("name") or tenant
    cache = S.tenant_dir(tenant) / "notion_cache"
    cache.mkdir(parents=True, exist_ok=True)
    known = json.loads(brain.meta("notion_pages") or "{}")
    first = not known
    pages = notion.pages()
    seen, report = {}, {"pages": len(pages), "changed": 0, "events": 0, "tombstoned": 0,
                        "chunks_changed": 0, "baseline": first}
    recent = (datetime.now(timezone.utc) - timedelta(days=14)).isoformat()
    for page in pages:
        pid = page["id"]
        edited = page.get("last_edited_time", "")
        if page.get("archived") or page.get("in_trash"):
            continue
        seen[pid] = edited
        if known.get(pid) == edited:
            continue
        title = title_of(page)
        md = "# " + title + "\n\n" + to_markdown(notion.blocks(pid))
        before_f = cache / (pid + ".md")
        before = before_f.read_text(encoding="utf-8") if before_f.exists() else ""
        chunks = chunk_markdown(md, title=title, company=company, source_label="Notion")
        r = brain.upsert_page("notion:" + pid, chunks, source="notion", authority=authority,
                              url=page.get("url"), updated_at=edited)
        report["changed"] += 1
        report["chunks_changed"] += r["added_or_changed"]
        created_recently = str(page.get("created_time", "")) >= recent
        if (not first or created_recently) and r["added_or_changed"]:
            try:
                c = classify_fn(title, before, md)
            except Exception:                       # noqa: BLE001 — no event, the text is still in
                c = {"kind": "noise"}
            if c["kind"] != "noise":
                brain.add_event("notion:" + pid + ":" + edited, at=edited, kind=c["kind"],
                                title=c["title"], detail=c.get("detail", ""), source="notion",
                                url=page.get("url") or "")
                report["events"] += 1
        before_f.write_text(md, encoding="utf-8")
    for pid in set(known) - set(seen):              # unshared, deleted or trashed
        brain.upsert_page("notion:" + pid, [], source="notion", authority=authority)
        (cache / (pid + ".md")).unlink(missing_ok=True)
        report["tombstoned"] += 1
    brain.meta("notion_pages", json.dumps(seen))
    brain.meta("notion_last_sync", datetime.now(timezone.utc).isoformat())
    brain.meta("notion_dirty", "")
    report["ok"] = True
    return report


def mark_dirty(tenant: str) -> dict[str, Any]:
    """A Notion webhook said something changed: sync at the next run start."""
    Brain(tenant).meta("notion_dirty", datetime.now(timezone.utc).isoformat())
    return {"ok": True, "tenant": tenant, "marked": True}


if __name__ == "__main__":
    import sys
    if sys.argv[1:2] == ["dirty"]:
        print(json.dumps(mark_dirty(sys.argv[2] if len(sys.argv) > 2 else "vanna")))
    else:
        print(json.dumps(sync(sys.argv[1] if len(sys.argv) > 1 else "vanna"), indent=1))
