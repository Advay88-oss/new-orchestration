"""Campaigns for the GTM engineer.

Scrapes a live quest site and writes a judgment on the campaigns that are
worth a look: why this one, whether it is worth studying, what Vanna can do,
why that would work, and what else is possible. Every count and reward is
the number the source returned. A sentence that adds a number the source
did not state is dropped.

    python -m pipeline.gtm_os.campaigns list [tenant]
    python -m pipeline.gtm_os.campaigns run  <tenant> "<query>" [galxe]
"""
from __future__ import annotations

import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from typing import Any

from pipeline.brand_brain.client import Brain, current_tenant
from pipeline.brand_brain.inspiration import _clean_handle, _strip_unsupported

LATEST = "campaigns:latest"
SHELF = "campaigns:shelf"
JOB = "campaigns:job"
ORDER = (
    "Numbered by people who joined, most first. "
    "A campaign with no public count is numbered after those. "
    "Campaigns that 0 or 1 people joined are left out."
)
QUERY = """
query CampaignList($input: ListCampaignInput!) {
  campaigns(input: $input) {
    pageInfo { endCursor hasNextPage }
    list {
      id name type rewardName status chain description
      space { name alias isVerified }
      participants { participantsCount }
      tokenReward { depositedTokenAmount tokenSymbol }
      rewardInfo { luckBasedToken { totalAmount tokenSymbol } discordRole { roleName } }
      loyaltyPoints
    }
  }
}
"""
QUERY_SHORT = QUERY.replace(" description", "")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _job(tenant: str, state: str, **extra: Any) -> None:
    Brain(tenant).meta(JOB, json.dumps({"state": state, "at": _now(), **extra}))


def _reward(c: dict) -> str:
    parts = []
    if c.get("rewardName"):
        parts.append(str(c["rewardName"]))
    tr = c.get("tokenReward") or {}
    if tr.get("depositedTokenAmount") and tr.get("tokenSymbol"):
        parts.append(str(tr["depositedTokenAmount"]) + " " + str(tr["tokenSymbol"]))
    luck = ((c.get("rewardInfo") or {}).get("luckBasedToken") or {})
    if luck.get("totalAmount") and luck.get("tokenSymbol"):
        parts.append(str(luck["totalAmount"]) + " " + str(luck["tokenSymbol"]))
    if c.get("loyaltyPoints"):
        parts.append(str(c["loyaltyPoints"]) + " points")
    role = ((c.get("rewardInfo") or {}).get("discordRole") or {})
    if role.get("roleName"):
        parts.append("Discord role: " + str(role["roleName"]))
    if not parts:
        parts.append(str(c.get("type") or "reward not stated on the listing"))
    return " + ".join(parts)


def _clean_desc(text: str) -> str:
    s = " ".join(str(text or "").split())
    s = re.sub(r"^(description|desc)\s*[:\-]?\s*", "", s, flags=re.I)
    return s[:500]


def _row(i: int, c: dict) -> dict | None:
    if not c.get("id") or not c.get("name"):
        return None
    space = c.get("space") or {}
    alias = str(space.get("alias") or "").strip("/")
    count = (c.get("participants") or {}).get("participantsCount")
    return {
        "rank": i,
        "id": c["id"],
        "name": str(c["name"])[:180],
        "url": "https://app.galxe.com/quest/" + (alias + "/" if alias else "") + str(c["id"]),
        "status": c.get("status") or "",
        "type": c.get("type") or "",
        "space": space.get("name") or "",
        "verified": bool(space.get("isVerified")),
        "chain": c.get("chain") or "",
        "participants": int(count) if count is not None else None,
        "reward": _reward(c)[:240],
        "description": _clean_desc(c.get("description")),
    }


def _gql(query: str, variables: dict | None = None) -> dict:
    url = "https://graphigo.prd.galaxy.eco/query"
    headers = {
        "content-type": "application/json",
        "accept": "*/*",
        "origin": "https://app.galxe.com",
        "referer": "https://app.galxe.com/",
        "user-agent": "Mozilla/5.0",
    }
    payload: dict[str, Any] = {"query": query}
    if variables:
        payload["variables"] = variables
        payload["operationName"] = "CampaignList"
    body = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=body, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())


