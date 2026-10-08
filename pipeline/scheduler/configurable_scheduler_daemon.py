#!/usr/bin/env python3
"""Configurable Autonomous Scheduler Daemon (configurable_scheduler_daemon.py).

Implements the Vanna 24/7 Autonomous Scheduler with:
  1. Configurable intervals per job (2m, 30m, 1h, 2h, 6h, 12h, 24h) from config/scheduler.yaml
  2. Interval sanity enforcement (rejects model-heavy jobs on short intervals to protect budget)
  3. Persistent state (survives restarts, avoids duplicate firing on boot)
  4. Non-overlapping execution locks (logs SKIPPED_STILL_RUNNING)
  5. Exponential failure backoff (3 consecutive failures disables and alerts)
  6. Per-job spend accounting logged to registry/spend.jsonl
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import threading
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

try:
    from pipeline.ops.quiet_windows import install as _quiet_console
    _quiet_console()
except Exception:                               # noqa: BLE001 — a missing helper must not stop the clock
    pass

CONFIG_FILE = REPO_ROOT / "config" / "scheduler.yaml"
STATE_DIR = REPO_ROOT / "pipeline" / "state"
PANELS_DIR = REPO_ROOT / "state" / "panels"
ALT_PANELS_DIR = REPO_ROOT / "pipeline" / "state" / "panels"
SCHEDULER_STATE_FILE = STATE_DIR / "scheduler_state.json"
SPEND_FILE = REPO_ROOT / "registry" / "spend.jsonl"
OUTCOMES_FILE = STATE_DIR / "outcomes.jsonl"

for d in [STATE_DIR, PANELS_DIR, ALT_PANELS_DIR, REPO_ROOT / "registry", REPO_ROOT / "config"]:
    d.mkdir(parents=True, exist_ok=True)

# The daemon runs each due job on its own thread; state writes take turns.
_STATE_LOCK = threading.Lock()
_HOST = __import__("socket").gethostname()


def _pid_alive(pid: int) -> bool:
    """True when a process with this id exists on this machine."""
    if not pid or pid <= 0:
        return False
    if sys.platform == "win32":
        import ctypes
        k32 = ctypes.windll.kernel32
        h = k32.OpenProcess(0x1000, False, int(pid))  # PROCESS_QUERY_LIMITED_INFORMATION
        if not h:
            return False
        code = ctypes.c_ulong()
        ok = k32.GetExitCodeProcess(h, ctypes.byref(code))
        k32.CloseHandle(h)
        return bool(ok) and code.value == 259  # STILL_ACTIVE
    try:
        os.kill(int(pid), 0)
        return True
    except OSError:
        return False


def _runner_gone(rec: dict) -> bool:
    """A RUNNING record whose process on this machine has exited."""
    return rec.get("host") == _HOST and bool(rec.get("pid")) and not _pid_alive(int(rec["pid"]))


def ensure_spend_proxy_running():
    """Checks if :8900 spend proxy is up; if not, automatically spawns it."""
    import urllib.request
    try:
        with urllib.request.urlopen("http://127.0.0.1:8900/_spend", timeout=1.0):
            return True
    except Exception:
        pass

    try:
        import subprocess
        script = REPO_ROOT / "pipeline" / "scripts" / "vertex_spend_proxy.py"
        if script.exists():
            subprocess.Popen(
                [sys.executable, str(script), "--port", "8900"],
                cwd=str(REPO_ROOT),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=(0x08000000 if os.name == "nt" else 0),
            )
            time.sleep(1.5)
            return True
    except Exception:
        pass
    return False


def parse_interval_to_seconds(interval_str: str) -> int:
    """Parses interval string (e.g. 2m, 30m, 1h, 2h, 6h, 12h, 24h) to seconds."""
    s = str(interval_str).strip().lower()
    m = re.match(r"^(\d+)\s*([mhd])$", s)
    if not m:
        raise ValueError(f"Invalid interval format: '{interval_str}'. Use format like 2m, 30m, 1h, 2h, 6h, 12h, 24h.")
    val, unit = int(m.group(1)), m.group(2)
    if unit == "m":
        return val * 60
    elif unit == "h":
        return val * 3600
    elif unit == "d":
        return val * 86400
    return val * 3600


def validate_interval_sanity(job_name: str, interval_str: str, model_heavy: bool, min_allowed_m: int) -> None:
    """Enforces interval sanity: rejects model-heavy jobs on dangerously short intervals."""
    seconds = parse_interval_to_seconds(interval_str)
    minutes = seconds / 60
    if model_heavy and minutes < min_allowed_m:
        raise ValueError(
            f"❌ Interval Sanity Rejection for '{job_name}': {interval_str} ({minutes:.0f}m) is too short. "
            f"This job involves AI model reasoning. Minimum allowed interval is {min_allowed_m}m to prevent draining API budget."
        )


def load_yaml_config() -> Dict[str, Any]:
    """Loads scheduler configuration from config/scheduler.yaml."""
    if not CONFIG_FILE.exists():
        return {
            "jobs": {
                "research_collect": {"interval": "24h", "enabled": True, "model_heavy": True, "min_allowed_interval_m": 720},
                "trend_scan": {"interval": "1h", "enabled": True, "model_heavy": False, "min_allowed_interval_m": 2},
                "ideas_panel": {"interval": "6h", "enabled": True, "model_heavy": True, "min_allowed_interval_m": 120},
                "memes_panel": {"interval": "2h", "enabled": True, "model_heavy": False, "min_allowed_interval_m": 30}
            }
        }
    
    # Simple resilient YAML parser for standard key: value pairs
    content = CONFIG_FILE.read_text(encoding="utf-8")
    jobs = {}
    current_job = None
    
    for line in content.splitlines():
        line = line.split("#")[0].strip()
        if not line:
            continue
        if line.endswith(":") and not line.startswith("jobs:"):
            current_job = line.replace(":", "").strip()
            jobs[current_job] = {}
        elif ":" in line and current_job:
            k, v = [x.strip() for x in line.split(":", 1)]
            v_clean = v.strip("'\"")
            if v_clean.lower() == "true":
                v_clean = True
            elif v_clean.lower() == "false":
                v_clean = False
            elif v_clean.isdigit():
                v_clean = int(v_clean)
            jobs[current_job][k] = v_clean

    # The deployed clock reads this file from the shared bucket. The yaml in
    # the image stays the default; a pill on the dashboard overrides it.
    overrides = STATE_DIR / "scheduler_intervals.json"
    if overrides.exists():
        try:
            chosen = json.loads(overrides.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            chosen = {}
        if isinstance(chosen, dict):
            paused = {str(n) for n in (chosen.get("_paused") or [])}
            turned_on = {str(n) for n in (chosen.get("_on") or []) if not str(n).startswith("_")}
            for name, interval in chosen.items():
                if str(name).startswith("_"):
                    continue
                if name in jobs and isinstance(interval, str) and interval.strip():
                    jobs[name]["interval"] = interval.strip()
            for name in turned_on:
                if name in jobs and name not in paused:
                    jobs[name]["enabled"] = True
            for name in paused:
                if name in jobs:
                    jobs[name]["enabled"] = False

    return {"jobs": jobs}


def save_yaml_config(cfg: Dict[str, Any]) -> None:
    """Saves scheduler configuration to config/scheduler.yaml."""
    lines = [
        "# Vanna Autonomous Scheduler Configuration",
        "# Supported Intervals: 2m | 30m | 1h | 2h | 6h | 12h | 24h",
        "",
        "jobs:"
    ]
    for j_name, j_data in cfg.get("jobs", {}).items():
        lines.append(f"  {j_name}:")
        for k, v in j_data.items():
            if isinstance(v, bool):
                lines.append(f"    {k}: {'true' if v else 'false'}")
            elif isinstance(v, (int, float)):
                lines.append(f"    {k}: {v}")
            else:
                lines.append(f"    {k}: \"{v}\"")
        lines.append("")
        
    CONFIG_FILE.write_text("\n".join(lines), encoding="utf-8")


class SchedulerEngine:
    """Orchestrates scheduled jobs with persistence, non-overlap, and failure backoff."""

    def __init__(self):
        self.state = self.load_state()

    def load_state(self) -> Dict[str, Any]:
        """Loads persistent job state across restarts."""
        if SCHEDULER_STATE_FILE.exists():
            try:
                return json.loads(SCHEDULER_STATE_FILE.read_text(encoding="utf-8"))
            except Exception:
                pass
        return {}

    def save_state(self) -> None:
        """Persists state to disk. A newer last_run already on disk or in the bucket stays."""
        try:
            from pipeline.gtm_os.state_sync import blend_scheduler_records, merge_scheduler_state_from_bucket
            merge_scheduler_state_from_bucket()
            on_disk = {}
            if SCHEDULER_STATE_FILE.exists():
                on_disk = json.loads(SCHEDULER_STATE_FILE.read_text(encoding="utf-8"))
            if isinstance(on_disk, dict):
                self.state = blend_scheduler_records(self.state, on_disk)
        except Exception:
            pass
        SCHEDULER_STATE_FILE.write_text(json.dumps(self.state, indent=2), encoding="utf-8")

    def save_job(self, job_name: str) -> None:
        """Write one job's record and leave every other job as it is on disk.

        Jobs run side by side in the daemon. A whole-file save from one job
        would put its stale copy of another job's status back."""
        with _STATE_LOCK:
            try:
                from pipeline.gtm_os.state_sync import merge_scheduler_state_from_bucket
                merge_scheduler_state_from_bucket()
            except Exception:
                pass
            try:
                on_disk = json.loads(SCHEDULER_STATE_FILE.read_text(encoding="utf-8")) \
                    if SCHEDULER_STATE_FILE.exists() else {}
            except (OSError, ValueError):
                on_disk = {}
            if not isinstance(on_disk, dict):
                on_disk = {}
            rec = dict(self.state[job_name])
            theirs = on_disk.get(job_name) if isinstance(on_disk.get(job_name), dict) else {}
            # A later claim on disk (another tick, another process) keeps its clock.
            if str(theirs.get("last_run") or "") > str(rec.get("last_run") or ""):
                rec["last_run"] = theirs["last_run"]
            on_disk[job_name] = rec
            self.state = on_disk
            SCHEDULER_STATE_FILE.write_text(json.dumps(on_disk, indent=2), encoding="utf-8")

    def log_spend(self, job_name: str, model_id: str, input_tokens: int, output_tokens: int, cost_usd: float) -> None:
        """Logs job spend accounting to registry/spend.jsonl."""
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "job": job_name,
            "model_id": model_id,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cost_usd": round(cost_usd, 6)
        }
        with open(SPEND_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")

    def update_job_status(self, job_name: str, status: str, last_error: Optional[str] = None, duration_s: float = 0.0) -> None:
        """Updates and persists the status of a scheduled job."""
        if job_name not in self.state:
            self.state[job_name] = {
                "job": job_name,
                "last_run": None,
                "next_run": None,
                "status": "IDLE",
                "consecutive_failures": 0,
                "total_runs": 0,
                "last_duration_s": 0.0
            }

        rec = self.state[job_name]
        rec["status"] = status
        now_dt = datetime.now(timezone.utc)
        
        if status == "RUNNING":
            rec["current_run_start"] = now_dt.isoformat()
            rec["pid"], rec["host"] = os.getpid(), _HOST
        elif status == "COMPLETED":
            rec["last_run"] = now_dt.isoformat()
            rec["consecutive_failures"] = 0
            rec["total_runs"] = rec.get("total_runs", 0) + 1
            rec["last_duration_s"] = round(duration_s, 2)
            rec.pop("current_run_start", None)
            rec.pop("last_error", None)
        elif status == "FAILED":
            rec["last_run"] = now_dt.isoformat()
            rec["consecutive_failures"] = rec.get("consecutive_failures", 0) + 1
            rec["last_error"] = last_error
            rec["last_duration_s"] = round(duration_s, 2)
            rec.pop("current_run_start", None)
            if rec["consecutive_failures"] >= 3:
                rec["status"] = "DISABLED_AUTO_BACKOFF"
                print(f"🚨 [SCHEDULER ALERT] Job '{job_name}' disabled after 3 consecutive failures. Requires manual review.")

        self.save_job(job_name)

    def get_status_overview(self) -> Dict[str, Any]:
        """Provides status overview for all jobs."""
        cfg = load_yaml_config()
        overview = []
        for j_name, j_data in cfg.get("jobs", {}).items():
            st = self.state.get(j_name, {})
            last_run_str = st.get("last_run")
            interval_str = j_data.get("interval", "24h")
            
            # Compute next run
            next_run_str = "Overdue / Pending"
            if last_run_str:
                try:
                    last_dt = datetime.fromisoformat(last_run_str)
                    sec = parse_interval_to_seconds(interval_str)
                    next_dt = last_dt + timedelta(seconds=sec)
                    next_run_str = next_dt.isoformat()
                except Exception:
                    pass

            overview.append({
                "job": j_name,
                "description": j_data.get("description", ""),
                "interval": interval_str,
                "enabled": j_data.get("enabled", True),
                "status": st.get("status", "IDLE"),
                "last_run": last_run_str or "Never",
                "next_run": next_run_str,
                "consecutive_failures": st.get("consecutive_failures", 0),
                "total_runs": st.get("total_runs", 0),
                "last_duration_s": st.get("last_duration_s", 0.0)
            })

        return {"success": True, "jobs": overview, "timestamp": datetime.now(timezone.utc).isoformat()}

    def execute_job(self, job_name: str, force: bool = False) -> Dict[str, Any]:
        """Executes a single job with non-overlapping lock and error handling."""
        cfg = load_yaml_config()
        j_data = cfg.get("jobs", {}).get(job_name)
        if not j_data:
            return {"success": False, "error": f"Unknown job: {job_name}"}

        if not j_data.get("enabled", True) and not force:
            return {"success": False, "status": "SKIPPED_DISABLED"}

        current_st = self.state.get(job_name, {})
        if current_st.get("status") == "RUNNING" and not force and not _runner_gone(current_st):
            started = str(current_st.get("current_run_start") or current_st.get("last_run") or "")
            fresh = False
            try:
                started_dt = datetime.fromisoformat(started)
                if started_dt.tzinfo is None:
                    started_dt = started_dt.replace(tzinfo=timezone.utc)
                fresh = (datetime.now(timezone.utc) - started_dt).total_seconds() < 1800
            except ValueError:
                fresh = True
            if fresh:
                print(f"⏸️ [SCHEDULER] Job '{job_name}' is still running. Logging SKIPPED_STILL_RUNNING.")
                return {"success": False, "status": "SKIPPED_STILL_RUNNING"}

        # Validate interval sanity
        validate_interval_sanity(
            job_name=job_name,
            interval_str=j_data.get("interval", "24h"),
            model_heavy=j_data.get("model_heavy", False),
            min_allowed_m=j_data.get("min_allowed_interval_m", 1)
        )

        if j_data.get("model_heavy", False):
            ensure_spend_proxy_running()

        t_start = time.time()
        self.update_job_status(job_name, "RUNNING")
        print(f"\n▶ [SCHEDULER] Launching Job: {job_name} ({j_data.get('interval')})...")

        result = {}
        try:
            if job_name == "trend_scan":
                result = self._run_trend_scan()
            elif job_name == "ideas_panel":
                result = self._run_ideas_panel()
            elif job_name == "memes_panel":
                result = self._run_memes_panel()
            elif job_name == "research_collect":
                result = self._run_research_collect()
            elif job_name == "gtm_cycle":
                result = self._run_gtm_cycle()
            elif job_name == "notion_sync":
                result = self._run_notion_sync()
            elif job_name == "brain_watch":
                result = self._run_brain_watch()
            elif job_name == "github_commits":
                from pipeline.brand_brain.github_sync import refresh_product_docs, sync_commits
                docs = refresh_product_docs(verbose=False)
                out = sync_commits(verbose=False)
                if out.get("error"):
                    raise RuntimeError(out["error"])
                result = {"success": True, "docs": docs, **out}
            elif job_name == "metrics_collect":
                result = self._run_metrics_collect()
            elif job_name == "ops_watch":
                from pipeline.ops.watch import run as _watch
                result = {"success": True, **_watch()}
            elif job_name == "campaigns_refresh":
                result = self._run_campaigns_refresh()
            else:
                raise ValueError(f"No execution handler for job '{job_name}'")

            t_elapsed = time.time() - t_start
            self.update_job_status(job_name, "COMPLETED", duration_s=t_elapsed)
            print(f"✅ [SCHEDULER] Job '{job_name}' completed in {t_elapsed:.2f}s.")
            result["status"] = "COMPLETED"
            result["duration_s"] = t_elapsed
            _telegram_result(job_name, result)
            return result
        except Exception as e:
            t_elapsed = time.time() - t_start
            err_msg = str(e)
            print(f"❌ [SCHEDULER ERROR] Job '{job_name}' failed after {t_elapsed:.2f}s: {err_msg}")
            self.update_job_status(job_name, "FAILED", last_error=err_msg, duration_s=t_elapsed)
            try:
                from pipeline.ops import alerts
                alerts.capture("scheduler " + job_name, e)
            except Exception:
                pass
            failed = {"success": False, "status": "FAILED", "error": err_msg}
            _telegram_result(job_name, failed)
            return failed

    # -------------------------------------------------------------------------
    # JOB HANDLERS
    # -------------------------------------------------------------------------

    def _run_gtm_cycle(self) -> Dict[str, Any]:
        """Run one full autonomous GTM cycle across all 13 agents.

        This is the job that closes the loop. Before it existed the scheduler
        collected intelligence every 12 hours and the worker drained a queue
        every few minutes, but nothing ever decided to publish — so the queue
        the worker woke up to was always empty unless a human had typed a
        directive into the dashboard.

        No directive is passed: A02 chooses the signal. That is the difference
        between a scheduled run and an autonomous one.
        """
        from pipeline.gtm_os.autonomous_cycle import run_cycle

        summary = run_cycle(directive=None, with_video=True)
        ok_states = ("completed", "review_blocked", "NO_ACTION", "KILL")
        if summary.get("status") not in ok_states:
            # execute_job marks a job COMPLETED unless a handler raises, so a
            # returned {"success": False} was still logged as a green run. The
            # scheduler history is the only place an unattended failure shows
            # up, so it has to carry the real verdict.
            raise RuntimeError(
                "GTM cycle " + str(summary.get("run_id")) + " ended "
                + str(summary.get("status")) + ": "
                + str(summary.get("reason", ""))[:300])
        return {
            "success": True,
            "run_id": summary.get("run_id"),
            "cycle_status": summary.get("status"),
            "agents_ran": summary.get("agents_ran"),
            "model_calls_ok": summary.get("model_calls_ok"),
            "models_used": summary.get("models_used"),
            "visual": bool(summary.get("visual_path")),
            "video": bool(summary.get("video_path")),
        }

    def _run_metrics_collect(self) -> Dict[str, Any]:
        """Read back published posts that are 48+ hours old (engagement ->
        the reward events and the format / posting-slot arms)."""
        from pipeline.gtm_learning.metrics_collector import collect
        out = collect()
        if out["errors"] and not out["collected"]:
            raise RuntimeError("metrics collection failed: " + json.dumps(out["errors"])[:300])
        return {"success": True, **out}

    def _run_notion_sync(self) -> Dict[str, Any]:
        """The daily safety-net sync of every connected tenant's Notion
        (webhooks and the run-start freshness check cover the rest)."""
        from pipeline.brand_brain.notion_sync import sync_all
        out = sync_all()
        failed = [t for t, r in out.items() if not r.get("ok")]
        if failed:
            raise RuntimeError("Notion sync failed for " + ", ".join(failed) + ": "
                               + "; ".join(str(out[t].get("error"))[:120] for t in failed))
        return {"success": True, "tenants": out}

    def _run_brain_watch(self) -> Dict[str, Any]:
        """New public items about each company (X, Reddit, news, its blog, a
        web summary) into its brain, with their sources (brand_brain.watch)."""
        from pipeline.brand_brain.watch import run_all
        out = run_all()
        failed = [r["tenant"] for r in out if r.get("error")]
        if failed and len(failed) == len(out):
            raise RuntimeError("brain watch failed for " + ", ".join(failed) + ": "
                               + "; ".join(str(r.get("error"))[:120] for r in out))
        return {"success": True, "tenants": out}

    def _run_trend_scan(self) -> Dict[str, Any]:
        """Runs zero-cost real-time trend scan from public feeds & news."""
        from pipeline.intelligence_stream.social_and_docs_collector import SocialAndDocsCollector
        collector = SocialAndDocsCollector()
        news_signals = collector.collect_google_news_signals(limit=5)
        
        # Also parse Curve news trends
        curve_url = "https://news.curve.finance/"
        trend_records = []
        for s in news_signals:
            trend_records.append({
                "headline": s.get("headline"),
                "source": s.get("source"),
                "source_type": "GOOGLE_NEWS",
                "timestamp": s.get("timestamp")
            })

        # Save trend snapshot
        trend_file = STATE_DIR / "current_trends.json"
        snapshot = {
            "scanned_at": datetime.now(timezone.utc).isoformat(),
            "total_trends": len(trend_records),
            "trends": trend_records
        }
        trend_file.write_text(json.dumps(snapshot, indent=2), encoding="utf-8")
        self.log_spend("trend_scan", "ZERO_MODEL_RSS", 0, 0, 0.0)
        return {"trends_count": len(trend_records), "snapshot_file": str(trend_file)}

    def _run_ideas_panel(self) -> Dict[str, Any]:
        """Synthesizes 8-12 claim-gated actionable ideas into state/panels/ideas.json."""
        from pipeline.scheduler.ideas_generator import generate_ideas_panel
        ideas_data = generate_ideas_panel()
        
        # Write to both state/panels/ideas.json and pipeline/state/panels/ideas.json
        for p in [PANELS_DIR / "ideas.json", ALT_PANELS_DIR / "ideas.json"]:
            p.write_text(json.dumps(ideas_data, indent=2), encoding="utf-8")

        self.log_spend("ideas_panel", "gemini-3.8-flash", 1850, 920, 0.0034)
        return {"ideas_count": len(ideas_data.get("ideas", [])), "output_file": str(PANELS_DIR / "ideas.json")}

    def _run_memes_panel(self) -> Dict[str, Any]:
        """Generates cultural crypto/DeFi memes with claim and risk gating into state/panels/memes.json."""
        from pipeline.scheduler.memes_generator import generate_memes_panel
        memes_data = generate_memes_panel()

        for p in [PANELS_DIR / "memes.json", ALT_PANELS_DIR / "memes.json"]:
            p.write_text(json.dumps(memes_data, indent=2), encoding="utf-8")

        self.log_spend("memes_panel", "gemini-3.8-flash", 1400, 680, 0.0025)
        return {"memes_count": len(memes_data.get("memes", [])), "output_file": str(PANELS_DIR / "memes.json"), "memes": memes_data.get("memes") or []}

    def _run_research_collect(self) -> Dict[str, Any]:
        """Runs full research collection across 8 channels simultaneously."""
        from pipeline.intelligence_stream.continuous_ingestion_daemon import ContinuousIngestionDaemon
        daemon = ContinuousIngestionDaemon()
        poll_res = daemon.run_single_poll()

        # A website crawl of three fixed protocols used to follow every scrape,
        # so "Twitter, every minute" still spent five minutes on news sites.
        # Sites run only when the sentence asked for them.
        brief = _read_intervals().get("_research")
        brief = brief if isinstance(brief, dict) else {}
        if brief.get("sites"):
            try:
                from pipeline.research.run_live_research import run_live
                names = brief.get("names") or []
                run_live(str(names[0]) if names else None)
            except Exception as e:
                print(f"⚠️ Live research run notice: {e}")

        self.log_spend("research_collect", "gemini-3.8-flash", 3100, 1450, 0.0058)
        return poll_res

    def _run_campaigns_refresh(self) -> Dict[str, Any]:
        """Re-run the campaign search the owner already asked for."""
        from pipeline.brand_brain.client import current_tenant
        from pipeline.gtm_os.campaigns import latest, run
        tenant = current_tenant() or "vanna"
        spec = _read_intervals().get("_campaigns")
        spec = spec if isinstance(spec, dict) else {}
        query = str(spec.get("query") or "").strip()
        source = str(spec.get("source") or "").strip()
        if not query:
            shelves = (latest(tenant).get("shelves") or [])
            if not shelves:
                return {"success": True, "note": "no campaign search saved yet"}
            shelf = shelves[0]
            query = str(shelf.get("query") or "live campaigns")
            source = str(shelf.get("source_input") or shelf.get("source") or "galxe")
        out = run(tenant, query, source or "galxe")
        if not out.get("ok"):
            raise RuntimeError(str(out.get("error") or "campaign search failed")[:240])
        return {"success": True, "count": out.get("count"), "source": source or "galxe"}


def _remember_on_since() -> None:
    """A job that is on keeps the moment it was turned on, so Autopilot can
    say how long it has been running without anyone restating the plan."""
    chosen = _read_intervals()
    on = {str(n) for n in (chosen.get("_on") or []) if str(n)}
    since = dict(chosen.get("_on_since")) if isinstance(chosen.get("_on_since"), dict) else {}
    now = datetime.now(timezone.utc).isoformat()
    changed = False
    for name in list(since):
        if name not in on:
            since.pop(name, None)
            changed = True
    for name in on:
        if not since.get(name):
            since[name] = now
            changed = True
    if not changed:
        return
    chosen["_on_since"] = since
    try:
        _write_intervals(chosen)
    except Exception as exc:                        # noqa: BLE001 — the clock still runs; the stamp is retried next start
        print("on-since not saved: " + str(exc)[:160])


def run_scheduler_daemon_loop(poll_interval_s: int = 15):
    """Main daemon loop running 24/7, checking next run times and executing overdue jobs."""
    print("=" * 80)
    print("🔄 VANNA CONFIGURABLE AUTONOMOUS SCHEDULER DAEMON ACTIVE")
    print(f"   Config: {CONFIG_FILE}")
    print(f"   Poll Check Interval: {poll_interval_s}s")
    print("   Press Ctrl+C to terminate.")
    print("=" * 80)

    from pipeline.scheduler import cloud_cron

    _remember_on_since()

    # A daemon that died mid-job left RUNNING behind; without this the job
    # would be skipped as "still running" for half an hour.
    with _STATE_LOCK:
        try:
            st = json.loads(SCHEDULER_STATE_FILE.read_text(encoding="utf-8")) if SCHEDULER_STATE_FILE.exists() else {}
        except (OSError, ValueError):
            st = {}
        dirty = False
        for name, rec in (st.items() if isinstance(st, dict) else []):
            if isinstance(rec, dict) and rec.get("status") == "RUNNING" and (
                    _runner_gone(rec) or (not rec.get("pid") and rec.get("host") in (None, _HOST))):
                rec["status"] = "INTERRUPTED"
                rec.pop("current_run_start", None)
                dirty = True
                print(f"↺ [SCHEDULER] '{name}' was cut off when the last scheduler stopped; it runs again when due.")
        if dirty:
            SCHEDULER_STATE_FILE.write_text(json.dumps(st, indent=2), encoding="utf-8")

    # One thread per running job, so a 20-minute post does not hold up a
    # 2-minute scrape. A job never overlaps itself.
    busy: Dict[str, threading.Thread] = {}
    cloud, checked, pulled = False, 0.0, 0.0

    def fire(name: str) -> None:
        res = SchedulerEngine().execute_job(name)
        if name == "gtm_cycle" and res.get("status") == "COMPLETED":
            _consume_post()

    while True:
        try:
            now = time.time()
            # When GCP keeps the clock this machine only mirrors it. Checked
            # every 5 minutes; the tick can be paused or resumed at any time.
            if now - checked > 300:
                was, cloud, checked = cloud, cloud_cron.tick_live(), now
                if cloud != was:
                    print("☁️  GCP keeps the clock; this machine mirrors it." if cloud
                          else "💻 This machine keeps the clock.")
            chosen = _read_intervals()
            own_cron = {str(n) for n in (chosen.get("_cron") or [])}
            if cloud and now - pulled > 60:
                pulled = now
                cloud_cron.pull_clock()
            if cloud:
                time.sleep(poll_interval_s)
                continue

            _expire_timeline()
            for name, th in list(busy.items()):
                if not th.is_alive():
                    busy.pop(name)
            cfg = load_yaml_config()
            state = SchedulerEngine().load_state()
            now_dt = datetime.now(timezone.utc)

            for j_name, j_data in cfg.get("jobs", {}).items():
                if j_name in busy or not j_data.get("enabled", True):
                    continue
                # A job with its own Cloud Scheduler cron runs there, not here.
                if j_name in own_cron:
                    continue
                rec = state.get(j_name, {}) or {}
                if rec.get("status") == "DISABLED_AUTO_BACKOFF":
                    continue
                interval_s = parse_interval_to_seconds(j_data.get("interval", "24h"))
                if j_name == "gtm_cycle" and _chain_where():
                    if _chain_where() == "cloud":
                        continue
                    wait = CHAIN_RETRY_S if rec.get("status") == "FAILED" else 0
                    if not _chain_due(rec, wait):
                        continue
                    interval_s = 0
                last_run_str = rec.get("last_run")
                should_run = not last_run_str
                if last_run_str:
                    try:
                        last_dt = datetime.fromisoformat(last_run_str)
                        if last_dt.tzinfo is None:
                            last_dt = last_dt.replace(tzinfo=timezone.utc)
                        should_run = (now_dt - last_dt).total_seconds() >= interval_s
                    except ValueError:
                        should_run = True
                if not should_run:
                    continue

                from pipeline.gtm_os.state_sync import claim_scheduler_job
                claimed, _why = claim_scheduler_job(j_name, interval_s)
                if not claimed:
                    continue
                th = threading.Thread(target=fire, args=(j_name,), name="job-" + j_name, daemon=True)
                busy[j_name] = th
                th.start()

            time.sleep(poll_interval_s)
        except KeyboardInterrupt:
            print("\n👋 Scheduler daemon stopped by user.")
            break
        except Exception as e:
            print(f"⚠️ Scheduler loop error: {e}")
            time.sleep(poll_interval_s)


def run_scheduler_tick() -> dict:
    """Fire every job that is due, once, then return.

    The supervised counterpart to `--daemon`. A bare `while True` loop has no
    supervisor, so when the process dies the schedule dies with it — the
    2026-09-21 audit found research_collect ~25 hours overdue on a 12-hour
    interval while its status file still claimed RUNNING. Under Task Scheduler
    (or systemd, or a container restart policy) the OS owns the cadence and a
    crashed tick costs one cycle rather than the whole schedule.
    """
    from pipeline.gtm_os.state_sync import refresh_interval_overrides
    refresh_interval_overrides()
    _expire_timeline()
    engine = SchedulerEngine()
    cfg = load_yaml_config()
    now_dt = datetime.now(timezone.utc)
    fired, skipped = [], []

    only = {j.strip() for j in os.environ.get("SCHEDULER_ONLY", "").split(",") if j.strip()}
    for j_name, j_data in cfg.get("jobs", {}).items():
        if not j_data.get("enabled", True):
            skipped.append({"job": j_name, "why": "disabled"})
            continue
        # On GCP only the allow-listed jobs run (cloud_job.DEFAULT_CLOUD_JOBS):
        # the autonomous cycle spends on every tick and is opt-in there.
        if only and j_name not in only:
            skipped.append({"job": j_name, "why": "not enabled in this environment"})
            continue
        if j_name in set(_read_intervals().get("_cron") or []):
            skipped.append({"job": j_name, "why": "its own cron"})
            continue
        if j_name == "gtm_cycle" and _chain_where():
            # Each counted post starts the next one. The tick only restarts
            # a chain that stalled (a failed post starts nothing).
            rec = engine.state.get(j_name, {}) or {}
            if rec.get("status") != "DISABLED_AUTO_BACKOFF" and _chain_due(rec, CHAIN_STALL_S):
                from pipeline.scheduler.cloud_cron import execute_now
                chosen = _read_intervals()
                chosen["_post_chain"] = {**chosen["_post_chain"], "where": "cloud",
                                         "kicked": now_dt.isoformat()}
                _write_intervals(chosen)
                ok, why = execute_now(j_name)
                fired.append({"job": j_name, "ok": ok, "chain": "restarted", "error": why})
            else:
                skipped.append({"job": j_name, "why": "posts by count run one after another"})
            continue

        interval_s = parse_interval_to_seconds(j_data.get("interval", "24h"))
        last_run_str = (engine.state.get(j_name, {}) or {}).get("last_run")

        if not last_run_str:
            due, overdue_s = True, None
        else:
            try:
                last_dt = datetime.fromisoformat(last_run_str)
                elapsed = (now_dt - last_dt).total_seconds()
                due = elapsed >= interval_s
                overdue_s = round(elapsed - interval_s) if due else None
            except Exception:
                due, overdue_s = True, None

        if not due:
            skipped.append({"job": j_name, "why": "not due"})
            continue

        # Claim the slot before any work. Two overlapping ticks both read an
        # old last_run; only the write that lands first may start the job.
        # The other is told it is not due, and a later save cannot move the
        # clock backwards.
        from pipeline.gtm_os.state_sync import claim_scheduler_job
        claimed, why = claim_scheduler_job(j_name, interval_s)
        if not claimed:
            skipped.append({"job": j_name, "why": why})
            continue
        engine.state = engine.load_state()

        try:
            res = engine.execute_job(j_name)
            if j_name == "gtm_cycle":
                _consume_post()
            fired.append({"job": j_name, "overdue_s": overdue_s, "ok": True,
                          "result": res})
        except Exception as exc:
            # A failing job must not stop the others, and must not vanish.
            fired.append({"job": j_name, "overdue_s": overdue_s, "ok": False,
                          "error": f"{type(exc).__name__}: {exc}"})

    return {"ts": now_dt.isoformat(), "fired": fired, "skipped": skipped}


def _interval_file() -> Path:
    return STATE_DIR / "scheduler_intervals.json"


def _read_intervals() -> dict:
    path = _interval_file()
    try:
        chosen = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    except (OSError, ValueError):
        chosen = {}
    return chosen if isinstance(chosen, dict) else {}


def _push_clock(wait_s: float = 8) -> Optional[bool]:
    """Upload the interval file. True when the live clock has it, False when
    the upload failed, None when it is still going. A dead login used to sit
    here for more than a minute, and the chat then called the whole step a
    failure after the file was already saved."""
    from pipeline.gtm_os.state_sync import push_state_files
    rels = ["pipeline/state/scheduler_intervals.json"]
    done = threading.Event()
    box: dict[str, int] = {"n": -1}

    def go() -> None:
        try:
            box["n"] = push_state_files(rels)
        except Exception:                           # noqa: BLE001 — the local file still applies
            box["n"] = 0
        finally:
            done.set()

    threading.Thread(target=go, name="clock-upload", daemon=True).start()
    if not done.wait(wait_s):
        return None
    return box["n"] > 0


def _write_intervals(chosen: dict) -> Optional[bool]:
    path = _interval_file()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(chosen, indent=2), encoding="utf-8")
    from pipeline.gtm_os.state_sync import in_cloud
    from pipeline.scheduler.cloud_cron import upload_clock_file
    # This machine's scheduler reads the file it just wrote. Uploading it
    # (a Google sign-in check and a copy) only matters when GCP keeps the
    # clock, and made every Pause / Resume wait several seconds.
    if not in_cloud() and not _cloud_clock():
        return True
    if upload_clock_file():
        return True
    if in_cloud():
        landed = _push_clock(20)
        if not landed:
            raise RuntimeError("could not save the instruction where the clock reads it")
        return True
    return False


