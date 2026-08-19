#!/usr/bin/env python3
"""Slack reader script to search and retrieve messages from channels.

Uses the SLACK_BOT_TOKEN in .env to list all accessible channels and fetch their
latest conversation histories, proving that the bot is fully authorized and
can communicate both ways.
"""

import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

def load_token() -> str:
    token = os.environ.get("SLACK_BOT_TOKEN", "").strip()
    env_file = Path("C:/Users/Advay Anand/AppData/Local/hermes/.env")
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("SLACK_BOT_TOKEN="):
                token = line.split("=", 1)[1].strip().strip("\"'")
    return token

def call_slack_api(method: str, token: str, params: dict = None) -> dict:
    url = f"https://slack.com/api/{method}"
    if params:
        query = urllib.parse.urlencode(params)
        url = f"{url}?{query}"
        
    req = urllib.request.Request(
        url,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        method="GET"
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            headers = r.info()
            scopes = headers.get("X-OAuth-Scopes", "")
            accepted_scopes = headers.get("X-Accepted-OAuth-Scopes", "")
            if scopes:
                print(f"  [Scopes on Token]: {scopes}")
            payload = json.loads(r.read().decode())
            if not payload.get("ok"):
                print(f"Slack API error in {method}: {payload.get('error')}", file=sys.stderr)
            return payload
    except Exception as e:
        print(f"Error calling Slack API: {e}", file=sys.stderr)
        return {"ok": False}

def main() -> int:
    print("=== Search and Read Slack Channels ===")
    token = load_token()
    if not token:
        print("Error: No SLACK_BOT_TOKEN found in .env!", file=sys.stderr)
        return 1
        
    # 0. Run Auth Test
    print("Testing token authorization (auth.test)...")
    auth_resp = call_slack_api("auth.test", token)
    if auth_resp.get("ok"):
        print(f"  Authenticated Bot: @{auth_resp.get('user')} (ID: {auth_resp.get('user_id')})")
        print(f"  Slack Workspace: {auth_resp.get('team')} (ID: {auth_resp.get('team_id')})")
    else:
        print("❌ auth.test failed! Your SLACK_BOT_TOKEN is invalid.")
        return 1
        
    # 1. List accessible channels
    print("\nFetching accessible Slack channels...")
    channels_resp = call_slack_api("conversations.list", token, {"types": "public_channel,private_channel"})
    if not channels_resp.get("ok"):
        return 1
        
    channels = channels_resp.get("channels", [])
    if not channels:
        print("No channels found. Please ensure the bot is invited to at least one channel!")
        return 0
        
    print(f"Found {len(channels)} channel(s):")
    for ch in channels:
        print(f"  - Name: #{ch.get('name')} (ID: {ch.get('id')})")
        
    # 2. Fetch history for each channel
    for ch in channels:
        ch_id = ch.get("id")
        ch_name = ch.get("name")
        print(f"\n--- Reading latest messages in #{ch_name} (ID: {ch_id}) ---")
        
        history_resp = call_slack_api("conversations.history", token, {"channel": ch_id, "limit": 10})
        if not history_resp.get("ok"):
            print(f"Could not fetch history for #{ch_name}. Is the bot invited to this channel?")
            continue
            
        messages = history_resp.get("messages", [])
        if not messages:
            print("  (No messages found in this channel)")
            continue
            
        print(f"  Found {len(messages)} recent message(s):")
        for msg in reversed(messages):
            user = msg.get("user", "System/Bot")
            text = msg.get("text", "")
            ts = msg.get("ts")
            print(f"    [{ts}] User {user}: {text}")
            
    print("\n=== Search Finished ===")
    return 0

if __name__ == "__main__":
    sys.exit(main())
