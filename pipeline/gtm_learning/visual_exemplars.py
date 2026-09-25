"""Founder-approved visuals — what the visual agent learns to make.

The run ledger (`feedback.py`) rewards whole runs. Visuals made outside a run
— the reference posters, the direct-model posters — had nowhere to go, and
they are exactly the ones the founder judged: on 2026-09-25 the four posters
the image model made directly from the references were "bahut behtar", and
the code-set ones were liked but less.

Two things are learned from that here:

  **Exemplars.** Approved images are copied into the Brain DB with a score
  and the founder's note. The direct image agent shows the best of them to
  the model first, ahead of the design references, as "this is the level the
  founder approved" — so what the founder liked becomes what the agent
  reaches for, without anyone writing it into code.

  **Renderer preference.** Each exemplar is also a vote for the way it was
  made (`direct_model` or `code_set`). A Beta posterior per renderer, fed by
  exemplar scores and by run feedback that carries `visual_renderer`, decides
  by Thompson sampling which renderer a run uses. A clear winner is used most
  of the time; the other still gets tried, so the preference can change.

    python -m pipeline.gtm_learning.visual_exemplars add IMAGE --renderer direct_model --score 1.0 --note "..."
    python -m pipeline.gtm_learning.visual_exemplars list
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

REPO = Path(__file__).resolve().parents[2]
EX_DIR = REPO / "pipeline" / "brain" / "visual_exemplars"
INDEX = EX_DIR / "exemplars.jsonl"
RENDERERS = ("direct_model", "code_set")


def _rows() -> list[dict]:
    try:
        return [json.loads(l) for l in INDEX.read_text(encoding="utf-8").splitlines()
                if l.strip()]
    except FileNotFoundError:
        return []


def add(image: str | Path, *, renderer: str, score: float, note: str = "",
        brief: str = "", source: str = "founder") -> dict[str, Any]:
    """Store an approved visual. `score` is the founder's reward in [0, 1]."""
    if renderer not in RENDERERS:
        raise ValueError("renderer must be one of " + ", ".join(RENDERERS))
    src = Path(image)
    data = src.read_bytes()
    digest = hashlib.sha1(data).hexdigest()[:12]
    EX_DIR.mkdir(parents=True, exist_ok=True)
    dest = EX_DIR / (digest + src.suffix.lower())
    if not dest.exists():
        shutil.copyfile(src, dest)
    prior = next((r for r in _rows() if r.get("id") == digest), {})
    rows = [r for r in _rows() if r.get("id") != digest]      # re-rating replaces
    # A re-rating adds to the note instead of replacing it: the founder's own
    # words on a benchmark are what the agents learn from, and a later note
    # (the Coach's, or a one-line approval) must not wipe them out.
    new_note = " ".join(str(note).split())
    old_note = str(prior.get("note") or "")
    if old_note and new_note and new_note not in old_note:
        new_note = old_note + " | " + new_note
    elif old_note and not new_note:
        new_note = old_note
    row = {"id": digest, "file": dest.name, "renderer": renderer,
           "score": max(0.0, min(1.0, float(score))),
           "note": new_note[:900] or None,
           "brief": " ".join(str(brief).split())[:600] or prior.get("brief") or None,
           "source": source, "from": str(src.name),
           "at": datetime.now(timezone.utc).isoformat()}
    rows.append(row)
    tmp = INDEX.with_suffix(".tmp")
    tmp.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n",
                   encoding="utf-8")
    tmp.replace(INDEX)
    # Into the brand brain's visual memory, where the image agent looks.
    try:
        from pipeline.brand_brain.onboard import remember_image
        remember_image(dest, kind="approved_poster", score=row["score"], note=row["note"] or "")
    except Exception:                               # noqa: BLE001 — boundary
        pass
    return row


def top(k: int = 3, *, renderer: Optional[str] = None,
        min_score: float = 0.7) -> list[Path]:
    """The best-rated exemplars, as image paths, newest first on a tie."""
    rows = [r for r in _rows()
            if r.get("score", 0) >= min_score
            and (renderer is None or r.get("renderer") == renderer)
            and (EX_DIR / r["file"]).exists()]
    rows.sort(key=lambda r: (r.get("score", 0), r.get("at", "")), reverse=True)
    return [EX_DIR / r["file"] for r in rows[:k]]


def renderer_posteriors() -> dict[str, dict[str, float]]:
    """Beta per renderer from exemplar scores and run feedback."""
    post = {r: {"alpha": 1.0, "beta": 1.0, "n": 0} for r in RENDERERS}
    for r in _rows():
        p = post.get(r.get("renderer"))
        if p is None:
            continue
        s = float(r.get("score", 0.0))
        p["alpha"] += s
        p["beta"] += 1.0 - s
        p["n"] += 1
    try:
        from pipeline.gtm_learning.preferences import latest_per_run
        for r in latest_per_run():
            p = post.get((r.get("features") or {}).get("visual_renderer"))
            if p is None:
                continue
            s = float(r.get("reward", 0.0))
            p["alpha"] += s
            p["beta"] += 1.0 - s
            p["n"] += 1
    except Exception:                               # noqa: BLE001 — boundary
        pass
    for p in post.values():
        p["mean"] = round(p["alpha"] / (p["alpha"] + p["beta"]), 3)
    return post


def preferred_renderer(rng: Optional[random.Random] = None) -> str:
    """One Thompson draw per renderer; the higher draw is used this run."""
    rng = rng or random.Random()
    post = renderer_posteriors()
    draws = {k: rng.betavariate(p["alpha"], p["beta"]) for k, p in post.items()}
    return max(draws, key=draws.get)


def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Founder-approved visual exemplars.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("add")
    a.add_argument("image")
    a.add_argument("--renderer", required=True, choices=RENDERERS)
    a.add_argument("--score", type=float, required=True)
    a.add_argument("--note", default="")
    a.add_argument("--brief", default="")
    sub.add_parser("list")
    args = ap.parse_args(argv)
    if args.cmd == "add":
        print(json.dumps(add(args.image, renderer=args.renderer, score=args.score,
                             note=args.note, brief=args.brief), ensure_ascii=False))
    else:
        print(json.dumps({"exemplars": _rows(), "renderers": renderer_posteriors()},
                         indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
