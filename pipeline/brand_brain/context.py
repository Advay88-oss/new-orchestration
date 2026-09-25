"""What agents put in their prompts — built from the brain, never from code.

Every company-specific word an agent used to carry in a Python constant
(the product anchors, the partner list, the prohibited visuals, the palette,
the house style, the "Vanna is ... on Stellar Soroban TESTNET" line) now
comes from the tenant's brand profile or its knowledge base, through these
helpers. Agents call them; the tenant comes from the session.

The profile is read once per process and refreshed every 60 s, so an edit the
founder approves on the dashboard reaches the next run without a restart.
"""
from __future__ import annotations

import json
import threading
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Optional

from pipeline.brand_brain.client import Brain, current_tenant

SEEDS = Path(__file__).resolve().parent / "seeds"
_lock = threading.Lock()
_cache: dict[str, tuple[float, dict]] = {}


def brain(tenant: Optional[str] = None) -> Brain:
    return Brain(tenant or current_tenant())


def profile(tenant: Optional[str] = None) -> dict[str, Any]:
    """The tenant's brand profile. Falls back to the tenant's seed file (data,
    not code) only if its brain has not been created yet."""
    t = tenant or current_tenant()
    with _lock:
        hit = _cache.get(t)
        if hit and time.time() - hit[0] < 60:
            return hit[1]
    try:
        p = Brain(t).get_brand_profile()
    except Exception:                               # noqa: BLE001 — brain not onboarded
        p = {}
    if not p:
        seed = SEEDS / (t + ".profile.json")
        p = json.loads(seed.read_text(encoding="utf-8")) if seed.exists() else {}
    with _lock:
        _cache[t] = (time.time(), p)
    return p


def _get(path: str, default: Any = None, tenant: Optional[str] = None) -> Any:
    cur: Any = profile(tenant)
    for k in path.split("."):
        if not isinstance(cur, dict) or k not in cur:
            return default
        cur = cur[k]
    return cur


# ------------------------------------------------------------------ identity

def company_name(tenant: Optional[str] = None) -> str:
    return str(_get("company.name", "the company", tenant))


def company_line(tenant: Optional[str] = None) -> str:
    """One paragraph: what the company is and where it is deployed."""
    what = _get("company.what_it_is", "", tenant)
    dep = _get("company.deployment", "", tenant)
    return (company_name(tenant) + " — " + what + (" Deployment: " + dep if dep else "")).strip()


def stage(tenant: Optional[str] = None) -> str:
    return str(_get("company.stage", "", tenant))


def cta(tenant: Optional[str] = None) -> str:
    return str(_get("voice.cta", "", tenant))


def disclosure(tenant: Optional[str] = None) -> str:
    """The word every capability statement must carry (e.g. 'testnet')."""
    return str(_get("voice.required_disclosure", "", tenant))


def disclosure_footer(tenant: Optional[str] = None) -> str:
    return str(_get("visual.disclosure_footer", "", tenant))


# ------------------------------------------------------------ claims & people

def anchors(tenant: Optional[str] = None) -> dict[str, str]:
    return dict(_get("visual.anchors", {}, tenant) or {})


def partners(tenant: Optional[str] = None) -> dict[str, str]:
    return dict(_get("partners", {}, tenant) or {})


def is_partner(name: str, tenant: Optional[str] = None) -> bool:
    n = " ".join(str(name or "").lower().split())
    return any(n == k.lower() for k in partners(tenant))


def competitors(tenant: Optional[str] = None) -> list[str]:
    return [str(c.get("name")) for c in (_get("competitors", [], tenant) or []) if c.get("name")]


def approved_claims(tenant: Optional[str] = None) -> list[str]:
    return list(_get("claims.approved", [], tenant) or [])


def prohibited_claims(tenant: Optional[str] = None) -> list[str]:
    return list(_get("claims.prohibited", [], tenant) or [])


def true_figures(tenant: Optional[str] = None) -> list[dict]:
    return list(_get("claims.true_figures", [], tenant) or [])


def never_state(tenant: Optional[str] = None) -> list[str]:
    return list(_get("claims.never_state", [], tenant) or [])


def pillars(tenant: Optional[str] = None) -> list[str]:
    return list(_get("pillars", [], tenant) or [])


def audiences(tenant: Optional[str] = None) -> list[dict]:
    return list(_get("audiences", [], tenant) or [])


def relevance_terms(tenant: Optional[str] = None) -> list[str]:
    return list(_get("relevance_terms", [], tenant) or [])


# -------------------------------------------------------------------- visual

def palette(tenant: Optional[str] = None) -> dict[str, str]:
    return dict(_get("visual.palette", {}, tenant) or {})


def fonts(tenant: Optional[str] = None) -> dict[str, str]:
    return dict(_get("visual.fonts", {}, tenant) or {})


def house_style(tenant: Optional[str] = None) -> str:
    return str(_get("visual.house_style", "", tenant))


def prohibited_visual(tenant: Optional[str] = None) -> str:
    return str(_get("visual.prohibited", "", tenant))


def avoid_colors(tenant: Optional[str] = None) -> list[str]:
    return list(_get("visual.avoid_colors", [], tenant) or [])


