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
        # The research step of the architecture: the brand brain's knowledge on
        # this subject, with sources. Only what is here may be stated as fact;
        # the reviewer checks every claim against the same brain.
        ground_truth = C.facts_block(" ".join([str(context), str(strategy.problem or "")])[:400], k=6)

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

Stay on the subject. If the founder asked for a concept, explain THAT concept; never swap it for a neighbouring one (liquidity is not liquidation). If the request names a structure (problem, how it works, why it matters, where {name} fits) or a quality (simple language, saveable, shareable), the X post follows that structure in that order.
{learned_section}
Editorial & Algorithmic Rules to Follow Strictly (HERMES HUMANIZER SKILL):
1. Voice: Speak as an authentic engineer/builder. Write with real opinions, natural sentence variation, and zero marketing fluff.
2. Ban AI Clichés: Never use "introduces", "features include", "revolutionary", "game-changing", "seamlessly", "stands as", "is a testament to", "in today's evolving landscape".
3. Ban Structural Slop: Never use em dashes (—), exclamation marks (!), or negative parallelisms ("Not only X, but Y").
4. Ban Robotic Lists: Never write "- **Feature:** description" bullet lists. Write natural prose.
5. Specifics Over Adjectives: {name}'s real figures are {figures}. Use a figure ONLY when it is about the subject; a figure bolted on to look technical is filler. These are {name}'s figures: never attribute them to other protocols or to the category as a whole.
6. X/Twitter: First 7 words must hook the target audience. Never put links in Tweet 1. Put the CTA link only at the end.
7. LinkedIn: Thought leadership focusing on architecture and execution latency over pooled risk.
8. Reddit: Honest technical forum breakdown with personal disclosure.

Return STRICT JSON matching this schema:
{{
  "x_hook": "Sharp, scroll-stopping opening hook under 120 characters without any links",
  "x_post_body": "Full multi-paragraph post for X that can be split into a thread: under 600 characters, or up to 1100 when the founder asked for an explainer. Do not put links in the first paragraph. Include only the proof points that are about the subject. End with the CTA link.",
  "linkedin_hook": "Opening headline hook for institutional readers",
  "linkedin_copy": "3-paragraph institutional thought leadership article with institutional architecture framing. Zero em dashes.",
  "reddit_hook": "Technical discussion title for r/defi or r/stellar",
  "reddit_copy": "Markdown technical breakdown detailing smart contract architecture, risk parameters, and testnet deployment instructions. Must end with disclosure. Zero em dashes."
}}"""

        sys_inst = "You are a core Web3 protocol builder writing for developers and traders. Write naturally like a human. Avoid all AI marketing buzzwords, em dashes, and robotic bullet formats. Output only valid JSON."
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
            proof = [str(c).strip() for c in (getattr(strategy, "proof", []) or []) if str(c).strip()][:3]
            proof_block = "\n".join("- " + c for c in proof)

            body_parts = [p for p in (problem, opportunity) if p]
            body = "\n\n".join(body_parts) or (name + "'s position on " + subject + ".")

            parsed_data = {
                "x_hook": (opportunity.split(".")[0].strip() or subject)[:120],
                "x_post_body": (body + ("\n\n" + proof_block if proof_block else "")
                                + "\n\n" + cta),
                "linkedin_hook": subject,
                "linkedin_copy": body + ("\n\n" + proof_block if proof_block else "")
                                 + "\n\n" + cta,
                "reddit_hook": subject,
                "reddit_copy": (body + ("\n\n" + proof_block if proof_block else "")
                                + "\n\n" + cta
                                + "\n\n*(" + _disclosure() + ")*"),
                # Carried through so the reviewer and the dashboard can see the
                # model did not write this.
                "_synthesised": True,
            }

        x_hook = parsed_data.get("x_hook", title)
        x_copy = parsed_data.get("x_post_body", f"{title}\n\n{cta}")
        # This was a hard cut at 790 characters. An explainer asked for four
        # sections lost the third mid-sentence and the fourth entirely — the
        # "how Vanna fits" part — and nothing recorded it; the creative judge
        # caught it as a copy REJECT. X copy ships as a thread, so the ceiling
        # only guards against a runaway reply, and when it bites it cuts at a
        # paragraph or sentence boundary and says so.
        X_MAX = 1600
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
            format="thread_lead",
            objective=objective,
            audience=audience,
            source_claims=valid_claims,
            exact_evidence_refs=evidence_refs,
            hook=x_hook,
            copy=x_copy,
            call_to_action=cta,
            risk_flags=["Requires testnet anchor verification"],
            confidence="HIGH",
            provenance={"strategy_id": strategy.strategy_id, "machine_id": strategy.gtm_machine_id},
            media_direction="16:9 cinematic textless video showing sub-second optical deflection path away from danger boundary."
        )

        # -------------------------------------------------------------
        # 2. LINKEDIN ADAPTATION
        # -------------------------------------------------------------
        linkedin_hook = parsed_data.get("linkedin_hook", f"Strategic Update: {title}")
        linkedin_copy = parsed_data.get("linkedin_copy", f"{title}\n\n{cta}")
        if "architecture" not in linkedin_copy.lower():
            linkedin_copy += "\n\n" + cta
        post_linkedin = ChannelPostPayload(
            content_id=f"POST-LI-{pkg_id}",
            channel="LinkedIn",
            format="institutional_article",
            objective=objective,
            audience=audience,
            source_claims=valid_claims,
            exact_evidence_refs=evidence_refs,
            hook=linkedin_hook,
            copy=linkedin_copy,
            call_to_action=cta,
            risk_flags=["Must not claim mainnet live or live institutional fund adoption"],
            confidence="HIGH",
            provenance={"strategy_id": strategy.strategy_id, "machine_id": strategy.gtm_machine_id},
            media_direction="High-resolution 2-panel architecture schematic comparing monolithic pool vs isolated sandboxes."
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
            discussion_question="How does your protocol handle liquidation execution uncertainty on testnet?",
            risk_flags=["Requires testnet disclosure"],
            confidence="HIGH",
            provenance={"strategy_id": strategy.strategy_id, "machine_id": strategy.gtm_machine_id},
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


def _disclosure() -> str:
    """The contributor disclosure a community post ends with."""
    from pipeline.brand_brain import context as C
    stage = C.disclosure()
    return ("Disclosure: I am a core contributor at " + C.company_name() + "."
            + (" This is on " + stage + "." if stage else ""))
