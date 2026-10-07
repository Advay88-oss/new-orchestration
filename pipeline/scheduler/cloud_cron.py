"""Turn a plan the Assistant accepted into Cloud Scheduler cron jobs.

One sentence can name several gaps (a scrape every 5 minutes, posts every
20). One cron expression cannot say both, so each job gets its own cron,
named vanna-cron-<job>, firing only that job. The 2-minute tick leaves those
jobs alone so they are not run twice.
"""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

PROJECT = "sales-agent-504607"
REGION = "us-central1"
JOB = "vanna-gtm-pipeline"
SA = "114262736718-compute@developer.gserviceaccount.com"
URI = ("https://run.googleapis.com/v2/projects/" + PROJECT
       + "/locations/" + REGION + "/jobs/" + JOB + ":run")


def interval_to_cron(interval: str) -> str | None:
    """A Cloud Scheduler cron for 5m, 20m, 2h. None when cron cannot say it."""
    from pipeline.scheduler.configurable_scheduler_daemon import parse_interval_to_seconds
    try:
        seconds = parse_interval_to_seconds(interval)
    except Exception:                               # noqa: BLE001 — not a gap we can schedule
        return None
    if seconds < 60 or seconds % 60:
        return None
    minutes = seconds // 60
    if minutes < 60 and 60 % minutes == 0:
        return "*/" + str(minutes) + " * * * *"
    if minutes % 60 == 0:
        hours = minutes // 60
        if hours == 24:
            return "0 0 * * *"
        if 0 < hours < 24 and 24 % hours == 0:
            return "0 */" + str(hours) + " * * *"
    return None


def _gcloud() -> str | None:
    return shutil.which("gcloud") or shutil.which("gcloud.cmd")


def _run(args: list[str], timeout: float = 20, limit: int = 300) -> tuple[int, str]:
    exe = _gcloud()
    if not exe:
        return 1, "gcloud is not installed"
    try:
        proc = subprocess.run(
            [exe, *args, "--project", PROJECT],
            capture_output=True, text=True, timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return 1, "gcloud timed out"
    except OSError as exc:
        return 1, str(exc)[:160]
    text = ((proc.stderr or "") + "\n" + (proc.stdout or "")).strip()
    return proc.returncode, text[:limit]


def authed() -> bool:
    """True when the user login can call Google. The token is never returned."""
    exe = _gcloud()
    if not exe:
        return False
    try:
        proc = subprocess.run(
            [exe, "auth", "print-access-token"],
            capture_output=True, text=True, timeout=30,
        )
    except (subprocess.TimeoutExpired, OSError):
        return False
    return proc.returncode == 0


def _job_id(name: str) -> str:
    return "vanna-cron-" + name.replace("_", "-")


def _body(name: str) -> dict:
    return {"overrides": {"containerOverrides": [
        {"args": ["job", "sched", "--job", name]}]}}


def _list_schedules() -> dict[str, str] | None:
    """Job id -> schedule for crons that already exist. None when the list failed."""
    code, raw = _run(
        ["scheduler", "jobs", "list", "--location", REGION, "--format", "json(name,schedule)"],
        timeout=15, limit=20000,
    )
    if code != 0:
        return None
    try:
        rows = json.loads(raw[raw.find("["):] if "[" in raw else raw)
    except ValueError:
        return None
    out = {}
    for row in rows if isinstance(rows, list) else []:
        name = str(row.get("name") or "").rstrip("/").split("/")[-1]
        if name:
            out[name] = str(row.get("schedule") or "")
    return out


def _upsert(name: str, cron: str, existing: dict[str, str] | None) -> tuple[bool, str]:
    job_id = _job_id(name)
    body = json.dumps(_body(name))
    common = [
        "--location", REGION,
        "--schedule", cron,
        "--uri", URI,
        "--http-method", "POST",
        "--message-body", body,
        "--oauth-service-account-email", SA,
    ]
    if existing is not None and job_id in existing and existing[job_id] == cron:
        _run(["scheduler", "jobs", "resume", job_id, "--location", REGION], timeout=12)
        return True, ""
    if existing is not None and job_id in existing:
        code, detail = _run(["scheduler", "jobs", "update", "http", job_id,
                             "--update-headers", "Content-Type=application/json", *common], timeout=20)
        if code == 0:
            _run(["scheduler", "jobs", "resume", job_id, "--location", REGION], timeout=12)
        return code == 0, detail
    code, detail = _run([
        "scheduler", "jobs", "create", "http", job_id,
        "--headers", "Content-Type=application/json", *common,
        "--time-zone", "Etc/UTC",
    ], timeout=20)
    if code != 0 and "already exists" in detail.lower():
        code, detail = _run(["scheduler", "jobs", "update", "http", job_id,
                             "--update-headers", "Content-Type=application/json", *common], timeout=20)
    return code == 0, detail


SCHED_API = ("https://cloudscheduler.googleapis.com/v1/projects/" + PROJECT
             + "/locations/" + REGION + "/jobs")


def _rest():
    """An authorised HTTP session from application-default credentials, or None."""
    try:
        import google.auth
        from google.auth.transport.requests import AuthorizedSession
        creds, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
        return AuthorizedSession(creds)
    except Exception:                               # noqa: BLE001 — the gcloud CLI is the fallback
        return None


def live_crons() -> set[str] | None:
    """Ids of this project's Cloud Scheduler jobs that are ENABLED; None if unknown."""
    sess = _rest()
    if sess is not None:
        try:
            r = sess.get(SCHED_API, timeout=20)
            if r.status_code < 300:
                return {j["name"].rsplit("/", 1)[-1] for j in r.json().get("jobs", []) if j.get("state") == "ENABLED"}
        except Exception:                           # noqa: BLE001 — try the CLI
            pass
    code, raw = _run(["scheduler", "jobs", "list", "--location", REGION, "--format", "json(name,state)"],
                     timeout=20, limit=20000)
    if code != 0:
        return None
    try:
        rows = json.loads(raw[raw.find("["):])
    except ValueError:
        return None
    return {str(r.get("name", "")).rstrip("/").rsplit("/", 1)[-1] for r in rows if r.get("state") == "ENABLED"}


def _pause(name: str) -> bool:
    """Pause one job's cron in GCP. True when GCP confirms it is paused."""
    job_id = name if name.startswith("vanna-") else _job_id(name)
    sess = _rest()
    if sess is not None:
        try:
            r = sess.post(SCHED_API + "/" + job_id + ":pause", json={}, timeout=20)
            if r.status_code < 300 or r.status_code == 404:
                return True
        except Exception:                           # noqa: BLE001 — try the CLI
            pass
    code, _ = _run(["scheduler", "jobs", "pause", job_id, "--location", REGION], timeout=15)
    return code == 0


def _containers(payload: dict) -> list:
    """Find the container list that actually carries env, whichever shape describe returns."""
    found: list = []

    def walk(node: object) -> None:
        if isinstance(node, dict):
            containers = node.get("containers")
            if isinstance(containers, list) and containers and isinstance(containers[0], dict) and "env" in containers[0]:
                found.append(containers)
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)

    walk(payload)
    return found[0] if found else []


