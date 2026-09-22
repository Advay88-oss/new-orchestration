"""Evaluator-guided visual optimisation.

    render -> critique -> revise -> re-render -> re-critique -> accept/stop

The old pipeline had no loop at all: every `for attempt in range(...)` in the
visual path was an HTTP retry, and the first render was accepted unconditionally
— including one the system's own novelty detector had flagged `STRUCTURAL CLONE`
with novelty 0.0 and a composite score of -38.6.

This is **evaluator-guided iterative generation**, not reinforcement learning.
No reward model is trained and no policy is updated; a critic proposes defects
and a reviser edits a structured spec. Naming it RL would be the same category
of overclaim this whole rebuild exists to remove.

Two stopping rules, both required:
  * a hard round cap — without one, a critic and reviser holding different
    assumptions will burn budget until it runs out;
  * convergence — if a round does not reduce high-severity defects, stop and
    keep the best render rather than churning.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path

from .contracts import Critique, StageResult, VisualSpec, degraded, digest, ok
from .critic import critique_image, revise_spec
from .llm import LLMClient
from .render import OUT_DIR, RenderError, render_png

MAX_ROUNDS = 2


@dataclass
class Round:
    index: int
    spec: VisualSpec
    png: Path | None
    critique: Critique | None
    note: str = ""

    @property
    def high(self) -> int:
        return len(self.critique.high_severity) if self.critique else 99

    @property
    def total(self) -> int:
        return len(self.critique.defects) if self.critique else 99


@dataclass
class VisualOutcome:
    best: Round
    rounds: list[Round] = field(default_factory=list)
    stopped_because: str = ""

    @property
    def accepted(self) -> bool:
        return bool(self.best.critique and not self.best.critique.high_severity)


def _score(r: Round) -> tuple[int, int]:
    """Lower is better: high-severity first, then total defects."""
    return (r.high, r.total)


def optimize_visual(spec: VisualSpec, run_id: str, client: LLMClient, *,
                    max_rounds: int = MAX_ROUNDS,
                    texture_data_uri: str | None = None) -> StageResult[dict]:
    """Render and improve until the critic has no high-severity defects."""
    started = time.time()
    ih = digest(spec.model_dump())
    rounds: list[Round] = []
    current = spec
    stopped = "cap reached"

    # The critic's model calls happen inside this loop. Attribute them to this
    # stage, otherwise the dashboard reports an AGENT that never called a model
    # when in fact it made several.
    used_model: str | None = None
    in_tok = out_tok = 0
    cost = 0.0
    cost_known = True
    calls = 0

    for i in range(max_rounds + 1):
        png = OUT_DIR / f"{run_id}_r{i}.png"
        try:
            render_png(current, png, texture_data_uri=texture_data_uri)
        except RenderError as exc:
            rounds.append(Round(i, current, None, None, f"render failed: {exc}"))
            stopped = f"render failed at round {i}"
            break

        cres = critique_image(png, current, client)
        if cres.model:
            used_model = cres.model
            in_tok += cres.input_tokens
            out_tok += cres.output_tokens
            cost += cres.cost_usd
            cost_known = cost_known and cres.cost_known
            calls += 1
        crit = cres.value if cres.status == "ok" else None
        rnd = Round(i, current, png, crit,
                    "" if crit else (cres.degraded_reason or "critic unavailable"))
        rounds.append(rnd)

        if crit is None:
            stopped = "critic unavailable"
            break
        if not crit.high_severity:
            stopped = "accepted: no high-severity defects"
            break
        if i == max_rounds:
            stopped = f"round cap ({max_rounds}) reached with {rnd.high} high-severity defects"
            break

        revised = revise_spec(current, crit, client)
        if revised is None:
            stopped = "reviser could not produce a valid spec"
            break
        if revised.model_dump() == current.model_dump():
            stopped = "converged: reviser returned an unchanged spec"
            break
        current = revised

    rendered = [r for r in rounds if r.png is not None]
    if not rendered:
        return degraded("visual", None, started,
                        rounds[-1].note if rounds else "no render attempted",
                        input_hash=ih, model=used_model, prompt_version="visual-critic/v1",
        input_tokens=in_tok, output_tokens=out_tok, cost_usd=cost,
        cost_known=cost_known, attempts=calls,)

    best = min(rendered, key=_score)
    outcome = VisualOutcome(best=best, rounds=rounds, stopped_because=stopped)

    payload = {
        "path": str(best.png),
        "round": best.index,
        "rounds_run": len(rounds),
        "accepted": outcome.accepted,
        "stopped_because": stopped,
        "high_severity": best.high,
        "total_defects": best.total,
        "spec": best.spec.model_dump(),
        "defects": [d.model_dump() for d in best.critique.defects] if best.critique else [],
        "history": [
            {"round": r.index, "high": r.high if r.critique else None,
             "total": r.total if r.critique else None,
             "png": str(r.png) if r.png else None, "note": r.note}
            for r in rounds
        ],
    }

    if not outcome.accepted:
        # Unaccepted output may still be the best available — but the run must
        # not record it as a clean success. This is the whole point.
        return degraded("visual", payload, started,
                        f"shipped with {best.high} high-severity defect(s): {stopped}",
                        input_hash=ih, model=used_model, prompt_version="visual-critic/v1",
        input_tokens=in_tok, output_tokens=out_tok, cost_usd=cost,
        cost_known=cost_known, attempts=calls,
                        tool_calls=["playwright.screenshot", "vision"])

    return ok("visual", payload, started, input_hash=ih, model=used_model, prompt_version="visual-critic/v1",
        input_tokens=in_tok, output_tokens=out_tok, cost_usd=cost,
        cost_known=cost_known, attempts=calls,
              tool_calls=["playwright.screenshot", "vision"])
