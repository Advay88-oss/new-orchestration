"""
Mine Reddit User Discussions on Undercollateralized Lending & Leverage Primitives.
Queries r/defi, r/Stellar, r/ethfinance via authenticated OpenCLI session.
Captures sentiment, objection types, and excerpts (< 20 words).
"""

import subprocess
import json
import re
from pathlib import Path
from collections import Counter
from datetime import datetime, timezone

OPENCLI = "C:/Users/Advay Anand/AppData/Roaming/npm/opencli.cmd"
OUT_FILE = Path("pipeline/gtm_engine/registry/reddit_objections.jsonl")
OUT_FILE.parent.mkdir(parents=True, exist_ok=True)

SEARCH_TASKS = [
    ("defi", "undercollateralized lending"),
    ("defi", "Gearbox liquidation"),
    ("defi", "leverage looping risk"),
    ("Stellar", "Blend lending"),
    ("Stellar", "Soroban smart contracts DeFi"),
    ("CryptoCurrency", "undercollateralized crypto loan")
]

def classify_objection(title: str, text: str) -> str:
    combined = (title + " " + text).lower()
    if any(k in combined for k in ["liquidat", "wick", "health factor", "margin call"]):
        return "LIQUIDATION"
    if any(k in combined for k in ["hack", "exploit", "rug", "safe", "scam", "trust"]):
        return "TRUST"
    if any(k in combined for k in ["complex", "confusing", "understand", "how does"]):
        return "COMPLEXITY"
    if any(k in combined for k in ["custody", "keys", "smart contract risk"]):
        return "CUSTODY"
    if any(k in combined for k in ["apy", "yield", "ponzi", "unsustainable", "where does the yield"]):
        return "YIELD_SOURCE"
    if any(k in combined for k in ["stellar", "ethereum", "solana", "l2", "base", "why on"]):
        return "CHAIN_CHOICE"
    return "OTHER"

def classify_sentiment(title: str, text: str) -> str:
    combined = (title + " " + text).lower()
    if "?" in title or any(k in combined for k in ["how", "why", "what", "is it possible"]):
        return "QUESTION"
    if any(k in combined for k in ["risk", "danger", "lost", "bad", "scam", "careful", "warning", "wipe"]):
        return "NEGATIVE"
    if any(k in combined for k in ["great", "promising", "love", "good", "interesting", "bullish"]):
        return "POSITIVE"
    return "NEUTRAL"

def extract_short_excerpt(text: str, max_words: int = 18) -> str:
    clean = re.sub(r"\s+", " ", text).strip()
    words = clean.split()
    if not words:
        return "Discussion on protocol mechanics."
    return " ".join(words[:max_words]) + ("..." if len(words) > max_words else "")

def main():
    print("================================================================")
    print("🚀 Mining Reddit User Objections & Sentiment via OpenCLI")
    print("================================================================\n")

    captured_records = []
    seen_ids = set()

    for sub, q in SEARCH_TASKS:
        print(f"Searching r/{sub} for '{q}'...")
        cmd = [OPENCLI, "reddit", "search", q, "--subreddit", sub, "--limit", "10", "-f", "json"]
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=40)
            if r.returncode == 0 and r.stdout.strip():
                try:
                    data = json.loads(r.stdout)
                    items = data if isinstance(data, list) else data.get("items", [])
                    print(f"  ✓ Found {len(items)} posts in r/{sub}")
                    for item in items:
                        pid = item.get("id")
                        if not pid or pid in seen_ids:
                            continue
                        seen_ids.add(pid)

                        title = item.get("title", "")
                        selftext = item.get("selftext", "") or ""
                        
                        # Filter out promotional ads / spam
                        if any(sp in (title + selftext).lower() for sp in ["join my", "referral code", "airdrop claim now"]):
                            continue

                        obj_type = classify_objection(title, selftext)
                        sentiment = classify_sentiment(title, selftext)
                        excerpt = extract_short_excerpt(selftext if len(selftext) > 20 else title)

                        created_utc = item.get("created_utc")
                        date_str = datetime.fromtimestamp(created_utc, tz=timezone.utc).strftime("%Y-%m-%d") if created_utc else "UNKNOWN"

                        rec = {
                            "reddit_id": pid,
                            "subreddit": f"r/{sub}",
                            "url": item.get("url") or f"https://reddit.com/r/{sub}/comments/{pid}",
                            "date": date_str,
                            "title": title[:100],
                            "sentiment": sentiment,
                            "objection_type": obj_type,
                            "excerpt": excerpt,
                            "upvotes": item.get("score", 0),
                            "comments_count": item.get("comments", 0)
                        }
                        captured_records.append(rec)
                except Exception as e:
                    print(f"  ❌ Error parsing JSON from r/{sub}: {e}")
            else:
                print(f"  ⚠️ No posts returned or error from r/{sub}: {r.stderr[:80]}")
        except Exception as e:
            print(f"  ❌ Subprocess timeout/error on r/{sub}: {e}")

    print(f"\nTotal Valid Discussions Captured: {len(captured_records)}")
    
    # Save to jsonl
    with open(OUT_FILE, "w", encoding="utf-8") as f:
        for r in captured_records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    # Frequency distributions
    obj_counter = Counter(r["objection_type"] for r in captured_records)
    sent_counter = Counter(r["sentiment"] for r in captured_records)

    print("\n--- Objection Frequency Distribution ---")
    for ot, cnt in obj_counter.most_common():
        print(f"  • {ot:16}: {cnt:2d} ({cnt/max(len(captured_records),1)*100:.1f}%)")

    print("\n--- Sentiment Distribution ---")
    for st, cnt in sent_counter.most_common():
        print(f"  • {st:16}: {cnt:2d} ({cnt/max(len(captured_records),1)*100:.1f}%)")

if __name__ == "__main__":
    main()
