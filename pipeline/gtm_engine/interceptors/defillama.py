"""
DefiLlama code-first integration for GTM Intelligence Engine.
Deterministic before probabilistic: all numbers and product sets enter the registry
from code, and the model never touches them.
Base API: https://api.llama.fi (Free endpoints only. No Pro API, no MCP).
"""

import os
import sys
import re
import json
import time
import urllib.request
import urllib.error
import urllib.parse
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional, Set, Tuple
import logging

logger = logging.getLogger("gtm_engine.defillama")

BASE = "https://api.llama.fi"
SNAPSHOT_TTL_DAYS = 30          # matches Phase 1 cadence tier
RATE_LIMIT_RPM = 60             # free tier is 10-200; stay conservative
SNAPSHOT_FILE = Path("D:/new orchestration/pipeline/gtm_engine/registry/defillama_snapshot.json")
FEES_SNAPSHOT_FILE = Path("D:/new orchestration/pipeline/gtm_engine/registry/defillama_fees_snapshot.json")
SNAPSHOTS_DIR = Path("D:/new orchestration/pipeline/gtm_engine/registry/snapshots")

# -----------------------------------------------------------------------------
# Category Enum Mapping Table (from the 101 categories discovered in Step 0)
# -----------------------------------------------------------------------------

DEFILLAMA_CATEGORY_TO_ENUM = {
    # Subject's Own Category - Kept strictly distinct (NOT collapsed to LENDING)
    "Uncollateralized Lending": "UNCOLLATERALIZED_LENDING",
    
    # Core Lending
    "Lending": "LENDING",
    "Risk Curators": "LENDING",  # Gauntlet, Steakhouse, Sentora ($9.56B) - Morpho vault risk curators
    "NFT Lending": "LENDING",
    "Collateral Markets": "LENDING",
    "Secondary Debt Markets": "LENDING",
    
    # Spot AMM / DEX
    "Dexs": "SPOT_AMM_DEX",
    "DEX Aggregator": "DEX_AGGREGATOR",
    
    # Perpetuals / Derivatives (DefiLlama has no 'Perpetuals' label; 'Derivatives' is Perps)
    "Derivatives": "PERPETUALS",
    
    # Options & Interest Rate Derivatives
    "Options": "OPTIONS_DERIVATIVES",
    "Options Vault": "OPTIONS_DERIVATIVES",
    "Exotic Options": "OPTIONS_DERIVATIVES",
    "Interest Rate Derivatives": "OPTIONS_DERIVATIVES",
    
    # Staking
    "Liquid Staking": "LIQUID_STAKING",
    "Staking Pool": "LIQUID_STAKING",
    "Restaking": "RESTAKING",
    "Liquid Restaking": "RESTAKING",
    
    # BTCFi (Babylon, Lombard, etc.)
    "Anchor BTC": "BTCFI",
    "Decentralized BTC": "BTCFI",
    "Restaked BTC": "BTCFI",
    
    # Yield & Yield Trading
    "Yield": "YIELD",
    "Yield Aggregator": "YIELD",
    "Farm": "YIELD",
    "Leveraged Farming": "YIELD",
    "Yield Lottery": "YIELD",
    "ve-Incentive Automator": "YIELD",
    "Liquidity Manager": "YIELD",
    "Liquidity Automation": "YIELD",
    
    # Stablecoins & Synthetic Dollars (Ethena is 'Synthetics')
    "Synthetics": "SYNTHETIC_DOLLAR",
    "Stablecoins": "STABLECOINS",
    "Stablecoin Issuer": "STABLECOINS",
    "Stablecoin Wrapper": "STABLECOINS",
    "Algo-Stables": "STABLECOINS",
    "Dual-Token Stablecoin": "STABLECOINS",
    "Partially Algorithmic Stablecoin": "STABLECOINS",
    "Reserve Currency": "STABLECOINS",
    
    # Bridges / Cross Chain
    "Bridge": "BRIDGES",
    "Bridge Aggregator": "BRIDGES",
    "Bridge Aggregators": "BRIDGES",
    "Canonical Bridge": "BRIDGES",
    "Cross Chain Bridge": "CROSS_CHAIN",
    
    # RWA
    "RWA": "RWA",
    "RWA Lending": "RWA_LENDING",
    
    # Trading / Arbitrage
    "Basis Trading": "BASIS_TRADING",
    "Prediction Market": "PREDICTION_MARKETS",
    
    # Asset Management
    "Asset Management": "ASSET_MANAGEMENT",
    "Onchain Capital Allocator": "ASSET_MANAGEMENT",
    "Treasury Manager": "ASSET_MANAGEMENT",
    "Indexes": "ASSET_MANAGEMENT",
    "Portfolio Tracker": "ASSET_MANAGEMENT",
    
    # MEV / Block Building (Jito)
    "MEV": "MEV_BLOCK_BUILDING",
    "Block Builders": "MEV_BLOCK_BUILDING",
    
    # CDP
    "CDP": "CDP",
    "CDP Manager": "CDP",
}

