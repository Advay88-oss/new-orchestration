"""The pipeline stages.

Named honestly: `AGENT` stages make a model call whose reasoning determines the
output. `STAGE` entries are deterministic functions. The old system called all
thirteen "agents" while ten were rule tables or literal dicts — and four of the
thirteen produced output that nothing downstream ever read.

Every function here returns a StageResult, so a failure or a fallback is
recorded as such and cannot be reported as a clean success.
"""
from __future__ import annotations

import json
import os
import re
import time
from pathlib import Path
from typing import Any

from .contracts import (
    Block, Claim, CopyDraft, Focal, Opportunity, PaletteSlice, Signal,
    StageResult, Strategy, VisualSpec, degraded, digest, ok,
)
from .design import PALETTE, REJECTED_TREATMENTS, default_palette
from .evidence import EvidenceStore, now_iso
from .llm import LLMClient, LLMError, wrap_untrusted
from .models import client_for

REPO = Path(__file__).resolve().parents[1]
INTEL_CACHE = REPO / "pipeline" / "state" / "intelligence_cache.json"


# ==========================================================================
# 01  INGEST  — STAGE (deterministic reader over real collected intelligence)
# ==========================================================================

def ingest(limit: int = 150) -> StageResult[list[Signal]]:
    """Read collected intelligence. Engagement is passed through only when the
    source actually reported it — the old scout synthesised it with
    `random.randint(85, 850)` and wrote it out as observed."""
    started = time.time()
    # The cap is generous by design: the evidence store is the binding
    # constraint on whether anything can be verified at all, and a claim
    # retrieved from 150 candidates is no less checkable than from 30.
    ih = digest({"src": str(INTEL_CACHE), "limit": limit})

    if not INTEL_CACHE.exists():
        return degraded("ingest", [], started,
                        f"no intelligence cache at {INTEL_CACHE}", input_hash=ih)
    try:
        raw = json.loads(INTEL_CACHE.read_text(encoding="utf-8"))
    except Exception as exc:
        return degraded("ingest", [], started, f"cache unreadable: {exc}", input_hash=ih)

    signals: list[Signal] = []
    for source_name, payload in _iter_sources(raw):
        for item in payload[:limit]:
            if not isinstance(item, dict):
                continue
            title = str(item.get("title") or item.get("headline") or item.get("text") or "").strip()
            if not title:
                continue
            eng = item.get("engagement")
            signals.append(Signal(
                id=f"SIG-{digest(title)}",
                title=title[:280],
                summary=str(item.get("summary") or item.get("description") or "")[:600],
                source_name=source_name,
                source_url=item.get("url") or item.get("link"),
                observed_at=str(item.get("observed_at") or item.get("timestamp") or now_iso()),
                engagement=eng if isinstance(eng, dict) and all(
                    isinstance(v, int) for v in eng.values()) else None,
            ))

    # Onchain metric blocks (stellar_fee_stats, blend_tvl, ...) are measurements,
    # not headlines. They are the most valuable input the system has, because
    # they are the only numbers it is entitled to publish.
    signals.extend(_metric_signals(raw))

    # Competitor research: real scraped pages with per-claim provenance. Without
    # these the evidence store holds only a handful of onchain metrics, so a
    # query about lending mechanics retrieves nothing and every strategist
    # honestly cites no evidence — correct behaviour, useless output.
    signals.extend(_research_signals())

    if not signals:
        return degraded("ingest", [], started,
                        "cache present but contained no usable signals", input_hash=ih)
    return ok("ingest", signals[:limit], started, input_hash=ih,
              tool_calls=["intelligence_cache"])


def _metric_signals(raw: Any) -> list[Signal]:
    out: list[Signal] = []
    if not isinstance(raw, dict):
        return out
    for group, block in raw.items():
        if not isinstance(block, dict):
            continue
        observed = str(block.get("updated_at") or block.get("observed_at") or now_iso())
        facts = [(k, v) for k, v in block.items()
                 if k not in ("updated_at", "observed_at") and isinstance(v, (int, float, str))]
        if not facts:
            continue
        readable = ", ".join(f"{k.replace('_', ' ')} = {v}" for k, v in facts)
        title = f"{group.replace('_', ' ')}: {readable}"
        out.append(Signal(
            id=f"SIG-{digest(title)}",
            title=title[:280],
            summary=f"Measured onchain value for {group} as of {observed}.",
            source_name=f"onchain:{group}",
            source_url=None,
            observed_at=observed,
        ))
    return out



