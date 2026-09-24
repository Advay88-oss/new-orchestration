"""Vanna's own knowledge, wide enough to write from.

The agents were working from `pipeline/brain/knowledge/approved-claims.md`:
six claims and three pillars. That is why every visual came back about the
same two or three features — the SmartAccount sandbox, the 320ms Mercury
stream, the 10x leverage — and why a campaign about anything else had nothing
concrete to hold on to.

`docs.vanna.finance` publishes an `llms.txt` index and serves all 75 pages as
markdown. This module reads both sources and caches the docs under
`pipeline/brain/docs/`, so an agent asking "what does Vanna actually do here"
gets the mechanism pages rather than a six-line registry.

Two things it also provides, because the founder asked for them explicitly:

  `VISUAL_ANCHORS`  the concrete, recurring subject matter every generated
                    image and video must be built from — Soroban testnet,
                    Blend, the health-factor floor. Without these the art
                    director produced beautiful abstract glassware that could
                    have advertised a watch.

  `prohibited()`    what may never be said or shown. Kept separate from the
                    positive claims so it can be appended to every creative
                    prompt, not just the copy ones.
"""
from __future__ import annotations

import json
import re
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
BRAIN = REPO_ROOT / "pipeline" / "brain"
KNOWLEDGE_DIR = BRAIN / "knowledge"
DOCS_CACHE = BRAIN / "docs"
DOCS_STAMP = DOCS_CACHE / ".fetched"

INDEX_URL = "https://docs.vanna.finance/llms.txt"
DOCS_HOST = "docs.vanna.finance"
# The marketing site is a vision site, not a claim source. Never fetch it.
FORBIDDEN_HOSTS = ("vanna.finance", "www.vanna.finance")

USER_AGENT = "vanna-gtm-pipeline/1.0 (+internal research)"
MAX_AGE_S = 86_400
_MD_LINK = re.compile(r"https://docs\.vanna\.finance/[A-Za-z0-9/_\-.]+\.md")

# Pages that describe mechanism rather than click-here walkthroughs. These are
# where the checkable substance lives.
MECHANISM_PREFIXES = (
    "/learn/",
    "/developers/",
    "/guides/margin/",
    "/guides/how-vanna-works",
    "/guides/earn/",
    "/guides/for-",
)

# --------------------------------------------------------------------------
# The concrete world every asset must be built from
# --------------------------------------------------------------------------

VISUAL_ANCHORS: dict[str, str] = {
    "chain": "Stellar Soroban (TESTNET — never depict or imply mainnet)",
    "account": "SmartAccount — a per-borrower contract instance with its own "
               "isolated storage, drawn as a discrete sealed unit, never a "
               "shared pool",
    "venues": "Blend (b-tokens) and Aquarius (LP shares) — the external DeFi "
              "venues Vanna deploys credit into",
    "risk": "Health factor with a 1.10x liquidation floor and a 1.25x "
            "defensive-rebalance trigger",
    "telemetry": "Mercury event streaming, sub-second (~320ms)",
    "fees": "Fixed micro-gas at 0.00014 XLM, no priority-fee auction",
}

# The confirmed integration list, from the founder's Notion context pack
# (see pipeline/brain/knowledge/notion-ground-truth.md). It is a constant
# rather than prose because it is enforceable: a post claiming a relationship
# with anything not on this list is fabricating one. Older Vanna documents
# name protocols and chains beyond these; the confirmed list wins.
PARTNERS: dict[str, str] = {
    "Stellar": "chain — current deployment",
    "Soroswap": "spot / AMM (Stellar)",
    "Aquarius": "spot / AMM (Stellar)",
    "Blend": "lending (Stellar)",
    "Hyperliquid": "perps",
    "Aster": "perps",
    "Avantis": "perps",
    "Derive": "options (via Optimism)",
    "Optimism": "chain — accessed via Derive",
    "Uniswap": "spot / AMM",
    "Aerodrome": "spot / AMM",
    "Morpho": "lending",
    "Katana": "yield",
    "Privy": "wallet / auth infrastructure",
    "ZeroDev": "account abstraction infrastructure",
    "Draper University": "backer",
    "Pivot Ventures": "backer",
    "Gitcoin": "backer / ecosystem",
}