# Borderline mappings flagged for operator/human review
LOW_CONFIDENCE_MAPPINGS = {
    "Collateral Markets": {
        "mapped_to": "LENDING",
        "reason": "Currently only Symbiotic ($442M). Could arguably be RESTAKING collateral infrastructure rather than pure lending."
    },
    "Secondary Debt Markets": {
        "mapped_to": "LENDING",
        "reason": "Currently only EulerDebt ($3.9k). Could be standalone DEBT_MARKETS if the sub-sector expands."
    },
    "Synthetics": {
        "mapped_to": "SYNTHETIC_DOLLAR",
        "reason": "Includes Ethena (USDe synthetic dollar), but also legacy synthetic asset protocols like Synthetix."
    },
    "Interest Rate Derivatives": {
        "mapped_to": "OPTIONS_DERIVATIVES",
        "reason": "Includes fixed-rate yield trading; borderline with YIELD_TRADING."
    },
    "Staking Pool": {
        "mapped_to": "LIQUID_STAKING",
        "reason": "Generic staking pools that may not issue a liquid token."
    }
}


def enum_map(category_raw: str) -> str:
    """
    DefiLlama's raw category label -> prompt's market_category enum.
    Hardcoded lookup table. NOT a model call.
    Unmapped labels return 'OTHER' and are logged.
    """
    if not category_raw:
        return "OTHER"
    mapped = DEFILLAMA_CATEGORY_TO_ENUM.get(category_raw)
    if mapped:
        return mapped
    logger.info(f"Unmapped raw category '{category_raw}' mapped to OTHER")
    return "OTHER"


# -----------------------------------------------------------------------------
# Rate Limiter & HTTP Fetch
# -----------------------------------------------------------------------------

_LAST_CALL_TS = 0.0
_MIN_INTERVAL = 60.0 / RATE_LIMIT_RPM


def _rate_limited_fetch(url: str, timeout: float = 30.0) -> bytes:
    """Fetch URL respecting RATE_LIMIT_RPM with backoff on 429."""
    global _LAST_CALL_TS
    elapsed = time.time() - _LAST_CALL_TS
    if elapsed < _MIN_INTERVAL:
        time.sleep(_MIN_INTERVAL - elapsed)

    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) GTMIntelligence/1.0"}
    max_retries = 3
    backoff = 2.0

    for attempt in range(max_retries):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                _LAST_CALL_TS = time.time()
                return resp.read()
        except urllib.error.HTTPError as e:
            if e.code == 429:
                logger.warning(f"Rate limited (429) on {url}. Backoff {backoff}s...")
                time.sleep(backoff)
                backoff *= 2.0
                continue
            raise
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            time.sleep(backoff)
            backoff *= 2.0

    raise RuntimeError(f"Failed to fetch {url} after {max_retries} attempts")


# -----------------------------------------------------------------------------
# 1. Snapshot Management
# -----------------------------------------------------------------------------

