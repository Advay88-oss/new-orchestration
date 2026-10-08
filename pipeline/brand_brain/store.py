"""Per-tenant storage: Postgres + pgvector, or one SQLite file per company.

Five stores and the feedback tables, each in the format its data needs
rather than everything in a vector index — a brand colour retrieved by
similarity search is a colour that will sometimes be wrong:

  profile_versions   the brand profile, structured JSON, versioned
  chunks             knowledge base: text, metadata, embedding, and a keyword
                     index (Postgres full-text / SQLite FTS5 BM25) so product
                     terms like "Soroban" are found by keyword even where a
                     vector search would miss them
  images             visual memory: caption, style tags, embedding, source
  whats_new          dated events, time-sorted
  competitor_patterns summaries of how competitors post — never their text
  outcomes           post metrics logged back (performance memory)
  reward_events, preference_pairs   the learning loop
  tenant_secrets     encrypted per-tenant credentials (the Notion OAuth token)

Backend: Postgres when BRAIN_DATABASE_URL is set (pipeline/.env), which is
the architecture's store — one database, tenant_id on every row, isolation
enforced by row-level security. Otherwise one SQLite file per tenant, where
isolation is the file boundary. `python -m pipeline.brand_brain.pg` sets up
the database and migrates the SQLite brains into it.
"""
from __future__ import annotations

import os
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# BRAIN_ROOT moves the tenant files (tests point a child MCP server at theirs).
ROOT = Path(os.environ.get("BRAIN_ROOT") or Path(__file__).resolve().parents[1] / "brain" / "tenants")
_TENANT = re.compile(r"^[a-z0-9][a-z0-9_-]{1,40}$")

