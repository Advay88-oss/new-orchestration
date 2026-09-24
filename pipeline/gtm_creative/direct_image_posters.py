"""Posters made by the image model directly, from the references it can see.

The code-set posters (`reference_posters.py`) reproduce the founder's house
style by describing it in Python: every bloom, card and gradient is code, so
a new style means new code. This is the other approach: the image model is
shown the reference PNGs and the real logo, told what the post is about, and
returns the finished poster itself.

What the model cannot be trusted with — spelling, invented figures, the logo
— is checked afterwards by a vision judge that looks at the output. A REJECT
is fed back as a correction and the poster is made once more.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

REPO = Path(__file__).resolve().parents[2]
REF_DIR = REPO / "design references"
LOGO = REPO / "pipeline" / "state" / "logo.png"
OUT_DIR = REPO / "pipeline" / "state" / "direct_posters"
MODEL = "gemini-3-pro-image"

FACTS = """VANNA — the only facts you may use:
- Vanna is composable credit / unified margin infrastructure, live on Stellar Soroban TESTNET (not mainnet).
- Each user gets a SmartAccount: an isolated margin-account contract. Risk stays inside that account; it is not pooled with other users.
- Users borrow credit against collateral and deploy it across venues (Blend lending, Aquarius and Soroswap AMMs on Stellar).
- Health-factor liquidation floor: 1.10x. Fixed gas: 0.00014 XLM. Indexing latency: ~320ms.
- Never state any other number: no user counts, no TVL, no APY, no percentages, no price."""


def references() -> list[Path]:
    refs = sorted(REF_DIR.glob("cl-*.png"))
    extra = REF_DIR / "image.png"
    return refs + ([extra] if extra.exists() else [])


def _prompt(brief: str, correction: str = "") -> str:
    return (
        "You are designing ONE finished square (1:1) image for an X post by "
        "Vanna Finance.\n\n"
        "ATTACHED IMAGES: all images except the last are STYLE REFERENCES. "
        "The LAST image is the official Vanna logo.\n\n"
        "Match the references' house style exactly: very dark ground with a "
        "soft violet glow low-left and a magenta glow high-right; the logo "
        "centred at the top; a heavy bold sans-serif headline, centred, with "
        "ONE key word or short phrase in a pink-to-violet gradient italic; "
        "one short grey subtitle line; a clean centrepiece made of UI "
        "elements (glass cards, chips, rows with checkmarks, pills, arrows, "
        "stat tiles or a simple diagram) that explains the idea; and a footer "
        "line at the bottom: a few bold white words then a short grey "
        "caveat that says testnet. Generous spacing, nothing overlapping, "
        "everything aligned.\n\n"
        "LOGO: use the logo from the LAST attached image, exactly as it is — "
        "same mark, same wordmark 'vanna', same colours. Do NOT use the cube "
        "icon that appears in the style references; that is an old logo.\n\n"
        "TEXT RULES: every word must be spelled correctly. Keep all text "
        "short — headline under 9 words, subtitle under 14, labels 1-4 "
        "words. Use no text other than what explains the idea. " + FACTS
        + "\n\nTHE POST THIS IMAGE IS FOR:\n" + " ".join(brief.split())
        + ("\n\nFIX FROM THE PREVIOUS ATTEMPT (it was rejected): " + correction
           if correction else "")
    )


JUDGE_SYSTEM = (
    "You review a finished social image for Vanna Finance before a human "
    "sees it. Be strict and specific. Return strict JSON."
)

JUDGE_SCHEMA = (
    '{"spelling_errors": [str], "invented_figures": [str], '
    '"logo_correct": bool, "overlapping_or_clipped": [str], '
    '"matches_brief": bool, "matches_reference_style": bool, '
    '"verdict": "SHIP"|"REVISE"|"REJECT", "fix": str}'
)


def judge(image: Path, brief: str) -> dict[str, Any]:
    from pipeline.gtm_os import agent_runtime as R

    prompt = (
        "The FIRST image is the poster to review. The SECOND is the official "
        "Vanna logo.\n\n" + FACTS + "\n\nThe brief was:\n" + brief + "\n\n"
        "Check: every word spelled correctly and not garbled; no figure that "
        "is not in the facts list; the logo matches the official one (not a "
        "cube); nothing overlaps or is cut off; the image is about the brief. "
        "REJECT on any spelling error, invented figure, wrong logo or "
        "overlap. `fix` says exactly what to change, in one or two "
        "sentences.\n\nReturn JSON exactly:\n" + JUDGE_SCHEMA
    )
    return R.brain_vision(prompt, [image, LOGO], agent="A07_creative_director",
                          system=JUDGE_SYSTEM, role="reasoning",
                          temperature=0.1, max_output_tokens=2048)


def make(brief: str, name: str, *, out_dir: Optional[Path] = None,
         attempts: int = 2, extra_refs: Optional[list] = None) -> dict[str, Any]:
    from pipeline.scripts.gemini_flash_image import generate_gemini_image

    out_dir = Path(out_dir or OUT_DIR)
    out_dir.mkdir(parents=True, exist_ok=True)
    # The logo goes last: the prompt tells the model the LAST image is it.
    imgs = references() + [Path(p) for p in (extra_refs or []) if Path(p).exists()] + [LOGO]
    history = []
    correction = ""
    for n in range(1, attempts + 1):
        path = out_dir / f"{name}_try{n}.png"
        generate_gemini_image(prompt=_prompt(brief, correction), output_path=path,
                              model=MODEL, temperature=0.7, images=imgs,
                              aspect_ratio="1:1")
        try:
            v = judge(path, brief)
        except Exception as exc:                    # noqa: BLE001 — boundary
            v = {"verdict": "UNJUDGED", "fix": str(exc)[:200]}
        history.append({"path": str(path), **v})
        if str(v.get("verdict")).upper() == "SHIP":
            break
        correction = str(v.get("fix") or "")
    best = next((h for h in history if str(h.get("verdict")).upper() == "SHIP"),
                history[-1])
    final = out_dir / f"{name}.png"
    final.write_bytes(Path(best["path"]).read_bytes())
    return {"name": name, "final": str(final), "attempts": history}