def _words(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.casefold())


def _mentions(blob: str, term: str) -> bool:
    words = _words(term)
    if not words:
        return True
    if words[0] in set(_words(blob)):
        return True
    return len(term) >= 5 and term.casefold() in blob.casefold()


def _terms(term: str) -> list[str]:
    split = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", term).replace("_", " ")
    out = []
    for item in (term, split):
        item = " ".join(item.split())
        if item and item.casefold() not in [x.casefold() for x in out]:
            out.append(item)
    return out[:2]


def _space_ids(term: str) -> list[int]:
    """Galxe spaces whose name is that company, not a longer name that merely contains it."""
    data = _gql(
        "query { spaces(input: {first: 8, searchString: " + json.dumps(term)
        + "}) { list { id name } } }"
    )
    found = ((data.get("data") or {}).get("spaces") or {}).get("list") or []
    want = _words(term)
    ids = []
    for space in found:
        name = _words(str(space.get("name") or ""))
        if want and name[:len(want)] == want:
            ids.append(int(space["id"]))
        elif want and want[0] in name:
            ids.append(int(space["id"]))
    return ids[:2]


def _fetch_galxe(pages: int = 4, search: str = "", space_id: int | None = None) -> list[dict]:
    """Galxe's public GraphQL. No search: trending, about 100. With a search or a space: that company."""
    after = "-1"
    found: list[dict] = []
    query = QUERY
    got = 0
    listing = "Newest" if search or space_id else "Trending"
    while got < pages:
        variables: dict[str, Any] = {
            "listType": listing, "first": 30, "after": after,
            "isRecurring": False, "rewardTypes": [],
        }
        if search:
            variables["searchString"] = search
        if space_id:
            variables["spaceId"] = space_id
        try:
            data = _gql(query, {"input": variables})
        except urllib.error.HTTPError as exc:
            detail = exc.read()[:300].decode("utf-8", "replace")
            if query is QUERY and "description" in detail:
                query = QUERY_SHORT
                continue
            raise RuntimeError("Galxe " + str(exc.code) + " " + detail[:180])
        if data.get("errors"):
            if query is QUERY:
                query = QUERY_SHORT
                continue
            raise RuntimeError("Galxe " + str(data["errors"])[:180])
        block = ((data.get("data") or {}).get("campaigns") or {})
        batch = block.get("list") or []
        found.extend(batch)
        got += 1
        info = block.get("pageInfo") or {}
        if not info.get("hasNextPage"):
            break
        after = info.get("endCursor") or after
    rows = []
    seen: set[str] = set()
    term = search.casefold().strip()
    for c in found:
        row = _row(0, c)
        if not row or row["id"] in seen:
            continue
        blob = row["name"] + " " + row["space"] + " " + row["description"]
        if term and not space_id and not _mentions(blob, term):
            continue
        seen.add(row["id"])
        rows.append(row)
    return rows


def _host_name(url: str) -> str:
    host = urllib.parse.urlparse(url).netloc.lower()
    if host.startswith("www."):
        host = host[4:]
    skip = {"com", "org", "io", "xyz", "fi", "app", "www", "co", "net", "finance"}
    parts = [p for p in host.split(".") if p and p not in skip]
    return parts[0] if parts else host


def _galxe_term(url: str) -> str:
    parts = [p for p in urllib.parse.urlparse(url).path.strip("/").split("/")
             if p and p not in ("quest", "explore", "all")]
    return parts[0] if parts else ""


def _kind(source: str) -> tuple[str, str]:
    """trending, a Galxe link, any other link, or a name / handle."""
    s = (source or "").strip()
    low = s.lower().rstrip("/")
    if low in ("", "galxe", "galaxy", "https://galxe.com", "https://app.galxe.com",
               "https://app.galxe.com/quest/explore/all"):
        return "trending", ""
    if re.search(r"(?:x|twitter)\.com/", s, re.I) or s.startswith("@"):
        return "name", _clean_handle(s)
    if low.startswith("http://") or low.startswith("https://"):
        if "galxe.com" in low or "galaxy.eco" in low:
            return "galxe", _galxe_term(s) or _host_name(s)
        return "url", s
    return "name", s


