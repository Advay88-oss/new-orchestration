"""A public Notion workspace, page by page, into the brain.

The Notion integration (notion_sync) reads only pages shared with it, and the
founder's working workspace is shared by link instead ("anyone with the link").
Notion's own page API serves a public page and its blocks without a login, so
this crawls a root page and every page, database row, linked page and synced
block under it in the same workspace, and writes one markdown file per page:

  pipeline/brain/notion/<page id>.md           product, positioning, content work
  pipeline/brain/notion_internal/<page id>.md  fundraising, legal, money, people
  pipeline/brain/notion_<route>/...            a top-level section routed elsewhere
                                               (another company of the group, another tenant)

The tenant's sources file ingests the first at Notion authority and the second
at authority 4: the brain can be searched for internal pages, but they are
never handed to a writer as facts. Strings that look like keys or passwords are
redacted before anything is written.

    python -m pipeline.brand_brain.notion_public crawl <root page url or id> [--max 1500]
        [--route "Auri Canada=auri" --route "Cyber Security=other"]
    python -m pipeline.brand_brain.notion_public write [--route ...]   # re-route the last crawl, no fetch
"""
from __future__ import annotations

import json
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

REPO = Path(__file__).resolve().parents[2]
OUT = REPO / "pipeline" / "brain" / "notion"
OUT_INTERNAL = REPO / "pipeline" / "brain" / "notion_internal"
API = "https://www.notion.so/api/v3/"
PAGE_URL = "https://app.notion.com/p/"

# A page whose title, or an ancestor's title, names one of these is internal.
INTERNAL = re.compile(
    r"fundrais|investor|\binvest|\bsaft\b|term ?sheet|cap ?table|valuation|\blegal\b|contract|agreement|\bnda\b|"
    r"salar|payroll|compensation|\bhiring\b|recruit|candidate|interview|invoice|expense|\bbank|\btax|"
    r"accounting|password|credential|secret|api ?key|\bprivate\b|personal|\bhr\b", re.I)