def _narrow_tick(live: list[str]) -> None:
    """The 2-minute tick must not also fire a job that now has its own cron."""
    if not live:
        return
    code, raw = _run(
        ["run", "jobs", "describe", JOB, "--region", REGION, "--format", "json"],
        timeout=25, limit=500000,
    )
    if code != 0:
        return
    start = raw.find("{")
    try:
        payload = json.loads(raw[start:] if start >= 0 else raw)
        containers = _containers(payload)
        env = containers[0].get("env") or [] if containers else []
    except (ValueError, AttributeError, IndexError):
        return
    current = ""
    for item in env:
        if isinstance(item, dict) and item.get("name") == "SCHEDULER_ONLY":
            current = str(item.get("value") or "")
    if not current:
        return
    keep = [n for n in current.split(",") if n.strip() and n.strip() not in set(live)]
    previous = [n.strip() for n in current.split(",") if n.strip()]
    if keep == previous:
        return
    flag = Path(__file__).resolve().parents[1] / "state" / "_tick_flags.json"
    flag.write_text(json.dumps({
        "--update-env-vars": "^:^SCHEDULER_ONLY=" + ",".join(keep),
    }), encoding="utf-8")
    try:
        _run(["run", "jobs", "update", JOB, "--region", REGION,
              "--flags-file", str(flag)], timeout=50, limit=500)
    finally:
        flag.unlink(missing_ok=True)


BUCKET = "vanna-gtm-state-504607"
CLOCK_OBJECT = "gs://" + BUCKET + "/state/pipeline/state/scheduler_intervals.json"


def upload_clock_file() -> bool:
    """Copy the interval file with the user login. Application-default is stale."""
    src = Path(__file__).resolve().parents[1] / "state" / "scheduler_intervals.json"
    if not src.exists() or not authed():
        return False
    code, _ = _run(["storage", "cp", str(src), CLOCK_OBJECT], timeout=25, limit=400)
    return code == 0