def is_partner(name: str) -> bool:
    """Whether a named entity is a confirmed Vanna partner."""
    n = " ".join(str(name or "").lower().split())
    return any(n == k.lower() for k in PARTNERS)


# Text that must never appear in or be implied by an image.
PROHIBITED_VISUAL = (
    "ANY cryptocurrency glyph, symbol or coin — no Bitcoin B, no Ethereum "
    "diamond, no XLM or Stellar logo, no generic coin or token prop of any "
    "metal or colour, no vaults or safes holding coins. Vanna is credit "
    "infrastructure, not a currency, and a coin in frame advertises the wrong "
    "product. Also never: mainnet or live-trading cues, token price, ticker "
    "symbols, candlestick charts, price arrows, lambos, rockets, moons, bulls "
    "or bears, neon cyberpunk grids, hooded hackers, stock-photo handshakes, "
    "any competitor logo, and any rendered text, formula, label or numeral"
)


class KnowledgeError(RuntimeError):
    pass


def _get(url: str, timeout: float = 25.0) -> str:
    host = urllib.parse.urlparse(url).netloc.lower() if hasattr(urllib, "parse") else ""
    import urllib.parse as up
    host = up.urlparse(url).netloc.lower()
    if host in FORBIDDEN_HOSTS:
        raise KnowledgeError(host + " is a vision site, not a claim source")
    if host != DOCS_HOST:
        raise KnowledgeError("refusing to fetch " + host)
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "replace")


def _cache_name(url: str) -> str:
    return url.replace("https://" + DOCS_HOST + "/", "").replace("/", "__")


def refresh_docs(max_pages: int = 40, workers: int = 6) -> dict[str, Any]:
    """Fetch the documentation into the local cache."""
    DOCS_CACHE.mkdir(parents=True, exist_ok=True)
    try:
        pages = list(dict.fromkeys(_MD_LINK.findall(_get(INDEX_URL))))
    except Exception as exc:                        # noqa: BLE001 — boundary
        return {"ok": False, "error": str(exc)[:200], "pages": 0}

    targets = [p for p in pages
               if any(p.replace("https://" + DOCS_HOST, "").startswith(pref)
                      for pref in MECHANISM_PREFIXES)] or pages
    targets = targets[:max_pages]

    def one(url: str) -> bool:
        try:
            body = _get(url)
        except Exception:                           # noqa: BLE001 — boundary
            return False
        (DOCS_CACHE / _cache_name(url)).write_text(body, encoding="utf-8")
        return True

    with ThreadPoolExecutor(max_workers=workers) as pool:
        got = sum(1 for ok in pool.map(one, targets) if ok)

    DOCS_STAMP.write_text(str(time.time()), encoding="utf-8")
    return {"ok": got > 0, "pages": got, "listed": len(pages)}


def refresh_if_stale(max_age_s: int = MAX_AGE_S) -> dict[str, Any]:
    """Refetch once a day. Documentation moves on a release cadence, not a
    per-run one, and paying 40 HTTP round trips every cycle buys nothing."""
    try:
        age = time.time() - DOCS_STAMP.stat().st_mtime
        if age < max_age_s:
            return {"ok": True, "cached": True, "age_h": int(age / 3600)}
    except FileNotFoundError:
        pass
    return refresh_docs()


_HEADING = re.compile(r"^#{1,3}\s+(.+)$", re.M)
_LEAD = re.compile(r"^>\s*##\s*Documentation Index.*?(?=^#)", re.S | re.M)


def docs_excerpts(topic: str, limit: int = 8, chars: int = 900) -> list[dict[str, str]]:
    """Return the cached documentation sections most relevant to a topic.

    Deliberately keyword-scored rather than embedded: the corpus is 40 pages,
    the agent re-reads it every run, and an embedding index would be another
    thing to keep in sync for no measurable gain at this size.
    """
    if not DOCS_CACHE.exists():
        return []
    terms = [w for w in re.findall(r"[a-z]{4,}", topic.lower())][:12]
    scored: list[tuple[int, dict[str, str]]] = []

    for f in sorted(DOCS_CACHE.glob("*.md")):
        try:
            body = _LEAD.sub("", f.read_text(encoding="utf-8", errors="replace"))
        except Exception:                           # noqa: BLE001 — boundary
            continue
        page = f.stem.replace("__", "/")
        # split on headings so an excerpt is a coherent section
        parts = re.split(r"\n(?=#{1,3}\s)", body)
        for part in parts:
            text = re.sub(r"\s+", " ", part).strip()
            if len(text) < 180:
                continue
            low = text.lower()
            score = sum(low.count(t) for t in terms)
            if score <= 0:
                continue
            m = _HEADING.search(part)
            scored.append((score, {
                "page": page,
                "section": (m.group(1).strip() if m else page)[:120],
                "text": text[:chars],
            }))

    scored.sort(key=lambda x: -x[0])
    out, seen = [], set()
    for _, row in scored:
        key = row["section"].lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(row)
        if len(out) >= limit:
            break
    return out


