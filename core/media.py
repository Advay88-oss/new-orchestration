"""Media generation — images (nano banana / nano banana pro) and video (Veo 3.1).

Routing comes from `core.models`, so the model used is declared in one place and
recorded per run:

    image       gemini-3.1-flash-image     background texture for a rendered asset
    meme_image  nano-banana-pro-preview    the memes surface
    video       veo-3.1-generate-preview   long-running; polled to completion

The boundary the audit found broken is preserved here deliberately:

  * For a **post asset**, the image model may only paint a background plate.
    Text, logo, disclaimer and layout are rendered by `core/render.py`. This is
    the project's own tested doctrine (`.claude/agents/visual-creator.md`) which
    the old pipeline inverted, producing "horizotal" and "TECHNICALARCHITECTURE"
    baked into pixels.
  * A **meme** is different: the joke IS the image, and memes are not published
    as factual claims. There the image model may render its own text — but the
    asset is tagged so it can never be mistaken for a claim-bearing post.

Video generation does not fabricate progress. Veo is long-running; the stage
polls the real operation and reports what the operation says.
"""
from __future__ import annotations

import base64
import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Literal

from .contracts import StageResult, degraded, digest, ok
from .design import PALETTE, REJECTED_TREATMENTS
from .llm import API_ROOT, LLMError, api_key
from .models import Role, resolve
from .motion import motion_stage as _motion

REPO = Path(__file__).resolve().parents[1]
MEDIA_DIR = Path(os.environ.get("VANNA_MEDIA_DIR", REPO / "state" / "media"))

VIDEO_POLL_INTERVAL_S = 10.0
VIDEO_TIMEOUT_S = 600.0


class MediaError(RuntimeError):
    pass


def _post(url: str, payload: dict[str, Any], timeout: float) -> dict[str, Any]:
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raise MediaError(f"HTTP {exc.code}: {exc.read().decode('utf-8', 'replace')[:300]}") from exc
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise MediaError(f"transport error: {exc}") from exc


def _get(url: str, timeout: float) -> dict[str, Any]:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raise MediaError(f"HTTP {exc.code}: {exc.read().decode('utf-8', 'replace')[:300]}") from exc
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise MediaError(f"transport error: {exc}") from exc


# --------------------------------------------------------------------------
# Images
# --------------------------------------------------------------------------

BRAND_CLAUSE = (
    f"Palette strictly limited to obsidian {PALETTE['obsidian']}, "
    f"violet {PALETTE['violet_bloom']}, fuchsia {PALETTE['fuchsia_bloom']}, "
    f"lavender {PALETTE['lavender']}. 35mm film grain, generous negative space, "
    "institutional restraint."
)

NEGATIVE_CLAUSE = "Do NOT produce any of: " + "; ".join(REJECTED_TREATMENTS) + "."


def generate_image(prompt: str, role: Role, out_path: Path,
                   *, timeout: float = 180.0) -> tuple[Path, str]:
    """Generate one image. Returns (path, model_actually_used)."""
    r = resolve(role)
    url = f"{API_ROOT}/models/{r.model}:generateContent?key={api_key()}"
    body = _post(url, {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {"responseModalities": ["IMAGE"]},
    }, timeout)

    cands = body.get("candidates") or []
    if not cands:
        raise MediaError(f"{r.model} returned no candidates "
                         f"(promptFeedback={body.get('promptFeedback')})")
    for part in (cands[0].get("content") or {}).get("parts") or []:
        inline = part.get("inlineData") or part.get("inline_data")
        if inline and inline.get("data"):
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_bytes(base64.b64decode(inline["data"]))
            return out_path, body.get("modelVersion") or r.model
    raise MediaError(f"{r.model} returned no image part "
                     f"(finishReason={cands[0].get('finishReason')})")