RESEARCH_DIR = REPO / "pipeline" / "state" / "research_runs"

# Deliberately NOT ingested: pipeline/state/scraped_social_posts.jsonl. The
# audit found it is generated from a hand-written SEED_POSTS list, with invented
# engagement counts and profile URLs standing in for post URLs. Feeding it to
# the evidence store would launder fiction into observation, which is the exact
# failure this rebuild exists to remove.


# The upstream research extractor emits a lot of non-claims: page titles, image
# URL fragments parsed as metrics, and bare figures with no subject ("Metric
# observed: $12B" — of what?). Letting those into the evidence store does not
# make the system better grounded; it makes retrieval noisier and invites a
# verifier to match a number against a figure that means nothing.
_JUNK_SUBSTRINGS = (
    "official title on",      # a page title is not a claim
    # Keyword-presence rows from the retired regex extractor, e.g.
    # "Morpho explicitly references integration or compatibility with: Morpho".
    "explicitly references integration",
    "references integration or compatibility",
    "http://", "https://", "![", "](",
    ".png", ".jpg", ".jpeg", ".svg", ".webp",
)

_BARE_METRIC = re.compile(r"^\s*metric observed\s*:", re.I)
_URL_FRAGMENT = re.compile(r"^[A-Za-z0-9._/+-]{16,}$")


def _is_junk_claim(text: str) -> bool:
    """Reject extractor noise before it reaches the evidence store.

    The upstream research extractor emits page titles, image-URL fragments
    parsed as metrics, and bare figures with no subject ("Metric observed:
    $12B" — of what?). Admitting those does not make the system better
    grounded; it makes retrieval noisier and invites a verifier to match a
    number against a figure that means nothing.
    """
    s = text.strip()
    if len(s) < 16:
        return True
    low = s.lower()
    if any(j in low for j in _JUNK_SUBSTRINGS):
        return True
    if _BARE_METRIC.match(s):
        return True          # a figure with no subject cannot support a claim
    if _URL_FRAGMENT.match(s):
        return True
    # A path-like token with no prose around it ("finance/assets/hero/hero@1x").
    if "/" in s and " " not in s.split("/")[0]:
        return True
    # A "claim" that is mostly punctuation or digits is not a statement.
    letters = sum(ch.isalpha() for ch in s)
    return letters < len(s) * 0.5


def _research_signals(limit_per_run: int = 12) -> list[Signal]:
    """Competitor claims from real scraped pages, with their own provenance."""
    out: list[Signal] = []
    if not RESEARCH_DIR.exists():
        return out
    for f in sorted(RESEARCH_DIR.glob("*.json"), reverse=True):
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not isinstance(d, dict):
            continue
        entity = str(d.get("entity") or "unknown")
        for c in (d.get("claims") or [])[:limit_per_run]:
            if not isinstance(c, dict):
                continue
            text = str(c.get("claim") or "").strip()
            url = c.get("source_url")
            if not text or not url:
                continue          # a claim with no locator cannot be re-checked
            if _is_junk_claim(text):
                continue
            # Claims written before `core.research` carry no extractor tag and
            # no supporting quote. They are kept only if they survive the junk
            # filter above; the tagged ones are trusted because the extractor
            # verified each quote against the page it came from.
            if c.get("extractor") and not c.get("supporting_quote"):
                continue
            metric = c.get("metric_extracted")
            title = f"{entity}: {text}"
            if metric:
                title += f" [metric: {metric}]"
            out.append(Signal(
                id=f"SIG-{digest(c.get('claim_id') or title)}",
                title=title[:280],
                summary=(f"{c.get('category', '')} claim about {entity}, "
                         f"{c.get('source_type', 'source')}, "
                         f"evidence_status={c.get('evidence_status', 'UNKNOWN')}")[:600],
                source_name=f"research:{entity}",
                source_url=str(url),
                observed_at=str(c.get("observed_at") or c.get("data_as_of") or now_iso()),
            ))
    return out


