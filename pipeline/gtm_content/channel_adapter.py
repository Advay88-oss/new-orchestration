"""Phase 4: Channel Adaptation Engine (channel_adapter.py).

Produces genuinely channel-native copy for X, LinkedIn, and Reddit from a validated strategy.
Enforces that every statement has traceable claim provenance.
Uses Gemini 3.8 Flash to generate tailored, bespoke copy for any directive or market opportunity.
"""

from __future__ import annotations

from pipeline.gtm_os.agent_runtime import (
    brain as _brain, BrainError as _BrainError, record_stage as _record_stage,
)

import json
import os
import re
import textwrap
import urllib.request
import urllib.error
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone

from pipeline.gtm_orchestration.schemas import GTMStrategy, ClaimRecord
from pipeline.gtm_content.schemas import ChannelPostPayload, ChannelAdaptationPackage


def call_gemini_brain(prompt: str, system_instruction: str = "") -> Optional[str]:
    """Invoke Gemini 3.8 Flash via Vertex spend proxy (:8900) or direct key."""
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if api_key:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash:generateContent?key={api_key}"
    else:
        url = "http://127.0.0.1:8900/v1/projects/sales-agent-504607/locations/us-central1/publishers/google/models/gemini-3.8-flash:generateContent"

    combined_prompt = f"{system_instruction}\n\n{prompt}" if system_instruction else prompt
    payload = {
        "contents": [{"role": "user", "parts": [{"text": combined_prompt}]}],
        "generationConfig": {
            "temperature": 0.5,
            "maxOutputTokens": 2048
        }
    }

    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=45) as r:
            res = json.loads(r.read().decode("utf-8"))
            return res["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        print(f"⚠️ [ChannelAdapter] Brain call notice: {e}. Using deterministic humanizer synthesis.")
        return None


_AGENT = "A06_channel_adapter"


class ChannelAdapter:
    """Adapts an approved GTM strategy into channel-native posts."""

    @staticmethod
    def split_into_thread(text: str, max_chars: int = 280) -> List[str]:
        """Splits long-form technical copy into cleanly formatted thread segments without clipping."""
        if len(text) <= max_chars:
            return [text]

        # Use conservative width reservation for "[X/Y] " prefix
        target_width = max_chars - 8
        raw_chunks = textwrap.wrap(
            text.strip(),
            width=target_width,
            break_long_words=False,
            replace_whitespace=False
        )
        if not raw_chunks:
            return [text]

        total = len(raw_chunks)
        formatted: List[str] = []
        for i, c in enumerate(raw_chunks):
            chunk_str = f"[{i+1}/{total}] {c.strip()}"
            if len(chunk_str) > max_chars:
                # If prefix pushed over, wrap down tightly
                sub = textwrap.wrap(chunk_str, width=max_chars, break_long_words=False)
                formatted.extend(sub)
            else:
                formatted.append(chunk_str)

        return formatted

    def adapt_strategy_to_channels(
        self,
        strategy: GTMStrategy,
        campaign_id: Optional[str] = None
    ) -> ChannelAdaptationPackage:
        """Generate platform-adapted payloads with full claim provenance."""
        if strategy.action_status in ["NO_ACTION", "KILL"]:
            raise ValueError(f"Channel adapter cannot run for {strategy.action_status} strategy.")

        pkg_id = f"CAP-{strategy.strategy_id[:16]}-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M')}"
        valid_claims = [c.text for c in strategy.claims if c.action in ["USE", "USE_AS_INFERENCE"]]
        evidence_refs = [f"{e.get('source_type')}:{e.get('record_id')}" for e in strategy.evidence]

        # Determine Topic & Tone from Strategy
        title = getattr(strategy, "title", None) or strategy.strategy_id
        from pipeline.brand_brain import context as C
        name = C.company_name()
        auds = C.audiences()
        context = strategy.market_context or strategy.problem or C.company_line()
        audience = strategy.audience_segment or (auds[0].get("name") if auds else "the audience")
        objective = strategy.objective or "Educate the audience and drive the call to action"
        cta = strategy.cta or C.cta()
        figures = ", ".join(f["value"] + " " + f.get("meaning", "") for f in C.true_figures())
        stay_rule = C.rule("stay_on_source")
        figure_scope = C.rule("figure_scope")
        # The research step of the architecture: the brand brain's knowledge on
        # this subject, with sources. Only what is here may be stated as fact;
        # the reviewer checks every claim against the same brain.
        ground_truth = C.facts_block(" ".join([str(context), str(strategy.problem or "")])[:400], k=6)
        # How competitors post on this subject: the shape to learn from, never
        # wording to reuse (the brain keeps only pattern summaries).
        patterns = C.competitor_block(str(title) + " " + str(strategy.problem or ""))
        if patterns:
            ground_truth = ground_truth + "\n\n" + patterns
        traveling = _traveling_shapes()
        if traveling:
            ground_truth = ground_truth + "\n\n" + traveling
        # What the last posts leaned on and how their hooks opened: this one
        # says something else and opens differently (gtm_os/freshness.py).
        try:
            from pipeline.gtm_os.freshness import block as _fresh_block
            fresh = _fresh_block()
        except Exception:                           # noqa: BLE001 — the copy still gets written
            fresh = ""
        if fresh:
            ground_truth = ground_truth + "\n\n" + fresh

        # -------------------------------------------------------------
        # Call Gemini 3.8 Flash for Bespoke Copy Generation
        # -------------------------------------------------------------
        # What A03 decided about THIS subject. The copywriter used to receive a
        # strategy id as its "Title/Directive" and nothing of the problem,
        # positioning or requested format, so it wrote from its own rules —
        # which is how a request to explain liquidity came back as a post
        # about the liquidation floor.
        problem = strategy.problem if strategy.problem not in (None, "", "NONE") else ""
        positioning = strategy.positioning if strategy.positioning not in (None, "", "NONE") else ""
        content_type = strategy.content_type if strategy.content_type not in (None, "", "NONE") else ""
        # What the founder approved and what they sent back. Empty until a run
        # has been reviewed; after that the copywriter writes toward the
        # founder's own record rather than only its rules.
        try:
            from pipeline.gtm_learning.preferences import prompt_block
            learned = prompt_block(for_agent="A06")
        except Exception:                           # noqa: BLE001 — boundary
            learned = ""
        learned_section = ("\n" + learned + "\n") if learned else ""
        try:
            from pipeline.gtm_learning import bandit as _BD
            _bb = _BD.prompt_block(_BD.CURRENT, for_agent="A06")
            if _bb:
                learned_section += "\n" + _bb + "\n"
        except Exception:                           # noqa: BLE001 — boundary
            pass

        llm_prompt = f"""You are the senior technical copywriter for {C.company_line()}
{ground_truth}

State as fact ONLY what the ground truth above says. Every factual claim you make is checked against it by the reviewer, and an unsupported claim blocks the post. Describe mechanisms exactly as the sources do; do not embellish them.

Write native social copy for the following strategy:
- Subject and Founder Request (the post MUST be about this): "{context}"
- Problem to explain: "{problem}"
- {name}'s position on it: "{positioning}"
- Format asked for: "{content_type}"
- Target Audience: "{audience}"
- Core Objective: "{objective}"
- Call to Action: "{cta}"

Stay on the subject. If the founder asked for a concept, explain THAT concept in a few plain sentences; never swap it for a neighbouring one (liquidity is not liquidation). If the subject is a scraped reference, the post is about that doc, post or article, and the last line may be its URL. Do not replace that source with another subject. {stay_rule}
{learned_section}
How the posts that travel are written, and how you write:
People stop for one picture and one fact. They scroll past a mechanism paragraph.
The headlines above are the length and the shape to match. Learn that shape from competitors and from the news. Never reuse their sentences, their numbers, or their brand names.

Do not write like a spec. This is the failure, do not produce it:
"Why are traders still treating this as one pool? On our devnet fork, the protocol isolates assets into dedicated lending reserves while unifying margin. Borrowers take positions through swaps with no funding rate."
That stacks jargon. Nobody reposts it.

Write like this instead. Blank line between lines. Words a person would say out loud:
"One bad asset used to drag the whole pool down.

Now each one sits on its own.

One account. The cap the docs state. No extra fee to hold it."
Use the real subject from this run. Only a figure the ground truth states. If the ground truth does not state a number, do not invent one.

1. One idea. Then stop.
2. Short lines, separated by a blank line. No threads, no numbered points, no bullets, no bold labels.
3. Simple words. No "introduces", "revolutionary", "game-changing", "seamlessly", "isolates assets", "dedicated lending reserves", "unifying margin", "devnet fork", "uniform risk pool".
4. No em dashes and no exclamation marks.
5. A figure only when a GitHub product page in the ground truth states it for this subject. The profile figures are {figures}; never give them to another protocol. {figure_scope}
6. X: 2 or 3 short lines, under 280 characters. The first line is the picture. The link, if any, is the last line.
7. LinkedIn: the same picture in 3 or 4 short lines, under 500 characters. Not an article. Do not say "architecture" or "failure modes" unless the subject is those words.
8. Reddit: the same picture in short lines, under 700 characters, then the disclosure. The title is a plain sentence, not "Technical analysis".

Return STRICT JSON matching this schema:
{{
  "x_hook": "The first line, under 80 characters, no link",
  "x_post_body": "2 or 3 short lines separated by a blank line. Under 280 characters.",
  "linkedin_hook": "The first line for LinkedIn",
  "linkedin_copy": "3 or 4 short lines separated by a blank line. Under 500 characters. No bullets.",
  "reddit_hook": "A plain title a person would click",
  "reddit_copy": "The same picture in short lines, then the disclosure. No headings."
}}"""

        sys_inst = "You write one short social post per channel. Plain sentences, one idea, no threads and no lists. Output only valid JSON."
        # Routed through the shared runtime so this call lands in the run
        # journal. Previously it used a private client whose failure path
        # returned None and fell through to canned "humanizer synthesis" — the
        # run still reported CONTENT_CREATED and nothing recorded that the
        # model had never answered.
        raw_json = None
        try:
            raw_json = _brain(llm_prompt, agent=_AGENT, role="reasoning",
                              system=sys_inst, temperature=0.5,
                              max_output_tokens=8192)
        except _BrainError as exc:
            _record_stage(_AGENT, "degraded",
                          "generation failed, falling back to deterministic "
                          "synthesis: " + str(exc)[:250])

        def _parse(text: str):
            cleaned = re.sub(r"^```(?:json)?\s*", "", str(text).strip())
            cleaned = re.sub(r"\s*```$", "", cleaned)
            return json.loads(cleaned)

        parsed_data = None
        if raw_json:
            try:
                parsed_data = _parse(raw_json)
            except Exception as exc:                # noqa: BLE001 — boundary
                # This was `except Exception: pass`. A malformed reply fell
                # through to the canned template below while the stage still
                # recorded `ok` with a successful model call — so a run could
                # publish boilerplate and report it as generated copy.
                #
                # Retry once with room: the payload is six fields across three
                # channels, and a reply truncated mid-string is the common
                # failure, not a model that cannot do the task.
                _record_stage(_AGENT, "degraded",
                              "first reply was not valid JSON (" + str(exc)[:120]
                              + "); retrying with a larger budget")
                try:
                    retry = _brain(
                        llm_prompt + "\n\nReturn ONLY the JSON object. No prose, "
                        "no code fence. Keep every field complete.",
                        agent=_AGENT, role="reasoning", system=sys_inst,
                        temperature=0.4, max_output_tokens=8192)
                    parsed_data = _parse(retry)
                except Exception as exc2:           # noqa: BLE001 — boundary
                    _record_stage(_AGENT, "degraded",
                                  "model copy unusable after retry ("
                                  + str(exc2)[:160] + "); using the "
                                  "deterministic template")

        if not parsed_data:
            # Built from what A03 established about THIS subject, not from a
            # stored paragraph. Short and plain on purpose: this is a stand-in
            # a human will rewrite, and it should read like one rather than
            # impersonating finished copy.
            subject = clean_title = str(title).split("(")[0].strip()
            problem = str(getattr(strategy, "problem", "") or "").strip()
            opportunity = str(getattr(strategy, "strategic_opportunity", "") or "").strip()
            proof = [str(c).strip() for c in (getattr(strategy, "proof", []) or []) if str(c).strip()][:1]
            sentence = " ".join(p for p in (problem, opportunity, proof[0] if proof else "") if p)
            body = sentence or (name + " on " + subject + ".")

            parsed_data = {
                "x_hook": (opportunity.split(".")[0].strip() or subject)[:120],
                "x_post_body": ((opportunity.split(".")[0].strip() or subject) + ". " + cta).strip(),
                "linkedin_hook": subject,
                "linkedin_copy": (body + " " + cta).strip(),
                "reddit_hook": subject,
                "reddit_copy": (body + "\n\n" + cta + "\n\n*(" + _disclosure() + ")*").strip(),
                # Carried through so the reviewer and the dashboard can see the
                # model did not write this.
                "_synthesised": True,
            }

        # The template stand-in is marked on every post: the cycle stops
        # before paying for a poster or a video for copy no model wrote.
        synthesised = bool(parsed_data.get("_synthesised"))
        # Template copy no model wrote is LOW; model copy is unmeasured until
        # the reviewer and fact check run, so it is not claimed as HIGH.
        _confidence = "LOW" if synthesised else "MEDIUM"
        parsed_data = _simplify_if_dense(parsed_data, ground_truth)

        x_hook = parsed_data.get("x_hook", title)
        x_copy = parsed_data.get("x_post_body", f"{title}\n\n{cta}")
        # One short post. A reply that runs long is cut at a sentence.
        X_MAX = 280
        if len(x_copy) > X_MAX:
            head = x_copy[:X_MAX]
            cut = max(head.rfind("\n\n"), head.rfind(". "))
            x_copy = head[:cut + 1].rstrip() if cut > X_MAX * 0.6 else head.rstrip()
            _record_stage(_AGENT, "degraded",
                          "X copy exceeded " + str(X_MAX) + " characters and "
                          "was trimmed at a sentence boundary")
        post_x = ChannelPostPayload(
            content_id=f"POST-X-{pkg_id}",
            channel="X",
            format="single_post",
            objective=objective,
            audience=audience,
            source_claims=valid_claims,
            exact_evidence_refs=evidence_refs,
            hook=x_hook,
            copy=x_copy,
            call_to_action=cta,
            risk_flags=list(C.rule("risk_flags", []) or []),
            confidence=_confidence,
            provenance={"strategy_id": strategy.strategy_id, "machine_id": strategy.gtm_machine_id,
                        "synthesised": synthesised},
            media_direction=None
        )

        # -------------------------------------------------------------
        # 2. LINKEDIN ADAPTATION
        # -------------------------------------------------------------
        linkedin_hook = parsed_data.get("linkedin_hook", f"Strategic Update: {title}")
        linkedin_copy = parsed_data.get("linkedin_copy", f"{title}\n\n{cta}")
        if cta and cta not in linkedin_copy:
            linkedin_copy = (linkedin_copy.rstrip() + " " + cta).strip()
        post_linkedin = ChannelPostPayload(
            content_id=f"POST-LI-{pkg_id}",
            channel="LinkedIn",
            format="short_post",
            objective=objective,
            audience=audience,
            source_claims=valid_claims,
            exact_evidence_refs=evidence_refs,
            hook=linkedin_hook,
            copy=linkedin_copy,
            call_to_action=cta,
            risk_flags=list(C.rule("risk_flags", []) or []),
            confidence=_confidence,
            provenance={"strategy_id": strategy.strategy_id, "machine_id": strategy.gtm_machine_id,
                        "synthesised": synthesised},
            media_direction=None
        )

        # -------------------------------------------------------------
        # 3. REDDIT ADAPTATION
        # -------------------------------------------------------------
        reddit_hook = parsed_data.get("reddit_hook", f"Technical analysis: {title}")
        reddit_copy = parsed_data.get("reddit_copy", f"**Title:** {reddit_hook}\n\n{title}\n\n{cta}")
        if "disclosure" not in reddit_copy.lower():
            reddit_copy += "\n\n*(" + _disclosure() + ")*"

        post_reddit = ChannelPostPayload(
            content_id=f"POST-RD-{pkg_id}",
            channel="Reddit",
            format="technical_discussion",
            objective=objective,
            audience=audience,
            source_claims=valid_claims,
            exact_evidence_refs=evidence_refs,
            hook=reddit_hook,
            copy=reddit_copy,
            call_to_action=cta,
            discussion_question=(reddit_hook or "What would you want this to do next?"),
            risk_flags=list(C.rule("risk_flags", []) or []),
            confidence=_confidence,
            provenance={"strategy_id": strategy.strategy_id, "machine_id": strategy.gtm_machine_id,
                        "synthesised": synthesised},
            media_direction="Detailed code walkthrough of the mechanism the post explains."
        )

        return ChannelAdaptationPackage(
            package_id=pkg_id,
            strategy_id=strategy.strategy_id,
            campaign_id=campaign_id,
            created_at=datetime.now(timezone.utc).isoformat(),
            channel_posts={
                "x": post_x,
                "linkedin": post_linkedin,
                "reddit": post_reddit
            }
        )


def _traveling_shapes() -> str:
    """How the last scrape's posts are built. The shape to learn, not the words."""
    path = Path(__file__).resolve().parents[2] / "pipeline" / "state" / "research_latest.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return ""
    items = [i for i in (data.get("items") or []) if isinstance(i, dict) and i.get("headline")]

    def line(item: dict) -> str:
        headline = " ".join(str(item.get("headline") or "").split())[:140]
        style = " ".join(str(item.get("style") or "").split())
        reach = item.get("engagement")
        extra = style
        if isinstance(reach, int) and reach > 0:
            extra = (extra + ", " if extra else "") + str(reach) + " views or likes on the source"
        return "- " + headline + ((" (" + extra + ")") if extra else "")

    competitors = [i for i in items if i.get("kind") == "competitor"][:4]
    traveled = [i for i in items if i.get("kind") in ("news", "docs", "community")][:4]
    if not competitors and not traveled:
        competitors = items[:6]
    parts: List[str] = []
    if competitors:
        parts.append("HOW COMPETITORS WRITE (their latest posts). Match this length and hook. "
                     "Do not copy their words, names, or numbers:\n"
                     + "\n".join(line(i) for i in competitors))
    if traveled:
        parts.append("HOW NEWS, DOCS, AND COMMUNITY POSTS THAT GET READ ARE SHAPED. "
                     "Match this shortness. Do not copy their words, names, or numbers:\n"
                     + "\n".join(line(i) for i in traveled))
    return "\n\n".join(parts)


_DENSE = (
    "dedicated lending", "unifying margin", "devnet fork", "uniform risk",
    "isolates assets", "while unifying", "mechanism", "parameters are configured",
)


def _too_dense(text: str, *, max_chars: int, max_words_in_a_line: int) -> bool:
    body = " ".join(str(text or "").split())
    if not body:
        return True
    if len(body) > max_chars:
        return True
    low = body.lower()
    if any(phrase in low for phrase in _DENSE):
        return True
    for line in body.replace("!", ".").replace("?", ".").split("."):
        if len(line.split()) > max_words_in_a_line:
            return True
    return False


def _simplify_if_dense(parsed: dict, ground_truth: str) -> dict:
    """One rewrite when the draft still reads like a spec."""
    if not isinstance(parsed, dict):
        return parsed
    x = str(parsed.get("x_post_body") or "")
    li = str(parsed.get("linkedin_copy") or "")
    if not (_too_dense(x, max_chars=280, max_words_in_a_line=16) or _too_dense(li, max_chars=500, max_words_in_a_line=18)):
        return parsed
    try:
        raw = _brain(
            "Rewrite these three posts so a person scrolling would stop and repeat the first line. "
            "Keep every fact that is already here. Add no new fact and no number that is not already in the draft or the ground truth. "
            "Short lines. A blank line between lines. No spec language, no 'devnet fork', no 'dedicated reserves', no 'unifying margin'.\n\n"
            "GROUND TRUTH:\n" + ground_truth[:1500] + "\n\nDRAFT:\n" + json.dumps({
                "x_hook": parsed.get("x_hook"),
                "x_post_body": parsed.get("x_post_body"),
                "linkedin_hook": parsed.get("linkedin_hook"),
                "linkedin_copy": parsed.get("linkedin_copy"),
                "reddit_hook": parsed.get("reddit_hook"),
                "reddit_copy": parsed.get("reddit_copy"),
            }) + "\n\nReturn ONLY the same JSON keys.",
            agent=_AGENT, role="reasoning",
            system="You rewrite a spec into a short post. Output only JSON.",
            temperature=0.4, max_output_tokens=2048)
        cleaned = re.sub(r"^```(?:json)?\s*", "", str(raw).strip())
        cleaned = re.sub(r"\s*```$", "", cleaned)
        fresh = json.loads(cleaned)
    except Exception:                               # noqa: BLE001 — the first draft stands
        return parsed
    if isinstance(fresh, dict) and fresh.get("x_post_body"):
        _record_stage(_AGENT, "degraded", "first draft was a spec; rewritten into short lines")
        return fresh
    return parsed


def _disclosure() -> str:
    """The contributor disclosure a community post ends with."""
    from pipeline.brand_brain import context as C
    stage = C.disclosure()
    return ("Disclosure: I am a core contributor at " + C.company_name() + "."
            + (" This is on " + stage + "." if stage else ""))