SCHEMA = """
CREATE TABLE IF NOT EXISTS profile_versions (
  version     INTEGER PRIMARY KEY AUTOINCREMENT,
  profile     TEXT NOT NULL,
  status      TEXT NOT NULL DEFAULT 'draft',   -- draft | approved | superseded
  source      TEXT,
  note        TEXT,
  created_at  TEXT NOT NULL,
  approved_at TEXT
);

CREATE TABLE IF NOT EXISTS chunks (
  id           TEXT PRIMARY KEY,               -- source:hash
  source       TEXT NOT NULL,                  -- docs | notion | knowledge-pack | archive | website
  authority    INTEGER NOT NULL,               -- 1 founder-confirmed .. 4 archive
  url          TEXT,
  page_id      TEXT,
  title        TEXT,
  section      TEXT,
  parent_id    TEXT,                           -- the section a small chunk belongs to
  content_type TEXT NOT NULL,                  -- doc | blog | faq | fact | rule | summary
  prefix       TEXT NOT NULL,                  -- contextual line embedded with the text
  text         TEXT NOT NULL,
  hash         TEXT NOT NULL,
  updated_at   TEXT,
  deleted      INTEGER NOT NULL DEFAULT 0,     -- tombstone
  embedding    BLOB
);
CREATE INDEX IF NOT EXISTS chunks_page ON chunks(page_id);

CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts USING fts5(
  title, section, prefix, text, content='chunks', content_rowid='rowid',
  tokenize='porter unicode61'
);
CREATE TRIGGER IF NOT EXISTS chunks_ai AFTER INSERT ON chunks BEGIN
  INSERT INTO chunks_fts(rowid, title, section, prefix, text)
  VALUES (new.rowid, new.title, new.section, new.prefix, new.text);
END;
CREATE TRIGGER IF NOT EXISTS chunks_ad AFTER DELETE ON chunks BEGIN
  INSERT INTO chunks_fts(chunks_fts, rowid, title, section, prefix, text)
  VALUES ('delete', old.rowid, old.title, old.section, old.prefix, old.text);
END;
CREATE TRIGGER IF NOT EXISTS chunks_au AFTER UPDATE ON chunks BEGIN
  INSERT INTO chunks_fts(chunks_fts, rowid, title, section, prefix, text)
  VALUES ('delete', old.rowid, old.title, old.section, old.prefix, old.text);
  INSERT INTO chunks_fts(rowid, title, section, prefix, text)
  VALUES (new.rowid, new.title, new.section, new.prefix, new.text);
END;

CREATE TABLE IF NOT EXISTS images (
  id          TEXT PRIMARY KEY,                -- content hash
  path        TEXT NOT NULL,                   -- repo-relative file, or URL
  kind        TEXT NOT NULL,                   -- approved_poster | video_still | reference | logo | website
  caption     TEXT,
  style_tags  TEXT,                            -- JSON list
  score       REAL,                            -- founder rating where there is one
  note        TEXT,
  source      TEXT,
  embedding   BLOB,
  created_at  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS whats_new (
  id         TEXT PRIMARY KEY,
  at         TEXT NOT NULL,                    -- when it happened
  kind       TEXT NOT NULL,                    -- feature_launch | factual_update | milestone
  title      TEXT NOT NULL,
  detail     TEXT,
  source     TEXT,
  url        TEXT,
  created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS whats_new_at ON whats_new(at);

CREATE TABLE IF NOT EXISTS competitor_patterns (
  id          TEXT PRIMARY KEY,
  competitor  TEXT NOT NULL,
  topic       TEXT,
  pattern     TEXT NOT NULL,                   -- a summary, never their copy
  evidence_n  INTEGER NOT NULL DEFAULT 0,
  updated_at  TEXT NOT NULL,
  embedding   BLOB
);

CREATE TABLE IF NOT EXISTS outcomes (
  id        INTEGER PRIMARY KEY AUTOINCREMENT,
  post_id   TEXT NOT NULL,
  run_id    TEXT,
  metrics   TEXT NOT NULL,                     -- JSON
  source    TEXT,
  at        TEXT NOT NULL
);

-- The learning loop (Phase 4). One reward event per run, recomputed as its
-- signals arrive (reviewer at once, the founder's decision, engagement days
-- later); the arms it credits are the choices that run actually shipped.
CREATE TABLE IF NOT EXISTS reward_events (
  run_id      TEXT PRIMARY KEY,
  human       REAL,                            -- approve 1, edit 0.8, revise 0.3, kill 0
  reviewer_ok INTEGER,                         -- the hard gate: 0 makes the total 0
  engagement  REAL,                            -- normalised against this tenant's baseline
  total       REAL,
  arms        TEXT NOT NULL,                   -- JSON {dimension: option}
  context     TEXT NOT NULL,                   -- JSON {platform, day_type, whats_new, ...}
  at          TEXT NOT NULL
);

-- Draft vs the founder's edit: the preference dataset a later DPO step
-- would train on. Collected only; nothing trains on it yet.
CREATE TABLE IF NOT EXISTS preference_pairs (
  id        INTEGER PRIMARY KEY AUTOINCREMENT,
  run_id    TEXT NOT NULL,
  platform  TEXT NOT NULL,
  context   TEXT,                              -- the brief the draft was written from
  rejected  TEXT NOT NULL,                     -- the draft
  chosen    TEXT NOT NULL,                     -- the founder's final
  source    TEXT,
  at        TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS meta (
  key   TEXT PRIMARY KEY,
  value TEXT
);

CREATE TABLE IF NOT EXISTS tenant_secrets (
  name        TEXT PRIMARY KEY,
  ciphertext  TEXT NOT NULL,
  updated_at  TEXT NOT NULL
);
-- The assistant: conversations per company, and every action it started or
-- the owner confirmed from the chat.
CREATE TABLE IF NOT EXISTS chat_threads (
  id          TEXT PRIMARY KEY,
  title       TEXT,
  summary     TEXT,                            -- rolling summary of older messages
  summarized  INTEGER NOT NULL DEFAULT 0,      -- how many messages the summary covers
  created_at  TEXT NOT NULL,
  updated_at  TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS chat_messages (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  thread_id   TEXT NOT NULL,
  role        TEXT NOT NULL,                   -- user | assistant
  text        TEXT NOT NULL,
  meta        TEXT,                            -- JSON: tools, cards, grounding, error
  at          TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS chat_messages_thread ON chat_messages(thread_id, id);
CREATE TABLE IF NOT EXISTS audit_log (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  at          TEXT NOT NULL,
  actor       TEXT NOT NULL,                   -- assistant | owner
  action      TEXT NOT NULL,
  detail      TEXT,                            -- JSON
  thread_id   TEXT
);
"""

