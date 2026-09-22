#!/usr/bin/env python3
"""Hybrid trigger-runner — bridge between the Cloud Run dashboard and the local
scraping pipeline, with LIVE execution streaming to the dashboard.

Scraping (OpenCLI Chrome) is local-only, so runs execute here. The dashboard (on
Cloud Run) drops a run-request in gs://<bucket>/requests/. This runner:
    1. claims a request (moves it to requests/done/)
    2. runs autonomous_orchestrator.py --no-send, streaming its stdout LIVE into
       gs://<bucket>/traces/<run_id>.json every ~2s so the dashboard shows the
       whole process as it happens (scraping -> debate -> gate -> visual)
    3. delivers the winning draft + card to Telegram for review
    4. pushes the final trace + meta + card so the dashboard shows the result

Does NOT auto-publish to Twitter. Pipeline ends at human review.

    python runner.py --once
    python runner.py --interval 30
"""
from __future__ import annotations
import argparse, json, os, re, subprocess, sys, threading, time
from pathlib import Path
from google.cloud import storage

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
STATE = REPO / "pipeline" / "state"
PY = sys.executable
GEMINI_MODEL = os.environ.get("VANNA_GEMINI_MODEL", "gemini-3.5-flash")
BUCKET = os.environ.get("VANNA_GCS_BUCKET", "gs://vanna-pipeline-state-506009").replace("gs://", "")
PROJECT = os.environ.get("VERTEX_PROJECT", "video-506009")

_bucket = None
def bucket():
    global _bucket
    if _bucket is None:
        _bucket = storage.Client(project=PROJECT).bucket(BUCKET)
    return _bucket


def _sync(*args: str) -> dict:
    r = subprocess.run([PY, str(HERE / "gcs_sync.py"), *args], capture_output=True, text=True)
    try:
        return json.loads(r.stdout.strip().splitlines()[-1]) if r.stdout.strip() else {}
    except Exception:
        return {}


def highlights(log: str) -> dict:
    def find(pat, default=""):
        m = re.search(pat, log)
        return m.group(1).strip() if m else default
    tweets = re.findall(r"Scraped (\d+) tweets", log)
    posts = re.findall(r"Scraped (\d+) (?:posts|reddit)", log)
    return {
        "topic": find(r"Selected LRU Topic: '([^']+)'"),
        "angle": find(r"Angle: ([^)]+)\)"),
        "competitor": find(r"Research on Competitor '([^']+)'") or find(r"Scraper on Competitor '([^']+)'"),
        "scraped_tweets": int(tweets[0]) if tweets else 0,
        "scraped_reddit": int(posts[0]) if posts else 0,
        "verdict": find(r"Verdict:\s*(\w+)"),
        "gate_pass": '"pass": true' in log,
    }


def read_scraped() -> dict:
    """The raw scraped signals the scout persisted this run (tweets + reddit),
    so the dashboard can render them as expandable cards."""
    p = STATE / "temp_scraped.json"
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def upload_trace(run_id: str, status: str, focus: str, started: float, log: str, final_post: str = "", has_card: bool = False) -> None:
    trace = {
        "run_id": run_id, "status": status, "focus": focus,
        "started": started, "updated": time.time(),
        "brain": f"gemini ({GEMINI_MODEL}) · GCP",
        "log": log[-60000:],  # cap
        "highlights": highlights(log),
        "scraped": read_scraped(),
        "final_post": final_post, "has_card": has_card,
    }
    try:
        bucket().blob(f"traces/{run_id}.json").upload_from_string(
            json.dumps(trace, ensure_ascii=False), content_type="application/json")
    except Exception as e:
        print(f"[runner] trace upload failed: {e}", file=sys.stderr)