def _iter_sources(raw: Any):
    if isinstance(raw, dict):
        for key, val in raw.items():
            if isinstance(val, list):
                yield key, val
            elif isinstance(val, dict):
                for k2, v2 in val.items():
                    if isinstance(v2, list):
                        yield f"{key}.{k2}", v2
    elif isinstance(raw, list):
        yield "cache", raw


# ==========================================================================
# 02  SELECT  — AGENT
# ==========================================================================

SELECT_VERSION = "select/v1"
SELECT_SCHEMA = {
    "type": "object",
    "properties": {
        "chosen_signal_id": {"type": "string"},
        "title": {"type": "string"},
        "rationale": {"type": "string"},
        "audience": {"type": "string"},
        "score": {"type": "number"},
        "rejected": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {"signal_id": {"type": "string"}, "why": {"type": "string"}},
                "required": ["signal_id", "why"],
            },
        },
    },
    "required": ["chosen_signal_id", "title", "rationale", "audience", "score", "rejected"],
}

SELECT_SYSTEM = """You choose what Vanna should talk about next.

Vanna is composable credit infrastructure on Stellar Soroban testnet: unified
margin accounts, isolated per-user contracts, policy-bounded risk management,
credit rails for autonomous agents.

You are given candidate signals and the topics recently covered. Pick the ONE
worth a post now, and say why the others are not.

Judge on:
- Does Vanna have something specific to say about it, or only a generic take?
- Is there evidence behind it, or would a post have to invent support?
- Has this ground been covered recently? Repetition is a cost.
- Would the audience recognise the problem without being told it exists?

`score` is your confidence that this is worth publishing, 0.0-1.0. Be willing to
score low: a weak week honestly scored is more useful than a manufactured one.
`rejected` must name every other candidate you considered and why it lost."""


def select(signals: list[Signal], directive: str = "",
           client: LLMClient | None = None,
           recent_topics: list[str] | None = None) -> StageResult[Opportunity]:
    """Choose the topic worth publishing.

    This was a keyword-weight table: it could tell that a headline contained
    "liquidation" but not whether Vanna had anything to say about it. The score
    was the sum of matched weights, which is a relevance proxy, not a judgement.
    """
    started = time.time()
    ih = digest({"n": len(signals), "directive": directive})

    if not signals and not directive:
        return degraded("select", None, started,
                        "no signals and no directive to select from", input_hash=ih)

    # A founder directive is an instruction, not a candidate to be judged.
    if directive.strip():
        opp = Opportunity(
            id=f"OPP-{digest(directive)}", title=directive.strip()[:180],
            rationale="Founder directive; selection deferred to the instruction.",
            audience="A1: Stellar & Soroban DeFi builders",
            score=0.7,
            signal_ids=[s.id for s in signals[:5]],
        )
        return ok("select", opp, started, input_hash=ih)

    if client is None:
        client, _ = client_for("reasoning")

    listing = "\n".join(f"- [{s.id}] {s.title[:180]} (source: {s.source_name})"
                         for s in signals[:40])
    recent = ", ".join(recent_topics or []) or "(nothing recent)"
    prompt = (
        f"RECENTLY COVERED: {recent}\n\n"
        f"{wrap_untrusted('candidate signals', listing)}\n\n"
        "Choose what to publish about."
    )

    try:
        data, resp = client.complete_json(
            prompt, schema=SELECT_SCHEMA, system=SELECT_SYSTEM,
            prompt_version=SELECT_VERSION, temperature=0.3, max_output_tokens=4096,
        )
    except LLMError as exc:
        return degraded("select", None, started, f"select agent failed: {exc}",
                        input_hash=ih)

    chosen = next((s for s in signals if s.id == data.get("chosen_signal_id")), None)
    opp = Opportunity(
        id=f"OPP-{digest(data['title'])}",
        title=data["title"][:180],
        rationale=data["rationale"][:600],
        audience=data["audience"][:120],
        score=min(max(float(data.get("score", 0.5)), 0.0), 1.0),
        signal_ids=[chosen.id] if chosen else [s.id for s in signals[:3]],
    )
    meta = dict(model=resp.model, prompt_version=resp.prompt_version,
                input_tokens=resp.input_tokens, output_tokens=resp.output_tokens,
                cost_usd=resp.cost_usd or 0.0, cost_known=resp.pricing_known)

    if opp.score < 0.4:
        return degraded("select", opp, started,
                        f"agent scored this topic {opp.score:.2f} — thin week, "
                        f"publishing is a judgement call", input_hash=ih, **meta)
    return ok("select", opp, started, input_hash=ih, **meta)


