"""Connecting a tenant's Notion workspace: the OAuth public integration.

The architecture's multi-tenant form of the Notion sync. Each company clicks
"Connect Notion" on the dashboard, picks the pages to share on Notion's own
consent screen, and the token Notion returns is stored ENCRYPTED for that
tenant (vault.py). Disconnecting deletes the token and stops the sync.

The integration is registered once, by the operator, at
notion.so/profile/integrations (OAuth), and its credentials go in
pipeline/.env locally, Secret Manager on GCP — never in code:

    NOTION_OAUTH_CLIENT_ID=...
    NOTION_OAUTH_CLIENT_SECRET=...
    NOTION_OAUTH_REDIRECT_URI=<dashboard>/api/connect/notion/callback

A CLIENT connects their own Notion through an invite: the owner makes a
link for one tenant (signed with BRAIN_INVITE_SECRET, valid 7 days, used
once), sends it, and the client picks their pages on Notion's own screen.
The owner's own "Connect Notion" is the same flow with an invite made on
the spot, so there is one callback and one way in.

An internal integration token (NOTION_TOKEN) still works as a single-tenant
fallback.

    python -m pipeline.brand_brain.notion_oauth authorize-url --tenant vanna --state S
    python -m pipeline.brand_brain.notion_oauth exchange --tenant vanna   # the code on stdin
    python -m pipeline.brand_brain.notion_oauth disconnect --tenant vanna
    python -m pipeline.brand_brain.notion_oauth status --tenant vanna
"""
from __future__ import annotations

import argparse
import base64
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from typing import Any, Optional

from pipeline.brand_brain import store as S
from pipeline.brand_brain import vault

AUTHORIZE = "https://api.notion.com/v1/oauth/authorize"
TOKEN = "https://api.notion.com/v1/oauth/token"
SECRET = "notion_token"
DEFAULT_REDIRECT = "http://localhost:3000/api/connect/notion/callback"
INVITE_DAYS = 7


def _cfg() -> dict[str, Optional[str]]:
    return {"client_id": S._env_file("NOTION_OAUTH_CLIENT_ID"),
            "client_secret": S._env_file("NOTION_OAUTH_CLIENT_SECRET"),
            "redirect_uri": S._env_file("NOTION_OAUTH_REDIRECT_URI") or DEFAULT_REDIRECT}


def configured() -> bool:
    c = _cfg()
    return bool(c["client_id"] and c["client_secret"])


def authorize_url(state: str) -> str:
    c = _cfg()
    if not configured():
        raise RuntimeError("NOTION_OAUTH_CLIENT_ID / NOTION_OAUTH_CLIENT_SECRET are not in pipeline/.env")
    return AUTHORIZE + "?" + urllib.parse.urlencode({
        "client_id": c["client_id"], "response_type": "code", "owner": "user",
        "redirect_uri": c["redirect_uri"], "state": state})


# --------------------------------------------------------------- invites

def _invite_key() -> bytes:
    k = S._env_file("BRAIN_INVITE_SECRET")
    if not k:
        # Generated once per machine, like the vault key. On GCP it is a secret.
        import secrets as _secrets
        k = _secrets.token_urlsafe(32)
        f = vault.ENV
        lines = f.read_text(encoding="utf-8").splitlines() if f.exists() else []
        f.write_text("\n".join([l for l in lines if not l.startswith("BRAIN_INVITE_SECRET=")]
                               + ["BRAIN_INVITE_SECRET=" + k]) + "\n", encoding="utf-8")
    return k.encode()


def _b64(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).decode().rstrip("=")


def _unb64(s: str) -> bytes:
    return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))


def make_invite(tenant: str, *, days: int = INVITE_DAYS, base: str = "") -> dict[str, Any]:
    """A signed, single-use link for one tenant to connect its Notion."""
    import hashlib
    import hmac
    import secrets as _secrets
    import time
    S.tenant_dir(tenant)
    body = {"t": tenant, "n": _secrets.token_urlsafe(9), "exp": int(time.time()) + days * 86400}
    payload = _b64(json.dumps(body, separators=(",", ":")).encode())
    sig = _b64(hmac.new(_invite_key(), payload.encode(), hashlib.sha256).digest())
    token = payload + "." + sig
    return {"ok": True, "tenant": tenant, "invite": token, "expires": body["exp"],
            "url": (base.rstrip("/") + "/connect/notion?invite=" + token) if base else None}


def check_invite(token: str) -> dict[str, Any]:
    """Who an invite is for, if it is genuine, unexpired and unused."""
    import hashlib
    import hmac
    import time
    from pipeline.brand_brain.client import Brain
    try:
        payload, sig = token.strip().split(".", 1)
        want = _b64(hmac.new(_invite_key(), payload.encode(), hashlib.sha256).digest())
        if not hmac.compare_digest(sig, want):
            return {"ok": False, "error": "this invite link is not valid"}
        body = json.loads(_unb64(payload))
    except Exception:                               # noqa: BLE001 — malformed
        return {"ok": False, "error": "this invite link is not valid"}
    if int(body.get("exp", 0)) < time.time():
        return {"ok": False, "error": "this invite link has expired — ask for a new one"}
    tenant = str(body.get("t") or "")
    try:
        S.tenant_dir(tenant)
        b = Brain(tenant, create=True)
        used = b.meta("notion_invite_used:" + str(body.get("n")))
        name = (b.get_brand_profile().get("company") or {}).get("name") or tenant
    except Exception:                               # noqa: BLE001
        return {"ok": False, "error": "this invite link is not valid"}
    if used:
        return {"ok": False, "error": "this invite link was already used"}
    return {"ok": True, "tenant": tenant, "nonce": body.get("n"), "company": name,
            "configured": configured()}


