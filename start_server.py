"""Persistent Localhost Supervisor for Mission Control & Spend Proxy.

Keeps both services running 24/7 with auto-restart on exit:
  - Next.js Mission Control: http://localhost:3000 (with 4GB memory)
  - Vertex Spend Watchdog:   http://127.0.0.1:8900/_spend
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

REPO_ROOT = Path("D:/new orchestration").resolve()
MISSION_ROOT = REPO_ROOT / "hermes-mission"
LOG_FILE = REPO_ROOT / "pipeline" / "logs" / "localhost_supervisor.log"
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

node = shutil.which("node") or "node"
next_bin = str(MISSION_ROOT / "node_modules" / "next" / "dist" / "bin" / "next")
spend_script = str(REPO_ROOT / "pipeline" / "scripts" / "vertex_spend_proxy.py")

print(f"Starting Localhost Supervisor...")
print(f"  Next.js Target: {MISSION_ROOT}")
print(f"  Logging to:     {LOG_FILE}")

with open(LOG_FILE, "a", encoding="utf-8") as log:
    log.write(f"\n--- [{time.strftime('%Y-%m-%d %H:%M:%S')}] Supervisor starting services ---\n")
    log.flush()

    # 1. Kill any stale node or proxy processes
    subprocess.run(["cmd.exe", "/c", "taskkill /F /IM node.exe"], capture_output=True)

    # 2. Start spend proxy
    proxy_proc = subprocess.Popen(
        [sys.executable, spend_script, "--port", "8900"],
        cwd=str(REPO_ROOT),
        stdout=log,
        stderr=log
    )

    # 3. Start Next.js with 4GB heap
    next_proc = subprocess.Popen(
        [node, "--max-old-space-size=4096", next_bin, "dev", "-p", "3000", "-H", "0.0.0.0"],
        cwd=str(MISSION_ROOT),
        stdout=log,
        stderr=log
    )

    log.write(f"Services initialized. Next.js PID: {next_proc.pid}, Proxy PID: {proxy_proc.pid}\n")
    log.flush()

    print(f"✓ Services initialized (Next.js PID: {next_proc.pid}, Proxy PID: {proxy_proc.pid})")

    # Supervisor keepalive & auto-restart loop
    while True:
        try:
            time.sleep(2)
            if proxy_proc.poll() is not None:
                log.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Proxy exited with code {proxy_proc.poll()}. Restarting...\n")
                log.flush()
                proxy_proc = subprocess.Popen(
                    [sys.executable, spend_script, "--port", "8900"],
                    cwd=str(REPO_ROOT),
                    stdout=log,
                    stderr=log
                )

            if next_proc.poll() is not None:
                log.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Next.js exited with code {next_proc.poll()}. Restarting...\n")
                log.flush()
                next_proc = subprocess.Popen(
                    [node, "--max-old-space-size=4096", next_bin, "dev", "-p", "3000", "-H", "0.0.0.0"],
                    cwd=str(MISSION_ROOT),
                    stdout=log,
                    stderr=log
                )
        except KeyboardInterrupt:
            break
        except Exception as e:
            log.write(f"Supervisor error: {e}\n")
            log.flush()
            time.sleep(2)
