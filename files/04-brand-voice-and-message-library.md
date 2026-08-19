# 04 — Brand Voice, Design System & Message Library

---

## PART A — VOICE

## 1. Voice attributes

| Attribute | What it means in practice |
|---|---|
| **Professional yet approachable** | Not dumbed down, not showing off. Explain a Greek, don't assume it. |
| **Empowering** | "You can run this." The user is capable; the tooling was the missing part. |
| **Educational** | Teach the mechanism. Vanna's edge is that its mechanism is genuinely interesting. |
| **Confident** | Backed by real architecture. State things plainly; no hedging theatre. |
| **Transparent** | Name the risks. Vanna's own docs disclose the debt-accrual trade-off — that honesty *is* the brand. |

## 2. Register and craft rules

**Do:**
- Write in **short declaratives**. The live site's rhythm is two-beat: *"Credit that composes. Leverage that holds."* / *"Isolated margin walls you in. Unified sets you free."* / *"Stop gambling. Start strategizing."* Reuse this cadence.
- Use **contrast structures** — the whole brand is built on "they make you choose / we do both."
- Lead with the **user's problem in their words**, not with the architecture. "Managing a leveraged book is a full-time job" before "cross-margined solvency ratio."
- Use **concrete numbers and named venues**. $10,000 → $30,000. BTC long / BTC short. Health 2.4 → 1.3 → 2.1.
- Use **second person**. "It caught the dip you slept through."
- Let the **em dash** carry the reveal — it's the site's signature punctuation.
- Name mechanisms precisely: *health factor*, *cross-margined*, *delta-neutral*, *utilization*, *self-collateralization*.

**Don't:**
- Crypto hype register: moon, wen, WAGMI, ape, degen, LFG, gm.
- FOMO or scarcity pressure.
- Guaranteed or implied returns.
- Jargon without a translation clause.
- Emoji in long-form or technical content. (Sparing use acceptable in social.)
- Exclamation marks. The brand does not shout.
- "Revolutionary", "game-changing", "next-gen", "seamlessly", "leverage" as a verb meaning "use".

## 3. The three narrative arcs (pick one per asset; never mix all three)

**Arc 1 — Capital efficiency.** *Your collateral is doing one job. It should be doing six.* → isolated vs unified margin → 10× credit → one health factor. **Audience: traders, institutions.**

**Arc 2 — Risk relief.** *Leverage is easy. Not getting liquidated is the hard part.* → risk guardian → health factor discipline → "leverage anywhere, without getting liquidated." **Audience: retail traders, yield farmers, LPs.**

**Arc 3 — Agentic credit.** *Agents can pay. Agents can't borrow.* → the missing layer → MCP/CLI/SDK → Agent Score → x402. **Audience: builders, agent frameworks, investors, Delphi-type funds.**

---

## PART B — DESIGN SYSTEM

> Source: `vanna-brand-guidelines` v1.0 (Feb 2026), in production use. Any generated visual asset, social template, landing page or slide must comply.

## 4. Typography

**Font:** **Plus Jakarta Sans** — `font-family: var(--font-plus-jakarta-sans), system-ui, sans-serif;`
Never mix fonts. System fonts only as fallback.

**Headings (Semibold 600):** H1 80/96 · H2 64/87 · H3 48/72 · H4 40/60 · H5 34/51 · H6 28/42 · H7 24/36 · H8 20/36 · H9 16/24 · H10 14/21 · H11 12/18 · H12 10/15 — classes `.text-h1`…`.text-h12`

**Body (Regular 400):** Subtext 20/30 · Body1 16/24 · Body2 14/21 · Body3 12/18 · Body4 10/15 · Body5 8/12 — classes `.text-subtext`, `.text-body-1`…`.text-body-5`

**Buttons (Semibold 600):** Large 20 · Medium 16 · Small 12 — `.text-btn-lg`, `.text-btn-md`, `.text-btn-sm`

**Text colour themes:** `.text-heading` #1F1F1F · `.text-paragraph` #4B5563 · `.text-label` #1F1F1F · `.text-placeholder` #9CA3AF

Use **monospace for numerical data** (prices, amounts) and for addresses (truncated).

## 5. Colour

**Base:** dark `#111111` · white `#FFFFFF` · platinum `#F7F7F7`