# ------------------------------------------------------------------ Postgres
#
# The architecture's store: one Postgres with pgvector. Every table carries
# tenant_id, and row-level security enforces the isolation rule in the
# database itself, not only in this code: the app connects as `brain_app`,
# a role that owns nothing and cannot bypass RLS, and every connection is
# bound to one tenant (`app.tenant`) before its first query. A query that
# forgets a WHERE clause still sees one company's rows.
#
# tenant_id defaults to the bound tenant, so the application's INSERTs are
# the same SQL on both backends.

TENANT_COL = "tenant_id TEXT NOT NULL DEFAULT current_setting('app.tenant')"
PG_TABLES = ("profile_versions", "chunks", "images", "whats_new", "competitor_patterns",
             "outcomes", "reward_events", "preference_pairs", "meta", "tenant_secrets",
             "chat_threads", "chat_messages", "audit_log")

PG_SCHEMA = f"""
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS tenants (
  id          TEXT PRIMARY KEY,
  created_at  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS profile_versions (
  {TENANT_COL},
  version     INTEGER NOT NULL,
  profile     TEXT NOT NULL,
  status      TEXT NOT NULL DEFAULT 'draft',
  source      TEXT,
  note        TEXT,
  created_at  TEXT NOT NULL,
  approved_at TEXT,
  PRIMARY KEY (tenant_id, version)
);

CREATE TABLE IF NOT EXISTS chunks (
  {TENANT_COL},
  id           TEXT NOT NULL,
  source       TEXT NOT NULL,
  authority    INTEGER NOT NULL,
  url          TEXT,
  page_id      TEXT,
  title        TEXT,
  section      TEXT,
  parent_id    TEXT,
  content_type TEXT NOT NULL,
  prefix       TEXT NOT NULL,
  text         TEXT NOT NULL,
  hash         TEXT NOT NULL,
  updated_at   TEXT,
  deleted      INTEGER NOT NULL DEFAULT 0,
  embedding    vector({768}),
  -- Postgres full-text: title and section weigh more than the body, the way
  -- the SQLite FTS5 bm25() weights did.
  tsv          tsvector GENERATED ALWAYS AS (
                 setweight(to_tsvector('english', coalesce(title, '') || ' ' || coalesce(section, '')), 'A') ||
                 setweight(to_tsvector('english', coalesce(prefix, '') || ' ' || text), 'B')) STORED,
  PRIMARY KEY (tenant_id, id)
);
CREATE INDEX IF NOT EXISTS chunks_page ON chunks (tenant_id, page_id);
CREATE INDEX IF NOT EXISTS chunks_tsv ON chunks USING gin (tsv);
CREATE INDEX IF NOT EXISTS chunks_vec ON chunks USING hnsw (embedding vector_cosine_ops);

CREATE TABLE IF NOT EXISTS images (
  {TENANT_COL},
  id          TEXT NOT NULL,
  path        TEXT NOT NULL,
  kind        TEXT NOT NULL,
  caption     TEXT,
  style_tags  TEXT,
  score       REAL,
  note        TEXT,
  source      TEXT,
  embedding   vector({768}),
  created_at  TEXT NOT NULL,
  PRIMARY KEY (tenant_id, id)
);

CREATE TABLE IF NOT EXISTS whats_new (
  {TENANT_COL},
  id         TEXT NOT NULL,
  at         TEXT NOT NULL,
  kind       TEXT NOT NULL,
  title      TEXT NOT NULL,
  detail     TEXT,
  source     TEXT,
  url        TEXT,
  created_at TEXT NOT NULL,
  PRIMARY KEY (tenant_id, id)
);
CREATE INDEX IF NOT EXISTS whats_new_at ON whats_new (tenant_id, at);

CREATE TABLE IF NOT EXISTS competitor_patterns (
  {TENANT_COL},
  id          TEXT NOT NULL,
  competitor  TEXT NOT NULL,
  topic       TEXT,
  pattern     TEXT NOT NULL,
  evidence_n  INTEGER NOT NULL DEFAULT 0,
  updated_at  TEXT NOT NULL,
  embedding   vector({768}),
  PRIMARY KEY (tenant_id, id)
);

CREATE TABLE IF NOT EXISTS outcomes (
  {TENANT_COL},
  id        BIGINT GENERATED BY DEFAULT AS IDENTITY,
  post_id   TEXT NOT NULL,
  run_id    TEXT,
  metrics   TEXT NOT NULL,
  source    TEXT,
  at        TEXT NOT NULL,
  PRIMARY KEY (tenant_id, id)
);

CREATE TABLE IF NOT EXISTS reward_events (
  {TENANT_COL},
  run_id      TEXT NOT NULL,
  human       REAL,
  reviewer_ok INTEGER,
  engagement  REAL,
  total       REAL,
  arms        TEXT NOT NULL,
  context     TEXT NOT NULL,
  at          TEXT NOT NULL,
  PRIMARY KEY (tenant_id, run_id)
);

CREATE TABLE IF NOT EXISTS preference_pairs (
  {TENANT_COL},
  id        BIGINT GENERATED BY DEFAULT AS IDENTITY,
  run_id    TEXT NOT NULL,
  platform  TEXT NOT NULL,
  context   TEXT,
  rejected  TEXT NOT NULL,
  chosen    TEXT NOT NULL,
  source    TEXT,
  at        TEXT NOT NULL,
  PRIMARY KEY (tenant_id, id)
);

CREATE TABLE IF NOT EXISTS meta (
  {TENANT_COL},
  key   TEXT NOT NULL,
  value TEXT,
  PRIMARY KEY (tenant_id, key)
);

-- Per-tenant secrets (the Notion OAuth token), encrypted by the app before
-- they reach the database. Revoking deletes the row.
CREATE TABLE IF NOT EXISTS tenant_secrets (
  {TENANT_COL},
  name        TEXT NOT NULL,
  ciphertext  TEXT NOT NULL,
  updated_at  TEXT NOT NULL,
  PRIMARY KEY (tenant_id, name)
);
CREATE TABLE IF NOT EXISTS chat_threads (
  {TENANT_COL},
  id          TEXT NOT NULL,
  title       TEXT,
  summary     TEXT,
  summarized  INTEGER NOT NULL DEFAULT 0,
  created_at  TEXT NOT NULL,
  updated_at  TEXT NOT NULL,
  PRIMARY KEY (tenant_id, id)
);
CREATE TABLE IF NOT EXISTS chat_messages (
  {TENANT_COL},
  id          BIGINT GENERATED BY DEFAULT AS IDENTITY,
  thread_id   TEXT NOT NULL,
  role        TEXT NOT NULL,
  text        TEXT NOT NULL,
  meta        TEXT,
  at          TEXT NOT NULL,
  PRIMARY KEY (tenant_id, id)
);
CREATE INDEX IF NOT EXISTS chat_messages_thread ON chat_messages (tenant_id, thread_id, id);
CREATE TABLE IF NOT EXISTS audit_log (
  {TENANT_COL},
  id          BIGINT GENERATED BY DEFAULT AS IDENTITY,
  at          TEXT NOT NULL,
  actor       TEXT NOT NULL,
  action      TEXT NOT NULL,
  detail      TEXT,
  thread_id   TEXT,
  PRIMARY KEY (tenant_id, id)
);
"""


