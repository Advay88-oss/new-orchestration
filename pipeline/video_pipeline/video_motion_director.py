#!/usr/bin/env python3
"""Agent 3: MOTION DIRECTOR (video_motion_director.py)

Role: Choreographs camera, object kinetics, and seamless scene transitions.
Input:
  - VIDEO_SCRIPT.json
  - Art Direction output
Output:
  - Motion specifications ensuring the video feels like one continuous, art-directed film.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


class VideoMotionDirector:
    """Motion Director agent: eliminates slideshow cuts and enforces kinetic film continuity."""

    def direct_motion(self, script: Dict[str, Any], art_direction: Dict[str, Any]) -> Dict[str, Any]:
        """Attach precise motion, timing curves, and match-cut transitions to each scene."""
        scenes = art_direction.get("scenes", [])
        motion_directed_scenes: List[Dict[str, Any]] = []

        total_scenes = len(scenes)
        for i, s in enumerate(scenes):
            scene_id = s.get("scene_id", i + 1)
            duration = s.get("duration", 4.0)

            # Define continuous camera kinetics that carry momentum into the next scene
            if scene_id == 1:
                motion_choreography = {
                    "camera_kinetic": "Forward push along corridor Z-axis: 0 to 120 units at cubic-bezier(0.4, 0.0, 0.2, 1)",
                    "object_kinetic": "Sluggish fluid particles decelerating as choke-point narrows; viscosity increases",
                    "timing_breakdown": {
                        "in_transition": "0.0s to 0.5s: Fade in from deep obsidian void",
                        "climax_event": "2.8s: Corridor contracts into intense crimson warning node",
                        "settle_and_pass": "3.5s to 4.0s: Camera reaches focal choke-point, aligning directly into optical axis",
                    },
                    "continuous_transition_out": {
                        "type": "kinetic_match_cut",
                        "mechanism": "The narrow choke-point becomes the origin point for the high-velocity beam in Scene 2",
                        "overlap_duration": 0.4,
                    },
                    "moments_of_emphasis": [
                        {"timestamp": 2.5, "action": "Subtle bass pulse in lighting as gas spike reaches peak"}
                    ],
                }
            elif scene_id == 2:
                motion_choreography = {
                    "camera_kinetic": "Lateral high-speed tracking shot: matches beam velocity at linear(0, 1) then eases into lens",
                    "object_kinetic": "Laminar beam expands outward with zero turbulence (~320ms velocity impulse)",
                    "timing_breakdown": {
                        "in_transition": "0.0s to 0.4s: Seamless match-cut burst from Scene 1 choke-point",
                        "climax_event": "2.0s: Telemetry pulse node illuminates the entire horizontal axis",
                        "settle_and_pass": "3.6s to 4.0s: Beam slows into the focal threshold prism of Scene 3",
                    },
                    "continuous_transition_out": {
                        "type": "refractive_optical_wipe",
                        "mechanism": "The beam enters the front face of the crystalline prism, camera rotates 20 degrees with it",
                        "overlap_duration": 0.5,
                    },
                    "moments_of_emphasis": [
                        {"timestamp": 0.32, "action": "Sub-second 320ms latency milestone flash in pure cyan"}
                    ],
                }
            elif scene_id == 3:
                motion_choreography = {
                    "camera_kinetic": "Orbital arc: smooth 35-degree rotation around prism center of mass at ease-in-out",
                    "object_kinetic": "Deflection arc: trajectory bends gracefully upward into parallel trajectory",
                    "timing_breakdown": {
                        "in_transition": "0.0s to 0.5s: Refractive optical entry from Scene 2",
                        "climax_event": "1.8s: 1.25x trigger deflection point flashes with specular glint",
                        "settle_and_pass": "3.5s to 4.0s: Cyan trajectory levels out into perfectly calm horizontal orbit",
                    },
                    "continuous_transition_out": {
                        "type": "depth_pull_match_cut",
                        "mechanism": "Camera pulls back through the stable orbit line to reveal the modular vault array",
                        "overlap_duration": 0.5,
                    },
                    "moments_of_emphasis": [
                        {"timestamp": 1.8, "action": "Specular reflection glint on prism corner as danger path is avoided"}
                    ],
                }
            else:
                motion_choreography = {
                    "camera_kinetic": "Slow vertical crane-up (Y-axis +40 units) and pitch down (-15 degrees) settling into lock",
                    "object_kinetic": "Breathing luminescence: internal vault glows pulse slowly at 0.5 Hz harmonic frequency",
                    "timing_breakdown": {
                        "in_transition": "0.0s to 0.5s: Pull-back reveal from Scene 3 trajectory",
                        "climax_event": "1.5s: Vanna protocol monogram and endpoint resolve with crisp 1-frame opacity lock",
                        "settle_and_pass": "2.5s to 3.0s: Final hold on pristine institutional architecture before clean fade",
                    },
                    "continuous_transition_out": {
                        "type": "fade_to_obsidian",
                        "mechanism": "Gradual exposure drop into #07020D void",
                        "overlap_duration": 0.5,
                    },
                    "moments_of_emphasis": [
                        {"timestamp": 1.5, "action": "Terminal endpoint lock: test.stellar.vanna.finance"}
                    ],
                }

            s_copy = dict(s)
            s_copy["motion_choreography"] = motion_choreography
            motion_directed_scenes.append(s_copy)

        art_direction_copy = dict(art_direction)
        art_direction_copy["scenes"] = motion_directed_scenes
        art_direction_copy["motion_principles"] = {
            "pacing": "Continuous cinematic momentum with match-cut velocity preservation",
            "frame_rate": 30,
            "anti_slideshow_rule": "Every scene exit geometry directly informs the next scene entrance geometry",
        }
        return art_direction_copy


def apply_motion_direction(script: Dict[str, Any], art_direction: Dict[str, Any], out_path: Optional[Path] = None) -> Dict[str, Any]:
    md = VideoMotionDirector()
    motion_plan = md.direct_motion(script, art_direction)
    if out_path:
        out_path = Path(out_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(motion_plan, indent=2), encoding="utf-8")
        print(f"✅ VIDEO MOTION DIRECTOR: Applied motion kinetics to {out_path.name}")
    return motion_plan