def fetch_snapshot(force: bool = False) -> Dict[str, Any]:
    """
    One network pass. Writes registry/defillama_snapshot.json.
    Skip if existing snapshot is younger than SNAPSHOT_TTL_DAYS unless force.
    Also fetches overview/fees for fee/revenue joining.
    """
    SNAPSHOT_FILE.parent.mkdir(parents=True, exist_ok=True)
    SNAPSHOTS_DIR.mkdir(parents=True, exist_ok=True)

    if not force and SNAPSHOT_FILE.exists():
        try:
            data = json.loads(SNAPSHOT_FILE.read_text(encoding="utf-8"))
            snap_date = data.get("snapshot_date")
            if snap_date:
                dt = datetime.fromisoformat(snap_date.replace("Z", "+00:00"))
                age_days = (datetime.now(timezone.utc) - dt).days
                if age_days < SNAPSHOT_TTL_DAYS:
                    logger.info(f"Using cached DefiLlama snapshot from {snap_date} (age: {age_days}d)")
                    return data
        except Exception as e:
            logger.warning(f"Failed to read existing snapshot: {e}. Re-fetching.")

    print("Fetching fresh DefiLlama /protocols snapshot...")
    raw_protocols = _rate_limited_fetch(f"{BASE}/protocols")
    protocols_list = json.loads(raw_protocols.decode("utf-8"))

    # Also fetch fees
    fees_list = []
    try:
        print("Fetching DefiLlama /overview/fees snapshot...")
        raw_fees = _rate_limited_fetch(f"{BASE}/overview/fees")
        fees_json = json.loads(raw_fees.decode("utf-8"))
        fees_list = fees_json.get("protocols", [])
    except Exception as e:
        logger.warning(f"Optional fees fetch failed: {e}")

    now_iso = datetime.now(timezone.utc).isoformat()
    now_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    snapshot_payload = {
        "snapshot_date": now_iso,
        "snapshot_day": now_date,
        "protocol_count": len(protocols_list),
        "protocols": protocols_list,
        "fees": fees_list,
    }

    # Write primary snapshot
    SNAPSHOT_FILE.write_text(json.dumps(snapshot_payload, indent=2), encoding="utf-8")

    # Write timestamped historical archive
    archive_file = SNAPSHOTS_DIR / f"defillama_snapshot_{now_date}.json"
    archive_file.write_text(json.dumps(snapshot_payload), encoding="utf-8")

    print(f"✅ Saved DefiLlama snapshot ({len(protocols_list)} protocols) to {SNAPSHOT_FILE}")
    return snapshot_payload


# -----------------------------------------------------------------------------
# 2. Category Universe
# -----------------------------------------------------------------------------