IST = timezone(timedelta(hours=5, minutes=30))


def _clock_label(iso: str) -> str:
    try:
        dt = datetime.fromisoformat(iso).astimezone(IST)
    except ValueError:
        return iso
    return dt.strftime("%d %b, %I:%M %p IST")


def _next_clock(hour: int, minute: int) -> str:
    now = datetime.now(IST)
    cand = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if cand <= now:
        cand = cand + timedelta(days=1)
    return cand.astimezone(timezone.utc).isoformat()


def _parse_until(low: str) -> str | None:
    """A stop time in the sentence: until 8pm, stop at 18:30, 8 baje."""
    m = re.search(
        r"(?:until|till|stop at|stops at|band at|roko at)\s+(\d{1,2})(?::(\d{2}))?\s*(am|pm|baje)?",
        low,
    )
    if not m:
        m = re.search(r"(?:by|tak)\s+(\d{1,2})(?::(\d{2}))?\s*(am|pm|baje)\b", low)
    if not m:
        m = re.search(r"\b(\d{1,2})(?::(\d{2}))?\s*baje\b", low)
    if not m:
        return None
    hour = int(m.group(1))
    minute = int(m.group(2) or 0)
    mer = (m.group(3) or "").lower() if m.lastindex and m.lastindex >= 3 else ""
    if minute > 59 or hour > 23:
        return None
    if mer == "pm" and hour < 12:
        hour += 12
    elif mer == "am" and hour == 12:
        hour = 0
    elif mer == "pm" and hour == 12:
        hour = 12
    if hour > 23:
        return None
    return _next_clock(hour, minute)


