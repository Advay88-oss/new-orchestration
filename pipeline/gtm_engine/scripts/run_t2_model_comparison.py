"""
Run T2-rules vs T2-model (gemini-3.8-flash) on all 85 Curve artefacts.
Compares category classifications and calculates exact disagreement rate.
"""

import os
import sys
import json
import time
import urllib.request
from collections import Counter
from pathlib import Path

REPO_ROOT = Path("D:/new orchestration")
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from pipeline.gtm_engine.interceptors.context_isolation import assert_context_isolation

ENV_FILE = REPO_ROOT / "pipeline" / ".env"

def get_gemini_key():
    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        if line.startswith("GEMINI_API_KEY="):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    raise ValueError("GEMINI_API_KEY missing")

def load_curve_artefacts():
    from pipeline.gtm_engine.scripts.run_fix1_t2_and_fix2_clustering import build_curve_full_corpus
    return build_curve_full_corpus()

def call_flash_classify_batch(batch, api_key):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash:generateContent?key={api_key}"
    
    prompt = """Classify each DeFi artefact title/snippet into exactly ONE of these canonical categories:
- METRICS_PROOF
- GOVERNANCE
- TOKEN_ECONOMICS
- COMMUNITY
- PARTNERSHIP
- PRODUCT

Input artefacts:
"""
    for idx, a in enumerate(batch):
        prompt += f"[{idx}] (Channel: {a['channel']}) Title: {a['title']}\n"

    prompt += "\nReturn JSON object: {\"results\": [\"CATEGORY_FOR_0\", \"CATEGORY_FOR_1\", ...]}"

    # Enforce context isolation
    assert_context_isolation("flash", prompt)

    payload = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.0,
            "maxOutputTokens": 2048,
            "responseMimeType": "application/json"
        }
    }

    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )

    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        txt = data["candidates"][0]["content"]["parts"][0]["text"]
        parsed = json.loads(txt)
        return parsed.get("results", [])

def main():
    print("Loading 85 Curve artefacts...")
    artefacts = load_curve_artefacts()
    print(f"Loaded {len(artefacts)} Curve artefacts.")

    # 1. T2-rules
    rules_cats = [a["content_category"] for a in artefacts]
    rules_counter = Counter(rules_cats)
    rules_top3 = [c for c, _ in rules_counter.most_common(3)]
    
    expected_any = {'METRICS_PROOF', 'GOVERNANCE', 'TOKEN_ECONOMICS'}
    forbidden = {'COMMUNITY'}
    rules_passed = len(set(rules_top3) & expected_any) >= 2 and not (set(rules_top3) & forbidden)

    print("\n--- T2-rules Results ---")
    for cat, cnt in rules_counter.most_common():
        print(f"  {cat:18}: {cnt:2d} ({cnt/len(artefacts)*100:.1f}%)")
    print(f"Top 3: {rules_top3} | Passed: {rules_passed}")

    # 2. T2-model (gemini-3.8-flash)
    api_key = get_gemini_key()
    print("\nCalling gemini-3.8-flash for T2-model classification (batches of 20)...")
    model_cats = []
    batch_size = 20
    for i in range(0, len(artefacts), batch_size):
        batch = artefacts[i:i + batch_size]
        print(f"  Classifying batch {i//batch_size + 1} ({len(batch)} items)...")
        res = call_flash_classify_batch(batch, api_key)
        model_cats.extend(res)
        time.sleep(1.0)

    model_counter = Counter(model_cats)
    model_top3 = [c for c, _ in model_counter.most_common(3)]
    model_passed = len(set(model_top3) & expected_any) >= 2 and not (set(model_top3) & forbidden)

    print("\n--- T2-model Results ---")
    for cat, cnt in model_counter.most_common():
        print(f"  {cat:18}: {cnt:2d} ({cnt/len(artefacts)*100:.1f}%)")
    print(f"Top 3: {model_top3} | Passed: {model_passed}")

    # 3. Disagreement Analysis
    disagreements = 0
    disagreement_examples = []
    for idx, (r, m) in enumerate(zip(rules_cats, model_cats)):
        if r != m:
            disagreements += 1
            if len(disagreement_examples) < 5:
                disagreement_examples.append({
                    "title": artefacts[idx]["title"][:60],
                    "rule": r,
                    "model": m
                })

    disagreement_rate = (disagreements / len(artefacts)) * 100.0
    print("\n--- Comparison & Disagreement Rate ---")
    print(f"Total Artefacts:     {len(artefacts)}")
    print(f"Agreements:          {len(artefacts) - disagreements} ({100 - disagreement_rate:.1f}%)")
    print(f"Disagreements:       {disagreements} ({disagreement_rate:.1f}%)")
    print("\nSample Disagreements:")
    for ex in disagreement_examples:
        print(f"  Title: '{ex['title']}...' -> Rule: {ex['rule']} vs Model: {ex['model']}")

    # Save output report
    report = {
        "rules_top3": rules_top3,
        "rules_passed": rules_passed,
        "rules_counts": dict(rules_counter),
        "model_id": "gemini-3.8-flash",
        "model_top3": model_top3,
        "model_passed": model_passed,
        "model_counts": dict(model_counter),
        "disagreement_rate_pct": round(disagreement_rate, 2),
        "disagreements_count": disagreements
    }
    out_p = REPO_ROOT / "pipeline" / "gtm_engine" / "registry" / "t2_comparison_report.json"
    out_p.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"\nReport written to: {out_p}")

if __name__ == "__main__":
    main()
