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
_DETACHED = 0x00000008  # Windows ignores CREATE_NO_WINDOW when this is also set


def _quiet_argv(args):
    """python.exe is a console program. pythonw.exe is the same interpreter
    without a window. Swap it when the venv has it."""
    if isinstance(args, (list, tuple)) and args:
        head = args[0]
        if isinstance(head, str) and head.lower().endswith("python.exe"):
            windowless = head[: -len("python.exe")] + "pythonw.exe"
            if os.path.isfile(windowless):
                args = [windowless, *list(args)[1:]]
    return args


def _quiet_flags(kwargs: dict) -> None:
    flags = int(kwargs.get("creationflags") or 0) | _NO_WINDOW
    flags &= ~_DETACHED
    kwargs["creationflags"] = flags


def install() -> None:
    if os.name != "nt" or getattr(subprocess, "_vanna_no_console", False):
        return
    popen = subprocess.Popen
    run = subprocess.run

    class _Popen(popen):
        def __init__(self, args, **kwargs):
            args = _quiet_argv(args)
            _quiet_flags(kwargs)
            super().__init__(args, **kwargs)

    def _run(*args, **kwargs):
        if args:
            args = (_quiet_argv(args[0]), *args[1:])
        _quiet_flags(kwargs)
        return run(*args, **kwargs)

    subprocess.Popen = _Popen          # type: ignore[misc]
    subprocess.run = _run              # type: ignore[assignment]
    subprocess._vanna_no_console = True  # type: ignore[attr-defined]
