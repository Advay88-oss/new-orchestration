#!/usr/bin/env python3
"""AI Campaign Strategy & Execution Engine.

Not a post generator — a campaign planner. It researches, reasons, plans a whole
campaign, runs an adversarial specialist panel that debates and ranks competing
concepts, then expands the winner into a complete chronological operating plan
(per-step Day -> Platform -> Objective -> Audience -> Strategy -> Content -> Hook
-> Visual -> CTA -> Incentive -> Expected Action -> KPI), justifies every channel
(including Galxe quests when relevant), drafts the key content/creative, and
persists the run so it is fully traceable in the dashboard.

Tenant-aware (PIPELINE_TENANT_NAME + OKF_BUNDLE). Runs on the same capped Gemini
brain as the content pipeline (PIPELINE_BRAIN=gemini) or Claude.

    PIPELINE_BRAIN=gemini python pipeline/scripts/campaign_engine.py
    PIPELINE_BRAIN=gemini PIPELINE_TENANT_NAME=Auri \
      PIPELINE_CONFIG=okf-auri/marketing_config.json OKF_BUNDLE=okf-auri \
      python pipeline/scripts/campaign_engine.py
"""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from trendjack_news_orchestrator import (  # noqa: E402
    REPO, STATE, call_vertex, extract_json, load_scout_signals, load_tenant_facts,
    live_reset, live_emit, live_finalize,
)

TENANT = os.environ.get("PIPELINE_TENANT_NAME", "Vanna")
def _default_bundle() -> Path:
    p = REPO / "okf"
    if p.exists():
        return p
    return REPO / "pipeline" / "system1_extracted" / "okf"

BUNDLE = Path(os.environ.get("OKF_BUNDLE") or _default_bundle())
# Optional schedule constraint. Empty = the planner picks the window from research;
# set e.g. "1 week" to compress the whole campaign into a single 7-day sprint.
CAMPAIGN_WINDOW = os.environ.get("CAMPAIGN_WINDOW", "").strip()
CAMPAIGN_DIR = BUNDLE / "launches" / "2026-launch"


def _read_dir(rel: str, limit: int = 5, cap: int = 900) -> str:
    d = BUNDLE / rel
    out = []
    if d.is_dir():
        for f in sorted(d.glob("*.md"))[:limit]:
            try:
                out.append(f"### {f.stem}\n{f.read_text(encoding='utf-8')[:cap]}")
            except Exception:
                pass
    return "\n\n".join(out)


def build_research_brief() -> tuple[str, list[dict]]:
    """Assemble the raw research: real social signals + the OKF knowledge base."""
    live_emit("research-analyst", "step", "Research: gathering real signals + knowledge base")
    signals = load_scout_signals(TENANT)  # real Reddit/Twitter/RSS, engagement-ranked
    sig_txt = "\n".join(
        f"- [{s.get('description','')[:140]}]" for s in signals[:10]
    )
    parts = [
        f"# {TENANT} research brief",
        f"\n## Live social signals (real, engagement-ranked)\n{sig_txt or '(none)'}",
        f"\n## Positioning\n{_read_dir('positioning')}",
        f"\n## Facts (quotable, claim-safe)\n{_read_dir('facts', limit=4, cap=700)}",
        f"\n## Narrative arcs\n{_read_dir('arcs', limit=4, cap=400)}",
        f"\n## Competitors\n{_read_dir('competitors', limit=5, cap=700)}",
        f"\n## Prior launch plans (context, do not merely repeat)\n{_read_dir('launches/2026-launch', limit=3, cap=700)}",
    ]
    return "\n".join(parts), signals


def shared_context() -> str:
    ctx = ""
    for rel in ("pipeline/buzz-pack/campaign-doctrine.md", "pipeline/system1_extracted/buzz-pack/campaign-doctrine.md"):
        p = REPO / rel
        if p.exists():
            ctx += "\n\n" + p.read_text(encoding="utf-8")[:1800]
    try:
        from learning import learning_brief
        ctx += learning_brief()
    except Exception:
        pass
    ctx += load_tenant_facts(TENANT, BUNDLE)
    return ctx


