"""Visual critic — a model that actually looks at the rendered image.

What this replaces:

  visual_quality_critic.py:130-191   d4_score = 95; d5_score = 92; d7_score = 92
                                      d8_score = 94; d10_score = 95   # constants
  visual_pipeline_engine.py:212      score = 80 + resolution_bonus + corner_darkness
  reviewer.py:113                    dark_ratio >= 0.40 and cyan_ratio <= 0.25

None of those inspected the composition. The last one — a two-term colour
histogram — was the only gate in production, which is how a concept the system
itself flagged as a STRUCTURAL CLONE with novelty 0.0 shipped at 100/100.

The critic returns **structured defects**, not a score, because a score cannot
be acted on. A defect names what is wrong, where, and what to change — which is
what makes the revision loop possible.
"""
from __future__ import annotations

import time
from pathlib import Path

from .contracts import Critique, Defect, StageResult, VisualSpec, degraded, digest, ok
from .design import CANVAS, REJECTED_TREATMENTS
from .llm import LLMClient, LLMError

CRITIC_PROMPT_VERSION = "visual-critic/v1"

CRITIC_SCHEMA = {
    "type": "object",
    "properties": {
        "defects": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "severity": {"type": "string", "enum": ["low", "medium", "high"]},
                    "issue": {"type": "string"},
                    "location": {"type": "string"},
                    "reason": {"type": "string"},
                    "fix": {"type": "string"},
                    "confidence": {"type": "number"},
                },
                "required": ["severity", "issue", "location", "reason", "fix", "confidence"],
            },
        },
        "verdict": {"type": "string", "enum": ["accept", "revise", "reject"]},
    },
    "required": ["defects", "verdict"],
}

CRITIC_SYSTEM = f"""You are a senior art director reviewing a 1:1 social asset for a
DeFi credit-infrastructure brand. You are looking at the actual rendered image.

Judge only what you can SEE. Report defects, never praise.

Examine, in order:
1. COMPOSITION — is there a single clear focal point? Is the visual weight
   balanced, or is one region of the canvas dead? Does the eye have a path?
2. TYPOGRAPHY — hierarchy, line length, letterspacing (especially uppercase),
   optical alignment, widows and orphans, contrast against the ground.
3. HIERARCHY — does the most important element read first? In 2 seconds, what
   does a viewer take away?
4. BRAND — restrained, institutional, premium. One accent colour only. Generous
   negative space is intended, but *unbalanced* emptiness is a defect.
5. TECHNICAL — overlapping elements, clipping, crowding at the safe margins,
   rendering artifacts.
6. ORIGINALITY — does this look like generic AI-generated marketing?

These treatments are rejected by the brand; flag any of them as high severity:
{chr(10).join('  - ' + t for t in REJECTED_TREATMENTS)}

Severity:
  high   — ships broken or off-brand; must be fixed
  medium — noticeably weakens the asset
  low    — polish

Verdict rules (enforced downstream):
  accept — NO high-severity defects
  revise — fixable defects present
  reject — the concept itself does not work

Every `fix` must be a concrete, actionable instruction a layout engine can
follow (e.g. "move the stat block up 80px and reduce the headline to two
lines"), not a vague wish ("improve balance"). Be specific about location."""


