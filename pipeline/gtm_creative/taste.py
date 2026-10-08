"""The founder's taste in posters: what was approved, what was killed.

The Motion Director was shown only the posters the founder approved, and the
poster judge checked only for mistakes (spelling, logo, invented figures), so
nothing told either of them what the founder sends back. Four posters the
judge passed as SHIP were killed or revised. This module gives both of them
the two piles — the posters themselves, from the feedback ledger — and the
written taste in `brain/knowledge/poster-taste.md`.
"""
from __future__ import annotations

import hashlib
import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path

PIPELINE = Path(__file__).resolve().parents[1]
TASTE_FILE = PIPELINE / "brain" / "knowledge" / "poster-taste.md"
LEDGER = PIPELINE / "state" / "feedback.jsonl"
RUNS = PIPELINE / "state" / "gtm_runs"
# Beside the approved exemplars, so the folder sync carries them to the cloud
# job, but in their own index: the brain indexes every row of exemplars.jsonl
# as an approved poster.
EX_DIR = PIPELINE / "brain" / "visual_exemplars"
SENT_BACK = EX_DIR / "sent_back.jsonl"

# Words that made headlines read as an engineering spec on the killed
# posters. Matched as whole words, case-insensitive.
JARGON = ("monolithic", "mutualized", "mutualised", "socialized", "socialised",
          "blockspace", "deterministic", "primitives", "segregated", "unified margin")
# Promises a testnet protocol cannot keep, from the founder's never-make posters
# ("eliminate contagion and transaction failure", "Bank-grade assets cannot touch").
OVERCLAIM = ("eliminate", "eliminates", "eliminated", "guarantee", "guaranteed",
             "guarantees", "bank-grade", "risk-free", "zero risk", "stay safe",
             "never fails", "impossible", "never")


def rubric() -> str:
    try:
        return TASTE_FILE.read_text(encoding="utf-8").strip()
    except FileNotFoundError:
        return ""


def _words(text: str, words: tuple[str, ...]) -> list[str]:
    t = str(text or "").lower()
    return [w for w in words if re.search(r"\b" + re.escape(w) + r"\b", t)]


def jargon(text: str) -> list[str]:
    return _words(text, JARGON)


def overclaims(text: str) -> list[str]:
    return _words(text, OVERCLAIM)


def _latest() -> dict[str, str]:
    """Each run's latest founder decision; a later approve overrides a kill."""
    out: dict[str, str] = {}
    try:
        from pipeline.gtm_learning.feedback import ledger_path
        lines = ledger_path().read_text(encoding="utf-8").splitlines()
    except FileNotFoundError:
        return out
    for line in lines:
        try:
            r = json.loads(line)
        except ValueError:
            continue
        if r.get("run_id") and r.get("verdict"):
            out[r["run_id"]] = str(r["verdict"]).lower()
    return out


def remember_sent_back(image: str | Path, *, run_id: str, verdict: str,
                       brief: str = "", note: str = "", founder_ref: bool = False) -> bool:
    """Keep a poster the founder killed or sent back, for the judge and the director.

    `founder_ref` marks a poster the founder handed over as "never make this";
    those are always shown first, ahead of killed run posters.
    """
    src = Path(image)
    if not src.exists():
        return False
    digest = hashlib.sha1(src.read_bytes()).hexdigest()[:12]
    EX_DIR.mkdir(parents=True, exist_ok=True)
    dest = EX_DIR / ("sent_back_" + digest + src.suffix.lower())
    if not dest.exists():
        shutil.copyfile(src, dest)
    rows = [r for r in _sent_back_rows() if r.get("run_id") != run_id]
    rows.append({"run_id": run_id, "verdict": verdict, "file": dest.name,
                 "brief": " ".join(str(brief).split())[:500],
                 "note": " ".join(str(note or "").split())[:400] or None,
                 **({"founder_ref": True} if founder_ref else {}),
                 "at": datetime.now(timezone.utc).isoformat()})
    SENT_BACK.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n",
                         encoding="utf-8")
    return True


def _sent_back_rows() -> list[dict]:
    try:
        return [json.loads(l) for l in SENT_BACK.read_text(encoding="utf-8").splitlines()
                if l.strip()]
    except FileNotFoundError:
        return []


def piles(approved: int = 2, sent_back: int = 3) -> dict[str, list[dict]]:
    """The newest decided posters still on disk: {"approved": [...], "sent_back": [...]}.

    Each item is {"run_id", "verdict", "path", "brief"}. Sent-back posters come
    from the kept copies first (they exist on the cloud job too), then from
    run folders on this machine. A poster the founder later approved is not
    in the sent-back pile.
    """
    latest = _latest()
    out: dict[str, list[dict]] = {"approved": [], "sent_back": []}
    seen: set[str] = set()
    rows = sorted(_sent_back_rows(), key=lambda r: r.get("run_id", ""), reverse=True)
    for r in sorted(rows, key=lambda r: not r.get("founder_ref")):
        p = EX_DIR / str(r.get("file"))
        if (len(out["sent_back"]) >= sent_back or not p.exists()
                or latest.get(r.get("run_id"), r.get("verdict")) not in ("kill", "revise")):
            continue
        brief = r.get("brief") or ""
        if r.get("note"):
            brief += " — founder: " + r["note"]
        out["sent_back"].append({"run_id": r["run_id"], "verdict": r.get("verdict"),
                                 "path": p, "brief": brief})
        seen.add(r["run_id"])
    for run_id, verdict in sorted(latest.items(), reverse=True):
        if run_id in seen:
            continue
        pile = ("approved" if verdict in ("approve", "edit") else
                "sent_back" if verdict in ("kill", "revise") else None)
        if pile is None or len(out[pile]) >= (approved if pile == "approved" else sent_back):
            continue
        try:
            s = json.loads((RUNS / run_id / "summary.json").read_text(encoding="utf-8"))
        except Exception:                           # noqa: BLE001 — not on this machine
            continue
        p = Path(str(s.get("visual_path") or ""))
        if not s.get("visual_path") or not p.exists():
            continue
        out[pile].append({"run_id": run_id, "verdict": verdict, "path": p,
                          "brief": " ".join(str(s.get("poster_brief") or "").split())[:500]})
    return out
