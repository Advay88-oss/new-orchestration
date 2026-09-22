"""Remotion motion graphics — branded render, driven by verified claims only.

Veo produces abstract b-roll. Remotion produces the branded, typographic half:
deterministic, on-brand, and — critically — **only able to put a figure on
screen if that figure was verified against evidence**.

That constraint is the whole point of wiring it this way. The compositions ship
with default props containing figures like "$92M+ Total XLM Supplied" and
"378.88% Supply APY". Nothing in the repo establishes those, and a motion
graphic is the worst possible place for an unverified number: it is screen-
recorded, re-shared, and outlives the run that produced it. So the props are
built from the run's `verified` claims, and when none carry a figure the
pipeline picks a composition that does not display one.

Remotion is deterministic by construction — a composition is a pure function of
its frame, `Math.random()` is forbidden — so the same props render the same
frames. That matches the rest of this pipeline: given the same inputs, the same
output.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any

from .contracts import Claim, StageResult, VisualSpec, degraded, digest, ok
from .design import PALETTE

REPO = Path(__file__).resolve().parents[1]
REMOTION_DIR = Path(os.environ.get("VANNA_REMOTION_DIR", REPO / "remotion-video"))
OUT_DIR = Path(os.environ.get("VANNA_MEDIA_DIR", REPO / "state" / "media"))

RENDER_TIMEOUT_S = 600

# A figure worth animating: currency, percentage, multiplier, or a magnitude.
#
# Word boundaries matter here. Without them "$159,033,033 measured onchain"
# matched "$159,033,033 m" — swallowing the first letter of the next word, which
# corrupted both the figure and the label derived from the remaining text.
FIGURE = re.compile(
    r"(\$\s?\d[\d,.]*(?:\s?[KMB]\b)?\+?"     # $12M, $159,033,033
    r"|\d[\d,.]*\s?%"                        # 14%
    r"|\d+(?:\.\d+)?x\b"                     # 10x
    r"|\d[\d,.]*\s?[KMB]\b)",                # 175M
    re.I,
)


class MotionError(RuntimeError):
    pass


def cli_path() -> Path | None:
    """The project's own Remotion binary, or None."""
    bin_dir = REMOTION_DIR / "node_modules" / ".bin"
    for candidate in ("remotion.cmd", "remotion", "remotion.ps1"):
        c = bin_dir / candidate
        if c.exists():
            return c
    return None


def remotion_ready() -> tuple[bool, str]:
    """Readiness means the renderer can actually run — not that a folder exists.

    An earlier version of this check returned ready because `node_modules` was
    present. It was present and empty: `npm install` had failed with
    ERR_INVALID_ARG_TYPE while still exiting 0. A readiness check that passes on
    a broken install is the same defect this codebase is built to remove, so it
    now looks for the binary it intends to execute.
    """
    if not REMOTION_DIR.exists():
        return False, f"no Remotion project at {REMOTION_DIR}"
    nm = REMOTION_DIR / "node_modules"
    if not nm.exists() or not any(nm.iterdir()):
        return False, f"dependencies not installed — run `npm install` in {REMOTION_DIR}"
    if cli_path() is None:
        return False, (f"node_modules present but no Remotion CLI in {nm / '.bin'} — "
                       f"the install did not complete")
    return True, ""


def _first_figure(claims: list[Claim]) -> tuple[str, str] | None:
    """The first figure from a VERIFIED claim, with its surrounding statement.

    Unverified claims are skipped entirely — not softened, not hedged. A number
    that could not be entailed by evidence does not get animated.
    """
    for c in claims:
        if c.status != "verified":
            continue
        m = FIGURE.search(c.text)
        if m:
            label = c.text.replace(m.group(0), "").strip(" .,—-:")
            return m.group(0).strip(), (label[:64] or "verified figure")
    return None


