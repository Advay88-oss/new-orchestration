#!/usr/bin/env python3
"""Tenant-aware trend scout — real research from a tenant's own sources.

Unlike the trendjack orchestrator (hardcoded to Decrypt's crypto RSS and Gemini),
this reads the tenant's OKF bundle research config — its keywords and subreddits —
and gathers live signals appropriate to THAT company. For Auri that is gold,
inflation, tokenized gold and fintech; for Vanna it is DeFi and agent credit.

Sources, each best-effort (one failing never kills the run):
  1. Google News RSS per keyword  — real, no auth, works for any topic
  2. OpenCLI reddit search per subreddit — real engagement, if the bridge is up
  3. OpenCLI twitter search per keyword — real engagement, if the bridge is up

Output: pipeline/state/trends/<tenant>-<UTCdate>.json + a printed summary.
The synthesis (pick the trend, bridge it to an arc) is done by the brain
(Gemini when up, or Claude) reading this JSON — the scout only gathers.

    OKF_BUNDLE=okf-auri python pipeline/scripts/trend_scout.py --tenant auri
    python pipeline/scripts/trend_scout.py --tenant vanna --no-social   # RSS only
"""

from __future__ import annotations

import argparse
import html
import json
import re
import subprocess
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(HERE))
from okf_loader import Bundle, default_bundle_path  # noqa: E402

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}


def google_news(query: str, limit: int = 5) -> list[dict]:
    """Recent news for a query via Google News RSS (no auth, any topic)."""
    url = ("https://news.google.com/rss/search?q="
           + urllib.parse.quote(query + " when:14d")
           + "&hl=en-US&gl=US&ceid=US:en")
    out = []
    try:
        req = urllib.request.Request(url, headers=UA)
        with urllib.request.urlopen(req, timeout=25) as r:
            root = ET.fromstring(r.read())
        for item in root.findall(".//item")[:limit]:
            title = (item.findtext("title") or "").strip()
            link = (item.findtext("link") or "").strip()
            pub = (item.findtext("pubDate") or "").strip()
            src_el = item.find("{*}source")
            source = src_el.text.strip() if src_el is not None and src_el.text else "news"
            out.append({"channel": "google-news", "keyword": query, "title": title,
                        "url": link, "published": pub, "source": source, "engagement": None})
    except Exception as e:
        print(f"  ! google-news '{query}': {e}")
    return out


def opencli(args: list[str], timeout: int = 60) -> str | None:
    try:
        r = subprocess.run(["opencli", *args], capture_output=True, text=True,
                           timeout=timeout, shell=True, encoding="utf-8", errors="replace")
        return r.stdout if r.returncode == 0 else None
    except Exception:
        return None


def reddit_search(subreddit: str, keyword: str, limit: int = 3) -> list[dict]:
    """Best-effort reddit signal via OpenCLI (real engagement when the bridge is up)."""
    raw = opencli(["reddit", "search", f"{keyword} subreddit:{subreddit}", "-f", "json"])
    out = []
    if not raw:
        return out
    try:
        data = json.loads(raw)
        posts = data if isinstance(data, list) else data.get("results", data.get("posts", []))
        for p in (posts or [])[:limit]:
            out.append({"channel": "reddit", "keyword": keyword,
                        "title": (p.get("title") or "")[:200],
                        "url": p.get("url") or p.get("permalink") or "",
                        "published": p.get("created") or p.get("created_utc") or "",
                        "source": f"r/{subreddit}",
                        "engagement": p.get("score") or p.get("ups")})
    except Exception:
        pass
    return out


def twitter_search(keyword: str, limit: int = 3) -> list[dict]:
    raw = opencli(["twitter", "search", keyword, "--limit", str(limit), "-f", "json"])
    out = []
    if not raw:
        return out
    try:
        data = json.loads(raw)
        tweets = data if isinstance(data, list) else data.get("results", data.get("tweets", []))
        for t in (tweets or [])[:limit]:
            eng = (t.get("likes", 0) or 0) + (t.get("retweets", 0) or 0)
            out.append({"channel": "twitter", "keyword": keyword,
                        "title": (t.get("text") or "")[:200],
                        "url": t.get("url") or "", "published": t.get("created_at") or "",
                        "source": "@" + (t.get("author") or "?"), "engagement": eng})
    except Exception:
        pass
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tenant", default=None, help="label for the output file")
    ap.add_argument("--bundle", type=Path, default=None)
    ap.add_argument("--max-keywords", type=int, default=6)
    ap.add_argument("--no-social", action="store_true", help="RSS only, skip OpenCLI")
    args = ap.parse_args()

    root = args.bundle or default_bundle_path()
    bundle = Bundle.load(root)
    rc = bundle.research_config()
    tenant = args.tenant or root.name.replace("okf-", "").replace("okf", "vanna")
    keywords = (rc.get("search_keywords") or [])[: args.max_keywords]
    subreddits = rc.get("subreddits") or []

    print(f"=== trend scout · tenant={tenant} · bundle={root.name} ===")
    print(f"keywords : {keywords}")
    print(f"subreddits: {subreddits}")
    print(f"social   : {'off' if args.no_social else 'on (best-effort)'}\n")

    items: list[dict] = []

    print("[1] Google News RSS per keyword")
    for kw in keywords:
        got = google_news(kw)
        print(f"    {kw:26} {len(got)} items")
        items += got

    if not args.no_social:
        print("\n[2] Reddit (OpenCLI, best-effort)")
        for sub in subreddits[:4]:
            kw = keywords[0] if keywords else ""
            got = reddit_search(sub, kw)
            print(f"    r/{sub:22} {len(got)} items")
            items += got
        print("\n[3] Twitter (OpenCLI, best-effort)")
        for kw in keywords[:3]:
            got = twitter_search(kw)
            print(f"    {kw:26} {len(got)} items")
            items += got

    # dedupe by title
    seen, deduped = set(), []
    for it in items:
        k = re.sub(r"\W+", "", (it["title"] or "").lower())[:60]
        if k and k not in seen:
            seen.add(k)
            deduped.append(it)

    # engagement first (where known), then keep order (recency-ish from RSS)
    deduped.sort(key=lambda x: (x.get("engagement") or 0), reverse=True)

    out_dir = REPO / "pipeline" / "state" / "trends"
    out_dir.mkdir(parents=True, exist_ok=True)
    # Per-RUN timestamp (not just date) so a later, weaker pull never overwrites
    # an earlier richer one. learn.py globs all trends/*.json and dedupes, so
    # keeping every run compounds the signal instead of destroying it.
    stamp = time.strftime("%Y-%m-%d-%H%M%S", time.gmtime())
    out = out_dir / f"{tenant}-{stamp}.json"
    payload = {"tenant": tenant, "bundle": root.name, "gathered_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
               "keywords": keywords, "subreddits": subreddits,
               "counts": {"total": len(deduped),
                          "google_news": sum(1 for i in deduped if i["channel"] == "google-news"),
                          "reddit": sum(1 for i in deduped if i["channel"] == "reddit"),
                          "twitter": sum(1 for i in deduped if i["channel"] == "twitter")},
               "items": deduped}
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"\n=== {len(deduped)} unique signals -> {out.relative_to(REPO)} ===")
    for it in deduped[:12]:
        eng = f" ·{it['engagement']}" if it.get("engagement") else ""
        print(f"  [{it['channel']}{eng}] {it['title'][:78]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
