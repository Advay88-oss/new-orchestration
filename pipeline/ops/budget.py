"""Daily spend, caps and rate limits — shared by every process.

Every paid call (Gemini text, image, Veo, embeddings, Apify) passes the
guard in pipeline/ops/guard.py, which asks `check(service)` before the call
and `add(...)` after it. Spend is kept per UTC day and service in one table
(ops_spend) in the brain's database — Cloud SQL on GCP, so the dashboard,
the pipeline job and the scheduler all see the same totals — or in
pipeline/state/ops.db on a laptop without Postgres.

Caps come from config/budget.json. A service over its cap, or the day over
`daily_usd`, refuses new calls with BudgetExceeded until midnight UTC; the
owner is alerted at 80% and at 100%. `hit(key, per_minute, per_day)` is the
rate limiter (assistant turns, cycles).
"""
from __future__ import annotations

import json
import os
import sqlite3
import threading
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

REPO = Path(__file__).resolve().parents[2]
CONFIG = REPO / "config" / "budget.json"
LOCAL_DB = REPO / "pipeline" / "state" / "ops.db"
_lock = threading.Lock()
_cfg_cache: tuple[float, dict] = (0.0, {})

SQLITE_SCHEMA = """
CREATE TABLE IF NOT EXISTS ops_spend (
  day TEXT NOT NULL, service TEXT NOT NULL, calls INTEGER NOT NULL DEFAULT 0,
  input_tokens INTEGER NOT NULL DEFAULT 0, output_tokens INTEGER NOT NULL DEFAULT 0,
  usd REAL NOT NULL DEFAULT 0, updated_at TEXT NOT NULL, PRIMARY KEY (day, service));
CREATE TABLE IF NOT EXISTS ops_counters (
  key TEXT NOT NULL, win TEXT NOT NULL, count INTEGER NOT NULL DEFAULT 0, PRIMARY KEY (key, win));
CREATE TABLE IF NOT EXISTS ops_alerts (
  key TEXT PRIMARY KEY, severity TEXT, text TEXT, count INTEGER NOT NULL DEFAULT 0,
  first_at TEXT, last_at TEXT, last_sent TEXT);
CREATE TABLE IF NOT EXISTS ops_errors (
  fingerprint TEXT PRIMARY KEY, where_ TEXT, message TEXT, count INTEGER NOT NULL DEFAULT 0,
  first_seen TEXT, last_seen TEXT, alerted INTEGER NOT NULL DEFAULT 0);
"""

# Global (not per company): the owner's bill and the owner's alerts. The app
# role gets read/write on these; they hold no company content.
PG_SCHEMA = SQLITE_SCHEMA.replace("REAL", "DOUBLE PRECISION")


class BudgetExceeded(RuntimeError):
    pass


def config() -> dict[str, Any]:
    global _cfg_cache
    if time.time() - _cfg_cache[0] < 30:
        return _cfg_cache[1]
    try:
        cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        cfg = {"daily_usd": 15.0, "services": {}, "limits": {}, "rates": {}}
    if os.environ.get("BUDGET_DAILY_USD"):
        cfg["daily_usd"] = float(os.environ["BUDGET_DAILY_USD"])
    _cfg_cache = (time.time(), cfg)
    return cfg


def today() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# ------------------------------------------------------------------ storage

@contextmanager
def db():
    """A connection to the ops tables: Postgres when the brain is there
    (not bound to a tenant — these rows are the owner's, not a company's)."""
    from pipeline.brand_brain import store as S
    url = S.database_url() if S.backend() == "pg" else None
    if url:
        import psycopg
        con = psycopg.connect(url, connect_timeout=20, autocommit=True)
        try:
            yield _Pg(con)
        finally:
            con.close()
        return
    LOCAL_DB.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(str(LOCAL_DB), timeout=10)
    con.row_factory = sqlite3.Row
    con.executescript(SQLITE_SCHEMA)
    try:
        with con:
            yield con
    finally:
        con.close()


class _Pg:
    def __init__(self, con):
        self.con = con

    def execute(self, sql: str, params=()):
        cur = self.con.execute(sql.replace("?", "%s"), params)
        return _Cur(cur)


class _Cur:
    def __init__(self, cur):
        self.cur = cur

    def fetchone(self):
        r = self.cur.fetchone()
        return None if r is None else dict(zip([d.name for d in self.cur.description], r))

    def fetchall(self):
        cols = [d.name for d in self.cur.description or []]
        return [dict(zip(cols, r)) for r in self.cur.fetchall()]


# --------------------------------------------------------------------- spend

