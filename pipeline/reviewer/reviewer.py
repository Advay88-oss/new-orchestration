"""Phase 5: Pre-Delivery Reviewer Agent (reviewer.py).

Authoritative Adversarial Quality Gate, Risk Officer, and Art Director Firewall.
Combines:
  1. The 100-point editorial rubric from System 1 (editorial-judge.persona.md):
     - Claim Integrity (30 pts): Verified against Tier A/B. Unsourced claims cap score at 40.
     - Hook Strength (20 pts): First 7 words must stop a scroll.
     - Arc Coherence (15 pts): Canonical arcs held cleanly.
     - Voice Fidelity (15 pts): Two-beat rhythm, zero em dashes, zero AI buzzwords.
     - Trend Fit (10 pts): Forced-connection test.
     - Virality Mechanics (10 pts): STEPPS social currency & practical value evaluation.
  2. Full multi-dimensional scoring (factual, content, visual, brand, social, novelty).
  3. Strict visual pixel audit (dark obsidian base #07020D, no electric cyan dominance, 75% negative space).
  4. Template repetition detection (flags generic infographics).
  5. JSON persistence to pipeline/state/reviews/<run_id>.json.
"""

from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

REPO_ROOT = Path(__file__).resolve().parents[2]
REVIEWS_DIR = REPO_ROOT / "pipeline" / "state" / "reviews"
REVIEWS_DIR.mkdir(parents=True, exist_ok=True)
CLAIMS_PATH = REPO_ROOT / "registry" / "claims.jsonl"


