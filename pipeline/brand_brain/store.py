"""Per-tenant storage: one SQLite file per company.

Five stores and the feedback table, each in the format its data needs
rather than everything in a vector index — a brand colour retrieved by
similarity search is a colour that will sometimes be wrong:

  profile_versions   the brand profile, structured JSON, versioned
  chunks + chunks_fts knowledge base: text, metadata, embedding, and an FTS5
                     index (BM25) so product terms like "Soroban" are found
                     by keyword even where a vector search would miss them
  images             visual memory: caption, style tags, embedding, source
  whats_new          dated events, time-sorted
  competitor_patterns summaries of how competitors post — never their text
  outcomes           post metrics logged back (performance memory)

Isolation: `connect(tenant)` validates the id and opens only that tenant's
file. There is no query path that can reach another tenant's rows, because
they are in another database.
"""
from __future__ import annotations

import re
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "brain" / "tenants"
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
"""


class TenantError(ValueError):
    pass


def tenant_dir(tenant: str) -> Path:
    if not _TENANT.match(str(tenant or "")):
        raise TenantError("invalid tenant id: " + repr(tenant))
    return ROOT / tenant


def exists(tenant: str) -> bool:
    return (tenant_dir(tenant) / "brain.db").exists()


def tenants() -> list[str]:
    return sorted(p.name for p in ROOT.glob("*") if (p / "brain.db").exists()) if ROOT.exists() else []


def connect(tenant: str, *, create: bool = False) -> sqlite3.Connection:
    """Open exactly one tenant's brain. Never another's."""
    d = tenant_dir(tenant)
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