TICK = "vanna-gtm-tick"
STATE_OBJECT = "gs://" + BUCKET + "/state/pipeline/state/scheduler_state.json"


_TICK_SEEN: dict = {}


def tick_live(max_age_s: float = 120) -> bool:
    """True when GCP keeps the clock: the 2-minute tick exists and is enabled.

    Then the laptop's scheduler only mirrors the bucket, so a job never runs
    in both places (and never sends its Telegram note twice). The answer is
    kept for two minutes; asking gcloud takes seconds."""
    import time as _t
    # Kept in memory and on disk: a tell is a fresh process each time.
    cache = Path(__file__).resolve().parents[1] / "state" / "_tick_live.json"
    if not _TICK_SEEN:
        try:
            _TICK_SEEN.update(json.loads(cache.read_text(encoding="utf-8")))
        except (OSError, ValueError):
            pass
    if _TICK_SEEN and _t.time() - float(_TICK_SEEN.get("at", 0)) < max_age_s:
        return bool(_TICK_SEEN.get("live"))
    crons = live_crons()
    live = bool(crons and TICK in crons)
    _TICK_SEEN.update(at=_t.time(), live=live)
    try:
        cache.write_text(json.dumps(_TICK_SEEN), encoding="utf-8")
    except OSError:
        pass
    return live


def pull_clock() -> bool:
    """Copy the bucket's clock (gaps, post count, job state) to this machine,
    so the local dashboard shows what the cloud ran. Uses the user login."""
    from pipeline.gtm_os.state_sync import blend_scheduler_records
    state_dir = Path(__file__).resolve().parents[1] / "state"
    code, raw = _run(["storage", "cat", CLOCK_OBJECT], timeout=25, limit=200000)
    if code != 0:
        return False
    try:
        chosen = json.loads(raw[raw.find("{"):])
    except ValueError:
        return False
    if isinstance(chosen, dict):
        (state_dir / "scheduler_intervals.json").write_text(json.dumps(chosen, indent=2), encoding="utf-8")
    code, raw = _run(["storage", "cat", STATE_OBJECT], timeout=25, limit=500000)
    if code != 0:
        return True
    try:
        remote = json.loads(raw[raw.find("{"):])
    except ValueError:
        return True
    path = state_dir / "scheduler_state.json"
    try:
        local = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    except (OSError, ValueError):
        local = {}
    if isinstance(remote, dict) and isinstance(local, dict):
        merged = blend_scheduler_records(local, remote)
        # The cloud's status for a job it ran is the true one.
        for name, rec in remote.items():
            if isinstance(rec, dict) and isinstance(merged.get(name), dict) \
                    and str(rec.get("last_run") or "") >= str(local.get(name, {}).get("last_run") or ""):
                merged[name] = {**merged[name], **{k: rec[k] for k in ("status", "last_duration_s",
                                "consecutive_failures", "last_error", "current_run_start") if k in rec}}
        path.write_text(json.dumps(merged, indent=2), encoding="utf-8")
    return True


def execute_now(name: str) -> tuple[bool, str]:
    """Start one job on the pipeline now, as its own Cloud Run execution.

    From the laptop this is the user login (gcloud); inside GCP it is the
    job's service account, the same one Cloud Scheduler uses."""
    from pipeline.gtm_os.state_sync import in_cloud
    if in_cloud():
        try:
            import google.auth
            from google.auth.transport.requests import AuthorizedSession
            creds, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
            resp = AuthorizedSession(creds).post(URI, json=_body(name), timeout=30)
            return resp.status_code < 300, ("" if resp.status_code < 300 else resp.text[:200])
        except Exception as exc:                    # noqa: BLE001 — the caller says it did not start
            return False, str(exc)[:200]
    code, detail = _run(["run", "jobs", "execute", JOB, "--region", REGION, "--async",
                         "--args", "job,sched,--job," + name], timeout=60)
    return code == 0, ("" if code == 0 else detail)


def _row(name: str, interval: str, labels: dict, lands: dict) -> dict:
    return {
        "id": _job_id(name), "cron": interval_to_cron(interval) or "",
        "interval": interval, "label": labels.get(name, name),
        "lands": lands.get(name, "the dashboard"),
    }


