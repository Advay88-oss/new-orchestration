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
