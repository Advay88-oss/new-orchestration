"""Three competing strategists and a judge.

The audit found the old "tri-arc debate" existed only in a legacy orchestrator
that production never ran, while the dashboard rendered three arcs with verdicts
of WINNER / GRAFTED / REJECTED and scores computed by subtracting 4 and 8 from a
single number. This module makes the debate real, and fixes the two things that
made the original judge worthless.

**1. Every strategist sees the same full evidence.**
Cognition's argument against naive fan-out is that parallel agents act on
incomplete information, so their outputs carry conflicting implicit decisions.
The mitigation is shared context, not fewer agents: all three receive the
identical evidence block and the identical brief, and differ only in the arc
they are asked to argue.

**2. The judge sees the evidence too.**
In the old pipeline the judge's prompt contained the drafts and the rebuttals
and nothing else — `raw_scout_data` was passed to the strategists and never to
the judge. With no sources in context, "claim integrity" could only be scored on
how well-sourced a sentence *reads*, so a confident fabrication beat a hedged
truth by construction. Here the judge is given the same evidence and must cite
which pieces support the winner.

**3. The judge is not the last line on facts.**
LLM judges miss factuality problems at a high rate, so the winner still goes
through claim extraction and entailment verification downstream. The judge
ranks; `verify.py` adjudicates.
"""
from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from .contracts import Opportunity, StageResult, Strategy, degraded, digest, ok
from .llm import LLMClient, LLMError, wrap_untrusted

ARCS: dict[str, dict[str, str]] = {
    "capital_efficiency": {
        "axiom": "The same collateral should be doing more than one job.",
        "brief": "Argue from the inefficiency of idle or single-purpose collateral.",
    },
    "risk_relief": {
        "axiom": "Leverage is easy. Not getting liquidated is the hard part.",
        "brief": "Argue from the failure mode first, then the structural reason it cannot spread.",
    },
    "agentic_credit": {
        "axiom": "Agents can pay. Agents cannot borrow.",
        "brief": "Argue from what an autonomous program cannot safely do with credit today.",
    },
}

STRATEGIST_VERSION = "debate-strategist/v1"
JUDGE_VERSION = "debate-judge/v1"

STRATEGIST_SCHEMA = {
    "type": "object",
    "properties": {
        "problem_statement": {"type": "string"},
        "angle": {"type": "string"},
        "audience": {"type": "string"},
        "evidence_used": {"type": "array", "items": {"type": "string"}},
        "strongest_objection": {"type": "string"},
    },
    "required": ["problem_statement", "angle", "audience", "evidence_used",
                 "strongest_objection"],
}


def strategist_system(arc: str) -> str:
    spec = ARCS[arc]
    return f"""You are a GTM strategist for Vanna, composable credit infrastructure
on Stellar Soroban. You argue exactly one narrative arc: **{arc}**.

Axiom: {spec['axiom']}
Brief: {spec['brief']}

You are competing against two strategists arguing different arcs from the SAME
evidence. Win on the strength of the argument, not on confidence.

Rules:
- Use ONLY the supplied evidence. Cite the evidence ids you actually relied on
  in `evidence_used`. An empty list is an honest answer when the evidence does
  not support your arc — and a better one than inventing support.
- Do not state metrics, dates, partnerships or capabilities the evidence does
  not contain. Everything you write is decomposed into claims and checked.
- `strongest_objection` must name the best argument AGAINST your own arc for
  this topic. A strategist who cannot state the counter-case has not thought
  about it, and the judge is told to weigh this."""


JUDGE_SCHEMA = {
    "type": "object",
    "properties": {
        "winner": {"type": "string",
                   "enum": ["capital_efficiency", "risk_relief", "agentic_credit"]},
        "reason": {"type": "string"},
        "evidence_support": {"type": "array", "items": {"type": "string"}},
        "rankings": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "arc": {"type": "string"},
                    "evidence_grounding": {"type": "integer"},
                    "argument_quality": {"type": "integer"},
                    "audience_fit": {"type": "integer"},
                    "note": {"type": "string"},
                },
                "required": ["arc", "evidence_grounding", "argument_quality",
                             "audience_fit", "note"],
            },
        },
        "unsupported_spotted": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["winner", "reason", "evidence_support", "rankings",
                 "unsupported_spotted"],
}

JUDGE_SYSTEM = """You rule between three competing strategy briefs for the same
topic. You are given the SAME evidence the strategists were given.

Score each on three axes, 0-10:
  evidence_grounding — is every specific in the brief actually in the evidence?
                       This dominates. A well-argued brief resting on a figure
                       that is not in the evidence scores 0 here.
  argument_quality   — does the argument follow, and does it name its own
                       strongest objection honestly?
  audience_fit       — would the stated audience recognise this problem?

Then:
- `unsupported_spotted`: quote any specific claim from ANY brief that the
  evidence does not support. Check the numbers against the evidence directly.
  Finding none is a claim you are making; make it only if it is true.
- `evidence_support`: the evidence ids that actually back the winner.

Do not reward confidence, length, or polish. A hedged brief that stays inside
the evidence beats a assured brief that leaves it. You are not the last check —
every claim in the winner is verified against the evidence afterwards — so do
not wave something through on the assumption that someone else will catch it."""


