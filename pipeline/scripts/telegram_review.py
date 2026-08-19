#!/usr/bin/env python3
"""Telegram human-review gate for the Vanna content pipeline.

Sends an approved-by-machine draft (copy + visual) to Advay for the final human
call, then waits for a reply. Nothing reaches a social platform without this step
returning an explicit approval.

Reads TELEGRAM_BOT_TOKEN the same way tgbot.py does — env var first, then the
known .env locations. The token is never printed.

Usage:
    python telegram_review.py send   --draft draft.json [--image card.png]
    python telegram_review.py poll   --draft-id <id> [--timeout 3600]
    python telegram_review.py status --draft-id <id>

Reply protocol (in Telegram, replying to the draft message):
    ok / approve / haan      -> approved
    no / reject / nahi       -> rejected
    anything else            -> treated as revision notes, status = changes_requested
"""

from __future__ import annotations

import argparse
import json
import mimetypes
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from pathlib import Path

REVIEWER_CHAT_ID = "5501720892"          # Advay
STATE = Path(__file__).resolve().parents[1] / "state"
API = "https://api.telegram.org/bot{token}/{method}"

ENV_FILES = [
    Path("C:/Users/Advay Anand/AppData/Local/hermes/.env"),
    Path.home() / ".agent-reach" / "tools" / "telegram-bot" / ".env",
    Path.home() / ".agent-reach" / ".env",
    Path("D:/new orchestration/Agent-Reach/.env"),
]

APPROVE = {"ok", "okay", "approve", "approved", "haan", "ha", "yes", "y", "ship", "go"}
REJECT = {"no", "nope", "reject", "rejected", "nahi", "na", "n", "kill", "drop"}


def load_token() -> str:
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    if token:
        return token
    for env_file in ENV_FILES:
        if env_file.exists():
            for line in env_file.read_text(encoding="utf-8").splitlines():
                if line.strip().startswith("TELEGRAM_BOT_TOKEN="):
                    value = line.split("=", 1)[1].strip().strip("\"'")
                    if value:
                        return value
    sys.exit("No bot token found. Set TELEGRAM_BOT_TOKEN or populate a .env file.")


def call(method: str, **params):
    url = API.format(token=load_token(), method=method)
    data = urllib.parse.urlencode(params).encode() if params else None
    try:
        with urllib.request.urlopen(url, data=data, timeout=45) as resp:
            payload = json.load(resp)
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", "replace")
        sys.exit(f"Telegram API error {exc.code}: {body[:300]}")
    if not payload.get("ok"):
        sys.exit(f"Telegram API error: {payload.get('description')}")
    return payload["result"]


def send_photo(chat_id: str, image: Path, caption: str) -> dict:
    """Multipart upload — urllib has no helper, so build the body by hand."""
    boundary = f"----vanna{uuid.uuid4().hex}"
    mime = mimetypes.guess_type(image.name)[0] or "image/png"
    parts: list[bytes] = []

    def field(name: str, value: str) -> None:
        parts.append(
            f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"\r\n\r\n'
            f"{value}\r\n".encode()
        )

    field("chat_id", chat_id)
    field("caption", caption[:1024])
    field("parse_mode", "HTML")
    parts.append(
        f'--{boundary}\r\nContent-Disposition: form-data; name="photo"; '
        f'filename="{image.name}"\r\nContent-Type: {mime}\r\n\r\n'.encode()
    )
    parts.append(image.read_bytes())
    parts.append(f"\r\n--{boundary}--\r\n".encode())
    body = b"".join(parts)

    req = urllib.request.Request(
        API.format(token=load_token(), method="sendPhoto"),
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
    )
    try:
        with urllib.request.urlopen(req, timeout=90) as resp:
            payload = json.load(resp)
    except urllib.error.HTTPError as exc:
        sys.exit(f"sendPhoto failed {exc.code}: {exc.read().decode('utf-8','replace')[:300]}")
    if not payload.get("ok"):
        sys.exit(f"sendPhoto failed: {payload.get('description')}")
    return payload["result"]


def send_animation(chat_id: str, animation: Path, caption: str) -> dict:
    """Multipart upload for Telegram sendAnimation — identical to send_photo but using animation field."""
    boundary = f"----vanna{uuid.uuid4().hex}"
    mime = mimetypes.guess_type(animation.name)[0] or "image/gif"
    parts: list[bytes] = []

    def field(name: str, value: str) -> None:
        parts.append(
            f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"\r\n\r\n'
            f"{value}\r\n".encode()
        )

    field("chat_id", chat_id)
    field("caption", caption[:1024])
    field("parse_mode", "HTML")
    parts.append(
        f'--{boundary}\r\nContent-Disposition: form-data; name="animation"; '
        f'filename="{animation.name}"\r\nContent-Type: {mime}\r\n\r\n'.encode()
    )
    parts.append(animation.read_bytes())
    parts.append(f"\r\n--{boundary}--\r\n".encode())
    body = b"".join(parts)

    req = urllib.request.Request(
        API.format(token=load_token(), method="sendAnimation"),
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
    )
    try:
        with urllib.request.urlopen(req, timeout=90) as resp:
            payload = json.load(resp)
    except urllib.error.HTTPError as exc:
        sys.exit(f"sendAnimation failed {exc.code}: {exc.read().decode('utf-8','replace')[:300]}")
    if not payload.get("ok"):
        sys.exit(f"sendAnimation failed: {payload.get('description')}")
    return payload["result"]


