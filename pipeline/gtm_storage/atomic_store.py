"""Phase 9: Production Atomic File-Locking Storage Layer (atomic_store.py).

Provides concurrency-safe operations for .jsonl database tables.
Features:
  - Inter-process file locking via atomic lock files with timeout and retry.
  - Stale lock detection and automatic eviction (recovers from crashed processes).
  - Atomic write/replace using temporary files.
  - Thread-safe and cross-platform (Windows & POSIX).
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional


class LockTimeoutError(Exception):
    """Raised when a file lock cannot be acquired within the timeout window."""
    pass


class FileLockContext:
    """Inter-process cross-platform file lock using atomic lockfile semantics."""

    def __init__(self, target_path: Path, timeout_seconds: float = 10.0, poll_interval: float = 0.05):
        self.target_path = Path(target_path)
        self.lock_path = self.target_path.with_suffix(self.target_path.suffix + ".lock")
        self.timeout_seconds = timeout_seconds
        self.poll_interval = poll_interval
        self._acquired = False

    def acquire(self) -> None:
        start_time = time.time()
        pid = os.getpid()

        while True:
            try:
                # O_CREAT | O_EXCL is atomic across all major OSes
                fd = os.open(str(self.lock_path), os.O_CREAT | os.O_EXCL | os.O_RDWR)
                with os.fdopen(fd, "w") as f:
                    f.write(f"{pid}\n{time.time()}\n")
                self._acquired = True
                return
            except (FileExistsError, PermissionError):
                # On Windows, opening an existing exclusively locked file can raise PermissionError
                self._clean_stale_lock()

                if (time.time() - start_time) > self.timeout_seconds:
                    raise LockTimeoutError(
                        f"Timed out after {self.timeout_seconds}s waiting for lock on {self.target_path}"
                    )
                time.sleep(self.poll_interval)

    def release(self) -> None:
        if self._acquired:
            try:
                if self.lock_path.exists():
                    self.lock_path.unlink()
            except OSError:
                pass
            self._acquired = False

    def _clean_stale_lock(self) -> None:
        """Evicts lock files older than 30s to prevent deadlocks from dead processes."""
        try:
            if self.lock_path.exists():
                mtime = self.lock_path.stat().st_mtime
                if (time.time() - mtime) > 30.0:
                    self.lock_path.unlink(missing_ok=True)
        except OSError:
            pass

    def __enter__(self) -> FileLockContext:
        self.acquire()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.release()


class AtomicJsonlStore:
    """Atomic, concurrency-safe JSONL document store."""

    def __init__(self, file_path: Path | str, lock_timeout: float = 10.0):
        self.file_path = Path(file_path)
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        self.lock_timeout = lock_timeout

    def append(self, record: Dict[str, Any] | str) -> None:
        """Atomically appends a single JSON record to the store."""
        line = record if isinstance(record, str) else json.dumps(record)
        if not line.endswith("\n"):
            line += "\n"

        with FileLockContext(self.file_path, timeout_seconds=self.lock_timeout):
            with open(self.file_path, "a", encoding="utf-8") as f:
                f.write(line)
                f.flush()
                os.fsync(f.fileno())

    def append_batch(self, records: List[Dict[str, Any] | str]) -> None:
        """Atomically appends a batch of JSON records in a single locked transaction."""
        lines = []
        for r in records:
            line = r if isinstance(r, str) else json.dumps(r)
            if not line.endswith("\n"):
                line += "\n"
            lines.append(line)

        with FileLockContext(self.file_path, timeout_seconds=self.lock_timeout):
            with open(self.file_path, "a", encoding="utf-8") as f:
                f.writelines(lines)
                f.flush()
                os.fsync(f.fileno())

    def read_all(self) -> List[Dict[str, Any]]:
        """Atomically reads and parses all JSON records from the store."""
        if not self.file_path.exists():
            return []

        with FileLockContext(self.file_path, timeout_seconds=self.lock_timeout):
            records = []
            with open(self.file_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            records.append(json.loads(line))
                        except json.JSONDecodeError:
                            continue
            return records

    def atomic_overwrite(self, records: List[Dict[str, Any]]) -> None:
        """Safely overwrites the entire store using atomic rename."""
        temp_file = self.file_path.with_suffix(f".tmp.{os.getpid()}.{time.time()}")
        try:
            with open(temp_file, "w", encoding="utf-8") as f:
                for r in records:
                    f.write(json.dumps(r) + "\n")
                f.flush()
                os.fsync(f.fileno())

            with FileLockContext(self.file_path, timeout_seconds=self.lock_timeout):
                temp_file.replace(self.file_path)
        finally:
            if temp_file.exists():
                try:
                    temp_file.unlink()
                except OSError:
                    pass
