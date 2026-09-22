#!/usr/bin/env python3
"""Vanna Creative Architectural Diagram Generator (vanna_schematic_generator.py).

Produces creative, minimal-text 3D isometric architectural process diagrams
matching the user's approved reference visuals:
  - vanna_diagram_post2_blend_composability_83b2aa.png (Margin Account & Blend pool)
  - vanna_diagram_subsecond_solvency_rail_0964c2.png (Processor chip & solvency rail)
  - vanna_flash_post2_yield_stacking_fa05d6.png (Yield stacking & isolated cubes)

Core Design Invariants:
  1. Background: Deep obsidian (#080310) with signature Vanna ambient blooms
     (fuchsia-pink #C73770 in top-right, royal electric violet #7430CC in bottom-left).
  2. Logo: Official Vanna Monogram Logo in top-right corner.
  3. 3D Isometric Elements: Isometric modular cubes, processor microchips, lattice clusters.
  4. Minimal Text: Short, punchy node labels (2-3 words max) instead of paragraphs.
  5. Primary Engine: Google Model Garden gemini-3.1-flash-image with instant fallback.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, Optional

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

STATE_DIR = REPO_ROOT / "pipeline" / "state"
PUBLIC_DIR = REPO_ROOT / "hermes-mission" / "public"
STATE_DIR.mkdir(parents=True, exist_ok=True)
PUBLIC_DIR.mkdir(parents=True, exist_ok=True)

CHROME_PATH = os.environ.get("CHROME_PATH", r"C:\Program Files\Google\Chrome\Application\chrome.exe")
if not os.path.exists(CHROME_PATH):
    for p in [
        "/usr/bin/chromium",
        "/usr/bin/chromium-browser",
        "/usr/bin/google-chrome",
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
        os.path.expandvars(r"%PROGRAMFILES%\Google\Chrome\Application\chrome.exe")
    ]:
        if os.path.exists(p):
            CHROME_PATH = p
            break
    else:
        found = shutil.which("chromium") or shutil.which("chromium-browser") or shutil.which("google-chrome")
        if found:
            CHROME_PATH = found


def build_creative_diagram_prompt(archetype: str, title: str) -> str:
    """Builds a prompt-engineered specification for Gemini 3.1 Flash Image
    producing creative 3D isometric diagrams with minimal text.
    """
    arch = archetype.lower()

    base_aesthetic = (
        "Style: Modern Web3 Dark Mode UI, clean 3D isometric geometry combined with flat 2D vector elements, "
        "soft neon glows, high-contrast crisp typography, razor-sharp line work, generous negative space. "
        "Background: Deep space obsidian #080310 with signature Vanna ambient blooms: luminous fuchsia-pink #C73770 "
        "in the top-right corner and vibrant electric royal violet #7430CC in the bottom-left corner, with fine 35mm digital film grain. "
        "CRITICAL BRAND RULE: Keep the top-left corner and top header completely empty, dark, and clear of any Vanna logos, icons, or pill badges. "
        "Do NOT draw any Vanna logo, emblem, or badge on the canvas; the official lockup is composited externally onto the top-left only. "
        "MINIMAL TEXT: Only short, punchy 2-3 word labels below nodes. Zero text blocks, zero bullet points, zero paragraphs. "
        "Zero generic crypto spheres with rings, zero clutter, zero AI badges."
    )

    if "risk" in arch or "floor" in arch or "liquidation" in arch or "mercury" in arch or "solvency" in arch:
        # Prompt 1: Sub-Second Solvency Rail & Risk Guardian Processor
        return (
            "A clean horizontal process flow DeFi architectural risk diagram for Vanna Protocol on Stellar Soroban. "
            + base_aesthetic + " "
            "A balanced, three-stage linear left-to-right risk defense pipeline connected by glowing directional vector arrows: "
            "1. LEFT NODE (Data Ingestion): A dark frosted-glass squircle card with a thin lavender border, displaying bold cyan text '~320ms' "
            "and labeled beneath 'Mercury Event Stream' with subtitle 'Sub-Second Ingestion'. "
            "2. CENTER NODE (Compute Engine): A stylized 3D isometric computer processor microchip in pale lavender with coral/pink connector pins "
            "and soft inner core glow. Labeled beneath with bold text 'Risk Guardian' and subtitle '1.25x Rebalance'. "
            "3. RIGHT NODE (Solvency Floor): A dark rounded card with an intense glowing double neon coral/red border and protective outer aura, "
            "displaying bold text '1.10x' and labeled beneath 'Protected Solvency Floor' with subtitle 'Liquidation Floor'. Below it, a small pill tag '0.00014 XLM Gas'."
        )

    elif "margin" in arch or "account" in arch or "smartaccount" in arch or "soroban" in arch:
        # Prompt 2: Dedicated Soroban SmartAccount Margin Sandboxes
        return (
            "A clean horizontal process flow DeFi architectural schematic diagram for Vanna Protocol on Stellar Soroban. "
            + base_aesthetic + " "
            "A balanced, three-stage linear left-to-right transaction pipeline connected by glowing neon violet directional arrows: "
            "1. LEFT NODE (User Wallet Node): A semi-translucent frosted glass rounded-corner hexagon with a thin lavender border, "
            "labeled with clean white text 'Freighter Wallet' inside and '1,000 XLM Collateral' beneath. "
            "2. CENTER NODE (Soroban SmartAccount Sandbox): A large isometric 3D modular security container cube in solid periwinkle/lavender "
            "with clean darker contour lines and four coral-pink mechanical mounting latches, representing an isolated Soroban contract. "
            "Labeled beneath with bold white text 'Soroban SmartAccount' and subtitle 'Isolated Margin Sandbox'. "
            "3. RIGHT NODE (Multi-Venue Composability): A modular 3D isometric lattice cluster of interconnected dark purple cubes with vivid lavender edge highlights "
            "representing external DeFi liquidity. Hovering directly atop the cluster is a glowing cyan badge labeled '0.00014 XLM Gas'. "
            "Labeled beneath 'Composable Execution' with subtitle 'Multi-DApp Router'."
        )

    elif "sandbox" in arch or "isolated" in arch or "security" in arch or "gearbox" in arch or "morpho" in arch:
        # Prompt 2: Isolated Sandboxes vs Monolithic Pool
        return (
            "A clean comparative architectural schematic diagram for Vanna Protocol on Stellar Soroban. "
            + base_aesthetic + " "
            "A horizontal comparative layout with two distinct sides separated by a glowing cyan neon barrier: "
            "LEFT SIDE (Legacy EVM Pools): A single dark-red tinted glass chamber showing internal structural cracks and commingled red tokens, "
            "labeled beneath 'Monolithic Pool' with subtitle 'Shared Contagion Risk'. "
            "CENTER: A vertical glowing neon cyan firewall line with small shield icon. "
            "RIGHT SIDE (Vanna Protocol): Three separate, discrete 3D isometric modular cube vaults in lavender with coral edge latches and glowing green status lights, "
            "completely isolated from each other. Labeled beneath 'Vanna SmartAccounts' with subtitle 'Quarantined Sandboxes'."
        )

    elif "leverage" in arch or "multiplier" in arch or "capital" in arch or "10x" in arch:
        # Prompt 3: 10x Capital Efficiency Multiplier
        return (
            "A clean horizontal capital multiplier process diagram for Vanna Protocol on Stellar Soroban. "
            + base_aesthetic + " "
            "A balanced three-stage linear left-to-right amplification pipeline connected by glowing cyan arrows: "
            "1. LEFT NODE (Collateral Input): A single sleek 3D isometric modular cube in pale lavender, labeled beneath '1,000 XLM' with subtitle '1x Collateral'. "
            "2. CENTER NODE (Amplifier): A glowing 3D isometric prismatic funnel transformer in dark violet with electric cyan energy streams passing through it, "
            "labeled beneath with bold text '10x Multiplier' with subtitle '(C+B)/(D+B) ≥ 1.10'. "
            "3. RIGHT NODE (Effective Margin): A neat stacked isometric cluster of ten illuminated modular cubes in glowing lavender and cyan, "
            "labeled beneath '10,000 USDC' with subtitle 'Effective Borrow Power'."
        )

    else:
        # Default Prompt 4: Blend Composability & Margin Account
        return (
            "A clean horizontal process flow DeFi architectural schematic diagram for Vanna Protocol on Stellar Soroban. "
            + base_aesthetic + " "
            "A balanced, three-stage linear left-to-right transaction pipeline connected by glowing neon violet directional arrows: "
            "1. LEFT NODE (User Wallet Node): A semi-translucent frosted glass rounded-corner hexagon with a thin lavender border, "
            "labeled with clean white text 'User Wallet' inside and 'Deploy Collateral' beneath. "
            "2. CENTER NODE (Vanna Margin Account): A large isometric 3D modular security container cube in solid periwinkle/lavender with clean darker contour lines, "
            "featuring four small rectangular coral/salmon-pink mounting tabs on the visible edges. Labeled with bold white text 'Vanna Margin Account' "
            "and a muted subtitle 'Isolated Sandbox'. "
            "3. RIGHT NODE (Blend Lending Pool): A modular 3D isometric lattice cluster of interconnected dark purple cubes with vivid lavender edge highlights. "
            "Hovering directly atop the cluster is a glowing circular badge labeled 'BLUSDC'. Labeled beneath 'Blend Protocol' with subtitle 'Lending Pool'."
        )


def overlay_official_vanna_logo(target_path: Path):
    """Composites the full official Vanna brand badge ([Logo Icon] VANNA // COMPOSABLE CREDIT)
    onto the top-left corner of the visual, matching the exact brand specification.
    """
    badge_path = STATE_DIR / "vanna_full_brand_badge.png"
    if not badge_path.exists():
        badge_path = STATE_DIR / "vanna_official_master_logo.png"
    if not badge_path.exists():
        return
    try:
        from PIL import Image
        base_img = Image.open(target_path).convert("RGBA")
        badge_img = Image.open(badge_path).convert("RGBA")

        # Size badge to ~18% of canvas width for ideal proportion
        w_target = int(base_img.width * 0.18)
        h_target = int(w_target * badge_img.height / badge_img.width)
        badge_resized = badge_img.resize((w_target, h_target), Image.Resampling.LANCZOS)

        # Position at top-left with 4% horizontal margin and 5% vertical margin
        margin_x = int(base_img.width * 0.04)
        margin_y = int(base_img.height * 0.05)
        pos_x = margin_x
        pos_y = margin_y

        base_img.paste(badge_resized, (pos_x, pos_y), badge_resized)
        base_img.convert("RGB").save(target_path)
        print(f"✨ Composited full Vanna logo + name lockup onto top-left of {target_path.name}")
    except Exception as e:
        print(f"⚠️ Brand lockup overlay notice: {e}")


def generate_vanna_schematic(
    archetype: str,
    title: str,
    subtitle: str,
    output_path: Path | str,
    metrics: Optional[Dict[str, str]] = None
) -> Path:
    """Generates a creative 3D isometric diagram with minimal text and Vanna branding."""
    out = Path(output_path).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)

    # 1. Primary Engine: Gemini 3.1 Flash Image (Model Garden)
    try:
        from pipeline.scripts.gemini_flash_image import generate_gemini_image
        prompt = build_creative_diagram_prompt(archetype, title)
        print(f"🎨 Synthesizing creative 3D isometric diagram via Gemini 3.1 Flash Image (Archetype: {archetype})...")
        generate_gemini_image(
            prompt=prompt,
            output_path=out,
            project="vanna-mcp",
            location="global",
            model="gemini-3.1-flash-image"
        )
        if out.exists() and out.stat().st_size > 50000:
            overlay_official_vanna_logo(out)
            print(f"✅ Generated Creative 3D Isometric Visual: {out.name} ({out.stat().st_size:,} bytes)")
            # Copy to public directory for instant Next.js rendering
            if PUBLIC_DIR.exists() and out.resolve() != (PUBLIC_DIR / out.name).resolve():
                try:
                    shutil.copy(str(out), str(PUBLIC_DIR / out.name))
                except Exception:
                    pass
            return out
    except Exception as e:
        print(f"⚠️ Gemini 3.1 Flash Image generation encountered notice: {e}. Checking fallbacks...")

    # 2. Fast Fallback: Standalone Visual Asset if present
    archetype_key = archetype.lower()
    fallback_map = {
        "margin": "vanna_diagram_post2_blend_composability.png",
        "blend": "vanna_diagram_post2_blend_composability.png",
        "composab": "vanna_diagram_composable_credit_pipeline.png",
        "risk": "vanna_diagram_subsecond_solvency_rail.png",
        "floor": "vanna_diagram_subsecond_solvency_rail.png",
        "solvency": "vanna_diagram_subsecond_solvency_rail.png",
        "sandbox": "vanna_flash_post2_yield_stacking.png",
        "multiplier": "vanna_simple_post1_multiplier.png",
        "leverage": "vanna_simple_post1_multiplier.png"
    }

    for k, fname in fallback_map.items():
        if k in archetype_key:
            src = STATE_DIR / fname
            if src.exists():
                shutil.copy(str(src), str(out))
                overlay_official_vanna_logo(out)
                if PUBLIC_DIR.exists() and out.resolve() != (PUBLIC_DIR / out.name).resolve():
                    try:
                        shutil.copy(str(out), str(PUBLIC_DIR / out.name))
                    except Exception:
                        pass
                print(f"✅ Bound verified creative diagram asset: {out.name}")
                return out

    # Generic fallback to vanna_creative_diagram_test.png
    generic_src = STATE_DIR / "vanna_creative_diagram_test.png"
    if generic_src.exists():
        shutil.copy(str(generic_src), str(out))
        overlay_official_vanna_logo(out)
        if PUBLIC_DIR.exists():
            shutil.copy(str(out), str(PUBLIC_DIR / out.name))
        print(f"✅ Bound fallback creative diagram: {out.name}")
        return out

    return out


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Vanna Schematic Diagram Generator")
    parser.add_argument("--archetype", type=str, default="blend_composability")
    parser.add_argument("--title", type=str, default="10x Composable Margin on Blend v2 Pools")
    parser.add_argument("--subtitle", type=str, default="Single collateral deposit into isolated SmartAccount executes atomic borrowing against Blend pools.")
    parser.add_argument("--output", type=str, default=None)
    args = parser.parse_args()

    out_p = Path(args.output) if args.output else STATE_DIR / "vanna_creative_test_run.png"
    generate_vanna_schematic(
        archetype=args.archetype,
        title=args.title,
        subtitle=args.subtitle,
        output_path=out_p
    )
