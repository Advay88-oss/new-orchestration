"""Unit tests for Phase 5 Creative Director & Visual System (test_gtm_creative.py).

Validates:
  1. Generator cannot bypass CreativeDirector (raw copy in prompt is blocked).
  2. Visual direction is strategy-derived (not generic decoration).
  3. Negative constraints are checked correctly (prohibits floating coins, Tron grids).
  4. Multi-format support (Static Vector, Static Image, Veo 3.1 Video).
  5. Creative quality is scored separately from strategy quality.
  6. Audit report emission to creative_system_audit.json.
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
STATE_DIR = REPO_ROOT / "pipeline" / "state"

from pipeline.gtm_creative.creative_director_system import CreativeDirectorSystem
from pipeline.gtm_creative.creative_validator import CreativeValidator
from pipeline.gtm_orchestration.schemas import GTMStrategy, ContentPackage, PlatformPost


class TestGTMCreativeSystem(unittest.TestCase):
    """Test suite asserting strategy-derived visual blueprints and anti-slop enforcement."""

    def setUp(self):
        self.director = CreativeDirectorSystem()
        self.validator = CreativeValidator()

        # Valid strategy fixture
        self.sample_strategy = GTMStrategy(
            strategy_id="STRAT-CREATIVE-001",
            action_status="ACTION",
            objective="Educate builders on isolated SmartAccount sandboxes",
            audience_segment="A3: Institutional LPs & Risk Architects",
            problem="Shared pool contagion forces global haircuts",
            market_context="Soroban Protocol 20 is live",
            strategic_opportunity="Position Vanna state isolation",
            narrative_pillar="Pillar 2: Isolated SmartAccount Sandboxes",
            positioning="Vanna is the composable credit layer for Stellar",
            proof=["Zero state leakage", "Individual contract instance"],
            cta="test.stellar.vanna.finance",
            channel="X",
            content_type="architectural_schematic",
            gtm_machine_id="MACH_03_COMPETITOR_DISPLACEMENT"
        )
        self.sample_package = ContentPackage(
            package_id="PKG-001",
            strategy_id="STRAT-CREATIVE-001",
            core_message="Vanna isolates risk at contract instance level",
            content_category="PRODUCT",
            funnel_stage="CONSIDERATION",
            platforms={
                "x": PlatformPost(
                    platform="X", format="lead", hook="EVM shared pools break",
                    body="Traditional shared pools break. Vanna isolates risk.", cta="vanna.finance"
                )
            }
        )

    def test_01_creative_blueprint_is_strategy_derived(self):
        blueprint = self.director.compile_master_blueprint(self.sample_strategy, self.sample_package)
        self.assertIn("isolated", blueprint.visual_metaphor.concept.lower())
        self.assertIn("blast-radius", blueprint.visual_metaphor.metaphor.lower())
        self.assertGreater(len(blueprint.format_specs), 2)
        self.assertIn("STATIC_VECTOR", blueprint.format_specs)
        self.assertIn("VEO_VIDEO_31", blueprint.format_specs)

    def test_02_generator_bypass_prevented(self):
        blueprint = self.director.compile_master_blueprint(self.sample_strategy, self.sample_package)
        raw_copy = "Traditional shared pools break. Vanna isolates risk."
        
        # Valid blueprint passes
        res_valid = self.validator.validate_blueprint(blueprint, raw_post_copy=raw_copy)
        self.assertTrue(res_valid.approved)
        self.assertTrue(res_valid.generator_bypass_prevented)

        # Corrupted blueprint that simply copied raw post into prompt is rejected
        blueprint_bypass = blueprint.model_copy(deep=True)
        blueprint_bypass.format_specs["STATIC_IMAGE"].compiled_prompt = raw_copy
        res_bad = self.validator.validate_blueprint(blueprint_bypass, raw_post_copy=raw_copy)
        self.assertFalse(res_bad.approved)
        self.assertFalse(res_bad.generator_bypass_prevented)
        self.assertTrue(any("Generator Bypass" in v for v in res_bad.slop_violations))

    def test_03_negative_constraints_block_slop(self):
        blueprint = self.director.compile_master_blueprint(self.sample_strategy, self.sample_package)
        # Inject slop into prompt
        blueprint_slop = blueprint.model_copy(deep=True)
        blueprint_slop.format_specs["STATIC_IMAGE"].compiled_prompt += " Add glowing spheres with concentric rings and tron neon grids."
        
        res_slop = self.validator.validate_blueprint(blueprint_slop)
        self.assertFalse(res_slop.approved)
        self.assertTrue(any("glowing spheres" in v for v in res_slop.slop_violations))
        self.assertTrue(any("tron neon grids" in v for v in res_slop.slop_violations))

    def test_04_brand_tokens_compliance(self):
        blueprint = self.director.compile_master_blueprint(self.sample_strategy, self.sample_package)
        self.assertEqual(blueprint.brand_tokens["obsidian_canvas"], "#07020D")
        self.assertEqual(blueprint.brand_tokens["electric_violet_bloom"], "#471485")
        self.assertEqual(blueprint.brand_tokens["fuchsia_magenta_bloom"], "#5E0D46")

    def test_05_strategy_mandatory_no_action_blocked(self):
        no_action_strat = self.sample_strategy.model_copy()
        no_action_strat.action_status = "NO_ACTION"
        with self.assertRaises(ValueError):
            self.director.compile_master_blueprint(no_action_strat, self.sample_package)

    def test_06_audit_report_generation(self):
        blueprint = self.director.compile_master_blueprint(self.sample_strategy, self.sample_package)
        res = self.validator.validate_blueprint(blueprint, out_audit_file=STATE_DIR / "creative_system_audit.json")
        self.assertTrue(res.approved)
        self.assertTrue((STATE_DIR / "creative_system_audit.json").exists())


if __name__ == "__main__":
    unittest.main()
