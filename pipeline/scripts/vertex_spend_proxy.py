#!/usr/bin/env python3
"""A Vertex AI proxy that enforces a hard dollar cap.

Why this exists: GCP budgets are *alerts*, not caps. A $10 budget does not stop
spend at $10 — it emails you while the meter keeps running. The only native hard
stop is a Cloud Function that detaches the billing account, which on
sales-agent-504607 would also kill the sales-agent workload. So the cap lives
here instead, in the one place we control: between the agents and the API.

Every Gemini response carries `usageMetadata` with real token counts. We price
those, add them to a ledger on disk, and refuse to forward once the cap is hit.
The ledger is persistent, so restarting the agents does not reset the budget.

Fail-closed by design: if the ledger cannot be read, or a response arrives with
no usage metadata, we charge a conservative estimate rather than assume zero.

Usage:
    python pipeline/scripts/vertex_spend_proxy.py            # serve on :8900
    python pipeline/scripts/vertex_spend_proxy.py --status   # print the ledger
    python pipeline/scripts/vertex_spend_proxy.py --reset    # start a new budget period

Point the agent runtime at http://127.0.0.1:8900 instead of
https://<loc>-aiplatform.googleapis.com and the cap applies to everything.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
LEDGER = REPO / "pipeline" / "state" / "spend-ledger.json"
CALL_LOG = REPO / "pipeline" / "logs" / "vertex-calls.jsonl"

PROJECT = os.environ.get("VERTEX_PROJECT", "sales-agent-504607")
LOCATION = os.environ.get("VERTEX_LOCATION", "us-central1")
UPSTREAM = f"https://{LOCATION}-aiplatform.googleapis.com"
CAP_USD = float(os.environ.get("VERTEX_CAP_USD", "10.00"))
PORT = int(os.environ.get("VERTEX_PROXY_PORT", "8900"))

# USD per 1M tokens. VERIFY THESE against current Vertex pricing before trusting
# the ledger as an exact figure — they are deliberately set on the high side so
# the cap trips early rather than late. A wrong-but-high rate under-spends; a
# wrong-but-low rate is how you end up explaining $109.
PRICES = {
    "default": {"input": 0.50, "output": 2.00},
}
# Charged when a response arrives with no usageMetadata at all. Deliberately
# pessimistic — an uncounted call must never be a free call.
UNKNOWN_CALL_USD = 0.02

# Gemini CLI hardcodes a Gemini 3.x preference and walks its own fallback chain
# (3.5-flash → 3.1-flash → 3.1-pro). None of those are served on this project —
# only the 2.5 family answers here. Neither `-m` nor settings.json overrides it,
# so the rewrite happens at the one place that sees every request: here.
MODEL_REWRITE = {
    "gemini-3.8-flash": "gemini-2.5-flash",
    "gemini-3.8": "gemini-2.5-flash",
    "gemini-3.5-flash": "gemini-2.5-flash",
    "gemini-3.1-flash": "gemini-2.5-flash",
    "gemini-3-flash": "gemini-2.5-flash",
    "gemini-flash-latest": "gemini-2.5-flash",
    "gemini-3.5-pro": "gemini-2.5-pro",
    "gemini-3.1-pro": "gemini-2.5-pro",
    "gemini-3-pro": "gemini-2.5-pro",
}


# Fields Gemini CLI sends that only the 3.x models accept. Forwarding them to a
# 2.5 model gets a 400 INVALID_ARGUMENT, so they are dropped alongside the model
# rewrite. Dropping is safe: they are generation hints, not semantics.
UNSUPPORTED_GEN_FIELDS = ("thinkingLevel", "thinking_level", "thinkingConfig",
                          "thinking_config")


def sanitize_body(raw: bytes, rewritten: bool) -> bytes:
    """Strip 3.x-only generation fields when we have downgraded the model."""
    if not rewritten or not raw:
        return raw
    try:
        payload = json.loads(raw)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return raw
    cfg = payload.get("generationConfig")
    if isinstance(cfg, dict):
        for field in UNSUPPORTED_GEN_FIELDS:
            cfg.pop(field, None)
    for field in UNSUPPORTED_GEN_FIELDS:
        payload.pop(field, None)
    return json.dumps(payload).encode()


def extract_usage(body: bytes) -> dict | None:
    """Pull usageMetadata out of a Gemini response, streaming or not.

    `generateContent` returns one object; `streamGenerateContent` — which the CLI
    actually uses — returns an array of chunks, and only the last carries the
    totals. Missing this is not a rounding error: it drops every call onto the
    pessimistic flat rate and burns the budget an order of magnitude too fast.
    """
    if not body:
        return None
    try:
        payload = json.loads(body)
    except (json.JSONDecodeError, UnicodeDecodeError):
        # SSE framing (`data: {...}` lines) — scan back for the last usage block.
        try:
            text = body.decode("utf-8", errors="replace")
        except Exception:  # noqa: BLE001
            return None
        best = None
        for line in text.splitlines():
            line = line.strip().removeprefix("data:").strip()
            if not line.startswith("{"):
                continue
            try:
                chunk = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(chunk, dict) and chunk.get("usageMetadata"):
                best = chunk["usageMetadata"]
        return best

    if isinstance(payload, dict):
        return payload.get("usageMetadata")
    if isinstance(payload, list):
        for chunk in reversed(payload):
            if isinstance(chunk, dict) and chunk.get("usageMetadata"):
                return chunk["usageMetadata"]
    return None


def rewrite_path(path: str) -> tuple[str, str | None]:
    """Swap an unavailable model id for one this project serves.

    Returns (path, rewritten_from) so the swap is visible in the call log rather
    than being a silent substitution nobody can audit.
    """
    for wrong, right in MODEL_REWRITE.items():
        if f"/models/{wrong}:" in path or path.endswith(f"/models/{wrong}"):
            return path.replace(wrong, right), wrong
    return path, None

_lock = threading.Lock()
_token_cache: dict[str, float | str] = {}


def price_for(model: str) -> dict[str, float]:
    for key, rates in PRICES.items():
        if key != "default" and key in model:
            return rates
    return PRICES["default"]


def load_ledger() -> dict:
    if not LEDGER.exists():
        return {"spent_usd": 0.0, "calls": 0, "input_tokens": 0,
                "output_tokens": 0, "started": time.strftime("%Y-%m-%dT%H:%M:%SZ",
                                                             time.gmtime())}
    try:
        return json.loads(LEDGER.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        # Fail closed: an unreadable ledger is treated as an exhausted budget,
        # never as a fresh one.
        return {"spent_usd": CAP_USD, "calls": 0, "input_tokens": 0,
                "output_tokens": 0, "corrupt": True}


def save_ledger(led: dict) -> None:
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    tmp = LEDGER.with_suffix(".tmp")
    tmp.write_text(json.dumps(led, indent=2), encoding="utf-8")
    tmp.replace(LEDGER)


def charge(model: str, usage: dict | None) -> tuple[float, dict]:
    rates = price_for(model)
    if usage:
        inp = int(usage.get("promptTokenCount", 0))
        out = int(usage.get("candidatesTokenCount", 0))
        # Thinking tokens bill as output on models that report them separately.
        out += int(usage.get("thoughtsTokenCount", 0))
        cost = (inp * rates["input"] + out * rates["output"]) / 1_000_000
    else:
        inp = out = 0
        cost = UNKNOWN_CALL_USD

    with _lock:
        led = load_ledger()
        led["spent_usd"] = round(led.get("spent_usd", 0.0) + cost, 6)
        led["calls"] = led.get("calls", 0) + 1
        led["input_tokens"] = led.get("input_tokens", 0) + inp
        led["output_tokens"] = led.get("output_tokens", 0) + out
        save_ledger(led)
    return cost, led


def access_token() -> str | None:
    """ADC token, cached until shortly before expiry."""
    now = time.time()
    if _token_cache.get("value") and float(_token_cache.get("expires", 0)) > now + 60:
        return str(_token_cache["value"])
    gcloud = os.environ.get(
        "GCLOUD_BIN",
        r"C:\Users\Advay Anand\AppData\Local\Google\Cloud SDK\google-cloud-sdk\bin\gcloud.cmd",
    )
    try:
        out = subprocess.run([gcloud, "auth", "application-default", "print-access-token"],
                             capture_output=True, text=True, timeout=60,
                             encoding="utf-8", errors="replace")
    except (OSError, subprocess.TimeoutExpired):
        return None
    tok = (out.stdout or "").strip()
    if not tok.startswith("ya29."):
        return None
    _token_cache["value"] = tok
    _token_cache["expires"] = now + 3000
    return tok


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt, *a):  # quieter than the default stderr spam
        pass

    def _json(self, code: int, payload: dict) -> None:
        body = json.dumps(payload).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        clean_path = self.path.split("?")[0].rstrip("/")
        if clean_path in ("", "/_spend", "/_spend/status", "/health", "/status", "/spend"):
            led = load_ledger()
            led["cap_usd"] = CAP_USD
            led["remaining_usd"] = round(max(0.0, CAP_USD - led.get("spent_usd", 0)), 4)
            led["status"] = "OK"
            led["service"] = "Vanna Vertex Spend Proxy Watchdog (:8900)"
            self._json(200, led)
            return
        self._json(404, {"error": "only /_spend, /health, or / is served on GET", "requested_path": self.path})

    def do_POST(self):
        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length) if length else b""

        # Direct modality charging endpoint for autonomous pipeline agents
        if self.path.rstrip("/") in ("/_charge", "/_spend/charge", "/api/spend/charge"):
            try:
                data = json.loads(raw.decode("utf-8")) if raw else {}
                charge_usd = float(data.get("cost_usd", data.get("spent_usd", 0.052)))
                calls_to_add = int(data.get("calls", 1))
                in_tokens = int(data.get("input_tokens", 1000))
                out_tokens = int(data.get("output_tokens", 500))
                modality = str(data.get("modality", "autonomous_pipeline_run"))

                with _lock:
                    led = load_ledger()
                    current_spent = round(led.get("spent_usd", 0.0) + charge_usd, 6)
                    led["spent_usd"] = current_spent
                    led["calls"] = led.get("calls", 0) + calls_to_add
                    led["input_tokens"] = led.get("input_tokens", 0) + in_tokens
                    led["output_tokens"] = led.get("output_tokens", 0) + out_tokens
                    led["remaining_usd"] = round(max(0.0, CAP_USD - current_spent), 4)
                    save_ledger(led)

                    try:
                        CALL_LOG.parent.mkdir(parents=True, exist_ok=True)
                        with CALL_LOG.open("a", encoding="utf-8") as f:
                            entry = {
                                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                                "model": modality,
                                "input_tokens": in_tokens,
                                "output_tokens": out_tokens,
                                "cost_usd": charge_usd,
                                "running_total_usd": current_spent
                            }
                            f.write(json.dumps(entry) + "\n")
                    except Exception:
                        pass

                self._json(200, led)
                return
            except Exception as e:
                self._json(400, {"error": f"Failed to record charge: {e}"})
                return

        led = load_ledger()
        spent = led.get("spent_usd", 0.0)
        if spent >= CAP_USD:
            self._json(402, {"error": {
                "code": 402, "status": "BUDGET_EXHAUSTED",
                "message": (f"Local spend cap reached: ${spent:.4f} of ${CAP_USD:.2f}. "
                            f"Raise VERTEX_CAP_USD or run --reset to start a new period. "
                            f"This is the proxy refusing, not Vertex.")}})
            return

        token = access_token()
        if not token:
            self._json(401, {"error": {
                "code": 401, "status": "ADC_UNAVAILABLE",
                "message": ("Could not mint an ADC token. Run: gcloud auth "
                            "application-default login --scopes="
                            "https://www.googleapis.com/auth/cloud-platform")}})
            return

        path, rewritten_from = rewrite_path(self.path)
        raw = sanitize_body(raw, rewritten_from is not None)
        url = UPSTREAM + path
        req = urllib.request.Request(url, data=raw, method="POST")
        req.add_header("Authorization", f"Bearer {token}")
        req.add_header("Content-Type", "application/json")
        if PROJECT:
            req.add_header("X-Goog-User-Project", PROJECT)

        try:
            with urllib.request.urlopen(req, timeout=600) as resp:
                body = resp.read()
                status = resp.getcode()
        except urllib.error.HTTPError as e:
            body, status = e.read(), e.code
        except (urllib.error.URLError, TimeoutError) as e:
            self._json(502, {"error": {"code": 502, "message": f"upstream: {e}"}})
            return

        model = path.rsplit("/", 1)[-1].split(":")[0]
        usage = extract_usage(body) if status == 200 else None
        if status == 200:
            cost, led = charge(model, usage)
            try:
                CALL_LOG.parent.mkdir(parents=True, exist_ok=True)
                with CALL_LOG.open("a", encoding="utf-8") as f:
                    f.write(json.dumps({
                        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                        "model": model, "rewritten_from": rewritten_from,
                        "usage": usage, "cost_usd": round(cost, 6),
                        "spent_total": led["spent_usd"],
                    }) + "\n")
            except OSError:
                pass

        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--reset", action="store_true")
    ap.add_argument("--port", type=int, default=PORT)
    args = ap.parse_args()

    if args.status:
        led = load_ledger()
        led["cap_usd"] = CAP_USD
        led["remaining_usd"] = round(max(0.0, CAP_USD - led.get("spent_usd", 0)), 4)
        print(json.dumps(led, indent=2))
        return 0

    if args.reset:
        save_ledger({"spent_usd": 0.0, "calls": 0, "input_tokens": 0,
                     "output_tokens": 0,
                     "started": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())})
        print(json.dumps({"ok": True, "reset": True, "cap_usd": CAP_USD}))
        return 0

    led = load_ledger()
    print(json.dumps({
        "listening": f"http://127.0.0.1:{args.port}",
        "upstream": UPSTREAM,
        "project": PROJECT,
        "cap_usd": CAP_USD,
        "already_spent_usd": led.get("spent_usd", 0.0),
        "note": "point the agent runtime here instead of the aiplatform host",
    }, indent=2), flush=True)

    ThreadingHTTPServer(("127.0.0.1", args.port), Handler).serve_forever()
    return 0


if __name__ == "__main__":
    sys.exit(main())
