"""Alerts to the owner's Telegram, and the error register.

`send(key, text, severity)` tells the owner once per window (60 min for a
warning, 30 for critical) however often the same thing happens; every
occurrence is still counted in ops_alerts. `capture(where, exc)` records an
error by fingerprint (where + type + first line) in ops_errors and alerts on
the first sighting; repeats only add to the count, and the hourly watch
reports a digest.

Alerts go to the reviewer chat the review packets use
(TELEGRAM_BOT_TOKEN / TELEGRAM_REVIEWER_CHAT_ID). Without them the alert is
recorded and nothing is sent.
"""
from __future__ import annotations

import hashlib
import json
import traceback
import urllib.request
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

WINDOW = {"critical": timedelta(minutes=30), "warn": timedelta(minutes=60), "info": timedelta(hours=6)}
ICON = {"critical": "CRITICAL", "warn": "WARNING", "info": "NOTE"}


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _telegram(text: str) -> bool:
    try:
        from pipeline.gtm_os.telegram_sender import _chat_id, _token
        token, chat = _token(), _chat_id()
    except Exception:                               # noqa: BLE001 — not configured
        return False
    # The guard would count Telegram as nothing (it is free); plain urlopen is fine.
    req = urllib.request.Request("https://api.telegram.org/bot" + token + "/sendMessage",
                                 data=json.dumps({"chat_id": chat, "text": text[:3800],
                                                  "disable_web_page_preview": True}).encode(),
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return bool(json.load(r).get("ok"))
    except Exception:                               # noqa: BLE001
        return False


def send(key: str, text: str, *, severity: str = "warn") -> bool:
    """Alert once per window for this key. Returns whether a message went out."""
    from pipeline.ops.budget import db
    now = _now()
    try:
        with db() as con:
            r = con.execute("SELECT last_sent FROM ops_alerts WHERE key=?", (key,)).fetchone()
            last = datetime.fromisoformat(r["last_sent"]) if r and r["last_sent"] else None
            due = last is None or now - last >= WINDOW.get(severity, WINDOW["warn"])
            con.execute("INSERT INTO ops_alerts(key, severity, text, count, first_at, last_at, last_sent) "
                        "VALUES (?,?,?,1,?,?,?) ON CONFLICT(key) DO UPDATE SET count = ops_alerts.count + 1, "
                        "severity = excluded.severity, text = excluded.text, last_at = excluded.last_at"
                        + (", last_sent = excluded.last_sent" if due else ""),
                        (key, severity, text[:2000], now.isoformat(), now.isoformat(), now.isoformat() if due else None))
    except Exception:                               # noqa: BLE001 — without the table, alert anyway
        due = True
    if not due:
        return False
    return _telegram("Mission Control · " + ICON.get(severity, "WARNING") + "\n" + text)


def capture(where: str, exc: BaseException, *, context: Optional[dict] = None) -> str:
    """Record an error; alert the first time this kind of error is seen."""
    from pipeline.ops.budget import db
    first_line = (str(exc).splitlines() or [""])[0][:200]
    fp = hashlib.sha1((where + "|" + type(exc).__name__ + "|" + first_line[:80]).encode()).hexdigest()[:16]
    now = _now().isoformat()
    tb = "".join(traceback.format_exception_only(type(exc), exc)).strip()[:500]
    new = False
    try:
        with db() as con:
            r = con.execute("SELECT count FROM ops_errors WHERE fingerprint=?", (fp,)).fetchone()
            new = r is None
            con.execute("INSERT INTO ops_errors(fingerprint, where_, message, count, first_seen, last_seen, alerted) "
                        "VALUES (?,?,?,1,?,?,0) ON CONFLICT(fingerprint) DO UPDATE SET count = ops_errors.count + 1, "
                        "last_seen = excluded.last_seen, message = excluded.message",
                        (fp, where[:80], tb, now, now))
    except Exception:                               # noqa: BLE001
        new = True
    if new:
        send("error-" + fp, "New error in " + where + ":\n" + tb
             + ("\n" + json.dumps(context, default=str)[:400] if context else ""), severity="warn")
    return fp


def recent(limit: int = 20) -> dict[str, Any]:
    from pipeline.ops.budget import db
    try:
        with db() as con:
            a = con.execute("SELECT key, severity, text, count, last_at, last_sent FROM ops_alerts "
                            "ORDER BY last_at DESC LIMIT ?", (limit,)).fetchall()
            e = con.execute("SELECT fingerprint, where_, message, count, first_seen, last_seen FROM ops_errors "
                            "ORDER BY last_seen DESC LIMIT ?", (limit,)).fetchall()
    except Exception:                               # noqa: BLE001
        a, e = [], []
    return {"alerts": a, "errors": e}
