"""Spend Proxy Watchdog & Auto-Spawning Health Guardian.
Fixes Blocker 10 (Spend Proxy Reliability & Process Watchdog).

Features:
  - Non-blocking health check on http://127.0.0.1:8900/_spend.
  - Auto-spawns vertex_spend_proxy.py if down.
  - Provides a fail-safe local budget tracker if port 8900 cannot be bound.
  - Prevents scripts from crashing on URLError or timeout.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path
from typing import Any, Dict

REPO_ROOT = Path(__file__).resolve().parents[2]
STATE_DIR = REPO_ROOT / "pipeline" / "state"
SPEND_FILE = STATE_DIR / "local_spend_tracker.json"
PROXY_SCRIPT = REPO_ROOT / "pipeline" / "scripts" / "vertex_spend_proxy.py"
PROXY_URL = "http://127.0.0.1:8900/_spend"


def is_proxy_alive(timeout: float = 1.0) -> bool:
    """Checks if the spend proxy on port 8900 is responding."""
    try:
        req = urllib.request.Request(PROXY_URL, headers={"User-Agent": "SpendWatchdog/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            if resp.status == 200:
                data = json.loads(resp.read().decode())
                return "spent_usd" in data or "total_spend" in data or "budget_usd" in data
    except Exception:
        return False
    return False


def get_spend_metrics() -> Dict[str, Any]:
    """Fetches spend metrics from live proxy or fallback local store."""
    if is_proxy_alive(timeout=1.5):
        try:
            req = urllib.request.Request(PROXY_URL, headers={"User-Agent": "SpendWatchdog/1.0"})
            with urllib.request.urlopen(req, timeout=1.5) as resp:
                data = json.loads(resp.read().decode())
                data["source"] = "LIVE_PROXY_8900"
                return data
        except Exception:
            pass

    # No proxy: today's numbers from the spend ledger every paid call is
    # counted in. Never a made-up starting figure — when the ledger cannot be
    # read, it says so and reports nothing as spent-or-left.
    try:
        from pipeline.ops import budget as B
        cfg = B.config()
        rows = B.spent(strict=True)
        spent = round(sum(v["usd"] for v in rows.values()), 4)
        cap = float(cfg.get("daily_usd", 15))
        return {"spent_usd": spent, "budget_usd": cap, "cap_usd": cap,
                "remaining_usd": round(max(0.0, cap - spent), 4),
                "calls_total": int(sum(v["calls"] for v in rows.values())),
                "by_service": rows, "source": "OPS_LEDGER"}
    except Exception as exc:                        # noqa: BLE001 — reported as unknown
        return {"spent_usd": None, "budget_usd": None, "cap_usd": None, "remaining_usd": None,
                "calls_total": None, "source": "UNAVAILABLE", "error": str(exc)[:200]}


def ensure_proxy_running() -> Dict[str, Any]:
    """Ensures spend proxy is alive, spawning it in background if necessary."""
    if is_proxy_alive(timeout=1.0):
        return {"status": "RUNNING", "metrics": get_spend_metrics()}

    print("⚠️ Spend Proxy :8900 is offline. Spawning vertex_spend_proxy.py in background...")
    if PROXY_SCRIPT.exists():
        try:
            # Spawn detached background process
            if sys.platform == "win32":
                exe = sys.executable
                if exe.lower().endswith("python.exe"):
                    windowless = exe[: -len("python.exe")] + "pythonw.exe"
                    if os.path.isfile(windowless):
                        exe = windowless
                subprocess.Popen(
                    [exe, str(PROXY_SCRIPT)],
                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP | 0x08000000,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    cwd=str(REPO_ROOT)
                )
            else:
                subprocess.Popen(
                    [sys.executable, str(PROXY_SCRIPT)],
                    start_new_session=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    cwd=str(REPO_ROOT)
                )

            # Wait briefly for startup
            for _ in range(6):
                time.sleep(0.5)
                if is_proxy_alive(timeout=0.5):
                    print("✅ Spend Proxy :8900 successfully spawned and responding.")
                    return {"status": "SPAWNED", "metrics": get_spend_metrics()}
        except Exception as e:
            print(f"⚠️ Could not spawn spend proxy background process: {e}")

    # Graceful fallback so caller never crashes
    print("ℹ️ Falling back to Local Spend Watchdog Store.")
    return {"status": "FALLBACK_LOCAL", "metrics": get_spend_metrics()}


if __name__ == "__main__":
    result = ensure_proxy_running()
    print(f"Spend Proxy Status: {result['status']}")
    print(f"Metrics: {json.dumps(result['metrics'], indent=2)}")