def category_universe(snapshot: Any) -> List[Dict[str, Any]]:
    """
    Aggregate /protocols by the `category` field.
    Emits MARKET_CATEGORY records with numbers already filled in from code.
    THE MODEL DOES NOT PRODUCE THESE NUMBERS.
    """
    if isinstance(snapshot, dict):
        protocols = snapshot.get("protocols", [])
        fees_by_slug = {f.get("slug"): f for f in snapshot.get("fees", []) if f.get("slug")}
        snapshot_day = snapshot.get("snapshot_day") or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    else:
        protocols = snapshot if isinstance(snapshot, list) else []
        fees_by_slug = {}
        snapshot_day = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # Aggregate by raw category
    cat_map: Dict[str, Dict[str, Any]] = {}

    for p in protocols:
        raw_cat = p.get("category")
        if not raw_cat:
            continue

        c_entry = cat_map.setdefault(raw_cat, {
            "category_raw": raw_cat,
            "category": enum_map(raw_cat),
            "protocol_count": 0,
            "tvl_usd": 0.0,
            "protocols": [],
            "chains_set": set(),
            "change_1d_sum": 0.0,
            "change_1d_count": 0,
            "change_7d_sum": 0.0,
            "change_7d_count": 0,
            "fees_annualised_usd": 0.0,
            "revenue_annualised_usd": 0.0,
            "has_fee_data": False,
        })

        c_entry["protocol_count"] += 1
        tvl = p.get("tvl")
        if isinstance(tvl, (int, float)):
            c_entry["tvl_usd"] += tvl

        for ch in p.get("chains", []):
            if ch:
                c_entry["chains_set"].add(ch)

        # Changes
        c1d = p.get("change_1d")
        if isinstance(c1d, (int, float)):
            c_entry["change_1d_sum"] += c1d
            c_entry["change_1d_count"] += 1

        c7d = p.get("change_7d")
        if isinstance(c7d, (int, float)):
            c_entry["change_7d_sum"] += c7d
            c_entry["change_7d_count"] += 1

        c_entry["protocols"].append({
            "name": p.get("name"),
            "slug": p.get("slug"),
            "tvl": tvl or 0.0,
            "twitter": p.get("twitter"),
            "url": p.get("url"),
            "parentProtocol": p.get("parentProtocol"),
        })

        # Join fee data if present
        slug = p.get("slug")
        if slug in fees_by_slug:
            fee_rec = fees_by_slug[slug]
            total24h = fee_rec.get("total24h") or 0.0
            if isinstance(total24h, (int, float)) and total24h > 0:
                c_entry["fees_annualised_usd"] += total24h * 365.0
                c_entry["has_fee_data"] = True

    # Build final list of MARKET_CATEGORY records
    universe: List[Dict[str, Any]] = []

    for raw_cat, c in sorted(cat_map.items(), key=lambda x: x[1]["tvl_usd"], reverse=True):
        # Sort protocols by TVL descending
        sorted_prots = sorted(c["protocols"], key=lambda x: x["tvl"], reverse=True)
        top_5_names = [p["name"] for p in sorted_prots[:5] if p["name"]]

        avg_c7d = (c["change_7d_sum"] / c["change_7d_count"]) if c["change_7d_count"] > 0 else 0.0

        record = {
            "record_type": "MARKET_CATEGORY",
            "category_raw": raw_cat,
            "category": c["category"],
            "definition": None,  # Model fills this prose mechanically
            "major_protocols": top_5_names,
            "protocol_count": c["protocol_count"],
            "tvl_usd": round(c["tvl_usd"], 2),
            "fees_annualised_usd": round(c["fees_annualised_usd"], 2) if c["has_fee_data"] else "UNKNOWN",
            "revenue_annualised_usd": "UNKNOWN",
            "chains": sorted(list(c["chains_set"]))[:10],
            "chains_count": len(c["chains_set"]),
            "avg_change_7d": round(avg_c7d, 2),
            "trend": None,        # Model derives given avg_change_7d
            "trend_basis": None,  # Model writes basis citing avg_change_7d
            "snapshot_date": snapshot_day,
            "evidence_tier": "OBSERVED",
            "derived_by": "code",
            "source_url": f"{BASE}/protocols",
        }
        universe.append(record)

    return universe


# -----------------------------------------------------------------------------
# 3. Player Metrics
# -----------------------------------------------------------------------------

def player_metrics(snapshot: Any, slug_or_name: str) -> Dict[str, Any]:
    """
    tvl, chains, change_1d, change_7d, fees/revenue joined from /overview/fees.
    Computes TVL percentile within player's category.
    """
    if isinstance(snapshot, dict):
        protocols = snapshot.get("protocols", [])
        fees_by_slug = {f.get("slug"): f for f in snapshot.get("fees", []) if f.get("slug")}
    else:
        protocols = snapshot if isinstance(snapshot, list) else []
        fees_by_slug = {}
    target = slug_or_name.lower().strip()

    # Find protocol
    match = None
    # 1. Exact slug match
    for p in protocols:
        if (p.get("slug") or "").lower() == target:
            match = p
            break

    # 2. Exact name match
    if not match:
        for p in protocols:
            if (p.get("name") or "").lower() == target:
                match = p
                break

    # 3. Parent protocol match (pick the largest instance by TVL)
    if not match:
        parent_candidates = [
            p for p in protocols
            if (p.get("parentProtocol") or "").lower() in (f"parent#{target}", target)
        ]
        if parent_candidates:
            match = max(parent_candidates, key=lambda x: x.get("tvl") or 0.0)

    # 4. Slug prefix match (pick largest)
    if not match:
        prefix_candidates = [
            p for p in protocols
            if (p.get("slug") or "").lower().startswith(f"{target}-")
        ]
        if prefix_candidates:
            match = max(prefix_candidates, key=lambda x: x.get("tvl") or 0.0)

    if not match:
        return {"error": f"Protocol '{slug_or_name}' not found in snapshot"}

    cat = match.get("category")
    cat_protocols = [p for p in protocols if p.get("category") == cat and isinstance(p.get("tvl"), (int, float))]
    sorted_cat_tvls = sorted([p.get("tvl", 0.0) for p in cat_protocols])

    player_tvl = match.get("tvl") or 0.0
    rank = sum(1 for t in sorted_cat_tvls if t <= player_tvl)
    percentile = (rank / len(sorted_cat_tvls) * 100.0) if sorted_cat_tvls else 50.0

    fee_info = fees_by_slug.get(match.get("slug"), {})

    return {
        "name": match.get("name"),
        "slug": match.get("slug"),
        "parentProtocol": match.get("parentProtocol"),
        "category_raw": cat,
        "category": enum_map(cat),
        "tvl_usd": player_tvl,
        "tvl_percentile_in_category": round(percentile, 1),
        "chains": match.get("chains", []),
        "chain_count": len(match.get("chains", [])),
        "change_1d": match.get("change_1d"),
        "change_7d": match.get("change_7d"),
        "fees_24h_usd": fee_info.get("total24h", "UNKNOWN"),
        "fees_7d_usd": fee_info.get("total7d", "UNKNOWN"),
        "twitter": match.get("twitter"),
        "url": match.get("url"),
        "audits": match.get("audits"),
        "listedAt": match.get("listedAt"),
        "evidence_tier": "OBSERVED",
        "derived_by": "code",
        "source_url": f"{BASE}/protocols",
    }


