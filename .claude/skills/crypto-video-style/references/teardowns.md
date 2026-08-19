# Reference video teardowns

Four crypto/DeFi product-marketing videos analysed frame-by-frame (via the
`/watch` skill — yt-dlp/ffmpeg frame extraction). The house style in `SKILL.md`
is derived from these. Ecosystem: Morpho / Base / Uniswap / a "swappy" wallet.

## V1 — Uniswap Earn (16s, square) — *app demo*
- **Ground:** near-black with a subtle dot/line grid.
- **Intro:** two rounded app-icon tiles side by side (Uniswap pink unicorn + Morpho
  blue butterfly) with a small caption "Uniswap Earn".
- **Body:** a single iPhone mockup, centered, running a guided app-UI flow —
  USDC wallet ($1.00, balance $14,399, chart, 1H/1D/1W tabs) → "Confirm deposit"
  sheet ($1,000, 5.23% APY, projected earnings) → **pink "Deposit" button with a
  tap ripple**.
- **Type:** native app UI — clean sans, light app on dark ground.
- **Accents:** Uniswap pink/magenta + blue. **Takeaway:** product demo = real
  screen recording in a phone frame on a dark grid, CTA tap ripples.

## V2 — "swappy" wallet (4.5s, landscape) — *app demo, dark mode*
- **Ground:** pure black, phone centered.
- **Body:** dark-mode wallet ($439.17, Swap/Buy/Send/Receive row) → "Earn with
  USDT" sheet (Est. APY 3.64%, total deposits, white "Deposit" button).
- **Accents:** magenta/pink on black; token rows with coin glyphs.
- **Takeaway:** same demo pattern as V1 but a *dark-mode* app; short, loopable.

## V3 — Morpho "Onchain" (66s, landscape) — *kinetic typography* (most edited)
- **Structure (color flips per scene):**
  1. **Intro:** solid **blue** card, pixelated logo mark + "Onchain" wordmark
     (thin light sans), tiny `0x5A80` tag.
  2. **Body:** flat **light-grey** ground with faint circuit lines; **bold black
     word-by-word reveals** — "at", "and stay alerted" — one phrase at a time.
  3. Floating **micro-UI pills** (`Aug 4, 2026 · 45d · ⏱`), **blue accent squares**,
     and **`0x…` hex address tags** as decoration/proof.
  4. **Outro:** **dark** card, Morpho butterfly mark + "markets · morpho · org".
- **Type:** heavy grotesque for the reveals; mono-ish for hex tags.
- **Edits:** real scene cuts (27 scene-changes in 66s), fast pacing.
- **Takeaway:** the signature look — kinetic text + blue squares + hex tags, ground
  color flipping blue→light→dark, brand cards top and tail.

## V4 — Base "$5B+" (8s, square) — *stat reveal*
- **Ground:** glossy **blue gradient orb** (light glow top-right).
- **Body:** enormous bold white **"$5B+"** scales/fades in, "Total Deposits on
  Base" subhead below, two small logo chips bottom-left.
- **Takeaway:** big-number flex — one metric, huge type, gradient ground, logo chips.

## Cross-cutting patterns → the style system
- One accent + one ground; white/near-white text; extreme type-size contrast.
- One idea per frame; narrative = many short scenes, not one take.
- Reveals (word rise/fade, number scale), ground-color flips, floating chips.
- `0x` hex tags + accent squares are the recurring "onchain" signature.
- Brand intro/outro cards bookend the body.
- Reproduced in `render_video.py`: `stat` = V4, `kinetic` = V3, `card` = generic,
  `demo` (V1/V2) needs a real screen recording composited into a phone frame.
