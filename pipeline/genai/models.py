"""Model routing — which model serves which role, and over which transport.

The founder's routing, made explicit and enforceable:

    reasoning    gemini-3.8-flash            Vertex preferred
    critic       gemini-3.8-flash            Vertex preferred  (multimodal)
    image        gemini-3.1-flash-image      "nano banana"
    meme_image   nano-banana-pro-preview     "nano banana pro"
    video        veo-3.1-generate-preview    + Remotion / motion graphics

Two rules, both learned from the audit:

1. **A role's model is verified against the provider's live model list before
   use.** The old stack printed `gemini-3.8-flash` while a proxy silently
   rewrote it to `gemini-2.5-flash`; here a rewrite is impossible because the
   name is checked and the served name is recorded.

2. **Transport fallback is recorded, never silent.** Vertex needs ADC, which
   this org expires frequently. Falling back to the API key still runs the
   right model, so the work is real — but the run says which transport served
   it, and a fallback marks the stage `degraded` rather than `ok`.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Literal

from .llm import LLMClient, LLMError, available_models

Role = Literal["reasoning", "critic", "image", "meme_image", "video"]
Transport = Literal["vertex", "apikey"]


@dataclass(frozen=True)
class Route:
    role: Role
    model: str
    prefer: Transport
    fallback: Transport | None
    note: str


# Vertex project/location for the Model Garden path the founder wired up.
VERTEX_PROJECT = os.environ.get("VANNA_VERTEX_PROJECT", "vanna-mcp")
VERTEX_LOCATION = os.environ.get("VANNA_VERTEX_LOCATION", "global")

ROUTES: dict[Role, Route] = {
    "reasoning": Route(
        "reasoning", os.environ.get("VANNA_MODEL_REASONING", "gemini-3.8-flash"),
        "vertex", "apikey", "strategy, copy, claims, concepts, specs"),
    "critic": Route(
        "critic", os.environ.get("VANNA_MODEL_CRITIC", "gemini-3.8-flash"),
        "vertex", "apikey", "multimodal visual critique"),
    "image": Route(
        "image", os.environ.get("VANNA_MODEL_IMAGE", "gemini-3.1-flash-image"),
        "apikey", None, "nano banana — background texture only, never text"),
    "meme_image": Route(
        "meme_image", os.environ.get("VANNA_MODEL_MEME", "nano-banana-pro-preview"),
        "apikey", None, "nano banana pro — memes page"),
    "video": Route(
        "video", os.environ.get("VANNA_MODEL_VIDEO", "veo-3.1-generate-preview"),
        "apikey", None, "Veo 3.1 + motion graphics + Remotion"),
}


class RoutingError(RuntimeError):
    pass


@dataclass
class Resolved:
    """A route bound to a transport that is actually usable right now."""
    role: Role
    model: str
    transport: Transport
    degraded_reason: str | None = None
    note: str = ""

    @property
    def ok(self) -> bool:
        return self.degraded_reason is None


def vertex_available() -> tuple[bool, str]:
    """Can we mint a Vertex token right now? Cheap, cached per process."""
    global _VERTEX_STATE
    if _VERTEX_STATE is not None:
        return _VERTEX_STATE
    try:
        import google.auth
        from google.auth.transport.requests import Request as GRequest

        creds, _ = google.auth.default(
            scopes=["https://www.googleapis.com/auth/cloud-platform"])
        if not creds.valid:
            creds.refresh(GRequest())
        _VERTEX_STATE = (bool(creds.token), "" if creds.token else "no token returned")
    except Exception as exc:
        _VERTEX_STATE = (False, f"{type(exc).__name__}: {str(exc)[:160]}")
    return _VERTEX_STATE


_VERTEX_STATE: tuple[bool, str] | None = None
_MODEL_CACHE: list[str] | None = None


def served_models() -> list[str]:
    global _MODEL_CACHE
    if _MODEL_CACHE is None:
        try:
            _MODEL_CACHE = available_models()
        except Exception:
            _MODEL_CACHE = []
    return _MODEL_CACHE


def resolve(role: Role) -> Resolved:
    """Bind a role to a model + a transport that works, recording any downgrade."""
    route = ROUTES.get(role)
    if route is None:
        raise RoutingError(f"no route declared for role {role!r}")

    models = served_models()
    if models and route.model not in models:
        raise RoutingError(
            f"role {role!r} is routed to {route.model!r}, which this key does not "
            f"serve. Declared routes must name a real model.")

    if route.prefer == "vertex":
        ok, why = vertex_available()
        if ok:
            return Resolved(role, route.model, "vertex", note=route.note)
        if route.fallback:
            return Resolved(
                role, route.model, route.fallback,
                degraded_reason=f"Vertex unavailable ({why}); served over {route.fallback}",
                note=route.note)
        raise RoutingError(f"role {role!r} requires Vertex and it is unavailable: {why}")

    return Resolved(role, route.model, route.prefer, note=route.note)


def client_for(role: Role, **kw) -> tuple[LLMClient, Resolved]:
    """An LLM client bound to the role's model, plus how it was resolved."""
    r = resolve(role)
    return LLMClient(model=r.model, transport=r.transport, **kw), r


def routing_table() -> list[dict]:
    """Serialised for the dashboard, including live reachability."""
    models = served_models()
    v_ok, v_why = vertex_available()
    out = []
    for role, route in ROUTES.items():
        served = (route.model in models) if models else None
        transport = route.prefer
        degraded = None
        if route.prefer == "vertex" and not v_ok:
            transport = route.fallback or "vertex"
            degraded = f"Vertex unavailable ({v_why})"
        out.append({
            "role": role,
            "model": route.model,
            "preferred_transport": route.prefer,
            "effective_transport": transport,
            "served_by_key": served,
            "degraded": degraded,
            "note": route.note,
        })
    return out


if __name__ == "__main__":
    import json

    print(json.dumps({
        "vertex": dict(zip(("available", "reason"), vertex_available())),
        "vertex_project": VERTEX_PROJECT,
        "vertex_location": VERTEX_LOCATION,
        "routes": routing_table(),
    }, indent=2))
