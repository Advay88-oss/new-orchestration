"""Agents reach the brand brain through the Brain MCP server — the one door.

The architecture: agents never read files, Notion or the database; they call
the Brain MCP server, and the tenant is fixed for the session. This is the
client half. One MCP session per process and tenant, opened on first use and
kept open (a run makes dozens of lookups; spawning a server per call would
cost a second each).

    transport   BRAIN_MCP_URL set  -> streamable HTTP to that server
                                      (Authorization: Bearer BRAIN_MCP_TOKEN)
                otherwise          -> stdio: the server as a child process

The MCP SDK is async; the pipeline is not. The session lives on a private
event loop in a daemon thread, and each call is a blocking round trip to it.

If the server cannot be started, reads fall back to the in-process client so
a run still completes; `transport()` says which one is serving, and the run
records it.
"""
from __future__ import annotations

import asyncio
import atexit
import json
import os
import sys
import threading
from pathlib import Path
from typing import Any, Optional

REPO = Path(__file__).resolve().parents[2]
TOOLS = ("get_brand_profile", "get_whats_new", "search_knowledge", "get_visual_refs",
         "get_competitor_patterns", "log_post_outcome")
CALL_TIMEOUT_S = 90.0
CONNECT_TIMEOUT_S = 45.0


class MCPUnavailable(RuntimeError):
    pass


def _result(res: Any) -> Any:
    """A tool result as the Python value the server returned."""
    # mcp 2.x names these in snake_case; 1.x in camelCase.
    if getattr(res, "is_error", None) or getattr(res, "isError", None):
        text = " ".join(getattr(c, "text", "") for c in (res.content or []))
        raise RuntimeError("brain tool error: " + text[:300])
    sc = getattr(res, "structured_content", None)
    if sc is None:
        sc = getattr(res, "structuredContent", None)
    if isinstance(sc, dict):
        # FastMCP-style servers wrap non-object returns as {"result": ...}.
        return sc["result"] if set(sc) == {"result"} else sc
    for c in res.content or []:
        text = getattr(c, "text", None)
        if text is not None:
            try:
                return json.loads(text)
            except ValueError:
                return text
    return None


class BrainMCP:
    """A blocking handle on one tenant's Brain MCP session."""

    def __init__(self, tenant: str):
        self.tenant = tenant
        self._loop = asyncio.new_event_loop()
        self._ready = threading.Event()
        self._error: Optional[BaseException] = None
        self._session = None
        self._stop: Optional[asyncio.Event] = None
        self.transport = "http" if os.environ.get("BRAIN_MCP_URL") else "stdio"
        self._thread = threading.Thread(target=self._run, name="brain-mcp-" + tenant, daemon=True)
        self._thread.start()
        if not self._ready.wait(CONNECT_TIMEOUT_S):
            raise MCPUnavailable("brain MCP server did not answer in " + str(CONNECT_TIMEOUT_S) + "s")
        if self._error:
            raise MCPUnavailable(str(self._error)[:300])

    # --------------------------------------------------------------- session

    def _run(self) -> None:
        asyncio.set_event_loop(self._loop)
        try:
            self._loop.run_until_complete(self._serve())
        except BaseException as exc:                     # noqa: BLE001 — surfaced to the caller
            self._error = exc
            self._ready.set()

    async def _serve(self) -> None:
        from mcp import ClientSession
        self._stop = asyncio.Event()
        if self.transport == "http":
            import httpx
            from mcp.client.streamable_http import streamable_http_client
            token = os.environ.get("BRAIN_MCP_TOKEN")
            headers = {"Authorization": "Bearer " + token} if token else {}
            async with httpx.AsyncClient(headers=headers, timeout=CALL_TIMEOUT_S) as http:
                async with streamable_http_client(os.environ["BRAIN_MCP_URL"], http_client=http) as streams:
                    await self._session_on(ClientSession, streams[0], streams[1])
        else:
            from mcp import StdioServerParameters
            from mcp.client.stdio import stdio_client
            env = {**os.environ, "BRAIN_TENANT": self.tenant, "PYTHONIOENCODING": "utf-8"}
            params = StdioServerParameters(
                command=sys.executable,
                args=["-m", "pipeline.brand_brain.mcp_server", "--tenant", self.tenant],
                env=env, cwd=str(REPO))
            with open(os.devnull, "w") as errlog:
                async with stdio_client(params, errlog=errlog) as (read, write):
                    await self._session_on(ClientSession, read, write)

    async def _session_on(self, ClientSession, read, write) -> None:
        async with ClientSession(read, write) as session:
            await session.initialize()
            self._session = session
            self._ready.set()
            await self._stop.wait()

    def close(self) -> None:
        if self._stop is not None and self._loop.is_running():
            self._loop.call_soon_threadsafe(self._stop.set)
            self._thread.join(timeout=5)

    # ----------------------------------------------------------------- calls

    def call(self, tool: str, **args: Any) -> Any:
        if tool not in TOOLS:
            raise ValueError("not a brain tool: " + tool)
        if self._session is None or not self._thread.is_alive():
            raise MCPUnavailable("brain MCP session is closed")
        args = {k: v for k, v in args.items() if v is not None}
        fut = asyncio.run_coroutine_threadsafe(self._session.call_tool(tool, args), self._loop)
        return _result(fut.result(CALL_TIMEOUT_S))


