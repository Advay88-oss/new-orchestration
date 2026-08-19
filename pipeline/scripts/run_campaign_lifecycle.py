#!/usr/bin/env python3
import os
import sys
import time
import subprocess
import shutil
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
ORCHESTRATOR = REPO / "pipeline" / "scripts" / "autonomous_orchestrator.py"
STATE_DIR = REPO / "pipeline" / "state"

CAMPAIGNS = [
    {
        "num": 1,
        "focus": "Morpho Labs fixed-rate credit markets launch. Highlight capital efficiency and borrowing predictability.",
        "visual": "static",
        "desc": "Static Visual Campaign: Morpho Midnight Launch"
    },
    {
        "num": 2,
        "focus": "stablecoin contract address confusion (native USDC vs bridged USDC.e) on Arbitrum. Highlight the pain of manual mistakes and risk relief.",
        "visual": "animated",
        "desc": "Animated Visual Campaign: Stablecoin Usability & Liquidation Volatility"
    },
    {
        "num": 3,
        "focus": "Stellar Soroban DeFi primitives, Blend lending, and liquidity fragmentation. Highlight how Vanna builds the credit layer.",
        "visual": "static",
        "desc": "Static Visual Campaign: Stellar Credit Composability"
    },
    {
        "num": 4,
        "focus": "Gearbox Protocol credit agent autonomous policy decision making. Highlight agents making active capital decisions with balance sheets.",
        "visual": "animated",
        "desc": "Animated Visual Campaign: Agentic Credit Autonomy"
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
    print("👑 Starting Vanna E2E Multi-Campaign Content Lifecycle 👑")
    print("=========================================================")
    
    clear_drafts()
    
    for camp in CAMPAIGNS:
        print(f"\n🚀 Launching Campaign {camp['num']}/4: {camp['desc']}")
        print(f"Focus: {camp['focus']}")
        print(f"Visual Style: {camp['visual']}")
        print("-" * 57)
        
        # Build subprocess arguments
        cmd_args = [
            sys.executable,
            str(ORCHESTRATOR),
            "--focus", camp["focus"],
            "--visual", camp["visual"]
        ]
        
        # Execute the orchestrator for this campaign
        try:
            res = subprocess.run(cmd_args, check=True)
            print(f"\n✅ Campaign {camp['num']}/4 completed successfully!")
        except subprocess.CalledProcessError as e:
            print(f"\n❌ Campaign {camp['num']}/4 failed with exit code: {e.returncode}")
            
        print("\nSleeping for 15 seconds to let the dashboard poll and update...")
        time.sleep(15)
        
    print("\n=========================================================")
    print("🎉 All 4 E2E Campaigns completed! Check Telegram & Dashboard!")
    print("=========================================================")
    return 0

if __name__ == "__main__":
    sys.exit(main())