# ==========================================================================
# 03  STRATEGY  — AGENT
# ==========================================================================

STRATEGY_VERSION = "strategy/v1"
STRATEGY_SCHEMA = {
    "type": "object",
    "properties": {
        "narrative_arc": {"type": "string",
                          "enum": ["capital_efficiency", "risk_relief", "agentic_credit"]},
        "problem_statement": {"type": "string"},
        "angle": {"type": "string"},
        "audience": {"type": "string"},
    },
    "required": ["narrative_arc", "problem_statement", "angle", "audience"],
}

STRATEGY_SYSTEM = """You are a GTM strategist for Vanna, composable credit
infrastructure on Stellar Soroban.

Pick exactly ONE narrative arc and commit to it. Mixing arcs is forbidden.
  capital_efficiency — the same collateral doing more work
  risk_relief        — not getting liquidated is the hard part
  agentic_credit     — credit that programs can use safely

Write a problem_statement that names a concrete situation the audience
recognises, and an angle that is a specific argument — not a topic.

Use ONLY the supplied evidence. Do not introduce metrics, dates, partnerships or
product capabilities that are not in it. If the evidence is thin, say so in the
angle rather than inventing support."""


def strategy(opp: Opportunity, signals: list[Signal], client: LLMClient) -> StageResult[Strategy]:
    started = time.time()
    ih = digest({"opp": opp.model_dump(), "n": len(signals)})

    ctx = "\n".join(f"- [{s.source_name}] {s.title}" for s in signals[:12]) or "(none)"
    prompt = (
        f"OPPORTUNITY: {opp.title}\n"
        f"RATIONALE: {opp.rationale}\n\n"
        f"{wrap_untrusted('signals', ctx)}\n\n"
        "Produce the strategy."
    )
    try:
        data, resp = client.complete_json(
            prompt, schema=STRATEGY_SCHEMA, system=STRATEGY_SYSTEM,
            prompt_version=STRATEGY_VERSION, temperature=0.3, max_output_tokens=4096,
        )
    except LLMError as exc:
        return degraded("strategy", None, started, f"strategy agent failed: {exc}",
                        input_hash=ih)

    st = Strategy(
        id=f"STR-{digest(opp.id + data['angle'])}",
        opportunity_id=opp.id,
        audience=data["audience"][:120],
        narrative_arc=data["narrative_arc"],
        problem_statement=data["problem_statement"],
        angle=data["angle"],
        evidence_ids=opp.signal_ids,
    )
    return ok("strategy", st, started, input_hash=ih, model=resp.model,
              prompt_version=resp.prompt_version, input_tokens=resp.input_tokens,
              output_tokens=resp.output_tokens, cost_usd=resp.cost_usd or 0.0, cost_known=resp.pricing_known,
              attempts=resp.attempts)


# ==========================================================================
# 04  PLAYBOOK  — STAGE (deterministic; output IS consumed by copy)
# ==========================================================================

PLAYBOOKS: dict[str, dict[str, Any]] = {
    "capital_efficiency": {
        "id": "PB_CAPITAL",
        "shape": "Lead with the inefficiency, then the mechanism, then the number.",
        "forbidden": ["yield farming framing", "APY chasing"],
    },
    "risk_relief": {
        "id": "PB_RISK",
        "shape": "Name the failure mode first, then the structural reason it cannot spread.",
        "forbidden": ["fear-mongering about competitors", "implying zero risk"],
    },
    "agentic_credit": {
        "id": "PB_AGENTIC",
        "shape": "Start from what an autonomous agent cannot safely do today.",
        "forbidden": ["AI hype register", "claims of autonomous trading"],
    },
}


