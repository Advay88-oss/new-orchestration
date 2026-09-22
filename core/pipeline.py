"""The pipeline.

Thirteen stages, declared honestly as AGENT (a model call whose reasoning
determines the output) or STAGE (a deterministic function). Six are agents.

Two invariants the old orchestrator did not have:

  * **Every stage output is consumed.** In the audited run, four of thirteen
    agents wrote to `agent_outputs` and were never read again, and Agent 03's
    output never reached Agent 08 because of a field-name mismatch that
    `getattr(..., None)` swallowed. Here the dataflow is explicit and typed, so
    a severed link is a TypeError, not a silent literal.

  * **The run's status is the worst stage's status.** A run containing a
    degraded stage is reported as degraded. There is no path to a clean success
    that did not do the work.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Literal

from . import stages as S
from .debate import run_debate, strategy_from
from .contracts import Claim, CopyDraft, StageResult, VisualSpec, degraded, digest, ok
from .evidence import EvidenceStore, ingest_signals
from .gate import run_gate
from .knowledge import load_all as load_knowledge
from .llm import LLMClient
from .models import client_for, routing_table
from .runlog import RunLog
from .verify import VerificationCache, extract_claims, verify_claims, report as claim_report
from .media import media_stage, texture_data_uri
from .visual import optimize_visual

Kind = Literal["AGENT", "STAGE"]

# The declared pipeline. `kind` is not decoration — it is the claim the system
# makes about itself, and `python -m core.pipeline --manifest` prints it so the
# dashboard cannot describe a rule table as an agent.
MANIFEST: list[tuple[int, str, Kind, str]] = [
    (1,  "ingest",   "STAGE", "Read collected intelligence into typed signals"),
    (2,  "select",   "AGENT", "Judge which topic is worth publishing, and why not the others"),
    (3,  "debate",   "AGENT", "Three strategists argue competing arcs; a judge rules"),
    (4,  "plan",     "STAGE", "Bind arc to structure, format and length"),
    (5,  "copy",     "AGENT", "Write the post from evidence only"),
    (6,  "extract",  "AGENT", "Decompose copy into atomic claims"),
    (7,  "verify",   "AGENT", "Entailment-check every claim against evidence"),
    (8,  "concept",  "AGENT", "Three competing visual concepts + novelty gate"),
    (9,  "spec",     "AGENT", "Emit a schema-validated VisualSpec"),
    (10, "media",    "AGENT", "Generate media: texture, meme or Veo video"),
    (11, "visual",   "AGENT", "Render deterministically, critique, revise"),
    (12, "gate",     "STAGE", "Vocabulary rules + blocking-claim check"),
    (13, "review",   "STAGE", "Stage the asset for human approval"),
]

STAGE_KIND = {name: kind for _, name, kind, _ in MANIFEST}
STAGE_ORDER = [name for _, name, _, _ in MANIFEST]

WORST = {"ok": 0, "degraded": 1, "failed": 2}


@dataclass
class RunContext:
    run_id: str
    directive: str
    log: RunLog
    client: LLMClient
    store: EvidenceStore
    cache: VerificationCache
    results: dict[str, StageResult[Any]] = field(default_factory=dict)

    def record(self, res: StageResult[Any]) -> StageResult[Any]:
        self.results[res.stage] = res
        self.log.stage_ended(res)
        return res

    @property
    def status(self) -> str:
        if not self.results:
            return "failed"
        worst = max(self.results.values(), key=lambda r: WORST[r.status])
        return worst.status

    def totals(self) -> dict[str, Any]:
        return {
            "cost_usd": round(sum(r.cost_usd for r in self.results.values()), 6),
            "input_tokens": sum(r.input_tokens for r in self.results.values()),
            "output_tokens": sum(r.output_tokens for r in self.results.values()),
            "model_calls": sum(1 for r in self.results.values() if r.model),
            "agents_declared": sum(1 for k in STAGE_KIND.values() if k == "AGENT"),
            "agents_that_called_a_model": sum(
                1 for n, r in self.results.items()
                if STAGE_KIND.get(n) == "AGENT" and r.model),
        }


def new_run_id() -> str:
    return "RUN-" + datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")


def _guard(ctx: RunContext, name: str, fn: Callable[[], StageResult[Any]],
           input_hash: str) -> StageResult[Any]:
    """Run one stage with journaling. An exception becomes a failed result —
    never an unhandled crash that leaves the journal without an ending."""
    ctx.log.stage_started(name, input_hash)
    started = time.time()
    try:
        res = fn()
    except Exception as exc:                       # noqa: BLE001 — boundary
        from .contracts import failed as _failed
        res = _failed(name, started, f"{type(exc).__name__}: {exc}", input_hash=input_hash)
    return ctx.record(res)


def run_pipeline(directive: str, *, run_id: str | None = None,
                 client: LLMClient | None = None,
                 recent_layouts: list[str] | None = None) -> dict[str, Any]:
    """Execute the pipeline end to end. Always returns a summary; never raises."""
    run_id = run_id or new_run_id()
    log = RunLog(run_id)

    # Roles are bound from the declared routing table, so the model a stage uses
    # is a configuration fact rather than a literal buried in the call site.
    if client is None:
        client, reasoning_route = client_for("reasoning")
        route_note = reasoning_route.degraded_reason
    else:
        route_note = None

    ctx = RunContext(
        run_id=run_id, directive=directive, log=log,
        client=client, store=EvidenceStore(), cache=VerificationCache(),
    )
    log.run_started(directive, {
        "model": ctx.client.model,
        "routing": routing_table(),
        "routing_note": route_note,
        "manifest": [{"n": n, "stage": s, "kind": k} for n, s, k, _ in MANIFEST],
    })

    # 1 ingest --------------------------------------------------------------
    # Vanna's own facts ledger is loaded first. Without it the store holds only
    # competitor research and onchain readings, so a claim about Vanna's own
    # mechanism can never be entailed and the gate blocks almost everything.
    # Only Tiers A and B are admitted; C (illustrative), D (roadmap), E
    # (internal only) and F (stale) are read and withheld by `core.knowledge`.
    try:
        kb = load_knowledge(ctx.store)
    except Exception as exc:                      # noqa: BLE001 — boundary
        kb = {"error": str(exc)[:200]}
    log.event("knowledge_loaded", **kb)

    r_ing = _guard(ctx, "ingest", lambda: S.ingest(), digest(directive))
    signals = r_ing.value or []
    if signals:
        ingest_signals(ctx.store, signals)

    # 2 select --------------------------------------------------------------
    # Recent topics so the agent can decline to repeat itself.
    recent_topics = []
    try:
        from .runlog import list_runs as _list_runs
        recent_topics = [str(r.get("directive") or "")[:80]
                         for r in _list_runs(limit=6) if r.get("directive")]
    except Exception:
        pass

    r_sel = _guard(ctx, "select",
                   lambda: S.select(signals, directive, ctx.client, recent_topics),
                   digest([s.id for s in signals]))
    opp = r_sel.value
    if opp is None:
        return _finish(ctx, "nothing to act on: selection produced no opportunity")

    # 3 debate (AGENT: 3 strategists in parallel + a judge that sees evidence) --
    # The evidence block is built BEFORE the debate, so all three strategists and
    # the judge argue from identical context. The old pipeline passed sources to
    # the strategists and withheld them from the judge.
    ev_block = "\n".join(
        f"- [{e.id}] {e.snippet[:220]} (source: {e.source_name}, observed {e.observed_at[:10]})"
        for e in ctx.store.search(f"{opp.title} {opp.rationale}", limit=12)
    )
    r_deb = _guard(ctx, "debate", lambda: run_debate(opp, ev_block, ctx.client),
                   digest(opp.model_dump()))
    if not r_deb.value:
        return _finish(ctx, "debate produced no strategy")
    st = strategy_from(r_deb.value)

    # 4 plan ----------------------------------------------------------------
    r_plan = _guard(ctx, "plan", lambda: S.plan(st, opp), digest(st.narrative_arc))
    planv = r_plan.value or {}
    pb, vh = planv.get("playbook"), planv.get("vehicle")
    if not pb or not vh:
        return _finish(ctx, "plan stage produced no playbook/vehicle")

    # 5 copy (AGENT) ---------------------------------------------------------
    # Re-retrieve against the winning angle. The debate's block was built from
    # the opportunity; the angle names the mechanism the copy will actually
    # assert, so the facts that can support it are different.
    ev_block = "\n".join(
        f"- [{e.id}] {e.snippet[:240]} (source: {e.source_name})"
        for e in ctx.store.search(f"{st.angle} {st.problem_statement}", limit=14)
    ) or ev_block
    r_cpy = _guard(ctx, "copy", lambda: S.write_copy_agent(st, pb, vh, ctx.store, ctx.client, ctx.cache),
                   digest({"st": st.id, "ev": digest(ev_block)}))
    draft: CopyDraft | None = r_cpy.value
    if draft is None:
        return _finish(ctx, "copy agent produced nothing")

    # 7 extract / 8 verify (AGENTS) ----------------------------------------
    surface = "\n".join([draft.hook, draft.body, *draft.thread])
    r_ext = _guard(ctx, "extract", lambda: extract_claims(surface, ctx.client),
                   digest(surface))
    claims: list[Claim] = r_ext.value or []

    r_ver = _guard(ctx, "verify",
                   lambda: verify_claims(claims, ctx.store, ctx.client, ctx.cache),
                   digest([c.text for c in claims]))
    verified: list[Claim] = r_ver.value or claims
    draft = draft.model_copy(update={"claims": verified})

    # 9 concept (AGENT) -----------------------------------------------------
    r_con = _guard(ctx, "concept",
                   lambda: S.concepts(st, draft, recent_layouts or [], ctx.client),
                   digest(draft.id))
    concept = (r_con.value or {}).get("chosen")

    # 10 spec (AGENT) -------------------------------------------------------
    spec: VisualSpec | None = None
    if concept:
        r_spec = _guard(ctx, "spec",
                        lambda: S.visual_spec(concept, draft, verified, ctx.client),
                        digest(concept))
        spec = r_spec.value
    else:
        ctx.record(degraded("spec", None, time.time(),
                            "no concept available to specify", input_hash=digest(draft.id)))

    # 10 media (AGENT: nano banana / nano banana pro / Veo 3.1) -------------
    r_media = _guard(ctx, "media",
                     lambda: media_stage(directive, (spec.headline if spec else draft.hook),
                                         run_id, caption=draft.hook,
                                         spec=spec, claims=verified),
                     digest(directive))
    media_payload = r_media.value or {}
    tex = texture_data_uri(media_payload.get("path"))         if media_payload.get("kind") == "texture" else None

    # 11 visual (AGENT: render + critic loop) -------------------------------
    visual_payload: dict[str, Any] | None = None
    if spec is not None:
        r_vis = _guard(ctx, "visual",
                       lambda: optimize_visual(spec, run_id, ctx.client,
                                               texture_data_uri=tex),
                       digest(spec.model_dump()))
        visual_payload = r_vis.value
        if visual_payload and visual_payload.get("path"):
            log.adopt_file("visual.png", Path(visual_payload["path"]))
    else:
        ctx.record(degraded("visual", None, time.time(),
                            "no spec to render", input_hash=digest(draft.id)))

    # 12 gate ---------------------------------------------------------------
    r_gate = _guard(ctx, "gate", lambda: run_gate(draft, spec, verified),
                    digest(surface))
    decision = r_gate.value

    # 13 review -------------------------------------------------------------
    r_rev = _guard(ctx, "review",
                   lambda: _stage_for_review(ctx, draft, spec, visual_payload, decision),
                   digest(draft.id))

    return _finish(ctx, None, draft=draft, spec=spec, visual=visual_payload,
                   decision=decision, claims=verified)


def _stage_for_review(ctx: RunContext, draft: CopyDraft, spec: VisualSpec | None,
                      visual: dict | None, decision) -> StageResult[dict]:
    """Write the review packet. Human approval is the terminus — this stage
    stages, it does not publish, and it does not claim delivery it did not make.

    The old Agent 11 wrote `published_channels: 3` with fabricated receipt URLs,
    and Agent 12 set `delivered_to_telegram: True` as a hardcoded literal while
    containing no Telegram code at all.
    """
    started = time.time()
    ih = digest(draft.id)
    packet = {
        "run_id": ctx.run_id,
        "status": "awaiting_human_review",
        "publishable": bool(decision and decision.passed),
        "channel": draft.channel,
        "hook": draft.hook,
        "body": draft.body,
        "thread": draft.thread,
        "visual_path": (visual or {}).get("path"),
        "visual_accepted": (visual or {}).get("accepted"),
        "gate": decision.model_dump() if decision else None,
        "claims": claim_report(draft.claims),
        # Deliberately absent: receipts, published_channels, delivered_to_*.
        # Nothing here asserts an action that was not taken.
    }
    rel = ctx.log.artifact("review_packet.json",
                           __import__("json").dumps(packet, indent=2, default=str).encode())
    packet["artifact"] = rel

    if not packet["publishable"]:
        reasons = []
        if decision:
            reasons += decision.rule_violations
            reasons += [f"unverified: {c.text[:60]}" for c in decision.blocking_claims[:4]]
        return degraded("review", packet, started,
                        "staged but BLOCKED for publication: " + "; ".join(reasons)[:400],
                        input_hash=ih)
    return ok("review", packet, started, input_hash=ih)


def _finish(ctx: RunContext, abort_reason: str | None, **extra: Any) -> dict[str, Any]:
    status = "aborted" if abort_reason else ctx.status
    totals = ctx.totals()
    summary = {
        "run_id": ctx.run_id,
        "status": status,
        "abort_reason": abort_reason,
        "stages": {
            n: {"kind": STAGE_KIND.get(n), "status": r.status,
                "duration_s": r.duration_s, "model": r.model,
                "degraded_reason": r.degraded_reason, "error": r.error}
            for n, r in ctx.results.items()
        },
        "degraded": [n for n, r in ctx.results.items() if r.status == "degraded"],
        "failed": [n for n, r in ctx.results.items() if r.status == "failed"],
        **totals,
    }
    if extra.get("draft") is not None:
        d = extra["draft"]
        summary["hook"] = d.hook
        summary["body"] = d.body
    if extra.get("visual"):
        summary["visual_path"] = extra["visual"].get("path")
        summary["visual_accepted"] = extra["visual"].get("accepted")
    if extra.get("decision") is not None:
        summary["gate_passed"] = extra["decision"].passed
    if extra.get("claims") is not None:
        summary["claims"] = claim_report(extra["claims"])

    ctx.log.run_ended(status, summary)
    return summary


def manifest_text() -> str:
    lines = ["#   stage        kind    purpose"]
    for n, name, kind, why in MANIFEST:
        lines.append(f"{n:<3} {name:<12} {kind:<7} {why}")
    agents = sum(1 for _, _, k, _ in MANIFEST if k == "AGENT")
    lines.append(f"\n{len(MANIFEST)} stages — {agents} agents, {len(MANIFEST) - agents} deterministic")
    return "\n".join(lines)


if __name__ == "__main__":
    import argparse
    import json

    ap = argparse.ArgumentParser(description="Vanna v2 pipeline")
    ap.add_argument("--directive", default="", help="founder directive")
    ap.add_argument("--manifest", action="store_true", help="print the stage manifest and exit")
    ap.add_argument("--model", default=None)
    a = ap.parse_args()

    if a.manifest:
        print(manifest_text())
        raise SystemExit(0)

    client = LLMClient(model=a.model) if a.model else LLMClient()
    out = run_pipeline(a.directive, client=client)
    print(json.dumps(out, indent=2, default=str))
