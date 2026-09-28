"""Where A01 looks, as data rather than as code.

The source lists used to be class constants in the collector, so widening the
engine's field of view meant editing Python. Worse, they were narrow and
self-referential: four doc sources of which two were Blend and Stellar, two
subreddits, and a single fixed Google News query. A pipeline cannot discover
anything its inputs do not contain, which is how 32 of 41 runs arrived at the
same Blend v2 topic while the agents downstream were working correctly.

Defaults live here so the collector still runs if the config file is missing
or malformed; the file overrides them key by key.
"""
from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Any

CONFIG_PATH = (Path(__file__).resolve().parents[1] / "config"
               / "intelligence_sources.json")

DEFAULTS: dict[str, Any] = {
    "news_queries": ["stellar soroban defi", "defi lending protocol liquidation"],
    "reddit_subreddits": ["defi", "Stellar"],
    "telegram_channels": [
        {"handle": "the_block_crypto", "entity": "The Block"},
        {"handle": "cointelegraph", "entity": "Cointelegraph"},
    ],
    "news_feeds": [
        {"name": "CoinDesk", "url": "https://www.coindesk.com/arc/outboundfeeds/rss/"},
        {"name": "The Block", "url": "https://www.theblock.co/rss.xml"},
    ],
    "docs_and_blogs": [
        {"name": "Stellar Foundation Blog",
         "url": "https://stellar.org/blog/rss.xml", "type": "RSS"},
        {"name": "Blend Protocol Docs",
         "url": "https://docs.blend.capital", "type": "DOCS"},
    ],
    "defillama": {"enabled": True, "categories": ["Lending", "CDP"],
                  "min_tvl_usd": 20_000_000, "movers": 6},
}


def load() -> dict[str, Any]:
    """Config merged over defaults. Never raises — a bad file must not stop a run."""
    cfg = dict(DEFAULTS)
    try:
        raw = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        for k, v in raw.items():
            if k.startswith("_") or v in (None, [], {}):
                continue
            cfg[k] = v
    except Exception:                               # noqa: BLE001 — boundary
        pass
    return _for_tenant(cfg)


# The file above is Vanna's: Stellar queries, r/Stellar, the Stellar and Blend
# blogs, and Vanna's competitors on X (Morpho among them). For any other
# company the scout searches for THAT company: its name and topics, its own X
# account and its competitors', its subreddits and its own blog. The global,
# company-neutral feeds (news RSS, Telegram news channels, DefiLlama) stay.
_VANNA_ONLY = ("stellar", "soroban", "blend")


def _for_tenant(cfg: dict[str, Any]) -> dict[str, Any]:
    try:
        from pipeline.brand_brain import context as C
        from pipeline.brand_brain.client import Brain, current_tenant
        t = current_tenant()
        if t == "vanna":
            return cfg
        p = C.profile(t) or {}
        if not p:
            return cfg
        co = p.get("company") or {}
        name = C.company_name(t)
        b = Brain(t)
        own = str(co.get("x_handle") or b.meta("watch:x_handle") or "").lstrip("@")
        terms = [x for x in (p.get("relevance_terms") or []) if isinstance(x, str) and len(x) > 3][:3]
        cfg = dict(cfg)
        cfg["news_queries"] = [name, name + " protocol", name + " news"] + [name + " " + x for x in terms]
        comps = [c for c in (p.get("competitors") or []) if isinstance(c, dict)]
        x = ([{"handle": own, "name": name}] if own else []) + [
            {"handle": str(c["handle"]).lstrip("@"), "name": c.get("name") or c["handle"]}
            for c in comps if c.get("handle") and str(c["handle"]).lstrip("@").lower() != own.lower()]
        cfg["x_accounts"] = x or [a for a in cfg.get("x_accounts", [])
                                  if str(a.get("name", "")).lower() != name.lower()]
        subs = [str(s).strip().lstrip("/").replace("r/", "", 1) for s in (co.get("subreddits") or [])]
        cfg["reddit_subreddits"] = subs or [s for s in cfg.get("reddit_subreddits", [])
                                            if s.lower() not in _VANNA_ONLY]
        blogs = [d for d in cfg.get("docs_and_blogs", [])
                 if not any(v in (str(d.get("name")) + str(d.get("url"))).lower() for v in _VANNA_ONLY)]
        feed = b.meta("watch:blog_feed")
        if feed:
            blogs = [{"name": name + " Blog", "url": feed, "type": "RSS"}] + blogs
        cfg["docs_and_blogs"] = blogs
    except Exception:                               # noqa: BLE001 — the file's config is the fallback
        pass
    return cfg


def news_queries(n: int = 4) -> list[str]:
    """A different slice of the query list each cycle.

    One fixed query returned near-identical headlines every run. Sampling
    means consecutive cycles genuinely look at different corners of the
    market rather than re-reading the same page.
    """
    qs = list(load().get("news_queries") or DEFAULTS["news_queries"])
    if len(qs) <= n:
        return qs
    return random.sample(qs, n)