def _page_row(url: str) -> dict | None:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Accept": "text/html"})
    with urllib.request.urlopen(req, timeout=20) as r:
        raw = r.read(400_000).decode("utf-8", "replace")
    title = ""
    m = re.search(r"<title[^>]*>(.*?)</title>", raw, re.I | re.S)
    if m:
        title = _clean_desc(re.sub(r"<[^>]+>", " ", m.group(1)))
    text = _clean_desc(re.sub(r"<script[\s\S]*?</script>|<style[\s\S]*?</style>|<[^>]+>", " ", raw))
    if not title and not text:
        return None
    return {
        "rank": 0, "id": "page:" + url[:80], "name": (title or url)[:180], "url": url,
        "status": "Page", "type": "website", "space": _host_name(url), "verified": False,
        "chain": "", "participants": None, "reward": "Not stated on this page",
        "description": text[:500],
    }


def _news_rows(term: str) -> list[dict]:
    from pipeline.brand_brain.watch import _atom_or_rss, _get
    q = urllib.parse.quote(term + " campaign")
    raw = _get("https://news.google.com/rss/search?q=" + q + "&hl=en-US&gl=US&ceid=US:en")
    rows = []
    needle = (_words(term) or [""])[0]
    for it in _atom_or_rss(raw)[:12]:
        title = _clean_desc(it.get("title"))
        blob = title + " " + str(it.get("text") or "")
        if needle and needle not in _words(blob) and needle not in blob.casefold():
            continue
        rows.append({
            "rank": 0, "id": "news:" + str(it.get("url") or title)[:80],
            "name": title[:180] or "News item", "url": it.get("url") or "",
            "status": "News", "type": "article", "space": str(it.get("by") or "News")[:80],
            "verified": False, "chain": "", "participants": None,
            "reward": "Not stated in this headline",
            "description": _clean_desc(it.get("text"))[:500],
        })
        if len(rows) >= 6:
            break
    return rows


def _collect(source: str) -> tuple[list[dict], str]:
    """Live rows for a Galxe listing, a website, a name, or a handle."""
    kind, target = _kind(source)
    rows: list[dict] = []
    label = "Galxe trending"
    if kind == "trending":
        rows = _fetch_galxe()
        return rows, label
    term = target if kind == "name" else (_host_name(target) if kind == "url" else target)
    if kind == "galxe":
        term = target
    errors = []
    if term:
        try:
            for t in _terms(term):
                ids = _space_ids(t)
                if not ids:
                    continue
                for sid in ids:
                    rows.extend(_fetch_galxe(pages=1, space_id=sid))
                break
            rows.extend(_fetch_galxe(pages=1, search=_terms(term)[-1]))
        except Exception as exc:                   # noqa: BLE001 — the other sources can still answer
            errors.append(str(exc)[:120])
    if kind == "url":
        try:
            page = _page_row(target)
            if page:
                rows.append(page)
        except Exception as exc:                   # noqa: BLE001 — news and Galxe can still answer
            errors.append(str(exc)[:120])
    if term and kind in ("name", "url", "galxe"):
        try:
            rows.extend(_news_rows(_terms(term)[-1]))
        except Exception as exc:                   # noqa: BLE001 — Galxe rows are enough when news fails
            errors.append(str(exc)[:120])
    if not rows and errors:
        raise RuntimeError(errors[0])
    seen: set[str] = set()
    unique = []
    for row in rows:
        if row["id"] in seen:
            continue
        seen.add(row["id"])
        unique.append(row)
    where = term or source
    label = "Galxe, the site, and news for " + where if kind == "url" else "Galxe and news for " + where
    return unique, label


