"""Where one company's learning state lives.

Feedback, learned rules, preferences, the coach's cursor and performance
records were single files shared by every tenant, so a rule learned from
Vanna's posters was added to Auri's prompts. Each is now resolved per tenant
at the moment it is read or written:

    the primary tenant (vanna)   the original path, unchanged — nothing moves
    any other tenant             <same folder>/tenants/<tenant>/<same name>

The tenant is the process's (BRAIN_TENANT, set for every run and every
cloud job); state_sync backs the tenants/ folders up with the rest.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

PRIMARY = "vanna"
_TENANT = re.compile(r"^[a-z0-9][a-z0-9_-]{1,40}$")


def tenant_file(default: Path, tenant: Optional[str] = None) -> Path:
    from pipeline.brand_brain.client import current_tenant
    t = (tenant or current_tenant() or PRIMARY).lower()
    if t == PRIMARY:
        return default
    if not _TENANT.match(t):
        raise ValueError("not a tenant id: " + repr(t))
    p = default.parent / "tenants" / t / default.name
    p.parent.mkdir(parents=True, exist_ok=True)
    return p
