"""A12 — actually sending the review packet.

`TelegramPacketBuilder` builds a packet and renders it as markdown. Nothing
sent it. So the documented terminus of the whole system — a human deciding
whether this publishes — was not reachable from a run: the cycle assembled a
review packet and left it on disk.

This module is the missing half. It posts the packet and its assets to the
reviewer, and it is deliberately loud about the one state that used to be
silent:

  **Unconfigured is reported, not swallowed.** With no bot token the send does
  not quietly do nothing and let the stage pass. It records `skipped` with the
  reason, so a run that reached nobody says so rather than looking delivered.

Nothing here publishes to a channel. It sends to one reviewer for a decision;
approval is a separate, human action.
"""
from __future__ import annotations

import json
import mimetypes
import os
import urllib.error
import urllib.request
import uuid
from pathlib import Path
from typing import Any, Optional

from pipeline.gtm_os import agent_runtime as R

AGENT = "A12_telegram_gateway"
REPO_ROOT = Path(__file__).resolve().parents[2]
API = "https://api.telegram.org/bot{token}/{method}"

# Telegram's own limits. A caption over 1024 characters is rejected outright,
# and a message over 4096 is truncated server-side without warning.
CAPTION_MAX = 1024
MESSAGE_MAX = 4096


class NotConfigured(RuntimeError):
    """No credentials. Distinct from a send that was attempted and failed."""


def _token() -> str:
    tok = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    if tok:
        return tok
    for env in (REPO_ROOT / "pipeline" / ".env",
                REPO_ROOT / ".env",
                REPO_ROOT / "Agent-Reach" / ".env"):
        if not env.exists():
            continue
        for line in env.read_text(encoding="utf-8", errors="replace").splitlines():
            if line.strip().startswith("TELEGRAM_BOT_TOKEN="):
                v = line.split("=", 1)[1].strip().strip('"').strip("'")
                if v:
                    return v
    raise NotConfigured(
        "TELEGRAM_BOT_TOKEN is not set. Add it to pipeline/.env or the "
        "environment; until then review packets are written to disk and "
        "delivered to nobody.")


def _chat_id() -> str:
    cid = os.environ.get("TELEGRAM_REVIEWER_CHAT_ID", "").strip()
    if cid:
        return cid
    for env in (REPO_ROOT / "pipeline" / ".env", REPO_ROOT / ".env"):
        if not env.exists():
            continue
        for line in env.read_text(encoding="utf-8", errors="replace").splitlines():
            if line.strip().startswith("TELEGRAM_REVIEWER_CHAT_ID="):
                v = line.split("=", 1)[1].strip().strip('"').strip("'")
                if v:
                    return v
    raise NotConfigured("TELEGRAM_REVIEWER_CHAT_ID is not set.")


