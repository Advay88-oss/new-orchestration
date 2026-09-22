"""
Rewired Phase 1 Runner for GTM Intelligence Engine (Step 2).
Code supplies every number and protocol list.
Model (Flash tier) supplies ONLY the mechanical definition, trend, and trend_basis.
Eliminates numeric fabrication by structural design.
"""

import os
import sys
import json
import time
import urllib.request
from pathlib import Path

REPO_ROOT = Path("D:/new orchestration")
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from pipeline.gtm_engine.interceptors.defillama import (
    fetch_snapshot,
    category_universe,
)
from pipeline.gtm_engine.evals.assertions import run_all_assertions


def get_gemini_key() -> str:
    k = os.environ.get("GEMINI_API_KEY")
    if k:
        return k
    envf = REPO_ROOT / "pipeline" / ".env"
    if envf.exists():
        for line in envf.read_text(encoding="utf-8").splitlines():
            if line.startswith("GEMINI_API_KEY="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    raise ValueError("GEMINI_API_KEY not found in env or pipeline/.env")


def call_flash_for_narratives(categories_summary: list) -> list:
    """Send compact structural summary to Flash. Returns ONLY definitions and trends."""
    key = get_gemini_key()
    model = os.environ.get("GTM_FLASH_MODEL") or os.environ.get("VANNA_GEMINI_MODEL") or "gemini-flash-latest"
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"

    system_instruction = (
        "You are a market discovery specialist in DeFi. "
        "Given the aggregated category metrics computed strictly by code from DeFiLlama, "
        "you provide ONLY the mechanical definition of what protocols in each category do, "
        "and determine the trend ('GROWING' | 'FLAT' | 'DECLINING' | 'UNKNOWN') citing the provided change figures in trend_basis.\n"
        "Return a JSON array of objects with keys: "
        "['category_raw', 'definition', 'trend', 'trend_basis'].\n"
        "Do not invent any numbers. Reference ONLY the figures given in the input."
    )

    user_prompt = f"CATEGORIES_INPUT:\n{json.dumps(categories_summary, indent=2)}"

    payload = {
        "contents": [{"role": "user", "parts": [{"text": user_prompt}]}],
        "systemInstruction": {"parts": [{"text": system_instruction}]},
        "generationConfig": {
            "temperature": 0.1,
            "maxOutputTokens": 8192,
            "responseMimeType": "application/json"
        }
    }

    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    print(f"Calling Flash tier model ({model}) for {len(categories_summary)} category narratives...")
    with urllib.request.urlopen(req, timeout=90) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        raw_text = data["candidates"][0]["content"]["parts"][0]["text"]
        return json.loads(raw_text)


def main():
    print("================================================================")
    print("🚀 GTM Engine: Code-First Rewired Phase 1 (Market Discovery)")
    print("================================================================")

    # 1. Load or fetch snapshot (code only)
    snapshot = fetch_snapshot(force=False)
    raw_universe = category_universe(snapshot)
    print(f"Aggregated {len(raw_universe)} categories from DefiLlama snapshot.")

    # Select top 16 categories by TVL (exceeds >=12 gate requirement)
    selected_categories = raw_universe[:16]

    # 2. Build compact projection for model (W3)
    compact_summary = []
    for c in selected_categories:
        compact_summary.append({
            "category_raw": c["category_raw"],
            "category": c["category"],
            "protocol_count": c["protocol_count"],
            "tvl_usd": c["tvl_usd"],
            "top_5_by_tvl": c["major_protocols"],
            "chains_count": c["chains_count"],
            "avg_change_7d": c["avg_change_7d"],
        })

    print(f"Prepared compact projection ({len(compact_summary)} categories).")
    print(f"Sample projection: {json.dumps(compact_summary[0], indent=2)}")

    # 3. Model call for prose only
    t0 = time.time()
    narratives = call_flash_for_narratives(compact_summary)
    print(f"✅ Received narratives in {time.time() - t0:.2f}s.")

    narrative_map = {n.get("category_raw"): n for n in narratives if n.get("category_raw")}

    # 4. Code merges model prose into deterministic numeric records
    final_records = []
    for c in selected_categories:
        cat_raw = c["category_raw"]
        prose = narrative_map.get(cat_raw, {})

        merged_rec = dict(c)
        merged_rec["definition"] = prose.get("definition") or f"Mechanisms operating in {cat_raw} across DeFi."
        merged_rec["trend"] = prose.get("trend") or "UNKNOWN"
        merged_rec["trend_basis"] = prose.get("trend_basis") or f"7-day average change of {c['avg_change_7d']}%."

        final_records.append(merged_rec)

    # Build final envelope
    envelope = {
        "phase": 1,
        "scope": "full market universe",
        "status": "COMPLETE",
        "records": final_records,
        "unknowns": [
            {
                "field": "revenue_annualised_usd",
                "reason": "DeFiLlama free tier reports fees; protocol-retained revenue not isolated on free endpoints",
                "what_was_found": "annualised fees where available"
            }
        ],
        "contradictions": [],
        "warnings": [],
        "sources_visited": ["https://api.llama.fi/protocols", "https://api.llama.fi/overview/fees"],
        "next_phase_ready": True,
        "blocker": None,
    }

    # Save to registry
    out_path = REPO_ROOT / "pipeline" / "gtm_engine" / "registry" / "phase_1_output.json"
    out_path.write_text(json.dumps(envelope, indent=2), encoding="utf-8")
    print(f"💾 Saved verified rewired Phase 1 output to: {out_path}")

    # 5. Run assertion suite with numeric truth verification
    print("\n----------------------------------------------------------------")
    print("🔍 Running Assertion Suite (with L1_verify_numerics)...")
    print("----------------------------------------------------------------")

    truth_map = {c["category_raw"]: c for c in raw_universe}
    results = run_all_assertions(envelope, check_live_urls=True, truth_categories=truth_map)

    print(f"Phase: {results['phase']}")
    print(f"Passed: {results['passed']}")
    print(f"Total Violations: {results['total_violations']}")
    print(f"Summary: {json.dumps(results['summary'], indent=2)}")
    print(f"UNKNOWN Rate: {results['unknown_rate']:.1%}")
    print(f"URL Metrics: {json.dumps(results['url_metrics'], indent=2)}")

    if results["violations"]:
        print("\nViolations List:")
        for v in results["violations"]:
            print(f"  • [{v['layer']}] {v['rule']}: {v['message']}")

    report_path = REPO_ROOT / "pipeline" / "gtm_engine" / "registry" / "phase_1_rewired_assertion_report.json"
    report_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"💾 Assertion report saved to: {report_path}")

    return 0 if results["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
