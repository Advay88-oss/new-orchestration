# Motion direction — A09 Video Production

**Status: not built. Recorded 2026-09-22 so the brief is not lost.**
A09 currently renders Veo 3.1 cinematic shots. The founder has rejected that
register. Do not refine the cinematic prompts; the direction below replaces
them.

---

## What is wrong with the current videos

Veo produces film. A slow dolly through an obsidian void with a key light
grazing a machined object is a *product film* — it has mood, depth of field,
camera movement and a sense of place. One frame came back as a glowing Bitcoin
coin in a vault, which is both the wrong product and the wrong genre.

The problem is not prompt quality. It is that a text-to-video model's whole
competence is cinematography, and cinematography is not what these posts need.

## What is wanted instead

> "simple video explaining about the post or visuals we have created… Vanna
> colour background, some transitions and basic motion graphics"

A motion graphic, not a shot. Specifically:

- The **same Vanna ground** the still assets use — the docs hero gradient,
  hardcoded, unchanged for the duration. No camera move across it, no parallax.
- The post's own **archetype, animated**. The threshold column fills; the
  isolation grid lights one cell; the composition bar grows its segments; the
  sequence advances marker by marker. The video explains the still, and is
  built from the same elements.
- **Transitions, not camera work.** Fades, wipes, a value counting up, a line
  drawing itself on. Everything moves in the plane. No dolly, no orbit, no
  rack focus, no depth of field.
- **Typography carries the argument**, exactly as in the stills: headline in,
  supporting line in, figure resolves, footnote. Composited, never generated.
- 6–10 seconds. Legible muted, because most of these autoplay silently.

## How to build it

**Not Veo.** Veo cannot make a flat motion graphic; asking it to is asking a
cinematographer to make a slide transition. The archetype renderers already
produce every frame element deterministically, so the honest path is:

1. Extend each archetype renderer to emit a **frame sequence** — it already
   draws the ground, the figure and the type, so animating means drawing them
   at N states rather than one.
2. Encode with FFmpeg. Already a dependency; the creative judge uses it to pull
   a frame from the MP4.
3. Where a generated element is needed (the frosted figure in A13, the grid in
   A4), generate it **once** as a still and move it in the plane — the model
   renders one frame, not the motion.

This keeps the guarantee the stills have: every word is composited, so nothing
published can be misspelt, and the background is byte-identical to the post it
accompanies.

**Remotion** is already in the repo (`remotion-video/`) and is the obvious
alternative to hand-rolled PIL frames if the sequences get complex. Check what
state it is in before committing to it — it was last touched before this work
began.

## What Veo is still good for

Nothing in this system, on current direction. If a genuinely cinematic asset is
ever wanted — a launch film, not a post — Veo is the right tool and the
existing A09 path can be revived from git history rather than rewritten.
