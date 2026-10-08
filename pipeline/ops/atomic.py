"""State files that survive a crash mid-write, and one writer at a time.

Every JSON file in pipeline/state is read and rewritten by more than one
process: the scheduler's job threads, the assistant, the dashboard, a cloud
job. A plain write_text that is killed half way leaves a truncated file,
which then parsed as {} — and an empty scheduler state means every job looks
never-run and all of them start at once.

    write_json(path, obj)        temp file in the same folder, fsync, os.replace;
                                 the previous good copy is kept as <name>.bak
    read_json(path, default)     the file, else its .bak, else `default`;
                                 strict=True raises CorruptState instead of
                                 falling back to the default
    with FileLock(path): ...     one process at a time (a <name>.lock file,
                                 taken with O_EXCL; a holder that died leaves
                                 it, so one older than `stale_s` is taken over)
"""
from __future__ import annotations

import json
import os
import shutil
import time
from pathlib import Path
from typing import Any


class CorruptState(RuntimeError):
    """A state file and its backup both failed to parse."""


def write_text(path: Path | str, text: str, *, backup: bool = True) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name("." + path.name + "." + str(os.getpid()) + "." + str(time.time_ns()) + ".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(text)
        f.flush()
        os.fsync(f.fileno())
    if backup and path.exists():
        try:
            shutil.copy2(path, path.with_name(path.name + ".bak"))
        except OSError:
            pass
    # Windows refuses to replace a file another process has open for a moment.
    for attempt in range(20):
        try:
            os.replace(tmp, path)
            return
        except PermissionError:
            if attempt == 19:
                tmp.unlink(missing_ok=True)
                raise
            time.sleep(0.05)


def write_json(path: Path | str, obj: Any, *, backup: bool = True, **dumps: Any) -> None:
    dumps.setdefault("indent", 2)
    write_text(path, json.dumps(obj, **dumps), backup=backup)


def read_json(path: Path | str, default: Any = None, *, strict: bool = False) -> Any:
    """The parsed file. A missing file is `default`. A file that does not
    parse falls back to its .bak; when that fails too, `default` — or, with
    strict=True, CorruptState, so the caller can stop instead of acting on
    an empty state."""
    path = Path(path)
    if not path.exists():
        return default
    for candidate in (path, path.with_name(path.name + ".bak")):
        try:
            return json.loads(candidate.read_text(encoding="utf-8"))
        except FileNotFoundError:
            continue
        except (OSError, ValueError):
            continue
    if strict:
        raise CorruptState(str(path) + " and its backup do not parse")
    return default


class FileLock:
    """A cross-process lock beside `path` (<name>.lock)."""

    def __init__(self, path: Path | str, *, timeout_s: float = 30.0, stale_s: float = 120.0) -> None:
        p = Path(path)
        self.lock = p.with_name(p.name + ".lock")
        self.timeout_s, self.stale_s = timeout_s, stale_s

    def __enter__(self) -> "FileLock":
        self.lock.parent.mkdir(parents=True, exist_ok=True)
        deadline = time.time() + self.timeout_s
        while True:
            try:
                fd = os.open(str(self.lock), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                os.write(fd, str(os.getpid()).encode())
                os.close(fd)
                return self
            except FileExistsError:
                try:
                    if time.time() - self.lock.stat().st_mtime > self.stale_s:
                        self.lock.unlink(missing_ok=True)
                        continue
                except FileNotFoundError:
                    continue
                if time.time() > deadline:
                    raise TimeoutError("another process holds " + str(self.lock))
                time.sleep(0.1)

    def __exit__(self, *exc: Any) -> None:
        self.lock.unlink(missing_ok=True)