def _post_json(method: str, payload: dict, token: str, timeout: float = 30.0) -> dict:
    req = urllib.request.Request(
        API.format(token=token, method=method),
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def _post_file(method: str, field: str, path: Path, fields: dict,
               token: str, timeout: float = 180.0) -> dict:
    """multipart/form-data by hand — the repo has no requests dependency."""
    boundary = "----vanna" + uuid.uuid4().hex
    body = bytearray()

    def part(name: str, value: str) -> None:
        body.extend(("--" + boundary + "\r\n").encode())
        body.extend(('Content-Disposition: form-data; name="' + name + '"\r\n\r\n').encode())
        body.extend((value + "\r\n").encode("utf-8"))

    for k, v in fields.items():
        part(k, str(v))

    mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    body.extend(("--" + boundary + "\r\n").encode())
    body.extend(('Content-Disposition: form-data; name="' + field
                 + '"; filename="' + path.name + '"\r\n').encode())
    body.extend(("Content-Type: " + mime + "\r\n\r\n").encode())
    body.extend(path.read_bytes())
    body.extend(("\r\n--" + boundary + "--\r\n").encode())

    req = urllib.request.Request(
        API.format(token=token, method=method), data=bytes(body),
        headers={"Content-Type": "multipart/form-data; boundary=" + boundary})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def _decision_keyboard(run_id: str) -> dict:
    """Approve / revise / kill. The callbacks are what the listener handles."""
    return {"inline_keyboard": [[
        {"text": "✅ Approve", "callback_data": "approve:" + run_id},
        {"text": "✏️ Revise", "callback_data": "revise:" + run_id},
        {"text": "❌ Kill", "callback_data": "kill:" + run_id},
    ]]}


def send_review(summary: dict[str, Any], run_id: str, *,
                markdown: Optional[str] = None,
                dry_run: bool = False) -> dict[str, Any]:
    """Deliver the packet to the reviewer. Returns what actually happened."""
    try:
        token, chat = _token(), _chat_id()
    except NotConfigured as exc:
        R.record_stage(AGENT, "skipped", "not delivered: " + str(exc)[:300])
        return {"sent": False, "reason": "not_configured", "detail": str(exc)}

    posts = summary.get("posts") or {}
    x = posts.get("x") or {}
    review = summary.get("review_notes") or {}

    text = markdown or "\n".join(filter(None, [
        "*" + _esc(__import__('pipeline.brand_brain.context', fromlist=['company_name']).company_name()) + " — review needed*",
        "`" + run_id + "`",
        "",
        "*" + _esc(str(summary.get("pillar") or "")) + "*",
        _esc(str(summary.get("signal") or ""))[:300],
        "",
        "*Hook*",
        _esc(str(x.get("hook") or ""))[:400],
        "",
        "*Machine* " + _esc(str(summary.get("machine") or "—")),
        "*Creative* " + _esc(str(summary.get("creative_verdict") or "—")),
        "*Gate* " + ("passed" if summary.get("review_passed") else "BLOCKED"),
        ("*Blocking* " + _esc(json.dumps(review)[:300])
         if not summary.get("review_passed") else ""),
    ]))[:MESSAGE_MAX]

    if dry_run:
        R.record_stage(AGENT, "ok", "dry run: packet assembled, nothing sent")
        return {"sent": False, "reason": "dry_run", "chat": chat,
                "text_len": len(text),
                "assets": [k for k in ("visual_path", "meme_path", "video_path")
                           if summary.get(k)]}

    sent: list[str] = []
    errors: list[str] = []

    # Assets first, then the decision message last, so the buttons sit at the
    # bottom of the thread where a reviewer on a phone will actually find them.
    for key, method, field in (("visual_path", "sendPhoto", "photo"),
                               ("meme_path", "sendPhoto", "photo"),
                               ("video_path", "sendVideo", "video")):
        p = summary.get(key)
        if not p or not Path(str(p)).exists():
            continue
        try:
            res = _post_file(method, field, Path(str(p)),
                             {"chat_id": chat,
                              "caption": key.replace("_path", "")},
                             token)
            sent.append(key) if res.get("ok") else errors.append(
                key + ": " + json.dumps(res)[:160])
        except Exception as exc:                    # noqa: BLE001 — boundary
            errors.append(key + ": " + str(exc)[:160])

    try:
        res = _post_json("sendMessage", {
            "chat_id": chat, "text": text, "parse_mode": "Markdown",
            "reply_markup": _decision_keyboard(run_id),
        }, token)
        if res.get("ok"):
            sent.append("message")
        else:
            errors.append("message: " + json.dumps(res)[:200])
    except Exception as exc:                        # noqa: BLE001 — boundary
        errors.append("message: " + str(exc)[:200])

    ok = "message" in sent
    R.record_stage(AGENT, "ok" if ok and not errors else
                   ("degraded" if ok else "failed"),
                   ("delivered: " + ", ".join(sent) if sent else "nothing sent")
                   + (" | errors: " + "; ".join(errors) if errors else ""))
    return {"sent": ok, "delivered": sent, "errors": errors, "chat": chat}


_MD = "_*[]()~`>#+-=|{}.!"


def _esc(s: str) -> str:
    """Telegram Markdown is unforgiving; an unescaped underscore breaks the
    whole message and the API reports success for a mangled render."""
    out = []
    for ch in str(s):
        out.append("\\" + ch if ch in _MD else ch)
    return "".join(out)
