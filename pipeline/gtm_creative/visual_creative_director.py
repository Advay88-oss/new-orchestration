#!/usr/bin/env python3
"""Vanna Visual Creative Director (pipeline/gtm_creative/visual_creative_director.py).

Core Mandates:
  1. REASON FIRST: Answers the 10 Creative Reasoning Questions before generating.
  2. REFERENCE != TEMPLATE: Borrows principles (clarity, restraint, hierarchy) without copying surface appearance.
  3. CONTENT-DRIVEN: Distinct visual language for architecture, market data, product, risk, ecosystem.
  4. CREATIVE REASONING PACKET: Provides Nano Banana with creative direction and autonomous decision room rather than micro-managed cubes & arrows.
  5. MULTI-CONCEPT EXPLORATION: Generates 3 structurally distinct concepts before choosing a winner with clear justification.
"""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.request
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from pipeline.creative_memory.visual_reference_principles import (
    CONTENT_TREATMENT_MAPPING,
    VANNA_VISUAL_REFERENCE_PRINCIPLES
)
from pipeline.gtm_creative.structural_fingerprint import (
    CreativeFatigueTracker,
    StructuralCreativeFingerprint,
    StructuralNoveltyAuditor
)


def call_gemini_brain(prompt: str, system_instruction: str = "") -> Optional[str]:
    """Invokes Gemini 3.8 Flash via Vertex spend proxy or direct API key."""
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if api_key:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash:generateContent?key={api_key}"
    else:
        url = "http://127.0.0.1:8900/v1/projects/sales-agent-504607/locations/us-central1/publishers/google/models/gemini-3.8-flash:generateContent"

    combined = f"{system_instruction}\n\n{prompt}" if system_instruction else prompt
    payload = {
        "contents": [{"role": "user", "parts": [{"text": combined}]}],
        "generationConfig": {
            "temperature": 0.85,
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
        with urllib.request.urlopen(req, timeout=40) as r:
            res = json.loads(r.read().decode("utf-8"))
            return res["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        print(f"⚠️ [VisualCreativeDirector] Gemini Brain call notice: {e}")
        return None


class VisualCreativeDirector:
    """Executive Visual Creative Director enforcing non-convergent, high-craft brand design."""

    def __init__(self, memory_dir: Optional[Path] = None):
        self.memory_dir = memory_dir or (REPO_ROOT / "pipeline" / "creative_memory")
        self.fatigue_tracker = CreativeFatigueTracker(history_limit=15)
        self.novelty_auditor = StructuralNoveltyAuditor()

    def direct_visual_asset(
        self,
        brief_title: str,
        content_type: str,
        directive: str,
        audience: str,
        key_claim: str,
        recent_fingerprints: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """Main entry point: Reasons across 10 dimensions, explores 3 concepts, selects winner,

        and produces the Creative Reasoning Packet for Nano Banana.
        """
        print("=" * 80)
        print(f"🎨 VISUAL CREATIVE DIRECTOR: ART-DIRECTING VISUAL ASSET")
        print(f"   Brief: \"{brief_title}\" | Type: {content_type}")
        print(f"   Directive: \"{directive}\"")
        print("=" * 80)

        recent_fps = recent_fingerprints or []

        # Step 1: 10-Question Creative Reasoning
        reasoning_dossier = self._reason_ten_questions(
            brief_title=brief_title,
            content_type=content_type,
            directive=directive,
            audience=audience,
            key_claim=key_claim,
            recent_fps=recent_fps
        )

        # Step 2: Multi-Concept Exploration (3 genuinely structurally different concepts)
        concepts = self._explore_three_concepts(
            reasoning=reasoning_dossier,
            content_type=content_type,
            directive=directive,
            audience=audience,
            recent_fps=recent_fps
        )

        # Step 3: Novelty Audit & Fatigue Scoring
        scored_concepts = []
        for c in concepts:
            fp = c["fingerprint"]
            novelty_result = self.novelty_auditor.audit_novelty(fp, recent_fps)
            fatigue_penalty, warnings = self.fatigue_tracker.calculate_fatigue_penalty(fp, recent_fps)

            # Combined Judge Score
            narrative_fit = 95.0
            craft_alignment = novelty_result["reference_quality_alignment"]
            novelty = novelty_result["novelty_score"]
            clone_penalty = 80.0 if novelty_result["is_structural_clone"] else 0.0

            total_score = (narrative_fit * 0.30) + (craft_alignment * 0.35) + (novelty * 0.35) - fatigue_penalty - clone_penalty

            c["novelty_result"] = novelty_result
            c["fatigue_penalty"] = fatigue_penalty
            c["fatigue_warnings"] = warnings
            c["judge_score"] = round(total_score, 1)
            scored_concepts.append(c)

            clone_flag = "🚨 STRUCTURAL CLONE" if novelty_result["is_structural_clone"] else "✅ NOVEL"
            print(f"   Concept {c['concept_id']} (\"{c['concept_title'][:45]}...\") | Score: {c['judge_score']} | Novelty: {novelty:.1f} | {clone_flag}")

        # Step 4: Creative Judge Selection
        scored_concepts.sort(key=lambda x: x["judge_score"], reverse=True)
        winner = scored_concepts[0]
        runner_ups = scored_concepts[1:]

        selection_reason = (
            f"Selected Concept {winner['concept_id']} ('{winner['concept_title']}'): "
            f"Achieved highest composite score ({winner['judge_score']}/100) with "
            f"{winner['novelty_result']['novelty_score']}/100 structural novelty. "
            f"Communicates '{content_type}' through a unique {winner['fingerprint'].visual_metaphor_type.lower()} "
            f"without repeating recent visual treatments."
        )
        winner["selection_rationale"] = selection_reason
        winner["rejected_concepts"] = [
            {
                "concept_id": r["concept_id"],
                "title": r["concept_title"],
                "rejection_reason": (
                    f"Lower composite score ({r['judge_score']}/100); "
                    f"{'detected as structural clone;' if r['novelty_result']['is_structural_clone'] else ''} "
                    f"{'; '.join(r['fatigue_warnings']) if r['fatigue_warnings'] else 'less direct visual clarity for audience.'}"
                )
            }
            for r in runner_ups
        ]

        print(f"\n🏆 Selected Winner: Concept {winner['concept_id']} (\"{winner['concept_title']}\")")
        print(f"   Reason: {selection_reason}")

        # Step 5: Construct Nano Banana Creative Reasoning Packet
        nano_banana_packet = self._build_nano_banana_packet(winner, reasoning_dossier)

        return {
            "brief_title": brief_title,
            "content_type": content_type,
            "directive": directive,
            "reasoning_dossier": reasoning_dossier,
            "selected_concept": winner,
            "all_explored_concepts": scored_concepts,
            "nano_banana_packet": nano_banana_packet,
            "fingerprint": winner["fingerprint"].to_dict()
        }

    def _reason_ten_questions(
        self,
        brief_title: str,
        content_type: str,
        directive: str,
        audience: str,
        key_claim: str,
        recent_fps: List[Dict[str, Any]]
    ) -> Dict[str, str]:
        """Executes the mandatory 10-Question Creative Reasoning stage."""
        mapping = CONTENT_TREATMENT_MAPPING.get(content_type, CONTENT_TREATMENT_MAPPING["technical_architecture"])
        recent_metaphors = list({fp.get("visual_metaphor_type") for fp in recent_fps[-6:] if fp.get("visual_metaphor_type")})
        recent_objects = list({fp.get("primary_object_type") for fp in recent_fps[-6:] if fp.get("primary_object_type")})

        q1 = f"We are communicating: {directive}. Specifically proving {key_claim}."
        q2 = f"Primary audience is {audience}. They require high intellectual signal, zero crypto buzzwords, and verifiable institutional rigor."
        q3 = f"In 2-3 seconds, viewer must understand: Vanna solves {brief_title} through sovereign isolated architecture rather than pooled vulnerability."
        q4 = f"Central creative idea: Eliminate shared counterparty vulnerability by modular isolation and deterministic execution."
        
        # Metaphor tailored to content type
        if content_type == "risk_security_concept":
            q5 = "Hydro-dynamic dampening or pressure bulkhead containment: kinetic force deflected away from protected capital buffer."
        elif content_type == "market_data_insight":
            q5 = "Editorial statistical data matrix or kinetic rate curve: mathematical precision replacing speculative hype."
        elif content_type == "product_value_proposition":
            q5 = "Tactile high-precision avionics terminal: live user interaction executing multi-venue leverage with zero slippage."
        elif content_type == "ecosystem_integration":
            q5 = "Modular infrastructure dock: sovereign SmartAccounts docking seamlessly into Blend and Soroswap protocols."
        else:
            q5 = "Refined technical system architecture: isolated Soroban sandboxes with clean state boundaries."

        q6 = f"This treatment fits because '{content_type}' demands {mapping['primary_focus']} rather than generic 3D cubes."
        q7 = "Approved reference principles applied: Generous negative space (>65%), high optical contrast, strict two-tier typography, and technical restraint."
        q8 = "CRITICAL: Do NOT copy the reference surface details (no 3 identical cubes, no neon arrows, no lavender processor chip, no 3-column flowchart)."
        q9 = f"Recently overused treatments to avoid: {', '.join(recent_metaphors or ['generic 3D cubes', 'three-column diagrams'])}."
        q10 = f"Alternative high-impact treatments: {', '.join(mapping['recommended_treatments'][:3])}."

        return {
            "Q01_what_are_we_communicating": q1,
            "Q02_who_is_the_audience": q2,
            "Q03_viewer_comprehension_2_sec": q3,
            "Q04_central_creative_idea": q4,
            "Q05_visual_metaphor": q5,
            "Q06_why_treatment_appropriate": q6,
            "Q07_reference_principles_borrowed": q7,
            "Q08_reference_elements_NOT_copied": q8,
            "Q09_overused_treatments_avoided": q9,
            "Q10_alternative_treatments_explored": q10
        }

    def _explore_three_concepts(
        self,
        reasoning: Dict[str, str],
        content_type: str,
        directive: str,
        audience: str,
        recent_fps: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Synthesizes 3 genuinely structurally different concepts tailored to the content type."""
        mapping = CONTENT_TREATMENT_MAPPING.get(content_type, CONTENT_TREATMENT_MAPPING["technical_architecture"])

        # Concept Archetypes tailored per content type:
        if content_type == "technical_architecture":
            c1 = {
                "concept_id": "A",
                "concept_title": "The Sectional Isometric Cutaway: Isolated Contract Sandboxes",
                "treatment_style": "Refined Technical Illustration",
                "visual_thesis": "A clean sectional architectural cutaway revealing isolated Soroban contract sandboxes with zero pooled contagion.",
                "visual_metaphor": "Precision engineering blueprint with watertight structural compartments.",
                "fingerprint": StructuralCreativeFingerprint(
                    composition_type="SECTIONAL_ARCHITECTURAL_CUTAWAY",
                    symmetry="ASYMMETRICAL",
                    visual_metaphor_type="ARCHITECTURAL_CONTAINMENT",
                    primary_object_type="ISOMETRIC_VAULT_SECTION",
                    layout_structure="HERO_WITH_DATA_RAILS",
                    typography_strategy="ENGINEERED_COORDINATE_STAMPS",
                    background_type="TECHNICAL_GRID_SUBSTRATE",
                    color_distribution="MONOCHROME_WITH_MINT_CONFIRMATION",
                    depth_strategy="ISOMETRIC_INFINITE_DEPTH",
                    product_integration="SCHEMATIC_SPECIFICATION",
                    information_density="CALIBRATED_TECHNICAL",
                    viewpoint="ISOMETRIC_30_DEGREE"
                )
            }
            c2 = {
                "concept_id": "B",
                "concept_title": "The Sovereign Boundary: Spatial State Separation",
                "treatment_style": "Spatial System Metaphor",
                "visual_thesis": "Minimalist spatial boundary planes where independent SmartAccount instances execute without shared memory leaks.",
                "visual_metaphor": "Floating acoustic dampening baffles or clean-room isolation airlocks.",
                "fingerprint": StructuralCreativeFingerprint(
                    composition_type="ASYMMETRICAL_SPLIT",
                    symmetry="DYNAMIC_BALANCED",
                    visual_metaphor_type="PHYSICAL_MATERIAL",
                    primary_object_type="CRYSTALLINE_BARRIER",
                    layout_structure="EXPANSIVE_FIELD_WITH_ANCHOR",
                    typography_strategy="OVERSIZED_STATEMENT_WITH_CHIPS",
                    background_type="DEEP_OBSIDIAN_VOID",
                    color_distribution="HIGH_CONTRAST_CYAN_ACCENTS",
                    depth_strategy="SHALLOW_FIELD_MACRO",
                    product_integration="NONE_PURE_METAPHOR",
                    information_density="MINIMAL_EXECUTIVE",
                    viewpoint="OBLIQUE_PERSPECTIVE"
                )
            }
            c3 = {
                "concept_id": "C",
                "concept_title": "The Deterministic State Transition Matrix",
                "treatment_style": "Editorial System Diagram",
                "visual_thesis": "High-contrast technical vector map detailing sub-second Soroban invocation states under Protocol 20.",
                "visual_metaphor": "Precision telemetry flight rail with verified block confirmations.",
                "fingerprint": StructuralCreativeFingerprint(
                    composition_type="EDITORIAL_TYPOGRAPHIC_DATA",
                    symmetry="BILATERAL",
                    visual_metaphor_type="EDITORIAL_DATA_GRID",
                    primary_object_type="DATA_STREAM_MATRIX",
                    layout_structure="SPLIT_PERSPECTIVE_VIEW",
                    typography_strategy="EDITORIAL_HEADLINE_DATA_SPLIT",
                    background_type="CLEAN_DARK_CANVAS",
                    color_distribution="WARM_CHAMFER_SPECULAR",
                    depth_strategy="FLAT_TECHNICAL_PROJECTION",
                    product_integration="SUB_MODULE_HUD_CHIPS",
                    information_density="DATA_RICH_EDITORIAL",
                    viewpoint="FRONTAL_ELEVATION"
                )
            }
        elif content_type == "product_value_proposition":
            c1 = {
                "concept_id": "A",
                "concept_title": "The Tactical Avionics Cockpit: 1-Click Margin Execution",
                "treatment_style": "Designed Product Interface Integration",
                "visual_thesis": "Elevated 3D perspective viewport of the live Vanna terminal executing atomic 10x leverage into Blend vaults.",
                "visual_metaphor": "An ultra-precision avionics flight deck with live status telemetry.",
                "fingerprint": StructuralCreativeFingerprint(
                    composition_type="PERSPECTIVE_TERMINAL_VIEWPORT",
                    symmetry="DYNAMIC_BALANCED",
                    visual_metaphor_type="TACTILE_PRODUCT_HUD",
                    primary_object_type="TERMINAL_INTERFACE",
                    layout_structure="INTEGRATED_TERMINAL_FRAME",
                    typography_strategy="TERMINAL_STATUS_MONOSPACE",
                    background_type="WARM_SLATE_STUDIO",
                    color_distribution="HIGH_CONTRAST_CYAN_ACCENTS",
                    depth_strategy="LAYERED_PERSPECTIVE_PLANES",
                    product_integration="REAL_UI_TERMINAL_PERSPECTIVE",
                    information_density="CALIBRATED_TECHNICAL",
                    viewpoint="OBLIQUE_PERSPECTIVE"
                )
            }
            c2 = {
                "concept_id": "B",
                "concept_title": "The Atomic Leverage Handshake: Single-Deposit Composability",
                "treatment_style": "Dual-State Process Visualization",
                "visual_thesis": "Before-and-after comparison showing 150% capital drag transformed into 10x capital efficiency.",
                "visual_metaphor": "Kinetic mechanical multiplier turning a single input into multi-venue force.",
                "fingerprint": StructuralCreativeFingerprint(
                    composition_type="ASYMMETRICAL_SPLIT",
                    symmetry="ASYMMETRICAL",
                    visual_metaphor_type="MECHANICAL_CALIBRATION",
                    primary_object_type="SCULPTURAL_EQUILIBRIUM",
                    layout_structure="HERO_WITH_DATA_RAILS",
                    typography_strategy="OVERSIZED_STATEMENT_WITH_CHIPS",
                    background_type="DEEP_OBSIDIAN_VOID",
                    color_distribution="VIOLET_FUCHSIA_AMBIENT_BLOOMS",
                    depth_strategy="SHALLOW_FIELD_MACRO",
                    product_integration="SUB_MODULE_HUD_CHIPS",
                    information_density="MINIMAL_EXECUTIVE",
                    viewpoint="FRONTAL_ELEVATION"
                )
            }
            c3 = {
                "concept_id": "C",
                "concept_title": "The Sovereign Balance Sheet Specimen",
                "treatment_style": "Editorial Financial Specimen",
                "visual_thesis": "Clean typographic specimen contrasting isolated credit accounts against pooled counterparty risk.",
                "visual_metaphor": "An audited financial ledger certificate with cryptographic verification seals.",
                "fingerprint": StructuralCreativeFingerprint(
                    composition_type="EDITORIAL_TYPOGRAPHIC_DATA",
                    symmetry="BILATERAL",
                    visual_metaphor_type="EDITORIAL_DATA_GRID",
                    primary_object_type="DATA_STREAM_MATRIX",
                    layout_structure="EXPANSIVE_FIELD_WITH_ANCHOR",
                    typography_strategy="EDITORIAL_HEADLINE_DATA_SPLIT",
                    background_type="CLEAN_DARK_CANVAS",
                    color_distribution="MONOCHROME_WITH_MINT_CONFIRMATION",
                    depth_strategy="FLAT_TECHNICAL_PROJECTION",
                    product_integration="SCHEMATIC_SPECIFICATION",
                    information_density="DATA_RICH_EDITORIAL",
                    viewpoint="FRONTAL_ELEVATION"
                )
            }
        elif content_type == "market_data_insight":
            c1 = {
                "concept_id": "A",
                "concept_title": "The Polynomial Yield Strata: Algorithmic Rate Optimization",
                "treatment_style": "Editorial Data Visualization",
                "visual_thesis": "Layered translucent strata illustrating polynomial lending rates optimizing yields across utilization curves.",
                "visual_metaphor": "Geological strata of crystallized financial value with illuminated depth contours.",
                "fingerprint": StructuralCreativeFingerprint(
                    composition_type="VERTICAL_TIERED_STACK",
                    symmetry="DYNAMIC_BALANCED",
                    visual_metaphor_type="PHYSICAL_MATERIAL",
                    primary_object_type="LAYERED_STRATA",
                    layout_structure="HERO_WITH_DATA_RAILS",
                    typography_strategy="EDITORIAL_HEADLINE_DATA_SPLIT",
                    background_type="DEEP_OBSIDIAN_VOID",
                    color_distribution="HIGH_CONTRAST_CYAN_ACCENTS",
                    depth_strategy="LAYERED_PERSPECTIVE_PLANES",
                    product_integration="NONE_PURE_METAPHOR",
                    information_density="DATA_RICH_EDITORIAL",
                    viewpoint="OBLIQUE_PERSPECTIVE"
                )
            }
            c2 = {
                "concept_id": "B",
                "concept_title": "The Fixed-Gas Sovereign Benchmark: 0.00014 XLM vs EVM",
                "treatment_style": "Information-Led Comparative Data Board",
                "visual_thesis": "Authoritative statistical matrix proving Soroban fixed fee immunity during peak market volatility.",
                "visual_metaphor": "A high-precision scientific spectrometer recording zero volatility distortion.",
                "fingerprint": StructuralCreativeFingerprint(
                    composition_type="EDITORIAL_TYPOGRAPHIC_DATA",
                    symmetry="ASYMMETRICAL",
                    visual_metaphor_type="EDITORIAL_DATA_GRID",
                    primary_object_type="DATA_STREAM_MATRIX",
                    layout_structure="SPLIT_PERSPECTIVE_VIEW",
                    typography_strategy="ENGINEERED_COORDINATE_STAMPS",
                    background_type="TECHNICAL_GRID_SUBSTRATE",
                    color_distribution="MONOCHROME_WITH_MINT_CONFIRMATION",
                    depth_strategy="FLAT_TECHNICAL_PROJECTION",
                    product_integration="SUB_MODULE_HUD_CHIPS",
                    information_density="DATA_RICH_EDITORIAL",
                    viewpoint="FRONTAL_ELEVATION"
                )
            }
            c3 = {
                "concept_id": "C",
                "concept_title": "The Gravitational Yield Horizon: Institutional Liquidity Flow",
                "treatment_style": "Cosmic Physical Metaphor",
                "visual_thesis": "Massive capital reservoirs establishing stable gravitational orbital paths for institutional depositors.",
                "visual_metaphor": "Gravitational potential well where capital settles into minimum-risk orbits.",
                "fingerprint": StructuralCreativeFingerprint(
                    composition_type="MINIMALIST_ORBITAL",
                    symmetry="RADIAL",
                    visual_metaphor_type="COSMIC_GRAVITATIONAL",
                    primary_object_type="SCULPTURAL_EQUILIBRIUM",
                    layout_structure="EXPANSIVE_FIELD_WITH_ANCHOR",
                    typography_strategy="OVERSIZED_STATEMENT_WITH_CHIPS",
                    background_type="ATMOSPHERIC_HAZE",
                    color_distribution="WARM_CHAMFER_SPECULAR",
                    depth_strategy="SHALLOW_FIELD_MACRO",
                    product_integration="NONE_PURE_METAPHOR",
                    information_density="MINIMAL_EXECUTIVE",
                    viewpoint="AERIAL_TOP_DOWN"
                )
            }
        elif content_type == "risk_security_concept":
            c1 = {
                "concept_id": "A",
                "concept_title": "The Hydro-Dynamic Dampening Field: 1.10x Solvency Horizon",
                "treatment_style": "Physical Shock Absorption Metaphor",
                "visual_thesis": "Volatile market pressure strikes an engineered dampening barrier, diffusing harmlessly before reaching the liquidation threshold.",
                "visual_metaphor": "A precision hydraulic surge arrestor preserving structural equilibrium.",
                "fingerprint": StructuralCreativeFingerprint(
                    composition_type="ASYMMETRICAL_SPLIT",
                    symmetry="DYNAMIC_BALANCED",
                    visual_metaphor_type="HYDRO_DYNAMIC_FLOW",
                    primary_object_type="CRYSTALLINE_BARRIER",
                    layout_structure="HERO_WITH_DATA_RAILS",
                    typography_strategy="ENGINEERED_COORDINATE_STAMPS",
                    background_type="DEEP_OBSIDIAN_VOID",
                    color_distribution="HIGH_CONTRAST_CYAN_ACCENTS",
                    depth_strategy="SHALLOW_FIELD_MACRO",
                    product_integration="NONE_PURE_METAPHOR",
                    information_density="CALIBRATED_TECHNICAL",
                    viewpoint="OBLIQUE_PERSPECTIVE"
                )
            }
            c2 = {
                "concept_id": "B",
                "concept_title": "The Quarantined Bulkhead: Sovereign Debt Isolation",
                "treatment_style": "Structural Containment Architecture",
                "visual_thesis": "Watertight submarine bulkheads where localized debt default is quarantined without affecting adjacent pools.",
                "visual_metaphor": "Hermetically sealed industrial chambers under dynamic pressure test.",
                "fingerprint": StructuralCreativeFingerprint(
                    composition_type="SECTIONAL_ARCHITECTURAL_CUTAWAY",
                    symmetry="ASYMMETRICAL",
                    visual_metaphor_type="ARCHITECTURAL_CONTAINMENT",
                    primary_object_type="ISOMETRIC_VAULT_SECTION",
                    layout_structure="SPLIT_PERSPECTIVE_VIEW",
                    typography_strategy="OVERSIZED_STATEMENT_WITH_CHIPS",
                    background_type="TECHNICAL_GRID_SUBSTRATE",
                    color_distribution="MONOCHROME_WITH_MINT_CONFIRMATION",
                    depth_strategy="ISOMETRIC_INFINITE_DEPTH",
                    product_integration="SCHEMATIC_SPECIFICATION",
                    information_density="CALIBRATED_TECHNICAL",
                    viewpoint="ISOMETRIC_30_DEGREE"
                )
            }
            c3 = {
                "concept_id": "C",
                "concept_title": "The Optical Caustic Deflection: Sub-Second Telemetry",
                "treatment_style": "Optical Caustic Metaphor",
                "visual_thesis": "An intense incoming laser vector bent safely into a closed stable loop by an optical leaded prism.",
                "visual_metaphor": "Precision laser refraction avoiding a lower hazard plane.",
                "fingerprint": StructuralCreativeFingerprint(
                    composition_type="CENTRAL_MONOLITH",
                    symmetry="BILATERAL",
                    visual_metaphor_type="OPTICAL_REFRACTION",
                    primary_object_type="CRYSTALLINE_BARRIER",
                    layout_structure="EXPANSIVE_FIELD_WITH_ANCHOR",
                    typography_strategy="MINIMALIST_CAPSULE_TAGS",
                    background_type="CLEAN_DARK_CANVAS",
                    color_distribution="VIOLET_FUCHSIA_AMBIENT_BLOOMS",
                    depth_strategy="SHALLOW_FIELD_MACRO",
                    product_integration="NONE_PURE_METAPHOR",
                    information_density="MINIMAL_EXECUTIVE",
                    viewpoint="MACRO_EYE_LEVEL"
                )
            }
        else:  # ecosystem_integration
            c1 = {
                "concept_id": "A",
                "concept_title": "The Modular Liquidity Confluence: Vanna + Blend Vaults",
                "treatment_style": "Ecosystem Relationship Visualization",
                "visual_thesis": "Sovereign SmartAccounts acting as a programmatic conduit docking cleanly into Blend's $148M liquidity pools.",
                "visual_metaphor": "An advanced orbital docking mechanism uniting specialized modules into a larger station.",
                "fingerprint": StructuralCreativeFingerprint(
                    composition_type="ASYMMETRICAL_SPLIT",
                    symmetry="DYNAMIC_BALANCED",
                    visual_metaphor_type="MECHANICAL_CALIBRATION",
                    primary_object_type="MODULAR_DOCK",
                    layout_structure="HERO_WITH_DATA_RAILS",
                    typography_strategy="ENGINEERED_COORDINATE_STAMPS",
                    background_type="TECHNICAL_GRID_SUBSTRATE",
                    color_distribution="HIGH_CONTRAST_CYAN_ACCENTS",
                    depth_strategy="LAYERED_PERSPECTIVE_PLANES",
                    product_integration="SUB_MODULE_HUD_CHIPS",
                    information_density="CALIBRATED_TECHNICAL",
                    viewpoint="OBLIQUE_PERSPECTIVE"
                )
            }
            c2 = {
                "concept_id": "B",
                "concept_title": "The Cross-Protocol Highway: Soroban Protocol 20 Mesh",
                "treatment_style": "Infrastructure Network Architecture",
                "visual_thesis": "Streamlined high-speed optical conduits linking Freighter wallet, Soroswap AMM, and Vanna margin accounts.",
                "visual_metaphor": "An illuminated fiber-optic backbone connecting discrete regional data centers.",
                "fingerprint": StructuralCreativeFingerprint(
                    composition_type="HORIZONTAL_PROCESS_FLOW",
                    symmetry="ASYMMETRICAL",
                    visual_metaphor_type="HYDRO_DYNAMIC_FLOW",
                    primary_object_type="KINETIC_FLOW_CONDUIT",
                    layout_structure="SPLIT_PERSPECTIVE_VIEW",
                    typography_strategy="OVERSIZED_STATEMENT_WITH_CHIPS",
                    background_type="DEEP_OBSIDIAN_VOID",
                    color_distribution="VIOLET_FUCHSIA_AMBIENT_BLOOMS",
                    depth_strategy="ISOMETRIC_INFINITE_DEPTH",
                    product_integration="SCHEMATIC_SPECIFICATION",
                    information_density="DATA_RICH_EDITORIAL",
                    viewpoint="ISOMETRIC_30_DEGREE"
                )
            }
            c3 = {
                "concept_id": "C",
                "concept_title": "The Multi-Venue Liquidity Specimen",
                "treatment_style": "Editorial Ecosystem Specimen",
                "visual_thesis": "Authoritative map of Soroban DeFi showing liquidity distribution across native protocols.",
                "visual_metaphor": "An institutional transit map documenting verified high-speed routes.",
                "fingerprint": StructuralCreativeFingerprint(
                    composition_type="EDITORIAL_TYPOGRAPHIC_DATA",
                    symmetry="BILATERAL",
                    visual_metaphor_type="EDITORIAL_DATA_GRID",
                    primary_object_type="DATA_STREAM_MATRIX",
                    layout_structure="EXPANSIVE_FIELD_WITH_ANCHOR",
                    typography_strategy="EDITORIAL_HEADLINE_DATA_SPLIT",
                    background_type="CLEAN_DARK_CANVAS",
                    color_distribution="MONOCHROME_WITH_MINT_CONFIRMATION",
                    depth_strategy="FLAT_TECHNICAL_PROJECTION",
                    product_integration="SUB_MODULE_HUD_CHIPS",
                    information_density="CALIBRATED_TECHNICAL",
                    viewpoint="FRONTAL_ELEVATION"
                )
            }

        return [c1, c2, c3]

    def _build_nano_banana_packet(self, winner: Dict[str, Any], reasoning: Dict[str, str]) -> Dict[str, Any]:
        """Constructs the rich Creative Explainer Diagram Packet for Nano Banana (gemini-3.1-flash-image).

        Strictly enforces the Image 2 and Image 3 Web3 product process explainer style:
        - Clean horizontal process pipeline (A -> B -> C)
        - Big bold metrics and numbers (~320ms, 1.10x, 10x Multiplier, 0.00014 XLM)
        - Dark frosted-glass squircle cards with glowing neon borders
        - Sleek horizontal directional vector arrows
        - Bold titles and clean subtitles beneath each node
        - Deep space obsidian #080310 with Vanna dual ambient blooms (#C73770 top-right, #7430CC bottom-left)
        - NO CINEMATIC LIGHTING, NO VOLUMETRIC FILM PROPS, NO MOVIE SCENES.
        """
        fp: StructuralCreativeFingerprint = winner["fingerprint"]
        directive = reasoning.get("Q01_what_are_we_communicating", "Vanna Protocol on Stellar Soroban")
        key_claim = reasoning.get("key_claim", "0.00014 XLM fixed gas")

        # Dynamically build the 3-stage or 4-stage process flow based on content type and directive
        # The art director's own concept drives the image.
        #
        # This was a five-branch if/else on keywords in the directive, each
        # branch a fully written infographic with its text baked into the
        # prompt — 'LEFT NODE (Telemetry Ingestion)... displaying bold glowing
        # cyan text "~320ms"... a small pill tag "0.00014 XLM Gas"'. So every
        # campaign about risk got the identical three-node diagram, A07's
        # reasoning was discarded, and the model was explicitly told to render
        # text it cannot spell. The creative judge rejected the result for
        # "blatant rendered text and unedited placeholder labels ('LEFT NODE',
        # 'Pill tag')" — those labels were in the prompt.
        #
        # `directive` is `blueprint.visual_metaphor.concept`: what A07 actually
        # art-directed for this campaign, grounded in Vanna's mechanism.
        pipeline_desc = (
            "Depict this specific mechanism as a clear left-to-right "
            "architectural relationship: " + str(directive).strip() + " "
            "Show it with geometry, proportion, containment and connection — "
            "discrete sealed units versus one shared volume, a quantity "
            "approaching a boundary, a path routed outward and returning. "
            "Do not label anything; the relationships must read from form alone."
        )
        title_text = "Vanna Protocol on Stellar Soroban"
        sub_text = str(winner.get("visual_thesis") or "")[:70]

        prompt_text = (
            f"A clean horizontal process flow DeFi architectural explainer diagram for {title_text}. "
            f"Style: Modern Web3 Dark Mode UI, clean isometric pseudo-3D vector geometry combined with flat 2D vector elements, "
            f"soft glows, razor-sharp line work, generous negative space. "
            f"Background: Deep space obsidian #080310 with signature Vanna ambient blooms: luminous fuchsia-pink #C73770 in top-right "
            f"and vibrant electric royal violet #7430CC in bottom-left, with fine 35mm digital film grain. "
            f"NO CINEMATIC LIGHTING, NO VOLUMETRIC FILM PROPS, NO MOVIE SCENES. PURE CLEAN FINTECH PRODUCT EXPLAINER DIAGRAM. "
            # The canvas is rendered TEXTLESS on purpose. `_composite_brand_finish`
            # draws the title and subtitle afterwards with PIL, where the words
            # are exactly what we passed in. Asking the image model for a header
            # instead produced invented ticker symbols and misspelt formulas —
            # and once a run leaked a raw provenance tag into `title_text`, the
            # canvas rendered "[Blend Protocol Docs] Blend v2 pool architecture"
            # as its headline. A misspelt figure in an image is a false claim.
            f"Leave the top 22% of the canvas clear, dark and empty for an "
            f"externally composited headline. "
            f"RENDER NO TEXT OF ANY KIND: no words, letters, numerals, labels, "
            f"axis ticks, formulas, ticker symbols, percentages or captions "
            f"anywhere on the canvas. Express quantity and relationship through "
            f"geometry, proportion and position only. "
            f"CRITICAL BRAND INVARIANT: Do NOT render any Vanna logo, emblem, V-icon, wordmark, or pill badge on the image canvas. "
            f"Keep the top-left corner completely clear and dark, as the official Vanna brand badge is composited externally. "
            f"There must be ZERO logos or Vanna pill badges rendered by the image model anywhere on the canvas. "
            f"{pipeline_desc} "
            f"CRITICAL: Keep upper-right and top-left corners clear of decorative badges. Clean, crisp, legible, vector-like diagram precision."
        )

        return {
            "communication_objective": reasoning["Q01_what_are_we_communicating"],
            "target_audience": reasoning["Q02_who_is_the_audience"],
            "key_message": reasoning["Q03_viewer_comprehension_2_sec"],
            "desired_viewer_reaction": "Immediate recognition of engineered institutional superiority and mathematical safety.",
            "creative_thesis": winner["visual_thesis"],
            "visual_metaphor": winner["visual_metaphor"],
            "art_direction_style": winner["treatment_style"],
            "composition_fingerprint": fp.to_dict(),
            "reference_principles_borrowed": reasoning["Q07_reference_principles_borrowed"],
            "anti_copy_constraints": reasoning["Q08_reference_elements_NOT_copied"],
            "brand_constraints": "Obsidian base #080310, ambient fuchsia/violet blooms, 35mm film grain, generous negative space (>65%).",
            "factual_constraints": "Must accurately communicate sovereign SmartAccount state isolation without false claims.",
            "things_to_avoid": [
                "Rendering any Vanna logo or V-icon or pill badge on the image canvas (only external top-left lockup allowed)",
                "Duplicate branding or logos",
                "Cinematic volumetric movie scenes or raytraced film props",
                "Generic glowing spheres with concentric rings",
                "Any rendered text, numeral, formula, ticker symbol or label",
                "Any cryptocurrency glyph or coin prop — no Bitcoin, Ethereum, "
                "XLM or generic token discs; Vanna is credit infrastructure, "
                "not a currency",
            ],
            "autonomous_decisions_for_image_model": [
                "Exact micro-surface texture and refraction indices",
                "Subtle atmospheric particle drift and caustic dissipation",
                "Edge bevel radius and matte specular falloff"
            ],
            "image_model_prompt": prompt_text
        }