def _arrange(rows: list[dict]) -> list[dict]:
    """Drop 0 and 1. Number the rest: most people joined is 1."""
    kept = []
    for seq, row in enumerate(rows):
        n = row.get("participants")
        if isinstance(n, int) and n < 2:
            continue
        row["_seq"] = seq
        kept.append(row)

    def key(row: dict) -> tuple:
        n = row.get("participants")
        if isinstance(n, int):
            return (0, -n, row["_seq"])
        return (1, row["_seq"], 0)

    kept.sort(key=key)
    for i, row in enumerate(kept, 1):
        row["rank"] = i
        row.pop("_seq", None)
    return kept


def _facts(c: dict) -> str:
    return " ".join(str(c.get(k) or "") for k in
                    ("name", "reward", "participants", "space", "chain", "type", "status", "description"))


def _judge(tenant: str, query: str, rows: list[dict]) -> list[dict]:
    """The strategist and the copywriter write the GTM read. The reviewer drops invented numbers."""
    from pipeline.gtm_os.agent_runtime import brain_json
    prof = Brain(tenant).get_brand_profile() or {}
    company = prof.get("company") or {}
    ours = str(company.get("name") or tenant)
    facts = json.dumps((prof.get("claims") or {}).get("true_figures") or [], ensure_ascii=False)[:1200]
    # Already numbered, busiest first. The first 18 are the ones a person would study.
    pool = rows[:18]
    lines = []
    for i, c in enumerate(pool):
        people = "count not stated" if c.get("participants") is None else str(c["participants"]) + " participants"
        lines.append(
            f"[{i}] {c['name']} | {people} | reward: {c['reward']} | "
            f"{c['space']} on {c['chain']} | {c['status']} {c['type']} | {c['description'][:280]}"
        )
    prompt = (
        "You are briefing a GTM engineer at " + ours + ". " + str(company.get("what_it_is") or "") + "\n"
        "Facts you may use about " + ours + ": " + facts + "\n"
        "The engineer asked: " + (query or "campaigns worth learning from") + "\n\n"
        "These are live listings. Counts and rewards below are the source's numbers. Do not change them "
        "and do not add a number that is not written here or in the facts.\n"
        + "\n".join(lines) + "\n\n"
        "Pick up to 8. Prefer a campaign a lot of people joined, that is close to credit, lending, "
        "margin, or collateral. If none are close, pick a mechanic " + ours + " could still use, and say it is not close.\n"
        "Each field is one sentence, under 28 words, in plain words a colleague can read once. "
        "Do not start a sentence with Description or Counts.\n"
        "- why_selected: why this one, from the listing.\n"
        "- worth: exactly one of Worth studying, Skip, Only as an idea.\n"
        "- worth_why: why that call. Do not repeat the worth label.\n"
        "- vanna_can: what " + ours + " can actually do. Only a feature the facts support.\n"
        "- why_it_works: why that move could earn attention, tied to this listing.\n"
        "- what_else: one other way to use the same mechanic.\n"
        "- related: close or idea.\n"
        'Return JSON: {"picks": [{"i": <index>, "why_selected": str, "worth": str, "worth_why": str, '
        '"vanna_can": str, "why_it_works": str, "what_else": str, "related": "close"|"idea"}]}'
    )
    out = brain_json(prompt, agent="A03_gtm_strategist", role="reasoning",
                     system="You brief a GTM engineer from listings you were given. You invent no figure.",
                     temperature=0.2, max_output_tokens=8192)
    picks = (out or {}).get("picks") if isinstance(out, dict) else []
    chosen = []
    for p in picks or []:
        if not isinstance(p, dict):
            continue
        try:
            src = pool[int(p["i"])]
        except (KeyError, TypeError, ValueError, IndexError):
            continue
        blob = _facts(src) + "\n" + facts
        note = {"id": src["id"]}
        for key in ("why_selected", "worth", "worth_why", "vanna_can", "why_it_works", "what_else"):
            clean, _ = _strip_unsupported(str(p.get(key) or "")[:500], blob)
            note[key] = clean
        rel = str(p.get("related") or "").lower()
        note["related"] = "close" if "close" in rel else "idea"
        w = note["worth"].lower()
        if "skip" in w:
            note["worth"] = "Skip"
        elif "idea" in w:
            note["worth"] = "Only as an idea"
        elif note["worth"]:
            note["worth"] = "Worth studying"
        if note["why_selected"] or note["vanna_can"]:
            chosen.append(note)
        if len(chosen) >= 8:
            break
    return chosen


