"""A12's other half — hearing the founder's answer.

`telegram_sender` posts each review packet with Approve / Revise / Kill
buttons whose callback data is `approve:<run_id>`. Nothing listened. The old
`telegram_approval_listener` expected a different format (`act:APPROVE:<id>`),
so no button ever matched it, and on approve it "published" a hardcoded
packet with a hardcoded image and reported PUBLISHED. It is not wired in.

This listener only RECORDS the decision (pipeline.gtm_learning.feedback) —
the reward the learning loop needs. It never publishes.

  * Approve / Kill: recorded at once.
  * Revise: recorded, then the founder's next text message in that chat is
    attached as the revision note ("what should change").
  * Only the configured reviewer chat (TELEGRAM_REVIEWER_CHAT_ID), or the
    founder's user id, is accepted.

    python -m pipeline.gtm_os.feedback_listener          # run until stopped
    python -m pipeline.gtm_os.feedback_listener --once   # one poll, then exit
"""
from __future__ import annotations

import argparse
import json
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from pipeline.gtm_os.telegram_sender import NotConfigured, _chat_id, _token

STATE = Path(__file__).resolve().parents[2] / "pipeline" / "state"
OFFSET_FILE = STATE / "telegram_offset.json"
PENDING_FILE = STATE / "telegram_pending_revise.json"
FOUNDER_USER_ID = 5501720892          # from the original listener
API = "https://api.telegram.org/bot{token}/{method}"
PENDING_TTL_S = 30 * 60


def _call(token: str, method: str, payload: dict, timeout: float = 40.0) -> dict:
    req = urllib.request.Request(
        API.format(token=token, method=method),
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def _load(path: Path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:                               # noqa: BLE001 — absent
        return default


def _save(path: Path, obj) -> None:
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(obj), encoding="utf-8")
    tmp.replace(path)


def _authorized(chat_id: Any, user_id: Any, reviewer_chat: Optional[str]) -> bool:
    if reviewer_chat and str(chat_id) == str(reviewer_chat):
        return True
    return str(user_id) == str(FOUNDER_USER_ID)


def _reply(token: str, chat_id: Any, text: str) -> None:
    try:
        _call(token, "sendMessage", {"chat_id": chat_id, "text": text}, timeout=20)
    except Exception:                               # noqa: BLE001 — best effort
        pass


def handle(update: dict, token: str, reviewer_chat: Optional[str]) -> Optional[dict]:
    """Process one update. Returns the recorded feedback row, if any."""
    from pipeline.gtm_learning.feedback import record

    cq = update.get("callback_query")
    if cq:
        data = str(cq.get("data") or "")
        chat_id = ((cq.get("message") or {}).get("chat") or {}).get("id")
        user_id = (cq.get("from") or {}).get("id")
        who = (cq.get("from") or {}).get("username") or str(user_id)
        if not _authorized(chat_id, user_id, reviewer_chat):
            _call(token, "answerCallbackQuery",
                  {"callback_query_id": cq["id"], "text": "Not authorised."}, timeout=20)
            return None
        verdict, _, run_id = data.partition(":")
        if verdict not in ("approve", "revise", "kill") or not run_id:
            _call(token, "answerCallbackQuery",
                  {"callback_query_id": cq["id"], "text": "Unknown button."}, timeout=20)
            return None
        try:
            row = record(run_id, verdict, source="telegram", by=who)
        except FileNotFoundError:
            _call(token, "answerCallbackQuery",
                  {"callback_query_id": cq["id"], "text": "Run not found locally."}, timeout=20)
            return None
        labels = {"approve": "Approved", "revise": "Revision noted", "kill": "Killed"}
        _call(token, "answerCallbackQuery",
              {"callback_query_id": cq["id"], "text": labels[verdict] + " — recorded."},
              timeout=20)
        if verdict == "revise":
            _save(PENDING_FILE, {"chat_id": chat_id, "run_id": run_id,
                                 "at": time.time()})
            _reply(token, chat_id, "What should change for " + run_id
                   + "? Reply with a note and it will be attached.")
        else:
            _reply(token, chat_id, labels[verdict] + ": " + run_id
                   + ". Recorded for learning; nothing was published.")
        return row

    msg = update.get("message")
    if msg and msg.get("text"):
        chat_id = (msg.get("chat") or {}).get("id")
        user_id = (msg.get("from") or {}).get("id")
        pending = _load(PENDING_FILE, None)
        if (pending and str(pending.get("chat_id")) == str(chat_id)
                and time.time() - float(pending.get("at", 0)) < PENDING_TTL_S
                and _authorized(chat_id, user_id, reviewer_chat)):
            who = (msg.get("from") or {}).get("username") or str(user_id)
            row = record(pending["run_id"], "revise", msg["text"],
                         source="telegram", by=who)
            PENDING_FILE.unlink(missing_ok=True)
            _reply(token, chat_id, "Note attached to " + pending["run_id"] + ".")
            return row
    return None


def poll_once(token: str, reviewer_chat: Optional[str], *, wait: int = 25) -> int:
    state = _load(OFFSET_FILE, {"offset": 0})
    res = _call(token, "getUpdates",
                {"offset": state.get("offset", 0), "timeout": wait,
                 "allowed_updates": ["callback_query", "message"]},
                timeout=wait + 15)
    if not res.get("ok"):
        raise RuntimeError("getUpdates failed: " + json.dumps(res)[:300])
    n = 0
    for up in res.get("result") or []:
        try:
            if handle(up, token, reviewer_chat):
                n += 1
        finally:
            # Advance past every update, handled or not, so one bad update
            # cannot wedge the queue.
            state["offset"] = int(up["update_id"]) + 1
            _save(OFFSET_FILE, state)
    return n


def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Record founder feedback from Telegram.")
    ap.add_argument("--once", action="store_true", help="poll once and exit")
    a = ap.parse_args(argv)
    try:
        token = _token()
    except NotConfigured as exc:
        print("feedback listener: " + str(exc))
        return 2
    try:
        reviewer = _chat_id()
    except NotConfigured:
        reviewer = None
        print("feedback listener: TELEGRAM_REVIEWER_CHAT_ID not set — accepting "
              "the founder's user id only.")
    print("feedback listener: polling (" + datetime.now(timezone.utc).isoformat() + ")")
    while True:
        try:
            got = poll_once(token, reviewer, wait=0 if a.once else 25)
            if got:
                print("recorded " + str(got) + " decision(s)")
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", "replace")[:300]
            print("telegram HTTP " + str(exc.code) + ": " + body)
            if exc.code == 409:
                print("Another program is already reading this bot's updates (a second "
                      "listener, or a webhook). Only one can run; this one exits.")
                return 3
            time.sleep(10)
        except Exception as exc:                    # noqa: BLE001 — keep polling
            print("poll error: " + type(exc).__name__ + ": " + str(exc)[:200])
            time.sleep(10)
        if a.once:
            return 0


if __name__ == "__main__":
    raise SystemExit(main())
