"""Vanna GTM Orchestration Pipeline Package."""

# Every paid API call is checked against the day's budget and counted
# (pipeline/ops/guard.py). Installed here so no module can bypass it.
try:
    from pipeline.ops.guard import install as _install_guard
    _install_guard()
except Exception as _exc:                           # noqa: BLE001 — never block an import, but say so
    import os as _os
    import sys as _sys
    _os.environ["VANNA_GUARD_MISSING"] = type(_exc).__name__ + ": " + str(_exc)[:200]
    print("[pipeline] the spend guard did not install (" + _os.environ["VANNA_GUARD_MISSING"]
          + "); paid calls through agent_runtime are refused", file=_sys.stderr)