SECRETS = [
    re.compile(r"AIza[0-9A-Za-z_\-]{35}"),
    re.compile(r"\bsk-[A-Za-z0-9_\-]{20,}"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{30,}"),
    re.compile(r"\bxox[abpr]-[A-Za-z0-9\-]{10,}"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?-----END [A-Z ]*PRIVATE KEY-----", re.S),
    re.compile(r"(?i)((?:password|passwd|secret|api[_ -]?key|token|private[_ ]key)\s*[:=]\s*)\S{6,}"),
]


def page_id(s: str) -> str:
    """A Notion URL or id as a dashed UUID."""
    h = re.findall(r"[0-9a-f]{32}", s.replace("-", "").lower())
    if not h:
        raise ValueError("no Notion page id in " + s)
    x = h[-1]
    return "-".join((x[:8], x[8:12], x[12:16], x[16:20], x[20:]))


def redact(text: str) -> str:
    for pat in SECRETS:
        text = pat.sub(lambda m: (m.group(1) if m.groups() else "") + "[redacted]", text)
    return text


def _post(path: str, body: dict, *, tries: int = 5) -> dict:
    req = urllib.request.Request(API + path, data=json.dumps(body).encode(), method="POST",
                                 headers={"Content-Type": "application/json",
                                          "User-Agent": "vanna-brand-brain/1 (public page reader)"})
    for attempt in range(tries):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                time.sleep(0.05)
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503, 504) and attempt < tries - 1:
                time.sleep(float(e.headers.get("Retry-After") or 2 * (attempt + 1)))
                continue
            raise
        except (urllib.error.URLError, TimeoutError):
            if attempt < tries - 1:
                time.sleep(2 * (attempt + 1))
                continue
            raise
    raise RuntimeError("notion unreachable")


def _val(rec: Any) -> Optional[dict]:
    """A record's value; the API nests it once or twice."""
    v = rec.get("value") if isinstance(rec, dict) else None
    if isinstance(v, dict) and isinstance(v.get("value"), dict) and "id" in v["value"]:
        v = v["value"]
    return v if isinstance(v, dict) else None


class Crawler:
    def __init__(self, root: str, max_pages: int = 1500):
        self.root = page_id(root)
        self.max_pages = max_pages
        self.blocks: dict[str, dict] = {}
        self.collections: dict[str, dict] = {}
        self.space: Optional[str] = None
        self.pages: dict[str, dict] = {}            # id -> {"title", "path", "md", "edited", "internal"}
        self.queue: list[tuple[str, list[str]]] = [(self.root, [])]
        self.queued = {self.root}
        self.failed: list[str] = []

    # ------------------------------------------------------------ fetching
    def _absorb(self, rm: dict) -> None:
        for bid, rec in (rm.get("block") or {}).items():
            v = _val(rec)
            if v:
                self.blocks[bid] = v
        for cid, rec in (rm.get("collection") or {}).items():
            v = _val(rec)
            if v:
                self.collections[cid] = v

    def _sync(self, ids: list[str]) -> None:
        for i in range(0, len(ids), 80):
            r = _post("syncRecordValues", {"requests": [
                {"pointer": {"table": "block", "id": b, **({"spaceId": self.space} if self.space else {})},
                 "version": -1} for b in ids[i:i + 80]]})
            self._absorb(r.get("recordMap") or {})

    def _load(self, pid: str) -> None:
        cursor: dict = {"stack": []}
        for chunk in range(50):
            r = _post("loadPageChunk", {"pageId": pid, "limit": 100, "cursor": cursor,
                                        "chunkNumber": chunk, "verticalColumns": False})
            self._absorb(r.get("recordMap") or {})
            cursor = r.get("cursor") or {}
            if not cursor.get("stack"):
                break
        if self.space is None and pid in self.blocks:
            self.space = self.blocks[pid].get("space_id")
        # Blocks the chunks did not carry (deep toggles, synced blocks).
        for _ in range(4):
            missing = [c for c in self._descendants(pid) if c not in self.blocks]
            if not missing:
                break
            self._sync(missing)

    def _descendants(self, bid: str) -> list[str]:
        out, stack = [], list((self.blocks.get(bid) or {}).get("content") or [])
        while stack:
            c = stack.pop()
            out.append(c)
            b = self.blocks.get(c)
            if b and b.get("type") not in ("page", "collection_view_page"):
                stack.extend(b.get("content") or [])
        return out

    def _rows(self, b: dict) -> list[str]:
        cid = b.get("collection_id") or ((b.get("format") or {}).get("collection_pointer") or {}).get("id")
        vids = b.get("view_ids") or []
        if not cid or not vids:
            return []
        sid = b.get("space_id") or self.space
        try:
            r = _post("queryCollection", {
                "collection": {"id": cid, "spaceId": sid}, "collectionView": {"id": vids[0], "spaceId": sid},
                "loader": {"type": "reducer", "reducers": {"collection_group_results": {"type": "results",
                                                                                          "limit": 1000}},
                           "searchQuery": "", "userTimeZone": "UTC"}})
        except Exception:                           # noqa: BLE001 — a view we cannot query
            return []
        self._absorb(r.get("recordMap") or {})
        if cid not in self.collections:
            try:
                rr = _post("syncRecordValues", {"requests": [
                    {"pointer": {"table": "collection", "id": cid, "spaceId": sid}, "version": -1}]})
                self._absorb(rr.get("recordMap") or {})
            except Exception:                       # noqa: BLE001 — rows without a schema
                pass
        res = ((r.get("result") or {}).get("reducerResults") or {}).get("collection_group_results") or {}
        return list(res.get("blockIds") or [])

    def _enqueue(self, pid: str, path: list[str]) -> None:
        b = self.blocks.get(pid)
        if b and self.space and b.get("space_id") not in (None, self.space):
            return                                  # another workspace
        if pid not in self.queued:
            self.queued.add(pid)
            self.queue.append((pid, path))

    # ------------------------------------------------------------ rendering
    def title(self, bid: str) -> str:
        b = self.blocks.get(bid) or {}
        if b.get("type") in ("collection_view_page", "collection_view"):
            c = self.collections.get(b.get("collection_id") or "") or {}
            return self.rich(c.get("name")) or "Untitled database"
        return self.rich((b.get("properties") or {}).get("title"), plain=True) or "Untitled"

    def rich(self, prop: Any, plain: bool = False, path: Optional[list[str]] = None) -> str:
        if not isinstance(prop, list):
            return ""
        out = []
        for seg in prop:
            if not seg:
                continue
            text = str(seg[0]) if seg else ""
            marks = seg[1] if len(seg) > 1 and isinstance(seg[1], list) else []
            for m in marks:
                if not m:
                    continue
                k = m[0]
                if k == "p" and len(m) > 1:           # page mention
                    text = self.title(m[1]) if m[1] in self.blocks else "a linked page"
                    if not plain:
                        text = "[[" + text + "]](" + PAGE_URL + m[1].replace("-", "") + ")"
                elif k == "d" and len(m) > 1 and isinstance(m[1], dict):
                    text = str(m[1].get("start_date") or text)
                elif k == "u":
                    text = "@user"
                elif plain:
                    continue
                elif k == "a" and len(m) > 1:
                    text = "[" + text + "](" + str(m[1]) + ")"
                elif k == "b":
                    text = "**" + text + "**" if text.strip() else text
                elif k == "i":
                    text = "*" + text + "*" if text.strip() else text
                elif k == "c":
                    text = "`" + text + "`"
                elif k == "s":
                    text = "~~" + text + "~~"
                elif k == "e" and len(m) > 1:
                    text = "$" + str(m[1]) + "$"
            out.append(text)
        return "".join(out)

    def render(self, bid: str, path: list[str], depth: int = 0) -> list[str]:
        b = self.blocks.get(bid)
        if not b or b.get("alive") is False:
            return []
        t = b.get("type")
        props, fmt = b.get("properties") or {}, b.get("format") or {}
        pad = "  " * depth
        txt = self.rich(props.get("title"), path=path)
        kids = list(b.get("content") or [])
        lines: list[str] = []

        def children(d: int = depth) -> list[str]:
            out = []
            for c in kids:
                out += self.render(c, path, d)
            return out

        if t in ("page", "collection_view_page"):
            self._enqueue(bid, path)
            return [pad + "- → page: [[" + self.title(bid) + "]](" + PAGE_URL + bid.replace("-", "") + ")"]
        if t == "alias":
            target = (fmt.get("alias_pointer") or {}).get("id")
            if target:                              # a link, not a child: not followed
                return [pad + "- → link to page: " + PAGE_URL + target.replace("-", "")]
            return []
        if t == "collection_view":
            rows = self._rows(b)
            c = self.collections.get(b.get("collection_id") or "") or {}
            lines.append("")
            lines.append(pad + "**Database: " + (self.rich(c.get("name")) or "Untitled") + "** (" + str(len(rows)) + " rows)")
            lines += self.table_of_rows(rows, c, path, pad)
            return lines
        if t == "header":
            return ["", "## " + txt]
        if t == "sub_header":
            return ["", "### " + txt]
        if t == "sub_sub_header":
            return ["", "#### " + txt]
        if t == "bulleted_list":
            return [pad + "- " + txt] + children(depth + 1)
        if t == "numbered_list":
            return [pad + "1. " + txt] + children(depth + 1)
        if t == "to_do":
            done = self.rich(props.get("checked"), plain=True).lower() == "yes"
            return [pad + "- [" + ("x" if done else " ") + "] " + txt] + children(depth + 1)
        if t == "toggle":
            return [pad + "- " + txt] + children(depth + 1)
        if t == "quote":
            return ["", pad + "> " + txt] + children(depth)
        if t == "callout":
            icon = str(fmt.get("page_icon") or "")
            return ["", pad + "> " + (icon + " " if icon and len(icon) < 4 else "") + txt] + children(depth)
        if t == "code":
            lang = self.rich(props.get("language"), plain=True)
            return ["", pad + "```" + lang.lower(), self.rich(props.get("title"), plain=True), pad + "```"]
        if t == "divider":
            return ["", "---"]
        if t == "equation":
            return ["", "$$" + self.rich(props.get("title"), plain=True) + "$$"]
        if t in ("image", "video", "file", "pdf", "audio", "embed", "bookmark", "figma", "drive", "maps",
                 "tweet", "gist", "codepen", "typeform", "loom"):
            src = self.rich(props.get("source"), plain=True) or str(fmt.get("display_source") or "")
            if src.startswith("attachment:"):
                src = "(file in Notion: " + src.split(":")[-1] + ")"
            cap = self.rich(props.get("caption"))
            link = self.rich(props.get("link"), plain=True)
            return [pad + "- [" + t + "] " + (txt + " " if txt else "") + (cap + " " if cap else "")
                    + (link or src)]
        if t == "table":
            order = fmt.get("table_block_column_order") or []
            rows = []
            for r in kids:
                rb = self.blocks.get(r) or {}
                rp = rb.get("properties") or {}
                cols = order or list(rp.keys())
                rows.append([self.rich(rp.get(c), path=path).replace("|", "/").replace("\n", " ") for c in cols])
            if not rows:
                return []
            w = max(len(r) for r in rows)
            rows = [r + [""] * (w - len(r)) for r in rows]
            return ["", "| " + " | ".join(rows[0]) + " |", "|" + "---|" * w] + \
                   ["| " + " | ".join(r) + " |" for r in rows[1:]]
        if t == "transclusion_reference":
            src = (fmt.get("transclusion_reference_pointer") or {}).get("id")
            if src and src not in self.blocks:
                try:
                    self._sync([src])
                    self._sync([c for c in (self.blocks.get(src) or {}).get("content") or []
                                if c not in self.blocks])
                except Exception:                   # noqa: BLE001 — a synced block we cannot read
                    return []
            return self.render(src, path, depth) if src else []
        if t in ("column_list", "column", "transclusion_container", "table_of_contents", "breadcrumb"):
            return children(depth)
        # text and anything else: its text, then its children
        return ([pad + txt] if txt else [""]) + children(depth + 1 if txt else depth)

    def table_of_rows(self, rows: list[str], coll: dict, path: list[str], pad: str) -> list[str]:
        schema = coll.get("schema") or {}
        cols = [k for k, v in schema.items() if v.get("type") != "title"][:6]
        head = ["Name"] + [str(schema[k].get("name") or k) for k in cols]
        out = ["", pad + "| " + " | ".join(head) + " |", pad + "|" + "---|" * len(head)]
        for r in rows:
            rb = self.blocks.get(r) or {}
            rp = rb.get("properties") or {}
            cells = ["[[" + self.title(r) + "]]"] + [self.rich(rp.get(k), path=path).replace("|", "/").replace("\n", " ")[:120]
                                                       for k in cols]
            out.append(pad + "| " + " | ".join(cells) + " |")
            self._enqueue(r, path)
        return out

    def row_props(self, bid: str) -> list[str]:
        b = self.blocks.get(bid) or {}
        if b.get("parent_table") != "collection":
            return []
        coll = self.collections.get(b.get("parent_id") or "") or {}
        schema = coll.get("schema") or {}
        out = []
        for k, v in (b.get("properties") or {}).items():
            if k == "title" or k not in schema:
                continue
            val = self.rich(v)
            if val.strip():
                out.append("- **" + str(schema[k].get("name") or k) + "**: " + val)
        return out

    # ------------------------------------------------------------ crawl
    def crawl(self, log=print) -> dict[str, Any]:
        from concurrent.futures import ThreadPoolExecutor
        pool = ThreadPoolExecutor(max_workers=8)
        while self.queue and len(self.pages) < self.max_pages:
            batch, self.queue = self.queue[:8], self.queue[8:]
            errs = list(pool.map(self._try_load, [pid for pid, _ in batch]))
            for (pid, path), err in zip(batch, errs):
                if err:
                    self.failed.append(pid + ": " + err)
                    continue
                self._page(pid, path, log)
        pool.shutdown()
        return {"pages": len(self.pages), "queued_left": len(self.queue), "failed": self.failed}

    def _try_load(self, pid: str) -> str:
        try:
            self._load(pid)
            return ""
        except Exception as exc:                    # noqa: BLE001 — one page fails alone
            return str(exc)[:120]

    def _page(self, pid: str, path: list[str], log) -> None:
            b = self.blocks.get(pid)
            if not b:
                self.failed.append(pid + ": not public or not found")
                return
            if self.space and b.get("space_id") not in (None, self.space):
                return
            title = self.title(pid)
            here = path + [title]
            body: list[str] = self.row_props(pid)
            if b.get("type") == "collection_view_page":
                c = self.collections.get(b.get("collection_id") or "") or {}
                body += self.table_of_rows(self._rows(b), c, here, "")
            for c in b.get("content") or []:
                body += self.render(c, here)
            edited = b.get("last_edited_time")
            when = datetime.fromtimestamp(edited / 1000, timezone.utc).isoformat() if edited else ""
            internal = bool(INTERNAL.search(" / ".join(here)))
            archive = bool(re.search(r"\barchive", " / ".join(here[1:]), re.I))
            md = ("# " + title + "\n\n"
                  + "Notion page: " + PAGE_URL + pid.replace("-", "") + "  \n"
                  + "Path: " + " › ".join(here) + "  \n"
                  + ("Last edited: " + when[:10] + "  \n" if when else "")
                  + ("Internal: never published\n" if internal else "")
                  + ("Archive: older material, not current\n" if archive and not internal else "") + "\n"
                  + "\n".join(body).strip() + "\n")
            self.pages[pid] = {"title": title, "path": here, "md": redact(re.sub(r"\n{3,}", "\n\n", md)),
                               "edited": when, "internal": internal, "archive": archive and not internal}
            log(f"[{len(self.pages)}] {'INTERNAL ' if internal else 'ARCHIVE ' if archive else ''}"
                f"{' › '.join(here)[:140]}", flush=True)

    def save(self) -> None:
        OUT.mkdir(parents=True, exist_ok=True)
        (OUT / ".crawl.json").write_text(json.dumps({"root": self.root, "pages": self.pages,
                                                    "failed": self.failed}, ensure_ascii=False), encoding="utf-8")

    @classmethod
    def last(cls) -> "Crawler":
        d = json.loads((OUT / ".crawl.json").read_text(encoding="utf-8"))
        c = cls(d["root"])
        c.pages, c.failed = d["pages"], d["failed"]
        return c

    def write(self, routes: Optional[dict[str, str]] = None) -> dict[str, int]:
        """Each page to its folder: the main one, unless its top-level section
        is routed (routes: section title -> route name)."""
        routes = routes or {}
        written: dict[str, int] = {}
        keep: dict[Path, set] = {}
        for pid, p in self.pages.items():
            route = routes.get(p["path"][1]) if len(p["path"]) > 1 else None
            base = REPO / "pipeline" / "brain" / ("notion_" + route if route else "notion")
            # Internal pages of a section that stays in this tenant (a level
            # route: background or archive) go with the other internal pages.
            same = route in (None, "archive", "background")
            d = ((OUT_INTERNAL if same else base.with_name(base.name + "_internal")) if p["internal"]
                 else base.with_name("notion_archive") if p.get("archive") and same
                 else base.with_name(base.name + "_archive") if p.get("archive") else base)
            d.mkdir(parents=True, exist_ok=True)
            name = pid.replace("-", "") + ".md"
            (d / name).write_text(p["md"], encoding="utf-8")
            keep.setdefault(d, set()).add(name)
            written[d.name] = written.get(d.name, 0) + 1
        # A page removed from Notion leaves the brain on the next ingest.
        for d in {x for x in (REPO / "pipeline" / "brain").glob("notion*") if x.is_dir()} | set(keep):
            for f in d.glob("*.md"):
                if f.name not in keep.get(d, set()):
                    f.unlink()
        tree = ["# Notion workspace tree (crawled " + datetime.now(timezone.utc).isoformat()[:16] + "Z)", ""]
        for pid, p in sorted(self.pages.items(), key=lambda kv: kv[1]["path"]):
            tree.append("  " * (len(p["path"]) - 1) + "- " + p["title"] + (" (internal)" if p["internal"] else "")
                        + " — " + pid.replace("-", ""))
        (OUT / ".tree.md").write_text("\n".join(tree) + "\n", encoding="utf-8")
        (OUT / ".manifest.json").write_text(json.dumps(
            {"root": self.root, "crawled_at": datetime.now(timezone.utc).isoformat(), "failed": self.failed,
             "pages": {k: {"title": v["title"], "path": v["path"], "edited": v["edited"], "internal": v["internal"]}
                       for k, v in self.pages.items()}}, ensure_ascii=False, indent=1), encoding="utf-8")
        return written


def main(argv: Optional[list[str]] = None) -> int:
    import argparse
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("crawl")
    c.add_argument("root")
    c.add_argument("--max", type=int, default=1500)
    c.add_argument("--route", action="append", default=[], help='"<top-level section title>=<route>"')
    w = sub.add_parser("write")
    w.add_argument("--route", action="append", default=[])
    a = ap.parse_args(argv)
    routes = dict(r.split("=", 1) for r in a.route)
    if a.cmd == "write":
        cr = Crawler.last()
        res: dict[str, Any] = {"pages": len(cr.pages)}
    else:
        cr = Crawler(a.root, max_pages=a.max)
        res = cr.crawl()
        cr.save()
    res["written"] = cr.write(routes)
    print(json.dumps(res, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