def main() -> int:
    print("=" * 60)
    print(f"AI CAMPAIGN ENGINE — {TENANT}")
    print("=" * 60)
    brain = os.environ.get("PIPELINE_BRAIN", "claude").lower()
    if brain == "gemini":
        try:
            with urllib.request.urlopen("http://127.0.0.1:8900/_spend", timeout=5) as r:
                sp = json.loads(r.read())
                print(f"Spend: ${sp['spent_usd']:.4f}/${sp['cap_usd']:.2f} (${sp['remaining_usd']:.4f} left)")
                if sp["remaining_usd"] <= 0.05:
                    print("Budget exhausted."); return 1
        except Exception as e:
            print(f"Spend proxy down: {e}"); return 1

    live_reset(TENANT, "campaign planning")
    brief, signals = build_research_brief()
    ctx = shared_context()

    # ---- 1. Research -> strategy intelligence (spec §1) -------------------
    print("\n=== 1. Research → strategy intelligence ===")
    live_emit("research-analyst", "step", "Analyzing what strategies/formats/hooks/incentives actually convert")
    intel = extract_json(call_vertex(
        f"You are {TENANT}'s head of campaign research. Extract the underlying MECHANISMS "
        f"behind what works — never copy competitors, extract the strategy.\n\n{ctx}",
        f"""From this research, produce campaign intelligence for {TENANT}. Return clean JSON:
{{
 "strategies_in_use": ["..."],
 "formats_that_work": ["..."],
 "video_short_hooks_that_work": ["..."],
 "when_premium_visuals": "when premium visuals are worth it vs cheap",
 "intro_by_stage": {{"awareness":"...","launch":"..."}},
 "platform_audience_fit": {{"x":"...","reddit":"...","linkedin":"...","youtube":"...","galxe":"..."}},
 "incentives_that_convert": ["..."],
 "conversion_mechanisms": ["what actually converts vs vanity engagement"]
}}

RESEARCH:
{brief[:6000]}""",
        temperature=0.4,
    ))
    log_json("research-analyst", "Strategy Intelligence", intel)

    # ---- 2. Three competing campaign concepts (spec §2) -------------------
    print("\n=== 2. Competing campaign concepts ===")
    arcs = [("capital-lens", "capital efficiency / make idle assets work"),
            ("risk-lens", "risk / control / safety"),
            ("agentic-lens", "the frontier wedge / what only we enable")]
    concepts = []
    for cid, lens in arcs:
        live_emit(f"strategist-{cid}", "step", f"Proposing a full campaign from the {lens} angle")
        c = extract_json(call_vertex(
            f"You are a {TENANT} campaign strategist arguing the '{lens}' angle. Propose a WHOLE "
            f"campaign (not a post). Be claim-safe (testnet: no token/mainnet/production-grade for Vanna).\n\n{ctx}",
            f"""Using this intelligence, propose ONE original {TENANT} campaign from your angle. Return JSON:
{{
 "id": "{cid}",
 "name": "short campaign name",
 "thesis": "the one-sentence idea",
 "why_now": "why this campaign, why now (cite a real signal)",
 "audience": "who it's for (ICP)",
 "primary_platform": "the lead channel + why",
 "core_message": "...",
 "signature_hook": "the hook that leads",
 "incentive": "the incentive/mechanism that drives a real action (or 'none' + why)",
 "funnel_emphasis": "which of Awareness/Education/Curiosity/Reveal/Proof/Conversion/Retention/Referral this leans on",
 "conversion_action": "the real business action it drives (not vanity)"
}}

INTELLIGENCE: {json.dumps(intel)[:2500]}
KEY FACTS: {brief[3000:5000]}""",
            temperature=0.8,
        ))
        c["id"] = cid
        concepts.append(c)
        log_json(f"strategist-{cid}", "Campaign Concept", c)

    # ---- 6. Specialist panel debate + ranking (spec §6) -------------------
    print("\n=== 3. Specialist panel (debate) ===")
    PANEL = [
        ("trend-scout", "Trend Scout", "Is each concept riding a REAL current trend? Cite live signals; penalize stale angles."),
        ("competitor-agent", "Competitor Analyst", "Is it differentiated or derivative? Extract mechanism — flag anything that just copies a rival."),
        ("growth-agent", "Growth Lead", "Will it ACQUIRE users, not just impressions? Where is the acquisition loop?"),
        ("content-agent", "Content Lead", "Will the hooks/content land on the chosen platforms?"),
        ("creative-agent", "Creative Director", "Is the visual/video concept strong enough to stop the scroll? Are premium visuals justified?"),
        ("conversion-agent", "Conversion Strategist", "Will it convert to the real action, not vanity engagement?"),
        ("risk-agent", "Risk Officer", "What could fail? Claim-safety, platform risk, incentive abuse, reputational risk."),
    ]
    concept_blob = json.dumps([{k: c.get(k) for k in ("id", "name", "thesis", "primary_platform", "signature_hook", "incentive", "conversion_action")} for c in concepts])
    opinions = []
    for aid, title, mandate in PANEL:
        live_emit(aid, "step", f"{title} evaluating the {len(concepts)} concepts")
        op = extract_json(call_vertex(
            f"You are the {title} on {TENANT}'s campaign board. Mandate: {mandate} Be adversarial and specific.\n\n{ctx}",
            f"""Score EACH concept 0-10 from your lens and name concerns. Return JSON:
{{"scores": {{"capital-lens": 0, "risk-lens": 0, "agentic-lens": 0}},
  "top_pick": "id", "concerns": ["..."], "verdict": "one-line take"}}

CONCEPTS: {concept_blob}""",
            temperature=0.5,
        ))
        op["agent"] = title
        opinions.append(op)
        log_json(aid, f"{title} Opinion", op)

    # Aggregate scores + a ranking/decision agent
    print("\n=== 4. Ranking → final decision ===")
    live_emit("campaign-director", "step", "Aggregating panel, ranking concepts, deciding")
    totals = {c["id"]: 0.0 for c in concepts}
    for op in opinions:
        for cid, sc in (op.get("scores") or {}).items():
            if cid in totals:
                try:
                    totals[cid] += float(sc)
                except Exception:
                    pass
    decision = extract_json(call_vertex(
        f"You are {TENANT}'s campaign director. Weigh the panel, resolve disagreements, pick ONE winner "
        f"and say why it beats the others. You may graft the best element of a runner-up.\n\n{ctx}",
        f"""Rank the concepts and decide. Return JSON:
{{"ranking": [{{"id":"...","name":"...","panel_score": 0, "why":"..."}}],
  "winner_id": "...", "rationale": "why this wins", "graft": "best idea to borrow from a runner-up or 'none'"}}

CONCEPTS: {concept_blob}
PANEL_TOTALS (sum of 0-10 across 7 agents): {json.dumps(totals)}
PANEL_OPINIONS: {json.dumps([{ 'agent': o.get('agent'), 'top': o.get('top_pick'), 'concerns': o.get('concerns'), 'verdict': o.get('verdict')} for o in opinions])[:3500]}""",
        temperature=0.3,
    ))
    log_json("campaign-director", "Ranking & Decision", decision)
    winner = next((c for c in concepts if c["id"] == decision.get("winner_id")), concepts[0])

    # ---- 3+4. Full chronological plan + platform/incentive intel ----------
    # Split into two calls: a big single JSON (funnel + platforms + galxe + full
    # timeline) overflows the model's output limit and truncates to unparseable.
    print("\n=== 5a. Funnel + platform + incentive intelligence ===")
    live_emit("campaign-planner", "step", f"Mapping the funnel, channels and incentives for '{winner.get('name')}'")
    scaffold = extract_json(call_vertex(
        f"You are {TENANT}'s campaign planner. Map the funnel and justify every channel and incentive for the "
        f"winning concept. Force nothing; justify each. Claim-safe.\n\n{ctx}",
        f"""Return JSON only:
{{
 "funnel_map": {{"awareness":"...","education":"...","curiosity":"...","reveal":"...","proof":"...","conversion":"...","retention":"...","referral":"..."}},
 "platform_intelligence": [{{"platform":"X/Reddit/LinkedIn/YouTube/TikTok/ProductHunt/Email/Communities/Galxe","use": true, "why":"justify use or skip","role_in_funnel":"..."}}],
 "galxe": {{"relevant": true, "why":"why Galxe (or why not)","quest_action":"action to incentivise","reward_mechanism":"Points/OATs/NFT/MysteryBox/Token/referral/sequential","funnel_fit":"where in the funnel"}},
 "primary_kpis": ["real business KPIs, not vanity"]
}}
WINNING CONCEPT: {json.dumps(winner)}
DIRECTOR RATIONALE: {decision.get('rationale','')}""",
        temperature=0.5, max_tokens=6000,
    ))

    print("\n=== 5b. Chronological timeline ===")
    live_emit("campaign-planner", "step", "Sequencing the day-by-day operating timeline")
    if CAMPAIGN_WINDOW:
        window_rule = (f"HARD CONSTRAINT: the ENTIRE campaign must fit in a {CAMPAIGN_WINDOW} window. "
                       f"Use days within that window only (e.g. 'Day 1' … 'Day 7' for one week), one step per "
                       f"active day, daily cadence, no pre/post-launch weeks. 5-7 steps.")
        example_day = "Day 1"
    else:
        window_rule = "Determine the real schedule from the research — do not copy a template. 6-9 steps."
        example_day = "Day -14"
    tl = extract_json(call_vertex(
        f"You are {TENANT}'s campaign planner. Produce the chronological execution timeline. {window_rule} "
        f"Keep each field to ONE tight sentence. Claim-safe.\n\n{ctx}",
        f"""Return JSON only, concise fields. {window_rule}
{{"timeline": [
   {{"day":"{example_day}","platform":"...","objective":"Awareness/Education/Curiosity/Reveal/Proof/Conversion/Retention/Referral","audience":"...","strategy":"...","content":"what to post","hook":"...","visual":"describe; premium yes/no + why","cta":"...","incentive":"...","expected_action":"...","kpi":"measurable KPI"}}
]}}
CAMPAIGN: {winner.get('name')} — {winner.get('thesis')}
FUNNEL: {json.dumps(scaffold.get('funnel_map', {}))[:900]}
GALXE: {json.dumps(scaffold.get('galxe', {}))[:400]}""",
        temperature=0.5, max_tokens=14000,
    ))
    plan = {**scaffold, "timeline": tl.get("timeline", [])}
    log_json("campaign-planner", "Operating Plan", {"timeline_steps": len(plan.get("timeline", [])), "galxe": plan.get("galxe", {}).get("relevant")})

    # ---- 5. Content + creative for the key steps (spec §5) ----------------
    print("\n=== 6. Content + creative drafts ===")
    key_steps = (plan.get("timeline") or [])[:3]
    for i, st in enumerate(key_steps):
        live_emit("content-agent", "step", f"Drafting content for {st.get('day')} ({st.get('platform')})")
        draft = extract_json(call_vertex(
            f"You are {TENANT}'s content+creative agent. Write the actual asset for one campaign step, on-brand and claim-safe.\n\n{ctx}",
            f"""Return JSON:
{{"copy":"the actual post/script/thread/caption ready to publish","creative_direction":"visual/video concept + why","format":"post/thread/short-video/launch-video/email"}}

STEP: {json.dumps(st)}
CAMPAIGN: {winner.get('name')} — {winner.get('thesis')}""",
            temperature=0.7,
        ))
        st["_draft"] = draft
        log_json("content-agent", f"Asset for {st.get('day')}", draft)

    # ---- 7. Persist the run data FIRST, then render the document ----------
    # (Persist before rendering so a formatting bug can never lose an expensive
    #  multi-agent run — the JSON is the source of truth; the .md is a view.)
    stamp = time.strftime("%Y%m%d-%H%M%S", time.gmtime())
    out_json = STATE / "campaigns"
    out_json.mkdir(parents=True, exist_ok=True)
    (out_json / f"{TENANT.lower()}-{stamp}.json").write_text(
        json.dumps({"tenant": TENANT, "intel": intel, "concepts": concepts, "opinions": opinions,
                    "decision": decision, "winner": winner, "plan": plan}, ensure_ascii=False, indent=2),
        encoding="utf-8")
    CAMPAIGN_DIR.mkdir(parents=True, exist_ok=True)
    out_md = CAMPAIGN_DIR / f"campaign-operating-plan-{stamp}.md"
    try:
        out_md.write_text(render_plan_doc(TENANT, intel, concepts, opinions, totals, decision, winner, plan), encoding="utf-8")
    except Exception as e:
        print(f"⚠️ doc render failed ({e}); data safe in {out_json}")

    live_finalize("completed", kind="campaign", pipeline=f"{TENANT} campaign engine",
                  winner_hook=winner.get("name"), winner_body=winner.get("thesis"),
                  trend=(signals[0].get("title") if signals else ""),
                  plan_file=str(out_md), timeline_steps=len(plan.get("timeline", [])))
    print(f"\n✅ Campaign operating plan → {out_md}")
    print(f"   Winner: {winner.get('name')} | steps: {len(plan.get('timeline', []))} | Galxe: {plan.get('galxe',{}).get('relevant')}")
    return 0


