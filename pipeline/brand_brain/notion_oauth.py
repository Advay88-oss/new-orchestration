"""Connecting a tenant's Notion workspace: the OAuth public integration.

The architecture's multi-tenant form of the Notion sync. Each company clicks
"Connect Notion" on the dashboard, picks the pages to share on Notion's own
consent screen, and the token Notion returns is stored ENCRYPTED for that
tenant (vault.py). Disconnecting deletes the token and stops the sync.

The integration is registered once, by the operator, at
notion.so/profile/integrations (type: Public), and its credentials go in
pipeline/.env — never in code or in the dashboard:

    NOTION_OAUTH_CLIENT_ID=...
    NOTION_OAUTH_CLIENT_SECRET=...
    NOTION_OAUTH_REDIRECT_URI=http://localhost:3000/api/gtm/brain/notion/callback

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
DEFAULT_REDIRECT = "http://localhost:3000/api/gtm/brain/notion/callback"


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


def main(argv: list[str]) -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["authorize-url", "exchange", "disconnect", "status"])
    ap.add_argument("--tenant", required=True)
    ap.add_argument("--state", default="")
    a = ap.parse_args(argv)
    S.tenant_dir(a.tenant)
    if a.cmd == "authorize-url":
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
