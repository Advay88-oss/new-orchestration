"""Vanna design tokens — the single source of truth for anything rendered.

Four mutually incompatible design systems existed in the repo, all of them in
modules that could not be imported. The shipping pipeline's entire "design
system" was one sentence in a prompt, which is why typography was whatever a
diffusion model felt like.

Tokens here are consumed by `render.py` and validated against `VisualSpec`. A
colour that is not in this file cannot reach a pixel: `PaletteSlice` values are
checked against `PALETTE` before rendering.

Values are inherited from the existing brand system (`gtm_orchestration/
creative_director.py`) and the strict-whitespace layout rules from the dead
`render_visual.py`, which were sound — they were simply unreachable.
"""
from __future__ import annotations

from typing import Final

# --------------------------------------------------------------------------
# Palette — named, closed set
# --------------------------------------------------------------------------

PALETTE: Final[dict[str, str]] = {
    "obsidian": "#07020D",          # ground
    "violet_bloom": "#471485",
    "fuchsia_bloom": "#5E0D46",
    "lavender": "#A387FF",          # primary accent
    "coral": "#FC5457",             # risk / negative only
    "cyan": "#22D3C4",              # telemetry / confirmation only
    "white": "#FFFFFF",
}

# Opacity steps are chosen for contrast against the obsidian ground, not for
# looks. The visual critic flagged the original 0.55/0.35 steps as failing
# legibility on captions and the disclaimer; these clear ~4.5:1 while keeping
# the hierarchy readable.
INK: Final[dict[str, str]] = {
    "hero": "#FFFFFF",
    "body": "rgba(255,255,255,0.78)",
    "muted": "rgba(255,255,255,0.64)",
    "dim": "rgba(255,255,255,0.50)",
}

HAIRLINE: Final[str] = "rgba(255,255,255,0.08)"

# One accent per asset. Two accents is the single most reliable way to make a
# composition read as generic AI output.
MAX_ACCENTS: Final[int] = 1


# --------------------------------------------------------------------------
# Typography — a real scale, not ad-hoc sizes
# --------------------------------------------------------------------------

FONT_SANS: Final[str] = "'Plus Jakarta Sans', 'Segoe UI', system-ui, sans-serif"
FONT_MONO: Final[str] = "'JetBrains Mono', 'Cascadia Mono', ui-monospace, monospace"

# Major-third scale anchored at 28px body.
TYPE: Final[dict[str, dict[str, object]]] = {
    "hero":     {"size": 180, "weight": 700, "tracking": "-0.04em", "leading": 0.92},
    "headline": {"size": 52,  "weight": 600, "tracking": "-0.02em", "leading": 1.12},
    "subhead":  {"size": 34,  "weight": 500, "tracking": "-0.01em", "leading": 1.25},
    "body":     {"size": 28,  "weight": 400, "tracking": "0",       "leading": 1.45},
    "label":    {"size": 18,  "weight": 600, "tracking": "0.14em",  "leading": 1.2},
    "caption":  {"size": 16,  "weight": 400, "tracking": "0.02em",  "leading": 1.4},
}

# Letterspacing on uppercase labels is a token, not a guess. The old pipeline
# produced "TECHNICALARCHITECTURE" because the overlay had no tracking at all.
UPPERCASE_TRACKING: Final[str] = "0.14em"


# --------------------------------------------------------------------------
# Layout — the whitespace rule is load-bearing
# --------------------------------------------------------------------------

CANVAS: Final[int] = 1080
MARGIN: Final[int] = 120
SAFE_WIDTH: Final[int] = CANVAS - 2 * MARGIN          # 840
CONTENT_MAX_HEIGHT: Final[int] = 400                  # the remaining 680 stays empty
GRID_COLUMNS: Final[int] = 12
GUTTER: Final[int] = 24

# Vertical rhythm. Every gap is a multiple of the base unit.
UNIT: Final[int] = 8
SPACE: Final[dict[str, int]] = {
    "xs": UNIT,          # 8
    "sm": UNIT * 2,      # 16
    "md": UNIT * 4,      # 32
    "lg": UNIT * 7,      # 56
    "xl": UNIT * 12,     # 96
}

LOGO_SIZE: Final[int] = 32
# The logo badge sits in its own reserved band. The old compositor pasted it at a
# fixed percentage with no bounding-box awareness, so it collided with headlines.
LOGO_BAND_HEIGHT: Final[int] = LOGO_SIZE + SPACE["md"]

RENDER_SCALE: Final[int] = 2                          # retina; 2160px output


def validate_palette_slice(ink: str, ground: str, accent: str) -> list[str]:
    """Reject colours that are not tokens. Returns a list of problems."""
    problems: list[str] = []
    allowed_ink = set(INK.values()) | {PALETTE["white"]}
    allowed_ground = {PALETTE["obsidian"], PALETTE["violet_bloom"], PALETTE["fuchsia_bloom"]}
    allowed_accent = {PALETTE["lavender"], PALETTE["cyan"], PALETTE["coral"]}

    if ink not in allowed_ink:
        problems.append(f"ink {ink!r} is not a design token")
    if ground not in allowed_ground:
        problems.append(f"ground {ground!r} is not a design token")
    if accent not in allowed_accent:
        problems.append(f"accent {accent!r} is not a design token")
    return problems


def default_palette() -> tuple[str, str, str]:
    return INK["hero"], PALETTE["obsidian"], PALETTE["lavender"]


# Treatments the brand has explicitly rejected. Carried here rather than in a
# module that nothing imports — the old `overfitted_cliches_to_avoid` list was
# imported once and referenced on zero subsequent lines, while the pipeline
# shipped item #2 from it verbatim.
REJECTED_TREATMENTS: Final[tuple[str, ...]] = (
    "three identical cubes connected by arrows",
    "horizontal three-column wallet-to-cube-to-lattice flow",
    "lavender processor chips with neon pins",
    "generic glowing spheres with concentric rings",
    "neon grid floors or Tron aesthetic",
    "floating 3D cubes with no architectural purpose",
    "flying coins or cartoon dollar signs",
    "stock crypto dashboards or candlestick charts",
)


def css_variables() -> str:
    """Tokens as CSS custom properties, so the stylesheet cannot drift."""
    lines = [f"  --ink-{k}: {v};" for k, v in INK.items()]
    lines += [f"  --c-{k}: {v};" for k, v in PALETTE.items()]
    lines += [f"  --space-{k}: {v}px;" for k, v in SPACE.items()]
    lines += [
        f"  --hairline: {HAIRLINE};",
        f"  --font-sans: {FONT_SANS};",
        f"  --font-mono: {FONT_MONO};",
        f"  --margin: {MARGIN}px;",
        f"  --safe-width: {SAFE_WIDTH}px;",
        f"  --track-upper: {UPPERCASE_TRACKING};",
    ]
    for name, spec in TYPE.items():
        lines.append(f"  --type-{name}-size: {spec['size']}px;")
        lines.append(f"  --type-{name}-weight: {spec['weight']};")
        lines.append(f"  --type-{name}-tracking: {spec['tracking']};")
        lines.append(f"  --type-{name}-leading: {spec['leading']};")
    return ":root {\n" + "\n".join(lines) + "\n}"
