"""One chokepoint for paid API calls.

The pipeline calls Gemini, Veo, image models, embeddings and Apify from
many modules, each with its own urllib code. Rather than wire a budget
into every one (and miss the next), `install()` wraps urllib.request.urlopen
once per process: a request to a paid endpoint is checked against the day's
caps before it goes (BudgetExceeded, which callers already treat as a
failed call) and its cost is added after — from the response's token counts
where the body says them, else the per-call estimate in config/budget.json.

Operation polls (GET …/operations/…), Telegram, GCS and everything else pass
through untouched.
"""
from __future__ import annotations

import io
import json
import re
import urllib.request
from typing import Any, Optional

_orig = urllib.request.urlopen
_installed = False
IMAGE_MODEL = re.compile(r"image|imagen|nano-banana", re.I)


def classify(url: str, method: str) -> Optional[str]:
    u = url.lower()
    if "api.apify.com" in u and "/runs" not in u and method == "POST":
        return "apify"
    gen = "generativelanguage.googleapis.com" in u or "aiplatform.googleapis.com" in u or "127.0.0.1:8900" in u
    if not gen or method != "POST":
        return None
    if ":predictlongrunning" in u:
        return "veo"
    if ":embedcontent" in u or ":batchembedcontents" in u:
        return "embed"
    if ":generatecontent" in u or ":streamgeneratecontent" in u:
        model = u.split("/models/")[-1].split(":")[0] if "/models/" in u else ""
        return "image" if IMAGE_MODEL.search(model) else "gemini"
    return None


class _Counted:
    """The response, read through once to count its tokens or results."""

    def __init__(self, resp, service: str, stream: bool):
        self._resp, self._service, self._stream = resp, service, stream
        self._counted = False

    def read(self, *a):
        data = self._resp.read(*a)
        if not self._counted and not a:
            self._counted = True
            _account(self._service, data)
        return data

    def __iter__(self):                             # streaming: counted by the caller (assistant)
        return iter(self._resp)

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        if not self._counted and not self._stream:
            self._counted = True
            _account(self._service, b"")
        return self._resp.__exit__(*exc)

    def __getattr__(self, name):
        return getattr(self._resp, name)


def _account(service: str, body: bytes) -> None:
    from pipeline.ops import budget as B
    rates = (B.config().get("rates") or {}).get(service) or {}
    try:
        if service == "gemini" and body:
            u = (json.loads(body.decode("utf-8", "replace")) or {}).get("usageMetadata") or {}
            i, o = int(u.get("promptTokenCount") or 0), int(u.get("candidatesTokenCount") or 0)
            if i or o:
                B.add("gemini", B.token_cost(i, o), input_tokens=i, output_tokens=o)
                return
        if service == "apify" and body:
            items = json.loads(body.decode("utf-8", "replace"))
            n = len(items) if isinstance(items, list) else 0
            B.add("apify", float(rates.get("per_call", 0.01)) + n * float(rates.get("per_result", 0.00025)))
            return
    except ValueError:
        pass
    B.add(service, float(rates.get("per_call", rates.get("per_call_estimate", 0.004))))


def _guarded(url, data=None, timeout=None, *args, **kwargs):
    req = url if isinstance(url, urllib.request.Request) else None
    full = req.full_url if req else str(url)
    method = (req.get_method() if req else ("POST" if data is not None else "GET")).upper()
    service = classify(full, method)
    if service:
        from pipeline.ops import budget as B
        B.check(service)                             # BudgetExceeded: the call is not made
    call_kwargs: dict[str, Any] = dict(kwargs)
    if timeout is not None:
        call_kwargs["timeout"] = timeout
    resp = _orig(url, data, *args, **call_kwargs) if data is not None else _orig(url, *args, **call_kwargs)
    if not service:
        return resp
    return _Counted(resp, service, stream=":streamgeneratecontent" in full.lower())


def install() -> None:
    """Idempotent. Set OPS_GUARD=0 to run without it (tests of the guard itself)."""
    global _installed
    import os
    if _installed or os.environ.get("OPS_GUARD") == "0":
        return
    urllib.request.urlopen = _guarded
    _installed = True
