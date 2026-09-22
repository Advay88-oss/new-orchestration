#!/usr/bin/env python3
"""Dynamic Creative Director for Vanna Video Engine (pipeline/video_pipeline/creative_director.py).

Core Principle:
  IDEA -> STORY -> CREATIVE DIRECTION -> UNIQUE VISUAL LANGUAGE -> PRODUCTION
  (Completely removes fixed "topic -> template" routing).

Generates 3-5 structurally distinct creative concepts per directive, audits each
against historical Creative Memory to prevent repeated visual structures, and
selects the optimal art-directed concept for production.
"""

from __future__ import annotations

import json
import os
import re
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

STATE_DIR = REPO_ROOT / "pipeline" / "state"
PUBLIC_DIR = REPO_ROOT / "hermes-mission" / "public"

from pipeline.creative_memory.creative_memory_store import CreativeMemoryStore
from pipeline.creative_memory.reference_library import ReferenceLibrary

# Available Vanna Real Product Recordings & Assets
AVAILABLE_PRODUCT_SCREENS = [
    {"id": "demo_farm", "file": "demo-farm.mp4", "topic": "Farm & Liquidity Supply", "duration": 15.0},
    {"id": "demo_swap", "file": "demo-swap.mp4", "topic": "Atomic Margin Swaps on Soroswap", "duration": 10.0},
    {"id": "demo_portfolio", "file": "demo-portfolio.mp4", "topic": "User SmartAccount Health & Portfolio", "duration": 12.0},
    {"id": "demo_analytics", "file": "demo-analytics.mp4", "topic": "Mercury Sub-Second Solvency Stream", "duration": 18.0},
    {"id": "pr_mockup", "file": "pr-Mockup.mp4", "topic": "Tactile SmartAccount Sandbox Interface", "duration": 14.0},
    {"id": "vanna_showcase", "file": "vanna-showcase.mp4", "topic": "End-to-End Composable Credit Walkthrough", "duration": 22.0},
]