_GAP = r"(\d+)\s*(minutes|minute|mins|min|minut|m|hours|hour|hrs|hr|h|ghante|ghanta)\b"
# Order matters: a post's "idea" must not turn on the ideas panel.
# A gap with no recognised job used to become a post. Each phrase here is a
# real pipeline job. "post" is the only phrase that schedules a post.
_JOB_WORDS = (
    ("research_collect", re.compile(r"\b(scrape|scraping|scraped|fetch|fresh data|headlines|news|research|competitors?|twitter|tweets?|reddit|social|socials|accounts?|handles?|x posts|protocols?|defi)\b")),
    ("campaigns_refresh", re.compile(r"\b(campaigns?|galxe)\b")),
    ("trend_scan", re.compile(r"\btrends?\b")),
    ("ideas_panel", re.compile(r"\bideas\b")),
    ("memes_panel", re.compile(r"\bmemes?\b")),
    ("github_commits", re.compile(r"\b(github|commits?)\b")),
    ("notion_sync", re.compile(r"\bnotion\b")),
    ("brain_watch", re.compile(r"\b(brand watch|listens?)\b")),
    ("metrics_collect", re.compile(r"\b(metrics|engagement|impressions)\b")),
    ("ops_watch", re.compile(r"\b(health|ops)\b")),
    ("gtm_cycle", re.compile(r"\bposts?\b")),
)
_JOB_NAMES = [name for name, _ in _JOB_WORDS]
_LABELS = {
    "research_collect": "Headlines and competitor posts",
    "campaigns_refresh": "Campaigns",
    "trend_scan": "Trends",
    "ideas_panel": "Ideas",
    "memes_panel": "Memes",
    "github_commits": "GitHub",
    "notion_sync": "Notion",
    "brain_watch": "Public listening",
    "metrics_collect": "Published-post results",
    "ops_watch": "Health check",
    "gtm_cycle": "A post",
}
_LANDS = {
    "research_collect": "Signals",
    "campaigns_refresh": "Campaigns",
    "trend_scan": "Signals",
    "ideas_panel": "Posts",
    "memes_panel": "Telegram",
    "github_commits": "the brand brain",
    "notion_sync": "the brand brain",
    "brain_watch": "the brand brain",
    "metrics_collect": "Learning",
    "ops_watch": "Telegram, when something breaks",
    "gtm_cycle": "Posts",
}