def texture_for(spec_headline: str, run_id: str) -> tuple[Path, str]:
    """A background plate for a post asset. Explicitly textless."""
    prompt = (
        "Abstract background texture for a premium financial-infrastructure brand. "
        f"Mood: {spec_headline[:90]}. {BRAND_CLAUSE} "
        "ABSOLUTELY NO TEXT, NO LETTERS, NO NUMBERS, NO LOGOS, NO UI, NO CHARTS. "
        "Soft depth, subtle gradient bloom, nothing figurative in the centre so "
        f"foreground type stays legible. {NEGATIVE_CLAUSE}"
    )
    return generate_image(prompt, "image", MEDIA_DIR / f"{run_id}_texture.png")


def meme_image(concept: str, caption: str, run_id: str) -> tuple[Path, str]:
    """A meme. Here the image model MAY render text — the joke is the image."""
    prompt = (
        f"Crypto-native meme illustration. Concept: {concept}. "
        f"Caption to render legibly in the image: \"{caption}\". "
        "Clean, high-contrast, readable at thumbnail size. Dry humour, not cringe. "
        "No fabricated statistics, no protocol logos, no price charts. "
        f"{NEGATIVE_CLAUSE}"
    )
    return generate_image(prompt, "meme_image", MEDIA_DIR / f"{run_id}_meme.png")


# --------------------------------------------------------------------------
# Video (Veo 3.1, long-running)
# --------------------------------------------------------------------------

def _find_video_uri(node: Any, depth: int = 0) -> str | None:
    """Walk the operation response for a video URI.

    Veo nests the result differently across shapes — the observed one is
    `response.generateVideoResponse.generatedSamples[].video.uri`, but the
    envelope has changed before. Searching rather than asserting one path means
    a future nesting change surfaces as a normal result, not a false failure.
    """
    if depth > 6:
        return None
    if isinstance(node, dict):
        for key in ("uri", "gcsUri", "videoUri"):
            val = node.get(key)
            if isinstance(val, str) and val.startswith("http"):
                return val
        for val in node.values():
            found = _find_video_uri(val, depth + 1)
            if found:
                return found
    elif isinstance(node, list):
        for item in node:
            found = _find_video_uri(item, depth + 1)
            if found:
                return found
    return None


def generate_video(prompt: str, run_id: str, *,
                   timeout_s: float = VIDEO_TIMEOUT_S) -> tuple[Path, str, dict]:
    """Start a Veo generation and poll the real operation to completion."""
    r = resolve("video")
    # personGeneration is deliberately not set: `dont_allow` is rejected by
    # veo-3.1-generate-preview, and guessing another value would be inventing a
    # setting rather than declaring one. The prompt asks for abstract motion.
    start = _post(
        f"{API_ROOT}/models/{r.model}:predictLongRunning?key={api_key()}",
        {"instances": [{"prompt": prompt}],
         "parameters": {"aspectRatio": "16:9"}},
        120.0)

    op_name = start.get("name")
    if not op_name:
        raise MediaError(f"Veo did not return an operation: {str(start)[:200]}")

    deadline = time.time() + timeout_s
    op: dict[str, Any] = {}
    polls = 0
    while time.time() < deadline:
        time.sleep(VIDEO_POLL_INTERVAL_S)
        polls += 1
        op = _get(f"{API_ROOT}/{op_name}?key={api_key()}", 60.0)
        if op.get("done"):
            break
    if not op.get("done"):
        raise MediaError(f"Veo operation {op_name} did not finish within {timeout_s}s "
                         f"({polls} polls)")
    if op.get("error"):
        raise MediaError(f"Veo failed: {str(op['error'])[:300]}")

    uri = _find_video_uri(op.get("response") or {})
    if not uri:
        raise MediaError(f"Veo finished but returned no video URI: "
                         f"{str(op.get('response'))[:300]}")

    out = MEDIA_DIR / f"{run_id}_veo.mp4"
    out.parent.mkdir(parents=True, exist_ok=True)
    sep = "&" if "?" in uri else "?"
    with urllib.request.urlopen(f"{uri}{sep}key={api_key()}", timeout=300) as src:
        out.write_bytes(src.read())
    return out, r.model, {"operation": op_name, "polls": polls}


