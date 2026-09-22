"""Strict Pydantic schemas for Phase 5 Creative Director & Visual System.

Enforces:
  - Visual concepts must be derived from communication objectives, not raw posts.
  - Multi-format generation support (Static Vector, Gemini Static Image, Veo 3.1 Video).
  - Explicit anti-slop rejection filters (blocks glowing spheres, Tron grids, fake dashboards).
"""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field


class VisualMetaphorSpec(BaseModel):
    """The central creative metaphor explaining the product primitive."""
    thesis: str
    concept: str
    metaphor: str
    composition: str
    lighting: str
    materials: str
    negative_elements: List[str] = Field(default_factory=list)


class CreativeFormatSpec(BaseModel):
    """Generator-specific instruction payload compiled from the visual brief."""
    format_type: Literal["STATIC_VECTOR", "STATIC_IMAGE", "VEO_VIDEO_31", "MEME_IMAGE"]
    dimensions: str
    framerate: Optional[int] = None
    duration_seconds: Optional[int] = None
    conditioning_asset: Optional[str] = None
    compiled_prompt: str


class CompleteCreativeBlueprint(BaseModel):
    """Master creative blueprint contract governing all generators."""
    creative_id: str
    strategy_id: str
    communication_objective: str
    visual_metaphor: VisualMetaphorSpec
    brand_tokens: Dict[str, Any]
    typography_hierarchy: Dict[str, str]
    format_specs: Dict[str, CreativeFormatSpec]
    negative_constraints: List[str]
    created_at: str


class CreativeValidationResult(BaseModel):
    """Audit gate output verifying brand compliance and absence of AI slop."""
    creative_id: str
    approved: bool
    score: int
    generator_bypass_prevented: bool
    slop_violations: List[str] = Field(default_factory=list)
    brand_compliance: bool
    reasoning: str
