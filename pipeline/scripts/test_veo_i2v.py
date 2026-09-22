import os, sys, json, base64, urllib.request, urllib.error
from pathlib import Path
REPO_ROOT = Path('.').resolve()
sys.path.insert(0, str(REPO_ROOT))
from pipeline.scripts.veo_broll import _vertex_token

token = _vertex_token()
project = 'vanna-mcp'
location = 'us-central1'
model = 'veo-3.1-generate-001'

# 1x1 transparent png
dummy_png = base64.b64encode(b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82').decode()

host = f'https://{location}-aiplatform.googleapis.com'
base = f'{host}/v1/projects/{project}/locations/{location}/publishers/google/models/{model}'
headers = {'Authorization': f'Bearer {token}', 'x-goog-user-project': project, 'Content-Type': 'application/json'}

body = {
    'instances': [
        {
            'prompt': 'Vanna logo pulsing with light',
            'image': {'bytesBase64Encoded': dummy_png, 'mimeType': 'image/png'}
        }
    ],
    'parameters': {'durationSeconds': 6, 'aspectRatio': '16:9'}
}

req = urllib.request.Request(f'{base}:predictLongRunning', data=json.dumps(body).encode(), headers=headers, method='POST')
try:
    with urllib.request.urlopen(req, timeout=10) as r:
        op = json.loads(r.read())
        print('IMAGE-TO-VIDEO SUCCESS! Operation:', op.get('name'))
except urllib.error.HTTPError as e:
    print('HTTP Error:', e.code, e.read().decode('utf-8', 'replace')[:400])
except Exception as e:
    print('Exception:', e)
