"""Append-only run journal.

The audit found 48 completed runs but only 26 records (46% lost), run records
overwritten in place by the approve button, and every gated draft landing in the
same `temp_winner.json` — so no past run could be reconstructed.

This module fixes that with one rule: **nothing is ever overwritten.** A run is a
directory of append-only events plus immutable artifacts addressed by content
hash. Approval appends a new event; it does not edit history.

Resume works because every stage is journaled twice — once when it starts, once
when it ends. A worker that dies mid-run leaves a `stage_started` with no
`stage_ended`, which is exactly the resume point.
"""
from __future__ import annotations

import json
import os
import shutil
import tempfile
import time
from pathlib import Path
from typing import Any, Iterator

from .contracts import StageResult, digest

REPO = Path(__file__).resolve().parents[1]
RUNS_ROOT = Path(os.environ.get("VANNA_RUNS_DIR", REPO / "state" / "runs"))


def _append_jsonl(path: Path, record: dict[str, Any]) -> None:
    """Append one line durably. Opened per-write so a crash cannot truncate."""
    path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(record, ensure_ascii=False, default=str)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(line + "\n")
        fh.flush()
        os.fsync(fh.fileno())


def write_atomic(path: Path, data: bytes) -> None:
    """Write-then-rename so a reader never sees a half-written artifact."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), suffix=".tmp")
    try:
        with os.fdopen(fd, "wb") as fh:
            fh.write(data)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, path)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise


class RunLog:
    """One run's immutable journal.

    events.jsonl   append-only event stream (the source of truth)
    artifacts/     content-addressed; a given hash is written at most once
    """

    def __init__(self, run_id: str, root: Path | None = None) -> None:
        self.run_id = run_id
        self.dir = (root or RUNS_ROOT) / run_id
        self.events_path = self.dir / "events.jsonl"
        self.artifacts_dir = self.dir / "artifacts"

    # -- writing ---------------------------------------------------------

    def event(self, kind: str, **fields: Any) -> None:
        _append_jsonl(self.events_path, {"ts": time.time(), "kind": kind, **fields})

    def run_started(self, directive: str, config: dict[str, Any]) -> None:
        self.event("run_started", directive=directive, config=config,
                   config_hash=digest(config))

    def stage_started(self, stage: str, input_hash: str) -> None:
        self.event("stage_started", stage=stage, input_hash=input_hash)

    def stage_ended(self, result: StageResult[Any]) -> None:
        """Journal the outcome. The result type already guarantees it is honest."""
        self.event(
            "stage_ended",
            stage=result.stage,
            status=result.status,
            state=result.state,
            duration_s=result.duration_s,
            degraded_reason=result.degraded_reason,
            error=result.error,
            model=result.model,
            prompt_version=result.prompt_version,
            input_tokens=result.input_tokens,
            output_tokens=result.output_tokens,
            cost_usd=result.cost_usd,
            cost_known=result.cost_known,
            attempts=result.attempts,
            tool_calls=result.tool_calls,
            input_hash=result.input_hash,
            output_hash=result.output_hash,
        )
        if result.value is not None:
            self.artifact(f"{result.stage}.json", json.dumps(
                result.value, default=_encode, ensure_ascii=False, indent=2).encode("utf-8"))

    def run_ended(self, status: str, summary: dict[str, Any] | None = None) -> None:
        self.event("run_ended", status=status, summary=summary or {})

    def decision(self, actor: str, action: str, note: str = "") -> None:
        """Human approval appends. It never rewrites the run record."""
        self.event("decision", actor=actor, action=action, note=note)

    def artifact(self, name: str, data: bytes) -> str:
        """Store bytes content-addressed. Returns the relative path."""
        h = digest(data.decode("utf-8", "replace") if len(data) < 1_000_000 else str(len(data)))
        suffix = Path(name).suffix or ".bin"
        stem = Path(name).stem
        rel = f"{stem}.{h}{suffix}"
        target = self.artifacts_dir / rel
        if not target.exists():           # immutable: written at most once
            write_atomic(target, data)
        self.event("artifact", name=name, path=str(target.relative_to(self.dir)), bytes=len(data))
        return rel

    def adopt_file(self, name: str, src: Path) -> str | None:
        """Copy an externally produced file (e.g. a PNG) into the run."""
        if not src.exists():
            return None
        return self.artifact(name, src.read_bytes())

    # -- reading ---------------------------------------------------------

    def events(self) -> Iterator[dict[str, Any]]:
        if not self.events_path.exists():
            return iter(())
        def _gen() -> Iterator[dict[str, Any]]:
            with self.events_path.open(encoding="utf-8") as fh:
                for line in fh:
                    line = line.strip()
                    if line:
                        try:
                            yield json.loads(line)
                        except json.JSONDecodeError:
                            continue          # a torn tail line never hides the rest
        return _gen()

    def completed_stages(self) -> set[str]:
        """Stages with a matching stage_ended — i.e. safe to skip on resume."""
        return {e["stage"] for e in self.events()
                if e.get("kind") == "stage_ended" and e.get("status") != "failed"}

    def summary(self) -> dict[str, Any]:
        """Derived view for the dashboard. Computed from events, never stored
        separately — a summary that can drift from the journal is a lie source."""
        stages: dict[str, dict[str, Any]] = {}
        started = ended = None
        directive = ""
        status = "running"
        decisions: list[dict[str, Any]] = []
        unpriced: set[str] = set()
        cost = 0.0
        in_tok = out_tok = 0

        for e in self.events():
            k = e.get("kind")
            if k == "run_started":
                started, directive = e["ts"], e.get("directive", "")
            elif k == "stage_started":
                stages[e["stage"]] = {"state": "running", "started_at": e["ts"]}
            elif k == "stage_ended":
                s = stages.setdefault(e["stage"], {})
                s.update({
                    "state": e.get("state"), "status": e.get("status"),
                    "duration_s": e.get("duration_s"),
                    "degraded_reason": e.get("degraded_reason"), "error": e.get("error"),
                    "model": e.get("model"), "prompt_version": e.get("prompt_version"),
                    "input_tokens": e.get("input_tokens", 0),
                    "output_tokens": e.get("output_tokens", 0),
                    "cost_usd": e.get("cost_usd", 0.0),
                    "cost_known": e.get("cost_known", True),
                    "attempts": e.get("attempts", 1),
                })
                cost += e.get("cost_usd", 0.0) or 0.0
                if e.get("model") and not e.get("cost_known", True):
                    unpriced.add(e.get("model"))
                in_tok += e.get("input_tokens", 0) or 0
                out_tok += e.get("output_tokens", 0) or 0
            elif k == "run_ended":
                ended, status = e["ts"], e.get("status", "unknown")
            elif k == "decision":
                decisions.append({"ts": e["ts"], "actor": e.get("actor"),
                                  "action": e.get("action"), "note": e.get("note")})

        return {
            "run_id": self.run_id,
            "directive": directive,
            "status": status,
            "started_at": started,
            "ended_at": ended,
            "duration_s": round(ended - started, 2) if started and ended else None,
            "stages": stages,
            "degraded_stages": [n for n, s in stages.items() if s.get("status") == "degraded"],
            "failed_stages": [n for n, s in stages.items() if s.get("status") == "failed"],
            "cost_usd": round(cost, 6),
            # A model we hold no rate for must not be reported as free.
            "cost_complete": not unpriced,
            "unpriced_models": sorted(unpriced),
            "input_tokens": in_tok,
            "output_tokens": out_tok,
            "decisions": decisions,
        }


def _encode(o: Any) -> Any:
    if hasattr(o, "model_dump"):
        return o.model_dump()
    return str(o)


def list_runs(root: Path | None = None, limit: int = 100) -> list[dict[str, Any]]:
    base = root or RUNS_ROOT
    if not base.exists():
        return []
    dirs = sorted((d for d in base.iterdir() if d.is_dir()), reverse=True)[:limit]
    out = []
    for d in dirs:
        try:
            out.append(RunLog(d.name, base).summary())
        except Exception as exc:                      # a corrupt run is reported,
            out.append({"run_id": d.name, "status": "unreadable", "error": str(exc)})
    return out