def logo_path(tenant: Optional[str] = None) -> Optional[Path]:
    p = _get("visual.logo.path", None, tenant)
    if not p:
        return None
    path = Path(p)
    return path if path.is_absolute() else Path(__file__).resolve().parents[2] / path


def logo_description(tenant: Optional[str] = None) -> str:
    return str(_get("visual.logo.description", "", tenant))


# -------------------------------------------------------------- prompt blocks

def figures_block(tenant: Optional[str] = None) -> str:
    """The true figures and the kinds of number that may never be stated."""
    lines = ["TRUE FIGURES (the only numbers that may appear):"]
    lines += ["  - " + f["value"] + " — " + f.get("meaning", "") for f in true_figures(tenant)]
    ns = never_state(tenant)
    if ns:
        lines.append("Never state: " + ", ".join(ns) + ".")
    return "\n".join(lines)


def partners_block(tenant: Optional[str] = None) -> str:
    p = partners(tenant)
    if not p:
        return ""
    return ("CONFIRMED PARTNERS (the whole list — never claim a relationship with anything "
            "not on it):\n" + "\n".join("  - " + n + " (" + r + ")" for n, r in p.items()))


def voice_block(tenant: Optional[str] = None) -> str:
    v = _get("voice", {}, tenant) or {}
    lines = ["VOICE: " + ", ".join(v.get("tone", []))]
    if v.get("do"):
        lines += ["Do:"] + ["  - " + d for d in v["do"]]
    if v.get("dont"):
        lines += ["Don't:"] + ["  - " + d for d in v["dont"]]
    if v.get("banned_words"):
        lines.append("Banned words: " + ", ".join(v["banned_words"]))
    return "\n".join(lines)


def whats_new_block(days: int = 21, tenant: Optional[str] = None) -> str:
    since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    try:
        ev = brain(tenant).get_whats_new(since, 8)
    except Exception:                               # noqa: BLE001 — boundary
        ev = []
    if not ev:
        return ""
    return ("WHAT'S NEW (dated):\n"
            + "\n".join("  - " + e["at"][:10] + " " + e["title"]
                        + (": " + e["detail"][:200] if e.get("detail") else "") for e in ev))


def knowledge_hits(topic: str, k: int = 8, tenant: Optional[str] = None,
                   max_authority: int = 3) -> list[dict]:
    try:
        return brain(tenant).search_knowledge(topic, k=k, max_authority=max_authority)
    except Exception:                               # noqa: BLE001 — boundary
        return []


def facts_block(topic: str, *, k: int = 8, excerpts: Optional[int] = None,
                tenant: Optional[str] = None) -> str:
    """Everything an agent should know before writing about `topic`: the
    product anchors, the knowledge base's best sections for the topic with
    their sources, the partner list, what is new, and what is never claimed.
    Archive material (authority 4) is left out: it predates the current
    deployment in places and is not proof of anything."""
    k = excerpts or k
    name = company_name(tenant).upper()
    lines = [name + " — GROUND TRUTH", "", company_line(tenant), "",
             "Product anchors (use these, they are what " + company_name(tenant)
             + " concretely is):"]
    lines += ["  - " + a + ": " + v for a, v in anchors(tenant).items()]
    hits = knowledge_hits(topic, k=k, tenant=tenant)
    if hits:
        lines += ["", "From the knowledge base (" + str(len(hits)) + " sections, with sources):"]
        for h in hits:
            lines.append("  [" + h["source"] + " · " + h["section"][:90]
                         + (" · " + h["url"] if h.get("url") else "") + "]")
            lines.append("    " + " ".join(h["text"].split())[:700])
    pb = partners_block(tenant)
    if pb:
        lines += ["", pb]
    wn = whats_new_block(tenant=tenant)
    if wn:
        lines += ["", wn]
    lines += ["", figures_block(tenant)]
    pc = prohibited_claims(tenant)
    if pc:
        lines += ["", "NEVER CLAIM:"] + ["  - " + p for p in pc[:14]]
    return "\n".join(lines)


def brand_visual_block(tenant: Optional[str] = None) -> str:
    """The visual brand for image, video and judge prompts."""
    pal = palette(tenant)
    lines = ["BRAND — " + company_name(tenant),
             "House style: " + house_style(tenant),
             "Palette: " + ", ".join(k + " " + v for k, v in pal.items()),
             "Fonts: " + ", ".join(k + " " + v for k, v in fonts(tenant).items()),
             "Logo: " + logo_description(tenant)]
    if avoid_colors(tenant):
        lines.append("Avoid colours: " + ", ".join(avoid_colors(tenant)))
    if prohibited_visual(tenant):
        lines.append("Never show: " + prohibited_visual(tenant))
    return "\n".join(lines)


def fill(text: str, tenant: Optional[str] = None) -> str:
    """Company facts into a prompt written without them. Tokens:
    {company} {company_line} {deployment} {anchors} {house_style} {cta}."""
    p = profile(tenant)
    anc = "; ".join(k + ": " + v.split(" — ")[0] for k, v in anchors(tenant).items())
    return (text.replace("{company_line}", company_line(tenant))
            .replace("{company}", company_name(tenant))
            .replace("{deployment}", str(p.get("company", {}).get("deployment", "")))
            .replace("{anchors}", anc)
            .replace("{house_style}", house_style(tenant))
            .replace("{cta}", cta(tenant)))
