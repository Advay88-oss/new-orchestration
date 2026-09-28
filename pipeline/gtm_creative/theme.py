"""The code-set renderers' colours, from the current company's profile.

archetypes.py was written for Vanna: its ground, ink and accent are module
constants read from docs.vanna.finance, and premium_archetypes / motion import
them by name. A Morpho poster came out on Vanna's dark violet and magenta.

apply() sets those constants, in every module that holds a copy, from the
tenant's palette (profile visual.palette: ground/background, text, accent,
accent_2 ...), before a render. Vanna keeps its original tokens exactly — its
posters are approved as they are. A light ground (Morpho's #FFFFFF) gets dark
ink, a faint grid and soft accent blooms instead of a dark field.
"""
from __future__ import annotations

from typing import Any, Optional

_NAMES = ("GROUND", "SURFACE", "SURFACE_2", "LINE", "INK", "INK_MUTED", "INK_FAINT", "INK_SOFT",
          "VIOLET", "VIOLET_LIGHT", "GROUND_BASE", "VIOLET_BLOOM", "PINK_BLOOM", "GRID", "BLOOM_ALPHA")
_originals: dict[str, dict[str, Any]] = {}


def _hex(v: Any) -> Optional[tuple[int, int, int]]:
    s = str(v or "").strip().lstrip("#")
    if len(s) == 3:
        s = "".join(c * 2 for c in s)
    if len(s) != 6:
        return None
    try:
        return tuple(int(s[i:i + 2], 16) for i in (0, 2, 4))      # type: ignore[return-value]
    except ValueError:
        return None


def _mix(a: tuple, b: tuple, t: float) -> tuple[int, int, int]:
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))  # type: ignore[return-value]


def _lum(c: tuple) -> float:
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def tokens(tenant: Optional[str] = None) -> Optional[dict[str, Any]]:
    """The renderer tokens for a tenant; None for Vanna (keep the originals)
    or when the profile has no usable palette."""
    from pipeline.brand_brain import context as C
    from pipeline.brand_brain.client import current_tenant
    t = tenant or current_tenant()
    if t == "vanna":
        return None
    pal = C.palette(t) or {}
    ground = _hex(pal.get("ground") or pal.get("background") or pal.get("bg"))
    if not ground:
        return None
    light = _lum(ground) > 140
    text = _hex(pal.get("text") or pal.get("ink")) or ((24, 24, 24) if light else (240, 240, 242))
    accent = _hex(pal.get("accent") or pal.get("primary")) or _mix(text, ground, 0.3)
    accent2 = (_hex(pal.get("accent_light") or pal.get("accent_2") or pal.get("secondary"))
               or _mix(accent, ground, 0.35))
    bloom2 = _hex(pal.get("accent_3") or pal.get("glow_high_right")) or accent2
    return {
        "GROUND": ground, "GROUND_BASE": ground,
        "SURFACE": _mix(ground, text, 0.04), "SURFACE_2": _mix(ground, text, 0.08),
        "LINE": _mix(ground, text, 0.14), "GRID": _mix(ground, text, 0.05 if light else 0.04),
        "INK": text, "INK_SOFT": _mix(text, ground, 0.06),
        "INK_MUTED": _mix(text, ground, 0.42), "INK_FAINT": _mix(text, ground, 0.6),
        "VIOLET": accent, "VIOLET_LIGHT": accent if light else accent2,
        "VIOLET_BLOOM": accent, "PINK_BLOOM": bloom2,
        # Blooms on a white ground are a tint, not a glow.
        "BLOOM_ALPHA": 0.06 if light else 0.40,
    }


def apply(tenant: Optional[str] = None) -> Optional[dict[str, Any]]:
    """Set the tokens in every renderer module (restoring the originals for
    Vanna, so one process can render two tenants in turn)."""
    import importlib
    mods = []
    for name in ("pipeline.gtm_creative.archetypes", "pipeline.gtm_creative.premium_archetypes",
                 "pipeline.gtm_creative.motion"):
        try:
            mods.append(importlib.import_module(name))
        except Exception:                           # noqa: BLE001 — a module that fails to import renders nothing
            continue
    for m in mods:
        _originals.setdefault(m.__name__, {n: getattr(m, n) for n in _NAMES if hasattr(m, n)})
    tok = tokens(tenant)
    for m in mods:
        values = tok if tok is not None else _originals[m.__name__]
        for n, v in values.items():
            if hasattr(m, n) or n in ("GRID", "BLOOM_ALPHA"):
                setattr(m, n, v)
    return tok
