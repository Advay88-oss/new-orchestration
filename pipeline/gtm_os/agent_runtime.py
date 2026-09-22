"""Shared runtime for the 13 GTM agents.

Every agent in `pipeline/gtm_*` previously either called Gemini through its own
private copy of `call_gemini_brain` — each with its own silent `except: return
None` — or called nothing at all. Two consequences the 2026-09-22 audit found:

  * A brain call that failed fell back to "deterministic humanizer synthesis"
    and the run still reported success. The 2026-09-17 trace shipped string
    literals typed into `content_creator.py` while claiming to be a live run.
  * Nine of thirteen agents made no model call whatsoever, so there was nothing
    to report even if anyone had looked.

This module gives all thirteen one way in and one way out:

  `brain()`  routes by ROLE, not by hardcoded URL, so the model each agent uses
             is declared in one table instead of thirteen string literals.
  `record()` appends every call to the run journal — including the failures.
             A degraded call is written down as degraded. That is the whole
             point: the dashboard can only be as honest as this file.

Roles map to the models the founder assigned:
    reasoning   gemini-3.8-flash            all judgement and copy
    image       gemini-3.1-flash-image      "nano banana" — post visuals
    meme        nano-banana-pro-preview     "nano banana pro" — memes
    video       veo-3.1-generate-001        Veo 3.1 — motion
"""
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

REPO_ROOT = Path(__file__).resolve().parents[2]
STATE_DIR = REPO_ROOT / "pipeline" / "state"
RUNS_DIR = STATE_DIR / "gtm_runs"

API_BASE = "https://generativelanguage.googleapis.com/v1beta/models"
# The Vertex spend proxy. The project here is the proxy's own, and it is only
# reachable when the proxy is running locally on :8900.
PROXY_BASE = ("http://127.0.0.1:8900/v1/projects/sales-agent-504607"
              "/locations/us-central1/publishers/google/models")

MODELS: dict[str, str] = {
    "reasoning": os.environ.get("VANNA_GTM_MODEL_REASONING", "gemini-3.8-flash"),
    "image":     os.environ.get("VANNA_GTM_MODEL_IMAGE", "gemini-3.1-flash-image"),
    # "nano banana pro". `nano-banana-pro-preview` is the marketing name and
    # 404s on Model Garden; this is the id the publisher actually serves.
    "meme":      os.environ.get("VANNA_GTM_MODEL_MEME", "gemini-3-pro-image"),
    "video":     os.environ.get("VANNA_GTM_MODEL_VIDEO", "veo-3.1-generate-001"),
}

# Which agent uses which role. Declared here so `--manifest` can print the
# routing and the dashboard cannot invent one.
AGENT_ROLES: dict[str, str] = {
    "A01_intelligence_scout":   "none",
    "A02_opportunity_selector": "reasoning",
    "A03_gtm_strategist":       "reasoning",
    "A04_machine_library":      "none",
    "A05_campaign_engine":      "none",
    "A06_channel_adapter":      "reasoning",
    "A07_creative_director":    "reasoning",
    "A08_visual_synthesis":     "image",
    "A09_video_production":     "video",
    "A10_reviewer_firewall":    "none",
    "A11_dispatch_worker":      "none",
    "A12_telegram_gateway":     "none",
    "A13_learning_engine":      "reasoning",
}

AGENT_NAMES: dict[str, str] = {
    "A01_intelligence_scout":   "Intelligence Scout",
    "A02_opportunity_selector": "Opportunity Selector",
    "A03_gtm_strategist":       "GTM Strategist",
    "A04_machine_library":      "GTM Machine Library",
    "A05_campaign_engine":      "Campaign & Series Engine",
    "A06_channel_adapter":      "Content Creator & Channel Adapter",
    "A07_creative_director":    "Creative Director System",
    "A08_visual_synthesis":     "Visual Synthesis Engine",
    "A09_video_production":     "Video Production Engine",
    "A10_reviewer_firewall":    "Pre-Delivery Reviewer Firewall",
    "A11_dispatch_worker":      "Approved Dispatch Worker",
    "A12_telegram_gateway":     "Telegram Gateway & Listener",
    "A13_learning_engine":      "Closed-Loop Learning Engine",
}


class BrainError(RuntimeError):
    """A model call that did not return usable output.

    Raised rather than returned as None so a caller has to decide, in writing,
    what a failure means for its stage. The old `return None` let every caller
    treat "the model never answered" as "use the canned text".
    """


@dataclass
class AgentCall:
    agent: str
    role: str
    model: Optional[str]
    ok: bool
    duration_s: float
    input_tokens: int = 0
    output_tokens: int = 0
    note: str = ""
    transport: str = ""
    at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


def _api_key() -> Optional[str]:
    key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if key:
        return key
    # pipeline/.env is the documented home for this key and is never committed.
    env = REPO_ROOT / "pipeline" / ".env"
    if env.exists():
        for line in env.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith(("GEMINI_API_KEY=", "GOOGLE_API_KEY=")):
                value = line.split("=", 1)[1].strip()
                return value.strip('"').strip("'")
    return None


def _post(url: str, payload: dict, timeout: float) -> dict:
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def endpoint(role: str) -> tuple[str, str, str]:
    """Return (url, model_id, transport) for a role."""
    model = MODELS.get(role)
    if not model:
        raise BrainError("no model configured for role " + repr(role))
    key = _api_key()
    if key:
        return API_BASE + "/" + model + ":generateContent?key=" + key, model, "apikey"
    return PROXY_BASE + "/" + model + ":generateContent", model, "proxy"