def sync_plan(chosen: dict, wait_narrow: bool = True) -> tuple[list[str], list[str], dict]:
    """Create or pause one cron per job in the plan.

    Returns (lines for the owner, job names whose cron is live, per-job status).
    One login check, then one list, then the creates in parallel. The tick
    allow-list update can run after the caller already has the result.
    """
    import threading
    from concurrent.futures import ThreadPoolExecutor
    from pipeline.scheduler.configurable_scheduler_daemon import _LABELS, _LANDS
    paused = {str(n) for n in (chosen.get("_paused") or [])}
    on = [str(n) for n in (chosen.get("_on") or []) if not str(n).startswith("_")]
    live: list[str] = []
    lines: list[str] = []
    state: dict = {}

    def remember(status: str) -> tuple[list[str], list[str], dict]:
        for name in on:
            if name in paused or (name == "gtm_cycle" and isinstance(chosen.get("_post_chain"), dict)):
                continue
            interval = chosen.get(name)
            if not isinstance(interval, str):
                continue
            row = _row(name, interval.strip(), _LABELS, _LANDS)
            row["state"] = status
            state[name] = row
        if status == "local":
            running = [n for n in on if n not in paused]
            return (["It runs on this machine and keeps its gap until you stop it."] if running else []), [], state
        return ["No cron was created: Google sign-in is missing (gcloud auth login). The plan is saved."], [], state

    for name in sorted(paused):
        interval = chosen.get(name)
        if not isinstance(interval, str) or not interval.strip():
            continue
        row = _row(name, interval.strip(), _LABELS, _LANDS)
        row["state"] = "stopped"
        state[name] = row
    if not _gcloud():
        return remember("local")
    from pipeline.gtm_os.state_sync import in_cloud
    if not in_cloud() and not tick_live():
        # GCP's clock is off, so this machine's scheduler runs the plan. A
        # cron still live in GCP would run the job a second time there — or,
        # for a job the owner stopped here, keep running it there (that sent
        # the research note every 2 minutes after "stop"). Pause every live
        # cron, whatever this machine remembers about it.
        live = live_crons()
        for job_id in sorted(live or []):
            if job_id.startswith("vanna-cron-"):
                _pause(job_id)
        lines, crons, state = remember("local")
        if live is None:
            lines.append("Could not reach GCP to check its crons; sign in again with gcloud auth login.")
        elif any(j.startswith("vanna-cron-") for j in live):
            lines.append("Paused the GCP crons so nothing runs twice.")
        return lines, crons, state
    if not authed():
        lines.append("No cron was changed: Google sign-in is missing (gcloud auth login). The plan is saved.")
        return lines, [], state

    existing = _list_schedules()
    pending = []
    for name in sorted(paused):
        _pause(name)
    for name in on:
        if name in paused:
            _pause(name)
            continue
        if name == "gtm_cycle" and isinstance(chosen.get("_post_chain"), dict):
            # Posts by count start each other; a cron would start extra ones.
            _pause(name)
            continue
        interval = chosen.get(name)
        if not isinstance(interval, str) or not interval.strip():
            continue
        row = _row(name, interval.strip(), _LABELS, _LANDS)
        if not row["cron"]:
            row["state"] = "clock"
            state[name] = row
            lines.append(row["label"] + " every " + interval + " stays on the 2-minute clock. Cron cannot say that gap.")
            continue
        pending.append((name, row))

    def one(item: tuple[str, dict]) -> tuple[str, dict, bool, str]:
        name, row = item
        ok, detail = _upsert(name, row["cron"], existing)
        return name, row, ok, detail

    if pending:
        with ThreadPoolExecutor(max_workers=min(4, len(pending))) as pool:
            for name, row, ok, detail in pool.map(one, pending):
                if ok:
                    row["state"] = "live"
                    live.append(name)
                    lines.append("Cron " + row["id"] + " is " + row["cron"] + " (" + row["label"] + " every " + row["interval"] + "). It shows in " + row["lands"] + ".")
                elif "Reauthentication" in detail or "auth login" in detail:
                    row["state"] = "auth"
                    lines.append("Cron for " + row["label"] + " needs a Google sign-in on this machine (gcloud auth login). The plan is saved and shows in " + row["lands"] + ".")
                else:
                    row["state"] = "failed"
                    useful = next((ln for ln in detail.splitlines() if ln.strip().startswith("ERROR")), "")
                    lines.append("Cron for " + row["label"] + " was not created. " + (useful or "gcloud failed")[:180])
                state[name] = row
    owned = set(live)
    for name in list(chosen.get("_cron") or []):
        if name not in owned and name not in on:
            _pause(str(name))
    if live:
        if wait_narrow:
            _narrow_tick(live)
        else:
            threading.Thread(target=_narrow_tick, args=(list(live),), daemon=True).start()
    return lines, live, state