# -----------------------------------------------------------------------------
# 4. Product Decomposition
# -----------------------------------------------------------------------------

def product_decomposition(snapshot: Any, parent_or_slug: str) -> List[Dict[str, Any]]:
    """
    All protocol entries sharing a parentProtocol or matching slug.
    e.g. parent#aave -> aave-v2, aave-v3, aave-v4, aave-horizon-rwa.
    Satisfies the Phase 3 gate (>=3 named products) IN CODE.
    """
    if isinstance(snapshot, dict):
        protocols = snapshot.get("protocols", [])
    else:
        protocols = snapshot if isinstance(snapshot, list) else []
    target = parent_or_slug.lower().strip()
    if not target.startswith("parent#"):
        parent_target = f"parent#{target}"
    else:
        parent_target = target

    matched_products = []

    for p in protocols:
        p_parent = (p.get("parentProtocol") or "").lower()
        p_slug = (p.get("slug") or "").lower()
        p_name = (p.get("name") or "").lower()

        # Match either exact parentProtocol, or fallback prefix
        if p_parent == parent_target or p_parent == target or (p_slug == target):
            matched_products.append({
                "name": p.get("name"),
                "slug": p.get("slug"),
                "what_it_does": p.get("description") or f"{p.get('name')} instance",
                "category": enum_map(p.get("category")),
                "tvl_usd": p.get("tvl") or 0.0,
                "chains": p.get("chains", []),
                "twitter": p.get("twitter"),
                "url": p.get("url"),
                "source_url": f"{BASE}/protocol/{p.get('slug')}",
                "evidence_tier": "OBSERVED",
                "derived_by": "code",
            })

    # If no parent match found, look for name prefix match (e.g. 'morpho-')
    if len(matched_products) <= 1:
        prefix = target.replace("parent#", "")
        for p in protocols:
            p_slug = (p.get("slug") or "").lower()
            if p_slug.startswith(f"{prefix}-") and p not in matched_products:
                matched_products.append({
                    "name": p.get("name"),
                    "slug": p.get("slug"),
                    "what_it_does": p.get("description") or f"{p.get('name')} instance",
                    "category": enum_map(p.get("category")),
                    "tvl_usd": p.get("tvl") or 0.0,
                    "chains": p.get("chains", []),
                    "twitter": p.get("twitter"),
                    "url": p.get("url"),
                    "source_url": f"{BASE}/protocol/{p.get('slug')}",
                    "evidence_tier": "OBSERVED",
                    "derived_by": "code",
                })

    # Sort products by TVL descending
    return sorted(matched_products, key=lambda x: x["tvl_usd"], reverse=True)


# -----------------------------------------------------------------------------
# 6. Historical Momentum & Protocol Cache (Item 2)
# -----------------------------------------------------------------------------

PROTOCOL_CACHE_DIR = Path("D:/new orchestration/pipeline/gtm_engine/registry/cache/protocol")
NETWORK_CALL_COUNTER = 0