def pg_policies_sql(app_role: str) -> str:
    """RLS on every tenant table, and the app role's grants."""
    out = []
    for t in PG_TABLES:
        out += [f"ALTER TABLE {t} ENABLE ROW LEVEL SECURITY;",
                f"ALTER TABLE {t} FORCE ROW LEVEL SECURITY;",
                f"DROP POLICY IF EXISTS tenant_isolation ON {t};",
                f"CREATE POLICY tenant_isolation ON {t} "
                f"USING (tenant_id = current_setting('app.tenant', true)) "
                f"WITH CHECK (tenant_id = current_setting('app.tenant', true));",
                f"GRANT SELECT, INSERT, UPDATE, DELETE ON {t} TO {app_role};"]
    out += ["GRANT SELECT, INSERT ON tenants TO " + app_role + ";",
            "GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO " + app_role + ";"]
    return "\n".join(out)


# ------------------------------------------------------------------ backends

OVERRIDE: Optional[str] = None       # tests set "sqlite"


def _env_file(key: str) -> Optional[str]:
    """A setting from the environment (Cloud Run, from Secret Manager), else
    pipeline/.env (last definition wins). Never printed."""
    if os.environ.get(key):
        return os.environ[key]
    f = Path(__file__).resolve().parents[1] / ".env"
    val = None
    try:
        for line in f.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith(key + "="):
                val = line.split("=", 1)[1].strip().strip('"').strip("'") or None
    except OSError:
        pass
    return val


