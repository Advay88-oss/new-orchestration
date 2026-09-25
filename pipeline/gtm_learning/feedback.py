"""Founder feedback — the reward signal the learning loop never had.

A13 was named a learning engine and learned nothing: it read performance
records that were all one test fixture, kept its weights in memory, and wrote
adjustments no agent ever read. The one reward that is available today, and
the one that matters most, is the founder's decision on a run: approve,
revise (with a note), or kill.

This records that decision, from Telegram or the dashboard, in one shape:

  gtm_runs/<run>/feedback.json   the latest decision for the run, plus history
  pipeline/state/feedback.jsonl  the ledger — one row per decision, carrying
                                 the run's features so a learner can ask
                                 "which pillars, archetypes and machines get
                                 approved?" without re-reading every run

Recording never publishes anything. Approve means "this was good", not "send
it"; dispatch stays a separate human action.

    python -m pipeline.gtm_learning.feedback record GTM-... approve --note "..."
    python -m pipeline.gtm_learning.feedback show [GTM-...]
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

REPO = Path(__file__).resolve().parents[2]
STATE = REPO / "pipeline" / "state"
RUNS = STATE / "gtm_runs"
LEDGER = STATE / "feedback.jsonl"

# Reward per decision. Revise is not a failure — the founder thought it was
# worth fixing — so it sits between the two, closer to kill than approve.
REWARD = {"approve": 1.0, "revise": 0.3, "kill": 0.0}
VERDICTS = tuple(REWARD)


def features(run_id: str) -> dict[str, Any]:
    """What the run chose — the things a learner can credit or blame."""
    try:
        s = json.loads((RUNS / run_id / "summary.json").read_text(encoding="utf-8"))
    except Exception:                               # noqa: BLE001 — boundary
        return {}
    x = (s.get("posts") or {}).get("x") or {}
    cr = s.get("creative_review") or {}
    return {
        "directive": (s.get("directive") or None),
        "signal": str(s.get("signal") or "")[:200] or None,
        "pillar": s.get("pillar"),
        "machine": s.get("machine"),
        "visual_archetype": s.get("visual_archetype"),
        "visual_renderer": s.get("visual_renderer"),
        "video_mode": s.get("video_mode"),
        "x_hook": str(x.get("hook") or "")[:200] or None,
        "x_chars": len(str(x.get("copy") or "")),
        "creative_verdict": s.get("creative_verdict"),
        "copy_verdict": cr.get("copy_verdict"),
        "review_passed": s.get("review_passed"),
    }


def record(run_id: str, verdict: str, note: str = "", *,
           source: str = "cli", by: Optional[str] = None) -> dict[str, Any]:
    verdict = verdict.strip().lower()
    if verdict not in REWARD:
        raise ValueError("verdict must be one of " + ", ".join(VERDICTS))
    run_dir = RUNS / run_id
    if not run_dir.is_dir():
        raise FileNotFoundError("no run " + run_id)

    row = {
        "run_id": run_id,
        "verdict": verdict,
        "reward": REWARD[verdict],
        "note": " ".join(str(note or "").split())[:2000] or None,
        "source": source,
        "by": by,
        "at": datetime.now(timezone.utc).isoformat(),
        "features": features(run_id),
    }

    # Per run: latest decision on top, every decision kept. A founder who
    # kills and then approves after a revision has changed their mind, and
    # both facts are signal.
    fb_file = run_dir / "feedback.json"
    try:
        prior = json.loads(fb_file.read_text(encoding="utf-8"))
    except Exception:                               # noqa: BLE001 — first one
        prior = {"history": []}
    doc = {"run_id": run_id, "latest": {k: row[k] for k in
                                        ("verdict", "reward", "note", "source", "by", "at")},
           "history": (prior.get("history") or []) + [
               {k: row[k] for k in ("verdict", "reward", "note", "source", "by", "at")}]}
    tmp = fb_file.with_suffix(".tmp")
    tmp.write_text(json.dumps(doc, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp.replace(fb_file)

    from pipeline.gtm_storage.atomic_store import AtomicJsonlStore
    AtomicJsonlStore(LEDGER).append(row)

    # A decision on a run with a Veo clip is also a rating of that clip, so
    # A09 learns from the same Approve / Revise / Kill with no separate step.
    try:
        s = json.loads((run_dir / "summary.json").read_text(encoding="utf-8"))
        vid = s.get("video_path")
        if vid and Path(str(vid)).exists() and s.get("video_mode") in (
                "veo_image_to_video", "veo_build"):
            from pipeline.gtm_creative.veo_video import add_exemplar
            add_exemplar(vid, score=row["reward"],
                         note=row["note"] or (verdict + " (no note)"),
                         prompt=s.get("video_prompt") or "",
                         still=s.get("visual_path"))
    except Exception:                               # noqa: BLE001 — boundary
        pass

    # Push to GCS so the deployed dashboard shows the decision too. Best
    # effort: a missing client or expired ADC must not lose the local record.
    try:
        from pipeline.gtm_os import state_sync
        summary = json.loads((run_dir / "summary.json").read_text(encoding="utf-8"))
        state_sync.push_run(run_id, summary)
    except Exception:                               # noqa: BLE001 — boundary
        pass
    return row


def ledger() -> list[dict[str, Any]]:
    try:
        return [json.loads(l) for l in LEDGER.read_text(encoding="utf-8").splitlines()
                if l.strip()]
    except FileNotFoundError:
        return []


def for_run(run_id: str) -> Optional[dict[str, Any]]:
    try:
        return json.loads((RUNS / run_id / "feedback.json").read_text(encoding="utf-8"))
    except Exception:                               # noqa: BLE001 — none yet
        return None


def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Record or show founder feedback on a run.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("record")
    r.add_argument("run_id")
    r.add_argument("verdict", choices=VERDICTS)
    r.add_argument("--note", default="")
    r.add_argument("--source", default="cli")
    r.add_argument("--by", default=None)
    s = sub.add_parser("show")
    s.add_argument("run_id", nargs="?")
    a = ap.parse_args(argv)

    if a.cmd == "record":
        try:
            row = record(a.run_id, a.verdict, a.note, source=a.source, by=a.by)
        except (ValueError, FileNotFoundError) as exc:
            print(json.dumps({"success": False, "error": str(exc)}))
            return 2
        print(json.dumps({"success": True, "feedback": row}, ensure_ascii=False))
        return 0
    out = for_run(a.run_id) if a.run_id else ledger()
    print(json.dumps(out, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