**Gray:** 50 `#F4F4F4` · 100 `#DFDFDF` · 200 `#BFBFBF` · 300 `#A9A9A9` · 400 `#949494` · 500 `#777777` · 600 `#595959` · 700 `#2C2C2C` · 800 `#1E1E1E` · 900 `#111111`

**Primary — Violet:** 50 `#F1EBFD` · 100 `#D3C2F7` · 200 `#BDA4F4` · 300 `#9F7BEE` · 400 `#8D61EB` · **500 `#703AE6` (primary)** · 600 `#6635D1` · 700 `#5029A3` · 800 `#3E207F` · 900 `#2F1B61`

**Primary — Rose:** 50 `#FFE6F2` · 100 `#FFB0D6` · 200 `#FF8AC2` · 300 `#FF54A6` · 400 `#FF3395` · **500 `#FF007A` (primary)** · 600 `#E8006F` · 700 `#B50057` · 800 `#8C0043` · 900 `#6B0033`

**Secondary — Imperial Red:** **500 `#FC5457` (key secondary)** · plus 50 `#FEEEEE` → 900 `#6A2325`

**Secondary — Electric Blue:** **500 `#32EEE2`** · 600 `#22CED9` · 700 `#24A0A9` · 800 `#1C7C83` · 900 `#155F64` · 50 `#EBFCFD` → 400 `#5BE8F1`

**Secondary — Magenta:** 500 `#3E2EE0` · 600 `#2E2CD9` · 700 `#2440A9` (note: the 50–400 ramp in the source file duplicates Electric Blue — treat as a known bug and prefer Electric Blue or Violet)

**Brand gradient:**
```css
.bg-gradient { background-image: linear-gradient(135deg, #FC5457 10%, #703AE6 80%); }
```

**Semantic usage:**
- Primary action → Violet-500 or the gradient
- Destructive / sell / short / negative → Imperial Red-500 `#FC5457`
- Success / buy / long / positive → Electric Blue-500 `#32EEE2` (Violet also acceptable for long)
- Table header bg `#111827` · disabled/gray bg `#F3F4F6` · borders `#E5E7EB` · input borders `#D1D5DB` · icons in inputs `#6B7280`
- Positive trends → gradient · negative trends → Imperial Red
- Maintain **WCAG AA** (4.5:1 for normal text)

**Observed in the live product (extends the token set):** the marketing site and video run on a **near-black indigo canvas** (~`#0B0B1E`–`#111111`) with violet/rose glow orbs, Electric Blue for confirmations and health-factor lines, Imperial Red for risk/short legs. Keep this.

## 6. Spacing, radius, stroke, shadow

**Spacing (px):** 0→2 · 1→4 · 2→8 · 3→12 · 4→16 · 5→20 · 6→24 · 7→32 · 8→40 · 9→48 · 10→56 · 11→64 · 12→72 · 13→80 · 14→120. **Never use off-scale values.**

**Radius (px):** 0→0 · 1→4 · 2→8 · 3→12 · 4→16 · 5→20 · 6→24 · 7→32 · 8→40 · 9→48 · 10→56 · 11→64 · 12→72 · 13→80 · `full`→999. Classes `.radius-0`…`.radius-13`, `.radius-full`.

**Stroke (px):** 0,1,2,3,4,5,6,8,10,12 → `.stroke-0`…`.stroke-9`.

**Shadow:**
```css
.shadow { box-shadow: 0px 7px 15px rgba(0,0,0,0.08), 0px 28px 28px rgba(0,0,0,0.07); }
```

## 7. Components

- **Buttons:** `.text-btn-*` sizing; primary = `bg-gradient` or violet/rose; secondary may use Imperial Red; radius `.radius-2`–`.radius-4` (8–16px).
- **Cards:** white or gray-50 bg; radius `.radius-3`–`.radius-5` (12–20px); `.shadow`; consistent padding from the scale.
- **Forms:** input borders Gray-300; focus Violet-500 or gradient; disabled Gray-100 bg; placeholder `.text-placeholder`; input icons Gray-500. **Number inputs must have spinners removed.**
- **Tables:** header bg Gray-900 `#111827`; striped rows Gray-100; borders Gray-200.
- **Scrollbars:** use `.scrollbar-thin` (thumb `#A7A7A7`, track `#F4F4F4`, 6px, hover `#777777`) or `.scrollbar-hide`. Never default browser scrollbars.
- **Wallet:** violet primary for connect; colour indicator for connection status; addresses in monospace, properly truncated.
- **Leverage display:** always show leverage clearly with appropriate warning colours.

