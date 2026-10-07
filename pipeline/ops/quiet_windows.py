"""Windows must not open a console for a pipeline child.

A post or a visual starts Python, then ffmpeg and the spend proxy. Each of
those is a console program. With no console to inherit, Windows opens a new
one — the PowerShell window that appears on every trigger. CREATE_NO_WINDOW
keeps the process and drops the window.
"""
from __future__ import annotations

import os
import subprocess

_NO_WINDOW = 0x08000000


def install() -> None:
    if os.name != "nt" or getattr(subprocess, "_vanna_no_console", False):
        return
    popen = subprocess.Popen
    run = subprocess.run

    class _Popen(popen):
        def __init__(self, args, **kwargs):
            kwargs["creationflags"] = int(kwargs.get("creationflags") or 0) | _NO_WINDOW
            super().__init__(args, **kwargs)

    def _run(*args, **kwargs):
        kwargs["creationflags"] = int(kwargs.get("creationflags") or 0) | _NO_WINDOW
        return run(*args, **kwargs)

    subprocess.Popen = _Popen          # type: ignore[misc]
    subprocess.run = _run              # type: ignore[assignment]
    subprocess._vanna_no_console = True  # type: ignore[attr-defined]