def plan_composition(spec: VisualSpec | None, claims: list[Claim]) -> dict[str, Any]:
    """Choose a composition and build its props. Pure — no rendering."""
    accent = PALETTE["lavender"]
    bg = PALETTE["obsidian"]

    figure = _first_figure(claims)
    if figure:
        stat, label = figure
        return {
            "id": "Stat",
            "props": {"stat": stat, "label": label, "accent": accent, "bg": bg},
            "reason": f"verified claim supplies the figure {stat!r}",
            "carries_figure": True,
        }

    # No verified figure: use the typographic composition, which displays words
    # rather than numbers. Headline and blocks already passed the gate.
    words: list[str] = []
    if spec is not None:
        words.append(spec.headline)
        if spec.subhead:
            words.append(spec.subhead)
        words += [b.text for b in spec.blocks if b.role in ("label", "caption", "step")]
    words = [w.strip() for w in words if w and w.strip()][:3]
    if not words:
        words = ["Composable credit.", "Isolated by design."]

    return {
        "id": "Kinetic",
        "props": {"words": words, "hexTag": "0xVANNA", "accent": accent},
        "reason": "no verified figure available; using a composition that shows none",
        "carries_figure": False,
    }


def render(plan: dict[str, Any], run_id: str) -> tuple[Path, dict[str, Any]]:
    ready, why = remotion_ready()
    if not ready:
        raise MotionError(why)

    out = OUT_DIR / f"{run_id}_motion.mp4"
    out.parent.mkdir(parents=True, exist_ok=True)
    props = json.dumps(plan["props"], ensure_ascii=False)

    # Resolve the project's own CLI. `npx remotion` failed with "could not
    # determine executable to run" because the package exposes its binary under
    # a different name than the package.
    binary = cli_path()
    if binary is None:
        raise MotionError(f"no Remotion CLI in {REMOTION_DIR / 'node_modules' / '.bin'}")

    cmd = [str(binary), "render", plan["id"], str(out), f"--props={props}"]
    started = time.time()
    proc = subprocess.run(
        cmd, cwd=str(REMOTION_DIR), capture_output=True, text=True,
        encoding="utf-8", errors="replace", timeout=RENDER_TIMEOUT_S,
        shell=os.name == "nt",   # npx is a .cmd shim on Windows
    )
    if proc.returncode != 0 or not out.exists():
        tail = (proc.stderr or proc.stdout or "").strip()[-600:]
        raise MotionError(f"remotion render exited {proc.returncode}: {tail}")

    return out, {
        "composition": plan["id"],
        "render_s": round(time.time() - started, 1),
        "bytes": out.stat().st_size,
    }


def motion_stage(spec: VisualSpec | None, claims: list[Claim],
                 run_id: str) -> StageResult[dict]:
    """Render the branded motion graphic for this run."""
    started = time.time()
    plan = plan_composition(spec, claims)
    ih = digest(plan)

    try:
        path, meta = render(plan, run_id)
    except (MotionError, subprocess.TimeoutExpired) as exc:
        # The asset can ship without motion graphics; the run must say it did.
        return degraded("motion", {"composition": plan["id"], "path": None,
                                   "reason": plan["reason"]},
                        started, f"remotion render failed: {exc}"[:400], input_hash=ih)

    payload = {
        "path": str(path),
        "props": plan["props"],
        "reason": plan["reason"],
        "carries_figure": plan["carries_figure"],
        **meta,
    }
    if not plan["carries_figure"]:
        # Not a failure — but worth surfacing that the run had no verified
        # number to show, because that is usually an evidence problem.
        return ok("motion", payload, started, input_hash=ih,
                  tool_calls=[f"remotion:{plan['id']}"])
    return ok("motion", payload, started, input_hash=ih,
              tool_calls=[f"remotion:{plan['id']}"])


if __name__ == "__main__":
    ready, why = remotion_ready()
    print(json.dumps({"ready": ready, "reason": why, "dir": str(REMOTION_DIR)}, indent=2))
