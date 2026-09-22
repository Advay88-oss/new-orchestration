"""Pydantic schema for machine-readable motion_design_spec.json.

Defines scene-by-scene motion, kinetic typography, shape choreography,
data visualization, easing, and narrative meaning.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class KineticTypographySpec(BaseModel):
    primary_text: str = Field(..., description="Main headline or statement")
    secondary_text: Optional[str] = Field(None, description="Supporting claim or parameter")
    highlight_words: List[str] = Field(default_factory=list, description="Words to receive brand accent gradient")
    stagger_frames: int = Field(default=3, description="Frames between word reveals")
    animation_style: str = Field(default="word-stagger-converge", description="Type of kinetic typography animation")
    font_family: str = Field(default="Plus Jakarta Sans", description="Primary font")
    font_size: int = Field(default=72, description="Font size in pixels for 1080p")
    text_color: str = Field(default="#F3F0F8", description="Hex color")
    tracking: str = Field(default="-0.03em", description="Letter spacing")


class ShapeChoreographySpec(BaseModel):
    primitive: str = Field(..., description="Chassis, hexagon, lattice, boundary, beam, or prism")
    motion_type: str = Field(..., description="Assemble, branch, deflect, expand, compress, quarantine")
    start_coordinates: Dict[str, Any] = Field(default_factory=dict)
    end_coordinates: Dict[str, Any] = Field(default_factory=dict)
    stroke_color: str = Field(default="#A387FF")
    fill_color: Optional[str] = Field(default=None)
    glow_color: Optional[str] = Field(default=None)
    anticipation_frames: int = Field(default=6)
    overshoot_percent: float = Field(default=1.05)


class DataVizSpec(BaseModel):
    metric_type: str = Field(..., description="Counter, gauge, trajectory, or threshold_rail")
    start_value: float = Field(default=0.0)
    end_value: float = Field(default=1.0)
    display_suffix: str = Field(default="")
    duration_frames: int = Field(default=30)
    curve: str = Field(default="bezier(0.16, 1, 0.3, 1)")
    alarm_threshold: Optional[float] = Field(None)


class SceneMotionSpec(BaseModel):
    scene_id: str = Field(..., description="Unique scene identifier")
    scene_index: int = Field(..., description="0-indexed scene order")
    start_frame: int = Field(..., description="Starting frame (30fps)")
    end_frame: int = Field(..., description="Ending frame (30fps)")
    duration_frames: int = Field(..., description="Duration in frames")
    duration_seconds: float = Field(..., description="Duration in seconds")
    narrative_purpose: str = Field(..., description="What concept or feeling is communicated")
    motion_meaning: str = Field(..., description="Physical or topological metaphor (expansion, compression, etc.)")
    typography: KineticTypographySpec
    shapes: List[ShapeChoreographySpec] = Field(default_factory=list)
    data_visualization: Optional[DataVizSpec] = None
    camera_movement: str = Field(default="slow_push_in", description="Camera or parallax instruction")
    transition_in: str = Field(default="hard_cut_ground_flip", description="Entry transition")
    transition_out: str = Field(default="directional_slide_left", description="Exit transition")
    easing: str = Field(default="cubic-bezier(0.16, 1, 0.3, 1)")
    background_color: str = Field(default="#0D0616")
    accent_color: str = Field(default="#703AE6")
    sound_cue: str = Field(default="low_sub_thud")


class MotionDesignSpec(BaseModel):
    title: str = Field(..., description="Video title")
    product: str = Field(default="Vanna Protocol")
    target_duration_seconds: float = Field(default=24.0)
    total_frames: int = Field(default=720)
    fps: int = Field(default=30)
    width: int = Field(default=1920)
    height: int = Field(default=1080)
    design_system: Dict[str, str] = Field(
        default_factory=lambda: {
            "bg": "#0D0616",
            "obsidian": "#07020D",
            "violet": "#703AE6",
            "violet_lt": "#9F7BEE",
            "rose": "#FC5457",
            "cyan": "#32EEE2",
            "paper": "#F3F0F8",
            "muted": "#A99FC0",
            "faint": "#6B6280",
            "green": "#41D99B",
        }
    )
    scenes: List[SceneMotionSpec]
    critic_verdict: Optional[str] = None
    critic_score: Optional[float] = None