def esc(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def build_caption(draft: dict, draft_id: str) -> str:
    body = draft.get("final_body") or draft.get("body", "")
    thread = draft.get("final_thread") or draft.get("thread") or []
    lines = [
        f"<b>Draft {draft_id}</b>  ·  {esc(draft.get('platform', 'x'))}"
        f"  ·  arc: {esc(draft.get('arc', '?'))}",
        "",
        esc(body),
    ]
    if thread:
        lines += ["", "<b>Thread:</b>"]
        lines += [f"{i}. {esc(t)}" for i, t in enumerate(thread, start=2)]
    if draft.get("trend_id"):
        lines += ["", f"<i>trend: {esc(draft['trend_id'])}</i>"]
    lines += ["", "Reply <b>ok</b> to approve, <b>no</b> to reject, or send notes."]
    return "\n".join(lines)


def cmd_send(args: argparse.Namespace) -> int:
    draft = json.loads(args.draft.read_text(encoding="utf-8"))
    draft_id = draft.get("id") or uuid.uuid4().hex[:8]
    caption = build_caption(draft, draft_id)

    if args.animation and args.animation.exists():
        message = send_animation(REVIEWER_CHAT_ID, args.animation, caption)
    elif args.image and args.image.exists():
        message = send_photo(REVIEWER_CHAT_ID, args.image, caption)
    else:
        message = call("sendMessage", chat_id=REVIEWER_CHAT_ID, text=caption,
                       parse_mode="HTML")

    record = {
        "draft_id": draft_id,
        "message_id": message["message_id"],
        "chat_id": REVIEWER_CHAT_ID,
        "sent_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        # Telegram's own clock for the sent message. Any reply must postdate this,
        # otherwise a stale message from before the draft could resolve it.
        "sent_unix": message.get("date", int(time.time())),
        "status": "awaiting_review",
        "draft": draft,
        "image": str(args.image) if args.image else None,
    }
    STATE.joinpath("drafts").mkdir(parents=True, exist_ok=True)
    STATE.joinpath("drafts", f"{draft_id}.json").write_text(
        json.dumps(record, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(json.dumps({"ok": True, "draft_id": draft_id,
                      "message_id": message["message_id"]}))
    return 0


def classify(text: str) -> str:
    # tolerate slash-command form (/approve) and trailing punctuation
    token = text.strip().lower().lstrip("/").rstrip(".!?")
    if token in APPROVE:
        return "approved"
    if token in REJECT:
        return "rejected"
    return "changes_requested"


def cmd_poll(args: argparse.Namespace) -> int:
    path = STATE / "drafts" / f"{args.draft_id}.json"
    if not path.exists():
        sys.exit(f"Unknown draft id: {args.draft_id}")
    record = json.loads(path.read_text(encoding="utf-8"))
    target_msg = record["message_id"]
    sent_unix = record.get("sent_unix", 0)

    deadline = time.time() + args.timeout
    offset = 0
    while time.time() < deadline:
        updates = call("getUpdates", offset=offset, timeout=25)
        for upd in updates:
            offset = upd["update_id"] + 1
            msg = upd.get("message") or {}
            if str(msg.get("chat", {}).get("id")) != REVIEWER_CHAT_ID:
                continue
            text = msg.get("text", "")
            if not text:
                continue

            # A reply must postdate the draft. Without this a message sent before
            # the draft existed can silently resolve it — including approving
            # something the reviewer never saw.
            if msg.get("date", 0) <= sent_unix:
                continue

            reply_to = (msg.get("reply_to_message") or {}).get("message_id")
            if reply_to and reply_to != target_msg:
                continue

            verdict = classify(text)
            record["status"] = verdict
            record["reviewer_reply"] = text
            record["reviewed_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            path.write_text(json.dumps(record, indent=2, ensure_ascii=False),
                            encoding="utf-8")

            if verdict == "approved":
                dest = STATE / "approved" / f"{args.draft_id}.json"
            elif verdict == "rejected":
                dest = STATE / "rejected" / f"{args.draft_id}.json"
            else:
                dest = None
            if dest:
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_text(json.dumps(record, indent=2, ensure_ascii=False),
                                encoding="utf-8")

            print(json.dumps({"ok": True, "draft_id": args.draft_id,
                              "status": verdict, "reply": text}))
            return 0
        time.sleep(2)

    print(json.dumps({"ok": False, "draft_id": args.draft_id,
                      "status": "timeout", "waited_seconds": args.timeout}))
    return 1


def cmd_status(args: argparse.Namespace) -> int:
    path = STATE / "drafts" / f"{args.draft_id}.json"
    if not path.exists():
        sys.exit(f"Unknown draft id: {args.draft_id}")
    record = json.loads(path.read_text(encoding="utf-8"))
    print(json.dumps({k: record[k] for k in
                      ("draft_id", "status", "sent_at") if k in record}, indent=2))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Telegram review gate")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_send = sub.add_parser("send")
    p_send.add_argument("--draft", type=Path, required=True)
    p_send.add_argument("--image", type=Path)
    p_send.add_argument("--animation", type=Path)
    p_send.set_defaults(func=cmd_send)

    p_poll = sub.add_parser("poll")
    p_poll.add_argument("--draft-id", required=True)
    p_poll.add_argument("--timeout", type=int, default=3600)
    p_poll.set_defaults(func=cmd_poll)

    p_stat = sub.add_parser("status")
    p_stat.add_argument("--draft-id", required=True)
    p_stat.set_defaults(func=cmd_status)

    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