_sessions: dict[str, BrainMCP] = {}
_failed: dict[str, str] = {}
_lock = threading.Lock()


def session(tenant: str) -> Optional[BrainMCP]:
    """The process's session for a tenant, or None when the server is down."""
    if os.environ.get("BRAIN_MCP_DISABLE") == "1":
        return None
    with _lock:
        s = _sessions.get(tenant)
        if s is not None and s._thread.is_alive():
            return s
        if tenant in _failed:
            return None
        try:
            s = BrainMCP(tenant)
        except Exception as exc:                        # noqa: BLE001 — fall back, recorded
            _failed[tenant] = str(exc)[:300]
            return None
        _sessions[tenant] = s
        return s


def transport(tenant: str) -> dict[str, Any]:
    s = _sessions.get(tenant)
    if s is not None and s._thread.is_alive():
        return {"transport": "mcp-" + s.transport}
    if tenant in _failed:
        return {"transport": "direct", "mcp_error": _failed[tenant]}
    return {"transport": "not-connected"}


@atexit.register
def _close_all() -> None:
    for s in list(_sessions.values()):
        try:
            s.close()
        except Exception:                               # noqa: BLE001 — exiting anyway
            pass


class AgentBrain:
    """What agents hold: the six tools over MCP, and nothing else.

    Writes and bookkeeping (ingest, meta, rewards) are pipelines, not agents,
    and use `client.Brain` directly.
    """

    def __init__(self, tenant: str):
        self.tenant = tenant

    def _call(self, tool: str, direct, **args: Any) -> Any:
        s = session(self.tenant)
        if s is not None:
            try:
                return s.call(tool, **args)
            except MCPUnavailable:
                pass
        from pipeline.brand_brain.client import Brain
        return direct(Brain(self.tenant))

    def get_brand_profile(self) -> dict[str, Any]:
        return self._call("get_brand_profile", lambda b: b.get_brand_profile()) or {}

    def get_whats_new(self, since: Optional[str] = None, limit: int = 20) -> list[dict]:
        return self._call("get_whats_new", lambda b: b.get_whats_new(since, limit),
                          since=since, limit=limit) or []

    def search_knowledge(self, query: str, *, k: int = 8, content_types=None, sources=None,
                         max_authority: int = 4) -> list[dict]:
        ct = list(content_types) if content_types else None
        src = list(sources) if sources else None
        return self._call("search_knowledge",
                          lambda b: b.search_knowledge(query, k=k, content_types=ct, sources=src,
                                                       max_authority=max_authority),
                          query=query, k=k, content_types=ct, sources=src,
                          max_authority=max_authority) or []

    def get_visual_refs(self, topic: str, n: int = 4, kinds=None) -> list[dict]:
        kd = list(kinds) if kinds else None
        return self._call("get_visual_refs", lambda b: b.get_visual_refs(topic, n, kd),
                          topic=topic, n=n, kinds=kd) or []

    def get_competitor_patterns(self, topic: Optional[str] = None, n: int = 6) -> list[dict]:
        return self._call("get_competitor_patterns", lambda b: b.get_competitor_patterns(topic, n),
                          topic=topic, n=n) or []

    def log_post_outcome(self, post_id: str, metrics: dict, *, run_id: Optional[str] = None,
                         source: str = "mcp") -> dict:
        return self._call("log_post_outcome",
                          lambda b: b.log_post_outcome(post_id, metrics, run_id=run_id, source=source),
                          post_id=post_id, metrics=metrics, run_id=run_id) or {}
