#!/usr/bin/env python3
"""Generate a Veo 3.1 clip via the Gemini API (the surface that works on our
billed key — Vertex blocks media for this org). Reads GEMINI_API_KEY from
pipeline/.env. Submit -> poll -> download.

    python veo_gen.py --prompt "..." --out clip.mp4 [--model veo-3.1-fast-generate-preview] [--aspect 16:9]
"""
from __future__ import annotations
import argparse, json, os, sys, time, urllib.request
from pathlib import Path

BASE = "https://generativelanguage.googleapis.com/v1beta"


def key() -> str | None:
    root = Path(__file__).resolve().parents[2]
    for envf in (root / "pipeline" / ".env", root / ".env"):
        if envf.exists():
            for line in envf.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line.startswith("GEMINI_API_KEY=") or line.startswith("VEO_API_KEY="):
                    v = line.split("=", 1)[1].strip().strip('"').strip("'")
                    if v:
                        return v
    return os.environ.get("GEMINI_API_KEY") or os.environ.get("VEO_API_KEY")


def get(url: str) -> dict:
    with urllib.request.urlopen(url, timeout=90) as r:
        return json.loads(r.read())


def find_video(node):
    if isinstance(node, dict):
        for k, v in node.items():
            if k in ("uri", "fileUri", "videoUri") and isinstance(v, str) and v.startswith("http"):
                return ("uri", v)
            if k in ("bytesBase64Encoded", "videoBytes") and isinstance(v, str) and len(v) > 100:
                return ("b64", v)
            r = find_video(v)
            if r:
                return r
    elif isinstance(node, list):
        for it in node:
            r = find_video(it)
            if r:
                return r
    return None


def generate(prompt: str, out: str, model: str, aspect: str) -> bool:
    K = key()
    if not K:
        print(json.dumps({"ok": False, "reason": "no GEMINI_API_KEY in pipeline/.env"})); return False
    body = json.dumps({"instances": [{"prompt": prompt}], "parameters": {"aspectRatio": aspect}}).encode()
    req = urllib.request.Request(f"{BASE}/models/{model}:predictLongRunning?key={K}", data=body,
                                 headers={"Content-Type": "application/json"}, method="POST")
    try:
        op = json.loads(urllib.request.urlopen(req, timeout=90).read())
    except urllib.error.HTTPError as e:
        print(json.dumps({"ok": False, "http": e.code, "body": e.read().decode("utf-8", "replace")[:300]})); return False
    name = op.get("name")
    if not name:
        print(json.dumps({"ok": False, "resp": str(op)[:300]})); return False
    print(f"submitted {name}; polling...")
    for i in range(60):
        time.sleep(9)
        st = get(f"{BASE}/{name}?key={K}")
        if st.get("done"):
            if "error" in st:
                print(json.dumps({"ok": False, "op_error": st["error"]})); return False
            got = find_video(st.get("response", st))
            if not got:
                print(json.dumps({"ok": False, "no_video": str(st.get("response"))[:400]})); return False
            Path(out).parent.mkdir(parents=True, exist_ok=True)
            if got[0] == "b64":
                import base64
                Path(out).write_bytes(base64.b64decode(got[1]))
            else:
                dl = got[1] + (("&" if "?" in got[1] else "?") + f"key={K}")
                urllib.request.urlretrieve(dl, out)
            print(json.dumps({"ok": True, "out": out, "bytes": Path(out).stat().st_size}))
            return True
        print(f"  ...generating ({(i + 1) * 9}s)")
    print(json.dumps({"ok": False, "reason": "timed out"})); return False


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--prompt", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--model", default="veo-3.1-fast-generate-preview")
    ap.add_argument("--aspect", default="16:9")
    a = ap.parse_args()
    return 0 if generate(a.prompt, a.out, a.model, a.aspect) else 2


if __name__ == "__main__":
    sys.exit(main())
