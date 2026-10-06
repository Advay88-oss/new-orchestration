"""The Brain MCP server — the one door agents use to reach a company's brain.

Seven tools: the architecture's six, plus the GitHub commit log. The tenant is fixed for the
session (the `--tenant` flag or BRAIN_TENANT), never a tool argument, so no
call can ask for another company's data and no prompt needs a company name.

    python -m pipeline.brand_brain.mcp_server --tenant vanna                  # stdio
    python -m pipeline.brand_brain.mcp_server --tenant vanna --http 8765      # HTTP, this machine only
    BRAIN_MCP_TOKEN=... python -m pipeline.brand_brain.mcp_server --tenant vanna --http 8765 --host 0.0.0.0

Over HTTP the server listens on 127.0.0.1 unless told otherwise. On any
other address it refuses to start without BRAIN_MCP_TOKEN, and then every
request must carry `Authorization: Bearer <token>` — a brand's brain is
never open to whoever can reach the port.
"""
from __future__ import annotations

import argparse
import os
from typing import Any, Optional

from mcp.server.mcpserver import MCPServer

from pipeline.brand_brain.client import Brain, current_tenant


def build(tenant: str) -> MCPServer:
    brain = Brain(tenant)
    server = MCPServer(
        name="brand-brain",
        title="Brand Brain (" + tenant + ")",
        instructions=(
            "The brand brain for one company. Load get_brand_profile at the start of every "
            "task and follow it: colours, fonts, voice, do/don'ts, claims. Use search_knowledge "
            "for facts and cite the returned source; a claim with no source here is not a fact. "
            "Use get_whats_new at the start of a run, get_visual_refs before making a visual, "
            "and get_competitor_patterns to learn how others post — never to copy them."),
    )

    @server.tool(description="The company's whole brand profile (versioned JSON): identity, "
                             "voice rules, audiences, pillars, approved and prohibited claims, "
                             "partners, competitors, palette, fonts, logo, house style.")
    def get_brand_profile() -> dict[str, Any]:
        return brain.get_brand_profile()

    @server.tool(description="Dated events (feature launches, factual updates) after `since`, "
                             "an ISO timestamp — usually the last run's start. Newest first.")
    def get_whats_new(since: Optional[str] = None, limit: int = 20) -> list[dict]:
        return brain.get_whats_new(since, limit)

    @server.tool(description="Hybrid keyword + semantic search over the company's knowledge base. "
                             "Returns chunks with source, url, authority (1 founder-confirmed .. "
                             "4 archive) and the parent section. content_types can include doc, "
                             "faq, rule, section, summary, code.")
    def search_knowledge(query: str, k: int = 8, content_types: Optional[list[str]] = None,
                         sources: Optional[list[str]] = None, max_authority: int = 4) -> list[dict]:
        return brain.search_knowledge(query, k=k, content_types=content_types, sources=sources,
                                      max_authority=max_authority)

    @server.tool(description="The company's own images closest to a topic (approved posters, "
                             "video stills, design references, logo), with caption and style tags. "
                             "Founder-approved images rank first on a near tie.")
    def get_visual_refs(topic: str, n: int = 4, kinds: Optional[list[str]] = None) -> list[dict]:
        return brain.get_visual_refs(topic, n, kinds)

    @server.tool(description="How competitors post about a topic: summarised patterns (formats, "
                             "hooks, topics), never their text.")
    def get_competitor_patterns(topic: Optional[str] = None, n: int = 6) -> list[dict]:
        return brain.get_competitor_patterns(topic, n)

    @server.tool(description="The company's newest GitHub commits (every branch, last 30 days), "
                             "newest first: repo, short sha, author, date (UTC), message, branches, "
                             "url. Filter by repo name or an ISO `since`. A commit message is "
                             "engineering activity, not a shipped feature or a claim.")
    def get_recent_commits(repo: Optional[str] = None, since: Optional[str] = None,
                           limit: int = 20) -> dict[str, Any]:
        from pipeline.brand_brain.github_sync import recent_commits
        return recent_commits(tenant, repo=repo, since=since, limit=limit)

    @server.tool(description="Record a published post's metrics (impressions, likes, replies, "
                             "reposts, clicks, …) so the learning loop can use them.")
    def log_post_outcome(post_id: str, metrics: dict, run_id: Optional[str] = None) -> dict:
        return brain.log_post_outcome(post_id, metrics, run_id=run_id, source="mcp")

    @server.tool(description="The ledger of published-post metrics recorded for this company, "
                             "newest first. Each row is one log_post_outcome call.")
    def list_outcomes(limit: int = 40) -> list[dict]:
        return brain.outcomes(limit)

    @server.tool(description="Posters the founder killed or handed over as never-make. "
                             "These are not approved references; do not imitate them.")
    def list_rejected_posters() -> list[dict]:
        from pipeline.brand_brain.dashboard import rejected_posters
        return rejected_posters(tenant)

    return server


class _BearerAuth:
    """ASGI middleware: every HTTP request needs the shared bearer token."""

    def __init__(self, app, token: str):
        self.app, self.token = app, token.encode()

    async def __call__(self, scope, receive, send):
        import hmac
        if scope.get("type") == "http":
            auth = dict(scope.get("headers") or []).get(b"authorization", b"")
            if not hmac.compare_digest(auth, b"Bearer " + self.token):
                await send({"type": "http.response.start", "status": 401,
                            "headers": [(b"content-type", b"application/json"),
                                        (b"www-authenticate", b"Bearer")]})
                await send({"type": "http.response.body", "body": b'{"error":"unauthorized"}'})
                return
        await self.app(scope, receive, send)


def serve_http(server: MCPServer, port: int, host: str = "127.0.0.1",
               token: Optional[str] = None) -> None:
    import uvicorn
    local = host in ("127.0.0.1", "localhost", "::1")
    if not local and not token:
        raise SystemExit("refusing to serve the brain on " + host + " without BRAIN_MCP_TOKEN")
    app = server.streamable_http_app(host=host)
    if token:
        app = _BearerAuth(app, token)
    uvicorn.run(app, host=host, port=port, log_level="warning")


def main() -> None:
    ap = argparse.ArgumentParser(description="Brand Brain MCP server")
    ap.add_argument("--tenant", default=None)
    ap.add_argument("--http", type=int, default=None, help="serve streamable HTTP on this port")
    ap.add_argument("--host", default="127.0.0.1", help="HTTP bind address (default: this machine only)")
    a = ap.parse_args()
    tenant = a.tenant or current_tenant()
    os.environ["BRAIN_TENANT"] = tenant
    server = build(tenant)
    if a.http:
        serve_http(server, a.http, a.host, os.environ.get("BRAIN_MCP_TOKEN") or None)
    else:
        server.run("stdio")


if __name__ == "__main__":
    main()
