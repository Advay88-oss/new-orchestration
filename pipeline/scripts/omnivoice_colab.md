# Clone a voice with OmniVoice on free Colab GPU → get vo.wav

OmniVoice (613M-param diffusion TTS) won't fit comfortably on a 7 GB / no-CUDA
laptop. Run it on Colab's free T4 (16 GB VRAM), download the wav, mux locally.

## Steps
1. Open https://colab.research.google.com → New notebook.
2. Runtime → Change runtime type → **T4 GPU** → Save.
3. Paste the cells below, run in order.
4. When prompted, upload your **reference voice clip** (`ref.wav`, ~15–30s, one
   speaker, clean, minimal noise/music).
5. Download `vo.wav` at the end.

---

### Cell 1 — install
```python
!pip -q install git+https://github.com/k2-fsa/OmniVoice.git soundfile
```

### Cell 2 — upload your reference voice clip
```python
from google.colab import files
up = files.upload()            # pick your ref.wav (or .mp3)
ref = list(up.keys())[0]
print("reference:", ref)
```

### Cell 3 — the script (already timed to the film)
```python
lines = [
    "Your positions live across five wallets and ten tabs.",
    "Vanna brings all of DeFi into one account.",
    "Spot, perps, options, yield and lending — margined together, and non-custodial.",
    "One health check shows your liquidation line, before you cross it.",
    "Gasless, session keys, always in your custody.",
    "Three integrations. One source of truth.",
    "Vanna. Composable credit on Stellar.",
]
text = " ".join(lines)
```

### Cell 4 — generate (zero-shot clone of your ref voice)
```python
from omnivoice import OmniVoice
import soundfile as sf, torch

model = OmniVoice.from_pretrained("k2-fsa/OmniVoice", device_map="cuda:0", dtype=torch.float16)
audio = model.generate(text=text, ref_audio=ref)   # ref_text optional (Whisper auto-transcribes)
sf.write("vo.wav", audio[0], 24000)
print("done -> vo.wav")
```

### Cell 5 — download
```python
from google.colab import files
files.download("vo.wav")
```

---

## Then locally (fits your machine — just ffmpeg)
Drop `vo.wav` into `pipeline/state/`, then:

```bash
cd "D:/new orchestration"
python pipeline/scripts/add_voice.py \
  --video pipeline/state/vanna-brand.mp4 \
  --voice pipeline/state/vo.wav \
  --out   pipeline/state/vanna-brand-vo.mp4
```

Add a bed too (optional): `--music pipeline/state/bed.mp3` (looped + ducked under the VO).

## Notes
- If the read runs longer than 22.6s, tell me — I'll retime the film to the VO
  (extend scenes) rather than clip the voice.
- Use a voice you have the right to clone (your own, or with consent).
- If Colab's per-line sync matters, I can switch the notebook to emit vo_1..vo_7
  and place each at its scene start.
```
