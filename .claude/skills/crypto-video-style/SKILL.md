---
name: crypto-video-style
description: Produce short-form crypto/DeFi product-marketing videos — either the reference house style (kinetic type, big-number stat reveals, phone-mockup demos, brand cards) OR the premium brand-film system (Remotion, each tenant's REAL logo + palette + font, smooth transitions, distinct-topic scenes). Use when asked to make a promo/launch/teaser/brand video, animate a stat, add a cloned voiceover, or turn a campaign step into a branded motion clip. Reference styles reverse-engineered from four videos (Morpho "Onchain", Uniswap Earn, "swappy", Base "$5B+"); brand films built for Vanna + Auri.
argument-hint: "<what to make> [style: stat|kinetic|card|demo]"
allowed-tools: Bash, Read
user-invocable: true
---

# crypto-video-style

Give Claude a repeatable way to make on-brand crypto/DeFi marketing videos that
look like the reference set — not generic stock motion. The renderer is
`pipeline/scripts/render_video.py` (deterministic PIL frames → ffmpeg MP4, the
"Remotion role"); it reads the tenant palette + logo from the OKF bundle via
`OKF_BUNDLE`. AI B-roll (Runway/Veo) is an optional background layer, only when a
`RUNWAY_API_KEY` exists — the default is clean, claim-safe motion graphics.

Full evidence + per-video breakdown: `references/teardowns.md`.

---

## The brand-film system (current premium default)

The four PIL styles below are the quick/bulk path. **Premium launch films** now use
a dedicated Remotion system built from each tenant's **real brand** — actual logo,
palette, and font from the OKF bundle — not the generic accent-on-ground look. This
is the direction for hero/launch pieces.

Three compositions in `D:/vanna-remotion/src/` (registered in `Root.tsx`):

| Composition | File | Brand | Duration | Output |
|---|---|---|---|---|
| `VannaBrand` | `VannaBrand.tsx` | Vanna | 678f / ~22.6s | `pipeline/state/vanna-brand.mp4` |
| `AuriBrand` | `AuriBrand.tsx` | Auri | 704f / ~23.5s | `pipeline/state/auri-brand.mp4` |
| `VannaAuriFilm` | `VannaAuriFilm.tsx` | both | 602f / ~20s | `pipeline/state/vanna-auri-film.mp4` |

**Structure** (7 scenes, each a DISTINCT topic — variance comes from content, not a
repeated template): hook/trend → name/thesis → data panel → live stat (counts up) →
chips → breadth → sign-off. Every scene: eyebrow → gradient-emphasis headline →
panel/stat, generous spacing (no text overlap), a glow background that drifts subtly.
Smooth scene transitions via **`@remotion/transitions`** (fade + slide-from-right +
slide-from-bottom). The combined film switches brand *worlds* (palette+logo+font)
between halves, bound by a neutral open/close.

### Real brand tokens (source: `okf/brand/palette.md`, `okf-auri/brand/palette.md`)

| | Vanna | Auri |
|---|---|---|
| bg | `#0D0616` | `#100A0E` |
| primary | violet `#703AE6` / light `#9F7BEE` | gold `#EAD9AE` / cream `#F2E9D4` |
| accent | rose `#FF007A`, cyan `#32EEE2` | wine `#C4699A` / light `#E7B7D2` |
| font | **Plus Jakarta Sans** | **Geist** (+ Geist Mono for numbers) |
| logo | `public/vanna-logo.png` | `public/auri-logo.png` |
| emphasis gradient | violet → rose | wine → gold |

Fonts live in `public/fonts/` (`PlusJakartaSans.ttf`, `Geist.ttf`, `GeistMono.ttf`,
`clashdisplay-*`, `inter-*`), injected by `src/fonts.ts`. Numbers use `tabular-nums`.

### Render a brand film
```bash
cd /d/vanna-remotion && export ComSpec="C:\\Windows\\System32\\cmd.exe" COMSPEC="C:\\Windows\\System32\\cmd.exe" PATH="/c/nvm4w/nodejs:$PATH"
node_modules/.bin/remotion render src/index.ts VannaBrand "/d/new orchestration/pipeline/state/vanna-brand.mp4" --gl=angle
```
`--gl=angle` is **required** (WebGL via SwiftShader — machine has no GPU). `ComSpec`
must be set or node-24/npm spawn fails (`ERR_INVALID_ARG_TYPE: file undefined`).

### Logo matte fix
If a logo PNG ships with a baked dark background (Vanna's did — opaque `#131020` box),
key it to transparent before use — PIL brightness threshold on `max(r,g,b)`, alpha
ramps 0→255 above the bg, save to `public/`. Auri's logo was already alpha-transparent.

### Claim discipline (baked into the films)
- **Auri** uses ONLY Tier-A facts (`okf-auri/facts/tier-a.md`) and obeys
  `okf-auri/rules/`: **no card, no Interac/fiat funding, no remittance/KYC**,
  **Ethereum mainnet only**, never "production/enterprise-grade", **borrowing always
  shows liquidation risk**, sign-off states "non-custodial — not a bank deposit, not
  insured". Quotable numbers only: 22+ tonnes, 1,792 bars, 3.75% APR, quarterly BDO.
- **Vanna** stays testnet + illustrative, **no high-APY hero** (the old 378% APY was
  the failure mode); lead with the liquidation-line / health-factor reveal instead.

## Voiceover (cloned voice)

Machine has **no GPU + 7.3 GB RAM** → OmniVoice (613M-param diffusion TTS) won't run
locally — the RAM wall, not just speed. Route that works, free:

1. **Clone on free Colab T4** — steps in `pipeline/scripts/omnivoice_colab.md`
   (upload a 15–30s clean reference clip → generates `vo.wav`).
2. **Mux locally** (pure ffmpeg, fits the machine):
   ```bash
   python pipeline/scripts/add_voice.py --video pipeline/state/vanna-brand.mp4 \
     --voice pipeline/state/vo.wav --out pipeline/state/vanna-brand-vo.mp4
   ```
   Optional `--music bed.mp3` (looped + ducked ~14 dB under the VO via sidechain).
   Video is the master clock; VO is padded with trailing silence, never stretched.

VO script (timed to the films) lives in `pipeline/state/vo-script.md`. Use a voice you
have the right to clone. OmniVoice supports CUDA / Apple MPS / Intel XPU — **not** this
box's AMD iGPU, so local is CPU-only and impractical.

## The house style (what makes it look "right")

**Format.** Square 1080×1080 (feed) or 9:16 for shorts. Short: 4–16s per clip; a
long explainer is many short scenes cut together, not one long take.

**Typography is the star.** Heavy geometric-grotesque sans (Helvetica Now / Inter /
SF / Arial-bold as the local fallback). Hero text is BIG and bold; captions are
regular/thin and small. One idea per frame. Numbers are enormous.

**Color = one accent, one ground.** Minimal: a single dominant accent over black,
light-grey, or a blue gradient. High contrast. White / near-white text. Per look:
| Look | Ground | Accent | Text |
|---|---|---|---|
| stat reveal | blue **gradient** glow | electric blue `#2f7bff` | white |
| kinetic type | flat **light-grey** `#e8e8e8` (or dark) | blue squares `#2f7bff` | near-black (or white on dark) |
| app demo | **dark** / pure black, subtle grid | brand pink/blue | app-UI native |
| brand card | solid accent or dark | brand color | white |

**Motion / edit grammar.**
- Word-by-word reveals (fade+rise), one phrase at a time — never a paragraph.
- Big number scales 0.8→1.0 + fades in; label follows.
- Fast scene cuts on beat; the *ground color flips* between scenes (blue → light → dark).
- Micro-UI chips float in as decoration + proof: date pills (`Aug 4, 2026 · 45d`),
  APY badges, and short **`0x…` address tags** with a small accent square.
- Phone mockups hold a real app screen recording with **tap ripples** on CTAs.
- Structure = **brand intro card → body (demo or kinetic) → brand outro card**
  (logo + `domain.xyz`).

**Decorative motifs (use sparingly):** small floating accent squares, `0x` hex
tags, pixelated/rounded logo tiles, glossy gradient orbs, faint circuit-grid bg.

## Produce it — the four styles

Palette/logo come from the tenant bundle: prefix every command with
`OKF_BUNDLE=okf` (Vanna) or `OKF_BUNDLE=okf-auri` (Auri). `--accent` overrides.

**1. `stat` — big-number flex** (ref: Base "$5B+").
```bash
echo '{"stat":"$5B+","label":"Total Deposits on Base"}' > /tmp/b.json
OKF_BUNDLE=okf python pipeline/scripts/render_video.py --brief /tmp/b.json --out clip.mp4 --style stat --bg gradient --accent "#2f7bff"
```
Use for: a single proof point / milestone / metric.

**2. `kinetic` — word-by-word typography** (ref: Morpho "Onchain").
```bash
echo '{"words":["Payments were the easy half.","Credit is the wedge.","Agents can pay.","They cannot borrow."],"hex_tag":"0xVANNA"}' > /tmp/b.json
OKF_BUNDLE=okf python pipeline/scripts/render_video.py --brief /tmp/b.json --out clip.mp4 --style kinetic --bg light --accent "#2f7bff"
```
Use for: a thesis / narrative told in punchy fragments. `--bg dark` for the outro half.

**3. `card` — hook + emphasis + CTA** (the campaign default).
```bash
echo '{"headline":"CEXs freeze your capital.","emphasis":"Stay in control.","body":"Unified margin keeps collateral active.","cta":"Read the thesis"}' > /tmp/b.json
OKF_BUNDLE=okf python pipeline/scripts/render_video.py --brief /tmp/b.json --out clip.mp4 --style card
```

**4. `demo` — real app screen-recording, branded** (ref: Uniswap Earn, "swappy";
built from Vanna's own workflow recordings). Executable via `build_demo_video.py`:
it renders a brand intro card → letterboxes the recording onto the tenant brand
ground at 1080² → renders a brand outro card, and concatenates them.
```bash
OKF_BUNDLE=okf python pipeline/scripts/build_demo_video.py \
  --recording "path/to/workflow.mp4" --title "Supply XLM. Earn onchain." \
  --subtitle "Farm" --cta "Try the testnet" --domain "vanna.finance" \
  --accent "#8B5CF6" --max-body 20 --out demo-farm.mp4
```
Use one recording per workflow (Vanna's map: Portfolio · Trade/Swap · Farm ·
Analytics). Gotchas already handled: the recording is scaled+padded with
`setsar=1` (concat rejects mismatched pixel-aspect); audio is dropped; `--max-body`
trims length. For a fancier body, add tap-ripple highlights or a kinetic caption
overlay before concat.

## Compose a multi-scene video (intro → body → outro)

Render each scene, then concat with ffmpeg (crossfade optional):
```bash
printf "file '%s'\n" intro.mp4 body.mp4 outro.mp4 > /tmp/list.txt
ffmpeg -y -f concat -safe 0 -i /tmp/list.txt -c copy full.mp4
# crossfades instead of hard cuts:
# ffmpeg -i a.mp4 -i b.mp4 -filter_complex "xfade=transition=fade:duration=0.4:offset=6" out.mp4
```
Outro card: `--style card` with the logo + a one-line CTA and the domain.

## Two render engines
- **PIL + ffmpeg** (`render_video.py`) — fast, zero-setup, good. Default.
- **Remotion** (`D:/vanna-remotion/`) — real-DOM, frame-exact, best typography/UI
  fidelity. This is where the **brand-film system** lives (see above). Compositions:
  `VannaBrand`, `AuriBrand`, `VannaAuriFilm` (premium brand films) plus the earlier
  `Stat`, `Kinetic`, `Mockup`, `Teaser`, `Broll` (edit `src/*.tsx`; props in
  `src/Root.tsx`). Render (MUST set `ComSpec` or npm/node-24 spawn fails; add
  `--gl=angle` for the WebGL substrate):
  ```bash
  cd /d/vanna-remotion && ComSpec="C:\\Windows\\System32\\cmd.exe" \
    node_modules/.bin/remotion render src/index.ts Mockup out.mp4
  ```
  Use Remotion for hero/launch pieces; PIL for quick/bulk (per-campaign-day) clips.

## Fonts
- **Brand films** use each tenant's real font: **Plus Jakarta Sans** (Vanna),
  **Geist** + Geist Mono (Auri). Bundled in `/d/vanna-remotion/public/fonts/`,
  injected by `src/fonts.ts`.
- **Reference PIL styles** default to Inter (`pipeline/assets/fonts/inter-*.ttf`) —
  matches the reference grotesque look. Clash Display is available for premium display.
- For licensed faces (e.g. Helvetica Now), drop the `.ttf`s in and set
  `VANNA_FONT_DIR` (PIL) / add the @font-face in `fonts.ts` (Remotion). Do not
  redistribute licensed fonts.

## Music
`add_music.py --video clip.mp4 --audio track.mp3 --out out.mp4` muxes a royalty-free
track (loops/trims/fades). **Brand films ship SILENT by default** — a low placeholder
hum reads worse than silence, so add a *real* bed or a cloned VO (see Voiceover) rather
than the synth placeholder. For VO + ducked bed together, use `add_voice.py --music …`.
Supply your own licensed track.

## AI B-roll (Runway/Veo)
`runway_broll.py --prompt "…" --out broll.mp4` generates abstract branded footage —
**requires `RUNWAY_API_KEY`** (you set it in the env; never committed). Then composite
branded text over it (`compose_over_broll`) or drop it in as a scene. Without a key
it's a no-op and the clean motion-graphics card is the claim-safe default.

## Rules
- Claim-safe: for Vanna (testnet) never put token/mainnet/production-grade on a
  frame; run the copy through `claim_safety_gate.py` before shipping.
- One message per frame; if you need two ideas, cut to a new scene.
- Never post — deliverables stop at file + Telegram + dashboard unless told otherwise.
