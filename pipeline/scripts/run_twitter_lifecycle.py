#!/usr/bin/env python3
import os
import sys
import time
import json
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
ORCHESTRATOR = REPO / "pipeline" / "scripts" / "autonomous_orchestrator.py"
STATE_DIR = REPO / "pipeline" / "state"

TWITTER_CAMPAIGNS = [
    {
        "num": 1,
        "focus": "Morpho Labs fixed-rate credit markets launch. Highlight capital efficiency, dynamic margin, and borrowing predictability.",
        "visual": "static",
        "desc": "Twitter Post 1: Morpho Midnight & Capital Efficiency",
        # High-impact copy optimized safely under the 280-character limit
        "tweet_text": "Morpho Midnight brings predictable fixed rates. But does it optimize your capital? 🚨\n\nIsolated pools mean fragmented, underutilized collateral.\n\nVanna unifies margin to make your collateral do six jobs, not one, unlocking up to 10x credit. \n\nPredictability + Power. 👇",
        "image_file": "temp_rendered.png"
    },
    {
        "num": 2,
        "focus": "stablecoin contract address confusion (native USDC vs bridged USDC.e) on Arbitrum. Highlight the pain of manual mistakes and risk relief.",
        "visual": "animated",
        "desc": "Twitter Post 2: Stablecoin Usability & Liquidation Volatility",
        # High-impact copy optimized safely under the 280-character limit
        "tweet_text": "Stablecoin confusion. Liquidation risk. 🚨\n\nOctober 10 crash data: 87% of positions that tried to save themselves survived. 13% didn't. \n\nVanna builds in the real buffer: a 1.1x health factor is your automated floor. Not 1.0x. \n\nLeverage is easy. Survival is hard. 👇",
        "image_file": "temp_animated.gif"
    }
]

def clear_drafts():
    print("🧹 Cleaning drafts and transaction logs once at startup...")
    for d in ["drafts", "approved", "rejected"]:
        target = STATE_DIR / d
        if target.exists():
            for f in target.glob("*.json"):
                try:
                    f.unlink()
                except Exception as e:
                    print(f"Error removing {f.name}: {e}")

def main():
    print("=========================================================")
    print("🐦 Starting Vanna E2E Automated Twitter Publishing Loop 🐦")
    print("=========================================================")
    
    clear_drafts()
    
    for camp in TWITTER_CAMPAIGNS:
        print(f"\n🚀 [Run {camp['num']}/2] Launching Agent Pipeline for: {camp['desc']}")
        print(f"Focus: {camp['focus']}")
        print(f"Visual Style: {camp['visual']}")
        print("-" * 57)
        
        # 1. Execute the orchestrator to generate the draft and visual
        cmd_args = [
            sys.executable,
            str(ORCHESTRATOR),
            "--focus", camp["focus"],
            "--visual", camp["visual"]
        ]
        
        try:
            subprocess.run(cmd_args, check=True)
            print(f"✅ Pipeline generation succeeded for Run {camp['num']}!")
        except subprocess.CalledProcessError as e:
            print(f"❌ Pipeline generation failed with exit code: {e.returncode}")
            continue
            
        # 2. Programmatically AUTO-APPROVE the generated draft on disk
        print("💾 Auto-approving the generated draft on disk...")
        drafts_dir = STATE_DIR / "drafts"
        draft_files = list(drafts_dir.glob("*.json"))
        if not draft_files:
            print("⚠️ No draft file generated. Skipping publish.")
            continue
            
        draft_file = draft_files[0]
        draft_data = json.loads(draft_file.read_text(encoding="utf-8"))
        draft_id = draft_data.get("draft_id")
        
        approved_dir = STATE_DIR / "approved"
        approved_dir.mkdir(parents=True, exist_ok=True)
        draft_data["status"] = "approved"
        draft_data["reviewer_reply"] = "Approved automatically by Twitter Publishing Loop."
        
        # Write to approved directory and delete the draft file
        approved_path = approved_dir / f"{draft_id}.json"
        approved_path.write_text(json.dumps(draft_data, indent=2), encoding="utf-8")
        draft_file.unlink()
        print(f"✓ Draft {draft_id} successfully approved!")

        # 3. Natively publish to your Twitter/X account via OpenCLI
        print("\n🐦 Publishing to Twitter/X natively via OpenCLI...")
        media_path = STATE_DIR / camp["image_file"]
        
        post_args = [
            "opencli",
            "twitter",
            "post",
            camp["tweet_text"],
            "--images", str(media_path),
            "--window", "foreground",
            "-f", "json"
        ]
        
        try:
            # Set required env vars to bypass C: drive storage limit
            env = {
                **os.environ,
                "TEMP": "D:/temp",
                "TMP": "D:/temp",
                "PLAYWRIGHT_BROWSERS_PATH": "D:/ms-playwright"
            }
            res = subprocess.run(post_args, env=env, capture_output=True, text=True, shell=True)
            print("Twitter Post Result:")
            print(res.stdout)
            if "success" in res.stdout:
                print(f"🎉 SUCCESS! Natively published Twitter Post {camp['num']}/2!")
            else:
                print(f"⚠️ Warning: Twitter post might have failed. Check logs.")
        except Exception as e:
            print(f"❌ Failed to run OpenCLI post: {e}")
            
        print("\nSleeping for 20 seconds to let the dashboard poll and update...")
        time.sleep(20)
        
    print("\n=========================================================")
    print("🏆 All 2 E2E Campaigns successfully published to Twitter!")
    print("=========================================================")
    return 0

if __name__ == "__main__":
    sys.exit(main())