def momentum_30d(slug: str) -> Dict[str, Any]:
    """
    /protocols has no change_1m. Derive it from the historical series.
    Cached forever — the series is append-only, so a stale tail is harmless
    for a 30-day window and a re-fetch is cheap when needed.
    """
    global NETWORK_CALL_COUNTER
    PROTOCOL_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    f = PROTOCOL_CACHE_DIR / f"{slug}.json"

    if f.exists():
        try:
            r = json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            r = None
    else:
        r = None

    if r is None:
        NETWORK_CALL_COUNTER += 1
        raw_bytes = _rate_limited_fetch(f"{BASE}/protocol/{slug}")
        r = json.loads(raw_bytes.decode("utf-8"))
        f.write_text(json.dumps(r), encoding="utf-8")

    series = r.get("tvl") or []
    if len(series) < 31:
        return {
            "slug": slug,
            "change_30d": None,
            "basis": f"UNKNOWN — only {len(series)} days of history",
            "evidence_tier": "UNKNOWN",
            "from_cache": f.exists(),
        }

    now_val = series[-1].get("totalLiquidityUSD", 0.0)
    then_val = series[-31].get("totalLiquidityUSD", 0.0)

    if not then_val or then_val <= 0:
        return {
            "slug": slug,
            "change_30d": None,
            "basis": "UNKNOWN — zero baseline",
            "evidence_tier": "UNKNOWN",
            "from_cache": f.exists(),
        }

    change_pct = round(((now_val - then_val) / then_val) * 100.0, 2)
    return {
        "slug": slug,
        "change_30d": change_pct,
        "tvl_then": then_val,
        "tvl_now": now_val,
        "basis": f"TVL ${then_val:,.0f} -> ${now_val:,.0f} over 30d ({change_pct:+.2f}%)",
        "evidence_tier": "OBSERVED",
        "from_cache": f.exists(),
    }

# -----------------------------------------------------------------------------
# 5. Channel Seeds & Probing (Fixes 0.1, 0.2, 0.3)
# -----------------------------------------------------------------------------

APP_PREFIXES = ("app", "www", "dapp", "trade", "swap", "portal", "my", "beta")
DEAD_PHRASES = (
    "page not found", "404 not found", "404 - ", "404 error",
    "does not exist", "page does not exist", "coming soon",
    "this page could not be found"
)
BLOG_SUBDOMAINS = ("news.", "blog.", "insights.", "research.", "mirror.")
FORUM_SUBDOMAINS = ("governance.", "forum.", "research.", "gov.", "discuss.", "snapshot.")
BLOG_PATHS = ["/blog", "/news", "/insights", "/updates"]
RSS_PATHS = ["/blog/rss.xml", "/rss.xml", "/feed", "/blog/feed", "/atom.xml"]


def resolve_player_id(protocol: Dict[str, Any]) -> str:
    """
    Fix 0.1: player_id is parentProtocol when present (not product slug).
    Standalone protocols use slug.
    """
    parent = protocol.get("parentProtocol")
    if parent:
        return parent.replace("parent#", "").strip()
    return protocol.get("slug") or protocol.get("name") or "unknown"


def domain_variants(url: str) -> List[str]:
    """
    Fix 0.2: Extract host and generate apex domain variants.
    e.g. https://app.morpho.org -> ['app.morpho.org', 'morpho.org']
    Prefers apex domain when both resolve.
    """
    if not url or url in ("NO_URL", "UNKNOWN", ""):
        return []
    parsed = urllib.parse.urlparse(url)
    host = parsed.netloc.lower()
    if host.startswith("www."):
        host = host[4:]
    parts = host.split(".")
    variants = [host]
    if len(parts) >= 3 and parts[0] in APP_PREFIXES:
        apex = ".".join(parts[1:])
        variants.append(apex)
    return variants