def database_url() -> Optional[str]:
    # BRAIN_BACKEND=sqlite pins the file backend (tests, and their child
    # MCP servers, which cannot see an in-process OVERRIDE).
    if OVERRIDE == "sqlite" or os.environ.get("BRAIN_BACKEND") == "sqlite":
        return None
    return os.environ.get("BRAIN_DATABASE_URL") or _env_file("BRAIN_DATABASE_URL")


FELL_BACK = False                                   # set when Postgres could not be reached


def backend() -> str:
    global OVERRIDE, FELL_BACK
    if OVERRIDE == "sqlite" or os.environ.get("BRAIN_BACKEND") == "sqlite":
        return "sqlite"
    u = database_url()
    if not u:
        return "sqlite"
    if "127.0.0.1:5433" in u:
        import socket
        try:
            with socket.create_connection(("127.0.0.1", 5433), timeout=0.5):
                return "pg"
        except OSError:
            OVERRIDE, FELL_BACK = "sqlite", True
            return "sqlite"
    if "/cloudsql/" in u:
        return "pg"
    # The laptop's Cloud SQL address often does not answer. Chat must still work.
    try:
        from pipeline.gtm_os.state_sync import in_cloud
        remote = not in_cloud()
    except Exception:                               # noqa: BLE001 — treat an unknown host as local
        remote = True
    if remote:
        import psycopg
        try:
            con = psycopg.connect(u, connect_timeout=3)
            con.close()
        except Exception:                           # noqa: BLE001 — the file brain is the fallback
            OVERRIDE, FELL_BACK = "sqlite", True
            os.environ["BRAIN_BACKEND"] = "sqlite"
            os.environ["BRAIN_FELL_BACK"] = "1"     # child processes inherit the pin: say why
            return "sqlite"
    return "pg"


def in_fallback() -> bool:
    """True when a Postgres brain is configured but this process fell back to
    the SQLite files (it could not reach the database). The files are then
    older than the database: they serve chat, and are never backed up over
    the real brain (state_sync._brain_snapshot)."""
    backend()
    return FELL_BACK or os.environ.get("BRAIN_FELL_BACK") == "1"


class TenantError(ValueError):
    pass


def tenant_dir(tenant: str) -> Path:
    """The tenant's files (images, caches). The rows live in the database."""
    if not _TENANT.match(str(tenant or "")):
        raise TenantError("invalid tenant id: " + repr(tenant))
    return ROOT / tenant


def _pg_raw():
    global OVERRIDE, FELL_BACK
    import time
    import psycopg

    url = database_url()
    # Cloud SQL's socket is often not ready in the first few seconds of a
    # cold job. Three seconds was turning that wait into a failed post.
    timeout = 20 if url and "/cloudsql/" in url else 10
    last_err = None
    for attempt in range(1, 4):
        try:
            return psycopg.connect(
                url,
                connect_timeout=timeout,
                keepalives=1,
                keepalives_idle=30,
                keepalives_interval=10,
                keepalives_count=5,
            )
        except Exception as exc:
            last_err = exc
            if attempt < 3:
                time.sleep(attempt)
    if url and "127.0.0.1:5433" in url:
        OVERRIDE, FELL_BACK = "sqlite", True
    raise last_err


