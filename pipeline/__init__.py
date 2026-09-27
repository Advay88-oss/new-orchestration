"""Vanna GTM Orchestration Pipeline Package."""

# Every paid API call is checked against the day's budget and counted
# (pipeline/ops/guard.py). Installed here so no module can bypass it.
try:
    from pipeline.ops.guard import install as _install_guard
    _install_guard()
except Exception:                                   # noqa: BLE001 — never block an import
    pass
