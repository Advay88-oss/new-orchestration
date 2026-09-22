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
from pipeline.gtm_os import agent_runtime as R
from pipeline.gtm_os.vanna_knowledge import prompt_block as _prompt_block

AGENT = "A07_creative_director"
STATE = Path(__file__).resolve().parents[2] / "pipeline" / "state"
RECENT_FILE = STATE / "recent_archetypes.json"
KEEP_RECENT = 2


# --------------------------------------------------------------------------
# Registry
# --------------------------------------------------------------------------

ARCHETYPES: dict[str, dict[str, Any]] = {
    "A2_product": {
        "name": "Product Frame",
        "when": "Something a person does in the app — depositing, withdrawing, "
                "checking a position before signing.",
        "generated": False,
        "slots": '{"headline": str, "deck": str, "panel_title": str, '
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
        "slots": '{"headline": str, "rows": [[str, str]], '
                 '"verdict": [str, str], "footnote": str}',
        "notes": "3-4 rows of [label, value]. verdict is [label, result]. "
                 "Every figure must be arithmetically consistent.",
    },
    "A7_composition": {
        "name": "Composition Bar",
        "when": "What something is made of — a split, a breakdown, a mix.",
        "generated": False,
        "slots": '{"headline": str, "deck": str, '
                 '"segments": [[str, number]], "total_label": str, '
                 '"footnote": str}',
        "notes": "2-4 segments of [label, weight]. Weights need not sum to "
                 "100; they are normalised. Say in the footnote if the split "
                 "is illustrative.",
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
}

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


def candidates() -> dict[str, dict[str, Any]]:
    """Every archetype except the last two used."""
    blocked = set(recent()[:KEEP_RECENT])
    open_set = {k: v for k, v in ARCHETYPES.items() if k not in blocked}
    # Never hand back an empty set; if the registry ever shrinks to two, the
    # oldest block lapses rather than the run failing.
    return open_set or dict(ARCHETYPES)


# --------------------------------------------------------------------------
# Direction
# --------------------------------------------------------------------------

SYSTEM = (
    "You are Vanna's creative director. Vanna is composable credit "
    "infrastructure on Stellar Soroban TESTNET.\n\n"
    "You choose ONE visual archetype for a post and write the words that go "
    "in it. You are not describing an image — the archetype already fixes the "
    "composition. Your job is the choice and the copy.\n\n"
    "Rules:\n"
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
    "- Footnotes carry the source and any caveat, quietly.\n\n"
    "Return strict JSON."
)


def direct(strategy: Any, hook: str, body: str,
           run_id: str, *, client_run_id: Optional[str] = None) -> dict[str, Any]:
    """Pick an archetype and fill its slots. Raises BrainError on failure."""
    opts = candidates()
    listing = "\n".join(
        "  " + k + " — " + v["name"] + "\n"
        "      use when: " + v["when"] + "\n"
        "      slots: " + v["slots"] + "\n"
        "      notes: " + v["notes"]
        for k, v in opts.items())

    blocked = recent()[:KEEP_RECENT]
    knowledge = _prompt_block(
        " ".join([str(getattr(strategy, "narrative_pillar", "")),
                  str(getattr(strategy, "problem", ""))])[:300], excerpts=5)

    prompt = (
        knowledge + "\n\n----\n\n"
        "THIS POST\n"
        "  pillar:  " + str(getattr(strategy, "narrative_pillar", "")) + "\n"
        "  problem: " + str(getattr(strategy, "problem", ""))[:400] + "\n"
        "  hook:    " + str(hook)[:300] + "\n"
        "  body:    " + str(body)[:1200] + "\n\n"
        "AVAILABLE ARCHETYPES\n" + listing + "\n\n"
        + ("ALREADY USED BY THE LAST POSTS, and therefore not available: "
           + ", ".join(blocked) + "\n\n" if blocked else "")
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
                      *, out_dir: Optional[Path] = None) -> dict[str, Any]:
    d = direct(strategy, hook, body, run_id)
    path = render(d, run_id, out_dir)
    return {**d, "path": str(path),
            "generated": ARCHETYPES[d["archetype"]]["generated"]}
