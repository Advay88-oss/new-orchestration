"""What the last posts leaned on, so the next one says something new.

Twenty-four posts in a row reached for the same anchors — SmartAccount
isolation in 21, the 1.10× floor in 16, Blend and Aquarius in 15, Mercury in
13 — while the brain holds 150 docs pages (earn, farm, strategies, swaps, the
oracle, vTokens, the Solana xStocks and PreStocks) that never made it into a
post. Nothing told the agents what they had just said.

This reads the recent runs and finds, from the posts themselves, the terms
that keep coming back and the way the hooks keep opening. It knows nothing
about any company: a term is "repeated" because it appears in most recent
posts, whatever it is. The strategist, the copywriter and the poster director
each get the block:

    RECENT POSTS — the last 8 leaned on: smartaccount (7/8), blend (5/8), ...
    and opened like: "Why are …", "Shared pools …". Unless this post is about
    one of them, use a different mechanism, example or asset, and open
    differently.

A founder directive that names one of those terms keeps it: the block says
"unless this post is about one of them".
"""
from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

RUNS = Path(__file__).resolve().parents[1] / "state" / "gtm_runs"

_UNUSED_STOP = set("""
about above after again against along also always among another anything around because before being
below between both cannot could doesn every first from have having here into itself just like make makes
many more most much must never only other over same should since some still such than that their them
then there these they this those through today under until very what when where which while with within
without would your yours you'll we're don't isn't it's that's what's there's here's post posts thread
users user trader traders people every across stays still keeps right means cannot need needs single
""".split())


def _posts(n: int) -> list[dict[str, Any]]:
    rows = []
    for f in sorted(RUNS.glob("GTM-*/summary.json"), reverse=True):
        try:
            s = json.loads(f.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        posts = s.get("posts") or {}
        if not posts:
            continue
        x = posts.get("x") or next(iter(posts.values()), {})
        text = " ".join(str(v.get("hook", "")) + " " + str(v.get("copy", "")) for v in posts.values())
        # The words drawn on the poster, not its brief's descriptions.
        for line in str(s.get("poster_brief") or "").splitlines():
            key, _, val = line.partition(":")
            if key.strip().lower() in ("headline", "subtitle", "labels (exact words)"):
                text += " " + re.sub(r"\(gradient word:[^)]*\)", "", val)
        rows.append({"hook": str(x.get("hook") or ""), "text": text, "run_id": f.parent.name})
        if len(rows) >= n:
            break
    return rows


_FIGURE = re.compile(r"\d+(?:\.\d+)?\s?[x×%]")
# A name or product term: CamelCase (SmartAccount), or a capitalised word that
# is not the first of its sentence (Blend, Aquarius, Mercury, Solana).
_NAME = re.compile(r"(?<![.!?:]\s)(?<!^)\b([A-Z][a-z]+(?:[A-Z][a-z]+)+|[A-Z][a-z]{3,})\b", re.M)


def _anchors(text: str, known: set[str], skip: set[str]) -> set[str]:
    found = {m.group(1) for m in _NAME.finditer(text)}
    found = {w for w in found if w.lower() not in skip}
    found |= {f.replace(" ", "").replace("×", "x") for f in _FIGURE.findall(text)}
    low = text.lower()
    found |= {k for k in known if k.lower() in low}
    return found


def _singular(w: str) -> str:
    if w[:1].isdigit() or not w.endswith("s") or w.endswith(("us", "ss", "is")):
        return w
    return w[:-1]


def repeated(n: int = 12, share: float = 0.4, top: int = 8) -> tuple[list[tuple[str, int]], list[str], int]:
    """(anchors in at least `share` of the last n posts with their counts, recent openings, n read)."""
    known: set[str] = set()
    skip = {"the", "this", "that", "your", "when", "what", "every", "testnet", "mainnet", "defi", "disclosure"}
    try:
        from pipeline.brand_brain import context as C
        skip.add(C.company_name().lower())
        # Where the company runs (Stellar, Soroban) is in every post by right.
        dep = str((C.profile().get("company") or {}).get("deployment") or "")
        skip |= {w.lower() for w in re.findall(r"[A-Za-z]{4,}", dep)}
        known |= {str(n) for n in (C.partners() or {})}
        known |= {str(f.get("value")) for f in C.true_figures() if f.get("value")}
    except Exception:                               # noqa: BLE001 — no profile: names from the posts only
        pass
    posts = _posts(n)
    if len(posts) < 3:
        return [], [], len(posts)
    df: Counter = Counter()
    for p in posts:
        # One count per post; "SmartAccounts" is "SmartAccount".
        df.update({_singular(a.lower()) for a in _anchors(p["text"], known, skip) if a.lower() not in skip})
    need = max(2, int(len(posts) * share + 0.999))
    common = [(t, c) for t, c in df.most_common() if c >= need][:top]
    openings = []
    for p in posts:
        words = p["hook"].split()
        if words:
            openings.append(" ".join(words[:3]))
    return common, openings[:6], len(posts)


def block(n: int = 12) -> str:
    """The prompt block, or "" when there is too little history to say anything."""
    try:
        common, openings, read = repeated(n)
    except Exception:                               # noqa: BLE001 — never block a run
        return ""
    if not common and not openings:
        return ""
    parts = ["RECENT POSTS — the last " + str(read) + " posts leaned on: "
             + (", ".join(t + " (" + str(c) + "/" + str(read) + ")" for t, c in common) or "nothing in particular")
             + "."]
    if openings:
        parts.append("Their hooks opened like: " + "; ".join('"' + o + ' …"' for o in openings) + ".")
    parts.append("Unless this post is about one of those, do not lean on them again: pick a different "
                 "mechanism, example, asset or use case from the sources (the brain has many pages these posts "
                 "never used), and open the hook a different way. Variety comes from the subject, never from "
                 "inventing facts: every claim still has to be in the sources.")
    return "\n".join(parts) + "\n\n"
