---
type: Brand Palette
title: Vanna social card palette
description: Colours, logo and card geometry used by the deterministic renderer.
tags: [brand, visual]
status: stable
resource: /pipeline/scripts/render_visual.py
background: "#0D0616"
colors:
  violet: "#703AE6"
  violet_light: "#9F7BEE"
  rose: "#FF007A"
  rose_light: "#FF54A6"
  red: "#FC5457"
  blue: "#32EEE2"
  gray: "#A9A9A9"
  gray_dim: "#949494"
accent: [red, rose, violet, blue]
logo: /pipeline/state/logo.png
logo_height_px: 44
card:
  width: 1080
  height: 1080
sources:
  - id: renderer
    resource: /pipeline/scripts/render_visual.py
    title: render_visual.py palette constants
  - id: design-refs
    resource: /design-references/cl-11
    title: Product cards cl-11 and cl-16
---

# Brand palette

The values the card renderer uses. Changing them here documents the intent;
`render_visual.py` lines 48–57 and 155 are still where they take effect, so
change both until the renderer reads this concept.

## Replacing these for another company

Replace the whole set together. The accents were chosen against a very dark
background (`#0D0616`) and will not survive a light one unaltered — a light
theme needs new accent values, not the same ones on a new backdrop.

Drop the new logo at the path in `logo`. **If it is missing the render still
succeeds with an empty brand block**, so check the produced card rather than
trusting the exit code.

Card geometry is fixed at 1080×1080 in two places: the CSS body rule and
Chrome's `--window-size`. Changing one without the other produces a cropped or
letterboxed card.

## Provenance

The dark social theme was derived from the product cards `cl-11` and `cl-16` in
`design references/`. Note that `design references/theme.md` documents the
company's **light** application system — it is not a spec for these cards. The
renderer is currently the only specification of the dark social variant, which
is why this concept exists.
