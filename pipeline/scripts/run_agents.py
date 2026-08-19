#!/usr/bin/env python3
"""Launch one buzz-acp harness per pipeline agent.

Each agent is a separate OS process holding its own Nostr key, so the relay sees
seven distinct identities rather than one process wearing seven hats. That
separation is the point: it is what lets the strategists argue with each other
instead of being summarised by a coordinator.

Two runtimes are supported:

  gemini  (default) — Gemini CLI in ACP mode, talking to Vertex *through*
          vertex_spend_proxy.py so every call is metered against a hard dollar
          cap. GCP budgets are alerts, not caps; the proxy is the actual stop.
  claude            — Claude Code via @agentclientprotocol/claude-agent-acp,
          billed against the Claude subscription. No dollar metering available.

Usage:
    python pipeline/scripts/run_agents.py
    python pipeline/scripts/run_agents.py --runtime claude
    python pipeline/scripts/run_agents.py --only conductor trend-scout
    python pipeline/scripts/run_agents.py --dry-run
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
PACK = REPO / "pipeline" / "buzz-pack"
KEYS = REPO / "pipeline" / "keys" / "agent-keys.json"
PROMPTS = REPO / "pipeline" / "state" / "prompts"
LOGS = REPO / "pipeline" / "logs" / "agents"

BUZZ_ACP = Path("D:/buzz/target/debug/buzz-acp.exe")
DEV_MCP = Path("D:/buzz/target/debug/buzz-dev-mcp.exe")
NPM_BIN = Path(r"C:\Users\Advay Anand\AppData\Roaming\npm")
NODE_BIN = os.environ.get("VANNA_NODE_BIN", r"C:\nvm4w\nodejs\node.exe")

RELAY_URL = os.environ.get("BUZZ_RELAY_URL", "ws://127.0.0.1:3000")

# Vertex, via the capped proxy. gemini-2.5-flash is what this project actually
# serves — gemini-3.x and gemini-flash-latest all 404 here, checked 8 Aug 2026.
VERTEX_PROJECT = os.environ.get("VERTEX_PROJECT", "sales-agent-504607")
VERTEX_LOCATION = os.environ.get("VERTEX_LOCATION", "us-central1")
PROXY_URL = os.environ.get("VERTEX_PROXY_URL", "http://127.0.0.1:8900")
GEMINI_MODEL = os.environ.get("VANNA_GEMINI_MODEL", "gemini-2.5-flash")
CLAUDE_MODEL = os.environ.get("VANNA_CLAUDE_MODEL", "claude-opus-5")

# Cost optimization via per-agent model tiering. Seven Opus agents burned a
# subscription session limit in ~28 min. Only the editorial-judge — the final
# quality gate — truly needs top-tier reasoning; the scout and visual-creator are
# near-mechanical; the conductor and strategists do well on Sonnet. This keeps
# the quality where it decides the output (the judge) and cuts the rest.
# Override with VANNA_MODEL_TIER='{"conductor":"claude-opus-5",...}'.
MODEL_TIER = {
    "conductor": "claude-sonnet-5",
    "trend-scout": "claude-haiku-4-5",
    "strategist-capital-efficiency": "claude-sonnet-5",
    "strategist-risk-relief": "claude-sonnet-5",
    "strategist-agentic-credit": "claude-sonnet-5",
    "editorial-judge": "claude-opus-5",
    "visual-creator": "claude-haiku-4-5",
}
try:
    MODEL_TIER.update(json.loads(os.environ.get("VANNA_MODEL_TIER", "{}")))
except Exception:
    pass

# Context management. The last run burned a session limit in ~28 minutes, and
# thread context was a large part of it: every reply re-sent the surrounding
# messages. The conductor mediates threads so it keeps a small window; workers
# only need the dispatch that summoned them, so they run near-context-free.
CONDUCTOR_CONTEXT = os.environ.get("VANNA_CONDUCTOR_CONTEXT", "3")
WORKER_CONTEXT = os.environ.get("VANNA_WORKER_CONTEXT", "2")
MAX_TURNS_PER_SESSION = os.environ.get("VANNA_MAX_TURNS", "20")

# A stuck ACP turn used to burn for the full 900s max. Killing it at 4 min keeps
# a single hang from quietly eating a session's worth of tokens.
IDLE_TIMEOUT = os.environ.get("VANNA_IDLE_TIMEOUT", "240")

# The conductor has to see every message to decide whether a run is warranted.
# Everyone else wakes on being addressed, which is what keeps spend sane.
SUBSCRIBE = {"conductor": "all"}
DEFAULT_SUBSCRIBE = "mentions"

# Star topology, not a mesh. Seven agents each set to respond to "anyone" is an
# N^2 cascade: every draft a strategist posts wakes the other six, each of whom
# spends a full Claude turn deciding whether to answer — that is where the tokens
# actually go (a worker posted a whole refusal to a kickoff that never addressed
# it). Workers instead allowlist ONLY the conductor (their dispatcher) and the
# operator (so a human can still DM an agent from the GUI). They ignore each
# other entirely; the conductor collects drafts and summons the judge/visual.
# The conductor alone stays open ("anyone") because it orchestrates.
def _load_pubkeys() -> dict:
    p = REPO / "pipeline" / "keys" / "agent-pubkeys.json"
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}

PUBKEYS = _load_pubkeys()
WORKER_ALLOWLIST = ",".join(
    pk for pk in (PUBKEYS.get("conductor"), PUBKEYS.get("operator")) if pk
)


def split_frontmatter(text: str) -> tuple[dict, str]:
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 3)
    if end == -1:
        return {}, text
    raw, body = text[3:end], text[end + 4 :]
    fields: dict[str, str] = {}
    for line in raw.splitlines():
        if ":" in line and not line.startswith((" ", "-", "\t")):
            k, v = line.split(":", 1)
            fields[k.strip()] = v.strip().strip('"')
    return fields, body.lstrip("\n")


def build_prompt(name: str, body: str, shared: str) -> Path:
    PROMPTS.mkdir(parents=True, exist_ok=True)
    path = PROMPTS / f"{name}.prompt.md"
    path.write_text(
        f"{body}\n\n---\n\n# Shared pack instructions\n\n{shared}\n", encoding="utf-8"
    )
    return path


def proxy_is_up() -> tuple[bool, str]:
    try:
        with urllib.request.urlopen(f"{PROXY_URL}/_spend", timeout=8) as r:
            d = json.loads(r.read())
        return True, (f"spent ${d.get('spent_usd', 0):.4f} of "
                      f"${d.get('cap_usd', 0):.2f}, "
                      f"${d.get('remaining_usd', 0):.4f} left")
    except Exception as e:  # noqa: BLE001 - any failure means "not usable"
        return False, str(e)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--runtime", choices=["gemini", "claude"], default="gemini")
    ap.add_argument("--only", nargs="*")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    for required in (BUZZ_ACP, DEV_MCP, KEYS):
        if not required.exists():
            print(json.dumps({"ok": False, "missing": str(required)}))
            return 1

    if args.runtime == "gemini":
        # Not gemini.cmd directly: its --acp mode advertises authMethods and
        # waits for an `authenticate` call that buzz-acp never makes, so every
        # turn fails with "Gemini API key is missing". The shim performs that
        # handshake and hands buzz-acp an already-authenticated agent.
        agent_command = Path(NODE_BIN)
        agent_args = str(REPO / "pipeline" / "scripts" / "gemini_acp_shim.js")
        model = GEMINI_MODEL
        # Refuse to start uncapped. Running seven agents straight at Vertex with
        # no meter is exactly how an unexplained bill happens.
        ok, detail = proxy_is_up()
        if not ok and not args.dry_run:
            print(json.dumps({
                "ok": False,
                "reason": "spend proxy is not running — refusing to start uncapped",
                "detail": detail,
                "fix": "python pipeline/scripts/vertex_spend_proxy.py",
            }, indent=2))
            return 1
        print(json.dumps({"spend_cap": detail}), flush=True)
    else:
        agent_command = NPM_BIN / "claude-agent-acp.cmd"
        agent_args = ""
        model = CLAUDE_MODEL

    if not agent_command.exists() and not args.dry_run:
        print(json.dumps({"ok": False, "missing": str(agent_command)}))
        return 1

    keys = json.loads(KEYS.read_text(encoding="utf-8"))
    shared = (PACK / "instructions.md").read_text(encoding="utf-8")
    manifest = json.loads((PACK / ".plugin" / "plugin.json").read_text(encoding="utf-8"))
    wanted = set(args.only) if args.only else None

    LOGS.mkdir(parents=True, exist_ok=True)
    started = []

    for rel in manifest["personas"]:
        persona_path = PACK / rel
        fields, body = split_frontmatter(persona_path.read_text(encoding="utf-8"))
        name = fields.get("name") or persona_path.stem.replace(".persona", "")

        if wanted is not None and name not in wanted:
            continue
        if name not in keys:
            print(json.dumps({"ok": False, "reason": f"no key for {name}"}))
            return 1

        is_conductor = name == "conductor"
        prompt_file = build_prompt(name, body, shared)
        cmd = [
            str(BUZZ_ACP),
            "--private-key", keys[name]["private_key_hex"],
            "--relay-url", RELAY_URL,
            "--agent-command", str(agent_command),
            # Equals form, not a separate token: a value starting with `--`
            # (e.g. `--acp`) is otherwise parsed as a buzz-acp flag of its own
            # and startup dies with "unexpected argument '--acp' found".
            f"--agent-args={agent_args}",
            "--mcp-command", str(DEV_MCP),
            "--system-prompt-file", str(prompt_file),
            "--subscribe", SUBSCRIBE.get(name, DEFAULT_SUBSCRIBE),
            # The persona `model:` field only reaches Goose (it becomes
            # GOOSE_MODEL, which buzz strips for other runtimes), so the model
            # has to be set here or the log reads `model=(agent default)`.
            # Per-agent tier for the claude runtime; single model for gemini.
            "--model", (MODEL_TIER.get(name, model) if args.runtime == "claude" else model),
            # Small window for the conductor (it mediates threads); near-zero for
            # workers (they only need the dispatch that summoned them).
            "--context-message-limit", (CONDUCTOR_CONTEXT if is_conductor else WORKER_CONTEXT),
            "--max-turns-per-session", MAX_TURNS_PER_SESSION,
            # Kill a hung turn at 4 min instead of letting it burn for 15.
            "--idle-timeout", IDLE_TIMEOUT,
            # NIP-AE core-memory injection renders an [Agent Memory] block into
            # every single prompt. These agents carry their whole brief in the
            # persona + pack already, so it is pure per-turn overhead — cut it.
            "--no-memory",
        ]
        # Star topology (see WORKER_ALLOWLIST): the conductor stays open so it can
        # hear the operator kickoff and read the channel; workers respond only to
        # the conductor + operator, never to each other, which is what collapses
        # the N^2 wake cascade that was burning the tokens.
        if is_conductor or not WORKER_ALLOWLIST:
            cmd += ["--respond-to", "anyone"]
        else:
            cmd += ["--respond-to", "allowlist",
                    "--respond-to-allowlist", WORKER_ALLOWLIST]

        if args.dry_run:
            safe = list(cmd)
            safe[safe.index("--private-key") + 1] = "<redacted>"
            print(" ".join(safe))
            started.append({"agent": name, "dry_run": True})
            continue

        env = os.environ.copy()
        # Agents post with `buzz messages send`; .claude/settings.local.json
        # allows it as `Bash(buzz messages:*)`, so the bare name must resolve.
        # The research tools go on PATH here for the same reason: last run the
        # scout wrote `export PATH=... && opencli ...`, and a compound command
        # does not match `Bash(opencli:*)`, so every research call was denied
        # and it fell back to plain web search with no engagement data at all.
        env["PATH"] = os.pathsep.join([
            str(BUZZ_ACP.parent),
            str(NPM_BIN),
            r"C:\Users\Advay Anand\AppData\Roaming\Python\Python313\Scripts",
            r"C:\Users\Advay Anand\.local\bin",
            env.get("PATH", ""),
        ])
        env["PYTHONIOENCODING"] = "utf-8"
        env["BUZZ_RELAY_URL"] = "http://127.0.0.1:3000"
        env["BUZZ_PRIVATE_KEY"] = keys[name]["private_key_hex"]

        if args.runtime == "gemini":
            env["GOOGLE_GENAI_USE_VERTEXAI"] = "true"
            env["GOOGLE_CLOUD_PROJECT"] = VERTEX_PROJECT
            env["GOOGLE_CLOUD_LOCATION"] = VERTEX_LOCATION
            # The whole point: every Vertex call goes through the meter.
            env["GOOGLE_VERTEX_BASE_URL"] = PROXY_URL
            env["GEMINI_MODEL"] = model
            env["GEMINI_ACP_DEBUG"] = "1"

        log = (LOGS / f"{name}.log").open("ab")
        proc = subprocess.Popen(
            cmd, stdout=log, stderr=subprocess.STDOUT,
            cwd=str(REPO), env=env,
            creationflags=getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0),
        )
        started.append({"agent": name, "pid": proc.pid})
        # Stagger. Six harnesses opening WebSockets in the same instant made the
        # relay answer 404 to all but one; started one at a time they all
        # connect. Cheap insurance against a race we do not control.
        time.sleep(6)

    print(json.dumps({"ok": True, "runtime": args.runtime, "model": model,
                      "started": started}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
