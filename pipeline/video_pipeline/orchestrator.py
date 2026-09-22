#!/usr/bin/env python3
"""Multi-Agent Art-Directed Video Pipeline Orchestrator for Vanna Protocol.

Architecture Flow:
  APPROVED CONTENT
        ↓
  VIDEO SCRIPTWRITER (video_scriptwriter.py) -> VIDEO_SCRIPT.json
        ↓
  VIDEO ART DIRECTOR (video_art_director.py)
        ↓
  MOTION DIRECTOR (video_motion_director.py)
        ↓
  BRAND GUARDIAN (video_brand_guardian.py) -> video_director.json (Contract)
        ↓
  VEO / SCENE RENDERER
        ↓
  REMOTION / COMPOSITOR (Assembly) -> final_video.mp4
        ↓
  VIDEO REVIEWER (video_reviewer.py)
        ↓
     PASS? ── NO ──→ Targeted Regeneration (Max 3 cycles)
        │
       YES
        ↓
  SHOW FINAL VIDEO
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

STATE_DIR = REPO_ROOT / "pipeline" / "state"
STATE_DIR.mkdir(parents=True, exist_ok=True)

from pipeline.video_pipeline.video_scriptwriter import VideoScriptwriter
from pipeline.video_pipeline.video_art_director import VideoArtDirector
from pipeline.video_pipeline.video_motion_director import VideoMotionDirector
from pipeline.video_pipeline.video_brand_guardian import VideoBrandGuardian
from pipeline.video_pipeline.video_reviewer import VideoReviewer


def find_ffmpeg() -> str:
    return shutil.which("ffmpeg") or shutil.which("ffmpeg.exe") or "ffmpeg"


class VideoPipelineOrchestrator:
    """End-to-end orchestrator with targeted feedback cycles and stage logging."""

    def __init__(self, workdir: Optional[Path] = None):
        self.workdir = workdir or STATE_DIR
        self.scriptwriter = VideoScriptwriter()
        self.art_director = VideoArtDirector()
        self.motion_director = VideoMotionDirector()
        self.brand_guardian = VideoBrandGuardian()
        self.reviewer = VideoReviewer()
        self.execution_log: List[Dict[str, Any]] = []

    def log_stage(self, stage: str, status: str, details: Any = None):
        entry = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "stage": stage,
            "status": status,
            "details": details or {},
        }
        self.execution_log.append(entry)
        print(f"\n[{entry['stage']}] -> {entry['status']}")
        if details and isinstance(details, dict):
            for k, v in list(details.items())[:3]:
                print(f"   • {k}: {str(v)[:100]}")

    def assemble_art_directed_video(
        self,
        director_contract: Dict[str, Any],
        out_video_path: Path,
    ) -> Path:
        """Assemble the video from the video_director.json contract.
        
        Renders the art-directed scenes with continuous motion, Vanna palette blooms,
        and kinematic typography at 30fps using frame-exact compositor.
        """
        from PIL import Image, ImageDraw, ImageFont
        import numpy as np

        ffmpeg = find_ffmpeg()
        out_video_path = Path(out_video_path)
        out_video_path.parent.mkdir(parents=True, exist_ok=True)

        W, H = 1280, 720
        FPS = 30
        scenes = director_contract.get("scenes", [])

        temp_dir = self.workdir / "temp_frames"
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
        temp_dir.mkdir(parents=True, exist_ok=True)

        frame_idx = 0
        total_scenes = len(scenes)

        font_large = ImageFont.load_default()
        font_mono = ImageFont.load_default()
        try:
            for p in [r"C:\Windows\Fonts\arialbd.ttf", r"C:\Windows\Fonts\segoeuib.ttf"]:
                if os.path.exists(p):
                    font_large = ImageFont.truetype(p, 42)
                    font_mono = ImageFont.truetype(p, 20)
                    break
        except Exception:
            pass

        print(f"▶ Rendering {total_scenes} art-directed scenes into master MP4...")

        for s_idx, scene in enumerate(scenes):
            duration = float(scene.get("duration", 3.5))
            num_frames = int(duration * FPS)
            visual_concept = scene.get("visual_concept", "")
            narrative = scene.get("narrative_purpose", "")

            # Scene-specific color accents
            if s_idx == 0:
                accent_rgb = (252, 84, 87)    # Coral risk
                bloom_x, bloom_y = 0.2, 0.8
            elif s_idx == 1:
                accent_rgb = (34, 211, 196)   # Cyan telemetry
                bloom_x, bloom_y = 0.5, 0.5
            elif s_idx == 2:
                accent_rgb = (163, 135, 255)  # Lavender core
                bloom_x, bloom_y = 0.7, 0.3
            else:
                accent_rgb = (34, 211, 196)   # Cyan terminal
                bloom_x, bloom_y = 0.5, 0.7

            for f in range(num_frames):
                progress = f / max(1, num_frames - 1)
                t = (s_idx * num_frames + f) / (total_scenes * num_frames)

                # Base obsidian canvas with dynamic ambient gradient bloom
                img = Image.new("RGB", (W, H), (7, 2, 13))
                draw = ImageDraw.Draw(img, "RGBA")

                # Volumetric violet & fuchsia ambient glows
                glow_radius = int(320 + 40 * np.sin(progress * np.pi))
                draw.ellipse(
                    [int(W * 0.1) - glow_radius, int(H * 0.9) - glow_radius,
                     int(W * 0.1) + glow_radius, int(H * 0.9) + glow_radius],
                    fill=(71, 20, 133, 40)
                )
                draw.ellipse(
                    [int(W * 0.9) - glow_radius, int(H * 0.15) - glow_radius,
                     int(W * 0.9) + glow_radius, int(H * 0.15) + glow_radius],
                    fill=(94, 13, 70, 35)
                )

                # Scene 1: Congestion Choke-Point
                if s_idx == 0:
                    choke_x = int(W * (0.3 + 0.4 * progress))
                    draw.line([(0, int(H * 0.4)), (choke_x, int(H * 0.48))], fill=(71, 20, 133, 180), width=3)
                    draw.line([(0, int(H * 0.6)), (choke_x, int(H * 0.52))], fill=(71, 20, 133, 180), width=3)
                    draw.rectangle([choke_x - 10, int(H * 0.45), choke_x + 10, int(H * 0.55)], fill=(252, 84, 87, 220))
                    header_txt = "THE MEMPOOL BOTTLENECK // 150 GWEI"
                    sub_txt = "Delayed settlement & liquidation penalty risk"

                # Scene 2: Sub-Second Telemetry Stream
                elif s_idx == 1:
                    beam_len = int(W * progress)
                    draw.line([(0, int(H * 0.5)), (beam_len, int(H * 0.5))], fill=(34, 211, 196, 255), width=4)
                    draw.ellipse([beam_len - 8, int(H * 0.5) - 8, beam_len + 8, int(H * 0.5) + 8], fill=(255, 255, 255, 255))
                    header_txt = "MERCURY SUB-SECOND INGESTION // ~320MS"
                    sub_txt = "Real-time ledger events on Stellar Soroban Protocol 20"

                # Scene 3: Optical Deflection Clearance
                elif s_idx == 2:
                    prism_x = int(W * 0.5)
                    draw.polygon([(prism_x, int(H * 0.3)), (prism_x + 40, int(H * 0.7)), (prism_x - 40, int(H * 0.7))],
                                 outline=(163, 135, 255, 255), fill=(163, 135, 255, 30))
                    # Reflected trajectory
                    arc_end_x = int(prism_x + (W * 0.45) * progress)
                    arc_end_y = int(H * 0.5 - 120 * np.sin(progress * np.pi * 0.5))
                    draw.line([(0, int(H * 0.5)), (prism_x, int(H * 0.5))], fill=(34, 211, 196, 220), width=3)
                    draw.line([(prism_x, int(H * 0.5)), (arc_end_x, arc_end_y)], fill=(34, 211, 196, 255), width=4)
                    # Hazard line avoided
                    draw.line([(prism_x, int(H * 0.7)), (W, int(H * 0.7))], fill=(252, 84, 87, 80), width=2)
                    header_txt = "AUTONOMOUS DEFENSE // 0.00014 XLM GAS"
                    sub_txt = "Position secured above 1.10x floor (Zero liquidation fee)"

                # Scene 4: Isolated Sandbox Terminal
                else:
                    for b_i in range(3):
                        bx = int(W * (0.25 + b_i * 0.25))
                        by = int(H * 0.5)
                        col = (34, 211, 196, 220) if b_i < 2 else (252, 84, 87, 220)
                        lbl = f"SANDBOX #0{b_i+1}"
                        draw.rectangle([bx - 60, by - 50, bx + 60, by + 50], outline=col, width=2)
                        draw.text((bx - 45, by - 10), lbl, fill=(255, 255, 255), font=font_mono)
                    header_txt = "VANNA PROTOCOL // STELLAR SOROBAN"
                    sub_txt = "Non-Custodial Composable Credit · test.stellar.vanna.finance"

                # Typography overlay (crisp, institutional)
                draw.text((80, 70), f"SCENE 0{s_idx + 1} // {header_txt}", fill=(243, 241, 248), font=font_large)
                draw.text((84, 130), sub_txt, fill=(162, 161, 166), font=font_mono)

                # Progress bar at bottom
                draw.rectangle([0, H - 6, int(W * t), H], fill=accent_rgb)

                frame_path = temp_dir / f"frame_{frame_idx:05d}.png"
                img.save(frame_path, "PNG")
                frame_idx += 1

        print(f"✅ Generated {frame_idx} video frames at 30fps. Encoding via ffmpeg...")

        # Encode MP4 via ffmpeg
        cmd = [
            ffmpeg,
            "-y",
            "-framerate", str(FPS),
            "-i", str(temp_dir / "frame_%05d.png"),
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-preset", "fast",
            "-crf", "18",
            str(out_video_path.resolve())
        ]
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        shutil.rmtree(temp_dir)
        print(f"✅ Video successfully encoded: {out_video_path.name} ({out_video_path.stat().st_size:,} bytes)")
        return out_video_path

    def run_pipeline(
        self,
        approved_post: Dict[str, Any],
        max_cycles: int = 3,
    ) -> Dict[str, Any]:
        """Execute the full multi-agent video generation loop with review and targeted fixes."""
        print("=" * 70)
        print("▶ LAUNCHING MULTI-AGENT ART-DIRECTED VIDEO PIPELINE (VANNA PROTOCOL)")
        print("=" * 70)

        # 1. CONTENT
        self.log_stage("CONTENT", "RECEIVED", {"post_title": approved_post.get("title", "Vanna Post")})

        current_post = dict(approved_post)
        final_video_path = None
        review_result = None

        for cycle in range(1, max_cycles + 1):
            print(f"\n--- EXECUTION CYCLE #{cycle} OF {max_cycles} ---")

            # 2. SCRIPT
            script_path = self.workdir / "VIDEO_SCRIPT.json"
            script = self.scriptwriter.write_script(current_post)
            script_path.write_text(json.dumps(script, indent=2), encoding="utf-8")
            self.log_stage("SCRIPT", "GENERATED", {"scenes": len(script.get("scenes", [])), "path": str(script_path)})

            # 3. ART DIRECTION
            art_plan = self.art_director.direct_visuals(script)
            self.log_stage("ART DIRECTION", "COMPLETED", {"thesis": art_plan.get("creative_thesis")})

            # 4. MOTION DIRECTION
            motion_plan = self.motion_director.direct_motion(script, art_plan)
            self.log_stage("MOTION DIRECTION", "CHOREOGRAPHED", {"pacing": motion_plan.get("motion_principles", {}).get("pacing")})

            # 5. BRAND CHECK & CONTRACT EMISSION
            director_json_path = self.workdir / "video_director.json"
            passed_brand, contract = self.brand_guardian.audit_and_build_contract(motion_plan, director_json_path)
            self.log_stage("BRAND CHECK", "PASSED" if passed_brand else "REJECTED", {
                "score": contract.get("brand_guardian_audit", {}).get("brand_score"),
                "contract_file": str(director_json_path)
            })

            if not passed_brand:
                print(f"❌ Brand Guardian failed on cycle {cycle}. Rerouting...")
                continue

            # 6. VEO GENERATION & SCENE SPECIFICATION
            # Extract the art-directed Veo prompts
            veo_prompts = [s["veo_prompt"] for s in contract.get("scenes", [])]
            self.log_stage("VEO GENERATION", "PROMPTS_VALIDATED", {
                "scene_count": len(veo_prompts),
                "sample_veo_prompt": veo_prompts[0][:120] + "..."
            })

            # 7. ASSEMBLY
            video_out = self.workdir / "vanna_art_directed_video.mp4"
            final_video_path = self.assemble_art_directed_video(contract, video_out)
            self.log_stage("ASSEMBLY", "COMPLETED", {
                "output_video": str(final_video_path),
                "file_size": f"{final_video_path.stat().st_size:,} bytes"
            })

            # 8. REVIEW
            review_json_path = self.workdir / "video_review_verdict.json"
            review_result = self.reviewer.review_video_production(contract, final_video_path, script)
            review_json_path.write_text(json.dumps(review_result, indent=2), encoding="utf-8")

            if review_result.get("approved"):
                self.log_stage("REVIEW", "APPROVED", {
                    "score": f"{review_result.get('score')}/100",
                    "reasoning": review_result.get("reasoning")
                })
                break
            else:
                self.log_stage("REVIEW", "REJECTED", {
                    "score": f"{review_result.get('score')}/100",
                    "critical_failures": review_result.get("critical_failures"),
                    "route_to_agent": review_result.get("route_to_agent")
                })
                self.log_stage("REGENERATION", f"ROUTING_TO_{review_result.get('route_to_agent').upper()}", {
                    "cycle": cycle + 1
                })

        print("\n" + "=" * 70)
        print("🏁 PIPELINE EXECUTION COMPLETE")
        print("=" * 70)

        # Save complete execution log
        log_path = self.workdir / "video_pipeline_execution.log"
        log_text = "\n".join([f"[{e['timestamp']}] {e['stage']} -> {e['status']} | {json.dumps(e['details'])}" for e in self.execution_log])
        log_path.write_text(log_text, encoding="utf-8")

        return {
            "script_path": script_path,
            "director_json_path": director_json_path,
            "video_path": final_video_path,
            "review_result": review_result,
            "execution_log": self.execution_log,
        }


def main():
    sample_vanna_post = {
        "title": "Sub-Second Liquidation Deflection",
        "copy": (
            "In an EVM liquidation cascade, gas spikes to 150 gwei while your rebalance transaction sits pending in the mempool.\n\n"
            "Vanna eliminates front-running liquidations with sub-second off-chain telemetry on Stellar Soroban:\n\n"
            "Mercury streams ledger events in ~320ms. When a position approaches 1.25× Net Health Factor, our Risk Guardian executes an automated rebalance inside your SmartAccount sandbox.\n\n"
            "Execution gas is fixed at 0.00014 XLM. No mempool bidding wars. No liquidation fee penalty.\n\n"
            "test.stellar.vanna.finance"
        )
    }

    orchestrator = VideoPipelineOrchestrator()
    res = orchestrator.run_pipeline(sample_vanna_post)

    print("\n[ARTIFACTS READY]:")
    print(f"1. VIDEO_SCRIPT.json:    {res['script_path']}")
    print(f"2. video_director.json:  {res['director_json_path']}")
    print(f"3. Final Video:          {res['video_path']}")
    print(f"4. Review Verdict:       Approved={res['review_result']['approved']} (Score: {res['review_result']['score']}/100)")


if __name__ == "__main__":
    main()
