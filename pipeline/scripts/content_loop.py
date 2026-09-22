#!/usr/bin/env python3
"""Loop B — Content: Asymmetric Writer + Skeptic Swarm.

Replaces the 3-strategist stylistic debate with two asymmetric agents:
1. WRITER (Strong tier): Has the brief, dynamically loads verified claims from registry.
2. SKEPTIC (Strong tier): Has the claim registry but NOT the brief.
   Judges draft against full verified and prohibited claims list, catching promotional upgrades.
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

REPO_ROOT = Path(os.environ.get("VANNA_ROOT", Path(__file__).resolve().parents[2]))
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

REGISTRY_DIR = REPO_ROOT / "registry"
CLAIMS_FILE = REGISTRY_DIR / "claims.jsonl"

from pipeline.scripts.render_visual import render as render_visual_card
from pipeline.scripts.runtime_assertions import assert_l0_schema, assert_l1_invariants

TEMPLATE_SELECTION = {
    "TRUST_RISK": "single_stat",
    "METRICS_PROOF": "single_stat",
    "EDUCATION": "architecture",
    "PRODUCT": "architecture",
    "NARRATIVE_THESIS": "statement",
    "ECOSYSTEM": "statement",
}


def is_rejected(skeptic_review: Dict[str, Any]) -> bool:
    """Allowlist check: only literal 'PASS' passes. Any missing key, typo, or challenge rejects."""
    return skeptic_review.get("verdict") != "PASS"


def extract_json(text: str, agent: str) -> dict:
    """Safe JSON extraction that guards against unhandled crashes on raw prose."""
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if not m:
        raise ValueError(f"{agent} returned no JSON object. First 200 chars: {text[:200]!r}")
    try:
        return json.loads(m.group(0))
    except json.JSONDecodeError as e:
        raise ValueError(f"{agent} returned malformed JSON: {e}")


def load_claims() -> Tuple[List[str], List[str]]:
    """Loads full structured claims registry without truncation."""
    if not CLAIMS_FILE.exists():
        return [], []
    claims = [json.loads(l) for l in CLAIMS_FILE.open(encoding="utf-8") if l.strip()]
    verified = [c["claim"] for c in claims if c.get("tier") == "VERIFIED"]
    prohibited = [c["claim"] for c in claims if c.get("tier") in ("RETIRED", "PROHIBITED")]
    return verified, prohibited


def run_content_loop(
    brief: Dict[str, Any],
    call_model_fn,
    human_approved: bool = True
) -> Dict[str, Any]:
    """Executes Loop B with asymmetric writer and skeptic, tracking call metrics."""
    assert_l0_schema(brief, record_type="brief")
    
    if not human_approved:
        return {"status": "HALTED_AT_HUMAN_CHECKPOINT", "brief": brief}

    model_calls = 0
    revision_used = False

    # FIX 1: Writer prompt claims registry se le, hardcode se nahi
    verified, prohibited = load_claims()
    writer_system = (
        "You are the Senior Technical Writer for Vanna Protocol.\n"
        "Your goal is clarity, precision, and strict pattern fidelity.\n"
        "Ground every sentence strictly in these verified claims only. Do not upgrade 'isolate' to 'eliminate' or add causal claims:\n" +
        "\n".join(f"- {c}" for c in verified) +
        "\n\nForbidden claims (never write):\n" +
        "\n".join(f"- {c}" for c in prohibited)
    )

    writer_prompt = f"""Write a compelling single post or short thread based on this verified brief:

{json.dumps(brief, indent=2)}

Format your response as clean JSON:
{{
  "headline": "...",
  "post_text": "...",
  "visual_brief": {{
    "content_category": "{brief.get('content_category', 'TRUST_RISK')}",
    "headline": "{brief.get('headline', '')}",
    "hero": {{ "value": "{brief.get('hero_value', '1.10x')}", "label": "{brief.get('hero_label', 'HEALTH FACTOR FLOOR')}" }},
    "support": "{brief.get('support', '')}",
    "footer": "docs.vanna.finance"
  }}
}}
"""
    print("▶ Running Writer Agent...")
    writer_raw = call_model_fn(writer_system, writer_prompt, tier="strong")
    model_calls += 1
    draft = extract_json(writer_raw, "writer")

    # 2. SKEPTIC AGENT (Has full claim registry, but DOES NOT HAVE THE BRIEF)
    skeptic_system = """You are the Lead Risk Skeptic for Vanna Protocol.