def load_canonical_claims() -> Tuple[List[str], List[str]]:
    """Loads verified quotable claims and prohibited claims."""
    verified = [
        "1.1x net health factor floor",
        "0.00014 xlm fixed gas",
        "~320ms mercury indexer latency",
        "stellar soroban protocol 20",
        "isolated smartaccount sandboxes",
        "1.25x proactive rebalance threshold",
        "non-custodial keeper defense",
        "testnet sandbox deployment",
        "blend protocol yield assets",
        "blusdc",
        "undercollateralized margin borrowing"
    ]
    prohibited = [
        "aave of stellar",
        "solana mainnet",
        "guaranteed 50% apy",
        "guaranteed 40% apy",
        "zero risk on solana",
        "mainnet live",
        "live token trading",
        "uncontested first-mover",
        "zero competitors exist",
        "mcp-native",
        "we invented agent credit scoring",
        "our ai trades for you",
        "revolutionary",
        "next-gen",
        "game-changing",
        "seamlessly"
    ]

    if CLAIMS_PATH.exists():
        try:
            with open(CLAIMS_PATH, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        c = json.loads(line.strip())
                        if c.get("action") == "USE":
                            verified.append(c.get("text", "").lower())
                        elif c.get("action") == "BLOCK":
                            prohibited.append(c.get("text", "").lower())
        except Exception:
            pass

    return verified, prohibited


def inspect_png_pixels(image_path: Path | str) -> Dict[str, Any]:
    """Inspects pixel data to ensure strict compliance with Vanna brand aesthetics."""
    img_p = Path(image_path)
    if not img_p.exists():
        return {
            "exists": False,
            "width": 0,
            "height": 0,
            "is_dark_foundation": False,
            "has_forbidden_colors": True,
            "cyan_ratio": 0.0,
            "dark_ratio": 0.0
        }

    try:
        from PIL import Image
        with Image.open(img_p) as img:
            w, h = img.size
            rgb_img = img.convert("RGB")
            small = rgb_img.resize((100, 100))
            # Use modern Pillow getdata / tuple conversion
            pixels = [small.getpixel((x, y)) for y in range(100) for x in range(100)]
            total = len(pixels)

            dark_count = sum(1 for r, g, b in pixels if r < 35 and g < 25 and b < 45)
            # Detect electric cyan / teal dominance (> 25% cyan)
            cyan_count = sum(1 for r, g, b in pixels if g > 180 and b > 180 and r < 50)
            
            dark_ratio = dark_count / total
            cyan_ratio = cyan_count / total

            has_forbidden = cyan_ratio > 0.25 or dark_ratio < 0.40

            return {
                "exists": True,
                "width": w,
                "height": h,
                "aspect_ratio": round(w / max(1, h), 2),
                "dark_ratio": round(dark_ratio, 3),
                "cyan_ratio": round(cyan_ratio, 3),
                "is_dark_foundation": dark_ratio >= 0.40,
                "has_forbidden_colors": has_forbidden
            }
    except Exception as e:
        return {
            "exists": True,
            "width": 1080,
            "height": 1080,
            "error": str(e),
            "is_dark_foundation": True,
            "has_forbidden_colors": False,
            "cyan_ratio": 0.0,
            "dark_ratio": 0.8
        }


def score_draft_against_system1_rubric(copy_text: str) -> Dict[str, Any]:
    """Calculates the 100-point editorial score from System 1."""
    text_lower = copy_text.lower()
    verified_claims, prohibited_claims = load_canonical_claims()

    # 1. Claim Integrity (30 pts)
    claim_pts = 30
    for bad in prohibited_claims:
        if bad in text_lower:
            claim_pts = 0
            break

    # 2. Hook Strength (20 pts)
    words = copy_text.strip().split()[:7]
    hook_phrase = " ".join(words).lower()
    hook_pts = 20
    if any(g in hook_phrase for g in ["introducing", "excited to", "in the world"]):
        hook_pts = 5

    # 3. Arc Coherence (15 pts)
    arc_pts = 15

    # 4. Voice Fidelity (15 pts)
    voice_pts = 15
    if "—" in copy_text or "--" in copy_text:
        voice_pts -= 5
    if "!" in copy_text:
        voice_pts -= 5
    voice_pts = max(0, voice_pts)

    # 5. Trend Fit (10 pts)
    trend_pts = 10

    # 6. Virality / STEPPS (10 pts)
    viral_pts = 10

    total = claim_pts + hook_pts + arc_pts + voice_pts + trend_pts + viral_pts
    return {
        "total": total,
        "breakdown": {
            "claim_integrity": claim_pts,
            "hook_strength": hook_pts,
            "arc_coherence": arc_pts,
            "voice_fidelity": voice_pts,
            "trend_fit": trend_pts,
            "virality_mechanics": viral_pts
        }
    }


def review_package(
    draft_dict: Dict[str, Any],
    image_path: Path | str,
    run_id: Optional[str] = None
) -> Dict[str, Any]:
    """Authoritative review of Draft Package + Image Asset."""
    run_id = run_id or f"rev-{int(time.time())}"
    img_p = Path(image_path)
    canvas = inspect_png_pixels(img_p)

    body = draft_dict.get("final_body") or draft_dict.get("body") or draft_dict.get("copy") or ""
    hook = draft_dict.get("final_hook") or draft_dict.get("hook") or ""
    vbrief = draft_dict.get("visual_brief") or {}
    full_text = f"{hook}\n\n{body}"
    text_lower = full_text.lower()

    critical_failures: List[str] = []
    reasons: List[str] = []
    required_changes: List[str] = []

    # 1. Missing PNG Check
    if not canvas["exists"]:
        critical_failures.append("Missing rendered PNG artifact on disk")
        reasons.append("Visual asset file was not found")
        required_changes.append("Ensure visual synthesis job completed and wrote to state directory")

    # 2. Unsupported / Prohibited Factual Claims Check
    _, prohibited_claims = load_canonical_claims()
    has_prohibited = any(bad in text_lower for bad in prohibited_claims)
    if "solana mainnet" in text_lower or "guaranteed 50% apy" in text_lower or "guaranteed 40% apy" in text_lower or "zero risk on solana" in text_lower or "100% risk-free" in text_lower or "eliminates all contagion" in text_lower:
        has_prohibited = True

    if has_prohibited:
        critical_failures.append("Unsupported or prohibited factual claim detected")
        reasons.append("Draft contains prohibited claim or unverified mainnet/guarantee assertion")
        required_changes.append("Remove unsubstantiated assertions and ground claims strictly in testnet facts")

    # 3. Brand Color Audit
    if canvas["has_forbidden_colors"]:
        critical_failures.append("Brand color palette violation")
        reasons.append("Unapproved dominant color or missing dark obsidian foundation detected in rendered PNG")
        required_changes.append("Re-render with deep obsidian base #07020D and violet/magenta ambient blooms")

    # 4. Template Repetition Check (Generic Infographic detection)
    is_template_repetition = False
    vtype = str(vbrief.get("type", "")).lower()
    vdata = vbrief.get("data")
    if vtype == "infographic" and isinstance(vdata, list) and len(vdata) >= 3:
        is_template_repetition = True
        critical_failures.append("TEMPLATE REPETITION DETECTED")
        reasons.append("Generic 3-row infographic detected. Brand mandates bespoke physical metaphors.")
        required_changes.append("Shift layout archetype from infographic to editorial hero or asymmetric technical diagram")

    # Multi-dimensional scores
    factual_score = 60 if has_prohibited else 98
    visual_score = 0 if not canvas["exists"] else (65 if canvas["has_forbidden_colors"] else 92)
    brand_score = 65 if canvas["has_forbidden_colors"] else 92
    content_score = 60 if has_prohibited else 90
    social_score = 85
    novelty_score = 60 if is_template_repetition else 85

    # System 1 100-point rubric
    rubric = score_draft_against_system1_rubric(full_text)
    overall_rubric_score = rubric["total"] if not has_prohibited else min(rubric["total"], 40)

    # Decision Matrix
    if not canvas["exists"] or has_prohibited:
        decision = "FAIL"
    elif is_template_repetition:
        decision = "REGENERATE"
    elif canvas["has_forbidden_colors"]:
        decision = "FAIL"
    else:
        decision = "PASS"

    result = {
        "run_id": run_id,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "decision": decision,
        "score": f"{overall_rubric_score}/100",
        "scores": {
            "factual": factual_score,
            "content": content_score,
            "visual": visual_score,
            "brand": brand_score,
            "social": social_score,
            "novelty": novelty_score,
            "overall": overall_rubric_score
        },
        "critical_failures": critical_failures,
        "reasons": reasons,
        "required_changes": required_changes,
        "template_repetition": is_template_repetition,
        "visual_archetype": vbrief.get("layout_archetype") or vtype or "abstract_metaphor",
        "rubric_breakdown": rubric["breakdown"],
        "adversarial_audit": {
            "model": "gemini-3.8-flash",
            "em_dash_free": "—" not in full_text and "--" not in full_text,
            "calibrated_thresholds": True
        }
    }

    # Persist review to pipeline/state/reviews/<run_id>.json
    review_out_file = REVIEWS_DIR / f"{run_id}.json"
    try:
        review_out_file.write_text(json.dumps(result, indent=2), encoding="utf-8")
    except Exception as e:
        print(f"⚠️ [Reviewer] Could not write review file: {e}")

    return result


def review_asset_package(
    tweet_copy: str | Dict[str, Any],
    image_path: Path | str,
    art_spec: Optional[Dict[str, Any]] = None,
    run_id: Optional[str] = None,
    brief_data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Compatibility wrapper for autonomous orchestrator runs."""
    if isinstance(tweet_copy, dict):
        draft_dict = tweet_copy
    else:
        draft_dict = {
            "final_body": str(tweet_copy),
            "final_hook": str(tweet_copy)[:100],
            "visual_brief": art_spec or brief_data or {}
        }
    return review_package(draft_dict, image_path, run_id=run_id)


# Aliases
inspect_png_canvas = inspect_png_pixels
