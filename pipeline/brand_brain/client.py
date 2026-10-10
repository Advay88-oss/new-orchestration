"""`Brain(tenant)` — the six calls agents make, and the writes that fill it.

The Brain MCP server (`mcp_server.py`) exposes exactly these read calls plus
`log_post_outcome`; the pipeline calls them in-process through this class so
a run does not pay a process hop per lookup. Either way the tenant is bound
once, at construction — no call takes a tenant argument, so no call can ask
for another company's data.
"""
from __future__ import annotations

import contextlib
import json
import os
import re
import sqlite3
import threading
from datetime import datetime, timezone
from typing import Any, Iterable, Optional

import numpy as np

from pipeline.brand_brain import embed as E
from pipeline.brand_brain import store as S
from pipeline.brand_brain.chunking import Chunk, digest, page_kind

# How much a source is trusted when two disagree: 1 founder-confirmed (the
# Notion ground truth), 2 the live docs, 3 the internal knowledge pack,
# 4 archive (the August knowledge base, which predates the Stellar-only
# deployment in places). Archive is found, but ranked below and marked, and
# the reviewer does not accept it alone as proof of a claim.
AUTHORITY_WEIGHT = {1: 1.0, 2: 0.95, 3: 0.85, 4: 0.6}
_WORD = re.compile(r"[A-Za-z0-9][A-Za-z0-9.\-]{1,}")
_vec_cache: dict[str, tuple[float, list[str], np.ndarray]] = {}

# BM25 on Postgres. Its built-in ts_rank has no inverse document frequency,
# so a rare product term ("Soroban") counts no more than a common word, and
# short authoritative chunks (the profile's "TESTNET, not mainnet") lost to
# long docs pages. This is Okapi BM25 over the tsvector (k1 1.2, b 0.75),
# title/section occurrences counted twice as the SQLite FTS5 weights did.
# Row-level security scopes every CTE to the bound tenant.
_PG_BM25 = """
WITH ql AS (SELECT DISTINCT unnest(tsvector_to_array(to_tsvector('english', ?))) AS lex),
docs AS (SELECT id, tsv, length(tsv) AS dl FROM chunks WHERE deleted=0 AND content_type!='section'),
stats AS (SELECT count(*)::float AS n, avg(dl)::float AS avgdl FROM docs),
tf AS (SELECT d.id, d.dl, u.lexeme,
              (SELECT count(*) FROM unnest(u.weights) w WHERE w = 'A') * 2.0
            + (SELECT count(*) FROM unnest(u.weights) w WHERE w <> 'A') AS tf
       FROM docs d, unnest(d.tsv) u WHERE u.lexeme IN (SELECT lex FROM ql)),
df AS (SELECT lexeme, count(DISTINCT id)::float AS df FROM tf GROUP BY lexeme)
SELECT tf.id, sum(ln((s.n - df.df + 0.5) / (df.df + 0.5) + 1)
                  * tf.tf * 2.2 / (tf.tf + 1.2 * (0.25 + 0.75 * tf.dl / s.avgdl))) AS score
FROM tf JOIN df USING (lexeme), stats s
GROUP BY tf.id ORDER BY score DESC LIMIT ?
"""
_vec_lock = threading.Lock()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def current_tenant() -> str:
    """The tenant this process serves: the session's, else Vanna (tenant #1)."""
    return os.environ.get("BRAIN_TENANT") or os.environ.get("VANNA_TENANT") or "vanna"


def _section_pricing(section: str) -> Optional[str]:
    """A section heading marks pricing ("Limits and fees"), never legal: a
    heading like "Traction, funding & legal" is not a legal page."""
    return "pricing" if page_kind("", section) == "pricing" else None


