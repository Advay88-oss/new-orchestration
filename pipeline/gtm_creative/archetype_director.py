"""Choosing the archetype — the part that actually stops the monotony.

Better prompting was never going to fix "every post looks the same", because
the composition was not being chosen at all: `visual_creative_director.py` held
a five-branch if/else on keywords and every risk campaign got byte-identical
art direction.

So selection is the mechanism, and it has two halves:

  **A07 picks and fills.** The creative director reads the copy, chooses one
  archetype from the registry, and fills that archetype's own slots — the bar's
  segments, the timeline's steps, the threshold's two callouts. Different
  archetypes want different content, which is precisely why one template could
  never serve them.

  **The last two are removed before it chooses.** Not discouraged in a prompt —
  removed from the candidate list. A model asked nicely not to repeat itself
  will repeat itself; a model handed nine options instead of eleven cannot pick
  the two that are gone.

Half the archetypes never reach an image model. A worked calculation and a
proportional bar are arithmetic, and arithmetic drawn by an image model is
arithmetic you cannot trust.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable, Optional

from pipeline.gtm_creative import archetypes as A
from pipeline.gtm_creative import premium_archetypes as P
from pipeline.gtm_os import agent_runtime as R
from pipeline.gtm_os.vanna_knowledge import prompt_block as _prompt_block

AGENT = "A07_creative_director"
STATE = Path(__file__).resolve().parents[2] / "pipeline" / "state"
RECENT_FILE = STATE / "recent_archetypes.json"
KEEP_RECENT = 4


# --------------------------------------------------------------------------
# Registry
# --------------------------------------------------------------------------

ARCHETYPES: dict[str, dict[str, Any]] = {
    "P1_hero_metric": {
        "name": "Hero Metric",
        "when": "ONE number is the whole point — a floor, a latency, a fee, a "
                "count. Prefer this whenever the post has a single figure "
                "worth staring at. Square card.",
        "generated": True,
        "slots": '{"eyebrow": str, "metric": str, "descriptor": str}',
        "notes": "metric is the figure alone and nothing else: \"1.10x\", "
                 "\"0.00014 XLM\", \"~320ms\". descriptor is one sentence "
                 "under 12 words saying what it is. eyebrow is the context "
                 "line, e.g. \"Vanna - Stellar Soroban Testnet\".",
    },
    "P2_announcement": {
        "name": "Announcement",
        "when": "A status or a launch: something is now live, shipped, or "
                "integrated. Not an explanation — a statement.",
        "generated": True,
        "slots": '{"term": str, "status_prefix": str, "status_accent": str, '
                 '"status_suffix": str, "partners": [str], "footnote": str}',
        "notes": "term is the thing being announced, one or two words, set "
                 "large. The status line reads prefix + accent + suffix and "
                 "the accent is the only coloured words, e.g. prefix "
                 "\"Isolated credit is\", accent \"live on Soroban "
                 "testnet\", suffix \"now\". partners is 1-2 names, Vanna "
                 "first; never claim a partnership that does not exist.",
    },
    "P3_product_card": {
        "name": "Product Card",
        "when": "The product answering a question a user would actually ask. "
                "Shows a real value inside a UI card.",
        "generated": True,
        "slots": '{"wordmark": str, "question": str, "card_label": str, '
                 '"card_value": str, "card_sub": str, "chip": str, '
                 '"chip_note": str}',
        "notes": "question is the headline, phrased as a question, 5-9 "
                 "words, and it must be about the founder's subject. "
                 "card_value is the figure ALONE and short — \"1.42x\", "
                 "\"~5s\", \"0.00001 XLM\" — never a sentence; it is set "
                 "very large and a long one shrinks until it no longer reads "
                 "as the hero. card_label names it in 2-3 words "
                 "(\"Health factor\"). card_sub is one line under 8 words. "
                 "chip is the object it applies to, 1-2 words "
                 "(\"SmartAccount\", \"USDC / XLM\"); chip_note is 2-3 "
                 "words under it. Every figure must be true of testnet.",
    },
    "A2_product": {
        "name": "Product Frame",
        "when": "Something a person does in the app — depositing, withdrawing, "
                "checking a position before signing.",
        "generated": False,
        "slots": '{"eyebrow": str, "headline": str, "deck": str, "panel_title": str, '
                 '"rows": [[str, str]], "primary": [str, str], '
                 '"footnote": str}',
        "notes": "2-3 context rows of [label, value], then primary is the one "
                 "line the post is about, as [label, value]. Every figure must "
                 "be arithmetically consistent with the others.",
    },
    "A9_lockup": {
        "name": "Ecosystem Lockup",
        "when": "An integration or a relationship between named protocols.",
        "generated": False,
        "slots": '{"names": [str], "statement": str, "sub": str, '
                 '"notes": [[str, str]], "footnote": str}',
        "notes": "names is 2-3 protocols, Vanna first. statement is the one "
                 "line, under ten words. Exactly three notes of [term, gloss].",
    },
    "A3_threshold": {
        "name": "Threshold",
        "when": "A boundary the reader should understand — a floor, a trigger, "
                "a limit the system defends.",
        "generated": True,
        "slots": '{"headline": str, "deck": str, "value_label": str, '
                 '"floor_label": str, "footnote": str}',
        "notes": "Headline MUST be under seven words: the right third of this "
                 "canvas is occupied by the figure. value_label and "
                 "floor_label are short callouts, 3-5 words, each naming a "
                 "level. Include the figure in the label text.",
    },
    "A4_isolation": {
        "name": "Isolation Grid",
        "when": "Containment: one account's problem not becoming everyone's.",
        "generated": True,
        "slots": '{"headline": str, "deck": str, "stat_value": str, '
                 '"stat_label": str, "footnote": str}',
        "notes": "stat_value is ONE short figure, four characters at most. "
                 "stat_label explains it in under nine words.",
    },
    "A5_round_trip": {
        "name": "Round Trip",
        "when": "Capital leaving and returning — composability, external "
                "positions still counting.",
        "generated": True,
        "slots": '{"headline": str, "deck": str, "labels": [str]}',
        "notes": "Exactly three short labels, two or three words each.",
    },
    "A6_ledger": {
        "name": "Ledger",
        "when": "A calculation the reader can follow line by line.",
        "generated": False,
        "slots": '{"eyebrow": str, "headline": str, "rows": [[str, str]], '
                 '"verdict": [str, str], "footnote": str}',
        "notes": "3-4 rows of [label, value]. verdict is [label, result]. "
                 "Every figure must be arithmetically consistent.",
    },
    "A7_composition": {
        "name": "Composition Bar",
        "when": "What something is made of — a split, a breakdown, a mix.",
        "generated": False,
        "slots": '{"eyebrow": str, "headline": str, "deck": str, '
                 '"segments": [[str, number]], "total_label": str, '
                 '"footnote": str}',
        "notes": "2-4 segments of [label, weight]. The weights are printed "
                 "as percentages, so they must be REAL figures stated in the "
                 "post or the knowledge pack. Never an illustrative or "
                 "invented split: if no real breakdown exists, choose a "
                 "different archetype. eyebrow is the topic in 1-3 words "
                 "(e.g. \"Liquidity\").",
    },
    "A8_sequence": {
        "name": "Sequence",
        "when": "Something that happens in ordered steps, especially over time.",
        "generated": True,
        "slots": '{"headline": str, "deck": str, "steps": [[str, str]], '
                 '"footnote": str}',
        "notes": "Exactly four steps of [title, subtitle]. Titles under five "
                 "words, subtitles under six.",
    },
    "A13_containment": {
        "name": "Containment Figure",
        "when": "Nesting — something held inside something else, still owned.",
        "generated": True,
        "slots": '{"headline": str, "deck": str, "notes": [[str, str]], '
                 '"footnote": str}',
        "notes": "Exactly three notes of [term, gloss].",
    },
    "A14_comparison": {
        "name": "Comparison",
        "when": "Two mechanisms, one axis of difference.",
        "generated": True,
        "slots": '{"headline": str, "deck": str, "left_label": str, '
                 '"right_label": str, "footnote": str}',
        "notes": "Never name a competitor. The left side is the generic "
                 "mechanism, the right is Vanna.",
    },
}

RENDERERS: dict[str, Callable[..., Path]] = {
    "A2_product": A.render_a2_product,
    "A9_lockup": A.render_a9_lockup,
    "A3_threshold": A.render_a3_threshold,
    "A4_isolation": A.render_a4_isolation,
    "A5_round_trip": A.render_a5_round_trip,
    "A6_ledger": A.render_a6_ledger,
    "A7_composition": A.render_a7_composition,
    "A8_sequence": A.render_a8_sequence,
    "A13_containment": A.render_a13_containment,
    "A14_comparison": A.render_a14_comparison,
    "P1_hero_metric": P.render_p1_hero_metric,
    "P2_announcement": P.render_p2_announcement,
    "P3_product_card": P.render_p3_product_card,
}

# Archetypes whose FIGURE is drawn by the image model, with labels composited
# at fixed positions on top. The model decides where its shapes land and the
# code cannot know, so labels collide with them: an A14 shipped with both
# column headings buried under the boxes, and the judge rejected the figure as
# abstract geometry. Every other archetype is laid out entirely in code — the
# model supplies light at most — so nothing in it can overlap by accident.
# These stay renderable (re-renders, demos); they are not offered to the
# director until their figures are drawn in code too.
MODEL_DRAWN_FIGURE = frozenset({
    "A3_threshold", "A4_isolation", "A5_round_trip",
    "A8_sequence", "A13_containment", "A14_comparison",
})

POSTERS = ("P1_hero_metric", "P2_announcement", "P3_product_card")

# Segment colours are assigned here, not by the model: the accent ramp is a
# brand decision and a model asked for hex values invents them.
_SEGMENT_RAMP = [A.VIOLET, A.VIOLET_LIGHT, (86, 80, 120), (58, 54, 82)]


# --------------------------------------------------------------------------
# Recency
# --------------------------------------------------------------------------

def recent() -> list[str]:
    try:
        return [str(x) for x in json.loads(RECENT_FILE.read_text(encoding="utf-8"))]
    except Exception:                               # noqa: BLE001 — boundary
        return []


def remember(archetype: str) -> None:
    hist = [archetype] + [a for a in recent() if a != archetype]
    RECENT_FILE.parent.mkdir(parents=True, exist_ok=True)
    RECENT_FILE.write_text(json.dumps(hist[:KEEP_RECENT + 2]), encoding="utf-8")


def blocked_recent() -> list[str]:
    """The recently used archetypes the director may not pick this time.

    Blocking the last four with only three posters in the registry meant two
    posts in a row could lock every poster out, and the director was pushed
    onto a schematic the post did not want. Variety must never cost the post
    its poster: the least recently used poster is always released.
    """
    blocked = [a for a in recent()[:KEEP_RECENT]
               if a in ARCHETYPES and a not in MODEL_DRAWN_FIGURE]
    if all(p in blocked for p in POSTERS):
        blocked.remove(max(POSTERS, key=blocked.index))
    return blocked


def candidates() -> dict[str, dict[str, Any]]:
    """Code-laid-out archetypes, minus the recently used."""
    blocked = set(blocked_recent())
    pool = {k: v for k, v in ARCHETYPES.items() if k not in MODEL_DRAWN_FIGURE}
    # Archetypes the founder has consistently killed (>= 3 reviewed runs,
    # approval under 20%) leave the pool. A prompt asking the model to avoid
    # them is a request; removing them is the learning actually taking effect.
    try:
        from pipeline.gtm_learning.preferences import retired
        gone = retired("visual_archetype")
        if gone and len(set(pool) - gone) >= 2:
            pool = {k: v for k, v in pool.items() if k not in gone}
    except Exception:                               # noqa: BLE001 — boundary
        pass
    open_set = {k: v for k, v in pool.items() if k not in blocked}
    # Never hand back an empty set; the oldest block lapses rather than the
    # run failing.
    return open_set or pool


# --------------------------------------------------------------------------
# Direction
# --------------------------------------------------------------------------

SYSTEM = (
    "You are Vanna's creative director. Vanna is composable credit "
    "infrastructure on Stellar Soroban TESTNET.\n\n"
    "You choose ONE visual archetype for a post and write the words that go "
    "in it. You are not describing an image — the archetype already fixes the "
    "composition. Your job is the choice and the copy.\n\n"
    "PREFER THE POSTER ARCHETYPES — P1_hero_metric, P2_announcement, "
    "P3_product_card. They read as brand posts: one idea, set large, with "
    "real brand furniture. The A-series are structured layouts; choose one "
    "only when the post's argument needs that structure — a product action "
    "(A2), named integrations (A9), a calculation (A6), a breakdown (A7). If "
    "a post can be carried by one number, one status, or one product value, "
    "a poster is the better asset.\n\n"
    "Rules:\n"
    "- The asset carries THIS POST's argument, not a new one. The headline "
    "restates the post's hook in fewer words; the deck and every figure come "
    "from the post body. Use the post's own terms: if the post says "
    "'isolated SmartAccount', the asset does not say 'unified' or 'netting'. "
    "A reader who sees the image and then the text must find the same claim "
    "twice. The founder's SUBJECT sets the topic; the POST sets the claim.\n"
    "- An explainer (the founder asked to explain a concept) wants the "
    "reader's question or the concept's structure — P3's question, or a "
    "structured layout — not a hero metric. Use P1 only when one number IS "
    "the subject, not because the post happens to contain one.\n"
    "- Pick the archetype whose shape IS the argument. A calculation wants a "
    "ledger; a boundary wants a threshold; a breakdown wants a bar. Do not "
    "pick on how interesting the picture sounds.\n"
    "- The headline is the one idea, under nine words, no colon, no hype. It "
    "should read as a sentence a competent engineer would say out loud.\n"
    "- The deck is ONE line that earns the headline. Never two ideas.\n"
    "- Every figure you write must be true of Vanna and checkable. If you are "
    "unsure of a number, state the mechanism without it.\n"
    "- Never imply mainnet. Vanna is on testnet.\n"
    "- Never name a competitor.\n"
    "- Footnotes carry the source and any caveat, quietly.\n"
    "- An `eyebrow` slot names THIS post's topic in 1-3 words ('Liquidity', "
    "'Health factor'); the network suffix is added for you.\n"
    "- Never print an illustrative, example or invented figure. Every "
    "number on the asset must be real and true of Vanna on testnet.\n\n"

    "HOW THESE ARE BUILT, and why your word counts matter:\n"
    "  An image model renders the background as light alone — a gradient "
    "wash, nothing in it. Every word, panel, figure and chip is then set by "
    "code at a measured position. Nothing is drawn behind your type and "
    "nothing will be added to fill space, so a long string does not shrink to "
    "fit gracefully: it either sets smaller than its neighbours or crowds "
    "them. The composition is generous when the copy is short.\n"
    "  Do NOT write art direction. Do not ask for an object, a diagram, a "
    "scene or a metaphor to be depicted — nothing you describe will be drawn. "
    "The argument is carried entirely by the words you choose.\n\n"

    "Return strict JSON."
)


def _learned_block(options: list[str]) -> str:
    """The founder's record with each open archetype, ranked by a Thompson
    draw so that a well-approved archetype usually leads but an untried one
    can still come first. Empty until there is feedback."""
    try:
        from pipeline.gtm_learning import preferences as P
    except Exception:                               # noqa: BLE001 — boundary
        return ""
    post = P.posteriors("visual_archetype")
    notes = P.prompt_block(for_agent="A07")
    if not post and not notes:
        return ""
    ranked = P.thompson_order("visual_archetype", options)
    lines = ["FOUNDER PREFERENCE, learned from reviewed runs. When two archetypes "
             "fit the argument equally, take the one higher on this list:"]
    for opt, _ in ranked:
        p = post.get(opt)
        lines.append("  - " + opt + (": " + P.record_text(p) if p else ": not yet reviewed"))
    return "\n".join(lines) + ("\n" + notes if notes else "") + "\n\n"


def direct(strategy: Any, hook: str, body: str,
           run_id: str, *, client_run_id: Optional[str] = None,
           subject: str = "") -> dict[str, Any]:
    """Pick an archetype and fill its slots. Raises BrainError on failure."""
    opts = candidates()
    listing = "\n".join(
        "  " + k + " — " + v["name"] + "\n"
        "      use when: " + v["when"] + "\n"
        "      slots: " + v["slots"] + "\n"
        "      notes: " + v["notes"]
        for k, v in opts.items())

    blocked = blocked_recent()
    knowledge = _prompt_block(
        " ".join([str(getattr(strategy, "narrative_pillar", "")),
                  str(getattr(strategy, "problem", ""))])[:300], excerpts=5)

    prompt = (
        knowledge + "\n\n----\n\n"
        "THIS POST\n"
        # The subject the founder asked for. Without it the director wrote its
        # headline from `problem` — A03's reframing — so a post about USDC/XLM
        # integration rendered as "Counterparty debt never enters the lending
        # pool" with the subject nowhere on the asset.
        + ("  SUBJECT (the topic the founder asked for; the asset must be "
           "about it, but its claim is the post's): " + str(subject)[:500] + "\n"
           if str(subject).strip() else "")
        + "  pillar:  " + str(getattr(strategy, "narrative_pillar", "")) + "\n"
        "  problem: " + str(getattr(strategy, "problem", ""))[:400] + "\n"
        "  hook:    " + str(hook)[:300] + "\n"
        "  body:    " + str(body)[:1200] + "\n\n"
        "AVAILABLE ARCHETYPES\n" + listing + "\n\n"
        + ("ALREADY USED BY THE LAST POSTS, and therefore not available: "
           + ", ".join(blocked) + "\n\n" if blocked else "")
        + _learned_block(list(opts))
        + "Choose one and fill its slots exactly. Return JSON:\n"
        '{"archetype": "<id>", "why": str, "slots": { ... }}' + "\n\n"
        "Keep `why` under 25 words. Put the effort into the slots; the "
        "rationale is a note, not an essay."
    )

    # One retry on a malformed reply. The selection is a single short JSON
    # object and the model gets it right almost every time, but an occasional
    # slip was costing the run its entire visual — and unlike a bad claim, a
    # broken brace is worth simply asking again for.
    try:
        out = R.brain_json(prompt, agent=AGENT, role="reasoning", system=SYSTEM,
                           temperature=0.55, max_output_tokens=6144,
                           run_id=client_run_id)
    except R.BrainError as first:
        R.record_stage(AGENT, "degraded",
                       "archetype selection returned malformed JSON, retrying: "
                       + str(first)[:200])
        out = R.brain_json(
            prompt + "\n\nReturn ONLY the JSON object. No prose "
                     "before or after it, no comments, no trailing commas, "
                     "no ellipsis. Every slot must carry a literal value.",
            agent=AGENT, role="reasoning", system=SYSTEM,
            temperature=0.2, max_output_tokens=6144, run_id=client_run_id)

    choice = str(out.get("archetype") or "")
    if choice not in opts:
        # The model named something excluded or invented. Do not silently
        # substitute: say so, then take the first open archetype rather than
        # failing the whole run for a naming slip.
        R.record_stage(AGENT, "degraded",
                       "model chose " + repr(choice) + ", not in the open set; "
                       "falling back to " + next(iter(opts)))
        choice = next(iter(opts))

    return {"archetype": choice, "why": str(out.get("why") or "")[:400],
            "slots": out.get("slots") or {}}


def render(direction: dict[str, Any], run_id: str,
           out_dir: Optional[Path] = None) -> Path:
    """Dispatch to the chosen archetype's renderer."""
    choice = direction["archetype"]
    slots = dict(direction.get("slots") or {})
    fn = RENDERERS[choice]
    out = Path(out_dir or STATE) / (run_id + "_visual.png")

    # Shape the model's JSON into each renderer's signature. Tuples and colours
    # are applied here rather than asked for: a model handed a hex slot invents
    # hex values, and the accent ramp is a brand decision.
    if choice == "A2_product":
        slots["rows"] = [tuple(r)[:2] for r in (slots.get("rows") or [])][:4]
        slots["primary"] = tuple((slots.get("primary") or ["", ""]))[:2]
    elif choice == "A9_lockup":
        slots["names"] = [str(n) for n in (slots.get("names") or [])][:3]
        slots["notes"] = [tuple(n)[:2] for n in (slots.get("notes") or [])][:3]
    elif choice == "A6_ledger":
        slots["rows"] = [tuple(r)[:2] for r in (slots.get("rows") or [])][:4]
        slots["verdict"] = tuple((slots.get("verdict") or ["", ""]))[:2]
    elif choice == "A7_composition":
        segs = []
        for i, s in enumerate((slots.get("segments") or [])[:4]):
            label, weight = (list(s) + [1])[:2]
            segs.append((str(label), float(weight or 1),
                         _SEGMENT_RAMP[i % len(_SEGMENT_RAMP)]))
        slots["segments"] = segs
    elif choice == "A8_sequence":
        slots["steps"] = [tuple(s)[:2] for s in (slots.get("steps") or [])][:4]
    elif choice == "A13_containment":
        slots["notes"] = [tuple(n)[:2] for n in (slots.get("notes") or [])][:3]
    elif choice == "A5_round_trip":
        slots["labels"] = [str(x) for x in (slots.get("labels") or [])][:3]

    # The subject the post is actually about. Archetype prompts were fixed
    # constants, so the same six diagrams came back whatever was written —
    # a health-factor post and a partnership post were drawn identically.
    # The renderer passes this to the image model alongside its own grammar.
    slots["subject"] = str(direction.get("subject") or "")[:220]
    # Which layout variant the poster archetypes use. Seeded from the run id
    # so it is stable for a run and differs between runs — without it every
    # poster would render the same arrangement forever, which is the whole
    # thing the variants exist to avoid.
    slots["variant_seed"] = run_id

    # Fill the renderer's signature, and only its signature.
    #
    # `footnote` was being set on every archetype, but A5 Round Trip does not
    # take one — so a perfectly good selection died on a TypeError. Renderers
    # differ by design; the director should adapt to them rather than assume
    # they share a shape.
    import inspect

    accepted = set(inspect.signature(fn).parameters)
    if "footnote" in accepted:
        slots.setdefault("footnote", "Stellar Soroban testnet · docs.vanna.finance")

    dropped = [k for k in slots if k not in accepted]
    for k in dropped:
        slots.pop(k)
    # subject and variant_seed are added above for the renderers that take
    # them; the rest ignore them by design, so their absence is not news.
    dropped = [k for k in dropped if k not in ("subject", "variant_seed")]
    missing = [k for k, prm in inspect.signature(fn).parameters.items()
               if prm.default is inspect.Parameter.empty
               and k not in ("out",) and k not in slots]
    if missing:
        raise ValueError("archetype " + choice + " needs " + ", ".join(missing)
                         + " and the director did not supply "
                         + ("them" if len(missing) > 1 else "it"))
    if dropped:
        R.record_stage(AGENT, "degraded",
                       "dropped slots " + choice + " does not accept: "
                       + ", ".join(dropped))

    path = fn(out=out, **slots)
    remember(choice)
    R.record_stage(AGENT, "ok",
                   "archetype " + choice + " — " + direction.get("why", "")[:160],
                   outputs=[str(path)])
    return Path(path)


def direct_and_render(strategy: Any, hook: str, body: str, run_id: str,
                      *, out_dir: Optional[Path] = None,
                      subject: str = "") -> dict[str, Any]:
    d = direct(strategy, hook, body, run_id, subject=subject)
    # What the figure should depict. The hook is the sharpest one-line
    # statement of the post's subject; the pillar and problem back it up when
    # the hook is too terse to draw from.
    d["subject"] = " ".join(str(
        subject or hook or getattr(strategy, "problem", "")
        or getattr(strategy, "narrative_pillar", "")).split())[:220]
    path = render(d, run_id, out_dir)
    return {**d, "path": str(path),
            "generated": ARCHETYPES[d["archetype"]]["generated"]}
