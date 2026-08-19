#!/usr/bin/env python3
import os
import sys
import time
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
ORCHESTRATOR = REPO / "pipeline" / "scripts" / "autonomous_orchestrator.py"

def main():
    print("=========================================================")
    print("👑 Starting Vanna Two-Run Dynamic Campaign Loop 👑")
    print("=========================================================")
    
    # 1. First Dynamic Run
    print("\n🚀 Launching Dynamic Campaign Run 1/2...")
    print("This run will automatically select Vanna as infrastructure/positioning.")
    print("-" * 57)
    
    cmd_args1 = [
        sys.executable,
        str(ORCHESTRATOR),
        "--visual", "static"  # Enforce static only as requested!
    ]
    
    try:
        subprocess.run(cmd_args1, check=True)
        print("\n✅ Run 1/2 completed successfully!")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Run 1/2 failed with exit code: {e.returncode}")
        return 1

    print("\nSleeping for 15 seconds to let the dashboard poll and let the history settle...")
    time.sleep(15)

    # 2. Second Dynamic Run
    print("\n🚀 Launching Dynamic Campaign Run 2/2...")
    print("This run will read the updated history and rotate to a completely different topic!")
    print("-" * 57)
    
    cmd_args2 = [
        sys.executable,
        str(ORCHESTRATOR),
        "--visual", "static"  # Enforce static only as requested!
    ]
    
    try:
        subprocess.run(cmd_args2, check=True)
        print("\n✅ Run 2/2 completed successfully!")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Run 2/2 failed with exit code: {e.returncode}")
        return 1
        
    print("\n=========================================================")
    print("🎉 Both consecutive dynamic runs finished! Check your Telegram!")
    print("=========================================================")
    return 0

if __name__ == "__main__":
    sys.exit(main())
