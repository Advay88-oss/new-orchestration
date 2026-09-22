#!/usr/bin/env python3
"""Creative Memory Store (pipeline/creative_memory/creative_memory_store.py).

Maintains persistent creative memory for Vanna video production:
  - Approved videos ledger (approved_videos.jsonl)
  - Rejected videos ledger (rejected_videos.jsonl)
  - Evaluated creative concepts (creative_concepts.jsonl)
  - Reviewer critic feedback (critic_feedback.jsonl)
  - Reinforcement learning reward ledger (reward_ledger.jsonl)
  - Multi-dimensional structural similarity engine (semantic != visual novelty)
"""

from __future__ import annotations

import json
import math
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

MEMORY_DIR = REPO_ROOT / "pipeline" / "creative_memory"
MEMORY_DIR.mkdir(parents=True, exist_ok=True)

APPROVED_FILE = MEMORY_DIR / "approved_videos.jsonl"
REJECTED_FILE = MEMORY_DIR / "rejected_videos.jsonl"
CONCEPTS_FILE = MEMORY_DIR / "creative_concepts.jsonl"
CRITIC_FILE = MEMORY_DIR / "critic_feedback.jsonl"
REWARD_FILE = MEMORY_DIR / "reward_ledger.jsonl"


class CreativeMemoryStore:
    """Manages creative memory, similarity auditing, and reinforcement logging."""

    def __init__(self, memory_dir: Optional[Path] = None):
        self.memory_dir = memory_dir or MEMORY_DIR
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        self.approved_file = self.memory_dir / "approved_videos.jsonl"
        self.rejected_file = self.memory_dir / "rejected_videos.jsonl"
        self.concepts_file = self.memory_dir / "creative_concepts.jsonl"
        self.critic_file = self.memory_dir / "critic_feedback.jsonl"
        self.reward_file = self.memory_dir / "reward_ledger.jsonl"

    def read_jsonl(self, path: Path) -> List[Dict[str, Any]]:
        if not path.exists():
            return []
        records = []
        for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
            line = line.strip()
            if line:
                try:
                    records.append(json.loads(line))
                except Exception:
                    pass
        return records

    def append_jsonl(self, path: Path, record: Dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")

    def get_approved_videos(self, limit: int = 20) -> List[Dict[str, Any]]:
        records = self.read_jsonl(self.approved_file)
        return records[-limit:]

    def get_rejected_videos(self, limit: int = 20) -> List[Dict[str, Any]]:
        records = self.read_jsonl(self.rejected_file)
        return records[-limit:]

    def record_concept_exploration(self, run_id: str, topic: str, concepts: List[Dict[str, Any]], selected_id: str) -> None:
        rec = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "run_id": run_id,
            "topic": topic,
            "total_concepts_explored": len(concepts),
            "selected_concept_id": selected_id,
            "concepts": concepts
        }
        self.append_jsonl(self.concepts_file, rec)

    def record_approved_video(self, video_data: Dict[str, Any]) -> None:
        entry = dict(video_data)
        entry["timestamp"] = datetime.now(timezone.utc).isoformat()
        self.append_jsonl(self.approved_file, entry)

    def record_rejected_video(self, video_data: Dict[str, Any], reason: str, reviewer_report: Dict[str, Any]) -> None:
        entry = dict(video_data)
        entry["timestamp"] = datetime.now(timezone.utc).isoformat()
        entry["rejection_reason"] = reason
        entry["reviewer_report"] = reviewer_report
        self.append_jsonl(self.rejected_file, entry)

    def record_reward(self, run_id: str, concept_id: str, scores: Dict[str, float], total_reward: float) -> None:
        rec = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "run_id": run_id,
            "concept_id": concept_id,
            "scores": scores,
            "total_reward": round(total_reward, 3)
        }
        self.append_jsonl(self.reward_file, rec)

    # -------------------------------------------------------------------------
    # MULTI-DIMENSIONAL STRUCTURAL SIMILARITY ENGINE
    # -------------------------------------------------------------------------

    def compute_structural_similarity(
        self,
        candidate: Dict[str, Any],
        reference: Dict[str, Any]
    ) -> Tuple[float, Dict[str, float]]:
        """Computes structural similarity across 10 distinct visual/creative dimensions.
        
        Returns:
            (overall_similarity_score [0.0 - 1.0], breakdown_dict)
        """
        # 1. Visual Language & Metaphor overlap
        c_lang = (candidate.get("visual_language") or "").lower()
        r_lang = (reference.get("visual_language") or "").lower()
        lang_sim = self._jaccard_similarity(c_lang, r_lang)

        c_meta = (candidate.get("visual_metaphor") or "").lower()
        r_meta = (reference.get("visual_metaphor") or "").lower()
        meta_sim = self._jaccard_similarity(c_meta, r_meta)

        # 2. Camera & Motion Language overlap
        c_cam = (candidate.get("camera_language") or "").lower()
        r_cam = (reference.get("camera_language") or "").lower()
        cam_sim = self._jaccard_similarity(c_cam, r_cam)

        c_mot = (candidate.get("motion_language") or "").lower()
        r_mot = (reference.get("motion_language") or "").lower()
        mot_sim = self._jaccard_similarity(c_mot, r_mot)

        # 3. Typography & Pacing overlap
        c_typ = (candidate.get("typography_language") or "").lower()
        r_typ = (reference.get("typography_language") or "").lower()
        typ_sim = self._jaccard_similarity(c_typ, r_typ)

        # 4. Product Screen Integration Match
        c_prod = bool(candidate.get("use_product_screen", False))
        r_prod = bool(reference.get("use_product_screen", False))
        prod_sim = 1.0 if c_prod == r_prod else 0.0

        # 5. Production Strategy / Toolchain Match
        c_strat = (candidate.get("generation_strategy") or "").lower()
        r_strat = (reference.get("generation_strategy") or "").lower()
        strat_sim = self._jaccard_similarity(c_strat, r_strat)

        # 6. Scene Plan Structure & Beat Count
        c_scenes = candidate.get("scene_plan", [])
        r_scenes = reference.get("scene_plan", [])
        scene_count_diff = abs(len(c_scenes) - len(r_scenes))
        scene_struct_sim = max(0.0, 1.0 - (scene_count_diff * 0.25))

        # Weighted aggregate similarity
        weights = {
            "visual_language": 0.20,
            "visual_metaphor": 0.25,
            "camera_choreography": 0.15,
            "motion_language": 0.10,
            "typography_style": 0.10,
            "product_integration": 0.05,
            "production_strategy": 0.05,
            "scene_structure": 0.10
        }

        breakdown = {
            "visual_language": round(lang_sim, 3),
            "visual_metaphor": round(meta_sim, 3),
            "camera_choreography": round(cam_sim, 3),
            "motion_language": round(mot_sim, 3),
            "typography_style": round(typ_sim, 3),
            "product_integration": round(prod_sim, 3),
            "production_strategy": round(strat_sim, 3),
            "scene_structure": round(scene_struct_sim, 3),
        }

        total_sim = sum(breakdown[k] * weights[k] for k in weights)
        return round(total_sim, 3), breakdown

    def audit_concept_novelty(
        self,
        candidate: Dict[str, Any],
        max_allowed_similarity: float = 0.55
    ) -> Tuple[bool, float, Optional[Dict[str, Any]], Dict[str, float]]:
        """Audits candidate concept against all approved historical videos.
        
        Returns:
            (is_novel: bool, max_similarity: float, closest_reference: dict, worst_breakdown: dict)
        """
        approved = self.get_approved_videos(limit=25)
        if not approved:
            return True, 0.0, None, {}

        highest_sim = 0.0
        closest_ref = None
        worst_breakdown = {}

        for ref in approved:
            sim, breakdown = self.compute_structural_similarity(candidate, ref)
            if sim > highest_sim:
                highest_sim = sim
                closest_ref = ref
                worst_breakdown = breakdown

        is_novel = highest_sim < max_allowed_similarity
        return is_novel, highest_sim, closest_ref, worst_breakdown

    @staticmethod
    def _jaccard_similarity(text_a: str, text_b: str) -> float:
        words_a = set(re.findall(r"\w+", text_a.lower()))
        words_b = set(re.findall(r"\w+", text_b.lower()))
        if not words_a or not words_b:
            return 0.0
        intersection = len(words_a & words_b)
        union = len(words_a | words_b)
        return intersection / union if union > 0 else 0.0
