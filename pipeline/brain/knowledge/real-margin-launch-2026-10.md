# Real margin — the Solana launch narrative (Oct 2026)

Source: the founder's Notion, read 10 Oct 2026 (public pages, workspace "Vanna Group of Companies"):

- **Real margin launch kit — X thread, posters, Telegram, Galxe quest (10 Oct)** — `app.notion.com/p/3f5846d6f5598121893cdd22319cf27b`. Status on the page: *ready to post when the waitlist page is live*.
- Its parent, **Colosseum World Fair** — `app.notion.com/p/3ee846d6f5598141930cc1691344c55b`: the Colosseum hackathon submission, draft v4 (3 Oct), deadline **12 Oct 2026, 11:59 pm PT**.
- Sibling: **Pitch video (2 min) — transcript v9 (real margin, waitlist proof, 9 Oct)** — `app.notion.com/p/3f4846d6f5598117938cc9680c2edbef`.

Not read (owned by someone else; reading needs the founder's approval): the claude.ai artifacts
"Vanna Testnet Waitlist" (`claude.ai/artifact/8KQg76yMVxB5NPvyM8yXJ7`) and "Vanna Web App V4"
(`claude.ai/artifact/6aG3KrGNZGotE9perhbhmr`). Nothing below describes them.

Every number here is FOUND in those pages with the source they cite. Lines marked INFERRED are
this brain's reading, not the founder's words. Claims are decided in
`files/08-facts-ledger-and-claim-safety.md`, not here.

---

## 1. What is happening (the situation)

- Vanna is building on **Solana** since August 2026. It first built on Stellar (closed testnet
  alpha) and plans to launch there separately; Stellar had no derivatives venues to integrate.
- The Solana build is entered in **Colosseum's World Fair hackathon** (deadline 12 Oct, 11:59 pm PT).
  Vanna is already selected for the Colosseum accelerator.
- The judges' biggest open point was a **Solana-specific proof number**. The answer is a public
  **waitlist launch** (10–12 Oct) plus **founding testers** on the Solana test app, counted on
  Sunday night / Monday morning and cut into the 2-minute pitch video at 1:16.
- The waitlist launch carries a new narrative: **real margin vs synthetic margin**. It came from
  a Superteam DevRel session (the "holy shit moment" that must land before 0:40 in the pitch).

## 2. The narrative: real margin vs synthetic margin

**The insight.** Most leverage in DeFi is *synthetic*: a perp exchange lets you take a bigger
position, but nobody lends you real money. All the risk stays on your collateral, and the leverage
cannot leave that exchange. Traditional finance runs on *real margin*: a prime broker lends real
money against a fund's whole portfolio, and the fund can use it in any market.

**The argument, in order (the 8-post thread is this order):**

1. Most leverage in DeFi is synthetic — a bigger bet, nothing lent, one exchange.
2. Synthetic margin has a cost — front-end traders on Hyperliquid, mostly retail, lost **$1.11B**
   (27 Mar 2025 – 30 Jun 2026); market makers made **$208M** over the same period.
3. Real margin is how traditional finance works — hedge funds borrowed **$7.95T** as of
   30 Jun 2026; **54%** went to funds running hedged strategies.
4. Same $10, two paths (an illustration) — synthetic: $10 × 5 = a $50 perp; a 20% move against
   you wipes out the $10. Real margin: $10 + $40 borrowed USDC = $50 in a hedged position (spot
   plus a short); you pay a borrow rate and the legs largely offset.
5. On-chain credit has a **synthetic margin addiction** — lending protocols lock $150 to lend
   $100; perp leverage stays inside one exchange; with no real margin on offer, traders chase
   returns with bigger bets.
6. Vanna brings real margin on-chain, starting on Solana — borrow real money, more than you
   deposit; secured credit: the loan stays in your Vanna account, so the whole account backs it;
   usable on Kamino, Jupiter, Phoenix and prediction markets.
7. One health factor, so a hedge counts as a hedge instead of two separate bets; when traders
   borrow real dollars, **more real money enters DeFi** — lenders earn on real loans, every
   platform it reaches gets real volume.
8. *Hungry for real margin?* Join the waitlist for early access. Ask: a hedge or a basis trade?

**Words that carry it:** real margin · synthetic margin · real money / real dollars / real USDC ·
secured credit · more than you deposit · one health factor · a hedge counts as a hedge · more
real money enters DeFi · borrow rate, not a funding fee · leverage as a service · *Hungry for
real margin?* (the CTA) · close: "We want real credit to move like the rest of finance: freely,
and mostly hedged."

**Wording decisions already made (keep them):**

- Say "it's secured credit: the loan stays in your Vanna account, so the whole account backs it".
  Never "credit can't be withdrawn" (it sounds like a punishment).
- Say "you borrow real money, more than you deposit" — real, not synthetic.
- Keep "leverage as a service" (not "real margin as a service").
- Do **not** say "synthetic margin only enriches perp DEXs": perp venues (Phoenix, Drift) sit on
  the judging side and Vanna integrates Phoenix. Say what synthetic margin is, show the losses,
  then make the positive point that real money reaches every platform.
- Never count X followers as waitlist interest. Quote verified signups only.

## 3. The product as the founder describes it (Solana build)

- **Composable credit infrastructure**: one unified margin account where humans and AI agents
  borrow undercollateralized credit and deploy it across lending, spot, perps, delta-neutral vaults
  and prediction markets under one health factor.
- **Two modes, one protocol.** *Isolated margin* — tokenized stocks, in the Android app (the build
  submitted to Solana's **Stocklana** hackathon on 25 Sep 2026). *Cross margin* — the main product,
  on the web at `test.solana.vanna.finance`. Both run on a hosted Solana **mainnet fork** (a test
  app). Cross margin comes to the app next.
- **Pools**: lenders fund USDC, USDT and SOL pools. Borrowers post LSTs or tokenized stocks.
- **How it uses Solana**: each margin account is a PDA only Vanna's program can sign for;
  `margin_execute` CPIs into whitelisted programs (Kamino, Jupiter, GMTrade) and the account is
  health-checked after every call; separate oracle and validator programs price each holding from
  Scope and Pyth and approve each call; a GMTrade position is revalued on every check.
- **World vault**: holders of World prediction-market bets deposit outcome tokens; Vanna matches
  YES against NO, merges them into CASH via World's prediCt program and lends the matched part as
  USDC in its pool, so stakes earn until the market resolves. (Its README still says it is not
  deployed — roadmap until it is.)
- **Basis vaults** on BTC, ETH and SOL: contracts and tests done, not yet in the UI.
- **AI**: the Copilot turns a plain-language strategy into a risk-checked position; AI agents use
  Vanna as policy-bounded tools over **MCP** (today the MCP server serves only the Copilot).
- **Who it is for**: traders (app + Copilot), businesses and protocols (embed credit through APIs
  and SDKs — *leverage as a service*, no risk engine to build), institutions (a prime-broker-style
  account on-chain), AI agents.
- **Revenue**: borrow interest (leverage keeps utilization high), referral fees and rebates from
  venues it routes to, liquidation fees, and API/infrastructure revenue share.
- **Stack**: Rust + Anchor programs (core, oracle, validator, World vault, basis vaults), LiteSVM
  tests against mainnet program snapshots, Surfpool mainnet fork; Next.js web app; Expo React Native
  Android app (Mobile Wallet Adapter, Solana Mobile Seeker); Python MCP server on Cloud Run;
  Gemini on Vertex behind the Copilot. Integrations: Kamino Lend + Scope, Jupiter v6, GMTrade,
  World prediCt, Pyth, Token-2022.
- **Repos**: `vanna-credit-layer` (cross-margin core), `Protocol_V1_Solana` (isolated mode),
  `vanna_prediction_earn_vault`, the basis-vault repo, `vanna-solana-app`, `vanna_mcp_solana`.
- **Competitive framing (Colosseum answer)**: Aave, Morpho, Kamino lend real assets but only
  overcollateralized; Hyperliquid and Lighter proved one account and portfolio margin, but only
  inside their venue; Gearbox credit accounts only over tokenized positions; DeltaPrime stalled
  after exploits; Project 0 unified collateral across lending markets (perps on its roadmap);
  Kamino Multiply loops inside one market. "Credit as a feature of one venue instead of a layer
  above all of them." Vanna integrates them instead of competing. (Compare jobs, never claim
  superiority.)

## 4. Traction and team, as the founder states it

- Stellar closed testnet alpha: **130+ wallets opened 99 margin accounts** (deposit, borrow,
  trade, farm). Funded by **Stellar Community Fund** and **Draper University** grants.
- Solana: ~20 test-user sign-ups at Solana Summit Canada (Sept) — *the founder still has to
  confirm the number*. 131 commits across six repos in one week (week before 3 Oct).
- Reach: 20K+ followers across the founders' channels (*to confirm*), a trading YouTube channel
  (@CutDNoise) with ~4,000 subscribers, partner/KOL communities covering 500K+ traders (reach, not
  users).
- Team: Opinder (product and economic risk; ETHLend/Aave GTM and fundraising in India, 2017;
  blockchain advisor; DeFi/AI products at Koinfox, Nahar, Perflo) and Vatsal Salkiya (co-founder,
  smart contracts and security; Spectral, Polynomial; Immunefi All-Star, 27 findings, 6 critical;
  30+ audits with 5+ firms incl. Halborn and Cantina). Engineers: Rohit Yadav (Solana programs,
  web app), Anubhav Gupta (MCP server, Copilot), Sanujit Majhi (infra, Android), Aditya Kumar
  (product, mobile design). Full-time since late 2023: EVM (Optimism, Base, Arbitrum) → Stellar →
  Solana (Aug 2026).
- Internal, never publish: investment agreements, fundraising, legal entity and location answers
  (they live in the founder's Notion, not here).

## 5. The launch kit (channels and assets)

**Assets**: an 8-post X thread (each post ≤ 280 characters, one poster per post), a single-post
version (for quotes, Vatsal's account, replies under bigger accounts), a Telegram channel post +
poll + group message, a Galxe quest, and a plan to use alpha testers as proof. Copy source in the
product repo: `docs/applications/colosseum_build/real_margin_thread.py`; posters:
`media/real-margin-posters/png/` (not in this repo).

**How to post**: from the Vanna account, then quote it from the founder's own account with one
line of their own (20K+ audience); one poster per post; pin the thread; weekday morning US time or
right after the waitlist goes live; reply to every early reply (good replies become the pitch
video's screenshots); tag Kamino, Jupiter and Phoenix in post 6 **only if they have agreed**.

**Telegram**: channel post (pinned, poster 1 or 8) in the founder's first person ("Real margin is
coming to Solana, and I want you in first"), with the waitlist link and referral line, the
giveaway line, then an anonymous poll: *Would you use real margin instead of perp leverage?* —
Yes, for hedged trades / Yes, for bigger spot positions / Maybe, I'd want to see it live first /
No, perps are enough for me. Follow-ups: Sunday evening the waitlist count with a thank-you;
Monday the giveaway winners.

**Galxe quest** — *Hungry for real margin? Vanna early access*. Window Sat 10 Oct – Mon 12 Oct,
12:00 IST. Tasks: join the waitlist (visit link, confirm with the same email in Galxe ID), follow
Vanna on X, like + repost the thread, join Telegram; optional bonus: quote the thread with what
you'd run first. Reward: raffle, 10 × $100 USDC on Solana, drawn only from verified-waitlist
emails; everyone who completes gets early access. Anti-bot: human verification, one entry per
email and wallet, X accounts older than 3 months, winners checked by hand. Rules line: no purchase
needed; no token or airdrop is promised; void where prohibited; winners announced on X and paid
within 7 days.

**Waitlist page** (per transcript v9): email, optional wallet and X handle, a referral link that
moves people up the list; headline "Get early access to real margin on Solana"; a live count to
screen-record.

**Alpha testers as proof** (stronger than a waitlist): invite the Stellar alpha testers (130+
wallets), the Solana Summit Canada sign-ups and the most active Telegram members as *founding
testers* on the Solana test app with a one-page guide (connect, faucet, deposit, borrow, one
trade). Count what is real (wallets connected, accounts opened, first borrows), screenshot the
dated numbers Sunday night, collect 2–3 one-sentence quotes with permission. **It is a test app:
never present test balances or volumes as real money; label it "test app".**

## 6. The poster system (8 posters, 2048×1152, 16:9; the kit says 1600×900)

Seen directly in Notion on 10 Oct. One system across all eight:

- **Ground**: near-black (#0E0D10–#141216), a faint violet glow top-right and a faint warm
  red/magenta glow bottom-left. No texture, no 3D, no photography.
- **Logo**: Logo V2 (gradient mark + white "vanna" wordmark), small, top-left. On the CTA poster
  it is centred above the headline.
- **Headline**: one line or two, heavy geometric sans (Plus Jakarta Sans–like, ExtraBold), white,
  with **one emphasis word or phrase** in colour: coral-red for "synthetic", the violet→magenta
  gradient for "real margin", "synthetic margin addiction", "more real money enters DeFi",
  "Hungry for real margin?".
- **Sub-line**: one sentence in grey (#A0A0A8) under the headline.
- **Colour meaning** (consistent): coral/red (#FF5A5F-ish) = synthetic margin, loss, risk;
  teal/cyan (#3CD3E0-ish) = real margin; violet→magenta gradient = Vanna's emphasis.
- **Modules** (one per poster): a two-column comparison table in two bordered cards (red-tinted
  border = synthetic, teal-tinted = real; mono-caps eyebrow labels "SYNTHETIC MARGIN" / "REAL
  MARGIN"; label left in grey, value right in bold white); a giant stat ($1.11B in coral, $7.95T in
  the violet→magenta gradient) with its meaning under it; a stat plus a progress bar (54%);
  equation tiles ($10 × 5 = $50; $10 + $40 = $50) with a coloured verdict to the right; two
  dark panels side by side; an account card with dashed connector lines to four venue pills
  (Kamino lending, Jupiter spot, Phoenix perps, Prediction markets) and "All under one health
  factor"; two small panels with mono-caps labels (LENDERS / EVERY PLATFORM IT REACHES).
- **Footer**: `vanna.finance` bottom-left, a counter `n / 8` bottom-right, the source line in
  small grey text bottom-right above the counter whenever a number appears ("Jia, Moallemi, Wang
  and Zeng (Stanford, Columbia), 2026"; "OFR Hedge Fund Monitor (SEC Form PF) …, 30 Jun 2026";
  "Illustration only. Hedged positions still carry risk.").
- **CTA poster (8/8)**: centred logo, a two-line gradient headline "Hungry for real margin?", a
  white sub-line, a gradient pill button "Link in the post".
- **Density**: generous negative space, at most ~25 words a poster, one idea a poster; numbers
  are huge, labels small. INFERRED: this is the founder's current house style for data posts —
  flat and editorial, closer to the founder launch slides than to the glow/3D brand posters.

## 7. Pitch-video rules that also apply to content (transcript v9)

- One idea per screen, held 3 seconds or more; plain fades; no counting numbers, no popping chips;
  light product screens with plain-language labels; captions kept. (Reviewers said the earlier
  cut moved too fast — viewers had to pause.)
- The centrepiece picture is synthetic vs real margin with the same $10 (a coin-pile idea).
- Lead with one big number for the problem; traction stated plainly ("over a thousand people
  joined our waitlist in three days" only if true when cut; alternates: "over five hundred…",
  "our waitlist is filling up every day").
- Winning Colosseum pitches open with name + company + one-line what, "on Solana".
