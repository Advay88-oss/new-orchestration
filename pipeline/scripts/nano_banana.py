#!/usr/bin/env python3
"""Nano Banana (gemini-2.5-flash-image) -> PNG. Reads GEMINI_API_KEY from
pipeline/.env. Usage: python nano_banana.py "prompt" out.png"""
import base64, json, sys, urllib.request
from pathlib import Path

B = "https://generativelanguage.googleapis.com/v1beta"
MODEL = "gemini-2.5-flash-image"


def key():
    for line in (Path(__file__).resolve().parents[2] / "pipeline" / ".env").read_text().splitlines():
        if line.startswith("GEMINI_API_KEY="):
            return line.split("=", 1)[1].strip().strip('"').strip("'")


def gen(prompt, out):
    K = key()
    body = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"responseModalities": ["IMAGE"]},
    }).encode()
    req = urllib.request.Request(f"{B}/models/{MODEL}:generateContent?key={K}", data=body,
                                 headers={"Content-Type": "application/json"}, method="POST")
    try:
        r = json.loads(urllib.request.urlopen(req, timeout=90).read())
    except urllib.error.HTTPError as e:
        print(json.dumps({"ok": False, "http": e.code, "body": e.read().decode()[:200]}))
        return False
    for p in r.get("candidates", [{}])[0].get("content", {}).get("parts", []):
        if "inlineData" in p:
            Path(out).parent.mkdir(parents=True, exist_ok=True)
            Path(out).write_bytes(base64.b64decode(p["inlineData"]["data"]))
            print(json.dumps({"ok": True, "out": out, "bytes": Path(out).stat().st_size}))
            return True
    print(json.dumps({"ok": False, "reason": "no image part", "resp": str(r)[:200]}))
    return False


if __name__ == "__main__":
    sys.exit(0 if gen(sys.argv[1], sys.argv[2]) else 2)
