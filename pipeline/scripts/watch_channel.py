#!/usr/bin/env python3
"""Print the #content-pipeline transcript with agent names instead of pubkeys.

`buzz messages get` returns raw Nostr events, so a human reading a run sees a
wall of 64-char hex. This maps each pubkey back to the agent that owns it.

Usage:
    python pipeline/scripts/watch_channel.py             # last 40, newest last
    python pipeline/scripts/watch_channel.py --limit 100
    python pipeline/scripts/watch_channel.py --full      # don't truncate bodies
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
BUZZ = Path("D:/buzz/target/debug/buzz.exe")
CHANNEL = "31098616-3d0b-4202-86b4-96bfd36680cd"
RELAY = os.environ.get("BUZZ_RELAY_URL", "http://127.0.0.1:3000")


def load_identities() -> dict[str, str]:
    """pubkey-prefix -> friendly name. Derived by asking the relay who each key is."""
    names: dict[str, str] = {}
    keyfiles = [
        REPO / "pipeline" / "keys" / "agent-keys.json",
        REPO / "pipeline" / "keys" / "operator-key.json",
    ]
    for kf in keyfiles:
        if not kf.exists():
            continue
        for name, entry in json.loads(kf.read_text(encoding="utf-8")).items():
            env = {**os.environ, "BUZZ_PRIVATE_KEY": entry["private_key_hex"],
                   "BUZZ_RELAY_URL": RELAY}
            out = subprocess.run([str(BUZZ), "users", "get"], capture_output=True,
                                 text=True, env=env, encoding="utf-8",
                                 errors="replace")
            try:
                rows = json.loads(out.stdout or "[]")
                if rows:
                    names[rows[0]["pubkey"]] = name
            except (json.JSONDecodeError, KeyError, IndexError):
                pass
    return names


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=40)
    ap.add_argument("--full", action="store_true")
    args = ap.parse_args()

    names = load_identities()
    # Read as the operator; any member can read the channel.
    opkey = json.loads((REPO / "pipeline" / "keys" / "operator-key.json")
                       .read_text(encoding="utf-8"))["operator"]["private_key_hex"]
    env = {**os.environ, "BUZZ_PRIVATE_KEY": opkey, "BUZZ_RELAY_URL": RELAY}

    out = subprocess.run(
        [str(BUZZ), "messages", "get", "--channel", CHANNEL, "--limit", str(args.limit)],
        capture_output=True, text=True, env=env,
        encoding="utf-8", errors="replace",
    )
    if out.returncode != 0:
        print(out.stderr.strip() or "failed to read channel")
        return 1

    msgs = json.loads(out.stdout or "[]")
    msgs.sort(key=lambda m: m.get("created_at", 0))

    for m in msgs:
        pk = m.get("pubkey", "")
        who = names.get(pk, pk[:8])
        ts = datetime.fromtimestamp(m.get("created_at", 0), tz=timezone.utc).strftime("%H:%M:%S")
        body = m.get("content", "")
        if not args.full and len(body) > 700:
            body = body[:700] + f"\n    … [{len(m['content']) - 700} more chars]"
        print(f"\n[{ts}] {who}\n{'-' * (len(who) + 12)}\n{body}")

    print(f"\n({len(msgs)} messages)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
