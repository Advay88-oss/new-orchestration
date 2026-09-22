import base64
import json
import os
import urllib.request
import urllib.error
from pathlib import Path

img_path = Path(r"C:\Users\Advay Anand\AppData\Roaming\Hermes\composer-images\image_14f935.png")
if not img_path.exists():
    print(f"File not found: {img_path}")
    exit(1)

b64_data = base64.b64encode(img_path.read_bytes()).decode("utf-8")

# Let's get access token using gcloud or ADC
import subprocess
gcloud = r"C:\Users\Advay Anand\AppData\Local\Google\Cloud SDK\google-cloud-sdk\bin\gcloud.cmd"
try:
    token = subprocess.check_output([gcloud, "auth", "application-default", "print-access-token"], timeout=60, text=True).strip()
except Exception as e:
    token = None

if token:
    url = "https://us-central1-aiplatform.googleapis.com/v1/projects/sales-agent-504607/locations/us-central1/publishers/google/models/gemini-2.5-flash:generateContent"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    payload = {
        "contents": [{
            "role": "user",
            "parts": [
                {"inlineData": {"mimeType": "image/png", "data": b64_data}},
                {"text": "Transcribe every single detail, error, text, button, component, and stack trace in this screenshot. Explain what error occurred, which file and line number caused it, and what is broken."}
            ]
        }]
    }
    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            print(data["candidates"][0]["content"]["parts"][0]["text"])
    except urllib.error.HTTPError as e:
        print("HTTP error:", e.code, e.read().decode("utf-8"))
else:
    print("No token available")
