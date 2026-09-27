"""Postgres for the brand brain: set up, migrate, export, check isolation.

    python -m pipeline.brand_brain.pg setup            # container, database, role, schema, RLS
    python -m pipeline.brand_brain.pg migrate          # SQLite brains -> Postgres, then switch over
    python -m pipeline.brand_brain.pg status
    python -m pipeline.brand_brain.pg check-isolation  # prove one tenant cannot read another
    python -m pipeline.brand_brain.pg export vanna out.db   # a portable SQLite copy (GCS snapshots)
    python -m pipeline.brand_brain.pg use-sqlite       # switch back (the SQLite files are kept)

`setup` runs pgvector/pgvector:pg17 in Docker on 127.0.0.1:5433 (this machine
only) with a named volume, and creates two logins with generated passwords:
the admin (owns the schema) and `brain_app` (what the pipeline uses — it owns
nothing, so row-level security always applies to it). Both connection
strings are written to pipeline/.env and never printed. For Cloud SQL or any
other Postgres, put its URLs in .env instead and skip the container.

`migrate` copies every table of every SQLite brain, checks the row counts,
and only then sets BRAIN_DATABASE_URL, which is what switches the pipeline
over. Until that line exists nothing reads Postgres.
"""
from __future__ import annotations

import json
import re
import secrets
import sqlite3
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

from pipeline.brand_brain import store as S

ENV = Path(__file__).resolve().parents[1] / ".env"
CONTAINER = "brand-brain-pg"
IMAGE = "pgvector/pgvector:pg17"
VOLUME = "brand-brain-pgdata"
PORT = 5433
DB = "brand_brain"
APP_ROLE = "brain_app"
# Copied in this order; tsv is generated, so it is never copied.
TABLES = ("profile_versions", "chunks", "images", "whats_new", "competitor_patterns",
          "outcomes", "reward_events", "preference_pairs", "meta", "tenant_secrets",
          "chat_threads", "chat_messages", "audit_log")
IDENTITY = ("outcomes", "preference_pairs", "chat_messages", "audit_log")


# --------------------------------------------------------------------- .env

def _set_env(key: str, value: str | None) -> None:
    """Set or remove one key in pipeline/.env, leaving every other line alone."""
    lines = ENV.read_text(encoding="utf-8").splitlines() if ENV.exists() else []
    out = [l for l in lines if not l.strip().startswith(key + "=")]
    if value is not None:
        out.append(key + "=" + value)
    ENV.write_text("\n".join(out) + "\n", encoding="utf-8")


def _admin_url() -> str:
    u = S._env_file("BRAIN_PG_ADMIN_URL")
    if not u:
        raise SystemExit("BRAIN_PG_ADMIN_URL is not in pipeline/.env — run `setup` first")
    return u


def _app_url() -> str:
    u = S._env_file("BRAIN_PG_APP_URL")
    if not u:
        raise SystemExit("BRAIN_PG_APP_URL is not in pipeline/.env — run `setup` first")
    return u


# ------------------------------------------------------------------- docker

