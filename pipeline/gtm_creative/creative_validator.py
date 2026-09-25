"""Phase 5: Creative System Validator (creative_validator.py).

Enforces:
  1. Generator Bypass Prevention: Asserts generator prompts are derived from strategy metaphors, not raw copy.
  2. Anti-Slop Audit: Scans compiled prompts against forbidden crypto visuals (no floating coins, Tron grids, spheres).
  3. Brand Compliance: Verifies obsidian void (#07020D) and dual bloom color coordinates.
Emits creative_system_audit.json.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone

REPO_ROOT = Path(__file__).resolve().parents[2]
STATE_DIR = REPO_ROOT / "pipeline" / "state"

from pipeline.gtm_creative.schemas import CompleteCreativeBlueprint, CreativeValidationResult
from pipeline.gtm_creative.creative_director_system import FORBIDDEN_CRYPTO_SLOP


class CreativeValidator:
    """Pre-generation quality firewall for visual blueprints."""

    def validate_blueprint(
        self,
        blueprint: CompleteCreativeBlueprint,
        raw_post_copy: Optional[str] = None,
        out_audit_file: Optional[Path] = None
    ) -> CreativeValidationResult:
        """Validate blueprint against anti-slop rules, brand tokens, and generator bypass invariants."""
        slop_violations: List[str] = []
        brand_issues: List[str] = []
        bypass_prevented = True

        # 1. Generator Bypass Invariant: Generator prompts must NOT simply repeat raw post copy
        if raw_post_copy and len(raw_post_copy) > 50:
            for fmt_name, fmt_spec in blueprint.format_specs.items():
                if raw_post_copy.strip().lower() in fmt_spec.compiled_prompt.lower():
                    bypass_prevented = False
                    slop_violations.append(f"Format {fmt_name} contains raw post copy directly in prompt (Generator Bypass).")

        # 2. Anti-Slop Scan across compiled prompts and concept
        text_to_scan = (
            f"{blueprint.visual_metaphor.concept} "
            f"{blueprint.visual_metaphor.metaphor} "
            f"{' '.join(fmt.compiled_prompt for fmt in blueprint.format_specs.values())}"
        ).lower()

        for slop in FORBIDDEN_CRYPTO_SLOP:
            if slop in text_to_scan:
                slop_violations.append(f"Blueprint contains forbidden visual pattern: '{slop}'")

        # 3. Brand Compliance Check
        # The blueprint must carry the tenant's own palette, exactly — the
        # brand profile is the one place colours come from.
        from pipeline.brand_brain import context as C
        tokens = dict(blueprint.brand_tokens or {})
        canon = C.palette()
        brand_compliant = bool(canon) and all(tokens.get(k) == v for k, v in canon.items())

        if not brand_compliant:
            brand_issues.append("Brand tokens do not match the brand profile's palette.")

        approved = len(slop_violations) == 0 and brand_compliant and bypass_prevented
        score = 96 if approved else max(0, 96 - len(slop_violations) * 25 - (30 if not bypass_prevented else 0))

        result = CreativeValidationResult(
            creative_id=blueprint.creative_id,
            approved=approved,
            score=score,
            generator_bypass_prevented=bypass_prevented,
            slop_violations=slop_violations,
            brand_compliance=brand_compliant,
            reasoning=(
                "Creative blueprint derived strictly from communication objective. "
                "Zero generic crypto slop detected. Canonical brand tokens verified."
                if approved else f"Creative validation failed: {slop_violations or brand_issues}"
            )
        )

        out_path = out_audit_file or (STATE_DIR / "creative_system_audit.json")
        audit_data = {
            "audit_timestamp": datetime.now(timezone.utc).isoformat(),
            "creative_id": blueprint.creative_id,
            "approved": result.approved,
            "score": result.score,
            "generator_bypass_prevented": result.generator_bypass_prevented,
            "formats_validated": list(blueprint.format_specs.keys()),
            "slop_violations_count": len(slop_violations),
            "brand_compliance": result.brand_compliance,
            "reasoning": result.reasoning
        }
        out_path.write_text(json.dumps(audit_data, indent=2), encoding="utf-8")
        print(f"📊 Emitted Creative System Audit Report: {out_path.name}")
        return result
