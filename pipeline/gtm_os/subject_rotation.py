"""Which product page the automatic clock posts about next.

Scraped headlines were changing, and the strategist still wrote Blend and
Aquarius, because that is the profile's first argument. The GitHub pages
already in the brain name other mechanisms. The clock takes the page that
has not been the subject lately and makes that the post.

A founder directive is left alone. This only applies when the clock chooses.

Everything company-specific comes from the tenant's profile
(prompt_rules.rotation_subjects and prompt_rules.doc_page_notes); the
rotation memory is kept per tenant. A tenant with no fixed subjects and no
docs pages in its brain has nothing to rotate, and next_subject() returns
None.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Optional

_STATE_DIR = Path(__file__).resolve().parents[1] / "state"


def _tenant(tenant: Optional[str] = None) -> str:
    from pipeline.brand_brain.client import current_tenant
    return tenant or current_tenant()


def _state(tenant: Optional[str] = None) -> Path:
    # Vanna keeps the original file so its history carries over.
    t = _tenant(tenant)
    return _STATE_DIR / ("recent_subjects.json" if t == "vanna" else "recent_subjects_" + t + ".json")


def fixed_subjects(tenant: Optional[str] = None) -> list[dict[str, Any]]:
    """The tenant's fixed product subjects, in rotation order."""
    from pipeline.brand_brain import context as C
    rows = C.rule("rotation_subjects", [], tenant) or []
    return [r for r in rows if isinstance(r, dict) and r.get("id") and r.get("text")]


def _load(tenant: Optional[str] = None) -> list[dict[str, Any]]:
    try:
        data = json.loads(_state(tenant).read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except Exception:                               # noqa: BLE001 — first run
        return []


# Docs pages in the brain that explain the product (public guides and
# learn pages) in any repo. Snippets, the home page and repo tooling are not
# subjects.
def _doc_page(tenant: Optional[str] = None) -> "re.Pattern[str]":
    """A docs page path. The tenant's prompt_rules.doc_roots names the docs
    folders when it has them; otherwise any folder's guides/ or learn/."""
    from pipeline.brand_brain import context as C
    roots = [re.escape(str(r)) for r in (C.rule("doc_roots", [], tenant) or []) if r]
    top = "(?:" + "|".join(roots) + ")" if roots else "[A-Za-z0-9_.-]+"
    return re.compile(r"(" + top + r"/(?:guides|learn)/[A-Za-z0-9_/.-]+\.mdx?)")


def _page_note(path: str, tenant: Optional[str] = None) -> str:
    """The tenant's scope note for a docs page, by its top folder ("*" = any)."""
    from pipeline.brand_brain import context as C
    notes = C.rule("doc_page_notes", {}, tenant) or {}
    top = path.split("/", 1)[0]
    return str(notes.get(top) or notes.get("*") or "")


def doc_subjects(tenant: Optional[str] = None, limit: int = 200) -> list[dict[str, Any]]:
    """One subject per public docs page in the brain, with what that page says.
    Code files and commit messages are not subjects: the facts ledger keeps
    private repos and contract source out of posts."""
    try:
        from pipeline.brand_brain.client import Brain
        brain = Brain(tenant) if tenant else Brain()
        with brain._db() as con:
            rows = con.execute("SELECT section, title, url, text FROM chunks WHERE source = 'github' "
                               "AND (deleted IS NULL OR deleted = 0)").fetchall()
    except Exception:                               # noqa: BLE001 — the fixed pages still rotate
        return []
    doc_page = _doc_page(tenant)
    pages: dict[str, list[str]] = {}
    for r in rows:
        r = dict(r)
        hay = " ".join(str(r.get(k) or "") for k in ("section", "title", "url"))
        m = doc_page.search(hay)
        if m:
            pages.setdefault(m.group(1), []).append(" ".join(str(r.get("text") or "").split()))
    out = []
    for path, texts in sorted(pages.items())[:limit]:
        name = path.rsplit("/", 1)[-1].rsplit(".", 1)[0].replace("-", " ")
        excerpt = " ".join(texts)[:1400]
        note = _page_note(path, tenant)
        out.append({
            "id": "doc:" + path,
            "text": ("The subject is the docs page '" + name + "' (" + path + "). Explain the one thing this "
                     "page lets a user do or understand, using only what it says: " + excerpt
                     + (" " + note if note else "")),
        })
    return out


def pool(tenant: Optional[str] = None) -> list[dict[str, Any]]:
    """The fixed product pages, then every docs page."""
    return fixed_subjects(tenant) + doc_subjects(tenant)


def next_subject(tenant: Optional[str] = None) -> Optional[dict[str, Any]]:
    """The page that has gone longest without a post (never used ones first),
    or None when the tenant has nothing to rotate."""
    subjects = pool(tenant)
    if not subjects:
        return None
    used = [str(r.get("id")) for r in _load(tenant)]
    fresh = [s for s in subjects if s["id"] not in used]
    if fresh:
        # Not always the first: a page from a different area than the last post.
        last = used[0].split("/")[1] if used and "/" in used[0] else ""
        other = [s for s in fresh if ("/" not in s["id"]) or s["id"].split("/")[1] != last]
        return (other or fresh)[0]
    for sid in reversed(used):
        hit = next((s for s in subjects if s["id"] == sid), None)
        if hit:
            return hit
    return subjects[0]


def others(current_id: str, tenant: Optional[str] = None) -> list[dict[str, Any]]:
    """The remaining pages, if the first one is declined."""
    used = {str(r.get("id")) for r in _load(tenant)}
    rest = [s for s in pool(tenant) if s["id"] != current_id]
    return [s for s in rest if s["id"] not in used] + [s for s in rest if s["id"] in used]


def remember(subject_id: str, run_id: Optional[str] = None, tenant: Optional[str] = None) -> None:
    try:
        rows = [r for r in _load(tenant) if r.get("id") != subject_id]
        rows.insert(0, {"id": subject_id, "run_id": run_id})
        path = _state(tenant)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(rows[:80], indent=2), encoding="utf-8")
    except Exception:                               # noqa: BLE001 — must not fail a run
        pass
