"""The Vanna mark, made usable on a dark poster.

`pipeline/state/logo.png` is the real lockup — the gradient mark plus the
white "vanna" wordtype — but it ships with a near-black rectangle baked in
rather than transparency (its alpha channel is uniformly opaque). Pasted
straight onto a poster it shows as a visible dark box around the logo.

So the box is keyed out by luminance: the mark and the wordtype are bright,
the background is not, and a soft threshold separates them without hard
edges. The alternative — typesetting "VANNA" as text — is what the posters
did before, and it is not the brand's mark.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Optional

from PIL import Image

def _logo_file() -> Path:
    """The tenant's logo, from its brand profile."""
    from pipeline.brand_brain import context as C
    return C.logo_path()

# Below this luminance a pixel is background; above it, logo. The ramp
# between keeps the mark's antialiased edges from going jagged.
_KEY_LOW = 26
_KEY_HIGH = 64


def _keyed() -> Optional[Image.Image]:
    """The current tenant's lockup with its background removed."""
    p = _logo_file()
    return _keyed_file(str(p)) if p else None


@lru_cache(maxsize=8)
def _keyed_file(path: str) -> Optional[Image.Image]:
    """One logo file with its background removed, or None if it is absent.
    Cached per file, so two tenants in one process never share a logo."""
    try:
        src = Image.open(path).convert("RGBA")
    except Exception:                               # noqa: BLE001 — boundary
        return None
    if src.getchannel("A").getextrema()[0] < 250:
        # Already transparent (brand_brain.logo captures it that way): keying
        # by luminance would erase a dark mark.
        return src.crop(src.getchannel("A").getbbox() or (0, 0, src.width, src.height))

    lum = src.convert("L")
    alpha = lum.point(
        lambda v: 0 if v <= _KEY_LOW
        else (255 if v >= _KEY_HIGH
              else int((v - _KEY_LOW) * 255 / (_KEY_HIGH - _KEY_LOW))))
    out = src.copy()
    out.putalpha(alpha)
    return out.crop(out.getbbox() or (0, 0, src.width, src.height))


def logo(height: int) -> Optional[Image.Image]:
    """The lockup at a given height, or None when the asset is missing.

    Returns None rather than raising: a poster without its logo is a lesser
    poster, but a render that fails outright produces nothing at all.
    """
    base = _keyed()
    if base is None or base.height == 0:
        return None
    w = max(1, int(base.width * height / base.height))
    return base.resize((w, height), Image.Resampling.LANCZOS)


def _lum(im: Image.Image, mask: Optional[Image.Image] = None) -> float:
    from PIL import ImageStat
    return ImageStat.Stat(im.convert("L"), mask).mean[0]


def contrast_safe(mark: Image.Image, ground: Image.Image) -> Image.Image:
    """The mark, inverted when it would vanish on the ground under it (a
    white logo on a white poster): same shape, opposite tone."""
    a = mark.getchannel("A")
    if abs(_lum(mark.convert("RGB"), a) - _lum(ground)) >= 70:
        return mark
    from PIL import ImageOps
    inv = ImageOps.invert(mark.convert("RGB")).convert("RGBA")
    inv.putalpha(a)
    return inv


def paste_logo(img: Image.Image, xy: tuple[int, int], height: int) -> int:
    """Composite the lockup and return the x it ends at, or the x given."""
    mark = logo(height)
    if mark is None:
        return xy[0]
    box = (xy[0], xy[1], min(img.width, xy[0] + mark.width), min(img.height, xy[1] + mark.height))
    if box[2] > box[0] and box[3] > box[1]:
        mark = contrast_safe(mark, img.crop(box))
    img.alpha_composite(mark, xy) if img.mode == "RGBA" else _paste_rgb(img, mark, xy)
    return xy[0] + mark.width


def _paste_rgb(img: Image.Image, mark: Image.Image, xy: tuple[int, int]) -> None:
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    layer.alpha_composite(mark, xy)
    img.paste(Image.alpha_composite(img.convert("RGBA"), layer).convert("RGB"), (0, 0))
