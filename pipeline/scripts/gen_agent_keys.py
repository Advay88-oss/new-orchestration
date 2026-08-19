#!/usr/bin/env python3
"""Generate one Nostr keypair per pipeline agent.

A Nostr secret key is just 32 random bytes interpreted as a secp256k1 scalar, so
`secrets.token_bytes(32)` is a correct generator — we only need to reject the
vanishingly unlikely case of a value outside [1, n-1].

Writes keys/agent-keys.json. That file is secrets: it stays out of git.
"""

from __future__ import annotations

import json
import secrets
from pathlib import Path

# secp256k1 group order
N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141

AGENTS = [
    "conductor",
    "trend-scout",
    "strategist-capital-efficiency",
    "strategist-risk-relief",
    "strategist-agentic-credit",
    "editorial-judge",
    "visual-creator",
]


def gen_secret() -> str:
    while True:
        raw = secrets.token_bytes(32)
        val = int.from_bytes(raw, "big")
        if 1 <= val < N:
            return raw.hex()


def main() -> None:
    out_dir = Path(__file__).resolve().parents[1] / "keys"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "agent-keys.json"

    if out_path.exists():
        print(json.dumps({"ok": False, "reason": "already exists, refusing to overwrite",
                          "path": str(out_path)}))
        return

    keys = {name: {"private_key_hex": gen_secret()} for name in AGENTS}
    out_path.write_text(json.dumps(keys, indent=2), encoding="utf-8")

    # Keep secrets out of version control even if the repo root .gitignore misses it.
    (out_dir / ".gitignore").write_text("*\n", encoding="utf-8")

    print(json.dumps({"ok": True, "path": str(out_path), "agents": list(keys)}, indent=2))


if __name__ == "__main__":
    main()