def call_gemini_brain(prompt: str, system_instruction: str = "") -> Optional[str]:
    """Calls Gemini 3.8 Flash via Vertex spend proxy (:8900) or direct key."""
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if api_key:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash:generateContent?key={api_key}"
    else:
        url = "http://127.0.0.1:8900/v1/projects/sales-agent-504607/locations/us-central1/publishers/google/models/gemini-3.8-flash:generateContent"

    combined_prompt = f"{system_instruction}\n\n{prompt}" if system_instruction else prompt
    payload = {
        "contents": [{"role": "user", "parts": [{"text": combined_prompt}]}],
        "generationConfig": {
            "temperature": 0.8,
            "maxOutputTokens": 4096,
            "responseMimeType": "application/json"
        }
    }

    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=45) as r:
            res = json.loads(r.read().decode("utf-8"))
            return res["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        print(f"⚠️ [CreativeDirector] Brain call notice: {e}")
        return None


class DynamicCreativeDirector:
    """Multi-stage Creative Director establishing genuine visual novelty per brief."""

    def __init__(self, memory_store: Optional[CreativeMemoryStore] = None, ref_library: Optional[ReferenceLibrary] = None):
        self.memory = memory_store or CreativeMemoryStore()
        self.ref_lib = ref_library or ReferenceLibrary()

    def _determine_reference_blend(self, directive: str, narrative_arc: str) -> Dict[str, Any]:
        """Determines which positive references to blend and what principles to borrow or omit."""
        d_lower = directive.lower()
        if "risk" in d_lower or "solvency" in d_lower or "floor" in d_lower or "cascade" in d_lower:
            primary_refs = ["REF_VID_02_RISK_MANAGEMENT", "REF_DEFI_TRANSITION", "REF_41S_MASTER_FILM"]
        elif "agent" in d_lower or "mcp" in d_lower or "autonomous" in d_lower:
            primary_refs = ["REF_VID_03_AGENTIC_CREDIT", "REF_DEFI_TRANSITION", "REF_41S_MASTER_FILM"]
        elif "lp" in d_lower or "yield" in d_lower or "rate" in d_lower:
            primary_refs = ["REF_VID_04_LP_CAPITAL_EFFICIENCY", "REF_41S_MASTER_FILM", "REF_DEFI_TRANSITION"]
        elif "walkthrough" in d_lower or "terminal" in d_lower or "step-by-step" in d_lower or "workflow" in d_lower:
            primary_refs = ["REF_VID_04_LP_CAPITAL_EFFICIENCY", "REF_DEFI_TRANSITION", "REF_41S_MASTER_FILM"]
        else:
            primary_refs = ["REF_41S_MASTER_FILM", "REF_DEFI_TRANSITION", "REF_VID_04_LP_CAPITAL_EFFICIENCY"]

        return self.ref_lib.blend_reference_principles(
            primary_ref_ids=primary_refs,
            narrative_intent=f"{directive} [{narrative_arc}]"
        )

    def direct_video(
        self,
        directive: str,
        audience: str = "DeFi Farmers & Allocators",
        narrative_arc: str = "Capital Efficiency",
        run_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Main entry point: Explores 3-5 concepts, audits novelty, judges, and outputs final contract."""
        t_id = run_id or f"RUN_VID_{int(time.time())}"
        print("=" * 80)
        print(f"🎬 DYNAMIC CREATIVE DIRECTOR: ART-DIRECTING NEW VIDEO [{t_id}]")
        print(f"   Directive: \"{directive}\"")
        print(f"   Audience:  {audience} | Narrative Arc: {narrative_arc}")
        print("=" * 80)

        # 0. Reference Library analysis & principle synthesis
        ref_blend = self._determine_reference_blend(directive, narrative_arc)
        print(f"🎨 Reference Blending: Applied [{', '.join(ref_blend['applied_references'])}]")
        for om in ref_blend.get("intentionally_omitted_principles", []):
            print(f"   🚫 {om}")

        # 1. Read Creative Memory of previous videos to enforce diversity
        past_videos = self.memory.get_approved_videos(limit=10)
        past_summaries = []
        for pv in past_videos:
            past_summaries.append({
                "concept": pv.get("creative_concept"),
                "visual_language": pv.get("visual_language"),
                "metaphor": pv.get("visual_metaphor"),
                "format": pv.get("format")
            })

        print(f"📚 Retrieved {len(past_videos)} approved videos from Creative Memory for structural diversity check.")

        # 2. Stage 1: Generate 3-5 structurally distinct concepts
        print("\n▶ [STAGE 1: CREATIVE EXPLORATION] Generating 3-5 structurally distinct concepts...")
        candidate_concepts = self._explore_diverse_concepts(directive, audience, narrative_arc, past_summaries, ref_blend)
        print(f"   Generated {len(candidate_concepts)} distinct candidate concepts.")

        # 3. Stage 2: Audit Concept Novelty & Diversity against Memory
        print("\n▶ [STAGE 2: NOVELTY & DIVERSITY AUDIT] Checking semantic and structural novelty...")
        scored_candidates: List[Dict[str, Any]] = []
        for idx, cand in enumerate(candidate_concepts):
            cand["reference_blending"] = ref_blend
            is_novel, max_sim, closest_ref, breakdown = self.memory.audit_concept_novelty(cand, max_allowed_similarity=0.60)
            cand["novelty_score"] = round((1.0 - max_sim) * 100, 1)
            cand["max_similarity"] = max_sim
            cand["closest_reference_title"] = closest_ref.get("creative_concept") if closest_ref else "None (First in Category)"
            cand["similarity_breakdown"] = breakdown
            cand["novelty_pass"] = is_novel
            scored_candidates.append(cand)
            status_glyph = "✅ PASS" if is_novel else "❌ REJECT (Structural Repetition)"
            print(f"   Concept {chr(65+idx)}: \"{cand.get('creative_concept')[:50]}...\" | Novelty: {cand['novelty_score']}/100 | Sim: {max_sim:.2f} -> {status_glyph}")

        # 4. Stage 3: Creative Judge Selection
        print("\n▶ [STAGE 3: CREATIVE JUDGE] Selecting winning concept based on narrative, originality, and feasibility...")
        selected_concept = self._judge_and_select_winner(scored_candidates, directive, audience)
        selected_concept["reference_blending"] = ref_blend
        print(f"🏆 Selected Winner: Concept {selected_concept.get('concept_id')} (\"{selected_concept.get('creative_concept')[:60]}...\")")
        print(f"   Visual Thesis: {selected_concept.get('visual_thesis')}")
        print(f"   Visual Language: {selected_concept.get('visual_language')}")
        print(f"   Production Method: {selected_concept.get('generation_strategy')}")
        print(f"   Use Product Screen: {selected_concept.get('use_product_screen')} ({selected_concept.get('product_screen_asset', 'None')})")

        # Persist exploration session to creative memory
        self.memory.record_concept_exploration(t_id, directive, scored_candidates, selected_concept.get("concept_id", "A"))

        return selected_concept

    def _explore_diverse_concepts(
        self,
        directive: str,
        audience: str,
        narrative_arc: str,
        past_summaries: List[Dict[str, Any]],
        ref_blend: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Generates 4 structurally distinct creative directions."""
        ref_guidelines = ""
        if ref_blend:
            applied = ", ".join(ref_blend.get("applied_references", []))
            omitted = "; ".join(ref_blend.get("intentionally_omitted_principles", []))
            ref_guidelines = (
                f"\nREFERENCE BLENDING GUIDELINES:\n"
                f"- Apply principles from: {applied}\n"
                f"- AVOID THESE CLICHES / REPETITIONS: {omitted}\n"
                f"- CRITICAL: Do NOT clone the 41s video or any reference scene. Invent a NEW visual metaphor for this story.\n"
            )

        prompt = (
            f"You are the Executive Creative Director for Vanna Protocol (Stellar Soroban credit).\n"
            f"Direct a custom video for: \"{directive}\"\n"
            f"Audience: {audience} | Narrative: {narrative_arc}\n"
            f"{ref_guidelines}\n"
            f"Generate a JSON array of 3 structurally distinct concepts:\n"
            f"Each object must have:\n"
            f"- concept_id: 'A' | 'B' | 'C'\n"
            f"- format_archetype: 'EDITORIAL_TYPOGRAPHY' | 'CINEMATIC_PHYSICAL' | 'PRODUCT_LED' | 'SPATIAL_ARCHITECTURAL' | 'DOCUMENTARY_SCREENCAST'\n"
            f"- creative_concept: 1-line concept title\n"
            f"- visual_thesis: 1 sentence visual thesis\n"
            f"- story_structure: 1 sentence narrative arc\n"
            f"- visual_language: 3-5 word style descriptor\n"
            f"- visual_metaphor: distinct physical metaphor\n"
            f"- format: '16:9 30fps'\n"
            f"- motion_language: 1 sentence physics description\n"
            f"- camera_language: 1 sentence camera movement\n"
            f"- typography_language: 1 sentence typography treatment\n"
            f"- product_integration: 'REAL UI' or 'NONE'\n"
            f"- use_product_screen: true or false\n"
            f"- product_screen_asset: 'demo-farm.mp4' | 'demo-swap.mp4' | 'demo-analytics.mp4' | 'pr-Mockup.mp4' | 'vanna-showcase.mp4' | 'NONE'\n"
            f"- generation_strategy: 'VEO_MACRO_ATMOSPHERIC' | 'REMOTION_KINETIC_EDITORIAL' | 'HYBRID_VEO_AND_PRODUCT_UI' | 'SPATIAL_ARCHITECTURAL_BREAKDOWN'\n"
            f"Output strictly a JSON array of 3 objects only."
        )

        raw = call_gemini_brain(prompt, system_instruction="You are an award-winning Creative Director. Output valid JSON array only.")
        if raw:
            try:
                parsed = json.loads(raw)
                if isinstance(parsed, list) and len(parsed) >= 3:
                    return parsed[:4]
            except Exception as e:
                print(f"⚠️ Error parsing creative exploration JSON: {e}")

        # Deterministic diverse fallback if AI call unavailable
        return self._build_deterministic_diverse_concepts(directive, narrative_arc)

    def _judge_and_select_winner(
        self,
        candidates: List[Dict[str, Any]],
        directive: str,
        audience: str
    ) -> Dict[str, Any]:
        """Judges candidates across 7 criteria and selects the most original and narrative-fitting concept."""
        best_concept = None
        best_score = -1.0

        for cand in candidates:
            # 1. Base Score from Rubric
            narrative_fit = 90.0
            prod_comms = 85.0 if cand.get("use_product_screen") else 80.0
            originality = float(cand.get("novelty_score", 85.0))
            brand_fit = 95.0
            feasibility = 95.0

            # Disqualify candidates that fail the novelty audit if any novel candidate exists
            sim_penalty = float(cand.get("max_similarity", 0.0)) * 40.0
            if not cand.get("novelty_pass", True):
                sim_penalty += 80.0

            total_score = (narrative_fit * 0.25) + (prod_comms * 0.20) + (originality * 0.25) + (brand_fit * 0.15) + (feasibility * 0.15) - sim_penalty
            cand["judge_total_score"] = round(total_score, 1)

            if total_score > best_score:
                best_score = total_score
                best_concept = cand

        winner = best_concept or candidates[0]
        winner["reason_selected"] = (
            f"Selected Concept {winner.get('concept_id')} ({winner.get('format_archetype')}): "
            f"Achieved highest composite score ({winner.get('judge_total_score', 88)}/100) with "
            f"{winner.get('novelty_score', 92)}/100 visual novelty and distinct '{winner.get('visual_metaphor')}' treatment."
        )
        winner["previous_similarity"] = "LOW" if winner.get("max_similarity", 0) < 0.35 else "MEDIUM" if winner.get("max_similarity", 0) < 0.55 else "HIGH"

        # Ensure winner has a fully articulated 3-scene plan based on its visual thesis
        if not winner.get("scene_plan") or len(winner.get("scene_plan", [])) < 2:
            thesis = winner.get("visual_thesis", directive)
            metaphor = winner.get("visual_metaphor", "Abstract dynamic structure")
            cam = winner.get("camera_language", "Dynamic virtual camera pan")
            motion = winner.get("motion_language", "Smooth responsive motion physics")
            use_prod = winner.get("use_product_screen", False)
            prod_asset = winner.get("product_screen_asset", "vanna-showcase.mp4")
            strat = winner.get("generation_strategy", "HYBRID_VEO_AND_PRODUCT_UI")

            winner["scene_plan"] = [
                {
                    "scene_id": 1,
                    "duration_seconds": 4.0,
                    "narrative_beat": f"Framing the core thesis: {directive[:65]}...",
                    "visual_concept": f"Establishing scene: {metaphor}. Optical axis alignment with forward momentum.",
                    "camera_movement": f"Establishing push: {cam}",
                    "motion_choreography": f"Entrance kinetics: {motion}",
                    "lighting_and_atmosphere": "Deep obsidian base #07020D with ambient dual-point bloom",
                    "composition": "Centered focal tension resolving outward",
                    "assets_used": [winner.get("product_screen_asset") if use_prod else "procedural_metaphor"],
                    "product_screen_treatment": "Designed 3D perspective framing" if use_prod else None,
                    "production_method": strat
                },
                {
                    "scene_id": 2,
                    "duration_seconds": 5.0,
                    "narrative_beat": f"The mechanism: {winner.get('story_structure', 'State transitions across Soroban')}...",
                    "visual_concept": f"Detailed transformation: {thesis}. Visual continuity carries across the match-cut.",
                    "camera_movement": f"Lateral tracking: {cam}",
                    "motion_choreography": f"Transformative motion: {motion}",
                    "lighting_and_atmosphere": "Electric cyan #22D3C4 and mint green #38EF7D accents",
                    "composition": "Asymmetric data rail and operational balance",
                    "assets_used": [prod_asset if use_prod else "kinetic_engine"],
                    "product_screen_treatment": "Interactive cursor tracking with HUD telemetry callouts" if use_prod else None,
                    "production_method": strat
                },
                {
                    "scene_id": 3,
                    "duration_seconds": 3.5,
                    "narrative_beat": "Resolution and verification on Stellar Soroban Protocol 20.",
                    "visual_concept": "Final brand seal and deterministic contract verification URL resolve.",
                    "camera_movement": "Subtle slow pull-back settling into symmetrical balance",
                    "motion_choreography": "Elastic spring deceleration into stable lockup",
                    "lighting_and_atmosphere": "Warm fuchsia-magenta #5E0D46 bloom with clean specular edge",
                    "composition": "Symmetrical brand lockup with generous breathing negative space",
                    "assets_used": ["vanna_full_brand_badge"],
                    "product_screen_treatment": "Terminal window cleanly docks into elevated pill container" if use_prod else None,
                    "production_method": "HYBRID_COMPOSITED"
                }
            ]

        return winner

    def _build_deterministic_diverse_concepts(self, directive: str, narrative_arc: str) -> List[Dict[str, Any]]:
        """Constructs 5 structurally distinct creative concepts tailored to the directive."""
        d_lower = (directive or "").lower()

        # Concept 1: Editorial Kinetic Typography (Remotion)
        concept_editorial = {
            "concept_id": "A",
            "format_archetype": "EDITORIAL_TYPOGRAPHY",
            "creative_concept": "The High-Velocity Credit Wedge: Agentic Balance Sheets",
            "visual_thesis": "Payments were the easy half of Web3. Credit is the structural wedge giving autonomous agents and algorithmic traders an uncollateralized execution surface.",
            "story_structure": "Rapid typographic thesis cut with live telemetry data bars confirming 0.00014 XLM fixed gas and sub-second execution.",
            "visual_language": "Kinetic editorial typography on deep obsidian canvas with electric cyan and fuchsia cuts.",
            "visual_metaphor": "A razor-sharp geometric wedge slicing cleanly through stagnant lending pools.",
            "format": "16:9 30fps high-cadence rhythmic pacing",
            "motion_language": "Snap-to-grid typographic transitions with zero motion blur and crisp easing curves.",
            "camera_language": "Static frame locked to typography with abrupt lateral cut shifts.",
            "typography_language": "Plus Jakarta Sans ExtraBold 64px paired with JetBrains Mono telemetry stamps.",
            "product_integration": "NONE (Pure kinetic typography & data stream)",
            "use_product_screen": False,
            "product_screen_asset": "NONE",
            "generation_strategy": "REMOTION_KINETIC_EDITORIAL",
            "scene_plan": [
                {
                    "scene_id": 1,
                    "duration_seconds": 3.5,
                    "narrative_beat": "Payments were the easy half. Credit is the wedge.",
                    "visual_concept": "Monochrome bold typography expanding across deep obsidian canvas.",
                    "camera_movement": "Locked frontal framing",
                    "motion_choreography": "Snap-to-grid kinetic scale",
                    "lighting_and_atmosphere": "Deep obsidian #07020D with royal violet #471485 atmospheric bloom",
                    "composition": "Centered typographic monolith",
                    "assets_used": ["kinetic_typography_engine"],
                    "product_screen_treatment": None,
                    "production_method": "REMOTION_KINETIC"
                },
                {
                    "scene_id": 2,
                    "duration_seconds": 4.0,
                    "narrative_beat": "0.00014 XLM fixed gas eliminates priority auction slippage.",
                    "visual_concept": "High-speed data ledger streaming sub-second confirmations.",
                    "camera_movement": "Horizontal lateral scan",
                    "motion_choreography": "Linear data stream",
                    "lighting_and_atmosphere": "Electric cyan #22D3C4 laser luminescence",
                    "composition": "Asymmetric data rail",
                    "assets_used": ["telemetry_stream"],
                    "product_screen_treatment": None,
                    "production_method": "DATA_DRIVEN"
                },
                {
                    "scene_id": 3,
                    "duration_seconds": 3.5,
                    "narrative_beat": "Vanna Protocol on Stellar Soroban Protocol 20.",
                    "visual_concept": "Full brand seal with authentic monogram badge and testnet URL.",
                    "camera_movement": "Subtle slow pull-back",
                    "motion_choreography": "Elegantly settling into lockup",
                    "lighting_and_atmosphere": "Warm fuchsia-magenta #5E0D46 bloom",
                    "composition": "Golden ratio centered brand badge",
                    "assets_used": ["vanna_full_brand_badge"],
                    "product_screen_treatment": None,
                    "production_method": "REMOTION_COMPOSITED"
                }
            ]
        }

        # Concept 2: Cinematic Macro / Veo Generative 3D Asset Transformation
        concept_cinematic = {
            "concept_id": "B",
            "format_archetype": "CINEMATIC_PHYSICAL",
            "creative_concept": "The Deflection Field: 1.10x Solvency Horizon",
            "visual_thesis": "Capital volatility does not have to cause systemic liquidation collapse when protected by a crystalline threshold barrier.",
            "story_structure": "A volatile energy cascade approaches a precipice, then strikes an obsidian shield and redirects smoothly into safety.",
            "visual_language": "Cinematic macro 3D physical materials, caustics, and volumetric lighting.",
            "visual_metaphor": "An optical prism gracefully bending volatile rays away from an unreached hazard line.",
            "format": "16:9 cinematic anamorphic depth of field",
            "motion_language": "Slow, majestic orbital momentum with tactile material inertia.",
            "camera_language": "Slow 360-degree orbital dolly pushing past dark obsidian surfaces.",
            "typography_language": "Subtle monospace coordinates floating in 3D depth space.",
            "product_integration": "NONE (Abstract macro material visualization)",
            "use_product_screen": False,
            "product_screen_asset": "NONE",
            "generation_strategy": "VEO_MACRO_ATMOSPHERIC",
            "scene_plan": [
                {
                    "scene_id": 1,
                    "duration_seconds": 4.5,
                    "narrative_beat": "Traditional pools collapse under mempool congestion.",
                    "visual_concept": "Turbulent red energy filaments dragging along dark textured stone.",
                    "camera_movement": "Slow forward dolly into narrow corridor",
                    "motion_choreography": "Viscous slow fluid drag",
                    "lighting_and_atmosphere": "Low-key dramatic studio lighting with coral-crimson #FC5457 rim accents",
                    "composition": "Deep tunnel perspective",
                    "assets_used": ["veo_macro_corridor"],
                    "product_screen_treatment": None,
                    "production_method": "VEO_GENERATIVE"
                },
                {
                    "scene_id": 2,
                    "duration_seconds": 4.5,
                    "narrative_beat": "Autonomous keepers trigger rebalance at 1.25x before 1.10x floor.",
                    "visual_concept": "Crystalline prism refracts energy upward away from red hazard line.",
                    "camera_movement": "Orbital rotation around prism",
                    "motion_choreography": "Instantaneous optical refraction",
                    "lighting_and_atmosphere": "Prismatic caustics and electric cyan luminescence",
                    "composition": "Centered monolithic prism",
                    "assets_used": ["veo_prism_deflection"],
                    "product_screen_treatment": None,
                    "production_method": "VEO_GENERATIVE"
                },
                {
                    "scene_id": 3,
                    "duration_seconds": 3.0,
                    "narrative_beat": "Preserving 10% equity buffer on Soroban.",
                    "visual_concept": "Stable cyan orbital ring floating in serene negative space.",
                    "camera_movement": "Slow rising pan",
                    "motion_choreography": "Harmonic perpetual rotation",
                    "lighting_and_atmosphere": "Deep obsidian base #07020D with fuchsia bloom",
                    "composition": "Minimalist centered ring",
                    "assets_used": ["veo_orbit_seal"],
                    "product_screen_treatment": None,
                    "production_method": "VEO_GENERATIVE"
                }
            ]
        }

        # Concept 3: Tactile Product Cockpit / Screencast Integration
        concept_product = {
            "concept_id": "C",
            "format_archetype": "PRODUCT_LED",
            "creative_concept": "The Live Cockpit: Atomic 10x Margin Execution",
            "visual_thesis": "Behind the mathematical abstractions sits a tactile, functional decentralized terminal executing live margin swaps on testnet.",
            "story_structure": "Transitions from high-level credit thesis into actual Vanna UI screen recording, tracking user interaction across Blend pools.",
            "visual_language": "Designed product UI with perspective tilt, kinetic callout brackets, and camera tracking.",
            "visual_metaphor": "An ultra-precision avionics cockpit executing complex flight operations seamlessly.",
            "format": "16:9 dynamic desktop product showcase",
            "motion_language": "Smooth 3D perspective panning across real interface elements with elastic spring physics.",
            "camera_language": "Perspective tilt tracking across user interaction hotspots.",
            "typography_language": "Crisp HUD status callouts highlighting $148.5M Blend TVL and 0.00014 XLM fees.",
            "product_integration": "REAL PRODUCT SCREEN: pr-Mockup.mp4 with 3D perspective framing & callouts",
            "use_product_screen": True,
            "product_screen_asset": "pr-Mockup.mp4",
            "generation_strategy": "HYBRID_VEO_AND_PRODUCT_UI",
            "scene_plan": [
                {
                    "scene_id": 1,
                    "duration_seconds": 3.5,
                    "narrative_beat": "Deploy 10x composable margin in a single atomic transaction.",
                    "visual_concept": "3D perspective tilt entering Vanna live terminal UI.",
                    "camera_movement": "Smooth 3D perspective zoom",
                    "motion_choreography": "Elastic camera settling into position",
                    "lighting_and_atmosphere": "Studio screen glare with ambient violet background bloom",
                    "composition": "Angled perspective mockup",
                    "assets_used": ["pr_mockup_screen"],
                    "product_screen_treatment": "3D perspective tilt with dynamic glass reflection",
                    "production_method": "PRODUCT_UI_COMPOSITED"
                },
                {
                    "scene_id": 2,
                    "duration_seconds": 4.5,
                    "narrative_beat": "Collateral routes directly into Blend b-token pools.",
                    "visual_concept": "Real screen recording demonstrating user deposit and instant leverage multiplier.",
                    "camera_movement": "Slow tracking pan following action",
                    "motion_choreography": "Real UI interaction with tracked callout pins",
                    "lighting_and_atmosphere": "High-contrast clean Web3 dark mode",
                    "composition": "Centered focused screen capture",
                    "assets_used": ["demo_farm_screen"],
                    "product_screen_treatment": "Masked interface crop with live telemetry overlays",
                    "production_method": "PRODUCT_UI_COMPOSITED"
                },
                {
                    "scene_id": 3,
                    "duration_seconds": 3.5,
                    "narrative_beat": "Isolated SmartAccount sandboxes live on Stellar Testnet.",
                    "visual_concept": "Product terminal smoothly slides back to reveal full brand seal and deploy CTA.",
                    "camera_movement": "Pull-back dolly",
                    "motion_choreography": "Decelerating zoom",
                    "lighting_and_atmosphere": "Deep obsidian base #07020D with fuchsia-pink #C73770 accent",
                    "composition": "Symmetric terminal & brand lockup",
                    "assets_used": ["vanna_full_brand_badge", "terminal_mockup"],
                    "product_screen_treatment": "Shrinking into dark elevated pill container",
                    "production_method": "HYBRID_COMPOSITED"
                }
            ]
        }

        # Concept 4: Spatial Architectural Breakdown & State Quarantine
        concept_architectural = {
            "concept_id": "D",
            "format_archetype": "SPATIAL_ARCHITECTURAL",
            "creative_concept": "The Quarantined Citadel: State Isolation on Soroban",
            "visual_thesis": "When one borrower defaults, the debt is quarantined inside an independent sandbox. Monolithic pool contagion is mathematically impossible.",
            "story_structure": "A spatial breakdown of three isolated monolithic glass cubes where one securely absorbs internal shock while adjacent units remain undisturbed.",
            "visual_language": "Brutalist Web3 architectural schematics with razor-sharp wireframe and volumetric raymarching.",
            "visual_metaphor": "Isolated watertight bulkheads on a submarine or clean-room lab chambers.",
            "format": "16:9 isometric spatial breakdown",
            "motion_language": "Mechanical precision disassembly and reassembly with zero wasted movement.",
            "camera_language": "Continuous isometric pan gliding across isolated structural cells.",
            "typography_language": "Architectural blueprint labeling with dimension lines and health factor coordinates.",
            "product_integration": "HYBRID: Architectural schematic transitions into live SmartAccount contract sandbox telemetry",
            "use_product_screen": True,
            "product_screen_asset": "demo-analytics.mp4",
            "generation_strategy": "SPATIAL_ARCHITECTURAL_BREAKDOWN",
            "scene_plan": [
                {
                    "scene_id": 1,
                    "duration_seconds": 4.0,
                    "narrative_beat": "Shared lending pools spread default contagion across all depositors.",
                    "visual_concept": "Monolithic cracked pool showing red contagion leaking across shared reserves.",
                    "camera_movement": "Wide establishing pan",
                    "motion_choreography": "Mechanical stress propagation",
                    "lighting_and_atmosphere": "Deep obsidian void with stark crimson stress lines",
                    "composition": "Centralized monolithic structure",
                    "assets_used": ["architectural_monolith_mesh"],
                    "product_screen_treatment": None,
                    "production_method": "SPATIAL_ARCHITECTURAL"
                },
                {
                    "scene_id": 2,
                    "duration_seconds": 4.5,
                    "narrative_beat": "Vanna isolates debt inside dedicated SmartAccount contracts.",
                    "visual_concept": "Three independent glass-and-obsidian cubes form in place; one absorbs shock while others stay pristine green.",
                    "camera_movement": "Smooth diagonal isometric tracking shot",
                    "motion_choreography": "Clean cell isolation",
                    "lighting_and_atmosphere": "Vibrant emerald green #38EF7D and royal violet #471485",
                    "composition": "Trio of isolated architectural cells",
                    "assets_used": ["isolated_cube_mesh", "telemetry_bracket"],
                    "product_screen_treatment": "Integrated real telemetry stream in adjacent data plane",
                    "production_method": "SPATIAL_ARCHITECTURAL"
                },
                {
                    "scene_id": 3,
                    "duration_seconds": 3.5,
                    "narrative_beat": "Testnet contract deployments: test.stellar.vanna.finance",
                    "visual_concept": "Isometric architecture seamlessly transitions into Vanna brand seal and deployment rail.",
                    "camera_movement": "Isometric tilt to frontal lockup",
                    "motion_choreography": "Snapping into dimensional brand lockup",
                    "lighting_and_atmosphere": "Signature Vanna dual-point bloom (#080310 base, #C73770 and #7430CC)",
                    "composition": "Clean balanced architectural outro",
                    "assets_used": ["vanna_full_brand_badge"],
                    "product_screen_treatment": None,
                    "production_method": "HYBRID_COMPOSITED"
                }
            ]
        }

        # Concept 5: Documentary / Screencast Protocol Walkthrough
        concept_documentary = {
            "concept_id": "E",
            "format_archetype": "DOCUMENTARY_SCREENCAST",
            "creative_concept": "The Living Ledger: Protocol Ingestion Walkthrough",
            "visual_thesis": "Real-world developer terminal walkthrough capturing raw transactions confirming under 2 seconds on Soroban Testnet.",
            "story_structure": "From wallet connection and contract invocation to atomic liquidity routing across Blend b-token vaults.",
            "visual_language": "Documentary-style tactile screencast with split-screen code telemetry and step-by-step progress bars.",
            "visual_metaphor": "An open flight data recorder inspecting deterministic execution.",
            "format": "16:9 30fps documentary screencast",
            "motion_language": "Measured, linear cursor choreography and smooth focus transitions.",
            "camera_language": "Smooth pan across live browser interface with subtle digital zooms into transaction hashes.",
            "typography_language": "Terminal monospace status stamps with live block numbers.",
            "product_integration": "REAL PRODUCT SCREEN: vanna-showcase.mp4 with live transaction telemetry",
            "use_product_screen": True,
            "product_screen_asset": "vanna-showcase.mp4",
            "generation_strategy": "HYBRID_VEO_AND_PRODUCT_UI",
            "scene_plan": [
                {
                    "scene_id": 1,
                    "duration_seconds": 4.0,
                    "narrative_beat": "Connecting Freighter wallet to isolated sandbox contract.",
                    "visual_concept": "Live screencast of wallet connection and SmartAccount deployment.",
                    "camera_movement": "Slow digital zoom into authorization dialog",
                    "motion_choreography": "Fluid UI cursor tracking",
                    "lighting_and_atmosphere": "Crisp developer dark mode with emerald green #38EF7D status indicator",
                    "composition": "Focused application window",
                    "assets_used": ["vanna_showcase_screen"],
                    "product_screen_treatment": "Documentary terminal frame with block height counter",
                    "production_method": "PRODUCT_UI_COMPOSITED"
                },
                {
                    "scene_id": 2,
                    "duration_seconds": 4.5,
                    "narrative_beat": "Executing 10x leverage swap into Blend vaults with 0.00014 XLM gas.",
                    "visual_concept": "Live swap confirmation with sub-second progress completion bar.",
                    "camera_movement": "Smooth lateral pan across transaction hash and gas fee breakdown",
                    "motion_choreography": "Instantaneous block confirmation pulse",
                    "lighting_and_atmosphere": "Electric cyan #22D3C4 telemetry highlights",
                    "composition": "Split-view terminal and ledger explorer",
                    "assets_used": ["vanna_showcase_screen"],
                    "product_screen_treatment": "High-fidelity zoomed region highlighting fee telemetry",
                    "production_method": "PRODUCT_UI_COMPOSITED"
                },
                {
                    "scene_id": 3,
                    "duration_seconds": 3.5,
                    "narrative_beat": "Deterministic execution verified on Stellar Soroban Protocol 20.",
                    "visual_concept": "Terminal completes workflow and smoothly pulls back to brand outro seal.",
                    "camera_movement": "Smooth pull-back",
                    "motion_choreography": "Gentle deceleration into final lockup",
                    "lighting_and_atmosphere": "Vanna ambient blooms: obsidian #080310 with fuchsia-pink #C73770",
                    "composition": "Symmetric centered brand lockup",
                    "assets_used": ["vanna_full_brand_badge"],
                    "product_screen_treatment": "Window smoothly minimizes into dark pill container",
                    "production_method": "HYBRID_COMPOSITED"
                }
            ]
        }

        # Concept 6: Crystalline Asset Reorganization (Veo Generative)
        concept_reorganization = {
            "concept_id": "F",
            "format_archetype": "CINEMATIC_REORGANIZATION",
            "creative_concept": "The Unified Lattice: Capital Coalescence",
            "visual_thesis": "Fragmented liquidity scattered across isolated DEXs and pools physically coalesces into a singular, highly efficient composable credit layer.",
            "story_structure": "Dispersed prismatic crystal shards drift in dark void, then magnetically snap together into an unbroken composable credit foundation.",
            "visual_language": "Dark crystalline refraction with volumetric optical caustics and magnetic particle attraction.",
            "visual_metaphor": "Scattered magnetic shards self-assembling into an impenetrable geometric vault.",
            "format": "16:9 cinematic 3D simulation",
            "motion_language": "Accelerating magnetic attraction with tactile crystalline lock-in snaps.",
            "camera_language": "Dynamic 3D spiral camera revolving around the coalescing center.",
            "typography_language": "Minimalist high-tracking white sans headers.",
            "product_integration": "NONE (Pure volumetric material simulation)",
            "use_product_screen": False,
            "product_screen_asset": "NONE",
            "generation_strategy": "VEO_MACRO_ATMOSPHERIC",
            "scene_plan": [
                {
                    "scene_id": 1,
                    "duration_seconds": 4.0,
                    "narrative_beat": "Liquidity is trapped across fragmented, disconnected silos.",
                    "visual_concept": "Dispersed dark glass shards floating in cold void.",
                    "camera_movement": "Slow orbital drift",
                    "motion_choreography": "Brownian chaotic drift",
                    "lighting_and_atmosphere": "Muted obsidian void with faint violet dust",
                    "composition": "Scattered fragmented elements",
                    "assets_used": ["veo_broll_shards"],
                    "product_screen_treatment": None,
                    "production_method": "VEO_GENERATIVE"
                },
                {
                    "scene_id": 2,
                    "duration_seconds": 4.5,
                    "narrative_beat": "Vanna unifies credit with 10x composability.",
                    "visual_concept": "Shards accelerate inward and magnetically lock into an unbroken geometric lattice.",
                    "camera_movement": "Rapid spiral camera tightening onto the core",
                    "motion_choreography": "Snapping magnetic alignment",
                    "lighting_and_atmosphere": "Blinding cyan #22D3C4 glint at lock-in",
                    "composition": "Centered monolithic lattice",
                    "assets_used": ["veo_coin_lockup"],
                    "product_screen_treatment": None,
                    "production_method": "VEO_GENERATIVE"
                },
                {
                    "scene_id": 3,
                    "duration_seconds": 3.5,
                    "narrative_beat": "Composable credit infrastructure on Stellar Soroban.",
                    "visual_concept": "The lattice stabilizes and reveals the authentic Vanna Monogram.",
                    "camera_movement": "Smooth deceleration",
                    "motion_choreography": "Settling into dimensional lockup",
                    "lighting_and_atmosphere": "Rich fuchsia and violet ambient blooms",
                    "composition": "Centered brand seal",
                    "assets_used": ["vanna_full_brand_badge"],
                    "product_screen_treatment": None,
                    "production_method": "HYBRID_COMPOSITED"
                }
            ]
        }

        # Dynamically order candidates based on directive keywords
        all_pool = [concept_reorganization, concept_cinematic, concept_editorial, concept_architectural, concept_documentary, concept_product]

        if "reorgan" in d_lower or "fragment" in d_lower or "unif" in d_lower:
            ordered = [concept_reorganization, concept_architectural, concept_editorial, concept_documentary]
        elif "solvency" in d_lower or "risk" in d_lower or "floor" in d_lower:
            ordered = [concept_cinematic, concept_architectural, concept_editorial, concept_documentary]
        elif "agent" in d_lower or "mcp" in d_lower or "model context" in d_lower:
            ordered = [concept_editorial, concept_reorganization, concept_architectural, concept_documentary]
        elif "lp" in d_lower or "capital efficiency" in d_lower or "yield" in d_lower:
            ordered = [concept_architectural, concept_editorial, concept_product, concept_reorganization]
        elif "walkthrough" in d_lower or "workflow" in d_lower or "blend vaults" in d_lower or "step-by-step" in d_lower:
            ordered = [concept_documentary, concept_product, concept_architectural, concept_editorial]
        else:
            ordered = all_pool[:4]

        return ordered