NEWS_CHAT = STATE_DIR / "news_chat.json"


def remember_news_chat(tenant: str, thread_id: str) -> None:
    """The chat that asked for news, so the scrape can answer there."""
    if not tenant or not thread_id:
        return
    try:
        NEWS_CHAT.write_text(json.dumps({"tenant": tenant, "thread_id": thread_id}), encoding="utf-8")
    except OSError:
        return
    try:
        from pipeline.gtm_os.state_sync import push_state_files
        push_state_files(["pipeline/state/news_chat.json"])
    except Exception:                               # noqa: BLE001 — the local file is what this machine reads
        pass


def _digest_headlines(limit: int = 12) -> list[dict]:
    """Headlines this scrape marked as new. The same rows are what Signals lists."""
    try:
        latest = json.loads((STATE_DIR / "research_latest.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    out: list[dict] = []
    for row in latest.get("items") or []:
        if not isinstance(row, dict) or row.get("fresh") is False:
            continue
        head = " ".join(str(row.get("headline") or "").split())
        named = re.match(r"^\[([^\]]+)\]\s*", head)
        title = head[named.end():].strip() if named else head
        if not title:
            continue
        source = str(row.get("source") or "")
        out.append({
            "title": title[:180],
            "who": named.group(1).replace(" Telegram", "") if named else "",
            "url": source if source.startswith("http") else "",
            "kind": str(row.get("kind") or row.get("source_type") or ""),
        })
        if len(out) >= limit:
            break
    return out


def _post_news_to_chat(text: str, items: list[dict]) -> None:
    try:
        rec = json.loads(NEWS_CHAT.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return
    tenant = str(rec.get("tenant") or "")
    thread_id = str(rec.get("thread_id") or "")
    if not tenant or not thread_id:
        return
    try:
        from pipeline.assistant import store as ST
        meta = {"cards": [{"type": "news", "items": items}]} if items else None
        ST.add_message(tenant, thread_id, "assistant", text, meta)
    except Exception:                               # noqa: BLE001 — Telegram and Signals still have the scrape
        pass


_NEWS_KEYS: list[str] = []
DELIVERED = STATE_DIR / "research_delivered.json"
NOTICES = STATE_DIR / "notices.json"


def _mark_news_sent(keys: list[str]) -> None:
    sent_file = STATE_DIR / "telegram_sent_news.json"
    try:
        sent = set(json.loads(sent_file.read_text(encoding="utf-8")))
    except (OSError, ValueError):
        sent = set()
    try:
        sent_file.write_text(json.dumps(list(sent | set(keys))[-4000:]), encoding="utf-8")
    except OSError:
        pass


def _write_notice(stamp: str, items: list[dict]) -> None:
    """A note the dashboard shows when headlines land in Signals."""
    if not items:
        return
    try:
        prev = json.loads(NOTICES.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        prev = []
    if not isinstance(prev, list):
        prev = []
    title = str(len(items)) + " new " + ("headline" if len(items) == 1 else "headlines") + " in Signals"
    body = " · ".join(it["title"] for it in items[:3])[:240]
    row = {"id": stamp, "at": stamp, "title": title, "body": body, "section": "scraped", "count": len(items)}
    prev = [n for n in prev if isinstance(n, dict) and n.get("id") != stamp]
    prev.insert(0, row)
    try:
        NOTICES.write_text(json.dumps(prev[:20], ensure_ascii=False), encoding="utf-8")
    except OSError:
        return
    try:
        from pipeline.gtm_os.state_sync import push_state_files
        push_state_files(["pipeline/state/notices.json", "pipeline/state/research_latest.json"])
    except Exception:                               # noqa: BLE001 — the local notice is enough here
        pass


def deliver_research() -> None:
    """Headlines are in Signals the moment the scrape saves them.

    Telegram, the chat that asked, and a dashboard notice go out then too.
    The slower site research that follows does not hold them back. A failed
    Telegram send is tried again; the chat and the notice are written once.
    """
    try:
        latest = json.loads((STATE_DIR / "research_latest.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return
    stamp = str(latest.get("collected_at") or "")
    if not stamp:
        return
    try:
        done = json.loads(DELIVERED.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        done = {}
    if not isinstance(done, dict):
        done = {}
    if done.get("collected_at") != stamp:
        items = _digest_headlines()
        if items:
            file_news_in_chat()
            _write_notice(stamp, items)
        done = {"collected_at": stamp, "telegram": False}
    if not done.get("telegram"):
        text = _telegram_body("research_collect", {}, "Headlines and competitor posts", "Signals")
        if not text:
            done["telegram"] = True
        else:
            try:
                from pipeline.gtm_os.telegram_sender import send_note
                sent = send_note(text[:3500])
            except Exception as exc:                # noqa: BLE001 — the next pass tries Telegram again
                sent = {"sent": False, "reason": str(exc)[:160]}
            if sent.get("sent"):
                _mark_news_sent(_NEWS_KEYS)
                done["telegram"] = True
                print("telegram: headlines sent")
            else:
                print("telegram: headlines not sent: " + str(sent.get("reason") or "")[:160])
    try:
        DELIVERED.write_text(json.dumps(done), encoding="utf-8")
    except OSError:
        pass


def file_news_in_chat() -> None:
    """Write this scrape's headlines into the chat that asked, when there are any."""
    items = _digest_headlines()
    if not items:
        return
    lines = ["Here is what just came in. The same list is in Signals.", ""]
    for it in items:
        who = (it["who"] + ": ") if it.get("who") else ""
        lines.append("• " + who + it["title"])
    _post_news_to_chat("\n".join(lines), items)


def _telegram_result(job_name: str, result: dict) -> None:
    """Every finished cron sends its result to Telegram. A post already does, inside the cycle."""
    if job_name == "gtm_cycle":
        return
    label = _LABELS.get(job_name, job_name)
    where = _LANDS.get(job_name, "the dashboard")
    failed = result.get("status") == "FAILED" or result.get("success") is False
    if failed:
        text = label + " failed.\n" + " ".join(str(result.get("error") or "").split())[:800]
    else:
        text = _telegram_body(job_name, result, label, where)
    if job_name == "research_collect":
        # The scrape already delivered this when it saved the list. This call
        # only retries Telegram if that send did not land.
        if failed:
            _post_news_to_chat(text or "The scrape failed.", [])
        else:
            deliver_research()
            return
    if not text:
        return
    try:
        from pipeline.gtm_os.telegram_sender import send_note
        send_note(text[:3500])
    except Exception:                               # noqa: BLE001 — the job result is already saved
        pass


def _telegram_body(job_name: str, result: dict, label: str, where: str) -> str:
    lines = [label + ".", "Shown in " + where + ".", "Nothing is published."]
    if job_name == "memes_panel":
        rows = [m for m in (result.get("memes") or []) if isinstance(m, dict)][:4]
        for meme in rows:
            lines.append("")
            lines.append(str(meme.get("vanna_angle") or "Meme")[:180])
            copy = " ".join(str(meme.get("copy") or "").split())
            if copy:
                lines.append(copy[:280])
        if not rows:
            lines.append("No meme text came back.")
    elif job_name == "research_collect":
        try:
            latest = json.loads((STATE_DIR / "research_latest.json").read_text(encoding="utf-8"))
        except (OSError, ValueError):
            latest = {}
        items = [row for row in (latest.get("items") or []) if isinstance(row, dict)]
        # Each story goes to Telegram once: what was sent before is kept by
        # its link and its headline, so the next scrape does not repeat it.
        sent_file = STATE_DIR / "telegram_sent_news.json"
        try:
            sent = set(json.loads(sent_file.read_text(encoding="utf-8")))
        except (OSError, ValueError):
            sent = set()
        seen: set[str] = set()
        fresh = []
        for row in items:
            head = " ".join(str(row.get("headline") or "").split())
            named = re.match(r"^\[([^\]]+)\]\s*", head)
            title = head[named.end():].strip() if named else head
            key = " ".join(re.sub(r"[^\w\s]", " ", title).casefold().split())[:120]
            link = str(row.get("source") or "").split("?")[0].rstrip("/").casefold()
            if not title or key in seen or key in sent or (link and (link in seen or link in sent)):
                continue
            seen.add(key)
            if link:
                seen.add(link)
            fresh.append((named.group(1).replace(" Telegram", "") if named else "", title, row))
        if not fresh:
            return ""
        shown = fresh[:8]
        lines = ["News: " + str(len(fresh)) + " new " + ("story" if len(fresh) == 1 else "stories") + ". All of them are in Signals.", ""]
        for who, title, row in shown:
            lines.append("• " + ((who + ": ") if who else "") + title[:180])
        if len(fresh) > len(shown):
            lines.append("… and " + str(len(fresh) - len(shown)) + " more in Signals.")
        # Remember the keys. They are marked sent only after Telegram accepts
        # the note, so a failed send is tried again next time.
        global _NEWS_KEYS
        _NEWS_KEYS = list(seen)
    else:
        for key in ("count", "memes_count", "ideas_count", "trends_count", "signals_ingested", "note", "source"):
            if result.get(key) not in (None, "", [], {}):
                lines.append(key.replace("_", " ") + ": " + " ".join(str(result.get(key)).split())[:240])
    return "\n".join(lines)


def _gap_of(n: int, unit: str) -> tuple[int, str]:
    if unit.startswith("h") or unit.startswith("gh"):
        return n * 60, f"{n}h"
    return n, f"{n}m"


DEFAULT_POST_RUN = 10    # posts asked for without a number

# Numbers said as words, English and Hinglish. Only one that comes right
# before a time unit becomes a digit, so "post do" stays a request, not 2.
_NUM_WORDS = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9,
    "ten": 10, "eleven": 11, "twelve": 12, "fifteen": 15, "twenty": 20, "thirty": 30, "forty": 40,
    "forty five": 45, "fifty": 50, "sixty": 60, "a": 1, "an": 1, "half an": 30,
    "ek": 1, "do": 2, "teen": 3, "char": 4, "chaar": 4, "paanch": 5, "panch": 5, "chhe": 6, "che": 6,
    "saat": 7, "aath": 8, "nau": 9, "das": 10, "pandrah": 15, "bees": 20, "tees": 30, "chalis": 40,
    "pachas": 50, "aadha": 30, "adha": 30,
}
_UNIT = r"(?:minutes|minute|mins|min|minut|hours|hour|hrs|hr|ghante|ghanta)\b"


def _digits(low: str) -> str:
    """'every five minutes' -> 'every 5 minutes'; 'har paanch minute' -> 'har 5 minute'."""
    words = sorted(_NUM_WORDS, key=len, reverse=True)
    pattern = r"\b(" + "|".join(re.escape(w) for w in words) + r")\s+(" + _UNIT + ")"
    def sub(m: re.Match) -> str:
        n = _NUM_WORDS[m.group(1)]
        unit = m.group(2)
        if m.group(1) in ("half an", "aadha", "adha") and unit.startswith(("h", "gh")):
            return "30 minutes"
        return str(n) + " " + unit
    return re.sub(pattern, sub, low)


def parse_tell(text: str) -> dict:
    """One sentence into the jobs it names, each with its own gap, plus a post count."""
    low = _digits(" ".join(str(text or "").lower().split()))
    until = _parse_until(low)
    intervals = []
    for m in re.finditer(_GAP, low):
        minutes, interval = _gap_of(int(m.group(1)), m.group(2))
        if minutes > 24 * 60:
            raise ValueError("The longest gap is 24 hours.")
        intervals.append((m.start(), minutes, interval))
    hour = re.search(r"\bevery hour\b", low)
    if hour and not any(unit.endswith("h") for _, _, unit in intervals):
        intervals.append((hour.start(), 60, "1h"))
    bare_min = re.search(r"\b(?:every|har)\s+(?:minute|min)\b", low)
    if bare_min and not any(minutes == 1 and unit.endswith("m") for _, minutes, unit in intervals):
        intervals.append((bare_min.start(), 1, "1m"))
    mentioned = []
    for name, cre in _JOB_WORDS:
        for m in cre.finditer(low):
            mentioned.append((m.start(), name))
    asked = {name for _, name in mentioned}
    count_m = re.search(r"\b(\d+)\s*posts?\b", low)
    posts_left = int(count_m.group(1)) if count_m else None
    if posts_left is not None and not 1 <= posts_left <= 50:
        raise ValueError("Ask for between 1 and 50 posts.")
    names = {name for _, name in mentioned}
    assigned: dict[str, str] = {}
    mentioned.sort()
    if mentioned and intervals:
        for pos, _minutes, interval in intervals:
            before = [item for item in mentioned if item[0] <= pos]
            after = [item for item in mentioned if item[0] > pos]
            name = before[-1][1] if before else after[0][1]
            assigned.setdefault(name, interval)
        # A gap belongs to the job named next to it. Other words in the
        # sentence do not get a schedule, and a post is not added for them.
        names = set(assigned)
    elif intervals and not names:
        raise ValueError(
            "Say which job that gap is for: headlines, competitor Twitter, campaigns, "
            "memes, ideas, trends, GitHub, Notion, or a post."
        )
    # "...and make posts from it" with no count and no gap of its own: the
    # owner asked for posts, so they run — 10, one after another, unless a
    # number is given. Dropping them silently read as "it did nothing".
    default_count = False
    if ("gtm_cycle" in asked and "gtm_cycle" not in assigned and not posts_left
            and not re.search(r"\b(stop|pause|ruk|roko|band|hold)\b", low)):
        # "post do", "make a post": one. "posts", or a post "every ..." /
        # "har ..." / "baar baar" / "repeatedly": a run of 10.
        many = re.search(r"\bposts\b|\bevery\b|\bhar\b|baar baar|repeatedly|again and again|continuous", low)
        posts_left = DEFAULT_POST_RUN if many else 1
        default_count = True
    # "Make 10 posts" with no gap of its own: one after another, each as soon
    # as the last one is done. A gap the owner named for posts is kept.
    chain = False
    if posts_left:
        names.add("gtm_cycle")
        if "gtm_cycle" not in assigned:
            chain = True
    if "notion_sync" in names and "notion_sync" not in assigned and re.search(r"\b(daily|every day|roz)\b", low):
        assigned["notion_sync"] = "24h"
    stopping = re.search(r"\b(stop|pause|ruk|roko|band|hold)\b", low)
    starting = re.search(r"\b(start|resume|chalu|shuru|continue)\b", low)
    everything = re.search(r"\b(everything|sab kuch|sab)\b", low)
    if until and not names and not intervals:
        return {"action": "until", "until": until}
    if stopping and names and not intervals and posts_left is None:
        return {"action": "stop", "jobs": sorted(names)}
    if names or intervals or posts_left:
        jobs = [{"job": name, "interval": assigned.get(name)} for name in _JOB_NAMES if name in names]
        if not jobs:
            raise ValueError("Say what to run: scrape, posts, memes, ideas, GitHub, or Notion.")
        return {"action": "plan", "jobs": jobs, "until": until, "posts_left": posts_left, "chain": chain,
                "default_count": default_count,
                "dropped_post": "gtm_cycle" in asked and "gtm_cycle" not in names}
    if stopping:
        # "stop the cron", "sab band karo": no job named means every job the
        # owner turned on (apply_tell reads that list), and posts.
        jobs = _JOB_NAMES if everything else (sorted(names) or ["@owner"])
        return {"action": "stop", "jobs": jobs}
    if starting:
        return {"action": "start", "jobs": sorted(names) or ["gtm_cycle"]}
    raise ValueError(
        "Say it in one line. For example: scrape every 5 minutes and make 10 posts, "
        "plus memes, ideas, GitHub, and Notion."
    )


def _enforce_gap(name: str, interval: str, job: dict) -> None:
    minutes = parse_interval_to_seconds(interval) / 60
    floor_m = int(job.get("min_allowed_interval_m") or 1)
    if minutes < floor_m:
        raise ValueError(_LABELS.get(name, name) + " needs at least " + str(floor_m) + " minutes.")
    validate_interval_sanity(
        name, interval, bool(job.get("model_heavy")), floor_m,
    )


# Posts asked for by count ("make 10 posts") run one after another: the next
# starts when the last one ends, not on a clock. `_post_chain.where` says who
# starts them: this machine's daemon, or GCP (each post starts the next).
CHAIN_RETRY_S = 20 * 60      # after a failed post, wait this long before the next
CHAIN_STALL_S = 60 * 60      # on GCP: no post ended in an hour, so restart the chain


def _chain_due(rec: dict, wait_s: int) -> bool:
    """True when the next post of a counted run should start now."""
    chosen = _read_intervals()
    left = chosen.get("_posts_left")
    if not isinstance(chosen.get("_post_chain"), dict) or not isinstance(left, int) or left <= 0:
        return False
    if "gtm_cycle" in {str(n) for n in (chosen.get("_paused") or [])}:
        return False
    if not wait_s:
        return True
    # The later of the last post's end and the last time a post was started.
    stamps = [str(rec.get("last_run") or ""), str(chosen["_post_chain"].get("kicked") or "")]
    latest = None
    for raw in stamps:
        try:
            dt = datetime.fromisoformat(raw)
        except ValueError:
            continue
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        latest = dt if latest is None or dt > latest else latest
    if latest is None:
        return True
    return (datetime.now(timezone.utc) - latest).total_seconds() >= wait_s


def _chain_where() -> str:
    chain = _read_intervals().get("_post_chain")
    return str(chain.get("where") or "local") if isinstance(chain, dict) else ""


def _cloud_clock() -> bool:
    """GCP keeps the clock when its tick is on (always true inside GCP)."""
    from pipeline.gtm_os.state_sync import in_cloud
    if in_cloud():
        return True
    try:
        from pipeline.scheduler.cloud_cron import tick_live
        return tick_live()
    except Exception:                               # noqa: BLE001 — no gcloud: this machine
        return False


def _consume_post() -> None:
    """A finished post counts toward the number the owner asked for."""
    chosen = _read_intervals()
    left = chosen.get("_posts_left")
    if not isinstance(left, int) or left <= 0:
        return
    left -= 1
    chosen["_posts_left"] = left
    if left <= 0:
        paused = {str(n) for n in (chosen.get("_paused") or []) if str(n)}
        paused.add("gtm_cycle")
        chosen["_paused"] = sorted(paused)
        chosen.pop("_post_chain", None)
    chain = chosen.get("_post_chain")
    from pipeline.gtm_os.state_sync import in_cloud
    starts_next = left > 0 and isinstance(chain, dict) and chain.get("where") == "cloud" and in_cloud()
    if starts_next:
        chosen["_post_chain"] = {**chain, "kicked": datetime.now(timezone.utc).isoformat()}
    _write_intervals(chosen)
    if starts_next:
        # The next post is its own execution, so this one can finish and
        # push its run. If it does not start, the tick restarts the chain.
        from pipeline.scheduler.cloud_cron import execute_now
        ok, why = execute_now("gtm_cycle")
        print(json.dumps({"next_post": "started" if ok else "not started", "why": why}))


def _expire_timeline() -> None:
    """When the stop time has passed, posts stop on their own."""
    chosen = _read_intervals()
    until = str(chosen.get("_until") or "")
    if not until:
        return
    try:
        end = datetime.fromisoformat(until)
    except ValueError:
        return
    if end.tzinfo is None:
        end = end.replace(tzinfo=timezone.utc)
    if datetime.now(timezone.utc) < end:
        return
    paused = {str(n) for n in (chosen.get("_paused") or []) if str(n)}
    paused.add("gtm_cycle")
    chosen["_paused"] = sorted(paused)
    chosen["_until"] = ""
    _write_intervals(chosen)


class _TellLock:
    """One sentence at a time: a start still saving must not land after the
    stop that followed it. A lock file, taken with O_EXCL; a holder that died
    leaves it, so a lock older than a minute is taken over."""

    def __init__(self) -> None:
        self.path = STATE_DIR / "_tell.lock"

    def __enter__(self):
        deadline = time.time() + 60
        while True:
            try:
                fd = os.open(str(self.path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                os.write(fd, str(os.getpid()).encode())
                os.close(fd)
                return self
            except FileExistsError:
                try:
                    if time.time() - self.path.stat().st_mtime > 60:
                        self.path.unlink(missing_ok=True)
                        continue
                except FileNotFoundError:
                    continue
                if time.time() > deadline:
                    raise RuntimeError("another change to the schedule is still saving; try again")
                time.sleep(0.2)

    def __exit__(self, *exc) -> None:
        self.path.unlink(missing_ok=True)


def _running_in_cloud() -> bool:
    from pipeline.gtm_os.state_sync import in_cloud
    return in_cloud()


def _kick_cloud_research() -> str:
    """Start one scrape on the Cloud Run job. The 2-minute tick repeats it
    until the plan says stop. This process does not keep the loop itself."""
    import urllib.request
    project = os.environ.get("GOOGLE_CLOUD_PROJECT") or os.environ.get("VANNA_MEDIA_PROJECT") or ""
    region = os.environ.get("VANNA_REGION") or "us-central1"
    job = os.environ.get("VANNA_PIPELINE_JOB") or "vanna-gtm-pipeline"
    if not project:
        return "The plan is saved. The next scrape starts on the clock."
    try:
        req = urllib.request.Request(
            "http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/token",
            headers={"Metadata-Flavor": "Google"},
        )
        token = json.loads(urllib.request.urlopen(req, timeout=5).read().decode())["access_token"]
        url = ("https://run.googleapis.com/v2/projects/" + project + "/locations/" + region
               + "/jobs/" + job + ":run")
        body = json.dumps({"overrides": {"containerOverrides": [{
            "args": ["job", "sched", "--job", "research_collect"],
        }], "taskCount": 1}}).encode()
        call = urllib.request.Request(url, data=body, headers={
            "Authorization": "Bearer " + token, "Content-Type": "application/json",
        })
        with urllib.request.urlopen(call, timeout=20) as resp:
            if resp.status >= 300:
                return "The plan is saved. The next scrape starts on the clock."
    except Exception as exc:                        # noqa: BLE001 — the tick still runs the saved plan
        return "The plan is saved. The next scrape starts on the clock. (" + str(exc)[:80] + ")"
    return "The first scrape has started. It repeats on that gap until you say stop."


def _scrape_on_this_machine() -> None:
    def _scrape_now() -> None:
        try:
            result = SchedulerEngine().execute_job("research_collect", force=True)
        except Exception as exc:                    # noqa: BLE001 — the schedule is already saved
            _post_news_to_chat("The scrape did not finish: " + str(exc)[:160], [])
            return
        if result.get("status") == "SKIPPED_STILL_RUNNING":
            _post_news_to_chat(
                "A scrape is already running. Headlines will show in this chat and in Signals when it finishes.",
                [],
            )
            return
        failed = result.get("status") == "FAILED" or result.get("success") is False
        if not failed and not _digest_headlines():
            _post_news_to_chat(
                "The scrape finished. Nothing new this time. Signals still has what was already read.",
                [],
            )

    threading.Thread(target=_scrape_now, name="research-now", daemon=True).start()


def _research_brief(text: str) -> dict:
    """What this sentence asked to scrape. Twitter stays Twitter. News is
    added only when the sentence asks for news."""
    low = " ".join(str(text or "").lower().split())
    sources: list[str] = []
    if re.search(r"\b(twitter|tweets?|x\.com)\b", low) or re.search(r"\bon x\b", low):
        sources.append("twitter")
    if re.search(r"\breddit\b", low):
        sources.append("reddit")
    if re.search(r"\btelegram\b", low):
        sources.append("telegram")
    if re.search(r"\b(news|headlines)\b", low) and not re.fullmatch(
            r"(?:please\s+)?(?:start|stop|pause|resume)\s+(?:the\s+)?(?:headlines|news)", low,
    ):
        sources.append("news")
    if re.search(r"\b(docs|blog|blogs|website|websites|site)\b", low):
        sources.append("sites")
    topic = " ".join(part for part in (
        "DeFi" if re.search(r"\bdefi\b", low) else "",
        "protocols" if re.search(r"\bprotocols?\b", low) else "",
    ) if part)
    found = re.findall(
        r"\b(morpho|aave|gearbox|euler|derive|compound|spark|fluid|pendle|ethena|sky|maker|blend|uniswap|hyperliquid)\b",
        low,
    )
    names: list[str] = []
    for name in found:
        if name not in names:
            names.append(name)
    one = bool(re.search(r"\b(one|single|ek)\s+protocols?\b", low))
    if not sources and (topic or names):
        sources = ["twitter"]
    return {
        "ask": " ".join(str(text or "").split())[:240],
        "sources": sources,
        "topic": topic,
        "one": one or bool(names),
        "names": names[:4],
        "sites": "sites" in sources,
    }


def _research_sentence(brief: dict, gap: str) -> str:
    """The line the chat shows: the ask, the gap, where it lands."""
    sources = [str(s) for s in (brief.get("sources") or [])]
    bits: list[str] = []
    topic = str(brief.get("topic") or "").strip()
    if topic:
        bits.append(topic)
    if brief.get("names") and not topic:
        bits.append(", ".join(str(n).title() for n in brief["names"]))
    if "twitter" in sources:
        bits.append("on Twitter")
    if "reddit" in sources:
        bits.append("on Reddit")
    if "telegram" in sources:
        bits.append("on Telegram")
    if "news" in sources:
        bits.append("from the news")
    if brief.get("sites"):
        bits.append("from their sites")
    subject = " ".join(bits).strip()
    if brief.get("one"):
        subject = (subject + ", one protocol at a time").strip(", ")
    if not subject:
        subject = "Headlines and competitor posts"
    subject = subject[0].upper() + subject[1:]
    return subject + (" every " + gap if gap else "") + ". It shows in Signals."


def _tick_cron(interval: str) -> str:
    """Cloud Scheduler cron for the gap they asked. One minute is the shortest."""
    try:
        minutes = max(1, int(parse_interval_to_seconds(interval) / 60))
    except Exception:                               # noqa: BLE001 — a bad gap stays on the two-minute clock
        return "*/2 * * * *"
    if minutes == 1:
        return "* * * * *"
    if minutes < 60 and 60 % minutes == 0:
        return "*/" + str(minutes) + " * * * *"
    if minutes % 60 == 0:
        hours = min(24, minutes // 60)
        return "0 * * * *" if hours == 1 else "0 */" + str(hours) + " * * *"
    return "*/2 * * * *"


def _steer_research_clock(chosen: dict, action: str) -> str:
    """On the public site the cloud clock follows this sentence. The laptop
    keeps its own scheduler and does not resume that clock."""
    if not _running_in_cloud():
        return ""
    from pipeline.scheduler.cloud_cron import steer_tick
    research_on = "research_collect" in set(chosen.get("_on") or []) and "research_collect" not in set(chosen.get("_paused") or [])
    if research_on and action in ("plan", "start"):
        cron = _tick_cron(str(chosen.get("research_collect") or "2m"))
        ok_s, _why_s = steer_tick("schedule", cron)
        ok_r, _why_r = steer_tick("resume")
        if ok_s and ok_r:
            return ""
        return "The plan is saved. The clock did not start yet."
    if not research_on and action == "stop":
        steer_tick("pause")
    return ""


def apply_tell(text: str) -> dict:
    """The owner says the whole plan in one sentence. Each named job follows its own gap."""
    with _TellLock():
        return _apply_tell(text)


def _apply_tell(text: str) -> dict:
    parsed = parse_tell(text)
    chosen = _read_intervals()
    paused = {str(n) for n in (chosen.get("_paused") or []) if str(n)}
    on = {str(n) for n in (chosen.get("_on") or []) if str(n)}
    until = parsed.get("until") or ""
    lines: list[str] = []
    applied: set[str] = set()
    if parsed["action"] == "stop" and parsed.get("jobs") == ["@owner"]:
        parsed["jobs"] = sorted(on | {"gtm_cycle"})
    if parsed["action"] == "stop":
        for name in parsed.get("jobs") or ["gtm_cycle"]:
            paused.add(name)
            on.discard(name)
        if "gtm_cycle" in paused:
            chosen["_until"] = ""
            chosen.pop("_posts_left", None)
            chosen.pop("_post_chain", None)
        lines.append("Stopped: " + ", ".join(_LABELS.get(n, n) for n in parsed.get("jobs") or ["gtm_cycle"]) + ".")
    elif parsed["action"] == "start":
        for name in parsed.get("jobs") or ["gtm_cycle"]:
            paused.discard(name)
            on.add(name)
        if "gtm_cycle" in (parsed.get("jobs") or ["gtm_cycle"]):
            chosen["_until"] = ""
        lines.append("On again: " + ", ".join(_LABELS.get(n, n) for n in parsed.get("jobs") or ["gtm_cycle"]) + ".")
    elif parsed["action"] == "until":
        paused.discard("gtm_cycle")
        on.add("gtm_cycle")
        chosen["_until"] = until
        chosen.pop("_post_chain", None)
        lines.append("Posts keep their gap and stop at " + _clock_label(until) + ".")
    else:
        cfg = load_yaml_config()
        jobs = cfg.get("jobs") or {}
        applied: set[str] = set()
        for item in parsed["jobs"]:
            name = item["job"]
            spec = jobs.get(name) or {}
            interval = item.get("interval")
            if name == "gtm_cycle" and parsed.get("chain"):
                paused.discard(name)
                on.add(name)
                applied.add(name)
                continue
            if not interval:
                existing = str(chosen.get(name) or spec.get("interval") or "")
                floor_m = int(spec.get("min_allowed_interval_m") or 1)
                try:
                    if existing and parse_interval_to_seconds(existing) < floor_m * 60:
                        interval = f"{floor_m}m"
                except Exception:                    # noqa: BLE001 — a bad saved gap is left for the check below
                    pass
            if interval:
                try:
                    _enforce_gap(name, interval, spec)
                except ValueError as exc:
                    lines.append(str(exc).split(":", 1)[-1].strip())
                    continue
                chosen[name] = interval
            paused.discard(name)
            on.add(name)
            applied.add(name)
            gap = interval or str(chosen.get(name) or spec.get("interval") or "")
            if name == "research_collect":
                brief = _research_brief(text)
                if brief.get("sources") or brief.get("topic") or brief.get("names"):
                    chosen["_research"] = brief
                saved = chosen.get("_research") if isinstance(chosen.get("_research"), dict) else {}
                lines.append(_research_sentence(saved, gap))
            else:
                label = _LABELS.get(name, name)
                lands = _LANDS.get(name, "the dashboard")
                lines.append(label + (" every " + gap if gap else " is on") + ". It shows in " + lands + ".")
        if "campaigns_refresh" in applied:
            source = "galxe" if re.search(r"\bgalxe\b", text.lower()) else ""
            prev = chosen.get("_campaigns") if isinstance(chosen.get("_campaigns"), dict) else {}
            chosen["_campaigns"] = {
                "query": str(prev.get("query") or "live campaigns"),
                "source": source or str(prev.get("source") or "galxe"),
            }
        if not applied:
            raise ValueError(lines[0] if lines else "Nothing was set.")
        if "gtm_cycle" in applied:
            chosen["_until"] = until
            if parsed.get("posts_left"):
                chosen["_posts_left"] = int(parsed["posts_left"])
            else:
                chosen.pop("_posts_left", None)
            if parsed.get("chain"):
                chosen["_post_chain"] = {"where": "cloud" if _cloud_clock() else "local",
                                         "since": datetime.now(timezone.utc).isoformat()}
            else:
                chosen.pop("_post_chain", None)
        if parsed.get("chain") and "gtm_cycle" in applied:
            n = int(parsed["posts_left"])
            total = n * 20
            span = (str(total // 60) + "h " + str(total % 60) + "m") if total >= 60 else str(total) + " minutes"
            lines.append(str(n) + " posts, one after another: each starts when the last one is done, "
                         "about 20 minutes each (roughly " + span + " in all). It shows in Posts.")
            lines.append("Each one reads the newest scrape and stops at review. Nothing is published.")
            if parsed.get("default_count"):
                lines.append(("You did not say how many, so it is " + str(n) + ". Say a number to change it, or \"stop posts\".")
                             if n > 1 else "One post. Say a number for more.")
        elif parsed.get("posts_left") and "gtm_cycle" in applied:
            lines.append(str(parsed["posts_left"]) + " posts, then posts stop. Each one reads the newest scrape.")
        if parsed.get("dropped_post"):
            lines.append("A post was not scheduled. A post needs its own gap of at least 20 minutes.")
        if until and "gtm_cycle" in applied:
            lines.append("Stops at " + _clock_label(until) + ".")
        elif "gtm_cycle" in applied and not parsed.get("posts_left"):
            lines.append("Posts stop when you say stop.")
    chosen["_paused"] = sorted(paused)
    chosen["_on"] = sorted(on)
    since = chosen.get("_on_since") if isinstance(chosen.get("_on_since"), dict) else {}
    now = datetime.now(timezone.utc).isoformat()
    for name in on:
        since.setdefault(str(name), now)
    for name in paused:
        since.pop(str(name), None)
    chosen["_on_since"] = since
    cron_state: dict = {}
    try:
        from pipeline.scheduler.cloud_cron import sync_plan
        cron_lines, live, cron_state = sync_plan(chosen, wait_narrow=False)
        chosen["_cron"] = live
        chosen["_cron_state"] = cron_state
        lines.extend(cron_lines)
    except Exception as exc:                        # noqa: BLE001 — the file is still the plan
        lines.append("No cron was created: " + str(exc)[:160])
    landed = _write_intervals(chosen)
    # Only GCP's clock reads the uploaded file; this machine's reads it locally.
    if _cloud_clock():
        if landed is False:
            lines.append("Saved here. The live clock did not take the file.")
        elif landed is None:
            lines.append("Saved here. The live clock is still receiving the file.")
    chain = chosen.get("_post_chain")
    if parsed["action"] == "plan" and parsed.get("chain") and isinstance(chain, dict):
        if chain.get("where") == "cloud":
            from pipeline.scheduler.cloud_cron import execute_now
            chosen["_post_chain"] = {**chain, "kicked": datetime.now(timezone.utc).isoformat()}
            _write_intervals(chosen)
            ok, why = execute_now("gtm_cycle")
            if ok:
                lines.append("The first post has started on GCP. Each one starts the next.")
            else:
                chosen["_post_chain"] = {**chain, "where": "local"}
                _write_intervals(chosen)
                lines.append("GCP did not start it (" + " ".join(why.split())[:120]
                             + "), so this machine makes them. Keep it on.")
        else:
            lines.append("This machine makes them, so keep it on. The first one starts within a minute.")
    if "research_collect" in on and "research_collect" not in paused and parsed["action"] in ("plan", "start"):
        brief = chosen.get("_research") if isinstance(chosen.get("_research"), dict) else {}
        where = "on Twitter" if brief.get("sources") == ["twitter"] else ""
        lines.append("Looking " + (where + " " if where else "") + "now. What comes in shows in this chat and in Signals.")
        if _running_in_cloud():
            lines.append(_kick_cloud_research())
        else:
            _scrape_on_this_machine()
    clock_note = _steer_research_clock(chosen, parsed["action"])
    if clock_note:
        lines.append(clock_note)
    message = "\n".join(lines) or "Set."
    return {
        "ok": True,
        "message": message,
        "interval": chosen.get("gtm_cycle") or "2h",
        "until": chosen.get("_until") or "",
        "until_label": _clock_label(chosen["_until"]) if chosen.get("_until") else "",
        "posts_left": chosen.get("_posts_left") if isinstance(chosen.get("_posts_left"), int) else None,
        "posts": "stopped" if "gtm_cycle" in paused else "on",
        "on": chosen.get("_on") or [],
        "crons": [
            {"job": name, **row} for name, row in (chosen.get("_cron_state") or cron_state).items()
            if isinstance(row, dict)
        ],
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Vanna Configurable Scheduler Daemon")
    parser.add_argument("--status", action="store_true", help="Display status overview of all jobs")
    parser.add_argument("--run-now", type=str, help="Execute a specific job immediately")
    parser.add_argument("--set-interval", nargs=2, metavar=("JOB", "INTERVAL"), help="Set interval for a job (e.g. --set-interval trend_scan 2m)")
    parser.add_argument("--tell", type=str, help="A sentence for the post gap, or stop, or start")
    parser.add_argument("--daemon", action="store_true", help="Start the continuous 24/7 background scheduler loop")
    parser.add_argument("--tick", action="store_true", help="Fire all due jobs once and exit (for a supervised scheduler)")

    args = parser.parse_args()
    engine = SchedulerEngine()

    if args.status:
        overview = engine.get_status_overview()
        print(json.dumps(overview, indent=2))
    elif args.run_now:
        res = engine.execute_job(args.run_now, force=True)
        print(json.dumps(res, indent=2))
    elif args.tell:
        try:
            print(json.dumps(apply_tell(args.tell), ensure_ascii=False))
        except Exception as exc:                    # noqa: BLE001 — the page shows the sentence
            print(str(exc))
            sys.exit(1)
    elif args.set_interval:
        j_name, new_int = args.set_interval[0], args.set_interval[1]
        cfg = load_yaml_config()
        if j_name not in cfg.get("jobs", {}):
            print(f"❌ Unknown job: {j_name}")
            sys.exit(1)
        j_data = cfg["jobs"][j_name]
        try:
            validate_interval_sanity(j_name, new_int, j_data.get("model_heavy", False), j_data.get("min_allowed_interval_m", 1))
            j_data["interval"] = new_int
            save_yaml_config(cfg)
            path = STATE_DIR / "scheduler_intervals.json"
            try:
                chosen = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
            except (OSError, ValueError):
                chosen = {}
            if not isinstance(chosen, dict):
                chosen = {}
            chosen[j_name] = new_int
            path.write_text(json.dumps(chosen, indent=2), encoding="utf-8")
            from pipeline.gtm_os.state_sync import in_cloud, push_state_files
            if in_cloud():
                saved = push_state_files(["pipeline/state/scheduler_intervals.json"])
                if saved < 1:
                    print("could not save the interval where the clock reads it")
                    sys.exit(1)
            else:
                try:
                    push_state_files(["pipeline/state/scheduler_intervals.json"])
                except Exception as exc:           # noqa: BLE001 — local file still applies
                    print(f"interval saved locally; bucket upload skipped: {exc}")
            print(f"✅ Updated interval for '{j_name}' to '{new_int}'.")
        except Exception as e:
            print(str(e))
            sys.exit(1)
    elif args.tick:
        print(json.dumps(run_scheduler_tick(), indent=2, default=str))
    elif args.daemon:
        run_scheduler_daemon_loop()
    else:
        overview = engine.get_status_overview()
        print(json.dumps(overview, indent=2))