**File layout for new components:** `/components/ui`, `/forms`, `/layout`, `/trading`. Always import `@/app/globals.css`.

**Quick reference:** Primary actions Violet-500/gradient · Destructive Imperial Red-500 · Success Electric Blue-500 · Neutral gray scale · Headings 600 · Body 400 · Buttons 600.

> ⚠️ The generic `brand-guidelines` skill inside `marketing.zip` describes **Anthropic's** brand (Poppins/Lora, `#d97757`). For anything Vanna, **the Vanna brand guidelines override it entirely.**

---

## PART C — MESSAGE LIBRARY

## 8. Headlines (live, approved)

**Hero:**
> **Credit that composes. Leverage that holds.**

Hero subhead:
> The undercollateralized credit layer for DeFi — one institution-grade margin account carrying your entire book across spot, perps, options, prediction and **AI-compute markets**, with up to **10× credit** and every drawdown in one venue offset by gains in another.

**Section headlines:**
- *Leveraged credit that actually moves.*
- *Isolated margin walls you in. Unified sets you free.*
- *Managing a leveraged book is a full-time job. Vanna's agents make it run itself.*
- *Every word becomes a parameter.*
- *Flip through proven playbooks. Or write your own.*
- *However it's written, it hits the same rails.*
- *We underwrite behavior, not promises.*
- *Never get liquidated in your sleep.*
- *Plug in what you already have. Get credit that composes.*
- *Trusted by the ecosystem.*
- *The future of DeFi is composable — and agentic.*
- *Stop gambling. Start strategizing.*

**Brand card / video outro:**
> **Leverage Anywhere, Without Getting Liquidated**
> *Composable Credit Infrastructure*

**Meta description (SEO, live):**
> Vanna is the undercollateralized credit layer for DeFi. One institution-grade margin account carries your whole book across spot, perps, options, prediction and AI-compute markets — up to 10× credit, with a loss in one venue offset by gains in another. Built for traders, businesses, institutions, and agents.

## 9. Legacy headlines (still on record, lower priority)

- *Borrow 10×. Trade Anywhere. Professional-grade DeFi.*
- *Earn real yield. No IL. No ponzinomics.* (LP-facing — still strong)
- *TradFi Precision. DeFi Freedom.*
- *Here's how your $1,000 becomes $10,000 of trading power across DeFi.*
- *Vanna connects you to the protocols you love — with 10× more capital.*

## 10. The proof-point bank

Use these as the evidence layer under any claim.

| Claim | Proof |
|---|---|
| 10× is real, not marketing | Falls mathematically out of the borrow guard `(C+B)/(D+B) ≥ 1.1` → `B ≤ 10C` |
| Credit genuinely moves | TrackingToken values external Blend/Aquarius/Soroswap positions as collateral inside the same account |
| One health factor for the whole book | Stateless RiskEngine prices every collateral and position via one oracle into one solvency ratio |
| Risk isolation | Every user gets their **own deployed** SmartAccount contract with its own storage — a bug in one cannot affect another |
| Pool isolation | XLM and USDC pools are separate contracts; a problem in one cannot affect the other |
| Rates are honest | No kink point. Smooth polynomial. No governance votes, no fixed rates. Rounding always floors *against* the protocol (`mul_wad_down`/`div_wad_down`) |
| Safe upgrades | Registry-based address resolution — no hardcoded addresses in business logic |
| Zero custody | Vanna never holds keys. Scoped session keys; a separate Sign Service is the only signer |
| Agents can't bypass risk | Every write from MCP/CLI/SDK passes the same RiskEngine guard as a human transaction |
| We disclose trade-offs | Docs openly publish the borrow-shares debt-accrual understatement and why 1.1× absorbs it |
| LP yield is real | Comes from borrower interest via vToken exchange-rate growth — not token emissions, no impermanent loss |
| Delta-neutral is documented, not theoretical | Four fully documented strategies with risk/complexity ratings |