def brain(
    prompt: str,
    *,
    agent: str,
    system: str = "",
    role: str = "reasoning",
    temperature: float = 0.4,
    max_output_tokens: int = 4096,
    json_out: bool = False,
    run_id: Optional[str] = None,
    timeout: float = 90.0,
) -> str:
    """Call the model assigned to `role`, journaling the attempt either way.

    Raises BrainError on failure. It does not return a fallback string: an
    agent that cannot reach its model has not done its job, and the run must be
    able to say so.
    """
    started = time.time()
    url, model, transport = endpoint(role)

    payload: dict[str, Any] = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": temperature,
            "maxOutputTokens": max_output_tokens,
        },
    }
    if system:
        payload["systemInstruction"] = {"parts": [{"text": system}]}
    if json_out:
        payload["generationConfig"]["responseMimeType"] = "application/json"

    try:
        res = _post(url, payload, timeout)
    except urllib.error.HTTPError as exc:
        body = ""
        try:
            body = exc.read().decode("utf-8", "replace")[:300]
        except Exception:
            pass
        note = "HTTP " + str(exc.code) + ": " + body
        record(AgentCall(agent, role, model, False, round(time.time() - started, 2),
                         note=note, transport=transport), run_id)
        raise BrainError(note) from exc
    except Exception as exc:                        # noqa: BLE001 — boundary
        note = (type(exc).__name__ + ": " + str(exc))[:300]
        record(AgentCall(agent, role, model, False, round(time.time() - started, 2),
                         note=note, transport=transport), run_id)
        raise BrainError(note) from exc

    usage = res.get("usageMetadata") or {}
    try:
        text = res["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError, TypeError):
        # A blocked or empty candidate is a failure, not an empty string. The
        # distinction matters: an empty string flows downstream as valid copy.
        note = "no text in response: " + json.dumps(res)[:250]
        record(AgentCall(agent, role, model, False, round(time.time() - started, 2),
                         note=note, transport=transport,
                         input_tokens=usage.get("promptTokenCount", 0)), run_id)
        raise BrainError(note)

    record(AgentCall(
        agent, role, model, True, round(time.time() - started, 2),
        input_tokens=usage.get("promptTokenCount", 0),
        output_tokens=usage.get("candidatesTokenCount", 0),
        transport=transport), run_id)
    return text


def brain_json(prompt: str, **kw) -> Any:
    """`brain` plus a parse. A model that returns unparseable JSON has failed."""
    raw = brain(prompt, json_out=True, **kw)
    txt = raw.strip()
    if txt.startswith("```"):
        parts = txt.split("```")
        txt = parts[1] if len(parts) > 1 else txt
        if txt.startswith("json"):
            txt = txt[4:]
    try:
        return json.loads(txt)
    except json.JSONDecodeError as exc:
        raise BrainError("unparseable JSON from model: " + str(exc)
                         + "; head=" + repr(txt[:200])) from exc


# --------------------------------------------------------------------------
# Journal — the dashboard's only source of truth for these agents
# --------------------------------------------------------------------------

_CURRENT_RUN: dict[str, str] = {}


def set_run(run_id: str) -> str:
    _CURRENT_RUN["id"] = run_id
    (RUNS_DIR / run_id).mkdir(parents=True, exist_ok=True)
    return run_id


def current_run() -> Optional[str]:
    return _CURRENT_RUN.get("id")


def new_run_id() -> str:
    return "GTM-" + datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")


def record(call: AgentCall, run_id: Optional[str] = None) -> None:
    rid = run_id or current_run()
    if not rid:
        return
    d = RUNS_DIR / rid
    d.mkdir(parents=True, exist_ok=True)
    with (d / "calls.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps(asdict(call)) + "\n")


def record_stage(agent: str, status: str, detail: str = "",
                 outputs: Optional[list[str]] = None,
                 run_id: Optional[str] = None) -> None:
    """Record that an agent ran, whether or not it called a model.

    Deterministic agents (the machine library, the dispatch worker) never
    appear in `calls.jsonl`, so without this they would look like they never
    ran. `status` is one of ok | degraded | failed | skipped.
    """
    rid = run_id or current_run()
    if not rid:
        return
    d = RUNS_DIR / rid
    d.mkdir(parents=True, exist_ok=True)
    with (d / "stages.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps({
            "agent": agent,
            "name": AGENT_NAMES.get(agent, agent),
            "role": AGENT_ROLES.get(agent, "none"),
            "status": status,
            "detail": detail[:500],
            "outputs": outputs or [],
            "at": datetime.now(timezone.utc).isoformat(),
        }) + "\n")


def manifest() -> list[dict[str, Any]]:
    out = []
    for i, (aid, role) in enumerate(AGENT_ROLES.items(), start=1):
        out.append({
            "n": i,
            "id": aid,
            "name": AGENT_NAMES.get(aid, aid),
            "role": role,
            "model": MODELS.get(role) if role != "none" else None,
            "kind": "DETERMINISTIC" if role == "none" else "MODEL_BACKED",
        })
    return out


if __name__ == "__main__":
    print(json.dumps({"models": MODELS, "agents": manifest()}, indent=2))
