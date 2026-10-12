"""Campaign art: the team's own campaign image (a Galxe cover, thumbnail or banner), made better.

  Director (A07, sees the image) keeps every word and number the team wrote and writes design moves
    for the platform it is for (a Galxe quest page: gamified, reward-forward) without adding text.
  Poster (A08, Nano Banana 2.1) redraws the image from it at the target shape.
  Judge (A08's own) checks the moves landed and nothing overlaps; a transcription diff checks that
    no word or number changed (the image model redraws every word and slips a digit unseen).

    python -m pipeline.gtm_creative.campaign_art SRC --kind cover|thumbnail|banner --out DIR
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Optional

from PIL import Image

from pipeline.gtm_creative import format_poster as FP

# Target shape per kind, and the model aspect to draw it at (cropped to the target afterwards).
KINDS = {
    "cover": ((2000, 1050), ["16:9"]),
    "thumbnail": ((2000, 2000), ["1:1"]),
    "banner": ((2000, 500), ["4:1", "21:9"]),
}


def _fit(path: Path, size: tuple[int, int]) -> None:
    """Centre-crop to the target ratio, then resize to the target size."""
    im = Image.open(path).convert("RGB")
    tw, th = size
    r = tw / th
    if im.width / im.height > r:
        w = int(im.height * r)
        im = im.crop(((im.width - w) // 2, 0, (im.width - w) // 2 + w, im.height))
    else:
        h = int(im.width / r)
        im = im.crop((0, (im.height - h) // 2, im.width, (im.height - h) // 2 + h))
    im.resize(size, Image.LANCZOS).save(path)


def make(src: Path, kind: str, *, name: str, out_dir: Path, platform: str = "Galxe quest page",
         notes: str = "", look: str = "", run_id: Optional[str] = None) -> dict[str, Any]:
    from pipeline.brand_brain import context as C
    from pipeline.gtm_os import agent_runtime as R
    from pipeline.scripts import claim_safety_gate as G
    from pipeline.scripts.gemini_flash_image import generate_gemini_image
    size, aspects = KINDS[kind]
    src, out_dir = Path(src), Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    system = C.fill("You are {company}'s Motion/Art Director. You make the team's campaign image better "
                    "for where it will appear, keeping every word it says. Return strict JSON only.")
    prompt = (
        C.facts_block("Galxe quest waitlist lucky draw referral race USDC", k=4, excerpts=2) + "\n\n----\n\n"
        "THE IMAGE (attached) is the team's " + kind + " for the " + platform + ", final size "
        + str(size[0]) + "x" + str(size[1]) + ". Its words and numbers are decided: keep every one exactly, "
        "add none (no new labels, taglines or badges with words). " + (("THE TEAM'S NOTES: " + notes + " ")
                                                                      if notes else "")
        + "Make it a better " + kind + ": it should feel like a quest/reward campaign on " + platform + " "
        "(gamified, reward-forward, premium) while staying Vanna's brand (near-black ground, violet-to-magenta "
        "gradient, teal and pink accents, Plus Jakarta Sans, the real logo top-left). Give at least THREE "
        "visible design moves, " + (("in THIS LOOK (it overrides everything else about finish): " + look + " ")
                                    if look else
        "for example: the prize as a glowing object (a coin stack or a vault of USDC "
        "coins with depth and light) instead of flat icons; the leaderboard as a lit 3D podium; cards with lit "
        "gradient borders and depth; an atmosphere (soft light rays, a faint grid or particles) behind; a "
        "stronger, larger call-to-action. ") + "Nothing may overlap text, nothing cut off, empty areas used, and at "
        + ("this small size every word must stay large and legible. " if kind != "cover" else "a glance the "
           "prize and the action must read first. ")
        + "List every string on the image, top to bottom, exactly as it is now.\n"
        'Return JSON: {"strings": [str], "design_moves": [str], "composition": str, "keep_out": [str]}')
    d = R.brain_vision(prompt, [src], agent=FP.AGENT_DIRECTOR, system=system, role="director",
                       temperature=0.4, max_output_tokens=4096, run_id=run_id)
    strings = [str(s) for s in d.get("strings") or []]
    g = G.check(" \n".join(strings), platform="x", require_testnet=False)
    R.record_decision(FP.AGENT_DIRECTOR, "campaign_art", {"brief": d, "from": str(src), "gate": g["pass"]},
                      run_id=run_id)
    before = FP._words(src)
    history, correction = [], ""
    for k in range(1, 4):
        path = out_dir / f"{name}_try{k}.png"
        p = ("You are Vanna's visual agent. Redraw the attached campaign image as a better " + kind + " for the "
             + platform + ". Arrange it like this: " + str(d.get("composition") or "") + "\nDESIGN MOVES (all "
             "visible):\n" + "\n".join("  - " + str(m) for m in d.get("design_moves") or [])
             + "\nTEXT (exactly these strings and no others, letter for letter, every digit as given):\n"
             + "\n".join("  " + s for s in strings)
             + "\nNo element overlaps any text; nothing cut off by the edge; keep a safe margin of 6% on every "
               "side. The Vanna logo stays top-left as in the attached image."
             + ("\n\nFIX THESE PROBLEMS FROM THE LAST ATTEMPT:\n" + correction if correction else ""))
        last: Optional[Exception] = None
        for asp in aspects:
            try:
                generate_gemini_image(prompt=p, output_path=path, model=R.MODELS["poster"], temperature=0.5,
                                      images=[src], aspect_ratio=asp,
                                      image_size=os.environ.get("VANNA_POSTER_SIZE", "4K"))
                last = None
                break
            except Exception as exc:                # noqa: BLE001 — an unsupported shape: the next one
                last = exc
        if last:
            raise last
        _fit(path, size)
        if kind != "banner":                        # the real logo, from the team's image (same size now);
            FP.paste_logo(path, src)                # the banner's logo sits too close to the top to find
        try:
            v = R.brain_vision(
                "Image 1 is the team's campaign image; image 2 is the redrawn one. Check: (a) these design moves "
                "are visible: " + " | ".join(str(m) for m in d.get("design_moves") or []) + "; (b) every one of "
                "these strings appears exactly: " + " | ".join(strings) + "; (c) no element overlaps text, "
                "nothing is cut off by the edge, every word legible; (d) the logo appears once, top-left; (e) it "
                "is visibly better, not a copy. Return JSON: {\"score\": int (0-10), \"differences\": [str] "
                "(each a concrete fix), \"verdict\": \"SHIP\"|\"REVISE\"|\"REJECT\"}",
                [src, path], agent=FP.AGENT_POSTER, role="reasoning", temperature=0.0, max_output_tokens=2048,
                system="You are the visual agent's judge. Be exact and brief.")
        except Exception as exc:                    # noqa: BLE001 — an unjudged image does not ship
            v = {"score": 0, "differences": ["judge failed: " + str(exc)[:120]], "verdict": "UNJUDGED"}
        after = FP._words(path)
        slips, lost = sorted(after - before), sorted(before - after)
        if slips:
            v["verdict"], v["score"] = "REVISE", min(int(v.get("score") or 0), 5)
            v.setdefault("differences", []).insert(
                0, "Text that is not on the team's image: " + ", ".join(repr(s) for s in slips[:10])
                + (" — it reads: " + ", ".join(repr(s) for s in lost[:10]) if lost else "")
                + ". Copy every string letter for letter.")
        v["slips"], v["lost"] = slips, lost
        history.append({"path": str(path), **v})
        if not slips and (str(v.get("verdict")).upper() == "SHIP" or int(v.get("score") or 0) >= 9):
            break
        correction = "\n".join("- " + str(x) for x in (v.get("differences") or [])[:8])
    best = max(history, key=lambda h: (not h.get("slips"), str(h.get("verdict")).upper() == "SHIP",
                                       int(h.get("score") or 0)))
    final = out_dir / f"{name}.png"
    final.write_bytes(Path(best["path"]).read_bytes())
    (out_dir / (name + ".json")).write_text(json.dumps(
        {"from": str(src), "kind": kind, "brief": d, "gate": g["pass"],
         "attempts": [{k2: h.get(k2) for k2 in ("path", "score", "verdict", "differences", "slips", "lost")}
                      for h in history]}, ensure_ascii=False, indent=1), encoding="utf-8")
    return {"name": name, "final": str(final), "attempts": history, "director": d}


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("--kind", choices=list(KINDS), required=True)
    ap.add_argument("--name", default="")
    ap.add_argument("--out", required=True)
    ap.add_argument("--notes", default="")
    ap.add_argument("--look", default="")
    a = ap.parse_args()
    r = make(Path(a.src), a.kind, name=a.name or a.kind, out_dir=Path(a.out), notes=a.notes, look=a.look)
    print(json.dumps({"final": r["final"], "attempts": [(h.get("verdict"), h.get("score"), h.get("slips"))
                                                         for h in r["attempts"]],
                      "moves": r["director"].get("design_moves")}, ensure_ascii=False))