## 11. Ready-made copy blocks

**Elevator, 15 seconds:**
> Vanna is undercollateralized credit for DeFi. Deposit once, borrow up to 10×, and deploy that credit across spot, perps, options, prediction and AI-compute markets — all under one health factor. A loss in one venue is offset by a gain in another. And agents can call all of it as typed, policy-bounded tools.

**Elevator, 30 seconds (agent-first):**
> AI agents can already pay for APIs and control wallets. What they can't do is borrow. Every agent infrastructure layer — wallets, x402 payments, orchestration — assumes the agent already has capital. Vanna is the credit layer underneath: an agent gets its own margin account with hard on-chain limits, up to 10× undercollateralized credit, and every Vanna action as a typed tool over MCP. Behaviour builds an on-chain track record, and that record is what deepens the credit line. Smart contracts can be forked. Credit history can't.

**The problem paragraph:**
> Right now DeFi makes you choose. Overcollateralized lending gives you credit that moves anywhere but never exceeds your collateral. Perp and options venues give you leverage that exceeds your collateral but is trapped in one place. So a $10,000 book gets split across three logins, a gain on the spot exchange can't back the perp, and you babysit a separate liquidation on each screen. Vanna refuses the trade-off.

**The LP paragraph:**
> Supply XLM or USDC to a Vanna pool and receive vTokens. The exchange rate grows as borrowers repay interest — that's your yield, and it comes from real borrowing demand, not token emissions. No positions to manage, no impermanent loss. And because Vanna's borrowers can take up to 10× rather than being forced to overcollateralize, utilization runs structurally higher than a standard money market. Higher utilization is higher yield.

**The developer paragraph:**
> One `open_position` call, three front doors. Register `mcp.vanna.finance` and your agent has typed tools. Or script the CLI and cron it. Or import `@vanna/sdk`. All three hit the same account, the same risk engine, the same guardrails — and return the same response. Scoped session keys, no custody, the guardian running beneath all three.

**The risk-guardian paragraph:**
> Leverage isn't the hard part. Not getting liquidated at 3am is. Set a health-factor floor and the guardian watches the book continuously — trimming leverage, topping up collateral, or repaying debt inside the policy you defined. One night SOL dropped 12% at 03:14. Health went 2.4 → 1.3, liquidation sat at 1.10, and by 03:15 the position was back to 2.1. You slept through it.

## 12. CTAs

**Primary:** Launch App · Read the docs
**Secondary:** View Strategies · Start Earning · Integrate Your Protocol · Join Discord · Join Waitlist

**Placement pattern:** Hero → *Launch App* + *Read the docs* · After problem statement → *See how it works* · After LP section → *Start Earning* · Footer → *Join Discord* + *Follow on X*

## 13. SEO keyword inventory

**Site meta keywords (live):** Vanna, Vanna Finance, composable credit, undercollateralized credit, unified portfolio margin, cross-margin DeFi, delta-neutral strategies, DeFi leverage, perpetuals, options, prediction markets, tokenized stocks, AI-compute markets, agentic finance, MCP, onchain credit infrastructure

**Primary:** composable credit DeFi · undercollateralized lending DeFi · DeFi leverage · margin trading DeFi · cross-protocol leverage · unified portfolio margin

**Long-tail:** how to get 10× leverage in DeFi · undercollateralized borrowing crypto · delta neutral strategies DeFi · composable DeFi protocols · best DeFi margin trading platform · how to hedge DeFi positions · options trading DeFi with leverage

**Agentic cluster (highest-opportunity, low competition — prioritise this):** credit layer for AI agents · undercollateralized credit for agents · MCP DeFi server · agent credit score onchain · x402 credit API · agentic finance credit · agent margin account · policy-bounded agent trading · AI agent liquidation protection

**Stellar cluster (underserved):** Stellar DeFi leverage · Soroban margin account · Stellar undercollateralized lending · Blend leveraged yield · Soroswap margin trading · Aquarius LP leverage

**Competitor-adjacent (handle carefully — see positioning rules):** Gearbox alternative · Aave leverage trading · GMX with more leverage. **Do not** publish "better than Hyperliquid" style content; use "X vs Vanna" comparison pages instead of superiority claims.
