"""Per-tenant secrets, encrypted before they reach the database.

The architecture keeps each tenant's Notion OAuth token encrypted, deletes it
on revoke, and stops that tenant's sync. Tokens are sealed with Fernet
(AES-128-CBC + HMAC-SHA256) under BRAIN_SECRET_KEY, which lives in
pipeline/.env and is generated there on first use; the database only ever
holds ciphertext, and a stolen database without the .env reads nothing.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from pipeline.brand_brain import store as S

ENV = Path(__file__).resolve().parents[1] / ".env"
KEY_NAME = "BRAIN_SECRET_KEY"


def _key(create: bool = False) -> Optional[bytes]:
    k = os.environ.get(KEY_NAME) or S._env_file(KEY_NAME)
    if k:
        return k.encode()
    if not create:
        return None
    from cryptography.fernet import Fernet
    k = Fernet.generate_key().decode()
    lines = ENV.read_text(encoding="utf-8").splitlines() if ENV.exists() else []
    lines = [l for l in lines if not l.strip().startswith(KEY_NAME + "=")] + [KEY_NAME + "=" + k]
    ENV.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return k.encode()


def put(tenant: str, name: str, value: str) -> None:
    from cryptography.fernet import Fernet
    from pipeline.brand_brain.client import Brain
    token = Fernet(_key(create=True)).encrypt(value.encode()).decode()
    Brain(tenant, create=True).set_secret(name, token)


def get(tenant: str, name: str) -> Optional[str]:
    from cryptography.fernet import Fernet, InvalidToken
    from pipeline.brand_brain.client import Brain
    key = _key()
    if not key:
        return None
    try:
        sealed = Brain(tenant).get_secret(name)
    except Exception:                               # noqa: BLE001 — no brain, no secret
        return None
    if not sealed:
        return None
    try:
        return Fernet(key).decrypt(sealed.encode()).decode()
    except InvalidToken:
        return None                                 # sealed under a key this machine does not have


def delete(tenant: str, name: str) -> None:
    from pipeline.brand_brain.client import Brain
    Brain(tenant).set_secret(name, None)