# --------------------------------------------------------------------------
# The pipeline stage
# --------------------------------------------------------------------------

MediaKind = Literal["none", "texture", "meme", "video"]

VIDEO_WORDS = ("video", "film", "clip", "reel", "motion", "animation", "veo")
MEME_WORDS = ("meme", "memes", "shitpost", "joke")


def decide_kind(directive: str) -> MediaKind:
    d = (directive or "").lower()
    if any(w in d for w in VIDEO_WORDS):
        return "video"
    if any(w in d for w in MEME_WORDS):
        return "meme"
    return "texture"


def media_stage(directive: str, headline: str, run_id: str,
                *, caption: str = "", spec=None, claims=None) -> StageResult[dict]:
    """Produce the media this directive actually calls for.

    A skipped media step is reported as skipped, not as a success — the old
    Agent 09 wrote `None` and the run still claimed thirteen agents completed.
    """
    started = time.time()
    kind = decide_kind(directive)
    ih = digest({"kind": kind, "headline": headline})

    try:
        if kind == "video":
            r = resolve("video")
            path, model, meta = generate_video(
                f"{headline}. Cinematic abstract motion for a financial-infrastructure "
                f"brand. {BRAND_CLAUSE} No on-screen text.", run_id)

            # Veo supplies abstract b-roll; Remotion supplies the branded,
            # typographic half. They are complementary, not alternatives: only
            # the deterministic renderer may put a figure on screen, and only
            # one that was verified against evidence.
            motion = _motion(spec, list(claims or []), run_id)

            payload = {"kind": "video", "path": str(path), "model": model,
                       "bytes": path.stat().st_size, **meta,
                       "motion": motion.value,
                       "motion_status": motion.status,
                       "motion_note": motion.degraded_reason}
            tools = [f"veo:{r.transport}"] + list(motion.tool_calls)

            if motion.status != "ok":
                # The b-roll exists, so the run is not a failure — but it did not
                # produce the branded render it set out to, and says so.
                return degraded("media", payload, started,
                                f"Veo ok; motion graphics degraded: {motion.degraded_reason}",
                                input_hash=ih, model=model, cost_known=False,
                                tool_calls=tools)
            return ok("media", payload, started, input_hash=ih, model=model,
                      cost_known=False, tool_calls=tools)

        if kind == "meme":
            path, model = meme_image(headline, caption or headline, run_id)
            payload = {"kind": "meme", "path": str(path), "model": model,
                       "bytes": path.stat().st_size,
                       "claim_bearing": False,
                       "note": "meme surface — image model rendered its own text by design"}
            return ok("media", payload, started, input_hash=ih, model=model,
                      cost_known=False, tool_calls=["nano-banana-pro"])

        path, model = texture_for(headline, run_id)
        data_uri = "data:image/png;base64," + base64.b64encode(path.read_bytes()).decode("ascii")
        payload = {"kind": "texture", "path": str(path), "model": model,
                   "bytes": path.stat().st_size, "data_uri_len": len(data_uri),
                   "note": "background plate only; all text rendered deterministically"}
        return ok("media", payload, started, input_hash=ih, model=model,
                  cost_known=False, tool_calls=["nano-banana"])

    except (MediaError, LLMError) as exc:
        # The asset can still ship without generated media — the deterministic
        # renderer does not need it — but the run must say the media step failed.
        return degraded("media", {"kind": kind, "path": None}, started,
                        f"{kind} generation failed: {exc}"[:400], input_hash=ih)


def texture_data_uri(path_str: str | None) -> str | None:
    if not path_str:
        return None
    p = Path(path_str)
    if not p.exists():
        return None
    return "data:image/png;base64," + base64.b64encode(p.read_bytes()).decode("ascii")
