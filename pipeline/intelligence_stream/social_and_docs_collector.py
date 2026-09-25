"""A01's collectors — free sources that run anywhere, no browser bridge.

Every source here is a public feed or API reachable with plain HTTP, so the
scrape runs the same on a laptop, on another machine and in a container:

  news_feeds       crypto newsroom RSS (CoinDesk, Cointelegraph, The Block,
                   Decrypt, The Defiant, …) — configurable, no key
  google_news      Google News RSS over a rotating slice of queries, no key
  gdelt            GDELT DOC 2.0 article search, one request a run, no key
                   (it allows one request per 5 s and answers 429 above that)
  reddit           the official Reddit API when REDDIT_CLIENT_ID and
                   REDDIT_CLIENT_SECRET are set (scores and comment counts);
                   otherwise the public multireddit RSS
  telegram         public broadcast channels via their t.me/s/ web preview;
                   with TELEGRAM_API_ID, TELEGRAM_API_HASH and a
                   TELEGRAM_SESSION string, Telethon reads them (and groups
                   the account has joined) through Telegram's own API
  docs_blogs       blog RSS, and docs pages that emit a signal only when the
                   page's content actually changed since the last scrape
  defillama        TVL movers from the DefiLlama API, no key
  defillama_hacks  recent exploits from the DefiLlama hacks API, no key
  twitter          the protocols' X accounts through an Apify actor, with
                   engagement counts; needs APIFY_TOKEN (paid per tweet,
                   inside Apify's free monthly credit at this volume)

The old X collector (OpenCLI driving the founder's logged-in Chrome) is gone:
it could not run anywhere but one laptop. Two rules carried over:

  * A source that fails contributes nothing. No placeholder signal is ever
    made up — the Telegram and Blend "fallbacks" this replaces were fixed
    strings presented as HIGH-confidence observations every run.
  * Relevance words come from the tenant's brand profile, not from code.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from html import unescape
from pathlib import Path
from typing import Any, Dict, List, Optional

from pipeline.intelligence_stream import source_config as _source_config

REPO_ROOT = Path(__file__).resolve().parents[2]
STATE_DIR = REPO_ROOT / "pipeline" / "state"
DOCS_WATCH = STATE_DIR / "docs_watch.json"

# Always interesting to a credit / DeFi infrastructure brand; the tenant's own
# relevance terms are added to these.
BASE_KEYWORDS = [
    "liquidation", "margin", "leverage", "bad debt", "contagion", "exploit", "hack",
    "lending", "borrow", "collateral", "credit", "stablecoin", "oracle", "audit",
    "yield", "vault", "defi", "tokeniz", "rwa", "restaking", "perp",
]


def _env(name: str) -> Optional[str]:
    v = os.environ.get(name)
    if v:
        return v
    # The last definition wins, as in dotenv: a key added again below an old
    # or placeholder line is the one meant.
    found = None
    try:
        for line in (REPO_ROOT / "pipeline" / ".env").read_text(encoding="utf-8").splitlines():
            if line.startswith(name + "="):
                found = line.split("=", 1)[1].strip().strip('"') or found
    except FileNotFoundError:
        pass
    return found


def _strip(html: str) -> str:
    return " ".join(unescape(re.sub(r"<[^>]+>", " ", html or "")).split())


def _iso(when: str) -> str:
    """RSS dates (RFC 822) and ISO both come back as ISO 8601, UTC."""
    if not when:
        return ""
    try:
        from email.utils import parsedate_to_datetime
        return parsedate_to_datetime(when).astimezone(timezone.utc).isoformat()
    except Exception:                               # noqa: BLE001 — already ISO, or unparseable
        return when


def _sid(prefix: str, text: str) -> str:
    return prefix + "-" + hashlib.md5(text.encode("utf-8", "replace")).hexdigest()[:8]


class SocialAndDocsCollector:
    """Free, portable collectors for A01. Each returns raw signal dicts."""

    _CFG = _source_config.load()
    TELEGRAM_CHANNELS = _CFG["telegram_channels"]
    REDDIT_SUBREDDITS = _CFG["reddit_subreddits"]
    DOCS_AND_BLOGS = _CFG["docs_and_blogs"]
    NEWS_FEEDS = _CFG.get("news_feeds", [])
    DEFILLAMA = _CFG.get("defillama", {})

    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                          "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
        }
        try:
            from pipeline.brand_brain import context as C
            terms = [t.lower() for t in C.relevance_terms()]
        except Exception:                           # noqa: BLE001 — brain not onboarded
            terms = []
        self.keywords = list(dict.fromkeys(BASE_KEYWORDS + terms))

    # --------------------------------------------------------------- helpers

    def _get(self, url: str, timeout: float = 15.0, headers: Optional[dict] = None,
             data: Optional[bytes] = None) -> bytes:
        req = urllib.request.Request(url, headers=headers or self.headers, data=data)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read()

    def _relevant(self, text: str) -> bool:
        low = text.lower()
        return any(k in low for k in self.keywords)

    def _rss_items(self, xml_bytes: bytes) -> List[Dict[str, str]]:
        out = []
        try:
            root = ET.fromstring(xml_bytes)
        except ET.ParseError:
            return out
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        for item in root.findall(".//item"):
            out.append({"title": _strip(item.findtext("title", "")),
                        "link": (item.findtext("link", "") or "").strip(),
                        "summary": _strip(item.findtext("description", ""))[:600],
                        "published": _iso(item.findtext("pubDate", "") or "")})
        for entry in root.findall(".//atom:entry", ns):
            link = entry.find("atom:link", ns)
            out.append({"title": _strip(entry.findtext("atom:title", "", ns)),
                        "link": link.get("href", "") if link is not None else "",
                        "summary": _strip(entry.findtext("atom:summary", "", ns)
                                          or entry.findtext("atom:content", "", ns))[:600],
                        "published": entry.findtext("atom:updated", "", ns)
                        or entry.findtext("atom:published", "", ns) or ""})
        return [i for i in out if i["title"]]

    # ------------------------------------------------------------ news feeds

    def collect_news_feed_signals(self, per_feed: int = 4) -> List[Dict[str, Any]]:
        """Crypto newsroom RSS: the most recent relevant items from each feed."""
        signals: List[Dict[str, Any]] = []
        for feed in self.NEWS_FEEDS:
            try:
                items = self._rss_items(self._get(feed["url"], timeout=15.0))
            except Exception:                       # noqa: BLE001 — this feed fails alone
                continue
            kept = 0
            for it in items:
                if kept >= per_feed:
                    break
                if not self._relevant(it["title"] + " " + it["summary"]):
                    continue
                kept += 1
                key = re.sub(r"[^A-Z0-9]", "", feed["name"].upper())[:14]
                signals.append({
                    "signal_id": _sid("SIG-FEED-" + key, it["title"]),
                    "headline": it["title"] + " - " + feed["name"],
                    "description": it["summary"] or it["title"],
                    "source": it["link"] or feed["url"],
                    "source_type": "PRIMARY_NEWS_OBSERVED",
                    "derivation_provenance": "NEWS_RSS:" + feed["name"],
                    "timestamp": it["published"] or datetime.now(timezone.utc).isoformat(),
                    "confidence": "HIGH",
                    "data": {"publisher": feed["name"], "title": it["title"], "summary": it["summary"]},
                })
        return signals

    def collect_google_news_signals(self, query: str = "defi lending", limit: int = 5) -> List[Dict[str, Any]]:
        """Google News RSS search for one query."""
        # "when:7d" keeps the search to the last week; without it the feed
        # ranks by relevance and returned stories months old.
        url = ("https://news.google.com/rss/search?q=" + urllib.parse.quote(query + " when:7d")
               + "&hl=en-US&gl=US&ceid=US:en")
        try:
            items = self._rss_items(self._get(url, timeout=12.0))
        except Exception:                           # noqa: BLE001 — boundary
            return []
        return [{
            "signal_id": _sid("SIG-NEWS", it["title"]),
            "headline": "[Market News] " + it["title"],
            "source": it["link"] or url,
            "source_type": "PRIMARY_NEWS_OBSERVED",
            "derivation_provenance": "GOOGLE_NEWS_RSS_SYNDICATION",
            "timestamp": it["published"] or datetime.now(timezone.utc).isoformat(),
            "confidence": "HIGH",
            "data": {"title": it["title"], "url": it["link"], "query": query},
        } for it in items[:limit]]

    def collect_gdelt_signals(self, queries: List[str], limit: int = 8) -> List[Dict[str, Any]]:
        """GDELT article search: one combined request a run (its limit is one
        request per 5 s, and a 429 is taken as 'nothing this run')."""
        if not queries:
            return []
        q = "(" + " OR ".join('"' + x.replace('"', "") + '"' for x in queries[:4]) + ")"
        url = ("https://api.gdeltproject.org/api/v2/doc/doc?query=" + urllib.parse.quote(q)
               + "&mode=artlist&format=json&maxrecords=" + str(limit * 3)
               + "&timespan=3d&sort=datedesc&sourcelang=english")
        try:
            arts = json.loads(self._get(url, timeout=25.0).decode("utf-8", "replace")).get("articles", [])
        except Exception:                           # noqa: BLE001 — rate-limited or down
            return []
        out, seen = [], set()
        for a in arts:
            title = _strip(a.get("title", ""))
            if not title or title.lower() in seen or not self._relevant(title):
                continue
            seen.add(title.lower())
            out.append({
                "signal_id": _sid("SIG-GDELT", title),
                "headline": title + " - " + str(a.get("domain", "")),
                "source": a.get("url", ""),
                "source_type": "PRIMARY_NEWS_OBSERVED",
                "derivation_provenance": "GDELT_DOC_API",
                "timestamp": a.get("seendate", "") or datetime.now(timezone.utc).isoformat(),
                "confidence": "MEDIUM",
                "data": {"publisher": a.get("domain"), "title": title},
            })
            if len(out) >= limit:
                break
        return out

    # ---------------------------------------------------------------- reddit

    def _reddit_token(self) -> Optional[str]:
        cid, secret = _env("REDDIT_CLIENT_ID"), _env("REDDIT_CLIENT_SECRET")
        if not (cid and secret):
            return None
        import base64
        auth = base64.b64encode((cid + ":" + secret).encode()).decode()
        try:
            body = self._get("https://www.reddit.com/api/v1/access_token", timeout=15.0,
                             headers={"Authorization": "Basic " + auth,
                                      "User-Agent": "brand-gtm-research/1.0",
                                      "Content-Type": "application/x-www-form-urlencoded"},
                             data=b"grant_type=client_credentials")
            return json.loads(body).get("access_token")
        except Exception:                           # noqa: BLE001 — fall back to RSS
            return None

    def collect_reddit_signals(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Reddit: the official API with scores when keys exist, else RSS."""
        subs = list(self.REDDIT_SUBREDDITS)
        multi = "+".join(subs)
        posts: List[Dict[str, Any]] = []
        token = self._reddit_token()
        if token:
            try:
                j = json.loads(self._get("https://oauth.reddit.com/r/" + multi + "/hot?limit=100",
                                         timeout=15.0,
                                         headers={"Authorization": "bearer " + token,
                                                  "User-Agent": "brand-gtm-research/1.0"}))
                for c in j.get("data", {}).get("children", []):
                    d = c.get("data", {})
                    posts.append({"sub": d.get("subreddit", ""), "title": d.get("title", ""),
                                  "link": "https://www.reddit.com" + d.get("permalink", ""),
                                  "updated": datetime.fromtimestamp(d.get("created_utc", 0), timezone.utc).isoformat(),
                                  "score": d.get("score"), "comments": d.get("num_comments"),
                                  "via": "REDDIT_API"})
            except Exception:                       # noqa: BLE001 — fall back to RSS
                posts = []
        if not posts:
            url = "https://www.reddit.com/r/" + multi + "/.rss?limit=100"
            for attempt in range(2):
                try:
                    for it in self._rss_items(self._get(url, timeout=12.0)):
                        m = re.search(r"/r/([^/]+)/", it["link"])
                        posts.append({"sub": m.group(1) if m else "", "title": it["title"],
                                      "link": it["link"], "updated": it["published"],
                                      "score": None, "comments": None, "via": "REDDIT_RSS"})
                    break
                except urllib.error.HTTPError as exc:
                    if exc.code != 429 or attempt:
                        break
                    time.sleep(10)
                except Exception:                   # noqa: BLE001 — boundary
                    break
        per_sub: Dict[str, int] = {}
        canon = {s.lower(): s for s in subs}
        signals = []
        for p in posts:
            sub = canon.get(str(p["sub"]).lower())
            if not sub or per_sub.get(sub, 0) >= limit or not self._relevant(p["title"]):
                continue
            per_sub[sub] = per_sub.get(sub, 0) + 1
            signals.append({
                "signal_id": _sid("SIG-REDDIT-" + sub.upper(), p["title"]),
                "headline": "[Reddit r/" + sub + "] " + p["title"],
                "source": p["link"],
                "source_type": "REDDIT_COMMUNITY_OBSERVED",
                "derivation_provenance": p["via"] + ":r/" + sub,
                "timestamp": p["updated"] or datetime.now(timezone.utc).isoformat(),
                "confidence": "HIGH",
                "data": {"platform": "reddit", "subreddit": "r/" + sub, "title": p["title"],
                         "link": p["link"], "score": p["score"], "comments": p["comments"]},
            })
        return signals

    # -------------------------------------------------------------- telegram

    def _telegram_via_telethon(self, per_channel: int) -> Optional[List[Dict[str, Any]]]:
        api_id, api_hash, session = (_env("TELEGRAM_API_ID"), _env("TELEGRAM_API_HASH"),
                                     _env("TELEGRAM_SESSION"))
        if not (api_id and api_hash and session):
            return None
        try:
            from telethon.sessions import StringSession
            from telethon.sync import TelegramClient
        except Exception:                           # noqa: BLE001 — telethon not installed
            return None
        out = []
        try:
            with TelegramClient(StringSession(session), int(api_id), api_hash) as client:
                for ch in self.TELEGRAM_CHANNELS:
                    for msg in client.iter_messages(ch["handle"], limit=per_channel * 3):
                        text = " ".join(str(msg.message or "").split())
                        if text:
                            out.append((ch, text, msg.date.isoformat(),
                                        "https://t.me/" + ch["handle"] + "/" + str(msg.id),
                                        getattr(msg, "views", None)))
        except Exception:                           # noqa: BLE001 — fall back to web preview
            return None
        return self._telegram_signals(out, per_channel, "TELEGRAM_API")

    def _telegram_signals(self, rows, per_channel: int, via: str) -> List[Dict[str, Any]]:
        signals, per = [], {}
        for ch, text, when, link, views in rows:
            h = ch["handle"]
            if per.get(h, 0) >= per_channel or not self._relevant(text):
                continue
            per[h] = per.get(h, 0) + 1
            signals.append({
                "signal_id": _sid("SIG-TG-" + h.upper(), text[:120]),
                "headline": "[" + ch["entity"] + " Telegram] " + text[:160],
                "description": text[:700],
                "source": link,
                "source_type": "TELEGRAM_CHANNEL_OBSERVED",
                "derivation_provenance": via + ":" + h,
                "timestamp": when or datetime.now(timezone.utc).isoformat(),
                "confidence": "HIGH",
                "data": {"platform": "telegram", "channel": h, "entity": ch["entity"],
                         "snippet": text[:250], "views": views},
            })
        return signals

    def collect_telegram_signals(self, per_channel: int = 3) -> List[Dict[str, Any]]:
        """Public channels. Telethon when keys exist; else the t.me/s/ preview,
        which public broadcast channels serve (groups and chats do not)."""
        via_api = self._telegram_via_telethon(per_channel)
        if via_api is not None:
            return via_api
        rows = []
        for ch in self.TELEGRAM_CHANNELS:
            try:
                html = self._get("https://t.me/s/" + ch["handle"], timeout=15.0).decode("utf-8", "replace")
            except Exception:                       # noqa: BLE001 — this channel fails alone
                continue
            blocks = re.split(r'<div class="tgme_widget_message_wrap', html)[1:]
            for b in reversed(blocks):              # newest last on the page
                text = re.search(r'<div class="tgme_widget_message_text[^"]*"[^>]*>(.*?)</div>', b, re.S)
                when = re.search(r'<time datetime="([^"]+)"', b)
                post = re.search(r'data-post="([^"]+)"', b)
                views = re.search(r'<span class="tgme_widget_message_views">([^<]+)</span>', b)
                if text:
                    rows.append((ch, _strip(text.group(1)), when.group(1) if when else "",
                                 "https://t.me/" + post.group(1) if post else "https://t.me/s/" + ch["handle"],
                                 views.group(1) if views else None))
        return self._telegram_signals(rows, per_channel, "TELEGRAM_WEB_PREVIEW")

    # ----------------------------------------------------------- docs & blogs

    def collect_docs_and_blog_signals(self, per_feed: int = 3) -> List[Dict[str, Any]]:
        """Blog RSS items, and docs pages that changed since the last scrape.

        A docs page is watched by the hash of its visible text. The first
        scrape records it; a later one emits a signal only when the text
        changed — a real "the docs were updated" event, never a standing
        description of the page."""
        signals: List[Dict[str, Any]] = []
        try:
            watch = json.loads(DOCS_WATCH.read_text(encoding="utf-8"))
        except Exception:                           # noqa: BLE001 — first run
            watch = {}
        changed_watch = False
        for doc in self.DOCS_AND_BLOGS:
            if doc["type"] == "RSS":
                try:
                    items = self._rss_items(self._get(doc["url"], timeout=15.0))
                except Exception:                   # noqa: BLE001 — this feed fails alone
                    continue
                kept = 0
                for it in items:
                    if kept >= per_feed:
                        break
                    if not self._relevant(it["title"] + " " + it["summary"]):
                        continue
                    kept += 1
                    signals.append({
                        "signal_id": _sid("SIG-DOCS", it["title"]),
                        "headline": "[" + doc["name"] + "] " + it["title"],
                        "description": it["summary"] or it["title"],
                        "source": it["link"] or doc["url"],
                        "source_type": "PRIMARY_DOCS_OBSERVED",
                        "derivation_provenance": "OFFICIAL_BLOG_FEED:" + doc["name"],
                        "timestamp": it["published"] or datetime.now(timezone.utc).isoformat(),
                        "confidence": "HIGH",
                        "data": {"title": it["title"], "url": it["link"], "publisher": doc["name"]},
                    })
            else:
                try:
                    html = self._get(doc["url"], timeout=15.0).decode("utf-8", "replace")
                except Exception:                   # noqa: BLE001 — this page fails alone
                    continue
                body = re.sub(r"(?is)<(script|style|nav|footer|header)[^>]*>.*?</\1>", " ", html)
                text = _strip(body)
                title = _strip((re.search(r"(?is)<title>(.*?)</title>", html) or [None, doc["name"]])[1])
                h = hashlib.sha1(text.encode("utf-8", "replace")).hexdigest()
                prev = watch.get(doc["url"])
                if prev and prev.get("hash") != h:
                    signals.append({
                        "signal_id": _sid("SIG-DOCS", doc["url"] + h),
                        "headline": "[" + doc["name"] + "] documentation updated: " + title,
                        "description": text[:600],
                        "source": doc["url"],
                        "source_type": "PRIMARY_DOCS_OBSERVED",
                        "derivation_provenance": "DOCS_CHANGE_DETECTED:" + doc["name"],
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "confidence": "HIGH",
                        "data": {"publisher": doc["name"], "previous_scrape": prev.get("at")},
                    })
                if not prev or prev.get("hash") != h:
                    watch[doc["url"]] = {"hash": h, "at": datetime.now(timezone.utc).isoformat()}
                    changed_watch = True
        if changed_watch:
            try:
                DOCS_WATCH.write_text(json.dumps(watch, indent=1), encoding="utf-8")
            except Exception:                       # noqa: BLE001 — boundary
                pass
        return signals

    # --------------------------------------------------------------------- X

    def collect_x_signals(self) -> List[Dict[str, Any]]:
        """Recent posts from the protocols' X accounts, through an Apify actor.

        Needs APIFY_TOKEN (Apify's free plan carries monthly credit; the
        default actor charges per tweet returned). Without the token the
        source is simply empty — nothing is invented.

        The default actor (kaitoeasyapi's tweet scraper) runs on Apify's free
        plan without a monthly run limit, applies `maxItems` to EACH search
        term (so one run covers every account evenly) and honours
        "-filter:replies". apidojo/tweet-scraper was tried first: it caps free
        users' runs per month and returned only placeholder "noResults" items
        once the cap was hit, and one shared maxItems let the first account
        take every slot.
        """
        token = _env("APIFY_TOKEN")
        cfg = dict(self._CFG.get("x_scraper") or {})
        accounts = self._CFG.get("x_accounts") or []
        if not token or not accounts or not cfg.get("enabled", True):
            return []
        per = int(cfg.get("per_account", 3))
        days = int(cfg.get("max_age_days", 7))
        since = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%d")
        actor = str(cfg.get("actor", "kaitoeasyapi~twitter-x-data-tweet-scraper-pay-per-result-cheapest"))
        timeout_s = int(cfg.get("timeout_s", 80))
        url = ("https://api.apify.com/v2/acts/" + actor
               + "/run-sync-get-dataset-items?timeout=" + str(timeout_s))
        body = {"searchTerms": ["from:" + a["handle"] + " since:" + since + " -filter:replies"
                                for a in accounts],
                "maxItems": int(cfg.get("items_per_account", 20)), "queryType": "Latest"}
        try:
            items = json.loads(self._get(url, timeout=timeout_s + 5,
                                         headers={"Authorization": "Bearer " + token,
                                                  "Content-Type": "application/json",
                                                  "User-Agent": "brand-gtm-research/1.0"},
                                         data=json.dumps(body).encode()))
        except Exception:                           # noqa: BLE001 — no posts this run
            return []
        items = [it for it in (items if isinstance(items, list) else []) if "noResults" not in it]
        names = {a["handle"].lower(): a.get("name") or a["handle"] for a in accounts}
        per_count: Dict[str, int] = {}
        signals = []
        for it in items if isinstance(items, list) else []:
            author = (it.get("author") or {}).get("userName") or it.get("username") or ""
            handle = str(author).lstrip("@").lower()
            text = " ".join(str(it.get("text") or it.get("fullText") or "").split())
            if (handle not in names or not text or it.get("isRetweet") or it.get("isReply")
                    or text.startswith("@")):
                continue
            if per_count.get(handle, 0) >= per:
                continue
            per_count[handle] = per_count.get(handle, 0) + 1
            when = str(it.get("createdAt") or "")
            try:
                when = datetime.strptime(when, "%a %b %d %H:%M:%S %z %Y").astimezone(timezone.utc).isoformat()
            except ValueError:
                pass
            link = it.get("url") or it.get("twitterUrl") or ("https://x.com/" + handle)
            signals.append({
                "signal_id": _sid("SIG-TWITTER-" + handle.upper(), text[:140]),
                "headline": "[" + names[handle] + " on X] " + text[:200],
                "description": text[:900],
                "source": link,
                "source_type": "X_POST_OBSERVED",
                "derivation_provenance": "APIFY:" + actor,
                "timestamp": when or datetime.now(timezone.utc).isoformat(),
                "confidence": "HIGH",
                "data": {"platform": "x", "handle": handle, "name": names[handle], "url": link,
                         "likes": it.get("likeCount"), "reposts": it.get("retweetCount"),
                         "replies": it.get("replyCount"), "quotes": it.get("quoteCount"),
                         "views": it.get("viewCount")},
            })
        return signals

    # -------------------------------------------------------------- defillama

    def collect_defillama_signals(self, limit: int = 6) -> List[Dict[str, Any]]:
        """Protocols whose TVL moved most this week, from DefiLlama.

        Measured rather than editorial: TVL changes daily, so the movers are
        genuinely different each cycle and each signal carries a real, dated
        number that the claim gate can check against the same endpoint.
        """
        cfg = dict(self.DEFILLAMA or {})
        if not cfg.get("enabled", True):
            return []
        categories = set(cfg.get("categories") or ["Lending", "CDP"])
        min_tvl = float(cfg.get("min_tvl_usd") or 20_000_000)
        limit = int(cfg.get("movers") or limit)
        try:
            protocols = json.loads(self._get("https://api.llama.fi/protocols", timeout=20.0))
        except Exception:                           # noqa: BLE001 — boundary
            return []
        rows = [p for p in protocols
                if p.get("category") in categories
                and float(p.get("tvl") or 0) >= min_tvl
                and p.get("change_7d") is not None]
        # Biggest absolute movers: a collapse is as much of a story as a rally.
        rows.sort(key=lambda p: abs(float(p.get("change_7d") or 0)), reverse=True)
        now = datetime.now(timezone.utc).isoformat()
        signals = []
        for p in rows[:limit]:
            name = str(p.get("name") or "?")
            tvl = float(p.get("tvl") or 0)
            d7 = float(p.get("change_7d") or 0)
            headline = (name + " TVL " + ("rose" if d7 >= 0 else "fell") + " "
                        + f"{abs(d7):.1f}% in 7 days to ${tvl/1e6:,.1f}M ({p.get('category')})")
            signals.append({
                "signal_id": "SIG-LLAMA-" + hashlib.md5((name + str(round(d7, 2))).encode()).hexdigest()[:8],
                "headline": headline,
                "source": "https://defillama.com/protocol/" + str(p.get("slug") or name),
                "source_type": "PRIMARY_ONCHAIN_OBSERVED",
                "derivation_provenance": "DEFILLAMA_API_TVL_SNAPSHOT",
                "timestamp": now,
                "confidence": "HIGH",
                "data": {"protocol": name, "category": p.get("category"), "tvl_usd": tvl,
                         "change_7d_pct": d7, "change_1d_pct": p.get("change_1d"),
                         "chains": p.get("chains") or []},
            })
        return signals

    def collect_defillama_hacks(self, days: int = 30, limit: int = 5) -> List[Dict[str, Any]]:
        """Exploits in the last `days`, largest first — each one a dated,
        sourced instance of the risk a credit protocol is built to contain."""
        try:
            hacks = json.loads(self._get("https://api.llama.fi/hacks", timeout=20.0))
        except Exception:                           # noqa: BLE001 — boundary
            return []
        since = (datetime.now(timezone.utc) - timedelta(days=days)).timestamp()
        recent = [h for h in hacks if float(h.get("date") or 0) >= since]
        recent.sort(key=lambda h: -float(h.get("amount") or 0))
        signals = []
        for h in recent[:limit]:
            name = str(h.get("name") or "?")
            amt = float(h.get("amount") or 0)
            when = datetime.fromtimestamp(float(h.get("date") or 0), timezone.utc)
            how = str(h.get("technique") or h.get("classification") or "exploit")
            headline = (name + " exploited for $" + f"{amt/1e6:,.1f}M" + " via " + how
                        + " (" + when.strftime("%Y-%m-%d") + ")")
            signals.append({
                "signal_id": _sid("SIG-HACK", name + when.isoformat()),
                "headline": headline,
                "description": headline + ". Chains: " + ", ".join(h.get("chain") or []) + ".",
                "source": str(h.get("source") or "https://defillama.com/hacks"),
                "source_type": "PRIMARY_ONCHAIN_OBSERVED",
                "derivation_provenance": "DEFILLAMA_HACKS_API",
                "timestamp": when.isoformat(),
                "confidence": "HIGH",
                "data": {"protocol": name, "amount_usd": amt, "technique": h.get("technique"),
                         "classification": h.get("classification"), "chains": h.get("chain") or [],
                         "returned_usd": h.get("returnedFunds")},
            })
        return signals
