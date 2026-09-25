"""Embeddings — one space for text and images.

`gemini-embedding-2` embeds text and images into the same vector space
(checked 2026-09-25 against this project's API key), so "reference images
for this topic" is a nearest-neighbour search from the topic's text vector
to the image vectors — the job a CLIP/SigLIP model would otherwise do.

Vectors are 768-d float32, L2-normalised, stored as BLOBs.
"""
from __future__ import annotations

import base64
import json
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Optional, Sequence

import numpy as np

MODEL = "gemini-embedding-2"
DIM = 768
API = "https://generativelanguage.googleapis.com/v1beta/models/"


def _key() -> str:
    from pipeline.gtm_os.agent_runtime import _api_key
    k = _api_key()
    if not k:
        raise RuntimeError("no GEMINI_API_KEY for embeddings")
    return k


def _post(method: str, body: dict, *, retries: int = 3) -> dict:
    req = urllib.request.Request(API + MODEL + ":" + method, data=json.dumps(body).encode(),
                                 headers={"x-goog-api-key": _key(),
                                          "Content-Type": "application/json"})
    for i in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 503) and i < retries - 1:
                time.sleep(2 * (i + 1))
                continue
            raise RuntimeError("embedding failed: " + e.read().decode()[:300]) from None
        except urllib.error.URLError:
            if i < retries - 1:
                time.sleep(2 * (i + 1))
                continue
            raise
    raise RuntimeError("embedding failed")


def _norm(v: Sequence[float]) -> np.ndarray:
    a = np.asarray(v, dtype=np.float32)
    n = float(np.linalg.norm(a)) or 1.0
    return a / n


def texts(items: list[str], *, task: str = "RETRIEVAL_DOCUMENT") -> list[np.ndarray]:
    """Embed many texts, in batches of 50."""
    out: list[np.ndarray] = []
    for i in range(0, len(items), 50):
        batch = items[i:i + 50]
        r = _post("batchEmbedContents", {"requests": [
            {"model": "models/" + MODEL, "content": {"parts": [{"text": t[:8000]}]},
             "taskType": task, "outputDimensionality": DIM} for t in batch]})
        out += [_norm(e["values"]) for e in r["embeddings"]]
    return out


def query(text: str) -> np.ndarray:
    return texts([text], task="RETRIEVAL_QUERY")[0]


def image(path: Path) -> np.ndarray:
    mime = "image/png" if path.suffix.lower() == ".png" else "image/jpeg"
    r = _post("embedContent", {"content": {"parts": [{"inline_data": {
        "mime_type": mime, "data": base64.b64encode(path.read_bytes()).decode()}}]},
        "outputDimensionality": DIM})
    return _norm(r["embedding"]["values"])


def to_blob(v: Optional[np.ndarray]) -> Optional[bytes]:
    return None if v is None else np.asarray(v, dtype=np.float32).tobytes()


def from_blob(b: Optional[bytes]) -> Optional[np.ndarray]:
    return None if not b else np.frombuffer(b, dtype=np.float32)