def probe_confirm(url: str, timeout: float = 8.0) -> Dict[str, Any]:
    """
    Fix 0.3: GET request and content validation.
    Catches SPA soft-404s (e.g. Curve) and confirms real blog/forum index content.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) GTMIntelligence/1.0",
        "Accept": "text/html,application/xhtml+xml,application/xml,application/rss+xml;q=0.9,*/*;q=0.8",
    }
    try:
        req = urllib.request.Request(url, headers=headers, method="GET")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            code = resp.getcode()
            if code >= 400:
                return {"url": url, "confirmed": False, "reason": f"http_{code}"}

            chunk = resp.read(24576).decode("utf-8", errors="ignore")
            chunk_lower = chunk.lower()

            # 1. Soft-404 detection via title or dead phrases
            if re.search(r"<title>.*?(?:404|not found|page not).*?</title>", chunk_lower):
                return {"url": url, "confirmed": False, "reason": "soft_404_title"}

            if any(m in chunk_lower for m in DEAD_PHRASES):
                return {"url": url, "confirmed": False, "reason": "soft_404_phrase"}

            # 2. RSS / Atom feed validation
            if any(ext in url for ext in ("xml", "rss", "feed")):
                if any(tag in chunk_lower for tag in ("<rss", "<feed", "<channel", "xmlns")):
                    return {"url": url, "confirmed": True, "reason": "rss_feed", "final_url": resp.geturl()}
                return {"url": url, "confirmed": False, "reason": "invalid_feed_xml"}

            # 3. Governance forum detection
            if any(pfx in url for pfx in FORUM_SUBDOMAINS) or "/governance" in url:
                if any(s in chunk_lower for s in ("discourse", "topic", "category", "governance", "proposal", "forum", "threads")):
                    return {"url": url, "confirmed": True, "reason": "governance_forum", "final_url": resp.geturl()}
                return {"url": url, "confirmed": False, "reason": "no_forum_markers"}

            # 4. Real blog / news index detection (dated links check)
            dated_links = len(re.findall(r"/20\d{2}[/\-]", chunk))
            
            # Subdomains dedicated to news/blog (e.g. news.curve.finance)
            is_blog_subdomain = any(pfx in url for pfx in BLOG_SUBDOMAINS)
            if is_blog_subdomain and dated_links >= 2:
                return {"url": url, "confirmed": True, "dated_links": dated_links, "final_url": resp.geturl()}

            if dated_links < 3:
                return {"url": url, "confirmed": False, "reason": f"no_post_index ({dated_links} dated links)"}

            return {"url": url, "confirmed": True, "dated_links": dated_links, "final_url": resp.geturl()}
    except urllib.error.HTTPError as e:
        return {"url": url, "confirmed": False, "reason": f"http_{e.code}"}
    except Exception as e:
        return {"url": url, "confirmed": False, "reason": f"unreachable: {type(e).__name__}"}


def probe_seeds(seeds: Dict[str, Any], max_candidates_per_type: int = 15) -> Dict[str, Any]:
    """
    Validate candidate channel URLs using content inspection (probe_confirm).
    Includes sanity guard: if > 2 blog candidates confirm for one player,
    mark probe_status: 'SUSPECTED_SOFT_404' and confirm none.
    """
    for key in ("candidate_blog_urls", "candidate_forum_urls", "candidate_rss_urls"):
        confirmed = []
        candidates = seeds.get(key, [])[:max_candidates_per_type]
        for u in candidates:
            res = probe_confirm(u, timeout=6.0)
            if res.get("confirmed"):
                confirmed.append(res.get("final_url") or u)

        # Sanity guard on blogs: if > 2 confirm, it's a SPA catch-all
        if key == "candidate_blog_urls" and len(confirmed) > 2:
            seeds["probe_status"] = "SUSPECTED_SOFT_404"
            seeds[key.replace("candidate_", "confirmed_")] = []
            continue

        seeds[key.replace("candidate_", "confirmed_")] = confirmed

    if seeds.get("probe_status") != "SUSPECTED_SOFT_404":
        seeds["probe_status"] = "PROBED"

    return seeds


def channel_seeds(snapshot: Any, slug_or_name: str, probe: bool = False) -> Dict[str, Any]:
    """
    Returns {player_id, product_slug, website, twitter_handle, github,
    candidate_blog_urls, candidate_forum_urls, candidate_rss_urls, probe_status}.
    Probes subdomains before paths.
    """
    metrics = player_metrics(snapshot, slug_or_name)
    website = metrics.get("url")
    twitter = metrics.get("twitter")
    parent_proto = metrics.get("parentProtocol")
    slug = metrics.get("slug") or slug_or_name

    # Fix 0.1: player_id is parentProtocol when present
    player_id = parent_proto.replace("parent#", "").strip() if parent_proto else slug

    candidate_blogs: List[str] = []
    candidate_forums: List[str] = []
    candidate_rss: List[str] = []

    if website and website not in ("NO_URL", "UNKNOWN", ""):
        # Fix 0.2: domain variants (apex domain prioritized)
        hosts = domain_variants(website)

        for host in hosts:
            site_root = f"https://{host}"

            # Subdomain prefixes FIRST (e.g. news.curve.finance, blog.morpho.org)
            for sub_pfx in BLOG_SUBDOMAINS:
                candidate_blogs.append(f"https://{sub_pfx}{host}")

            # Standard paths on this domain
            for p in BLOG_PATHS:
                candidate_blogs.append(f"{site_root}{p}")

            # Forum subdomains FIRST
            for f_pfx in FORUM_SUBDOMAINS:
                candidate_forums.append(f"https://{f_pfx}{host}")
            candidate_forums.append(f"{site_root}/governance")

            # RSS paths
            for p in RSS_PATHS:
                candidate_rss.append(f"{site_root}{p}")
                candidate_rss.append(f"https://news.{host}{p}")

        if twitter:
            candidate_blogs.append(f"https://mirror.xyz/{twitter}")
            candidate_blogs.append(f"https://medium.com/@{twitter}")

        # Deduplicate while preserving order
        candidate_blogs = list(dict.fromkeys(candidate_blogs))
        candidate_forums = list(dict.fromkeys(candidate_forums))
        candidate_rss = list(dict.fromkeys(candidate_rss))

        seeds = {
            "player_id": player_id,
            "product_slug": slug,
            "website": website,
            "twitter_handle": twitter or "UNKNOWN",
            "github": "UNKNOWN",
            "candidate_blog_urls": candidate_blogs,
            "candidate_forum_urls": candidate_forums,
            "candidate_rss_urls": candidate_rss,
            "probe_status": "UNPROBED",
            "derived_by": "code",
            "source_url": f"{BASE}/protocols",
        }
    else:
        # Case B: Website missing (38.6% of cases) -> 4-tier honest fallback
        docs_guess = f"https://docs.{player_id}.xyz"
        seeds = {
            "player_id": player_id,
            "product_slug": slug,
            "website": None,
            "twitter_handle": twitter or "UNKNOWN",
            "github": "UNKNOWN",
            "candidate_blog_urls": [f"https://mirror.xyz/{twitter}"] if twitter else [],
            "candidate_forum_urls": [],
            "candidate_rss_urls": [],
            "seed_source": "TWITTER_ONLY" if twitter else "NO_HANDLE_FOUND",
            "probe_status": "NO_WEBSITE_FOUND",
            "docs_candidate": docs_guess,
            "derived_by": "code",
            "source_url": f"{BASE}/protocols",
        }

    if probe:
        return probe_seeds(seeds)
    return seeds


def export_enum_map_tsv(output_path: Optional[Path] = None) -> Path:
    """Export the complete 101-category enum mapping table to clean TSV format."""
    snapshot = fetch_snapshot(force=False)
    cats = category_universe(snapshot)
    
    rows = []
    for c in cats:
        raw = c["category_raw"]
        en = enum_map(raw)
        n = c["protocol_count"]
        tvl = c["tvl_usd"]
        conf = "LOW" if raw in LOW_CONFIDENCE_MAPPINGS else "HIGH"
        rows.append((raw, en, n, tvl, conf))

    # Sort by mapped enum, then TVL descending
    rows = sorted(rows, key=lambda r: (r[1], -r[3]))

    out_file = output_path or Path("D:/new orchestration/pipeline/gtm_engine/registry/enum_map.tsv")
    out_file.parent.mkdir(parents=True, exist_ok=True)

    with open(out_file, "w", encoding="utf-8") as f:
        f.write("raw\tenum\tprotocol_count\ttvl_usd\tconfidence\n")
        for raw, en, n, tvl, conf in rows:
            f.write(f"{raw}\t{en}\t{n}\t{int(tvl)}\t{conf}\n")

    return out_file
