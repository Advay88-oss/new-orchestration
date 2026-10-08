"""The assistant's records, in the company's brain (row-level security keeps
each company's conversations to itself):

  chat_threads / chat_messages   conversations, on the server so they follow
                                 the owner to any device; long ones keep a
                                 rolling summary of their older messages
  audit_log                      every action the assistant started (an
                                 analysis, an invite link) and every button
                                 the owner pressed in the chat, with time,
                                 actor and the message that asked for it
"""
from __future__ import annotations

import json
import secrets
from datetime import datetime, timezone
from typing import Any, Optional

from pipeline.brand_brain.client import Brain

KEEP_RECENT = 16          # messages sent to the model verbatim
SUMMARIZE_AFTER = 24      # beyond this, the older ones are folded into the summary


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _b(tenant: str) -> Brain:
    return Brain(tenant, create=True)


# ------------------------------------------------------------------- threads

def new_thread(tenant: str, title: str = "") -> str:
    tid = "t_" + secrets.token_urlsafe(9)
    with _b(tenant)._db() as con:
        con.execute("INSERT INTO chat_threads(id, title, created_at, updated_at) VALUES (?,?,?,?)",
                    (tid, (title or "New chat")[:120], _now(), _now()))
    return tid


def _by(meta: Any) -> str:
    """Who started a thread, from its first message (older chats: the owner)."""
    try:
        return str((json.loads(meta) if isinstance(meta, str) else (meta or {})).get("by") or "owner")
    except (TypeError, ValueError):
        return "owner"


def threads(tenant: str, limit: int = 40, by: Optional[str] = None) -> list[dict]:
    """Newest first. `by`: only the chats that viewer started (a visitor or a
    client link); None for the owner, who sees every chat."""
    with _b(tenant)._db() as con:
        rows = con.execute(
            "SELECT t.id, t.title, t.created_at, t.updated_at, "
            "(SELECT m.text FROM chat_messages m WHERE m.thread_id = t.id "
            "AND m.role = 'assistant' ORDER BY m.id LIMIT 1) AS preview, "
            "(SELECT m.meta FROM chat_messages m WHERE m.thread_id = t.id "
            "AND m.role = 'user' ORDER BY m.id LIMIT 1) AS first_meta "
            "FROM chat_threads t ORDER BY t.updated_at DESC LIMIT ?",
            (limit * (4 if by else 1),)).fetchall()
    out = []
    for r in rows:
        d = dict(r)
        owner = _by(d.pop("first_meta", None))
        if by and owner != by:
            continue
        d["preview"] = " ".join(str(d.get("preview") or "").split())[:160]
        out.append(d)
    return out[:limit]


def thread_owner(tenant: str, thread_id: str) -> str:
    with _b(tenant)._db() as con:
        r = con.execute("SELECT meta FROM chat_messages WHERE thread_id=? AND role='user' ORDER BY id LIMIT 1",
                        (thread_id,)).fetchone()
    return _by(r["meta"] if r else None)


def thread(tenant: str, thread_id: str) -> Optional[dict]:
    with _b(tenant)._db() as con:
        t = con.execute("SELECT * FROM chat_threads WHERE id=?", (thread_id,)).fetchone()
        if not t:
            return None
        msgs = con.execute("SELECT id, role, text, meta, at FROM chat_messages WHERE thread_id=? ORDER BY id",
                           (thread_id,)).fetchall()
    out = dict(t)
    out["messages"] = [{"id": m["id"], "role": m["role"], "text": m["text"], "at": m["at"],
                        **(json.loads(m["meta"]) if m["meta"] else {})} for m in msgs]
    return out


def delete_thread(tenant: str, thread_id: str) -> bool:
    with _b(tenant)._db() as con:
        con.execute("DELETE FROM chat_messages WHERE thread_id=?", (thread_id,))
        con.execute("DELETE FROM chat_threads WHERE id=?", (thread_id,))
    return True


def add_message(tenant: str, thread_id: str, role: str, text: str, meta: Optional[dict] = None) -> None:
    with _b(tenant)._db() as con:
        con.execute("INSERT INTO chat_messages(thread_id, role, text, meta, at) VALUES (?,?,?,?,?)",
                    (thread_id, role, text, json.dumps(meta, ensure_ascii=False, default=str) if meta else None, _now()))
        if role == "user":
            first = con.execute("SELECT COUNT(*) FROM chat_messages WHERE thread_id=? AND role='user'",
                                (thread_id,)).fetchone()[0]
            if first == 1:                          # the first question names the thread
                con.execute("UPDATE chat_threads SET title=? WHERE id=?", (text.strip()[:80], thread_id))
        con.execute("UPDATE chat_threads SET updated_at=? WHERE id=?", (_now(), thread_id))


def history(tenant: str, thread_id: str) -> tuple[str, list[dict]]:
    """(summary of the older messages, the recent ones) — what the model sees."""
    t = thread(tenant, thread_id) or {"messages": [], "summary": ""}
    msgs = [{"role": m["role"], "text": m["text"]} for m in t["messages"]]
    return str(t.get("summary") or ""), msgs[int(t.get("summarized") or 0):]


def fold(tenant: str, thread_id: str, summarize) -> bool:
    """Keep long threads short for the model: when more than SUMMARIZE_AFTER
    messages are unsummarised, fold all but the last KEEP_RECENT into the
    thread's summary (`summarize(old_summary, messages) -> str`)."""
    t = thread(tenant, thread_id)
    if not t:
        return False
    done = int(t.get("summarized") or 0)
    msgs = t["messages"]
    if len(msgs) - done <= SUMMARIZE_AFTER:
        return False
    cut = len(msgs) - KEEP_RECENT
    new = summarize(str(t.get("summary") or ""), [{"role": m["role"], "text": m["text"]} for m in msgs[done:cut]])
    with _b(tenant)._db() as con:
        con.execute("UPDATE chat_threads SET summary=?, summarized=? WHERE id=?", (new[:6000], cut, thread_id))
    return True


# --------------------------------------------------------------------- audit

def audit(tenant: str, actor: str, action: str, detail: Optional[dict] = None, thread_id: str = "") -> None:
    with _b(tenant)._db() as con:
        con.execute("INSERT INTO audit_log(at, actor, action, detail, thread_id) VALUES (?,?,?,?,?)",
                    (_now(), actor, action, json.dumps(detail or {}, ensure_ascii=False, default=str)[:4000],
                     thread_id or None))


def audit_log(tenant: str, limit: int = 50) -> list[dict[str, Any]]:
    with _b(tenant)._db() as con:
        rows = con.execute("SELECT * FROM audit_log ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    return [{**{k: r[k] for k in r.keys() if k != "detail"}, "detail": json.loads(r["detail"] or "{}")} for r in rows]
