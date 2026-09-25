"""The creative rulebook, and the rules the Coach learns — with their record.

`creative-rules.md` holds the founder's rules. The Coach (A13) adds rules it
derives from runs, and those are LEARNED in the reinforcement sense, not just
written down: every learned rule carries a Beta posterior over "runs made
while this rule was active came out well". After each run the active rules
are credited with that run's reward (the judges' verdicts, and later the
founder's decision, which counts double); a rule that keeps coinciding with
bad outcomes is retired, and the Coach is shown which of its rules worked and
which were retired, so it builds on its own record instead of starting over.

State lives in `learned-rules.json`. `learned-rules.md` is the readable
mirror; deleting a line from it retires that rule — the founder's veto.
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

KNOWLEDGE = Path(__file__).resolve().parents[1] / "brain" / "knowledge"
RULES = KNOWLEDGE / "creative-rules.md"
LEARNED_MD = KNOWLEDGE / "learned-rules.md"
LEARNED_JSON = KNOWLEDGE / "learned-rules.json"
MAX_ACTIVE = 40
RETIRE_MIN_N = 4
RETIRE_BELOW = 0.3

_HEADER = (
    "# Learned creative rules\n\n"
    "Written by the Coach (A13) from what it saw in runs, each with its record: "
    "how the runs made while it was active came out. Rules that keep coinciding "
    "with bad outcomes are retired automatically. DELETE a line here to retire "
    "that rule yourself. State: `learned-rules.json`.\n\n"
)


def founder_rules() -> str:
    try:
        return RULES.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load() -> list[dict]:
    try:
        rules = json.loads(LEARNED_JSON.read_text(encoding="utf-8"))
    except Exception:                               # noqa: BLE001 — first run
        rules = []
    # The founder's veto: a rule whose line was deleted from the .md retires.
    try:
        md = LEARNED_MD.read_text(encoding="utf-8")
        for r in rules:
            if r["status"] == "active" and "[" + r["id"] + "]" not in md:
                r["status"], r["retired_why"] = "retired", "removed by the founder"
    except FileNotFoundError:
        pass
    return rules


def _save(rules: list[dict]) -> None:
    KNOWLEDGE.mkdir(parents=True, exist_ok=True)
    LEARNED_JSON.write_text(json.dumps(rules, indent=1, ensure_ascii=False), encoding="utf-8")
    active = [r for r in rules if r["status"] == "active"]
    LEARNED_MD.write_text(_HEADER + "\n".join(
        "- " + r["text"] + " — " + _record(r) + " [" + r["id"] + "]" for r in active) + "\n",
        encoding="utf-8")


def _mean(r: dict) -> float:
    return r["alpha"] / (r["alpha"] + r["beta"])


def _record(r: dict) -> str:
    return ("untested" if not r["n"] else
            "good in " + str(round(r["alpha"] - 1, 1)) + " of " + str(r["n"]) + " runs")


def learned_rules() -> list[str]:
    """Active learned rules, best-proven first, as prompt lines."""
    act = sorted((r for r in _load() if r["status"] == "active"),
                 key=lambda r: (-_mean(r), r["at"]))
    return [r["text"] for r in act]


def block(*, max_chars: int = 5000) -> str:
    """Both rulebooks as prompt text: the founder's first, then the learned."""
    learned = learned_rules()
    text = founder_rules()
    if learned:
        text += "\n\n## Learned from past runs (Coach)\n" + "\n".join("- " + r for r in learned)
    return text[:max_chars]


def coach_record() -> str:
    """The Coach's own track record — what it should build on and not repeat."""
    rules = _load()
    if not rules:
        return ""
    act = sorted((r for r in rules if r["status"] == "active"), key=lambda r: -_mean(r))
    ret = [r for r in rules if r["status"] == "retired"][-10:]
    lines = ["YOUR OWN RECORD AS COACH — build on it:"]
    if act:
        lines.append("Your active rules and how runs went while they applied:")
        lines += ["  - " + r["text"] + " (" + _record(r) + ")" for r in act[:15]]
    if ret:
        lines.append("Rules you tried that were RETIRED — do not propose them again:")
        lines += ["  - " + r["text"] + " (" + r.get("retired_why", "") + ")" for r in ret]
    return "\n".join(lines)


def _key(rule: str) -> set[str]:
    return {w for w in re.findall(r"[a-z]{4,}", rule.lower())}


def add_learned(rule: str, *, source: str) -> bool:
    """Add a rule unless one very like it exists — active, retired or founder's."""
    rule = " ".join(str(rule).split()).strip(" -")
    if len(rule) < 20:
        return False
    rules = _load()
    k = _key(rule)
    for existing in [r["text"] for r in rules] + founder_rules().splitlines():
        e = _key(existing)
        if e and len(k & e) / max(1, len(k | e)) > 0.55:
            return False
    rid = "r" + str(1 + max([int(r["id"][1:]) for r in rules] or [0]))
    rules.append({"id": rid, "text": rule, "source": source, "at": _now(),
                  "alpha": 1.0, "beta": 1.0, "n": 0, "status": "active"})
    active = [r for r in rules if r["status"] == "active"]
    if len(active) > MAX_ACTIVE:                    # the weakest active rule makes room
        worst = min(active, key=_mean)
        worst["status"], worst["retired_why"] = "retired", "made room for a newer rule"
    _save(rules)
    return True


def credit(reward: float, *, since: Optional[str] = None, weight: float = 1.0,
           run_id: str = "") -> dict[str, int]:
    """Credit every rule that was active for a run with that run's reward.

    `since` is the run's start: rules added after it did not shape it. The
    founder's decision on a run arrives later and is credited again, weighted.
    """
    rules = _load()
    reward = max(0.0, min(1.0, float(reward)))
    credited = retired = 0
    for r in rules:
        if r["status"] != "active" or (since and r["at"] > since):
            continue
        r["alpha"] += reward * weight
        r["beta"] += (1.0 - reward) * weight
        r["n"] += 1
        credited += 1
        if r["n"] >= RETIRE_MIN_N and _mean(r) < RETIRE_BELOW:
            r["status"] = "retired"
            r["retired_why"] = ("runs kept coming out badly while it applied ("
                                + _record(r) + ")")
            retired += 1
    if credited:
        _save(rules)
    return {"credited": credited, "retired": retired}


def run_reward(summary: dict) -> Optional[float]:
    """A run's reward from its judges: SHIP 1, REVISE 0.5, REJECT 0, averaged."""
    score = {"SHIP": 1.0, "REVISE": 0.5, "REJECT": 0.0}
    vals = []
    for k in ("visual_review", "video_review"):
        v = str((summary.get(k) or {}).get("verdict") or "").upper()
        if v in score:
            vals.append(score[v])
    v = str(summary.get("creative_verdict") or "").upper()
    if v in score:
        vals.append(score[v])
    return sum(vals) / len(vals) if vals else None
