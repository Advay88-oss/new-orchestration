"""X (Twitter) posts through Apify — one call shape for everything that needs it.

The competitor analyzer reads a competitor's recent posts; the metrics
collector reads the founder's published posts back 48-72 hours later. Both
are X advanced-search queries run by the same actor the intelligence scout
uses, with APIFY_TOKEN from pipeline/.env.
"""
from __future__ import annotations

import json
import urllib.request
from datetime import datetime, timezone
from typing import Any, Optional

ACTOR = "kaitoeasyapi~twitter-x-data-tweet-scraper-pay-per-result-cheapest"


def _token() -> Optional[str]:
    from pipeline.intelligence_stream.social_and_docs_collector import _env
    return _env("APIFY_TOKEN")


def _iso(created: str) -> str:
    try:
        return datetime.strptime(created, "%a %b %d %H:%M:%S %z %Y").astimezone(timezone.utc).isoformat()
    except (TypeError, ValueError):
        return str(created or "")


def search(terms: list[str], *, max_items: int = 20, timeout_s: int = 90,
           actor: str = ACTOR) -> list[dict[str, Any]]:
    """Posts matching X search queries, newest first, normalised.
    Raises RuntimeError without a token; returns [] when nothing matched."""
    token = _token()
    if not token:
        raise RuntimeError("APIFY_TOKEN is not set in pipeline/.env")
    url = "https://api.apify.com/v2/acts/" + actor + "/run-sync-get-dataset-items?timeout=" + str(timeout_s)
    body = {"searchTerms": terms, "maxItems": max_items, "queryType": "Latest"}
    req = urllib.request.Request(url, data=json.dumps(body).encode(), method="POST",
                                 headers={"Authorization": "Bearer " + token,
                                          "Content-Type": "application/json",
                                          "User-Agent": "brand-gtm-research/1.0"})
    with urllib.request.urlopen(req, timeout=timeout_s + 10) as r:
        items = json.loads(r.read().decode("utf-8"))
    out = []
    for it in items if isinstance(items, list) else []:
        if "noResults" in it:
            continue
        author = (it.get("author") or {}).get("userName") or it.get("username") or ""
        out.append({
            "id": str(it.get("id") or ""),
            "handle": str(author).lstrip("@"),
            "text": " ".join(str(it.get("text") or it.get("fullText") or "").split()),
            "url": it.get("url") or it.get("twitterUrl") or "",
            "created_at": _iso(it.get("createdAt")),
            "is_reply": bool(it.get("isReply")),
            "is_retweet": bool(it.get("isRetweet")),
            "impressions": it.get("viewCount"),
            "likes": it.get("likeCount"),
            "reposts": it.get("retweetCount"),
            "replies": it.get("replyCount"),
            "quotes": it.get("quoteCount"),
            "bookmarks": it.get("bookmarkCount"),
            "media": [m.get("type") for m in ((it.get("extendedEntities") or {}).get("media") or [])
                      if isinstance(m, dict)],
        })
    return out


def recent_posts(handle: str, *, days: int = 30, n: int = 20) -> list[dict[str, Any]]:
    """An account's own recent posts (no replies, no retweets)."""
    from datetime import timedelta
    since = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%d")
    posts = search(["from:" + handle.lstrip("@") + " since:" + since + " -filter:replies"], max_items=n)
    return [p for p in posts if p["text"] and not p["is_retweet"] and not p["is_reply"]]
