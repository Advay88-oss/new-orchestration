"""What Vanna can do, taking inspiration from the brands the founder adds.

Only brands the founder adds on What Vanna Can Do are shown. Adding one
stores the company in the brand brain, then the twelve agents do this job:

  - Scout reads X, Reddit, and hands LinkedIn and docs to a grounded search.
  - The analyst, the selector, the strategist and the copywriter write what
    each post is doing, what this company can do with that, and how.
  - The director notes the shape. The poster and video agents do not render
    a new asset; the shelf shows the source.
  - The two judges check the writing. Delivery saves it onto this section.
  - Learning stores a shape note the next post can read.

Every post kept has a real URL. No reward, participant count, or figure is
invented. A number stays only when that post or this company's facts state it.

    python -m pipeline.brand_brain.inspiration list   [tenant]
    python -m pipeline.brand_brain.inspiration add    <tenant> "<name>" [--x handle] [--subreddit name]
    python -m pipeline.brand_brain.inspiration refresh <tenant> <brand-id>
    python -m pipeline.brand_brain.inspiration remove <tenant> <brand-id>
    python -m pipeline.brand_brain.inspiration strategies <tenant> [brand-id]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from pipeline.brand_brain.client import Brain, current_tenant

WINDOW_DAYS = 30
AGENT = "brand-brain-inspiration"
BRANDS_KEY = "inspiration:brands"
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/126.0 Safari/537.36"}
SUBREDDITS = ("defi", "ethfinance", "ethereum", "CryptoCurrency", "Stellar", "ethtrader")


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")[:40] or "brand"


def _when(raw: Any) -> Optional[datetime]:
    try:
        d = datetime.fromisoformat(str(raw or "").replace("Z", "+00:00"))
    except ValueError:
        return None
    return (d if d.tzinfo else d.replace(tzinfo=timezone.utc)).astimezone(timezone.utc)


def _int(v: Any) -> Optional[int]:
    return int(v) if isinstance(v, (int, float)) and not isinstance(v, bool) else None


# ------------------------------------------------------------------ storage

def brands(tenant: str) -> list[dict[str, Any]]:
    try:
        return json.loads(Brain(tenant).meta(BRANDS_KEY) or "[]")
    except ValueError:
        return []


def _save_brands(tenant: str, rows: list[dict]) -> None:
    Brain(tenant).meta(BRANDS_KEY, json.dumps(rows, ensure_ascii=False))


def _data(tenant: str, bid: str) -> dict[str, Any]:
    try:
        return json.loads(Brain(tenant).meta("inspiration:data:" + bid) or "{}")
    except ValueError:
        return {}


def _save_data(tenant: str, bid: str, data: dict) -> None:
    Brain(tenant).meta("inspiration:data:" + bid, json.dumps(data, ensure_ascii=False, default=str))


def _job(tenant: str, bid: str, state: str, **extra: Any) -> None:
    Brain(tenant).meta("inspiration:job:" + bid, json.dumps({"state": state, "at": _now().isoformat(), **extra}))


def job(tenant: str, bid: str) -> dict[str, Any]:
    try:
        return json.loads(Brain(tenant).meta("inspiration:job:" + bid) or "{}")
    except ValueError:
        return {}


# --------------------------------------------------------------- collectors

def _x(handle: str) -> list[dict]:
    from pipeline.intelligence_stream import x_apify
    cutoff = _now() - timedelta(days=WINDOW_DAYS)
    posts = x_apify.search(["from:" + handle.lstrip("@") + " -filter:replies"], max_items=80)
    out = []
    for p in posts:
        at = _when(p.get("created_at"))
        if not p.get("url") or p.get("is_retweet") or p.get("is_reply") or (at and at < cutoff):
            continue
        out.append({"channel": "x", "url": p["url"], "at": p.get("created_at"), "text": p["text"][:600],
                    "by": "@" + (p.get("handle") or handle.lstrip("@")),
                    "likes": _int(p.get("likes")), "replies": _int(p.get("replies")),
                    "reposts": _int(p.get("reposts")), "views": _int(p.get("impressions")),
                    "media": p.get("media") or []})
    return _unique_posts(out)


def _reddit(name: str, subreddit: str) -> list[dict]:
    from pipeline.brand_brain.watch import _atom_or_rss
    q = urllib.parse.quote('"' + name + '"')
    subs = ([subreddit] if subreddit else []) + [s for s in SUBREDDITS if s.lower() != subreddit.lower()]
    cutoff = _now() - timedelta(days=WINDOW_DAYS)
    needle = name.lower()
    out, seen = [], set()
    for s in subs:
        url = ("https://www.reddit.com/r/" + s + "/search.rss?q=" + q
               + "&restrict_sr=1&type=link&sort=new&t=month&limit=25")
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=20) as r:
                items = _atom_or_rss(r.read())
        except Exception:                           # noqa: BLE001 — one subreddit fails alone
            items = []
        for it in items:
            at = _when(it.get("at"))
            if ("/comments/" not in it["url"] or it["url"] in seen or (at and at < cutoff)
                    or needle not in (it["title"] + " " + it["text"]).lower()):
                continue
            seen.add(it["url"])
            out.append({"channel": "reddit", "url": it["url"], "at": it.get("at"),
                        "text": (it["title"] + " — " + it["text"])[:600], "by": "r/" + s,
                        "likes": None, "replies": None, "reposts": None, "views": None})
        time.sleep(2)                               # Reddit answers 429 to a burst
    return out


def _heat(p: dict) -> int:
    return (p.get("likes") or 0) + 2 * (p.get("reposts") or 0) + (p.get("replies") or 0)


def _post_key(p: dict) -> str:
    """One identity per post. The same status was being stored twice, which
    doubled the cards and every like, reply and view total."""
    url = str(p.get("url") or "").split("?")[0].rstrip("/").lower().replace("twitter.com", "x.com")
    found = re.search(r"/status/(\d+)", url)
    if found:
        return str(p.get("channel") or "") + ":" + found.group(1)
    if url:
        return url
    text = re.sub(r"\s+", " ", str(p.get("text") or p.get("source_text") or "")).strip().lower()
    return "text:" + text[:200]


def _unique_posts(posts: list[dict]) -> list[dict]:
    seen: set[str] = set()
    out = []
    for p in posts:
        if not isinstance(p, dict):
            continue
        key = _post_key(p)
        if key in seen:
            continue
        seen.add(key)
        out.append(p)
    return out


def dedupe_saved(tenant: str) -> dict[str, Any]:
    """Drop duplicate posts already stored for each brand."""
    changed = []
    for b in brands(tenant):
        d = _data(tenant, b["id"])
        posts = d.get("posts") or []
        moves = d.get("moves") or []
        unique_posts = _unique_posts(posts)
        unique_moves = _unique_posts(moves)
        if len(unique_posts) == len(posts) and len(unique_moves) == len(moves):
            continue
        d["posts"] = unique_posts
        d["moves"] = unique_moves
        _save_data(tenant, b["id"], d)
        changed.append({"id": b["id"], "posts": [len(posts), len(unique_posts)],
                        "moves": [len(moves), len(unique_moves)]})
    return {"ok": True, "changed": changed}


# ------------------------------------------------------------------- moves

def _moves(tenant: str, name: str, posts: list[dict]) -> list[dict]:
    """One actionable strategy per post that got a response.

    Five fields, each tied to that post. A reward or a participant count is
    written only when the post states it. The like, reply and view counts are
    the measured response, not a signup total.
    """
    from pipeline.gtm_os import agent_runtime as R
    posts = _unique_posts(posts)
    top = sorted([p for p in posts if p["channel"] == "x"], key=_heat, reverse=True)[:6]
    top += [p for p in posts if p["channel"] == "reddit"][:3]
    if not top:
        return []
    prof = Brain(tenant).get_brand_profile() or {}
    company = prof.get("company") or {}
    ours = str(company.get("name") or tenant)
    facts = (prof.get("claims") or {}).get("true_figures") or []
    lines = []
    for i, p in enumerate(top):
        eng = ("no vote counts in Reddit's feed" if p["channel"] == "reddit" else
               f"{p.get('likes') or 0} likes, {p.get('replies') or 0} replies, "
               f"{p.get('reposts') or 0} reposts, {p.get('views') or 0} views")
        lines.append(f"[{i}] {p['channel']} {str(p.get('at'))[:10]} ({eng}): {p['text'][:500]}")
    prompt = (
        "You work for " + ours + ": " + str(company.get("what_it_is") or "") + "\n"
        "Facts you may use about " + ours + " (no other numbers): "
        + json.dumps(facts, ensure_ascii=False)[:1500] + "\n"
        "Pillars: " + json.dumps(prof.get("pillars") or [], ensure_ascii=False)[:800] + "\n\n"
        "Below are " + name + "'s recent posts. The counts in parentheses are the measured "
        "response to that post. They are not a count of campaign participants.\n"
        + "\n".join(lines) + "\n\n"
        "Pick up to 3 posts that got a real response. For each, write one campaign strategy "
        + ours + " could act on. Learn the shape. Do not copy their words, and do not claim "
        "their product is " + ours + "'s.\n"
        "Rules:\n"
        "- did: what the post itself says the project did. One or two sentences.\n"
        "- reward: the reward structure only if that post states one (points, tokens, a role, a fee). "
        "Otherwise exactly: Not stated in the post.\n"
        "- participation: a participant or user count only if that post states one, and say it is from the post. "
        "Otherwise describe the measured response using the exact counts given above, and say it is the response "
        "to the post, not signups.\n"
        "- why: one sentence on why it might have worked, tied to that response or to something the post says. "
        "Use 'might'.\n"
        "- adapt: what " + ours + " could run on its own channels. Use only the facts listed above. "
        "If a number is not in those facts, leave it out.\n"
        'Return JSON: {"moves": [{"post": <index>, "did": str, "reward": str, "participation": str, '
        '"why": str, "adapt": str, "format": str}]}'
    )
    out: dict = {}
    for attempt in range(2):
        try:
            out = R.brain_json(prompt, agent=AGENT, role="reasoning", temperature=0.2, max_output_tokens=8192,
                               system="You turn a competitor post into a strategy. You never invent a reward, "
                                      "a participant count, or a figure about the brand you work for.")
            break
        except Exception as exc:                    # noqa: BLE001 — posts alone are still shown
            if attempt:
                return [{"error": str(exc)[:200]}]
    moves = []
    for m in (out.get("moves") or [])[:3]:
        try:
            p = top[int(m.get("post"))]
        except (TypeError, ValueError, IndexError):
            continue
        did = str(m.get("did") or "")[:500]
        reward = str(m.get("reward") or "Not stated in the post.")[:300]
        participation = str(m.get("participation") or "")[:300]
        why = str(m.get("why") or m.get("what_worked") or "")[:400]
        adapt = str(m.get("adapt") or m.get("vanna_move") or "")[:500]
        moves.append({
            "did": did, "reward": reward, "participation": participation, "why": why, "adapt": adapt,
            "vanna_move": adapt, "what_worked": why,
            "format": str(m.get("format") or "")[:60],
            "channel": p["channel"], "url": p["url"], "source_text": p["text"][:240],
            "at": p.get("at"),
            "likes": p.get("likes"), "replies": p.get("replies"),
            "reposts": p.get("reposts"), "views": p.get("views"),
        })
    return moves


def strategies(tenant: str, bid: str = "") -> dict[str, Any]:
    """Rewrite the strategies from posts already stored. Does not scrape again."""
    ids = [bid] if bid else [b["id"] for b in brands(tenant)]
    done = []
    for i in ids:
        brand = next((b for b in brands(tenant) if b["id"] == i), None)
        if not brand:
            return {"ok": False, "error": "no such brand: " + i}
        d = _data(tenant, i)
        posts = _unique_posts(d.get("posts") or [])
        moves = _moves(tenant, brand["name"], posts)
        if moves and "error" in moves[0]:
            d.setdefault("errors", {})["moves"] = moves[0]["error"]
            moves = []
        elif "errors" in d:
            d["errors"].pop("moves", None)
        d["posts"] = posts
        d["moves"] = moves
        _save_data(tenant, i, d)
        done.append({"id": i, "moves": len(moves)})
    return {"ok": True, "rewritten": done}


# ---------------------------------------------------------------- commands

def _clean_handle(raw: str) -> str:
    """GearboxProtocol from a bare handle, @handle, or an x.com / twitter.com link."""
    s = (raw or "").strip()
    found = re.search(r"(?:https?://)?(?:www\.)?(?:mobile\.)?(?:x|twitter)\.com/([A-Za-z0-9_]{1,30})", s, re.I)
    if found:
        return found.group(1)
    return s.lstrip("@").split("/")[0].split("?")[0].split("#")[0]


def add(tenant: str, name: str, x_handle: str = "", subreddit: str = "") -> dict[str, Any]:
    name = name.strip()
    handle = _clean_handle(x_handle)
    if re.search(r"(?:x|twitter)\.com/", name, re.I):
        found = _clean_handle(name)
        if found:
            name = found
            if not handle:
                handle = found
    if not name:
        return {"ok": False, "error": "a brand needs a name"}
    rows = brands(tenant)
    bid = _slug(name)
    if any(b["id"] == bid for b in rows):
        return {"ok": False, "error": name + " is already added"}
    if not handle:
        from pipeline.brand_brain.analyzer import _lookup
        handle = _lookup(name).get("handle", "")
    rows.append({"id": bid, "name": name, "x_handle": handle,
                 "subreddit": re.sub(r"^/?r/", "", subreddit.strip()), "added_at": _now().isoformat()})
    _save_brands(tenant, rows)
    return {"ok": True, "id": bid, "x_handle": handle}


def remove(tenant: str, bid: str) -> dict[str, Any]:
    rows = [b for b in brands(tenant) if b["id"] != bid]
    _save_brands(tenant, rows)
    b = Brain(tenant)
    for k in ("inspiration:data:", "inspiration:job:"):
        b.meta(k + bid, "")
    b.clear_competitor_patterns(_pattern_key(tenant, bid))
    return {"ok": True, "removed": bid}


def _pattern_key(tenant: str, bid: str) -> str:
    return tenant + ":inspiration:" + bid + ":"


def _worked(log: list, agent: str, status: str, detail: str) -> None:
    from pipeline.gtm_os.agent_runtime import AGENT_NAMES
    log.append({"id": agent, "name": AGENT_NAMES.get(agent, agent),
                "status": status, "detail": detail[:240]})


def _grounded(agent: str, name: str, kind: str) -> tuple[list[dict], str]:
    """Pages a grounded search actually returned. Titles only, no written copy."""
    from pipeline.gtm_os import agent_runtime as R
    if kind == "linkedin":
        ask = ("Find recent public LinkedIn posts or the company LinkedIn page for " + name + ". "
               "Report only pages the search found.")
        channel, by = "linkedin", "LinkedIn"
    else:
        ask = ("Find the official website, documentation, and recent docs or blog pages for " + name + ". "
               "Skip LinkedIn, X, and Reddit. Report only pages the search found.")
        channel, by = "reference", "Docs"
    try:
        _text, sources = R.brain_search(
            ask + ' Then stop.',
            agent=agent,
            system="You look pages up. You do not write a post and you do not invent a URL.",
            role="reasoning", temperature=0.1, max_output_tokens=1024)
    except Exception as exc:                       # noqa: BLE001 — the other channels still show
        return [], str(exc)[:200]
    out, seen = [], set()
    for s in sources:
        url = str(s.get("url") or "")
        title = " ".join(str(s.get("title") or "").split())[:300]
        blob = (url + " " + title).lower()
        if not url.startswith("http"):
            continue
        if channel == "linkedin" and "linkedin" not in blob:
            continue
        if channel == "reference" and any(h in blob for h in ("linkedin", "twitter.com", "x.com", "reddit.com")):
            continue
        key = url.split("?")[0].rstrip("/")
        if key in seen:
            continue
        seen.add(key)
        out.append({"channel": channel, "url": url, "at": None, "text": title or url, "by": by,
                    "likes": None, "replies": None, "reposts": None, "views": None})
        if len(out) >= 5:
            break
    return out, ""


def _pick(posts: list[dict]) -> list[dict]:
    """A few posts from each place, strongest response first."""
    chosen: list[dict] = []
    for channel, n in (("x", 3), ("linkedin", 2), ("reddit", 2), ("reference", 2)):
        group = [p for p in posts if p.get("channel") == channel]
        group.sort(key=_heat, reverse=True)
        chosen.extend(group[:n])
    return _unique_posts(chosen)[:8]


def _numbers_in(text: str) -> list[str]:
    return re.findall(r"\d[\d,.]*%?", text or "")


def _supported(sentence: str, blob: str) -> bool:
    plain = blob.replace(",", "")
    for n in _numbers_in(sentence):
        if n not in blob and n.replace(",", "") not in plain:
            return False
    return True


def _strip_unsupported(text: str, blob: str) -> tuple[str, bool]:
    parts = re.split(r"(?<=[.!?])\s+", (text or "").strip())
    kept, dropped = [], False
    for sentence in parts:
        if sentence and not _supported(sentence, blob):
            dropped = True
            continue
        if sentence:
            kept.append(sentence)
    return " ".join(kept).strip(), dropped


def _ask(agent: str, prompt: str, system: str) -> tuple[Optional[dict], str]:
    from pipeline.gtm_os.agent_runtime import AGENT_ROLES, brain_json
    role = AGENT_ROLES.get(agent) or "reasoning"
    if role == "none":
        role = "reasoning"
    try:
        out = brain_json(prompt, agent=agent, role=role, system=system,
                         temperature=0.2, max_output_tokens=4096)
    except Exception as exc:                       # noqa: BLE001 — the shelf still saves the posts
        return None, str(exc)[:200]
    return (out if isinstance(out, dict) else None), ""


def _study(tenant: str, brand: dict, posts: list[dict]) -> dict[str, Any]:
    """The twelve agents read one added company and write the shelf."""
    name = brand["name"]
    log: list[dict] = []
    errors: dict[str, str] = {}
    extra: list[dict] = []

    linkedin, err = _grounded("A02_market_analyst", name, "linkedin")
    if err:
        errors["linkedin"] = err
    references, err = _grounded("A02_market_analyst", name, "reference")
    if err:
        errors["references"] = err
    extra = linkedin + references
    scout_detail = (str(sum(1 for p in posts if p.get("channel") == "x")) + " posts on X, "
                    + str(sum(1 for p in posts if p.get("channel") == "reddit")) + " Reddit threads, "
                    + str(len(linkedin)) + " LinkedIn pages, "
                    + str(len(references)) + " docs or site pages")
    _worked(log, "A01_intelligence_scout", "ok" if (posts or extra) else "degraded", scout_detail)

    picked = _pick(_unique_posts(posts + extra))
    _worked(log, "A02_opportunity_selector", "ok" if picked else "degraded",
            "Kept " + str(len(picked)) + " items that can teach a shape" if picked else "Nothing to keep")
    if not picked:
        for agent, detail in (
            ("A02_market_analyst", "No posts to read"),
            ("A03_gtm_strategist", "No subject to plan"),
            ("A06_channel_adapter", "No lines to write"),
            ("A07_creative_director", "No posts to shape"),
            ("A08_visual_synthesis", "No source image on this shelf"),
            ("A09_video_production", "No video is rendered for this shelf"),
            ("A15_creative_judge", "Nothing to judge"),
            ("A10_reviewer_firewall", "Nothing to check"),
            ("A13_learning_engine", "Stored the company with no posts yet"),
        ):
            _worked(log, agent, "degraded", detail)
        remembered = _remember(tenant, brand, [])
        _worked(log, "A11_delivery", "ok", "Company stored. The shelf is waiting on posts.")
        return {"extra_posts": extra, "moves": [], "agents": log, "errors": errors, "brain": remembered}

    prof = Brain(tenant).get_brand_profile() or {}
    company = prof.get("company") or {}
    ours = str(company.get("name") or tenant)
    facts = (prof.get("claims") or {}).get("true_figures") or []
    fact_blob = json.dumps(facts, ensure_ascii=False)[:1500]
    lines = []
    for i, p in enumerate(picked):
        eng = ("no public counts" if p.get("likes") is None else
               f"{p.get('likes') or 0} likes, {p.get('replies') or 0} replies, "
               f"{p.get('reposts') or 0} reposts, {p.get('views') or 0} views")
        lines.append(f"[{i}] {p['channel']} ({eng}) {p.get('url')}: {p['text'][:400]}")
    packet = "\n".join(lines)
    shelf = ("This is the What Vanna Can Do shelf for " + ours + ", not a post to publish. "
             "A number is allowed only when it appears in the item or in the facts. "
             "Do not copy " + name + "'s sentences. Do not say their product is " + ours + "'s.")

    reads, err = _ask(
        "A02_market_analyst",
        shelf + "\nFacts about " + ours + ": " + fact_blob + "\n\nItems:\n" + packet
        + "\n\nFor each item write one plain sentence on what that post or page is doing. "
        + 'Return JSON: {"reads": [{"post": <index>, "doing": str}]}',
        "You say what a post is doing. You add no new fact.")
    if err:
        errors["analyst"] = err
    doing = {}
    for row in (reads or {}).get("reads") or []:
        if isinstance(row, dict):
            doing[row.get("post")] = str(row.get("doing") or "")[:400]
    _worked(log, "A02_market_analyst", "ok" if doing else "degraded",
            "Read " + str(len(doing)) + " items" if doing else (err or "No reading came back"))

    plans, err = _ask(
        "A03_gtm_strategist",
        shelf + "\nWhat " + ours + " is: " + str(company.get("what_it_is") or "")
        + "\nFacts: " + fact_blob + "\n\nItems:\n" + packet
        + "\nWhat each item is doing:\n" + json.dumps(doing, ensure_ascii=False)[:2000]
        + "\n\nFor each item, say what " + ours + " can do on its own channels, and how, "
        + "in two or three short steps a person could follow. Use only the facts above. "
        + 'Return JSON: {"plans": [{"post": <index>, "can": str, "how": str}]}',
        "You plan what this company can do. You do not invent a figure or a feature.")
    if err:
        errors["strategist"] = err
    planned = {}
    for row in (plans or {}).get("plans") or []:
        if isinstance(row, dict):
            planned[row.get("post")] = row
    _worked(log, "A03_gtm_strategist", "ok" if planned else "degraded",
            "Planned " + str(len(planned)) + " moves" if planned else (err or "No plan came back"))

    shapes, err = _ask(
        "A07_creative_director",
        "Look at the shape only. Do not write a new post and do not describe a new picture.\n"
        + packet + '\nReturn JSON: {"shapes": [{"post": <index>, "format": str}]} '
        + "format is a few words: question or statement, short or long, image or text.",
        "You name the shape of a post. You do not design a new one.")
    shaped = {}
    for row in (shapes or {}).get("shapes") or []:
        if isinstance(row, dict):
            shaped[row.get("post")] = str(row.get("format") or "")[:80]
    _worked(log, "A07_creative_director", "ok" if shaped else "degraded",
            "Named the shape of " + str(len(shaped)) + " items" if shaped else (err or "No shape came back"))

    written, err = _ask(
        "A06_channel_adapter",
        shelf + "\n\nItems:\n" + packet
        + "\nDoing:\n" + json.dumps(doing, ensure_ascii=False)[:2000]
        + "\nPlan:\n" + json.dumps(planned, ensure_ascii=False)[:2500]
        + "\n\nWrite the shelf copy for each item. Short lines a person can read. "
        + "this_post: what their post is doing. vanna_can: what " + ours + " can do. "
        + "how: how, as two or three short steps. No spec language. No number that is not already above. "
        + 'Return JSON: {"lines": [{"post": <index>, "this_post": str, "vanna_can": str, "how": str}]}',
        "You write the shelf in plain words. Output only JSON.")
    if err:
        errors["copy"] = err
    lines_by = {}
    for row in (written or {}).get("lines") or []:
        if isinstance(row, dict):
            lines_by[row.get("post")] = row
    _worked(log, "A06_channel_adapter", "ok" if lines_by else "degraded",
            "Wrote " + str(len(lines_by)) + " shelf notes" if lines_by else (err or "No copy came back"))

    moves = []
    stripped = 0
    for i, p in enumerate(picked):
        row = lines_by.get(i) or {}
        plan = planned.get(i) or {}
        this_post = str(row.get("this_post") or doing.get(i) or "")[:500]
        vanna_can = str(row.get("vanna_can") or plan.get("can") or "")[:500]
        how = str(row.get("how") or plan.get("how") or "")[:500]
        blob = (p.get("text") or "") + "\n" + fact_blob
        this_post, d1 = _strip_unsupported(this_post, blob)
        vanna_can, d2 = _strip_unsupported(vanna_can, blob)
        how, d3 = _strip_unsupported(how, blob)
        stripped += int(d1 or d2 or d3)
        if not (this_post or vanna_can or how):
            continue
        eng = ""
        if p.get("likes") is not None:
            eng = (str(p.get("likes") or 0) + " likes, " + str(p.get("replies") or 0) + " replies, "
                   + str(p.get("views") or 0) + " views on the source")
        moves.append({
            "did": this_post, "this_post": this_post,
            "reward": "Not stated in the post.",
            "participation": eng or "No public counts on this source.",
            "why": how, "adapt": vanna_can, "vanna_can": vanna_can, "how": how,
            "vanna_move": vanna_can, "what_worked": how,
            "format": shaped.get(i) or "",
            "index": i,
            "channel": p.get("channel"), "url": p.get("url"), "source_text": (p.get("text") or "")[:240],
            "at": p.get("at"),
            "likes": p.get("likes"), "replies": p.get("replies"),
            "reposts": p.get("reposts"), "views": p.get("views"),
        })
    weak = [m for m in moves if len((m.get("how") or "").split()) < 8 or len((m.get("this_post") or "").split()) > 40]
    _worked(log, "A15_creative_judge", "ok" if moves and not weak else "degraded",
            "Clear enough to show" if moves and not weak else
            (str(len(weak)) + " notes were thin or too long" if moves else "No notes to judge"))
    if weak and moves:
        fixed, err = _ask(
            "A06_channel_adapter",
            shelf + "\nRewrite these notes. this_post under 30 words. how is two or three short steps.\n"
            + json.dumps([{k: m.get(k) for k in ("this_post", "vanna_can", "how", "source_text")} for m in weak],
                         ensure_ascii=False)[:3000]
            + '\nReturn JSON: {"lines": [{"post": <index in this list>, "this_post": str, "vanna_can": str, "how": str}]}',
            "You shorten a shelf note. You add no fact.")
        if not err:
            for row in (fixed or {}).get("lines") or []:
                if not isinstance(row, dict):
                    continue
                try:
                    target = weak[int(row.get("post"))]
                except (TypeError, ValueError, IndexError):
                    continue
                blob = (target.get("source_text") or "") + "\n" + fact_blob
                for src, dest in (("this_post", "this_post"), ("vanna_can", "vanna_can"), ("how", "how")):
                    clean, _drop = _strip_unsupported(str(row.get(src) or ""), blob)
                    if clean:
                        target[dest] = clean
                target["did"] = target.get("this_post") or target.get("did")
                target["adapt"] = target.get("vanna_can") or target.get("adapt")
                target["why"] = target.get("how") or target.get("why")

    made, err = _ask(
        "A07_creative_director",
        "For each item, say what " + ours + " would make from it. This is a plan, not a finished file. "
        "post: two or three short lines they could publish. visual: one sentence on what the poster shows. "
        "video: one sentence on what a short video would show. Use no number that is not in the item.\n"
        + json.dumps([{"post": m.get("index"), "source": m.get("source_text"), "can": m.get("vanna_can")}
                      for m in moves], ensure_ascii=False)[:3500]
        + '\nReturn JSON: {"makes": [{"post": <index>, "copy": str, "visual": str, "video": str}]}',
        "You plan a post, a poster, and a short video. You do not render them.")
    makes = {}
    for row in (made or {}).get("makes") or []:
        if isinstance(row, dict):
            makes[row.get("post")] = row
    for m in moves:
        row = makes.get(m.get("index")) or {}
        blob = (m.get("source_text") or "") + "\n" + fact_blob
        for src, dest in (("copy", "post_line"), ("visual", "visual"), ("video", "video")):
            clean, drop = _strip_unsupported(str(row.get(src) or "")[:400], blob)
            stripped += int(drop)
            if clean:
                m[dest] = clean
    _worked(log, "A08_visual_synthesis", "ok",
            "Planned the poster for " + str(sum(1 for m in moves if m.get("visual"))) + " items. No image was rendered.")
    _worked(log, "A09_video_production", "ok",
            "Planned the video for " + str(sum(1 for m in moves if m.get("video"))) + " items. No video was rendered.")
    if err:
        errors["creative"] = err

    _worked(log, "A10_reviewer_firewall", "ok" if not stripped else "degraded",
            "Every number in the notes is in the source or the facts" if not stripped else
            "Removed " + str(stripped) + " sentences that carried a number the source did not state")
    remembered = _remember(tenant, brand, _unique_posts(posts + extra))
    _worked(log, "A13_learning_engine", "ok" if remembered.get("ok") else "degraded",
            remembered.get("detail") or "Stored")
    _worked(log, "A11_delivery", "ok",
            "Wrote " + str(len(moves)) + " notes onto What Vanna Can Do for " + name)
    return {"extra_posts": extra, "moves": moves, "agents": log, "errors": errors, "brain": remembered}


def _remember(tenant: str, brand: dict, posts: list[dict]) -> dict[str, Any]:
    """Store the company in the brain: a page, and a shape note with no copied words."""
    from pipeline.brand_brain.chunking import Chunk
    name = brand["name"]
    bid = brand["id"]
    counts: dict[str, int] = {}
    words = []
    questions = 0
    for p in posts:
        counts[p.get("channel") or "?"] = counts.get(p.get("channel") or "?", 0) + 1
        text = str(p.get("text") or "")
        words.append(len(text.split()))
        if "?" in text[:80]:
            questions += 1
    median = sorted(words)[len(words) // 2] if words else 0
    pattern = (name + " was added on What Vanna Can Do. "
               + "In the last " + str(WINDOW_DAYS) + " days the shelf saw "
               + ", ".join(k + " " + str(v) for k, v in sorted(counts.items()))
               + ". Median length about " + str(median) + " words. "
               + str(questions) + " of the items open with a question. "
               + "Learn that shortness. Do not copy their words, names, or numbers.")
    try:
        brain = Brain(tenant)
        key = _pattern_key(tenant, bid)
        brain.clear_competitor_patterns(key)
        brain.set_competitor_pattern(
            key + "0", competitor=name, topic="x linkedin reddit docs",
            pattern=pattern, evidence_n=len(posts))
        page = Chunk(
            text=(name + " is an outside brand stored for What Vanna Can Do. "
                  + ("X @" + brand["x_handle"] + ". " if brand.get("x_handle") else "")
                  + str(len(posts)) + " public items were read. "
                  + "This page is not a fact about the company that owns this brain."),
            title=name + " inspiration",
            section="outside brand",
            content_type="blog",
            prefix="Inspiration",
        )
        brain.upsert_page("inspiration-" + bid, [page], source="public", authority=5)
    except Exception as exc:                       # noqa: BLE001 — the shelf can still show the posts
        return {"ok": False, "detail": "Could not store in the brain: " + str(exc)[:160]}
    return {"ok": True, "detail": "Stored " + name + " in the brand brain, with the shape of what was found"}


def organise_from_watch(tenant: str = "vanna") -> dict[str, Any]:
    """The accounts the scout already watches become What Vanna Can Do cards.

    One card is refreshed per scrape, the one that is oldest, so a short
    timer does not refetch every brand every time.
    """
    from datetime import timedelta
    from pipeline.intelligence_stream.source_config import load
    added: list[str] = []
    for account in load().get("x_accounts") or []:
        if not isinstance(account, dict):
            continue
        name = str(account.get("name") or "").strip()
        handle = str(account.get("handle") or "").strip()
        if not name:
            continue
        made = add(tenant, name, handle)
        if made.get("ok"):
            added.append(str(made.get("id") or name))
    known = brands(tenant)
    if any((job(tenant, b["id"]) or {}).get("state") == "running" for b in known):
        return {"ok": True, "added": added, "refreshing": ""}
    cutoff = (_now() - timedelta(minutes=30)).isoformat()
    waiting = []
    for brand in known:
        fetched = str((_data(tenant, brand["id"]) or {}).get("fetched_at") or "")
        if fetched and fetched > cutoff:
            continue
        waiting.append((fetched, brand["id"]))
    waiting.sort()
    started = ""
    if waiting:
        started = waiting[0][1]
        _job(tenant, started, "running")
        import os
        import subprocess
        from pathlib import Path
        root = str(Path(__file__).resolve().parents[2])
        exe = sys.executable
        if os.name == "nt" and exe.lower().endswith("python.exe"):
            windowless = exe[: -len("python.exe")] + "pythonw.exe"
            if os.path.isfile(windowless):
                exe = windowless
        subprocess.Popen(
            [exe, "-m", "pipeline.brand_brain.inspiration", "refresh", tenant, started],
            cwd=root,
            env={**os.environ, "PYTHONPATH": root},
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            creationflags=0x08000000 if os.name == "nt" else 0,
            start_new_session=os.name != "nt",
        )
    return {"ok": True, "added": added, "refreshing": started}


def refresh(tenant: str, bid: str) -> dict[str, Any]:
    brand = next((b for b in brands(tenant) if b["id"] == bid), None)
    if not brand:
        return {"ok": False, "error": "no such brand: " + bid}
    _job(tenant, bid, "running")
    errors: dict[str, str] = {}
    posts: list[dict] = []
    if brand.get("x_handle"):
        try:
            posts += _x(brand["x_handle"])
        except Exception as exc:                    # noqa: BLE001 — Reddit may still work
            errors["x"] = str(exc)[:200]
    else:
        errors["x"] = "no X handle found; add one"
    try:
        posts += _reddit(brand["name"], brand.get("subreddit") or "")
    except Exception as exc:                        # noqa: BLE001 — X may still work
        errors["reddit"] = str(exc)[:200]
    study = _study(tenant, brand, posts)
    posts = _unique_posts(posts + (study.get("extra_posts") or []))
    moves = study.get("moves") or []
    errors.update(study.get("errors") or {})
    _save_data(tenant, bid, {
        "fetched_at": _now().isoformat(), "posts": posts, "moves": moves, "errors": errors,
        "agents": study.get("agents") or [], "brain": study.get("brain") or {},
    })
    _job(tenant, bid, "done", posts=len(posts), moves=len(moves))
    return {"ok": True, "id": bid, "posts": len(posts), "moves": len(moves), "errors": errors}


def _channel(posts: list[dict], label: str, counted: bool) -> dict[str, Any]:
    s = lambda k: sum(p.get(k) or 0 for p in posts) if counted else None  # noqa: E731
    return {"label": label, "posts": len(posts), "likes": s("likes"), "comments": s("replies"),
            "reposts": s("reposts"), "views": s("views"), "counted": counted}


def report(tenant: str) -> list[dict[str, Any]]:
    """Every added brand, as the What Vanna Can Do section shows it."""
    out = []
    for b in brands(tenant):
        d = _data(tenant, b["id"])
        posts = _unique_posts(d.get("posts") or [])
        x = [p for p in posts if p["channel"] == "x"]
        li = [p for p in posts if p["channel"] == "linkedin"]
        rd = [p for p in posts if p["channel"] == "reddit"]
        rf = [p for p in posts if p["channel"] == "reference"]
        channels = {
            "twitter": _channel(x, "Twitter / X", True),
            "linkedin": _channel(li, "LinkedIn", False),
            "reddit": _channel(rd, "Reddit", False),
            "references": _channel(rf, "Docs and references", False),
        }
        best = max(x, key=_heat) if x else None
        summary = ""
        if posts or d.get("brain"):
            summary = (b["name"] + " is stored in the brand brain. "
                       + "The shelf is showing " + str(len(x)) + " X posts, "
                       + str(len(li)) + " LinkedIn pages, " + str(len(rd)) + " Reddit threads, and "
                       + str(len(rf)) + " docs or site pages from the last " + str(WINDOW_DAYS) + " days.")
            if best:
                summary += (" The strongest X post drew " + str(best.get("likes") or 0) + " likes and "
                            + str(best.get("views") or 0) + " views.")
        out.append({
            "id": b["id"], "name": b["name"], "handle": "@" + b["x_handle"] if b.get("x_handle") else "",
            "subreddit": b.get("subreddit") or "", "added_at": b.get("added_at"),
            "fetched_at": d.get("fetched_at"), "job": job(tenant, b["id"]), "errors": d.get("errors") or {},
            "window_days": WINDOW_DAYS, "channels": channels, "hype_origin": summary,
            "top_posts": (sorted(x, key=_heat, reverse=True)[:6] + li[:4] + rd[:4] + rf[:4]),
            "vanna_moves": d.get("moves") or [],
            "agents": d.get("agents") or [],
            "brain": d.get("brain") or {},
        })
    return out


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Brands Vanna takes inspiration from")
    ap.add_argument("cmd", choices=["list", "add", "refresh", "remove", "strategies"])
    ap.add_argument("tenant", nargs="?")
    ap.add_argument("arg", nargs="?", help="brand name (add) or brand id (refresh, remove)")
    ap.add_argument("--x", default="")
    ap.add_argument("--subreddit", default="")
    ap.add_argument("--no-fetch", action="store_true", help="add without fetching the posts")
    a = ap.parse_args(argv)
    tenant = a.tenant or current_tenant()
    if a.cmd == "list":
        from pipeline.brand_brain import store as S
        prof = Brain(tenant).get_brand_profile()
        out: Any = {"ok": True, "tenant": tenant, "tenants": S.tenants(),
                    "company": ((prof.get("company") or {}).get("name") or tenant),
                    "brands": report(tenant)}
    elif a.cmd == "add":
        out = add(tenant, a.arg or "", a.x, a.subreddit)
        if out.get("ok") and not a.no_fetch:
            out["fetch"] = refresh(tenant, out["id"])
    elif a.cmd == "refresh":
        try:
            out = refresh(tenant, a.arg or "")
        except Exception as exc:                    # noqa: BLE001 — the job must not stay "running"
            _job(tenant, a.arg or "", "failed", error=str(exc)[:200])
            raise
    elif a.cmd == "strategies":
        out = strategies(tenant, a.arg or "")
    else:
        out = remove(tenant, a.arg or "")
    sys.stdout.write(json.dumps(out, ensure_ascii=False, default=str))
    return 0 if out.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