def run(tenant: str, query: str, source: str = "galxe") -> dict[str, Any]:
    source = (source or "galxe").strip()
    _job(tenant, "running", query=query, source=source)
    try:
        rows, label = _collect(source)
        rows = _arrange(rows)
    except Exception as exc:                       # noqa: BLE001 — the page shows the failure
        err = str(exc)[:240]
        _job(tenant, "failed", error=err)
        return {"ok": False, "error": err}
    if not rows:
        err = "Nothing public came back for " + source + ". Try a company name, its website, or its X handle."
        _job(tenant, "failed", error=err)
        return {"ok": False, "error": err}
    notes: list[dict] = []
    judge_error = ""
    try:
        notes = _judge(tenant, query, rows)
    except Exception as exc:                       # noqa: BLE001 — the table is still the scrape
        judge_error = str(exc)[:200]
    by_id = {n["id"]: n for n in notes}
    for row in rows:
        extra = by_id.get(row["id"])
        if extra:
            row.update({k: v for k, v in extra.items() if k != "id"})
            row["selected"] = True
        else:
            row["selected"] = False
    result = {
        "ok": True,
        "tenant": tenant,
        "query": query,
        "source": label,
        "source_input": source,
        "order": ORDER,
        "scraped_at": _now(),
        "count": len(rows),
        "selected": len(notes),
        "judge_error": judge_error,
        "campaigns": rows,
    }
    brain = Brain(tenant)
    brain.meta(LATEST, json.dumps(result, ensure_ascii=False))
    shelf = _read_shelf(tenant)
    shelf[_shelf_key(source)] = result
    brain.meta(SHELF, json.dumps(shelf, ensure_ascii=False))
    _job(tenant, "done", count=len(rows), selected=len(notes), source=source)
    return result


def _shelf_key(source: str) -> str:
    kind, target = _kind(source)
    raw = (target or "galxe").lower()
    slug = re.sub(r"[^a-z0-9]+", "-", raw).strip("-")[:40] or "galxe"
    return kind + "-" + slug


def _read_shelf(tenant: str) -> dict:
    try:
        data = json.loads(Brain(tenant).meta(SHELF) or "{}")
    except ValueError:
        data = {}
    return data if isinstance(data, dict) else {}


def latest(tenant: str) -> dict[str, Any]:
    shelf = _read_shelf(tenant)
    shelves = [v for v in shelf.values() if isinstance(v, dict) and v.get("campaigns") is not None]
    if not shelves:
        try:
            old = json.loads(Brain(tenant).meta(LATEST) or "{}")
        except ValueError:
            old = {}
        if isinstance(old, dict) and old.get("campaigns") is not None:
            old.setdefault("source_input", old.get("source") or "galxe")
            shelves = [old]
    shelves.sort(key=lambda s: str(s.get("scraped_at") or ""), reverse=True)
    try:
        job = json.loads(Brain(tenant).meta(JOB) or "{}")
    except ValueError:
        job = {}
    return {"ok": True, "shelves": shelves, "job": job, "count": len(shelves)}


def main(argv: list[str]) -> int:
    cmd = argv[0] if argv else "list"
    tenant = argv[1] if len(argv) > 1 else current_tenant()
    if cmd == "run":
        query = argv[2] if len(argv) > 2 else ""
        source = argv[3] if len(argv) > 3 else "galxe"
        out = run(tenant, query, source)
    else:
        out = latest(tenant)
    sys.stdout.write(json.dumps(out, ensure_ascii=False, default=str))
    return 0 if out.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
