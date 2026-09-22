"""
Update corpus_coverage.json and ingest logic for FIX 3 and FIX 4.
"""
import json
from pathlib import Path
from pipeline.gtm_orchestration.config import BRAIN_DB_DIR, BRAIN_ROOT, CANONICAL_KNOWLEDGE_ROOT

DB_DIR = Path("D:/new orchestration/pipeline/gtm_engine/brain/db")
INTEL_DIR = BRAIN_DB_DIR
CHECKPOINT_FILE = Path("D:/new orchestration/pipeline/gtm_engine/registry/tier1_checkpoint.jsonl")

def update_corpus_coverage():
    for target_dir in (DB_DIR, INTEL_DIR):
        cov_file = target_dir / "corpus_coverage.json"
        if cov_file.exists():
            data = json.loads(cov_file.read_text(encoding="utf-8"))
            data["roster_scope"] = "FIRST_BATCH_10_OF_34"
            data["total_promoted_in_census"] = 34
            data["batch_count"] = 10
            data["x_collection_status"] = "TRUNCATED_AT_20"
            data["x_cadence_reliable"] = False
            data["cadence_derivation_policy"] = "BLOG_AND_FORUM_ONLY (X excluded due to page-size cap)"
            
            for p in data.get("players", []):
                p["x_collection_status"] = "TRUNCATED_AT_20"
                p["x_cadence_reliable"] = False
                p["limitations"].append("X timeline capped at 20 items by CLI cursor; cadence derived from blog/forum only")

            cov_file.write_text(json.dumps(data, indent=2), encoding="utf-8")
            print(f"✅ Updated {cov_file}")

if __name__ == "__main__":
    update_corpus_coverage()
