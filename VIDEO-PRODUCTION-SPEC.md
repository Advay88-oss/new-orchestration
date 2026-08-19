# Competitor Visual Research & AI Video Production

The video arm of the GTM engine. Extends [GTM-ENGINE-SPEC.md](GTM-ENGINE-SPEC.md)
Phase P5, and feeds the same learning loop
([learn.py](pipeline/scripts/learn.py), §7–§8).

**One feature, stated plainly:** study how competitors build their launch videos
and motion graphics, extract the *pattern* (never the assets), then produce a
professionally-edited brand launch film for the tenant — Claude directing, AI
tools generating shots, and a deterministic brand layer on top — measured and
learned from like every other piece of content.

Status legend: **[BUILT]** exists this session · **[PARTIAL]** substrate exists ·
**[NEW]** to build.

---

## The one principle that decides the whole architecture

This is the same lesson the static cards already proved, extended to video — and
it is the single most important thing in this spec:

> **Code renders everything readable and branded. AI generates only texture and
> motion. The two are composited; AI output is never the final video.**

Why this matters: diffusion/video models still cannot render exact text, a logo,
or a UI screen reliably (the FLUX test that decided `render_visual.py`). A launch
video that lets AI generate its own titles will produce garbled typography at the
worst possible moment — the product reveal. So:

- **Runway / Veo / Firefly** generate *B-roll, environments, abstract motion,
  cinematic backgrounds* — the parts where "roughly right and beautiful" wins.
- **Remotion (React → MP4)** renders *every title, lower-third, logo animation,
  UI screen, stat, and CTA* — frame-exact, in the tenant's OKF palette, exactly
  as `render_visual.py` does for cards.
- **The editor composites** the two.

Section 8's "professional editing layer" *is* this principle. Keep it central or
the videos will look like a pile of AI clips, which is exactly what the spec says
to avoid.

---

## Stage 1 — Competitor visual analysis  [PARTIAL]

Study competitors' videos and motion graphics and extract the creative pattern.

**Sourcing the videos** [PARTIAL]: the competitor set already exists per tenant
(`okf-auri/competitors/` — 21 dossiers with handles/sites). Their launch/brand
videos live on YouTube, their sites, and X. The trend scout + browser can fetch
them; a new step downloads the actual video (yt-dlp is already available) for
frame analysis.

**The analysis** [NEW] — Claude (vision) watches the video and scores it on the
§8 checklist, producing a structured teardown:

| Dimension | What Claude extracts |
|---|---|
| Opening hook (first 3–5s) | what grabs attention, and why |
| Visual storytelling | the narrative spine |
| Camera / transitions | movement grammar, cut rhythm |
| Typography / motion graphics | type system, kinetic style |
| Product reveal | how/when the product appears |
| Animation style, 3D use | 2D/3D, illustration vs render |
| Colour & lighting | palette, mood |
| Pacing / editing rhythm | cuts per section, tempo |
| Sound design, music, VO | audio identity |
| Brand positioning | the claim the video makes |
| CTA / closing | the ask |
| Overall production quality | tier, budget signal |

**The output is a pattern, never the assets.** Copyright/impersonation line
(same as the written GTM engine): learn the grammar and the quality bar, express
them in the tenant's own brand. Store teardowns in
`okf-{tenant}/competitors/video-teardowns/`.

---

## Stage 2 — Creative brief + storyboard (Claude as director)  [NEW]

Claude converts the teardowns + the tenant OKF bundle into a **scene-by-scene
creative brief**:

- what happens in each scene, and *why that sequence works*
- the visual technique per beat, and the emotion it targets
- what to adapt to the tenant vs what to avoid
- a storyboard: `Hook → Problem → Product reveal → Proof → CTA` (the launch-video
  grammar), each beat with a shot description
- **downstream prompts**: exact prompts for the image, video, voice, and music
  tools, plus the Remotion scene spec for the branded overlays

Grounded in the tenant's arcs, facts tiers (only claimable facts appear), and
brand palette. Gated: the script/VO passes the OKF claim gate before anything
renders — a video says claims out loud, so the gate matters more, not less.

---

## Stage 3 — Keyframes (image generation)  [NEW]

Before motion, establish the look: key frames, product/UI shots, environments,
backgrounds. These lock a consistent visual language so the generated shots don't
drift. Tools: Firefly / an image model for texture and environments; Remotion for
any frame containing text or UI (rendered, not generated).

---

## Stage 4 — Shot generation (per shot, never the whole video)  [NEW]

Generate **individual shots**, review, iterate — never one-shot the whole film.

```
Scene 01 → Scene 02 → Scene 03 → Product reveal → Hero shot → CTA
   each generated, reviewed, regenerated independently
```

| Tool | Best for | Note |
|---|---|---|
| **Runway (Gen-4.x)** | recurring subjects/objects/environments, coherent style across shots | reference-based consistency — its strength; the spec's right call |
| **Google Veo 3.1** (Vertex) | best prompt adherence, native audio, 4K | runs on Vertex → metered by the **existing `vertex_spend_proxy`** |
| **Adobe Firefly** | commercial-safe generation, image→video/text→video, browser editing | when commercial-safety / Adobe workflow matters |
| **Kling 3.0** | 4K/60fps, cheaper per clip (~$0.45–0.70/5s) | volume B-roll |

Every readable element still comes from Remotion, composited over these.

---

## Stage 5 — Professional editing layer  [NEW]