def _docker(*args: str, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(["docker", *args], capture_output=True, text=True, check=check)


def _container_exists() -> bool:
    r = _docker("ps", "-a", "--filter", "name=^" + CONTAINER + "$", "--format", "{{.Names}}", check=False)
    return r.stdout.strip() == CONTAINER


def _wait_ready(timeout: int = 90) -> None:
    t = time.time()
    while time.time() - t < timeout:
        r = _docker("exec", CONTAINER, "pg_isready", "-U", "postgres", "-d", DB, check=False)
        if r.returncode == 0:
            return
        time.sleep(2)
    raise SystemExit("Postgres did not become ready in " + str(timeout) + "s")


def setup() -> dict[str, Any]:
    import psycopg
    created = False
    if not _container_exists():
        admin_pw = secrets.token_urlsafe(24)
        # The password goes through an env file, not the command line, so it
        # is not visible in the process list.
        with tempfile.NamedTemporaryFile("w", suffix=".env", delete=False) as f:
            f.write("POSTGRES_PASSWORD=" + admin_pw + "\nPOSTGRES_DB=" + DB + "\n")
            env_file = f.name
        try:
            _docker("run", "-d", "--name", CONTAINER, "--env-file", env_file,
                    "-p", "127.0.0.1:" + str(PORT) + ":5432", "-v", VOLUME + ":/var/lib/postgresql/data",
                    "--restart", "unless-stopped", IMAGE)
        finally:
            Path(env_file).unlink(missing_ok=True)
        _set_env("BRAIN_PG_ADMIN_URL", f"postgresql://postgres:{admin_pw}@127.0.0.1:{PORT}/{DB}")
        created = True
    else:
        _docker("start", CONTAINER, check=False)
    _wait_ready()

    app_pw = None if S._env_file("BRAIN_PG_APP_URL") else secrets.token_urlsafe(24)
    with psycopg.connect(_admin_url(), autocommit=True, connect_timeout=15) as con:
        con.execute(S.PG_SCHEMA)
        has_role = con.execute("SELECT 1 FROM pg_roles WHERE rolname=%s", (APP_ROLE,)).fetchone()
        if app_pw:
            # psycopg cannot bind a parameter in CREATE/ALTER ROLE; the password
            # is generated here (url-safe alphabet), so quoting is safe.
            verb = "ALTER" if has_role else "CREATE"
            con.execute(f"{verb} ROLE {APP_ROLE} LOGIN PASSWORD '{app_pw}' "
                        "NOSUPERUSER NOBYPASSRLS NOCREATEDB NOCREATEROLE")
        con.execute(f"GRANT CONNECT ON DATABASE {DB} TO {APP_ROLE}")
        con.execute(f"GRANT USAGE ON SCHEMA public TO {APP_ROLE}")
        con.execute(S.pg_policies_sql(APP_ROLE))
    if app_pw:
        _set_env("BRAIN_PG_APP_URL", f"postgresql://{APP_ROLE}:{app_pw}@127.0.0.1:{PORT}/{DB}")
    return {"ok": True, "container_created": created, "container": CONTAINER, "port": PORT,
            "database": DB, "app_role": APP_ROLE, "switched_over": bool(S._env_file("BRAIN_DATABASE_URL"))}


def apply_schema(admin_url: str, app_password: str | None = None) -> dict[str, Any]:
    """Schema, RLS policies and the app role on any Postgres (Cloud SQL: the
    admin is the instance's `postgres` user). Idempotent."""
    import psycopg
    with psycopg.connect(admin_url, autocommit=True, connect_timeout=20) as con:
        con.execute(S.PG_SCHEMA)
        has_role = con.execute("SELECT 1 FROM pg_roles WHERE rolname=%s", (APP_ROLE,)).fetchone()
        if app_password:
            if not re.fullmatch(r"[A-Za-z0-9_\-]{16,128}", app_password):
                raise ValueError("app password must be 16-128 url-safe characters")
            verb = "ALTER" if has_role else "CREATE"
            con.execute(f"{verb} ROLE {APP_ROLE} LOGIN PASSWORD '{app_password}' "
                        "NOSUPERUSER NOBYPASSRLS NOCREATEDB NOCREATEROLE")
        elif not has_role:
            raise ValueError("the app role does not exist yet: pass its password")
        db = con.execute("SELECT current_database()").fetchone()[0]
        con.execute(f"GRANT CONNECT ON DATABASE {db} TO {APP_ROLE}")
        con.execute(f"GRANT USAGE ON SCHEMA public TO {APP_ROLE}")
        con.execute(S.pg_policies_sql(APP_ROLE))
        # The owner's ops tables (budget, alerts, errors): global, no company content.
        from pipeline.ops.budget import PG_SCHEMA as OPS
        con.execute(OPS)
        for t in ("ops_spend", "ops_counters", "ops_alerts", "ops_errors"):
            con.execute(f"GRANT SELECT, INSERT, UPDATE, DELETE ON {t} TO {APP_ROLE}")
        n = con.execute("SELECT count(*) FROM tenants").fetchone()[0]
    return {"ok": True, "database": db, "app_role": APP_ROLE, "tenants": n}


# ------------------------------------------------------------------ migrate

def _sqlite_rows(db: Path, table: str) -> tuple[list[str], list[tuple]]:
    con = sqlite3.connect(str(db))
    try:
        cur = con.execute("SELECT * FROM " + table)
        cols = [d[0] for d in cur.description]
        return cols, cur.fetchall()
    except sqlite3.OperationalError:              # an older brain without this table
        return [], []
    finally:
        con.close()


def _pg_count(con, table: str) -> int:
    return int(con.execute("SELECT COUNT(*) FROM " + table).fetchone()[0])


def migrate_tenant(tenant: str, db: Path, app_url: str) -> dict[str, Any]:
    """Replace this tenant's rows in Postgres with the SQLite brain's."""
    import os
    os.environ["BRAIN_DATABASE_URL"] = app_url            # this process only
    con = S.connect(tenant, create=True)                  # binds app.tenant; RLS scopes every row
    report: dict[str, Any] = {}
    try:
        for t in TABLES:
            cols, rows = _sqlite_rows(db, t)
            con.execute("DELETE FROM " + t)               # this tenant's rows only (RLS)
            if rows:
                sql = ("INSERT INTO " + t + "(" + ", ".join(cols) + ") VALUES ("
                       + ", ".join("?" * len(cols)) + ")")
                for r in rows:
                    con.execute(sql, tuple(r))
            report[t] = (len(rows), None)
        con.commit()
        for t in TABLES:
            report[t] = (report[t][0], _pg_count(con, t))
    finally:
        con.close()
    bad = {t: v for t, v in report.items() if v[0] != v[1]}
    return {"tenant": tenant, "ok": not bad, "rows": {t: v[0] for t, v in report.items()}, "mismatch": bad}


def migrate(tenants: list[str] | None = None) -> dict[str, Any]:
    import psycopg
    app_url = _app_url()
    prev = S.OVERRIDE
    S.OVERRIDE = "sqlite"
    try:
        found = tenants or S.tenants()
    finally:
        S.OVERRIDE = prev
    results = []
    for t in found:
        db = S.tenant_dir(t) / "brain.db"
        if not db.exists():
            results.append({"tenant": t, "ok": False, "error": "no SQLite brain"})
            continue
        results.append(migrate_tenant(t, db, app_url))
    # Explicit ids were copied; move the identity sequences past them.
    with psycopg.connect(_admin_url(), autocommit=True) as con:
        for t in IDENTITY:
            con.execute(f"SELECT setval(pg_get_serial_sequence('{t}', 'id'), "
                        f"GREATEST((SELECT COALESCE(MAX(id), 0) FROM {t}), 1))")
    ok = bool(results) and all(r.get("ok") for r in results)
    if ok:
        _set_env("BRAIN_DATABASE_URL", app_url)          # the switch-over
    return {"ok": ok, "switched_over": ok, "tenants": results}


def use_sqlite() -> dict[str, Any]:
    _set_env("BRAIN_DATABASE_URL", None)
    return {"ok": True, "backend": "sqlite",
            "note": "SQLite brains were left as they were at migration; writes since then are in Postgres"}


# ------------------------------------------------------------------- export

def export(tenant: str, out: Path) -> Path:
    """A portable SQLite copy of one tenant's Postgres brain."""
    from pipeline.brand_brain import embed as E
    src = S.connect(tenant)
    if not isinstance(src, S.PgConnection):
        src.close()
        raise SystemExit("the brain is on SQLite already")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.unlink(missing_ok=True)
    dst = sqlite3.connect(str(out))
    dst.executescript(S.SCHEMA)
    try:
        for t in TABLES:
            rows = src.execute("SELECT * FROM " + t).fetchall()
            for r in rows:
                cols = [c for c in r.keys() if c not in ("tenant_id", "tsv")]
                vals = []
                for c in cols:
                    v = r[c]
                    if c == "embedding" and v is not None:
                        v = E.to_blob(E.from_blob(v))
                    vals.append(v)
                dst.execute("INSERT INTO " + t + "(" + ", ".join(cols) + ") VALUES ("
                            + ", ".join("?" * len(cols)) + ")", vals)
        dst.commit()
    finally:
        dst.close()
        src.close()
    return out


# ------------------------------------------------------------------- checks

def status() -> dict[str, Any]:
    out: dict[str, Any] = {"backend": S.backend(), "container": None}
    try:
        r = _docker("inspect", "-f", "{{.State.Status}}", CONTAINER, check=False)
        out["container"] = r.stdout.strip() or "absent"
    except FileNotFoundError:
        out["container"] = "docker not installed"
    if S.backend() == "pg":
        out["tenants"] = {}
        for t in S.tenants():
            con = S.connect(t)
            try:
                out["tenants"][t] = {tb: _pg_count(con, tb) for tb in TABLES}
            finally:
                con.close()
    return out


def check_isolation() -> dict[str, Any]:
    """Bind a connection to each tenant and try to read the others' rows."""
    import os
    os.environ.setdefault("BRAIN_DATABASE_URL", _app_url())
    ts = S.tenants()
    if len(ts) < 2:
        # A throwaway second tenant, so the check has something to not see.
        probe = "isolation-probe"
        con = S.connect(probe, create=True)
        con.execute("INSERT INTO meta(key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                    ("probe", "secret-of-" + probe))
        con.commit()
        con.close()
        ts = S.tenants()
    leaks = []
    for t in ts:
        con = S.connect(t)
        try:
            for tb in TABLES:
                n = int(con.execute("SELECT COUNT(*) FROM " + tb + " WHERE tenant_id <> ?", (t,)).fetchone()[0])
                if n:
                    leaks.append({"as": t, "table": tb, "foreign_rows": n})
            # Writing another tenant's row must fail the policy check.
            other = next(x for x in ts if x != t)
            try:
                con.execute("INSERT INTO meta(tenant_id, key, value) VALUES (?, ?, ?)", (other, "x", "x"))
                con.commit()
                leaks.append({"as": t, "wrote_into": other})
            except Exception:                   # noqa: BLE001 — the policy refused it, as it must
                con.rollback()
        finally:
            con.close()
    if "isolation-probe" in ts:
        import psycopg
        with psycopg.connect(_admin_url(), autocommit=True) as admin:
            for tb in TABLES:
                admin.execute(f"DELETE FROM {tb} WHERE tenant_id = 'isolation-probe'")
            admin.execute("DELETE FROM tenants WHERE id = 'isolation-probe'")
    return {"ok": not leaks, "tenants": ts, "leaks": leaks}


def main(argv: list[str]) -> None:
    cmd = argv[0] if argv else "status"
    if cmd == "setup":
        res = setup()
    elif cmd == "migrate":
        res = migrate(argv[1:] or None)
    elif cmd == "status":
        res = status()
    elif cmd == "check-isolation":
        res = check_isolation()
    elif cmd == "export":
        res = {"out": str(export(argv[1], Path(argv[2])))}
    elif cmd == "use-sqlite":
        res = use_sqlite()
    else:
        raise SystemExit(__doc__)
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main(sys.argv[1:])
