#!/usr/bin/env python3
import json
import os
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
KEYS_PATH = REPO / "pipeline" / "keys" / "agent-keys.json"
OP_KEYS_PATH = REPO / "pipeline" / "keys" / "operator-key.json"
BUZZ = "D:/buzz/target/debug/buzz.exe"
OUT_PATH = REPO / "pipeline" / "keys" / "agent-pubkeys.json"

def get_pubkey(private_key_hex: str) -> str:
    env = {**os.environ, "BUZZ_PRIVATE_KEY": private_key_hex, "BUZZ_RELAY_URL": "http://127.0.0.1:3000"}
    try:
        out = subprocess.run(
            [BUZZ, "users", "get"],
            capture_output=True, text=True, env=env, encoding="utf-8"
        )
        if out.returncode == 0:
            rows = json.loads(out.stdout or "[]")
            if rows and len(rows) > 0:
                return rows[0]["pubkey"]
    except Exception as e:
        print(f"Error fetching pubkey: {e}")
    return ""

def main():
    print("=== Generating Nostr Pubkeys for Agents ===")
    pubkeys_map = {}

    # 1. Process agent-keys.json
    if KEYS_PATH.exists():
        data = json.loads(KEYS_PATH.read_text(encoding="utf-8"))
        for name, entry in data.items():
            if entry and "private_key_hex" in entry:
                pk = entry["private_key_hex"]
                pub = get_pubkey(pk)
                if pub:
                    pubkeys_map[name] = pub
                    print(f"  - {name}: {pub}")

    # 2. Process operator-key.json
    if OP_KEYS_PATH.exists():
        data = json.loads(OP_KEYS_PATH.read_text(encoding="utf-8"))
        for name, entry in data.items():
            if entry and "private_key_hex" in entry:
                pk = entry["private_key_hex"]
                pub = get_pubkey(pk)
                if pub:
                    pubkeys_map[name] = pub
                    print(f"  - {name}: {pub}")

    # Save to file
    OUT_PATH.write_text(json.dumps(pubkeys_map, indent=2), encoding="utf-8")
    print(f"\n✅ Successfully generated agent-pubkeys.json at: {OUT_PATH}")

if __name__ == "__main__":
    main()