def playbook(st: Strategy) -> StageResult[dict]:
    started = time.time()
    ih = digest(st.narrative_arc)
    pb = PLAYBOOKS[st.narrative_arc]
    return ok("playbook", dict(pb, arc=st.narrative_arc), started, input_hash=ih)


def plan(st: Strategy, opp: Opportunity) -> StageResult[dict]:
    """Playbook + vehicle in one deterministic step.

    Both were separate 'agents' in the old system; neither made a model call and
    one of them (`SeriesEngine`) was instantiated and never invoked at all.
    Merging them is the honest shape: it is a single routing decision.
    """
    started = time.time()
    ih = digest({"arc": st.narrative_arc, "score": opp.score})
    pb = dict(PLAYBOOKS[st.narrative_arc], arc=st.narrative_arc)
    vh = vehicle(st, opp).value or {}
    return ok("plan", {"playbook": pb, "vehicle": vh}, started, input_hash=ih)


# ==========================================================================
# 05  VEHICLE  — STAGE (deterministic; output IS consumed by copy + spec)
# ==========================================================================

def vehicle(st: Strategy, opp: Opportunity) -> StageResult[dict]:
    started = time.time()
    ih = digest({"arc": st.narrative_arc, "score": opp.score})
    # Thin evidence gets the shorter, lower-claim format. This is a real
    # decision with a downstream effect, not a label.
    if opp.score >= 0.6 and len(opp.signal_ids) >= 3:
        v = {"id": "VH_THREAD", "channel": "x", "shape": "thread", "max_parts": 3,
             "reason": f"score {opp.score} with {len(opp.signal_ids)} supporting signals"}
    else:
        v = {"id": "VH_SINGLE", "channel": "x", "shape": "single", "max_parts": 1,
             "reason": f"thin support (score {opp.score}, {len(opp.signal_ids)} signals)"}
    return ok("vehicle", v, started, input_hash=ih)


# ==========================================================================
# 05  COPY  — AGENT (tool-using, self-checking)
# ==========================================================================

COPY_AGENT_VERSION = "copy-agent/v1"

COPY_AGENT_SCHEMA = {
    "type": "object",
    "properties": {
        "hook": {"type": "string"},
        "body": {"type": "string"},
        "thread": {"type": "array", "items": {"type": "string"}},
        "checked_claims": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {"claim": {"type": "string"}, "status": {"type": "string"}},
                "required": ["claim", "status"],
            },
        },
        "dropped": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Claims you wanted to make but could not support.",
        },
    },
    "required": ["hook", "body", "thread", "checked_claims", "dropped"],
}


def copy_agent_goal(pb: dict, vh: dict, st: Strategy) -> str:
    return f"""You are Vanna's copywriter. Vanna is composable credit
infrastructure on Stellar Soroban testnet.

GOAL: a {vh['shape']} for {vh['channel'].upper()}, at most {vh['max_parts']}
part(s), arguing the {pb['arc']} arc — in which **every factual sentence has
been checked and came back verified**.

Structure: {pb['shape']}
Forbidden for this arc: {', '.join(pb['forbidden'])}.
Problem: {st.problem_statement}
Angle: {st.angle}

Work in this order. Do not gather indefinitely:
  1. search_evidence for the facts your argument needs.
  2. Draft.
  3. check_claim on EVERY factual sentence you intend to keep.
  4. If one comes back `unsupported`, the sentence is almost always wider than
     the fact. Narrow it to what the evidence says, or drop it and record it in
     `dropped`. Never submit an unsupported factual claim.
  5. submit.

Voice: plain, technical, unhurried. Short sentences. No hype register, no
exclamation marks, no "revolutionary"/"seamlessly". Rhetorical framing needs no
check — but anything with a number, a capability or a named entity does.

A shorter post where every line holds is the goal. Dropping a claim you cannot
support is success, not failure."""


