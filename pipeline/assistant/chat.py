"""The assistant's turn: Gemini with function calling over the tools.

A turn is the conversation so far (the browser keeps it) plus the selected
company. The model answers, or asks for tools; tools run, their results go
back, up to MAX_ROUNDS. Events are yielded as they happen so the chat can
show "searching the brain…" and the cards the tools return.

    for ev in turn("vanna", [{"role": "user", "text": "..."}]): ...
    ev = {"type": "tool", "name", "args", "summary"} | {"type": "card", "card"}
       | {"type": "text", "text"} | {"type": "error", "error"} | {"type": "done"}
"""
from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from typing import Any, Iterator

from pipeline.assistant import tools as T

MAX_ROUNDS = 6        # the last round may not call tools: it must answer
AGENT = "ASSISTANT"


def _system(tenant: str) -> str:
    from pipeline.brand_brain.client import Brain
    try:
        p = Brain(tenant).get_brand_profile()
        name = (p.get("company") or {}).get("name") or tenant
        line = (p.get("company") or {}).get("what_it_is") or ""
    except Exception:                               # noqa: BLE001 — a company without a brain yet
        name, line = tenant, ""
    return (
        "You are the assistant inside Mission Control, a content operations dashboard. The owner is "
        "talking to you about one company at a time. SELECTED COMPANY: " + name + " (id " + tenant + "). "
        + (line + " " if line else "")
        + "\n\nRules:\n"
        "- Facts about the company come ONLY from tools (search_knowledge, brand_profile, whats_new, runs). "
        "Say which source a fact came from. If the brain has nothing, say so; never invent figures, dates, "
        "partners or claims.\n"
        "- Reply in the owner's language and register (they often write Hinglish; answer in Hinglish then). "
        "Be short and concrete; use bullet points for lists. Plain markdown only: no LaTeX, no wide tables, "
        "formulas written inline like HF = collateral / debt.\n"
        "- To add a new company, use add_company with the URL they give (ask for it if missing). To connect "
        "Notion, use notion_connect (for_client=true when they want a link to send someone).\n"
        "- You never launch a run, approve, revise, kill or approve a profile yourself: use propose_action, "
        "which shows the owner a button. Nothing is ever published by you or by the pipeline.\n"
        "- When a tool returns a card, the chat shows it; refer to it in a sentence rather than repeating it.\n"
        "- Use as few tool calls as you need: list_runs already says why each run was blocked; open a run "
        "with get_run only when the owner asks about that run.")


def _to_contents(messages: list[dict]) -> list[dict]:
    out = []
    for m in messages[-30:]:
        text = str(m.get("text") or "").strip()
        if not text:
            continue
        out.append({"role": "model" if m.get("role") == "assistant" else "user", "parts": [{"text": text[:8000]}]})
    return out


def _generate(payload: dict) -> dict:
    from pipeline.gtm_os import agent_runtime as R
    url, model, transport = R.endpoint("reasoning")
    req = urllib.request.Request(url, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"})
    t = time.time()
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            res = json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raise RuntimeError("model HTTP " + str(exc.code) + ": " + exc.read().decode("utf-8", "replace")[:300]) from exc
    usage = res.get("usageMetadata") or {}
    R.record(R.AgentCall(AGENT, "reasoning", model, True, round(time.time() - t, 2),
                         input_tokens=usage.get("promptTokenCount", 0),
                         output_tokens=usage.get("candidatesTokenCount", 0), transport=transport))
    return res


def _summary(name: str, result: dict) -> str:
    if "error" in result:
        return "failed: " + str(result["error"])[:120]
    if name == "search_knowledge":
        srcs = sorted({r.get("source") for r in result.get("results", []) if r.get("source")})
        return str(len(result.get("results", []))) + " passages from " + (", ".join(srcs) or "the brain")
    if name == "list_runs":
        return str(len(result.get("runs", []))) + " runs"
    if name == "get_run":
        return str(result.get("run_id")) + " · " + str(result.get("status"))
    if name == "add_company":
        return "analysing " + str(result.get("url"))
    return "done"


def turn(tenant: str, messages: list[dict]) -> Iterator[dict]:
    from pipeline.brand_brain import mcp_client as M
    M.enable()                                      # the assistant is an agent: brain reads go over MCP
    contents = _to_contents(messages)
    if not contents:
        yield {"type": "error", "error": "empty message"}
        return
    base = {"systemInstruction": {"parts": [{"text": _system(tenant)}]},
            "tools": [{"functionDeclarations": T.declarations()}],
            "generationConfig": {"temperature": 0.3, "maxOutputTokens": 2048}}
    for rnd in range(MAX_ROUNDS):
        req = {**base, "contents": contents}
        if rnd == MAX_ROUNDS - 1:
            req["toolConfig"] = {"functionCallingConfig": {"mode": "NONE"}}
        try:
            res = _generate(req)
        except Exception as exc:                    # noqa: BLE001 — shown in the chat
            yield {"type": "error", "error": str(exc)[:400]}
            return
        cand = (res.get("candidates") or [{}])[0]
        content = cand.get("content") or {"role": "model", "parts": []}
        parts = content.get("parts") or []
        calls = [p["functionCall"] for p in parts if "functionCall" in p]
        text = "".join(p.get("text", "") for p in parts if "text" in p and not p.get("thought"))
        if not calls:
            yield {"type": "text", "text": text.strip() or "(no answer)"}
            yield {"type": "done"}
            return
        # Keep the model's own turn exactly as returned (it may carry thought
        # signatures that must travel back with the function responses).
        contents.append({"role": "model", "parts": parts})
        responses = []
        for c in calls:
            name, args = c.get("name", ""), c.get("args") or {}
            result = T.call(name, tenant, args)
            yield {"type": "tool", "name": name, "args": args, "summary": _summary(name, result)}
            card = result.pop("card", None) if isinstance(result, dict) else None
            if card:
                yield {"type": "card", "card": card}
            responses.append({"functionResponse": {"name": name, "response": {"result": result}}})
        contents.append({"role": "user", "parts": responses})
    yield {"type": "text", "text": "I stopped after " + str(MAX_ROUNDS) + " tool rounds; ask me to continue."}
    yield {"type": "done"}
