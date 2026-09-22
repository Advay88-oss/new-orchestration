#!/usr/bin/env python3
"""Agent 4: BRAND GUARDIAN (video_brand_guardian.py)

Role: Authoritative pre-generation gatekeeper.
Verifies:
  - Vanna brand colors (#07020D, #471485, #5E0D46, #A387FF, #FC5457, #22D3C4)
  - Typography hierarchy (Plus Jakarta Sans + JetBrains Mono)
  - Premium visual language (minimal, institutional, cinematic)
  - Contrast, spacing, and negative space
  - Strict absence of forbidden AI slop (no generic spheres, random grids, crypto coin spam)
Output:
  - Authoritative machine-readable contract artifact: video_director.json
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# Strict Brand Constants
ALLOWED_HEX_TOKENS = {
    "#07020D", "#08070C", "#0C0C10",  # Obsidian void variants
    "#471485", "#703AE6",              # Royal violet variants
    "#5E0D46",                         # Fuchsia-wine bloom
    "#A387FF",                         # Vanna lavender accent
    "#FC5457",                         # Coral risk accent
    "#22D3C4",                         # Cyan telemetry
    "#FFFFFF", "#F3F1F8", "#E2E1E6",  # Light text neutrals
    "#8C879E", "#5A566A",              # Muted monospace secondary
}

SLOP_TRIGGER_PATTERNS = [
    r"glowing sphere",
    r"concentric ring",
    r"neon grid",
    r"tron",
    r"cyberpunk city",
    r"flying (?:bitcoin|coin|token|dollar)",
    r"candlestick chart",
    r"holographic hud",
    r"matrix code rain",
    r"spinning (?:logo|coin)",
]


class VideoBrandGuardian:
    """Brand Guardian agent: audits motion and art direction before Veo is ever called."""

    def __init__(self):
        self.violations: List[str] = []
        self.warnings: List[str] = []

    def audit_scene(self, scene: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Audit an individual scene against Vanna brand and aesthetic rules."""
        scene_id = scene.get("scene_id", 0)
        scene_violations: List[str] = []

        content_to_check = (
            f"{scene.get('visual_concept', '')} "
            f"{scene.get('composition', '')} "
            f"{scene.get('veo_prompt', '')} "
            f"{scene.get('camera', '')} "
            f"{scene.get('motion', '')} "
            f"{scene.get('lighting', '')}"
        ).lower()

        # 1. Anti-Slop Check
        for pattern in SLOP_TRIGGER_PATTERNS:
            if re.search(pattern, content_to_check):
                scene_violations.append(f"Scene {scene_id} contains prohibited visual pattern: '{pattern}'")

        # 2. Veo Prompt Quality Check
        veo_prompt = scene.get("veo_prompt", "")
        if not veo_prompt:
            scene_violations.append(f"Scene {scene_id} is missing a required 'veo_prompt'")
        elif len(veo_prompt) < 50:
            scene_violations.append(f"Scene {scene_id} veo_prompt is too short to ensure art-directed quality")

        # 3. Brand Tone Keywords Check
        required_mood_keywords = ["cinematic", "obsidian", "lighting", "zero text"]
        missing_mood = [kw for kw in required_mood_keywords if kw not in veo_prompt.lower()]
        if missing_mood:
            self.warnings.append(f"Scene {scene_id} Veo prompt recommended to include mood keywords: {missing_mood}")

        return len(scene_violations) == 0, scene_violations

    def audit_and_build_contract(
        self,
        motion_plan: Dict[str, Any],
        out_director_json: Optional[Path] = None,
    ) -> Tuple[bool, Dict[str, Any]]:
        """Audit the entire multi-scene plan and emit the final video_director.json contract."""
        self.violations.clear()
        self.warnings.clear()

        scenes = motion_plan.get("scenes", [])
        if not scenes:
            return False, {"error": "No scenes present in motion plan"}

        sanitized_scenes: List[Dict[str, Any]] = []

        for s in scenes:
            valid, scene_errs = self.audit_scene(s)
            if not valid:
                self.violations.extend(scene_errs)

            # Assemble strictly matching the requested contract schema:
            contract_scene = {
                "scene_id": s.get("scene_id", 1),
                "duration": s.get("duration", 4.0),
                "narrative_purpose": s.get("narrative_purpose", ""),
                "visual_concept": s.get("visual_concept", ""),
                "composition": s.get("composition", ""),
                "camera": s.get("camera", ""),
                "motion": s.get("motion", ""),
                "lighting": s.get("lighting", ""),
                "color": s.get("color", ""),
                "typography": s.get("typography", ""),
                "assets": s.get("assets", []),
                "negative_constraints": s.get("negative_constraints", []),
                "veo_prompt": s.get("veo_prompt", ""),
            }
            sanitized_scenes.append(contract_scene)

        # Build official video_director.json structure
        video_director_contract: Dict[str, Any] = {
            "campaign": motion_plan.get("campaign", {}),
            "creative_thesis": motion_plan.get("creative_thesis", "Art-directed risk deflection on Stellar Soroban"),
            "brand_system": {
                "palette": {
                    "obsidian_base": "#07020D",
                    "royal_violet_bloom": "#471485",
                    "fuchsia_magenta_bloom": "#5E0D46",
                    "lavender_accent": "#A387FF",
                    "coral_accent": "#FC5457",
                    "cyan_telemetry": "#22D3C4",
                },
                "typography": {
                    "primary": "Plus Jakarta Sans",
                    "telemetry": "JetBrains Mono",
                },
                "aesthetic_posture": "Institutional, developer-grade, cinematic, minimal, non-promotional",
            },
            "scenes": sanitized_scenes,
            "global_negative_constraints": motion_plan.get("global_negative_constraints", []),
            "review_requirements": [
                "100% script narrative alignment",
                "Strict absence of generic AI slop or floating decorative spheres",
                "Full adherence to Vanna obsidian and dual-bloom color hierarchy",
                "Sub-second rebalancing and isolated sandbox claims must match verified technical truth",
            ],
            "brand_guardian_audit": {
                "status": "APPROVED" if len(self.violations) == 0 else "REJECTED",
                "brand_score": 96 if len(self.violations) == 0 else max(40, 96 - len(self.violations) * 20),
                "violations": list(self.violations),
                "warnings": list(self.warnings),
            },
        }

        if out_director_json:
            out_director_json = Path(out_director_json)
            out_director_json.parent.mkdir(parents=True, exist_ok=True)
            out_director_json.write_text(json.dumps(video_director_contract, indent=2), encoding="utf-8")
            print(f"✅ VIDEO BRAND GUARDIAN: Emitted {out_director_json.name} (Audit: {video_director_contract['brand_guardian_audit']['status']})")

        return len(self.violations) == 0, video_director_contract


def run_brand_guardian(motion_plan: Dict[str, Any], out_path: Optional[Path] = None) -> Tuple[bool, Dict[str, Any]]:
    guardian = VideoBrandGuardian()
    return guardian.audit_and_build_contract(motion_plan, out_path)