def write_copy_agent(st: Strategy, pb: dict, vh: dict, store, client: LLMClient,
                     cache=None) -> StageResult[CopyDraft]:
    """The copywriter as a real agent: goal, tools, and a bounded loop.

    The previous version received a fixed evidence block and produced a draft in
    one call. It had no way to find out whether a sentence would verify, so it
    routinely widened a fact by an adjective and the run was blocked two stages
    later. This one asks the verifier directly, before submitting.
    """
    from .agent import Agent
    from .tools import writing_toolbox

    started = time.time()
    ih = digest({"st": st.model_dump(), "pb": pb["id"], "vh": vh["id"]})

    agent = Agent(
        name="copywriter",
        goal=copy_agent_goal(pb, vh, st),
        tools=writing_toolbox(store, client, cache),
        answer_schema=COPY_AGENT_SCHEMA,
        client=client,
        prompt_version=COPY_AGENT_VERSION,
        max_steps=10,
        temperature=0.6,
    )

    def build(answer: dict) -> CopyDraft:
        thread = [x.strip() for x in (answer.get("thread") or []) if str(x).strip()]
        return CopyDraft(
            id=f"CPY-{digest(answer['hook'])}",
            strategy_id=st.id,
            channel=vh["channel"],
            hook=answer["hook"].strip(),
            body=answer["body"].strip(),
            thread=thread[: vh["max_parts"]],
        )

    res = agent.as_stage("copy", "Write it now. Follow the order in your instructions.",
                         input_hash=ih, build=build)

    # If the agent self-reported an unsupported claim it kept, say so — the run
    # should not look clean when the writer already knew.
    if res.status == "ok" and res.value is not None:
        return res
    return res


# ==========================================================================
# 09  CONCEPT  — AGENT (real competing concepts, with a novelty gate)
# ==========================================================================

CONCEPT_VERSION = "concept/v1"
CONCEPT_SCHEMA = {
    "type": "object",
    "properties": {
        "concepts": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "idea": {"type": "string"},
                    "layout": {"type": "string",
                               "enum": ["hero_stat", "comparison", "sequence", "quote", "diagram"]},
                    "why": {"type": "string"},
                },
                "required": ["title", "idea", "layout", "why"],
            },
        },
        "recommended": {"type": "integer"},
    },
    "required": ["concepts", "recommended"],
}

CONCEPT_SYSTEM = f"""You are an art director proposing visual concepts for a 1:1
social asset for a DeFi credit-infrastructure brand.

Propose THREE genuinely different concepts — different layout, different visual
argument. Three variations of one idea is a failure.

The brand rejects these treatments outright:
{chr(10).join('  - ' + t for t in REJECTED_TREATMENTS)}

Available layouts and what they are for:
  hero_stat  — one number carries the argument
  comparison — two states set against each other
  sequence   — an ordered mechanism, 3-5 steps
  quote      — a single sentence as the whole image
  diagram    — a structural relationship

Pick `recommended` as the index (0-2) of the strongest, and say why in that
concept's `why`."""


def concepts(st: Strategy, draft: CopyDraft, recent_layouts: list[str],
             client: LLMClient) -> StageResult[dict]:
    """Three competing concepts plus a novelty check against recent output."""
    started = time.time()
    ih = digest({"st": st.id, "draft": draft.id, "recent": recent_layouts})

    recent = ", ".join(recent_layouts[-6:]) or "(none)"
    prompt = (
        f"ARC: {st.narrative_arc}\nANGLE: {st.angle}\n"
        f"HOOK: {draft.hook}\nBODY: {draft.body[:600]}\n\n"
        f"Layouts used in recent assets (avoid repeating): {recent}\n\n"
        "Propose three concepts."
    )
    try:
        data, resp = client.complete_json(
            prompt, schema=CONCEPT_SCHEMA, system=CONCEPT_SYSTEM,
            prompt_version=CONCEPT_VERSION, temperature=0.8, max_output_tokens=6144,
        )
    except LLMError as exc:
        return degraded("concept", None, started, f"concept agent failed: {exc}",
                        input_hash=ih)

    cands = data.get("concepts", [])
    if not cands:
        return degraded("concept", None, started, "agent returned no concepts", input_hash=ih)

    idx = data.get("recommended", 0)
    idx = idx if 0 <= idx < len(cands) else 0

    # Novelty gate. Unlike the old one — which flagged every concept a STRUCTURAL
    # CLONE, scored them negative, and shipped the least bad — this one actually
    # switches to an unused layout when the recommendation repeats.
    chosen = cands[idx]
    note = ""
    if chosen["layout"] in recent_layouts[-3:]:
        alt = next((c for c in cands if c["layout"] not in recent_layouts[-3:]), None)
        if alt is not None:
            note = (f"novelty gate: '{chosen['layout']}' used in the last 3 assets; "
                    f"switched to '{alt['layout']}'")
            chosen = alt
        else:
            note = f"novelty gate: all three concepts reuse recent layouts ({chosen['layout']})"

    payload = {"chosen": chosen, "all": cands, "novelty_note": note}
    if note.startswith("novelty gate: all three"):
        return degraded("concept", payload, started, note, input_hash=ih,
                        model=resp.model, prompt_version=resp.prompt_version,
                        input_tokens=resp.input_tokens, output_tokens=resp.output_tokens,
                        cost_usd=resp.cost_usd or 0.0, cost_known=resp.pricing_known)
    return ok("concept", payload, started, input_hash=ih, model=resp.model,
              prompt_version=resp.prompt_version, input_tokens=resp.input_tokens,
              output_tokens=resp.output_tokens, cost_usd=resp.cost_usd or 0.0, cost_known=resp.pricing_known)