def _run_strategist(arc: str, opp: Opportunity, evidence_block: str,
                    client: LLMClient) -> dict[str, Any]:
    prompt = (
        f"TOPIC: {opp.title}\n"
        f"WHY THIS TOPIC: {opp.rationale}\n\n"
        f"{wrap_untrusted('evidence', evidence_block or '(no evidence available)')}\n\n"
        f"Make the strongest {arc} case for this topic."
    )
    try:
        data, resp = client.complete_json(
            prompt, schema=STRATEGIST_SCHEMA, system=strategist_system(arc),
            prompt_version=STRATEGIST_VERSION, temperature=0.7,
            max_output_tokens=4096,
        )
        return {"arc": arc, "ok": True, **data,
                "model": resp.model, "input_tokens": resp.input_tokens,
                "output_tokens": resp.output_tokens,
                "cost_usd": resp.cost_usd or 0.0, "cost_known": resp.pricing_known}
    except LLMError as exc:
        return {"arc": arc, "ok": False, "error": str(exc)[:300]}


def run_debate(opp: Opportunity, evidence_block: str,
               client: LLMClient) -> StageResult[dict]:
    """Three strategists in parallel, then a judge that sees the evidence."""
    started = time.time()
    ih = digest({"opp": opp.model_dump(), "ev": digest(evidence_block)})

    # Thin evidence is the binding constraint on everything downstream: with
    # nothing retrieved, the strategists correctly cite nothing, the verifier
    # correctly refuses every factual claim, and the gate correctly blocks. That
    # chain is honest but useless, and the operator needs to see the cause at
    # the top rather than infer it from four "unsupported" verdicts.
    evidence_thin = len(evidence_block.strip()) == 0

    with ThreadPoolExecutor(max_workers=3) as pool:
        briefs = list(pool.map(
            lambda arc: _run_strategist(arc, opp, evidence_block, client),
            ARCS.keys(),
        ))

    good = [b for b in briefs if b.get("ok")]
    in_tok = sum(b.get("input_tokens", 0) for b in good)
    out_tok = sum(b.get("output_tokens", 0) for b in good)
    cost = sum(b.get("cost_usd", 0.0) for b in good)
    cost_known = all(b.get("cost_known", False) for b in good) if good else False
    model = good[0].get("model") if good else None

    if not good:
        return degraded("debate", None, started,
                        "all three strategists failed: "
                        + "; ".join(b.get("error", "?") for b in briefs)[:300],
                        input_hash=ih)

    # --- judge --------------------------------------------------------
    brief_block = "\n\n".join(
        f"[{b['arc']}]\n"
        f"problem: {b['problem_statement']}\n"
        f"angle: {b['angle']}\n"
        f"audience: {b['audience']}\n"
        f"evidence cited: {', '.join(b.get('evidence_used') or []) or '(none)'}\n"
        f"strongest objection to itself: {b.get('strongest_objection', '')}"
        for b in good
    )
    judge_prompt = (
        f"TOPIC: {opp.title}\n\n"
        f"{wrap_untrusted('evidence', evidence_block or '(no evidence available)')}\n\n"
        f"COMPETING BRIEFS:\n{brief_block}\n\n"
        "Rule."
    )

    ruling: dict[str, Any] | None = None
    judge_note = ""
    try:
        ruling, jresp = client.complete_json(
            judge_prompt, schema=JUDGE_SCHEMA, system=JUDGE_SYSTEM,
            prompt_version=JUDGE_VERSION, temperature=0.1, max_output_tokens=6144,
        )
        in_tok += jresp.input_tokens
        out_tok += jresp.output_tokens
        cost += jresp.cost_usd or 0.0
        cost_known = cost_known and jresp.pricing_known
    except LLMError as exc:
        judge_note = f"judge failed ({str(exc)[:160]})"

    if ruling and any(b["arc"] == ruling.get("winner") for b in good):
        winner_arc = ruling["winner"]
    else:
        # Deterministic, explainable fallback: most evidence actually cited.
        # Never "the first one" and never a coin flip — and the run says a
        # fallback was used rather than presenting it as a ruling.
        winner_arc = max(good, key=lambda b: len(b.get("evidence_used") or []))["arc"]
        judge_note = judge_note or "judge returned an arc no strategist argued"
        judge_note += f"; fell back to most-evidence-cited ({winner_arc})"

    win = next(b for b in good if b["arc"] == winner_arc)
    strategy = Strategy(
        id=f"STR-{digest(opp.id + win['angle'])}",
        opportunity_id=opp.id,
        audience=win["audience"][:120],
        narrative_arc=winner_arc,  # type: ignore[arg-type]
        problem_statement=win["problem_statement"],
        angle=win["angle"],
        evidence_ids=list(win.get("evidence_used") or []),
    )

    payload = {
        "strategy": strategy.model_dump(),
        "winner": winner_arc,
        "briefs": briefs,
        "ruling": ruling,
        "judge_note": judge_note,
        "failed_strategists": [b["arc"] for b in briefs if not b.get("ok")],
    }

    meta = dict(model=model, prompt_version=JUDGE_VERSION, input_tokens=in_tok,
                output_tokens=out_tok, cost_usd=cost, cost_known=cost_known,
                attempts=len(good) + (1 if ruling else 0),
                tool_calls=[f"strategist x{len(good)}", "judge" if ruling else "judge:failed"])

    if judge_note or len(good) < 3 or evidence_thin:
        reasons = []
        if evidence_thin:
            reasons.append("no evidence retrieved for this topic — nothing "
                           "downstream can be verified")
        if len(good) < 3:
            reasons.append(f"only {len(good)}/3 strategists produced a brief")
        if judge_note:
            reasons.append(judge_note)
        return degraded("debate", payload, started, "; ".join(reasons)[:400],
                        input_hash=ih, **meta)

    return ok("debate", payload, started, input_hash=ih, **meta)


def strategy_from(payload: dict) -> Strategy:
    return Strategy(**payload["strategy"])
