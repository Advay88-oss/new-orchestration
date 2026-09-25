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
from pipeline.brand_brain.chunking import Chunk, digest

# How much a source is trusted when two disagree: 1 founder-confirmed (the
# Notion ground truth), 2 the live docs, 3 the internal knowledge pack,
# 4 archive (the August knowledge base, which predates the Stellar-only
# deployment in places). Archive is found, but ranked below and marked, and
# the reviewer does not accept it alone as proof of a claim.
AUTHORITY_WEIGHT = {1: 1.0, 2: 0.95, 3: 0.85, 4: 0.6}
_WORD = re.compile(r"[A-Za-z0-9][A-Za-z0-9.\-]{1,}")
_vec_cache: dict[str, tuple[float, list[str], np.ndarray]] = {}
_vec_lock = threading.Lock()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def current_tenant() -> str:
    """The tenant this process serves: the session's, else Vanna (tenant #1)."""
    return os.environ.get("BRAIN_TENANT") or os.environ.get("VANNA_TENANT") or "vanna"


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
                         max_authority: int = 4) -> list[dict]:
        """Hybrid search: BM25 keyword + vector, fused by reciprocal rank.

        Keyword search is what finds product names and terms ("Soroban",
        "health factor") that a vector search can rank below a paraphrase.
        Results carry their source, URL, authority and the parent section.
        """
        # Code listings only when asked for: a product question is not
        # answered by a Rust signature.
        ct = set(content_types or [])
        skip_code = "code" not in ct
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
                        or (src and r["source"] not in src)
                        or r["authority"] > max_authority):
                    continue
                out.append((score * AUTHORITY_WEIGHT.get(r["authority"], 0.5), r))
            out.sort(key=lambda x: -x[0])
            results = []
            for score, r in out[:k]:
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
    def _bm25(con: sqlite3.Connection, query: str, n: int) -> list[str]:
        terms = [t for t in _WORD.findall(query) if len(t) > 1][:24]
        if not terms:
            return []
        match = " OR ".join('"' + t.replace('"', "") + '"' for t in terms)
        try:
            rows = con.execute(
                "SELECT c.id FROM chunks_fts f JOIN chunks c ON c.rowid=f.rowid "
                "WHERE chunks_fts MATCH ? AND c.deleted=0 AND c.content_type!='section' "
                "ORDER BY bm25(chunks_fts, 2.0, 2.0, 1.0, 1.0) LIMIT ?", (match, n)).fetchall()
        except sqlite3.OperationalError:
            return []
        return [r["id"] for r in rows]

    def _vector(self, con: sqlite3.Connection, q: np.ndarray, n: int) -> list[str]:
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
            cur = con.execute(
                "INSERT INTO profile_versions(profile, status, source, note, created_at, approved_at) "
                "VALUES (?,?,?,?,?,?)",
                (json.dumps(clean, ensure_ascii=False), status, source, note, _now(),
                 _now() if status == "approved" else None))
            return int(cur.lastrowid)

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

    def upsert_page(self, page_id: str, chunks: list[Chunk], *, source: str, authority: int,
                    url: Optional[str] = None, updated_at: Optional[str] = None,
                    embed: bool = True) -> dict[str, int]:
        """Incremental: unchanged chunks are kept, changed ones re-embedded,
        vanished ones tombstoned. Returns what changed."""
        keymap = {c.key: "" for c in chunks}
        ids = {c.key: source + ":" + digest(page_id + c.key) for c in chunks}
        with self._db() as con:
            have = {r["id"]: r["hash"] for r in con.execute(
                "SELECT id, hash FROM chunks WHERE page_id=? AND deleted=0", (page_id,)).fetchall()}
            fresh = [c for c in chunks if ids[c.key] not in have
                     or have[ids[c.key]] != digest(c.content_type + "|" + c.text)]
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
                "unchanged": len(chunks) - len(fresh)}

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
            con.execute("INSERT OR REPLACE INTO whats_new(id, at, kind, title, detail, source, url, created_at) "
                        "VALUES (?,?,?,?,?,?,?,?)", (event_id, at, kind, title, detail, source, url, _now()))

    def set_competitor_pattern(self, pid: str, *, competitor: str, pattern: str, topic: str = "",
                               evidence_n: int = 0) -> None:
        try:
            v = E.texts([competitor + ": " + topic + " — " + pattern])[0]
        except Exception:                               # noqa: BLE001 — stored unranked
            v = None
        with self._db() as con:
            con.execute("INSERT OR REPLACE INTO competitor_patterns(id, competitor, topic, pattern, "
                        "evidence_n, updated_at, embedding) VALUES (?,?,?,?,?,?,?)",
                        (pid, competitor, topic, pattern, evidence_n, _now(), E.to_blob(v)))

    def meta(self, key: str, value: Optional[str] = None) -> Optional[str]:
        with self._db() as con:
            if value is not None:
                con.execute("INSERT OR REPLACE INTO meta(key, value) VALUES (?,?)", (key, value))
                return value
            r = con.execute("SELECT value FROM meta WHERE key=?", (key,)).fetchone()
            return r["value"] if r else None

    def stats(self) -> dict[str, Any]:
        with self._db() as con:
            q = lambda s: con.execute(s).fetchone()[0]   # noqa: E731
            by_src = {r[0]: r[1] for r in con.execute(
                "SELECT source, COUNT(*) FROM chunks WHERE deleted=0 AND content_type!='section' "
                "GROUP BY source").fetchall()}
            return {
                "tenant": self.tenant,
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