def critique_image(png_path: Path, spec: VisualSpec, client: LLMClient) -> StageResult[Critique]:
    """Send the rendered PNG to a multimodal model and get structured defects."""
    started = time.time()
    ih = digest({"spec": spec.model_dump(), "path": str(png_path)})

    if not png_path.exists():
        return degraded("critic", None, started,
                        f"no image at {png_path}", input_hash=ih)

    prompt = (
        f"This asset is {CANVAS}x{CANVAS} (rendered at 2x).\n"
        f"Intended layout: {spec.layout}\n"
        f"Intended focal element: block #{spec.focal.block_index} "
        f"({spec.blocks[spec.focal.block_index].text!r}) — {spec.focal.reason}\n"
        f"Headline: {spec.headline!r}\n\n"
        "Review the image and list every defect you can see."
    )

    try:
        data, resp = client.complete_image_json(
            prompt, png_path.read_bytes(),
            schema=CRITIC_SCHEMA, system=CRITIC_SYSTEM,
            prompt_version=CRITIC_PROMPT_VERSION,
        )
    except LLMError as exc:
        # A critic that cannot run must not be reported as "passed".
        return degraded("critic", None, started,
                        f"critic unavailable: {exc}"[:300], input_hash=ih)

    defects = []
    for d in data.get("defects", []):
        try:
            defects.append(Defect(
                severity=d["severity"], issue=d["issue"], location=d["location"],
                reason=d["reason"], fix=d["fix"],
                confidence=min(max(float(d.get("confidence", 0.5)), 0.0), 1.0),
            ))
        except Exception:
            continue

    verdict = data.get("verdict", "revise")
    # Contract forbids accept-with-high-severity. Rather than let the model
    # contradict itself (the 100/100-with-empty-audit pattern), correct it.
    if verdict == "accept" and any(d.severity == "high" for d in defects):
        verdict = "revise"

    crit = Critique(defects=defects, verdict=verdict)
    return ok("critic", crit, started, input_hash=ih,
              model=resp.model, prompt_version=resp.prompt_version,
              input_tokens=resp.input_tokens, output_tokens=resp.output_tokens,
              cost_usd=resp.cost_usd or 0.0, cost_known=resp.pricing_known, tool_calls=["vision"])


REVISE_PROMPT_VERSION = "visual-revise/v1"

REVISE_SYSTEM = """You revise a VisualSpec to fix specific, named defects.

You are editing a structured specification that a deterministic layout engine
will execute. You are NOT describing a picture — you cannot change anything the
spec does not control.

You may change: layout, headline, subhead, block text/role/emphasis, focal, and
background. You may NOT invent colours — the palette is fixed.

Address every high-severity defect. Make the smallest change that fixes it.
Do not restyle things that were not flagged; churn is a defect of its own."""


def revise_spec(spec: VisualSpec, critique: Critique, client: LLMClient) -> VisualSpec | None:
    """Produce a revised spec addressing the critique. None if revision fails."""
    if not critique.defects:
        return None

    defect_lines = "\n".join(
        f"- [{d.severity}] {d.issue} (at {d.location}). Fix: {d.fix}"
        for d in critique.defects
    )
    schema = VisualSpec.model_json_schema()
    # The palette is not the model's to choose.
    schema.get("properties", {}).pop("palette", None)
    if "required" in schema:
        schema["required"] = [r for r in schema["required"] if r != "palette"]

    prompt = (
        f"CURRENT SPEC:\n{spec.model_dump_json(indent=2)}\n\n"
        f"DEFECTS TO FIX:\n{defect_lines}\n\n"
        "Return the revised spec."
    )
    try:
        data, _ = client.complete_json(
            prompt, schema=_flatten_schema(schema), system=REVISE_SYSTEM,
            prompt_version=REVISE_PROMPT_VERSION, temperature=0.2,
            max_output_tokens=8192,
        )
    except LLMError:
        return None

    data["palette"] = spec.palette.model_dump()
    try:
        return VisualSpec(**data)
    except Exception:
        return None


def _flatten_schema(schema: dict) -> dict:
    """Inline $defs — the API's responseSchema does not resolve $ref."""
    defs = schema.pop("$defs", {})

    def walk(node):
        if isinstance(node, dict):
            if "$ref" in node:
                name = node["$ref"].split("/")[-1]
                return walk(dict(defs.get(name, {})))
            return {k: walk(v) for k, v in node.items()
                    if k not in ("title", "default", "additionalProperties")}
        if isinstance(node, list):
            return [walk(v) for v in node]
        return node

    return walk(schema)