def local_knowledge() -> dict[str, Any]:
    """The committed knowledge pack under pipeline/brain/knowledge."""
    out: dict[str, Any] = {}
    for f in sorted(KNOWLEDGE_DIR.glob("*.md")):
        try:
            out[f.stem] = f.read_text(encoding="utf-8", errors="replace")
        except Exception:                           # noqa: BLE001 — boundary
            continue
    return out


def prohibited() -> list[str]:
    """Claims that may never be made, from the registry."""
    doc = local_knowledge().get("approved-claims", "")
    out = []
    block = re.search(r"(?is)prohibited.*?$", doc)
    if block:
        for line in block.group(0).splitlines():
            s = line.strip().lstrip("-*").strip()
            if len(s) > 12 and not s.startswith("#") and "|" not in s:
                out.append(s[:200])
    return out[:12]


def knowledge_pack(topic: str, *, excerpts: int = 8) -> dict[str, Any]:
    """Everything an agent should know about Vanna before writing about `topic`.

    Wider than the six-claim registry the agents used to receive: the mechanism
    documentation is included so a campaign about liquidations can cite how
    liquidation actually works rather than repeating the same three headline
    features every time.
    """
    refresh_if_stale()
    local = local_knowledge()
    return {
        "anchors": VISUAL_ANCHORS,
        "positioning": local.get("positioning", "")[:2500],
        "approved_claims": local.get("approved-claims", "")[:2500],
        "audience": local.get("audience", "")[:2000],
        "objections": local.get("customer-objections", "")[:2000],
        "ground_truth": local.get("notion-ground-truth", "")[:3500],
        "category_patterns": local.get("category-patterns", "")[:2500],
        "partners": PARTNERS,
        "docs": docs_excerpts(topic, limit=excerpts),
        "prohibited_claims": prohibited(),
        "prohibited_visual": PROHIBITED_VISUAL,
    }


def prompt_block(topic: str, *, excerpts: int = 8) -> str:
    """The knowledge pack rendered for a prompt."""
    k = knowledge_pack(topic, excerpts=excerpts)
    lines = ["VANNA — GROUND TRUTH", "",
             "Product anchors (use these, they are what Vanna concretely is):"]
    for key, val in k["anchors"].items():
        lines.append("  - " + key + ": " + val)

    if k["docs"]:
        lines += ["", "From docs.vanna.finance (" + str(len(k["docs"])) + " sections):"]
        for d in k["docs"]:
            lines.append("  [" + d["page"] + " — " + d["section"] + "]")
            lines.append("    " + d["text"][:700])

    lines += ["", "Positioning:", k["positioning"][:1200]]
    lines += ["", "Approved claims registry:", k["approved_claims"][:1200]]

    if k.get("partners"):
        lines += ["",
                  "CONFIRMED PARTNERS — this is the whole list. Never claim a "
                  "relationship with anything not on it, however plausible it "
                  "sounds:"]
        lines += ["  - " + n + " (" + role + ")"
                  for n, role in k["partners"].items()]

    if k.get("ground_truth"):
        lines += ["", "Ground truth (founder's context pack):",
                  k["ground_truth"][:2200]]
    if k["prohibited_claims"]:
        lines += ["", "NEVER CLAIM:"] + ["  - " + p for p in k["prohibited_claims"]]
    return "\n".join(lines)


if __name__ == "__main__":
    print(json.dumps(refresh_docs(), indent=2))
    print()
    print(prompt_block("liquidation health factor margin")[:2500])