def log_json(agent, label, obj):
    from trendjack_news_orchestrator import log_agent_activity
    log_agent_activity(agent, f"{label}:\n{json.dumps(obj, indent=2, ensure_ascii=False)}")


def sj(xs, n=6) -> str:
    """Safe join: models sometimes return list items as dicts, not strings."""
    return ', '.join(str(x) for x in (xs or [])[:n])


def render_plan_doc(tenant, intel, concepts, opinions, totals, decision, winner, plan) -> str:
    L = []
    L.append(f"# {tenant} — Campaign Operating Plan")
    L.append(f"_Generated {time.strftime('%Y-%m-%d %H:%M UTC', time.gmtime())} · research → strategy → panel debate → plan → content_\n")

    L.append("## 1. Research → strategy intelligence")
    L.append(f"- **Strategies in use:** {sj(intel.get('strategies_in_use'))}")
    L.append(f"- **Formats that work:** {sj(intel.get('formats_that_work'))}")
    L.append(f"- **Video/short hooks:** {sj(intel.get('video_short_hooks_that_work'), 5)}")
    L.append(f"- **When premium visuals:** {intel.get('when_premium_visuals','')}")
    L.append(f"- **Incentives that convert:** {sj(intel.get('incentives_that_convert'), 5)}")
    L.append(f"- **Conversion mechanisms:** {sj(intel.get('conversion_mechanisms'), 5)}\n")

    L.append("## 2. Competing campaign concepts")
    for c in concepts:
        L.append(f"### {c.get('name')} `({c.get('id')})` — score {totals.get(c.get('id'),0):.0f}/70")
        L.append(f"- **Thesis:** {c.get('thesis')}")
        L.append(f"- **Why now:** {c.get('why_now')}")
        L.append(f"- **Audience:** {c.get('audience')} · **Platform:** {c.get('primary_platform')}")
        L.append(f"- **Hook:** {c.get('signature_hook')} · **Incentive:** {c.get('incentive')}")
        L.append(f"- **Converts via:** {c.get('conversion_action')}\n")

    L.append("## 3. Agent panel — opinions & debate")
    for op in opinions:
        L.append(f"- **{op.get('agent')}** → top: `{op.get('top_pick')}` — {op.get('verdict','')}")
        if op.get("concerns"):
            L.append(f"    - concerns: {sj(op.get('concerns'), 3)}")
    L.append("")

    L.append("## 4. Ranking → final decision")
    for r in decision.get("ranking", []):
        L.append(f"1. **{r.get('name')}** — {r.get('panel_score','')} — {r.get('why','')}")
    L.append(f"\n**WINNER: {winner.get('name')}** — {decision.get('rationale','')}")
    if decision.get("graft") and decision.get("graft") != "none":
        L.append(f"\n_Grafted from a runner-up:_ {decision.get('graft')}")
    L.append("")

    L.append("## 5. The chosen campaign")
    L.append(f"- **What:** {winner.get('name')} — {winner.get('thesis')}")
    L.append(f"- **Why:** {winner.get('why_now')}")
    L.append(f"- **Who:** {winner.get('audience')}")
    L.append(f"- **Message:** {winner.get('core_message')}")
    L.append(f"- **Hook:** {winner.get('signature_hook')}")
    L.append(f"- **Incentive:** {winner.get('incentive')}")
    L.append(f"- **Real conversion action:** {winner.get('conversion_action')}\n")

    fm = plan.get("funnel_map", {})
    if fm:
        L.append("## 6. Funnel map")
        for k in ("awareness", "education", "curiosity", "reveal", "proof", "conversion", "retention", "referral"):
            v = fm.get(k)
            if not v:
                continue
            if isinstance(v, dict):
                bits = [f"_{kk}:_ {vv}" for kk, vv in v.items() if vv and kk != "audience"]
                v = " · ".join(str(b) for b in bits)
            L.append(f"- **{k.title()}:** {v}")
        L.append("")

    L.append("## 7. Platform & incentive intelligence")
    for p in plan.get("platform_intelligence", []):
        mark = "✅ use" if p.get("use") else "⛔ skip"
        L.append(f"- **{p.get('platform')}** — {mark}: {p.get('why','')} _(funnel: {p.get('role_in_funnel','')})_")
    g = plan.get("galxe", {})
    if g:
        L.append(f"\n**Galxe:** {'RELEVANT ✅' if g.get('relevant') else 'not used'} — {g.get('why','')}")
        if g.get("relevant"):
            L.append(f"- **Quest action:** {g.get('quest_action')}")
            L.append(f"- **Reward mechanism:** {g.get('reward_mechanism')}")
            L.append(f"- **Funnel fit:** {g.get('funnel_fit')}")
    L.append("")

    L.append("## 8. Full chronological operating plan")
    L.append("| Day | Platform | Objective | Audience | Strategy | Content | Hook | Visual | CTA | Incentive | Expected action | KPI |")
    L.append("|---|---|---|---|---|---|---|---|---|---|---|---|")
    for s in plan.get("timeline", []):
        row = [s.get("day", ""), s.get("platform", ""), s.get("objective", ""), s.get("audience", ""),
               s.get("strategy", ""), s.get("content", ""), s.get("hook", ""), s.get("visual", ""),
               s.get("cta", ""), s.get("incentive", ""), s.get("expected_action", ""), s.get("kpi", "")]
        row = [str(x).replace("|", "/").replace("\n", " ")[:90] for x in row]
        L.append("| " + " | ".join(row) + " |")
    L.append("")

    L.append("## 9. Content & creative drafts (key steps)")
    for s in plan.get("timeline", [])[:3]:
        d = s.get("_draft") or {}
        if d:
            L.append(f"### {s.get('day')} · {s.get('platform')} · {d.get('format','')}")
            L.append(f"> {d.get('copy','')}")
            L.append(f"\n_Creative:_ {d.get('creative_direction','')}\n")

    L.append("## 10. KPIs & measurement")
    L.append(f"- **Primary KPIs:** {', '.join(plan.get('primary_kpis', []))}")
    L.append("- Each result feeds the learning loop; the next campaign is scored against these.\n")
    L.append("_Claim discipline enforced throughout. Every channel justified — nothing forced._")
    return "\n".join(L)


if __name__ == "__main__":
    sys.exit(main())
