#!/usr/bin/env python3
"""Vanna Meme Visual Generator (vanna_meme_renderer.py).

Generates unique, distinct cultural crypto/DeFi meme visuals using
Gemini 3.1 Flash Image (nano banana pro) on Model Garden (project: vanna-mcp, location: global),
composited with the official Vanna brand badge ([Icon] VANNA // COMPOSABLE CREDIT)
in the top-left corner.
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import shutil
import sys
import time
from pathlib import Path
from typing import Any, Dict

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

STATE_DIR = REPO_ROOT / "pipeline" / "state"
PUBLIC_DIR = REPO_ROOT / "hermes-mission" / "public"
STATE_DIR.mkdir(parents=True, exist_ok=True)
PUBLIC_DIR.mkdir(parents=True, exist_ok=True)

from pipeline.scripts.gemini_flash_image import generate_gemini_image
from pipeline.scripts.vanna_schematic_generator import overlay_official_vanna_logo


def build_meme_prompt(meme_data: Dict[str, Any]) -> str:
    """Build the image prompt from `core.media`.

    The previous builder hardcoded product figures into the picture — "fixed
    '0.00014 XLM'", "a glowing holographic 1.10x protective shield" — so the
    memes surface printed numbers that the claim verifier marks unsupported or
    refuted, bypassing the gate entirely. It also produced the lavender
    processor chip that sits on the brand's own rejected-treatments list.

    Delegating keeps one meme prompt in the codebase: humour-first, readable at
    thumbnail size, no invented statistics, and the rejected treatments
    excluded by construction.
    """
    import sys as _sys
    _repo = str(pathlib.Path(__file__).resolve().parents[2])
    if _repo not in _sys.path:
        _sys.path.insert(0, _repo)
    from core.design import REJECTED_TREATMENTS

    concept = str(meme_data.get("vanna_angle") or meme_data.get("reference") or "crypto credit").strip()
    caption = str(meme_data.get("copy") or concept).strip()
    fmt = str(meme_data.get("format") or "single panel").strip()

    return (
        f"Crypto-native meme illustration, {fmt}. Concept: {concept}. "
        f'Caption to render legibly in the image: "{caption}". '
        "Clean, high-contrast, readable at thumbnail size. Dry humour, not cringe. "
        "No fabricated statistics, no invented metrics, no protocol logos, no price charts. "
        "Do NOT produce any of: " + "; ".join(REJECTED_TREATMENTS) + "."
    )

def render_meme_card(meme_data: Dict[str, Any], output_path: Path | str | None = None) -> Path:
    """Renders a unique meme visual using Gemini 3.1 Flash Image."""
    m_id = meme_data.get("id", "meme_custom")
    out = Path(output_path) if output_path else STATE_DIR / f"meme_{m_id}_visual.png"
    out.parent.mkdir(parents=True, exist_ok=True)

    prompt = build_meme_prompt(meme_data)

    # Generated through core.media, which routes `meme_image` to nano banana pro
    # over the API key. The previous path called Vertex, where that model is not
    # published (HTTP 404), then copied a pre-existing PNG from state/ and
    # reported success — so the memes surface showed a recycled diagram carrying
    # figures the claim verifier rejects. A failed render is now a failure.
    import sys as _sys
    _repo = str(pathlib.Path(__file__).resolve().parents[2])
    if _repo not in _sys.path:
        _sys.path.insert(0, _repo)
    from core.media import generate_image, MediaError

    try:
        generated, used_model = generate_image(prompt, "meme_image", out)
    except MediaError as exc:
        raise RuntimeError(f"meme render failed: {exc}") from exc

    if not generated.exists() or generated.stat().st_size < 20_000:
        raise RuntimeError(
            f"meme render produced no usable image at {generated} "
            f"({generated.stat().st_size if generated.exists() else 0} bytes)")

    overlay_official_vanna_logo(out)
    print(f"✅ Generated meme visual via {used_model}: {out.name} ({out.stat().st_size:,} bytes)")

    if PUBLIC_DIR.exists() and out.resolve() != (PUBLIC_DIR / out.name).resolve():
        try:
            shutil.copy(str(out), str(PUBLIC_DIR / out.name))
        except Exception:
            pass

    return out


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Vanna Meme Visual Generator (Gemini 3.1 Flash Image)")
    parser.add_argument("--meme-id", type=str, help="Render specific meme ID from state")
    parser.add_argument("--output", type=str, help="Output PNG path", default=None)
    args = parser.parse_args()

    if args.meme_id:
        memes_file = REPO_ROOT / "state" / "panels" / "memes.json"
        if memes_file.exists():
            data = json.loads(memes_file.read_text(encoding="utf-8"))
            m = next((x for x in data.get("memes", []) if x.get("id") == args.meme_id), None)
            if m:
                render_meme_card(m, args.output)
            else:
                print(f"Meme {args.meme_id} not found in state/panels/memes.json")
    else:
        print("Usage: python vanna_meme_renderer.py --meme-id <ID>")
