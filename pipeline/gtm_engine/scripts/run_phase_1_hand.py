"""
Manual Phase 1 runner for GTM Intelligence Engine (Step 3 & 4 of build order).
Executes Phase 1 with the exact system prompt and phase instruction.
Saves raw output to registry/phase_1_raw_output.json and runs assertion suite.
"""

import os
import sys
import json
import time
import urllib.request
import urllib.error
from pathlib import Path

# Add project root to sys.path
REPO_ROOT = Path("D:/new orchestration")
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

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


def call_flash(system_prompt: str, user_prompt: str) -> str:
    key = get_gemini_key()
    model = os.environ.get("GTM_FLASH_MODEL") or os.environ.get("VANNA_GEMINI_MODEL") or "gemini-flash-latest"
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"

    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": user_prompt}]
            }
        ],
        "systemInstruction": {
            "parts": [{"text": system_prompt}]
        },
        "generationConfig": {
            "temperature": 0.1,  # Low temperature for strict structured adherence
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

    print(f"Connecting to Gemini Flash ({model})...")
    with urllib.request.urlopen(req, timeout=90) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        candidates = data.get("candidates", [])
        if not candidates:
            raise RuntimeError(f"No candidates returned: {data}")
        raw_text = candidates[0]["content"]["parts"][0]["text"]
        return raw_text


def main():
    print("================================================================")
    print("🚀 GTM Engine: Manual Phase 1 (Market Discovery) Execution")
    print("================================================================")

    system_prompt_path = REPO_ROOT / "pipeline" / "gtm_engine" / "prompts" / "system_prompt.md"
    system_prompt = system_prompt_path.read_text(encoding="utf-8")

    user_prompt = "PHASE: 1\nSCOPE: full market universe\nPRIOR_STATE: none"

    t0 = time.time()
    try:
        raw_response = call_flash(system_prompt, user_prompt)
    except Exception as e:
        print(f"❌ Error invoking Flash tier model: {e}")
        sys.exit(1)

    duration = time.time() - t0
    print(f"✅ Received response in {duration:.2f}s ({len(raw_response)} characters)")

    # Parse JSON
    try:
        envelope = json.loads(raw_response)
    except json.JSONDecodeError as e:
        # Strip markdown fences if present
        clean_text = raw_response.strip()
        if clean_text.startswith("```json"):
            clean_text = clean_text[7:]
        if clean_text.startswith("```"):
            clean_text = clean_text[3:]
        if clean_text.endswith("```"):
            clean_text = clean_text[:-3]
        clean_text = clean_text.strip()
        envelope = json.loads(clean_text)

    # Save raw output
    output_dir = REPO_ROOT / "pipeline" / "gtm_engine" / "registry"
    output_dir.mkdir(parents=True, exist_ok=True)
    raw_path = output_dir / "phase_1_raw_output.json"
    raw_path.write_text(json.dumps(envelope, indent=2), encoding="utf-8")
    print(f"💾 Raw envelope saved to: {raw_path}")

    # Step 4: Run assertions against this real output
    print("\n----------------------------------------------------------------")
    print("🔍 Running Assertion Suite against Real Phase 1 Output...")
    print("----------------------------------------------------------------")

    results = run_all_assertions(envelope, check_live_urls=True)

    print(f"Phase: {results['phase']}")
    print(f"Passed: {results['passed']}")
    print(f"Total Violations: {results['total_violations']}")
    print(f"Summary: {json.dumps(results['summary'], indent=2)}")
    print(f"UNKNOWN Rate: {results['unknown_rate']:.1%}")
    if results["url_metrics"]:
        print(f"URL Metrics: {json.dumps(results['url_metrics'], indent=2)}")

    if results["violations"]:
        print("\nViolations List:")
        for v in results["violations"]:
            print(f"  • [{v['layer']}] {v['rule']}: {v['message']}")

    # Save assertion report
    report_path = output_dir / "phase_1_assertion_report.json"
    report_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"💾 Assertion report saved to: {report_path}")

    return 0 if results["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