AI clips are raw material, not the deliverable. The editor combines: generated
clips + brand assets + product/UI footage + **Remotion motion graphics,
typography, logo animation, CTA** + VO (ElevenLabs) + music (Suno / ElevenLabs
Music) + SFX + colour grade. Output: a film that reads as professionally
produced, in the tenant's identity.

- **Remotion** does most of this natively (React timeline → MP4), and is the
  branded-overlay renderer.
- **FFmpeg** (already used) stitches, muxes audio, burns captions.
- The tenant's OKF `brand/palette.md` + logo drive the overlay look — the same
  per-tenant wiring the cards use (Auri gold, Vanna violet).

---

## Stage 6 — Publish → measure → learn  [PARTIAL]

Same loop as the rest of the engine, now for video:

```
Creative decision → published video → audience response → performance → learning
```

`learn.py` already aggregates by abstract feature; video adds video-specific
features — **hook style, opening technique, pacing, transition style, VO
presence, shot count, production tier** — tagged per published video. The
learning is **cross-company and feature-level** (OKF V6 isolation holds): "fast
cold-open + kinetic type outperforms slow ambient intro" transfers between
tenants; no tenant's footage or claims cross over.

Over time the system answers §8's goal: *what visual storytelling works for which
company, audience, platform, objective, and market* — not generic prompts.

---

## Connector-based architecture

Claude is the reasoning/orchestration layer; specialised tools do production.
The engine picks the right tool per stage instead of forcing one model.

```
Competitor research ─► Visual analysis ─► Creative brief ─► Storyboard
   (dossiers,           (Claude vision,     (Claude director)  (Claude)
    yt-dlp)              teardown)                │
                                                  ▼
        Asset generation ─────────────────► Shot generation
        (Firefly/image, Remotion frames)     (Runway · Veo/Vertex · Firefly · Kling)
                                                  │
                                                  ▼
        Editing layer ──► Claim gate ──► Publish ──► Performance analysis
        (Remotion + FFmpeg + ElevenLabs   (OKF)      (learn.py:
         + Suno + brand assets)                       video features)
```

Connectors, each real: **Runway API**, **Adobe Firefly API**, **Veo via Vertex**
(reuses the spend proxy), **ElevenLabs API**, **Suno API**, **Remotion**
(self-hosted, reuses the headless Chrome the cards already use), **FFmpeg**,
**yt-dlp**. Claude routes between them.

---

## Honest status and prerequisites

| Component | Status |
|---|---|
| Per-tenant competitor set + dossiers | [BUILT] (Auri: 21) |
| Video download for analysis (yt-dlp) | [PARTIAL] — tool present, step unwritten |
| Claude vision teardown on the §8 checklist | [NEW] |
| Creative brief + storyboard | [NEW] |
| Keyframes / shot generation (Runway/Veo/Firefly) | [NEW] — needs API keys |
| Remotion branded-overlay renderer | [NEW] — reuses headless Chrome + OKF palette/logo wiring [BUILT] |
| Editing layer (FFmpeg) | [PARTIAL] — FFmpeg present |
| Claim gate on script/VO | [BUILT] |
| Video performance → learn | [PARTIAL] — `learn.py` extends cleanly |
| Spend cap on Veo | [BUILT] — `vertex_spend_proxy` already meters Vertex |

**Prerequisites, in order:**
1. **API keys**: Runway, Firefly, ElevenLabs, Suno (Veo already runs on the
   existing Vertex project). Same pattern as the pending X API — the engine
   never sees the raw values.
2. **The Remotion project** — the branded-overlay renderer. Highest-value new
   build; it is the video analog of `render_visual.py` and reuses the OKF
   palette/logo wiring already in place.
3. **The publishing bottleneck is unchanged and it applies harder here.** We
   just proved even a static post can't auto-publish to X via browser automation
   (X blocks it). A 60-second launch film is far more expensive to produce, so it
   must not be gated behind a broken publish path — settle publishing (X API /
   YouTube API / manual) *before* investing in video production, or the output
   has nowhere reliable to go.
4. **Cost discipline**: Veo ~$2/5s, others ~$0.45–0.70/5s; a 60s film with a
   handful of AI shots is tens of dollars, Remotion overlays ~free. The Vertex
   proxy caps Veo; add a per-render budget for the others.

---

## Recommended first vertical

Don't build the whole stack. Prove it on one 15–20s Auri intro:
1. Claude teardown of **2–3 Auri competitor videos** (Wealthsimple, Glint,
   Kinesis) → one creative brief.
2. A **Remotion** intro spine reading the Auri OKF palette + logo (branded
   overlays only — no AI yet). This alone is a real, on-brand motion asset and
   the reusable core.
3. Add **one** Veo/Runway B-roll shot behind it (via the metered proxy).
4. Gate the VO script, render, and — crucially — have a working publish target
   (YouTube API or manual) before calling it done.

That proves the code-renders-brand / AI-renders-texture split in motion, reuses
everything already built, and costs a few dollars — the smallest thing that
shows the whole pattern works.

**Sources** (tool landscape, verified earlier this session):
[Creatomate — video APIs](https://creatomate.com/blog/the-best-video-generation-apis),
[ModelsLab — Veo 3.1 vs Kling 3 vs Sora 2](https://modelslab.com/blog/api/veo-3-1-vs-kling-3-sora-2-ai-video-api-cost-2026),
[Remotion — building with AI](https://www.remotion.dev/docs/ai/),
[RenderComp — programmatic video 2026](https://rendercomp.com/blog/best-programmatic-video-tools-2026/).