You do NOT care about marketing tone or style.
Your ONLY objective is finding unsupported, speculative, or prohibited claims.
You possess Vanna's verified facts ledger.
Scrutinize promotional upgrades: if the registry says 'provides isolated sandboxes', flag any draft that claims to 'eliminate contagion' or makes absolute guarantees.
"""
    skeptic_prompt = (
        "VERIFIED CLAIMS (only these may be stated plainly):\n" + "\n".join(f"- {c}" for c in verified) +
        "\n\nPROHIBITED CLAIMS (never publishable):\n" + "\n".join(f"- {c}" for c in prohibited) +
        f"\n\nDRAFT:\nHeadline: {draft.get('headline')}\nPost Copy:\n{draft.get('post_text')}\n\n"
        'Return JSON: {"verdict": "PASS"|"CHALLENGE", "unsupported_sentences": [...], "fix_required": "..."}'
    )
    print("▶ Running Skeptic Agent (Asymmetric — no brief provided)...")
    skeptic_raw = call_model_fn(skeptic_system, skeptic_prompt, tier="strong")
    model_calls += 1
    skeptic_review = extract_json(skeptic_raw, "skeptic")

    if is_rejected(skeptic_review):
        revision_used = True
        print(f"⚠️ Skeptic Challenge: {skeptic_review.get('unsupported_sentences')}")
        print("▶ Running Revision Pass with Skeptic Feedback...")
        revision_prompt = f"""The Risk Skeptic challenged the following claims in your draft:
{json.dumps(skeptic_review.get('unsupported_sentences'), indent=2)}

Skeptic feedback: {skeptic_review.get('fix_required', 'Remove unverified assertions and ground strictly in verified mechanisms.')}

Original Draft:
{json.dumps(draft, indent=2)}

Rewrite the post so every sentence is 100% verified and strictly answers the skeptic. Output clean JSON only.
"""
        revised_raw = call_model_fn(writer_system, revision_prompt, tier="strong")
        model_calls += 1
        draft = extract_json(revised_raw, "writer")

        # Re-check revised draft with Skeptic
        skeptic_prompt = (
            "VERIFIED CLAIMS (only these may be stated plainly):\n" + "\n".join(f"- {c}" for c in verified) +
            "\n\nPROHIBITED CLAIMS (never publishable):\n" + "\n".join(f"- {c}" for c in prohibited) +
            f"\n\nREVISED DRAFT:\nHeadline: {draft.get('headline')}\nPost Copy:\n{draft.get('post_text')}\n\n"
            'Return JSON: {"verdict": "PASS"|"CHALLENGE", "unsupported_sentences": [...], "fix_required": "..."}'
        )
        print("▶ Running Skeptic Verification on Revised Draft...")
        skeptic_raw = call_model_fn(skeptic_system, skeptic_prompt, tier="strong")
        model_calls += 1
        skeptic_review = extract_json(skeptic_raw, "skeptic")

        if is_rejected(skeptic_review):
            print(f"❌ Final Skeptic Rejection: {skeptic_review.get('unsupported_sentences')}")
            return {
                "status": "REJECTED_BY_SKEPTIC",
                "draft": draft,
                "verdict": skeptic_review.get("verdict"),
                "reasons": skeptic_review.get("unsupported_sentences", []),
                "fix": skeptic_review.get("fix_required"),
                "model_calls": model_calls,
                "revision_used": revision_used
            }
        print("✅ Skeptic PASS on revised draft!")

    # 3. Deterministic Claim Gate
    assert_l1_invariants(draft.get("post_text", ""))

    # 4. Deterministic Template Select (Dict lookup)
    category = brief.get("content_category", "TRUST_RISK")
    selected_template = TEMPLATE_SELECTION.get(category, "single_stat")
    print(f"▶ Deterministic Template Selected: {selected_template} for category {category}")

    # 5. Deterministic Visual Render
    v_brief = draft.get("visual_brief", {})
    image_path = REPO_ROOT / "pipeline" / "state" / "temp_rendered.png"
    render_visual_card(v_brief, image_path, forced_layout=selected_template)

    return {
        "status": "READY_FOR_TELEGRAM",
        "draft": draft,
        "template": selected_template,
        "image_path": str(image_path),
        "skeptic_verdict": "PASS",
        "model_calls": model_calls,
        "revision_used": revision_used
    }