def spent(day: Optional[str] = None, *, strict: bool = False) -> dict[str, dict[str, float]]:
    """Today's spend by service. `strict`: raise BudgetExceeded when the
    ledger cannot be read, instead of reporting nothing spent — the check
    before a paid call uses it, so an unreadable ledger refuses the call."""
    try:
        with db() as con:
            rows = con.execute("SELECT * FROM ops_spend WHERE day=?", (day or today(),)).fetchall()
    except Exception as exc:                        # noqa: BLE001 — reported, never silently zero
        if strict:
            raise BudgetExceeded("the spend ledger cannot be read (" + type(exc).__name__ + ": "
                                 + str(exc)[:120] + "); paid calls are refused until it can") from exc
        return {}
    return {r["service"]: {"calls": r["calls"], "usd": float(r["usd"]), "input_tokens": r["input_tokens"],
                           "output_tokens": r["output_tokens"]} for r in rows}


def check(service: str) -> None:
    """Raise BudgetExceeded when this service, or the day, is over its cap."""
    cfg = config()
    s = spent(strict=True)
    total = sum(v["usd"] for v in s.values())
    cap = (cfg.get("services") or {}).get(service)
    if total >= float(cfg.get("daily_usd", 15)):
        raise BudgetExceeded("today's budget of $" + str(cfg.get("daily_usd")) + " is used up (resets 00:00 UTC)")
    if cap is not None and s.get(service, {}).get("usd", 0) >= float(cap):
        raise BudgetExceeded(service + " is over its daily cap of $" + str(cap) + " (resets 00:00 UTC)")


def add(service: str, usd: float, *, calls: int = 1, input_tokens: int = 0, output_tokens: int = 0) -> None:
    """Count a call. Never raises: accounting must not break the call it
    counts. A call that cannot be counted is said on stderr and alerted
    once a day, rather than vanishing."""
    try:
        with _lock, db() as con:
            con.execute(
                "INSERT INTO ops_spend(day, service, calls, input_tokens, output_tokens, usd, updated_at) "
                "VALUES (?,?,?,?,?,?,?) ON CONFLICT(day, service) DO UPDATE SET "
                "calls = ops_spend.calls + excluded.calls, input_tokens = ops_spend.input_tokens + excluded.input_tokens, "
                "output_tokens = ops_spend.output_tokens + excluded.output_tokens, usd = ops_spend.usd + excluded.usd, "
                "updated_at = excluded.updated_at",
                (today(), service, calls, int(input_tokens), int(output_tokens), float(usd), _now()))
        _threshold_alerts()
    except Exception as exc:                        # noqa: BLE001 — reported, not raised
        import sys
        print("[budget] could not count $%.4f of %s: %s" % (usd, service, exc), file=sys.stderr)
        try:
            from pipeline.ops import alerts
            alerts.send("budget-uncounted-" + today(), "Spend is not being counted: " + service
                        + " call of $%.4f could not be written (%s)." % (usd, str(exc)[:120]))
        except Exception:                           # noqa: BLE001 — the stderr line stands
            pass


def token_cost(input_tokens: int, output_tokens: int) -> float:
    r = (config().get("rates") or {}).get("gemini") or {}
    return input_tokens / 1e6 * float(r.get("input_per_1m", 0.3)) + output_tokens / 1e6 * float(r.get("output_per_1m", 2.5))


def _threshold_alerts() -> None:
    cfg = config()
    total = sum(v["usd"] for v in spent().values())
    cap = float(cfg.get("daily_usd", 15))
    at = float(cfg.get("alert_at", 0.8))
    from pipeline.ops import alerts
    if total >= cap:
        alerts.send("budget-100-" + today(), "Budget used up: $%.2f of $%.2f today. Paid calls are refused until "
                    "00:00 UTC." % (total, cap), severity="critical")
    elif total >= at * cap:
        alerts.send("budget-80-" + today(), "Budget at %d%%: $%.2f of $%.2f today." % (total / cap * 100, total, cap))


# --------------------------------------------------------------- rate limit

def hit(key: str, *, per_minute: Optional[int] = None, per_day: Optional[int] = None) -> None:
    """Count one use of `key`; raise BudgetExceeded over either limit."""
    minute = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M")
    with db() as con:
        for window, limit in ((minute, per_minute), (today(), per_day)):
            if limit is None:
                continue
            r = con.execute("SELECT count FROM ops_counters WHERE key=? AND win=?", (key, window)).fetchone()
            if r and int(r["count"]) >= int(limit):
                raise BudgetExceeded("too many " + key.replace("_", " ") + " requests: the limit is "
                                     + str(limit) + (" a minute" if window == minute else " a day"))
        for window, limit in ((minute, per_minute), (today(), per_day)):
            if limit is None:
                continue
            con.execute("INSERT INTO ops_counters(key, win, count) VALUES (?,?,1) ON CONFLICT(key, win) "
                        "DO UPDATE SET count = ops_counters.count + 1", (key, window))


def status() -> dict[str, Any]:
    cfg = config()
    s = spent()
    return {"day": today(), "daily_usd": cfg.get("daily_usd"), "spent_usd": round(sum(v["usd"] for v in s.values()), 4),
            "services": {k: {**s.get(k, {"calls": 0, "usd": 0.0}), "cap": cap}
                         for k, cap in {**(cfg.get("services") or {}), **{k: None for k in s if k not in (cfg.get("services") or {})}}.items()},
            "limits": cfg.get("limits")}
