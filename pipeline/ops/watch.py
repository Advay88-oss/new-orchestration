"""The hourly health watch (scheduler job ops_watch; Cloud Scheduler on GCP).

Each check is independent and alerts on its own (once per window):

  database   the brain's database answers (Cloud SQL / local Postgres)
  webhook    Telegram's webhook points at the dashboard and is not failing
             (GCP only; locally the listener polls instead)
  dashboard  the dashboard's /api/health answers (DASHBOARD_URL, GCP)
  jobs       Cloud Run job executions that failed in the last two hours (GCP)
  budget     today's spend against the caps
  errors     errors recorded since the last watch, as one digest

The Cloud Monitoring uptime check (deploy_cloud.sh monitoring) watches the
dashboard from outside too, so an outage that also stops these jobs is
still reported, by email.

    python -m pipeline.ops.watch
"""
from __future__ import annotations

import json
import os
import urllib.request
from datetime import datetime, timedelta, timezone
from typing import Any

from pipeline.ops import alerts
from pipeline.ops import budget as B


def _in_cloud() -> bool:
    return bool(os.environ.get("K_SERVICE") or os.environ.get("CLOUD_RUN_JOB"))


def _get(url: str, headers: dict | None = None, timeout: float = 15.0) -> tuple[int, Any]:
    req = urllib.request.Request(url, headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            body = r.read().decode("utf-8", "replace")
            try:
                return r.status, json.loads(body)
            except ValueError:
                return r.status, body
    except urllib.error.HTTPError as e:            # type: ignore[attr-defined]
        return e.code, None
    except Exception as e:                          # noqa: BLE001
        return 0, str(e)[:200]


def check_database() -> dict:
    try:
        from pipeline.brand_brain import store as S
        tenants = S.tenants()
        return {"ok": True, "tenants": len(tenants)}
    except Exception as exc:                        # noqa: BLE001
        alerts.send("db-down", "The brain's database is not answering: " + str(exc)[:300], severity="critical")
        return {"ok": False, "error": str(exc)[:200]}


def check_webhook() -> dict:
    if not _in_cloud():
        return {"ok": True, "skipped": "local (polling listener)"}
    try:
        from pipeline.gtm_os.telegram_sender import _token
        token = _token()
    except Exception:                               # noqa: BLE001
        return {"ok": True, "skipped": "Telegram not configured"}
    code, info = _get("https://api.telegram.org/bot" + token + "/getWebhookInfo")
    res = (info or {}).get("result") if isinstance(info, dict) else None
    if code != 200 or not res:
        alerts.send("webhook-unreachable", "Could not read the Telegram webhook status (HTTP " + str(code) + ").")
        return {"ok": False, "code": code}
    want = os.environ.get("DASHBOARD_URL", "").rstrip("/") + "/api/telegram/webhook"
    problems = []
    if os.environ.get("DASHBOARD_URL") and res.get("url") != want:
        problems.append("it points at " + (res.get("url") or "nothing") + ", not the dashboard")
    last_err = res.get("last_error_date")
    if last_err and datetime.now(timezone.utc) - datetime.fromtimestamp(last_err, timezone.utc) < timedelta(hours=2):
        problems.append("Telegram reports: " + str(res.get("last_error_message"))[:200])
    if int(res.get("pending_update_count") or 0) > 20:
        problems.append(str(res["pending_update_count"]) + " button presses are waiting")
    if problems:
        alerts.send("webhook-broken", "The Telegram review buttons may not be reaching the dashboard: "
                    + "; ".join(problems), severity="critical")
    return {"ok": not problems, "problems": problems}


def check_dashboard() -> dict:
    base = os.environ.get("DASHBOARD_URL", "").rstrip("/")
    if not base:
        return {"ok": True, "skipped": "DASHBOARD_URL not set"}
    code, body = _get(base + "/api/health", timeout=25)
    if code != 200:
        alerts.send("dashboard-down", "The dashboard did not answer its health check (HTTP " + str(code) + ").",
                    severity="critical")
        return {"ok": False, "code": code}
    return {"ok": True}


def check_jobs() -> dict:
    """Cloud Run job executions that failed recently (crashes our own code never saw)."""
    if not _in_cloud():
        return {"ok": True, "skipped": "local"}
    try:
        tok = json.loads(urllib.request.urlopen(urllib.request.Request(
            "http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/token",
            headers={"Metadata-Flavor": "Google"}), timeout=5).read())["access_token"]
        project = urllib.request.urlopen(urllib.request.Request(
            "http://metadata.google.internal/computeMetadata/v1/project/project-id",
            headers={"Metadata-Flavor": "Google"}), timeout=5).read().decode()
    except Exception as exc:                        # noqa: BLE001
        return {"ok": True, "skipped": "no metadata server: " + str(exc)[:80]}
    region = os.environ.get("VANNA_REGION", "us-central1")
    failed = []
    for job in ("vanna-gtm-pipeline", "vanna-gtm-admin"):
        code, body = _get(f"https://run.googleapis.com/v2/projects/{project}/locations/{region}/jobs/{job}/executions"
                          "?pageSize=20", headers={"Authorization": "Bearer " + tok})
        for ex in (body or {}).get("executions", []) if isinstance(body, dict) else []:
            done = ex.get("completionTime") or ex.get("updateTime") or ""
            try:
                recent = datetime.now(timezone.utc) - datetime.fromisoformat(done.replace("Z", "+00:00")) < timedelta(hours=2)
            except ValueError:
                recent = False
            if recent and int(ex.get("failedCount") or 0) > 0:
                name = ex.get("name", "").rsplit("/", 1)[-1]
                failed.append(name)
                alerts.send("job-failed-" + name, "Cloud Run job execution failed: " + name
                            + " (logs: Cloud Run → Jobs → " + job + ")", severity="critical")
    return {"ok": not failed, "failed": failed}


def check_budget() -> dict:
    st = B.status()
    B._threshold_alerts()
    return {"ok": st["spent_usd"] < float(st["daily_usd"] or 0), "spent_usd": st["spent_usd"], "daily_usd": st["daily_usd"]}


def check_errors() -> dict:
    """A digest of errors seen since the last watch."""
    since = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
    rows = [e for e in alerts.recent(50)["errors"] if str(e.get("last_seen") or "") >= since]
    if rows:
        lines = ["- " + str(e["where_"]) + " ×" + str(e["count"]) + ": " + str(e["message"])[:140] for e in rows[:8]]
        alerts.send("errors-digest-" + datetime.now(timezone.utc).strftime("%Y-%m-%dT%H"),
                    str(len(rows)) + " kind(s) of error in the last hour:\n" + "\n".join(lines))
    return {"ok": not rows, "recent": len(rows)}


def run() -> dict[str, Any]:
    out: dict[str, Any] = {"at": datetime.now(timezone.utc).isoformat()}
    for name, fn in (("database", check_database), ("webhook", check_webhook), ("dashboard", check_dashboard),
                     ("jobs", check_jobs), ("budget", check_budget), ("errors", check_errors)):
        try:
            out[name] = fn()
        except Exception as exc:                    # noqa: BLE001 — one check fails alone
            out[name] = {"ok": False, "error": str(exc)[:200]}
    out["ok"] = all(v.get("ok", True) for k, v in out.items() if isinstance(v, dict))
    return out


if __name__ == "__main__":
    print(json.dumps(run(), indent=1, default=str))
