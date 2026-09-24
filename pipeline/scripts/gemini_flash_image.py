#!/usr/bin/env python3
"""Google Gemini 3.1 Flash Image Generator for Vanna Protocol.

Uses Google Cloud Model Garden `gemini-3.1-flash-image` on project `vanna-mcp` (location: global).
Generates high-resolution images returned directly as inline base64 PNG data.
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path
from typing import Any, Dict, Optional

REPO_ROOT = Path(os.environ.get("VANNA_ROOT", Path(__file__).resolve().parents[2]))

def get_vertex_token() -> str:
    """Retrieves Google Cloud OAuth access token from ADC or gcloud."""
    try:
        import google.auth
        from google.auth.transport.requests import Request as GRequest
        creds, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
        creds.refresh(GRequest())
        if creds.token:
            return creds.token
    except Exception:
        pass
        
    exe = shutil.which("gcloud") or shutil.which("gcloud.cmd") or "gcloud.cmd"
    try:
        r = subprocess.run(
            [exe, "auth", "application-default", "print-access-token"],
            capture_output=True, text=True, timeout=60
        )
        tok = (r.stdout or "").strip()
        if tok:
            return tok
    except Exception:
        pass
    raise RuntimeError("No Google Cloud access token found. Run: gcloud auth application-default login")


def _encode_image(path, max_side: int = 1024) -> str:
    """A reference as base64 PNG, downscaled so a handful fit in one request."""
    from io import BytesIO
    from PIL import Image
    im = Image.open(path)
    im = im.convert("RGBA") if im.mode in ("RGBA", "LA", "P") else im.convert("RGB")
    im.thumbnail((max_side, max_side))
    buf = BytesIO()
    im.save(buf, format="PNG", optimize=True)
    return base64.b64encode(buf.getvalue()).decode("ascii")


def generate_gemini_image(
    prompt: str,
    output_path: Path | str,
    project: str = "vanna-mcp",
    location: str = "global",
    model: str = "gemini-3.1-flash-image",
    temperature: float = 0.4,
    images: Optional[list] = None,
    aspect_ratio: Optional[str] = None,
) -> Path:
    """Calls a Gemini image endpoint on Model Garden and writes PNG to disk.

    `images` are sent with the prompt as inline parts, so the model can SEE
    them — style references, the real logo. Until this existed the image
    model received text only and never saw a single reference, which is why
    the house style had to be re-described in code.
    """
    out = Path(output_path).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    
    token = get_vertex_token()
    host = "https://aiplatform.googleapis.com" if location == "global" else f"https://{location}-aiplatform.googleapis.com"
    url = f"{host}/v1/projects/{project}/locations/{location}/publishers/google/models/{model}:generateContent"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "x-goog-user-project": project
    }
    
    parts: list = []
    for img in images or []:
        parts.append({"inlineData": {"mimeType": "image/png",
                                     "data": _encode_image(img)}})
    parts.append({"text": prompt})
    payload = {
        "contents": [{"role": "user", "parts": parts}],
        "generationConfig": {"temperature": temperature},
    }
    if aspect_ratio:
        payload["generationConfig"]["responseModalities"] = ["IMAGE"]
        payload["generationConfig"]["imageConfig"] = {"aspectRatio": aspect_ratio}
    
    print(f"▶ Calling Google Model Garden: {model} (Project: {project}, Location: {location})...")
    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers)
    
    max_retries = 4
    data = None
    for attempt in range(1, max_retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=240 if images else 90) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            break
        except urllib.error.HTTPError as e:
            err = e.read().decode("utf-8", "replace")
            if e.code in (429, 500, 502, 503, 504) and attempt < max_retries:
                import random
                backoff = (2 ** attempt) + random.uniform(0.5, 1.5)
                print(f"⚠️ Vertex API Error (HTTP {e.code}). Retrying in {backoff:.1f}s (Attempt {attempt}/{max_retries})...")
                time.sleep(backoff)
                continue
            raise RuntimeError(f"Vertex API Error (HTTP {e.code}): {err}")
        except (urllib.error.URLError, TimeoutError) as e:
            if attempt < max_retries:
                import random
                backoff = (2 ** attempt) + random.uniform(0.5, 1.5)
                print(f"⚠️ Network error: {e}. Retrying in {backoff:.1f}s (Attempt {attempt}/{max_retries})...")
                time.sleep(backoff)
                continue
            raise
        
    candidates = data.get("candidates", [])
    if not candidates:
        raise ValueError(f"No candidates returned: {data}")
        
    parts = candidates[0].get("content", {}).get("parts", [])
    image_data = None
    for p in parts:
        if "inlineData" in p:
            image_data = p["inlineData"].get("data")
            break
            
    if not image_data:
        raise ValueError(f"No inlineData image found in Gemini response parts: {[list(p.keys()) for p in parts]}")
        
    raw_bytes = base64.b64decode(image_data)
    out.write_bytes(raw_bytes)
    print(f"✅ Generated image saved to: {out} ({len(raw_bytes)} bytes)")
    return out


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate images via Gemini 3.1 Flash Image on Vertex AI.")
    parser.add_argument("prompt", help="Visual image prompt")
    parser.add_argument("-o", "--out", required=True, help="Output PNG path")
    parser.add_argument("--project", default="vanna-mcp", help="GCP project ID")
    parser.add_argument("--location", default="global", help="Vertex AI region")
    parser.add_argument("--model", default="gemini-3.1-flash-image", help="Model name")
    parser.add_argument("--temperature", type=float, default=0.4, help="Sampling temperature")
    args = parser.parse_args()
    
    generate_gemini_image(
        prompt=args.prompt,
        output_path=args.out,
        project=args.project,
        location=args.location,
        model=args.model,
        temperature=args.temperature
    )