def exists(tenant: str) -> bool:
    tenant_dir(tenant)
    if backend() == "pg":
        with _pg_raw() as con:
            return con.execute("SELECT 1 FROM tenants WHERE id=%s", (tenant,)).fetchone() is not None
    return (tenant_dir(tenant) / "brain.db").exists()


def tenants() -> list[str]:
    if backend() == "pg":
        with _pg_raw() as con:
            return [r[0] for r in con.execute("SELECT id FROM tenants ORDER BY id").fetchall()]
    return sorted(p.name for p in ROOT.glob("*") if (p / "brain.db").exists()) if ROOT.exists() else []


class Row(dict):
    """A result row readable by column name or position, like sqlite3.Row."""

    def __init__(self, cols: list[str], values):
        super().__init__(zip(cols, values))
        self._values = list(values)

    def __getitem__(self, k):
        return self._values[k] if isinstance(k, int) else super().__getitem__(k)

    def keys(self):
        return list(super().keys())


class _PgCursor:
    def __init__(self, cur):
        self._cur = cur

    def _cols(self) -> list[str]:
        return [d.name for d in (self._cur.description or [])]

    def fetchone(self):
        r = self._cur.fetchone()
        return None if r is None else Row(self._cols(), r)

    def fetchall(self):
        cols = self._cols()
        return [Row(cols, r) for r in self._cur.fetchall()]

    def __iter__(self):
        return iter(self.fetchall())


_QMARK = re.compile(r"\?")
_CONFLICT = re.compile(r"ON CONFLICT\s*\(\s*(?!tenant_id)([^)]*)\)", re.I)


def _vec_literal(b: bytes) -> str:
    import numpy as np
    return "[" + ",".join(f"{x:.7g}" for x in np.frombuffer(b, dtype=np.float32)) + "]"


class PgConnection:
    """The subset of sqlite3.Connection the brain uses, on Postgres.

    SQL is written once, in SQLite style: `?` placeholders become `%s`, an
    upsert's conflict target gains tenant_id, and an embedding (bytes) becomes
    a pgvector literal. Rows read by name or position.
    """

    def __init__(self, tenant: str):
        self._con = _pg_raw()
        self._con.execute("SELECT set_config('app.tenant', %s, false)", (tenant,))
        self.tenant = tenant

    @staticmethod
    def translate(sql: str) -> str:
        sql = sql.replace("%", "%%")
        sql = _QMARK.sub("%s", sql)
        return _CONFLICT.sub(lambda m: "ON CONFLICT (tenant_id, " + m.group(1) + ")", sql)

    def execute(self, sql: str, params=()):
        args = [(_vec_literal(p) if isinstance(p, (bytes, bytearray, memoryview)) else p)
                for p in (params or ())]
        return _PgCursor(self._con.execute(self.translate(sql), args))

    def commit(self) -> None:
        self._con.commit()

    def rollback(self) -> None:
        self._con.rollback()

    def close(self) -> None:
        self._con.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        if exc_type is None:
            self._con.commit()
        else:
            self._con.rollback()
        return False


def connect(tenant: str, *, create: bool = False):
    """Open exactly one tenant's brain. Never another's."""
    d = tenant_dir(tenant)
    if backend() == "pg":
        con = PgConnection(tenant)
        known = con.execute("SELECT 1 FROM tenants WHERE id=?", (tenant,)).fetchone()
        if not known:
            if not create:
                con.close()
                raise TenantError("no brain for tenant " + repr(tenant)
                                  + " — onboard it first (python -m pipeline.brand_brain init)")
            # tenants has no tenant_id column, so this skips the translator.
            con._con.execute("INSERT INTO tenants(id, created_at) VALUES (%s, %s) ON CONFLICT (id) DO NOTHING",
                             (tenant, datetime.now(timezone.utc).isoformat()))
            con.commit()
        return con
    db = d / "brain.db"
    if not db.exists() and not create:
        raise TenantError("no brain for tenant " + repr(tenant)
                          + " — onboard it first (python -m pipeline.brand_brain init)")
    d.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(str(db), timeout=30)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA journal_mode=WAL")
    con.executescript(SCHEMA)
    return con
