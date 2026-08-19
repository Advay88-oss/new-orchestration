#!/usr/bin/env python3
import json
import sys
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric import ec

REPO = Path(__file__).resolve().parents[2]
KEYS_PATH = REPO / "pipeline" / "keys" / "agent-keys.json"
OP_KEYS_PATH = REPO / "pipeline" / "keys" / "operator-key.json"
OUT_PATH = REPO / "pipeline" / "keys" / "agent-pubkeys.json"

def derive_nostr_pubkey(private_key_hex: str) -> str:
    try:
        priv_num = int(private_key_hex, 16)
        # Create private key on SECP256K1 curve
        private_key = ec.derive_private_key(priv_num, ec.SECP256K1())
        # Obtain public key numbers
        pn = private_key.public_key().public_numbers()
        # Nostr (BIP-340) pubkey is the 32-byte hex representation of the X-coordinate
        return f"{pn.x:064x}"
    except Exception as e:
        print(f"Error deriving key: {e}")
        return ""

def main():
    print("=== Cryptographically Deriving Nostr Pubkeys (Local & Offline) ===")
    pubkeys_map = {}

    # 1. Process agent-keys.json
    if KEYS_PATH.exists():
        data = json.loads(KEYS_PATH.read_text(encoding="utf-8"))
        for name, entry in data.items():
            if entry and "private_key_hex" in entry:
                pk = entry["private_key_hex"]
                pub = derive_nostr_pubkey(pk)
                if pub:
                    pubkeys_map[name] = pub
                    print(f"  - {name}: {pub}")

    # 2. Process operator-key.json
    if OP_KEYS_PATH.exists():
        data = json.loads(OP_KEYS_PATH.read_text(encoding="utf-8"))
        for name, entry in data.items():
            if entry and "private_key_hex" in entry:
                pk = entry["private_key_hex"]
                pub = derive_nostr_pubkey(pk)
                if pub:
                    pubkeys_map[name] = pub
                    print(f"  - {name}: {pub}")

    # Save to file
    OUT_PATH.write_text(json.dumps(pubkeys_map, indent=2), encoding="utf-8")
    print(f"\n✅ Success! Saved {len(pubkeys_map)} public keys to: {OUT_PATH}")

if __name__ == "__main__":
    main()