def process(req: dict) -> None:
    req_id = req.get("id") or "req"
    focus = req.get("focus", "") or req.get("prompt", "")
    visual = req.get("visual", "static")
    # one id across request -> run -> trace (dashboard opens /run/<id> immediately)
    run_id = req.get("run_id") or req.get("id") or ("vanna-" + time.strftime("%Y%m%d-%H%M%S", time.gmtime()))
    started = time.time()
    print(f"[runner] claiming {req_id} -> run {run_id} (focus={focus!r})")
    _sync("claim", "--req-id", req_id)
    try:  # clear previous run's scraped signals so the trace shows only this run's
        (STATE / "temp_scraped.json").unlink(missing_ok=True)
    except Exception:
        pass
    upload_trace(run_id, "running", focus, started, f"Queued: {focus or 'auto-pick trend'}\nStarting pipeline on {GEMINI_MODEL}...\n")
    # publish a 'running' meta immediately so /api/runs lists this run right away
    # (the dashboard then picks it as the active run and streams it live).
    try:
        bucket().blob(f"runs/{run_id}.meta.json").upload_from_string(json.dumps({
            "run_id": run_id, "pipeline": "Vanna content pipeline", "tenant": "Vanna",
            "started": started, "status": "running", "brain": f"gemini ({GEMINI_MODEL}) · GCP",
            "kind": "content-run", "winner_hook": "", "winner_body": "", "trend": focus,
        }, ensure_ascii=False), content_type="application/json")
    except Exception as e:
        print(f"[runner] running-meta push failed: {e}", file=sys.stderr)

    env = {**os.environ, "VANNA_GEMINI_MODEL": GEMINI_MODEL, "VANNA_RUN_ID": run_id,
           "VANNA_GCS_BUCKET": f"gs://{BUCKET}", "PYTHONIOENCODING": "utf-8", "PYTHONUNBUFFERED": "1"}
    cmd = [PY, "-u", str(HERE / "autonomous_orchestrator.py"), "--no-send", "--visual", visual]
    if focus:
        cmd += ["--focus", focus]

    # stream stdout live -> GCS trace every ~2s
    log_lines: list[str] = []
    last_push = [time.time()]
    proc = subprocess.Popen(cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
    for line in proc.stdout:  # type: ignore
        log_lines.append(line.rstrip("\n"))
        print(line, end="")
        if time.time() - last_push[0] > 2.0:
            upload_trace(run_id, "running", focus, started, "\n".join(log_lines))
            last_push[0] = time.time()
    proc.wait()
    log = "\n".join(log_lines)

    # final artefacts
    final_post = ""
    draft = STATE / "drafts" / "temp_winner.json"
    if draft.exists():
        try:
            d = json.loads(draft.read_text(encoding="utf-8"))
            final_post = d.get("final_body") or d.get("body") or ""
        except Exception:
            pass
    card = STATE / "temp_rendered.png"
    status = "completed" if proc.returncode == 0 else "failed"

    # push meta + draft + card, then Telegram, then final trace
    _sync("push", "--run-id", run_id)
    if draft.exists():
        tg = [PY, str(HERE / "telegram_review.py"), "send", "--draft", str(draft)]
        if card.exists():
            tg += ["--image", str(card)]
        subprocess.run(tg, env=env)
        print("[runner] delivered to Telegram")
    upload_trace(run_id, status, focus, started, log, final_post=final_post, has_card=card.exists())
    print(f"[runner] {run_id} {status} -> dashboard")


def poll_once() -> int:
    reqs = _sync("requests").get("requests", [])
    if not reqs:
        print("[runner] no pending requests")
        return 0
    for req in reqs:
        try:
            process(req)
        except Exception as e:
            print(f"[runner] error processing {req.get('id')}: {e}")
    return len(reqs)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--once", action="store_true")
    ap.add_argument("--interval", type=int, default=30)
    a = ap.parse_args()
    if a.once:
        poll_once()
        return 0
    print(f"[runner] polling gs://{BUCKET}/requests every {a.interval}s (model={GEMINI_MODEL}). Ctrl-C to stop.")
    while True:
        try:
            poll_once()
        except Exception as e:
            print(f"[runner] loop error: {e}")
        time.sleep(a.interval)


if __name__ == "__main__":
    sys.exit(main())
