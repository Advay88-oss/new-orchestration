"""Structured logs on GCP without rewriting every print.

The pipeline reports with print() (several hundred calls). On Cloud Run a
plain line becomes a log entry with no severity, so "show me the errors of
the last job" had no answer and nothing could alert on one. In the cloud,
`install()` puts a writer in front of stdout and stderr that turns each line
into the JSON Cloud Logging reads:

    {"severity": "WARNING", "message": "...", "component": "pipeline",
     "job": "<CLOUD_RUN_JOB>", "execution": "<CLOUD_RUN_EXECUTION>"}

Severity comes from the line itself: stderr and lines that say error, failed,
traceback or ❌ are ERROR; warn / ⚠️ / degraded are WARNING; the rest INFO.
Only in a Cloud Run Job: on a laptop, and in the dashboard service (whose
Python answers are read from stdout), nothing changes.
"""
from __future__ import annotations

import io
import json
import os
import re
import sys

_ERROR = re.compile(r"(traceback|\berror\b|\bfailed\b|exception|❌|\bfatal\b)", re.I)
_WARN = re.compile(r"(\bwarn(ing)?\b|⚠|\bdegraded\b|\bskipped\b|\bretry)", re.I)


def severity(line: str, stream: str) -> str:
    if _ERROR.search(line):
        return "ERROR"
    if _WARN.search(line):
        return "WARNING"
    return "WARNING" if stream == "stderr" else "INFO"


class _JsonLines(io.TextIOBase):
    def __init__(self, raw, stream: str) -> None:
        self._raw, self._stream, self._buf = raw, stream, ""
        self._base = {k: v for k, v in (("component", "pipeline"),
                                        ("job", os.environ.get("CLOUD_RUN_JOB")),
                                        ("execution", os.environ.get("CLOUD_RUN_EXECUTION")),
                                        ("service", os.environ.get("K_SERVICE")),
                                        ("tenant", os.environ.get("BRAIN_TENANT"))) if v}

    def writable(self) -> bool:
        return True

    def write(self, s: str) -> int:
        self._buf += s
        while "\n" in self._buf:
            line, self._buf = self._buf.split("\n", 1)
            self._emit(line)
        return len(s)

    def _emit(self, line: str) -> None:
        if not line.strip():
            return
        stripped = line.strip()
        if stripped.startswith("{") and '"severity"' in stripped:
            self._raw.write(line + "\n")             # already structured
        else:
            self._raw.write(json.dumps({"severity": severity(line, self._stream), "message": line,
                                        **self._base}, ensure_ascii=False) + "\n")
        self._raw.flush()

    def flush(self) -> None:
        if self._buf:
            self._emit(self._buf)
            self._buf = ""
        self._raw.flush()

    def fileno(self) -> int:
        return self._raw.fileno()

    @property
    def encoding(self) -> str:                      # type: ignore[override]
        return getattr(self._raw, "encoding", "utf-8")


def in_job() -> bool:
    """A Cloud Run Job. Not the dashboard service: there Python's stdout is
    read by Node (the assistant's protocol, every runPython JSON answer) and
    must stay exactly as written."""
    return bool(os.environ.get("CLOUD_RUN_JOB")) and not os.environ.get("K_SERVICE")


def install() -> None:
    """Idempotent; only in a Cloud Run Job, and not when VANNA_PLAIN_LOGS=1."""
    if not in_job() or os.environ.get("VANNA_PLAIN_LOGS") == "1" or isinstance(sys.stdout, _JsonLines):
        return
    sys.stdout = _JsonLines(sys.stdout, "stdout")
    sys.stderr = _JsonLines(sys.stderr, "stderr")