class Brain:
    def __init__(self, tenant: Optional[str] = None, *, create: bool = False):
        self.tenant = tenant or current_tenant()
        self._create = create
        S.tenant_dir(self.tenant)                       # validates the id

    @contextlib.contextmanager
    def _db(self):
        """One connection per call: committed on success, always closed.
        (sqlite3's own context manager commits but never closes, which
        leaked a file handle per call.)"""
        con = S.connect(self.tenant, create=self._create)
        try:
            with con:
                yield con
        finally:
            con.close()

    # ------------------------------------------------------------------ reads

    def get_brand_profile(self) -> dict[str, Any]:
        """The approved profile, else the newest draft — loaded whole, every run."""
        with self._db() as con:
            row = (con.execute("SELECT * FROM profile_versions WHERE status='approved' "
                               "ORDER BY version DESC LIMIT 1").fetchone()
                   or con.execute("SELECT * FROM profile_versions "
                                  "ORDER BY version DESC LIMIT 1").fetchone())
        if not row:
            return {}
        p = json.loads(row["profile"])
        p["_version"] = row["version"]
        p["_status"] = row["status"]
        return p

    def get_whats_new(self, since: Optional[str] = None, limit: int = 20) -> list[dict]:
        """Dated events after `since` (ISO time), newest first."""
        with self._db() as con:
            rows = con.execute("SELECT * FROM whats_new WHERE at > ? ORDER BY at DESC LIMIT ?",
                               (since or "", limit)).fetchall()
        return [dict(r) for r in rows]

    def search_knowledge(self, query: str, *, k: int = 8,
                         content_types: Optional[Iterable[str]] = None,
                         sources: Optional[Iterable[str]] = None,
                         max_authority: int = 4, include_legal: bool = False) -> list[dict]:
        """Hybrid search: BM25 keyword + vector, fused by reciprocal rank.

        Keyword search is what finds product names and terms ("Soroban",
        "health factor") that a vector search can rank below a paraphrase.
        Results carry their source, URL, authority and the parent section.
        """
        # Code listings only when asked for: a product question is not
        # answered by a Rust signature.
        ct = set(content_types or [])
        skip_code = "code" not in ct
        # Legal pages (terms, privacy, disclaimers) are not product facts: out
        # of the agents' searches unless asked for; the assistant includes them.
        skip_legal = not include_legal and "legal" not in ct
        src = set(sources or [])
        with self._db() as con:
            bm25 = self._bm25(con, query, 40)
            vec, mode = [], "hybrid"
            try:
                vec = self._vector(con, E.query(query), 40)
            except Exception:                           # noqa: BLE001 — degrade to keyword
                mode = "keyword-only"
            fused: dict[str, float] = {}
            for rank, cid in enumerate(bm25):
                fused[cid] = fused.get(cid, 0) + 1.0 / (60 + rank)
            for rank, cid in enumerate(vec):
                fused[cid] = fused.get(cid, 0) + 1.0 / (60 + rank)
            if not fused:
                return []
            marks = ",".join("?" * len(fused))
            rows = {r["id"]: r for r in con.execute(
                "SELECT * FROM chunks WHERE id IN (" + marks + ") AND deleted=0",
                list(fused)).fetchall()}
            out = []
            for cid, score in fused.items():
                r = rows.get(cid)
                if (not r or r["content_type"] == "section"
                        or (ct and r["content_type"] not in ct)
                        or (skip_code and r["content_type"] == "code")
                        or (skip_legal and r["content_type"] == "legal")
                        or (src and r["source"] not in src)
                        or r["authority"] > max_authority):
                    continue
                out.append((score * AUTHORITY_WEIGHT.get(r["authority"], 0.5), r))
            out.sort(key=lambda x: -x[0])
            # At most two passages per page: one long article otherwise fills
            # every slot ("Curators Explained" four times) and crowds out the rest.
            per_page: dict[str, int] = {}
            diverse = []
            for score, r in out:
                if per_page.get(r["page_id"], 0) >= 2:
                    continue
                per_page[r["page_id"]] = per_page.get(r["page_id"], 0) + 1
                diverse.append((score, r))
            results = []
            for score, r in diverse[:k]:
                parent = None
                if r["parent_id"]:
                    pr = con.execute("SELECT text FROM chunks WHERE id=?", (r["parent_id"],)).fetchone()
                    parent = pr["text"][:1800] if pr else None
                results.append({
                    "id": r["id"], "text": r["text"], "section": r["section"],
                    "title": r["title"], "source": r["source"], "authority": r["authority"],
                    "url": r["url"], "updated_at": r["updated_at"],
                    "content_type": r["content_type"], "parent": parent,
                    "score": round(score * 1000, 2), "mode": mode})
        return results

    def get_visual_refs(self, topic: str, n: int = 4,
                        kinds: Optional[Iterable[str]] = None) -> list[dict]:
        """Brand images closest to a topic — text and images share one space."""
        kinds = set(kinds or [])
        with self._db() as con:
            rows = [r for r in con.execute("SELECT * FROM images").fetchall()
                    if (not kinds or r["kind"] in kinds) and r["embedding"]]
        if not rows:
            return []
        try:
            q = E.texts([topic], task="RETRIEVAL_QUERY")[0]
            sims = [float(np.dot(q, E.from_blob(r["embedding"]))) for r in rows]
        except Exception:                               # noqa: BLE001 — rank by founder score
            sims = [0.0] * len(rows)
        # A founder-approved image outranks a merely similar one.
        ranked = sorted(zip(rows, sims), key=lambda x: -(x[1] + 0.15 * float(x[0]["score"] or 0)))
        return [{"id": r["id"], "path": r["path"], "kind": r["kind"], "caption": r["caption"],
                 "style_tags": json.loads(r["style_tags"] or "[]"), "score": r["score"],
                 "note": r["note"], "similarity": round(s, 3)} for r, s in ranked[:n]]

    def get_competitor_patterns(self, topic: Optional[str] = None, n: int = 6) -> list[dict]:
        """How competitors post about a topic — patterns, never their copy."""
        with self._db() as con:
            rows = con.execute("SELECT * FROM competitor_patterns").fetchall()
        if topic and rows and any(r["embedding"] for r in rows):
            try:
                q = E.query(topic)
                rows = sorted(rows, key=lambda r: -float(np.dot(q, E.from_blob(r["embedding"])))
                              if r["embedding"] else 0.0)
            except Exception:                           # noqa: BLE001 — unranked
                pass
        return [{"competitor": r["competitor"], "topic": r["topic"], "pattern": r["pattern"],
                 "evidence_n": r["evidence_n"], "updated_at": r["updated_at"]} for r in rows[:n]]

    def log_post_outcome(self, post_id: str, metrics: dict, *, run_id: Optional[str] = None,
                         source: str = "manual") -> dict:
        with self._db() as con:
            con.execute("INSERT INTO outcomes(post_id, run_id, metrics, source, at) VALUES (?,?,?,?,?)",
                        (post_id, run_id, json.dumps(metrics), source, _now()))
        return {"ok": True, "post_id": post_id}

    def outcomes(self, limit: int = 200) -> list[dict]:
        with self._db() as con:
            rows = con.execute("SELECT * FROM outcomes ORDER BY at DESC LIMIT ?", (limit,)).fetchall()
        return [{**dict(r), "metrics": json.loads(r["metrics"])} for r in rows]

    # --------------------------------------------------------------- internals

    @staticmethod
    def _bm25(con, query: str, n: int) -> list[str]:
        terms = [t for t in _WORD.findall(query) if len(t) > 1][:24]
        if not terms:
            return []
        if isinstance(con, S.PgConnection):
            try:
                rows = con.execute(_PG_BM25, (" ".join(terms), n)).fetchall()
            except Exception:                           # noqa: BLE001 — degrade to vector only
                con.rollback()
                return []
            return [r["id"] for r in rows]
        match = " OR ".join('"' + t.replace('"', "") + '"' for t in terms)
        try:
            rows = con.execute(
                "SELECT c.id FROM chunks_fts f JOIN chunks c ON c.rowid=f.rowid "
                "WHERE chunks_fts MATCH ? AND c.deleted=0 AND c.content_type!='section' "
                "ORDER BY bm25(chunks_fts, 2.0, 2.0, 1.0, 1.0) LIMIT ?", (match, n)).fetchall()
        except sqlite3.OperationalError:
            return []
        return [r["id"] for r in rows]

    def _vector(self, con, q: np.ndarray, n: int) -> list[str]:
        if isinstance(con, S.PgConnection):
            # pgvector: cosine distance over the HNSW index.
            rows = con.execute(
                "SELECT id FROM chunks WHERE deleted=0 AND content_type!='section' "
                "AND embedding IS NOT NULL ORDER BY embedding <=> ?::vector LIMIT ?",
                (E.to_blob(q), n)).fetchall()
            return [r["id"] for r in rows]
        db = str(S.tenant_dir(self.tenant) / "brain.db")
        stamp = con.execute("SELECT COALESCE(MAX(updated_at),'') || COUNT(*) FROM chunks").fetchone()[0]
        with _vec_lock:
            cached = _vec_cache.get(db)
            if not cached or cached[0] != stamp:
                rows = con.execute("SELECT id, embedding FROM chunks WHERE deleted=0 AND "
                                   "content_type!='section' AND embedding IS NOT NULL").fetchall()
                ids = [r["id"] for r in rows]
                mat = (np.vstack([E.from_blob(r["embedding"]) for r in rows])
                       if rows else np.zeros((0, E.DIM), dtype=np.float32))
                cached = (stamp, ids, mat)
                _vec_cache[db] = cached
        _, ids, mat = cached
        if not ids:
            return []
        sims = mat @ q
        top = np.argsort(-sims)[:n]
        return [ids[i] for i in top]

    # ------------------------------------------------------------------ writes

    def save_profile(self, profile: dict, *, status: str = "draft", source: str = "",
                     note: str = "") -> int:
        clean = {k: v for k, v in profile.items() if not k.startswith("_")}
        with self._db() as con:
            if status == "approved":
                con.execute("UPDATE profile_versions SET status='superseded' WHERE status='approved'")
            # Versions count per tenant (v1, v2, ...) on either backend.
            row = con.execute(
                "INSERT INTO profile_versions(version, profile, status, source, note, created_at, approved_at) "
                "VALUES ((SELECT COALESCE(MAX(version), 0) + 1 FROM profile_versions),?,?,?,?,?,?) "
                "RETURNING version",
                (json.dumps(clean, ensure_ascii=False), status, source, note, _now(),
                 _now() if status == "approved" else None)).fetchone()
            return int(row[0])

    def approve_profile(self, version: int, *, note: str = "") -> None:
        with self._db() as con:
            con.execute("UPDATE profile_versions SET status='superseded' WHERE status='approved'")
            con.execute("UPDATE profile_versions SET status='approved', approved_at=?, "
                        "note=COALESCE(NULLIF(?,''), note) WHERE version=?", (_now(), note, version))

    def profile_versions(self) -> list[dict]:
        with self._db() as con:
            rows = con.execute("SELECT version, status, source, note, created_at, approved_at "
                               "FROM profile_versions ORDER BY version DESC").fetchall()
        return [dict(r) for r in rows]

    def retire_pages(self, source: str, keep: set) -> int:
        """Tombstone every live page of `source` whose page id is not in
        `keep` (the pages its knowledge sources yield now). Returns the count."""
        with self._db() as con:
            live = {r["page_id"] for r in con.execute(
                "SELECT DISTINCT page_id FROM chunks WHERE source=? AND deleted=0", (source,)).fetchall()}
            gone = sorted(p for p in live if p not in keep)
            for p in gone:
                con.execute("UPDATE chunks SET deleted=1 WHERE page_id=? AND source=?", (p, source))
        return len(gone)

    def upsert_page(self, page_id: str, chunks: list[Chunk], *, source: str, authority: int,
                    url: Optional[str] = None, updated_at: Optional[str] = None,
                    embed: bool = True) -> dict[str, int]:
        """Incremental: unchanged chunks are kept, changed ones re-embedded,
        vanished ones tombstoned. Returns what changed.

        Legal and pricing pages are tagged here (chunking.page_kind), for
        every source. A chunk whose exact text another page already holds at
        the same or higher trust is not stored again (a feature paragraph on
        the homepage, /features and a blog post): search would otherwise
        return the same passage three times. Its children point at the copy
        already stored."""
        if source not in ("public", "profile", "rulebook"):
            kind = page_kind(page_id + " " + (url or ""), chunks[0].title if chunks else "")
            for c in chunks:
                k = kind or _section_pricing(c.section if c.section != c.title else "")
                if k and c.content_type in ("doc", "blog", "section", "faq"):
                    c.content_type = k
        keymap = {c.key: "" for c in chunks}
        ids = {c.key: source + ":" + digest(page_id + c.key) for c in chunks}
        with self._db() as con:
            have = {r["id"]: r["hash"] for r in con.execute(
                "SELECT id, hash FROM chunks WHERE page_id=? AND deleted=0", (page_id,)).fetchall()}
            fresh = [c for c in chunks if ids[c.key] not in have
                     or have[ids[c.key]] != digest(c.content_type + "|" + c.text)]
            dupes = 0
            if fresh:
                keep = []
                for c in fresh:
                    other = con.execute(
                        "SELECT id FROM chunks WHERE text=? AND page_id<>? AND deleted=0 AND authority<=? "
                        "LIMIT 1", (c.text, page_id, authority)).fetchone() if len(c.text) >= 80 else None
                    if other:
                        ids[c.key] = other["id"]            # children reference the stored copy
                        dupes += 1
                    else:
                        keep.append(c)
                fresh = keep
            gone = [i for i in have if i not in set(ids.values())]
            vecs: list[Optional[np.ndarray]] = [None] * len(fresh)
            if embed and fresh:
                try:
                    vecs = E.texts([c.prefix + "\n" + c.text for c in fresh])
                except Exception:                       # noqa: BLE001 — keyword still works
                    vecs = [None] * len(fresh)
            for c, v in zip(fresh, vecs):
                con.execute(
                    "INSERT INTO chunks(id, source, authority, url, page_id, title, section, parent_id, "
                    "content_type, prefix, text, hash, updated_at, deleted, embedding) "
                    "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,0,?) ON CONFLICT(id) DO UPDATE SET "
                    "text=excluded.text, hash=excluded.hash, prefix=excluded.prefix, "
                    "updated_at=excluded.updated_at, deleted=0, embedding=excluded.embedding, "
                    "authority=excluded.authority, url=excluded.url, parent_id=excluded.parent_id, "
                    "content_type=excluded.content_type",
                    (ids[c.key], source, authority, url, page_id, c.title, c.section,
                     ids.get(c.parent_key) if c.parent_key else None, c.content_type,
                     c.prefix, c.text, digest(c.content_type + "|" + c.text), updated_at or _now(), E.to_blob(v)))
            for i in gone:
                con.execute("UPDATE chunks SET deleted=1, updated_at=? WHERE id=?", (_now(), i))
        del keymap
        return {"added_or_changed": len(fresh), "tombstoned": len(gone),
                "unchanged": len(chunks) - len(fresh) - dupes, "duplicates": dupes}

    def tidy(self) -> dict[str, int]:
        """One pass over what is already stored, for brains built before
        tagging and dedupe: legal / pricing tags, and exact duplicates across
        pages tombstoned (the most trusted, then the oldest, copy is kept and
        children of a dropped parent point at the kept one)."""
        with self._db() as con:
            rows = [dict(r) for r in con.execute(
                "SELECT id, page_id, url, title, section, source, authority, content_type, text, updated_at "
                "FROM chunks WHERE deleted=0").fetchall()]
            tagged = dropped = cleaned = 0
            # The site's menu and footer, stripped from website chunks stored
            # before strip_boilerplate existed (re-embedded; emptied ones dropped).
            from pipeline.brand_brain.chunking import strip_boilerplate
            web = [r for r in rows if r["source"] == "website"]
            pages: dict[str, list[dict]] = {}
            for r in web:
                pages.setdefault(r["page_id"], []).append(r)
            if len(pages) >= 3:
                joined = strip_boilerplate(["\n".join(x["text"] for x in rs) for rs in pages.values()])
                keep_lines = {pid: set(j.splitlines()) for pid, j in zip(pages, joined)}
                changed = []
                for pid, rs in pages.items():
                    for r in rs:
                        new = "\n".join(ln for ln in r["text"].splitlines() if ln in keep_lines[pid]).strip()
                        if new != r["text"].strip():
                            changed.append((r, new))
                vecs: list = [None] * len(changed)
                try:
                    vecs = E.texts([new for _, new in changed if new]) if changed else []
                    it = iter(vecs)
                    vecs = [next(it) if new else None for _, new in changed]
                except Exception:                       # noqa: BLE001 — keyword search still works
                    vecs = [None] * len(changed)
                for (r, new), v in zip(changed, vecs):
                    if len(new) < 40:
                        con.execute("UPDATE chunks SET deleted=1, updated_at=? WHERE id=?", (_now(), r["id"]))
                    else:
                        con.execute("UPDATE chunks SET text=?, hash=?, embedding=? WHERE id=?",
                                    (new, digest(r["content_type"] + "|" + new), E.to_blob(v), r["id"]))
                        r["text"] = new
                    cleaned += 1
            for r in rows:
                # A legal tag given from a section heading before it was page-level only.
                if r["content_type"] == "legal" and page_kind(r["page_id"] + " " + (r["url"] or ""), r["title"] or "") != "legal":
                    back = "blog" if r["source"] == "website" else "doc"
                    con.execute("UPDATE chunks SET content_type=?, hash=? WHERE id=?",
                                (back, digest(back + "|" + r["text"]), r["id"]))
                    r["content_type"] = back
                if r["source"] in ("public", "profile", "rulebook") or r["content_type"] not in ("doc", "blog", "section", "faq"):
                    continue
                k = (page_kind(r["page_id"] + " " + (r["url"] or ""), r["title"] or "")
                     or _section_pricing(r["section"] if r["section"] != r["title"] else ""))
                if k:
                    con.execute("UPDATE chunks SET content_type=?, hash=? WHERE id=?",
                                (k, digest(k + "|" + r["text"]), r["id"]))
                    tagged += 1
            by_text: dict[str, list[dict]] = {}
            for r in rows:
                if len(r["text"] or "") >= 80:
                    by_text.setdefault(r["text"], []).append(r)
            for group in by_text.values():
                if len({r["page_id"] for r in group}) < 2:
                    continue
                group.sort(key=lambda r: (r["authority"], r["updated_at"] or ""))
                keep = group[0]
                for r in group[1:]:
                    if r["page_id"] == keep["page_id"]:
                        continue
                    con.execute("UPDATE chunks SET parent_id=? WHERE parent_id=?", (keep["id"], r["id"]))
                    con.execute("UPDATE chunks SET deleted=1, updated_at=? WHERE id=?", (_now(), r["id"]))
                    dropped += 1
        return {"chunks": len(rows), "tagged": tagged, "duplicates_dropped": dropped,
                "menu_lines_cleaned": cleaned}

    def add_image(self, image_id: str, path: str, *, kind: str, caption: str = "",
                  style_tags: Optional[list[str]] = None, score: Optional[float] = None,
                  note: str = "", source: str = "", vector: Optional[np.ndarray] = None) -> None:
        with self._db() as con:
            con.execute(
                "INSERT INTO images(id, path, kind, caption, style_tags, score, note, source, embedding, created_at) "
                "VALUES (?,?,?,?,?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET kind=excluded.kind, path=excluded.path, "
                "caption=COALESCE(NULLIF(excluded.caption,''), images.caption), "
                "style_tags=COALESCE(excluded.style_tags, images.style_tags), score=excluded.score, "
                "note=excluded.note, embedding=COALESCE(excluded.embedding, images.embedding)",
                (image_id, path, kind, caption, json.dumps(style_tags) if style_tags else None,
                 score, note, source, E.to_blob(vector), _now()))

    def has_image(self, image_id: str) -> bool:
        with self._db() as con:
            r = con.execute("SELECT embedding, caption FROM images WHERE id=?", (image_id,)).fetchone()
        return bool(r and r["embedding"] and r["caption"])

    def add_event(self, event_id: str, *, at: str, kind: str, title: str, detail: str = "",
                  source: str = "", url: str = "") -> None:
        with self._db() as con:
            con.execute("INSERT INTO whats_new(id, at, kind, title, detail, source, url, created_at) "
                        "VALUES (?,?,?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET at=excluded.at, "
                        "kind=excluded.kind, title=excluded.title, detail=excluded.detail, "
                        "source=excluded.source, url=excluded.url",
                        (event_id, at, kind, title, detail, source, url, _now()))

    def set_competitor_pattern(self, pid: str, *, competitor: str, pattern: str, topic: str = "",
                               evidence_n: int = 0) -> None:
        try:
            v = E.texts([competitor + ": " + topic + " — " + pattern])[0]
        except Exception:                               # noqa: BLE001 — stored unranked
            v = None
        with self._db() as con:
            con.execute("INSERT INTO competitor_patterns(id, competitor, topic, pattern, "
                        "evidence_n, updated_at, embedding) VALUES (?,?,?,?,?,?,?) "
                        "ON CONFLICT(id) DO UPDATE SET competitor=excluded.competitor, topic=excluded.topic, "
                        "pattern=excluded.pattern, evidence_n=excluded.evidence_n, "
                        "updated_at=excluded.updated_at, embedding=excluded.embedding",
                        (pid, competitor, topic, pattern, evidence_n, _now(), E.to_blob(v)))

    def clear_competitor_patterns(self, id_prefix: str) -> int:
        """Drop one analysis's patterns before it is rewritten."""
        with self._db() as con:
            rows = con.execute("SELECT id FROM competitor_patterns").fetchall()
            gone = [r["id"] for r in rows if str(r["id"]).startswith(id_prefix)]
            for i in gone:
                con.execute("DELETE FROM competitor_patterns WHERE id=?", (i,))
        return len(gone)

    def meta(self, key: str, value: Optional[str] = None) -> Optional[str]:
        with self._db() as con:
            if value is not None:
                con.execute("INSERT INTO meta(key, value) VALUES (?,?) "
                            "ON CONFLICT(key) DO UPDATE SET value=excluded.value", (key, value))
                return value
            r = con.execute("SELECT value FROM meta WHERE key=?", (key,)).fetchone()
            return r["value"] if r else None

    def set_secret(self, name: str, ciphertext: Optional[str]) -> None:
        """Store (or with None, delete) one encrypted per-tenant secret."""
        with self._db() as con:
            if ciphertext is None:
                con.execute("DELETE FROM tenant_secrets WHERE name=?", (name,))
            else:
                con.execute("INSERT INTO tenant_secrets(name, ciphertext, updated_at) VALUES (?,?,?) "
                            "ON CONFLICT(name) DO UPDATE SET ciphertext=excluded.ciphertext, "
                            "updated_at=excluded.updated_at", (name, ciphertext, _now()))

    def get_secret(self, name: str) -> Optional[str]:
        with self._db() as con:
            r = con.execute("SELECT ciphertext FROM tenant_secrets WHERE name=?", (name,)).fetchone()
        return r["ciphertext"] if r else None

    def stats(self) -> dict[str, Any]:
        with self._db() as con:
            q = lambda s: con.execute(s).fetchone()[0]   # noqa: E731
            by_src = {r[0]: r[1] for r in con.execute(
                "SELECT source, COUNT(*) FROM chunks WHERE deleted=0 AND content_type!='section' "
                "GROUP BY source").fetchall()}
            return {
                "tenant": self.tenant,
                "backend": S.backend(),
                "profile_version": q("SELECT MAX(version) FROM profile_versions"),
                "profile_status": (con.execute("SELECT status FROM profile_versions ORDER BY "
                                               "version DESC LIMIT 1").fetchone() or [None])[0],
                "chunks": q("SELECT COUNT(*) FROM chunks WHERE deleted=0 AND content_type!='section'"),
                "chunks_embedded": q("SELECT COUNT(*) FROM chunks WHERE deleted=0 AND embedding IS NOT NULL"),
                "chunks_by_source": by_src,
                "tombstoned": q("SELECT COUNT(*) FROM chunks WHERE deleted=1"),
                "images": q("SELECT COUNT(*) FROM images"),
                "events": q("SELECT COUNT(*) FROM whats_new"),
                "competitor_patterns": q("SELECT COUNT(*) FROM competitor_patterns"),
                "outcomes": q("SELECT COUNT(*) FROM outcomes"),
                "last_ingest": (con.execute("SELECT value FROM meta WHERE key='last_ingest'")
                                .fetchone() or [None])[0],
            }