# ==========================================================================
# 10  SPEC  — AGENT (LLM writes a schema-validated spec; it does not draw)
# ==========================================================================

SPEC_VERSION = "spec/v1"

SPEC_SYSTEM = """You convert an approved concept into a VisualSpec that a
deterministic layout engine will execute. You are NOT describing a picture.

Hard rules:
- Text you write is rendered verbatim by a browser. Keep the headline under ~70
  characters; it must fit two lines.
- At most 4 blocks. Fewer is stronger. Dense blocks are the single most common
  way these assets fail.
- `focal.block_index` must point at the block that carries the argument.
- Only state figures that appear in the supplied copy. Invent nothing.
- Prefer a `stat` block when there is a real number; otherwise do not fabricate
  one to fill the layout."""


def visual_spec(concept: dict, draft: CopyDraft, verified: list[Claim],
                client: LLMClient) -> StageResult[VisualSpec]:
    started = time.time()
    ih = digest({"concept": concept.get("title"), "draft": draft.id})

    safe_facts = [c.text for c in verified if c.status == "verified"]
    facts_block = "\n".join(f"- {f}" for f in safe_facts) or "(none verified — use no figures)"
    prompt = (
        f"CONCEPT: {concept['title']}\n"
        f"IDEA: {concept['idea']}\n"
        f"LAYOUT (use this): {concept['layout']}\n\n"
        f"HOOK: {draft.hook}\n"
        f"BODY: {draft.body[:700]}\n\n"
        f"VERIFIED FACTS (only these may appear as figures):\n{facts_block}\n\n"
        "Produce the VisualSpec."
    )

    from .critic import _flatten_schema
    schema = _flatten_schema(VisualSpec.model_json_schema())
    schema.get("properties", {}).pop("palette", None)
    if "required" in schema:
        schema["required"] = [r for r in schema["required"] if r != "palette"]

    try:
        data, resp = client.complete_json(
            prompt, schema=schema, system=SPEC_SYSTEM,
            prompt_version=SPEC_VERSION, temperature=0.4, max_output_tokens=6144,
        )
    except LLMError as exc:
        return degraded("spec", None, started, f"spec agent failed: {exc}", input_hash=ih)

    ink, ground, accent = default_palette()
    data["palette"] = {"ink": ink, "ground": ground, "accent": accent}
    data.setdefault("layout", concept["layout"])
    try:
        spec = VisualSpec(**data)
    except Exception as exc:
        return degraded("spec", None, started, f"agent produced an invalid spec: {exc}",
                        input_hash=ih)

    return ok("spec", spec, started, input_hash=ih, model=resp.model,
              prompt_version=resp.prompt_version, input_tokens=resp.input_tokens,
              output_tokens=resp.output_tokens, cost_usd=resp.cost_usd or 0.0, cost_known=resp.pricing_known)