def exchange(tenant: str, code: str, http=None) -> dict[str, Any]:
    """Trade the authorization code for the workspace token and seal it."""
    from pipeline.brand_brain.client import Brain
    c = _cfg()
    if not configured():
        raise RuntimeError("the Notion OAuth integration is not configured")
    basic = base64.b64encode((c["client_id"] + ":" + c["client_secret"]).encode()).decode()
    body = {"grant_type": "authorization_code", "code": code, "redirect_uri": c["redirect_uri"]}
    if http is None:
        req = urllib.request.Request(TOKEN, data=json.dumps(body).encode(), method="POST",
                                     headers={"Authorization": "Basic " + basic,
                                              "Content-Type": "application/json",
                                              "Notion-Version": "2022-06-28"})
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                res = json.load(r)
        except urllib.error.HTTPError as e:
            raise RuntimeError("Notion refused the code: HTTP " + str(e.code) + " "
                               + e.read().decode("utf-8", "replace")[:200]) from e
    else:
        res = http(body)
    token = res.get("access_token")
    if not token:
        raise RuntimeError("Notion returned no access token")
    vault.put(tenant, SECRET, token)
    b = Brain(tenant)
    b.meta("notion_workspace", json.dumps({"name": res.get("workspace_name"), "id": res.get("workspace_id"),
                                           "bot_id": res.get("bot_id"),
                                           "connected_at": datetime.now(timezone.utc).isoformat()}))
    b.meta("notion_dirty", datetime.now(timezone.utc).isoformat())      # first sync at the next run
    return {"ok": True, "tenant": tenant, "workspace": res.get("workspace_name")}


def disconnect(tenant: str) -> dict[str, Any]:
    """Revoke on our side: the token is deleted and the sync stops.
    (Removing the integration inside Notion also revokes it there.)"""
    from pipeline.brand_brain.client import Brain
    vault.delete(tenant, SECRET)
    b = Brain(tenant)
    b.meta("notion_workspace", "")
    b.meta("notion_dirty", "")
    return {"ok": True, "tenant": tenant, "connected": False}


def token(tenant: str) -> Optional[str]:
    return vault.get(tenant, SECRET)


def status(tenant: str) -> dict[str, Any]:
    from pipeline.brand_brain.client import Brain
    try:
        ws = json.loads(Brain(tenant).meta("notion_workspace") or "{}")
    except Exception:                               # noqa: BLE001
        ws = {}
    return {"configured": configured(), "connected": bool(token(tenant)), "workspace": ws.get("name"),
            "connected_at": ws.get("connected_at"),
            "fallback_token": bool(S._env_file("NOTION_TOKEN"))}


def exchange_invite(invite: str, code: str, http=None) -> dict[str, Any]:
    """The callback's work: the invite must still be good; then the code is
    traded, the token sealed for the invite's tenant, and the invite spent."""
    from pipeline.brand_brain.client import Brain
    chk = check_invite(invite)
    if not chk.get("ok"):
        return chk
    out = exchange(chk["tenant"], code, http=http)
    Brain(chk["tenant"]).meta("notion_invite_used:" + str(chk["nonce"]), datetime.now(timezone.utc).isoformat())
    return {**out, "company": chk["company"]}


def main(argv: list[str]) -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["authorize-url", "exchange", "disconnect", "status",
                                    "invite", "check-invite", "exchange-invite"])
    ap.add_argument("--tenant", default=None)
    ap.add_argument("--state", default="")
    ap.add_argument("--base", default="")
    a = ap.parse_args(argv)
    if a.cmd in ("check-invite", "exchange-invite"):
        data = json.loads(sys.stdin.read() or "{}")     # the invite and the code travel on stdin
        out = (check_invite(str(data.get("invite", ""))) if a.cmd == "check-invite"
               else exchange_invite(str(data.get("invite", "")), str(data.get("code", ""))))
        print(json.dumps(out))
        return
    if not a.tenant:
        raise SystemExit("--tenant is required")
    S.tenant_dir(a.tenant)
    if a.cmd == "invite":
        out = make_invite(a.tenant, base=a.base)
    elif a.cmd == "authorize-url":
        out = {"url": authorize_url(a.state)}
    elif a.cmd == "exchange":
        code = sys.stdin.read().strip()           # never on the command line
        out = exchange(a.tenant, code)
    elif a.cmd == "disconnect":
        out = disconnect(a.tenant)
    else:
        out = status(a.tenant)
    print(json.dumps(out))


if __name__ == "__main__":
    main(sys.argv[1:])
