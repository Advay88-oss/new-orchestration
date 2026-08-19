#!/usr/bin/env python3
"""Slack human-review gate for the Vanna content pipeline.

Sends an approved-by-machine draft (copy + visual) to Slack for the final human
call using a Slack Bot Token (xoxb-) or Slack Webhook URL.

Usage:
    python slack_review.py send --draft draft.json [--image card.png]
"""

import argparse
import json
import mimetypes
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
import uuid
from pathlib import Path

STATE = Path(__file__).resolve().parents[1] / "state"

def load_slack_config() -> tuple[str, str, str]:
    """Reads Slack configurations from env or the local .env file."""
    token = os.environ.get("SLACK_BOT_TOKEN", "").strip()
    channel = os.environ.get("SLACK_CHANNEL_ID", "").strip()
    webhook = os.environ.get("SLACK_WEBHOOK_URL", "").strip()
    
    # Fallback to local Hermes .env
    env_file = Path("C:/Users/Advay Anand/AppData/Local/hermes/.env")
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("SLACK_BOT_TOKEN="):
                token = line.split("=", 1)[1].strip().strip("\"'")
            elif line.startswith("SLACK_CHANNEL_ID="):
                channel = line.split("=", 1)[1].strip().strip("\"'")
            elif line.startswith("SLACK_WEBHOOK_URL="):
                webhook = line.split("=", 1)[1].strip().strip("\"'")
                
    return token, channel, webhook

def upload_file_to_slack(token: str, channel: str, image: Path, caption: str) -> None:
    """Uploads local image file directly to Slack via files.upload API."""
    url = "https://slack.com/api/files.upload"
    boundary = f"----vanna-slack-{uuid.uuid4().hex}"
    mime = mimetypes.guess_type(image.name)[0] or "image/png"
    parts: list[bytes] = []

    def field(name: str, value: str) -> None:
        parts.append(
            f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"\r\n\r\n'
            f"{value}\r\n".encode()
        )

    field("channels", channel)
    field("initial_comment", caption)
    parts.append(
        f'--{boundary}\r\nContent-Disposition: form-data; name="file"; '
        f'filename="{image.name}"\r\nContent-Type: {mime}\r\n\r\n'.encode()
    )
    parts.append(image.read_bytes())
    parts.append(f"\r\n--{boundary}--\r\n".encode())
    body = b"".join(parts)

    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": f"multipart/form-data; boundary={boundary}"
        },
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=90) as resp:
            payload = json.loads(resp.read().decode())
            if not payload.get("ok"):
                print(f"Slack upload failed: {payload.get('error')}", file=sys.stderr)
    except urllib.error.HTTPError as exc:
        print(f"Slack API error {exc.code}: {exc.read().decode()}", file=sys.stderr)

def send_via_webhook(webhook_url: str, text: str) -> None:
    """Sends rich Block Kit message via incoming Webhook (does not support local files)."""
    payload = {
        "text": "Vanna Content Review",
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": text
                }
            }
        ]
    }
    req = urllib.request.Request(
        webhook_url,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            resp.read()
    except Exception as e:
        print(f"Webhook failed: {e}", file=sys.stderr)

def build_slack_text(draft: dict, draft_id: str) -> str:
    body = draft.get("final_body") or draft.get("body", "")
    lines = [
        f"🚨 *Vanna Content Review: Draft {draft_id}*  ·  Platform: *{draft.get('platform', 'x')}*",
        f"Arc: `{draft.get('arc', '?')}`",
        "",
        body,
        "",
        "Reply *ok* to approve, *no* to reject, or write changes required."
    ]
    return "\n".join(lines)

def main() -> int:
    ap = argparse.ArgumentParser(description="Slack content review gateway")
    ap.add_argument("cmd", choices=["send"])
    ap.add_argument("--draft", type=Path, required=True)
    ap.add_argument("--image", type=Path)
    args = ap.parse_args()

    draft = json.loads(args.draft.read_text(encoding="utf-8"))
    draft_id = draft.get("id") or uuid.uuid4().hex[:8]
    caption = build_slack_text(draft, draft_id)
    
    token, channel, webhook = load_slack_config()
    
    if token and channel and args.image and args.image.exists():
        print(f"Uploading image to Slack channel {channel} via Bot Token...")
        upload_file_to_slack(token, channel, args.image, caption)
        print(json.dumps({"ok": True, "method": "bot_upload", "channel": channel}))
    elif webhook:
        print("Sending copy to Slack Webhook...")
        send_via_webhook(webhook, caption)
        print(json.dumps({"ok": True, "method": "webhook"}))
    else:
        print("Error: No Slack configurations found. Please populate SLACK_BOT_TOKEN and SLACK_CHANNEL_ID, or SLACK_WEBHOOK_URL.", file=sys.stderr)
        return 1
        
    return 0

if __name__ == "__main__":
    sys.exit(main())
