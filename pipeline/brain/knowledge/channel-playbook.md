# Channel playbook — how Vanna writes for X, LinkedIn and Reddit

Rules for every writer agent. Built from the founder's Notion (Language & Messaging, the
real margin launch kit, pitch transcript v9) and from mistakes in Vanna's own agent posts
(Oct 2026). The words come from the facts; this page decides how they are said.

## Every channel

1. **One idea per post.** One arc, one claim, one number. A second idea is a second post.
2. **Say what it means for the reader before how it works.** "Your hedge counts as a hedge"
   before "spot and short share one health factor".
3. **Plain words for traders; institutional words only for funds and investors.**
   - Say "your Vanna account", never "PDA". Say "one safety number (your health factor)"
     the first time a health factor appears.
   - Never "custody" about Vanna (Vanna never holds custody). Never "netting" on X or the
     website — say "offset".
   - Never a label nobody uses: "virtual contract", "collateral utility", "cross-offset",
     "real hedged cushion", "credit vs synthetics".
4. **A number carries its source in the same post** (Jia, Moallemi, Wang and Zeng 2026 for
   the $1.11B; OFR for the $7.95T). An example says "illustration".
5. **No absolutes that mislead.** Not "zero fees" — "a borrow rate, not a funding fee".
   Not "never liquidated" — "the guardian acts before the liquidation line, under your rules".
6. **The deployment is named and its figures stay on it.** Solana posts: the test app,
   Kamino / Jupiter / GMTrade, the 1.1 health-factor floor. Stellar posts: the testnet,
   Blend / Aquarius, XLM. Never "testnet" for the Solana app.
7. **Vocabulary ladder** (Language & Messaging): composable credit infrastructure (the
   company) → unified portfolio margin account (the product) → prime-broker-style (analogy).
8. **No hype register**: no exclamation marks, no "revolutionary", no "nobody can do this".

## X (Twitter)

- Hook in the first line, under ~12 words, a fact or a tension: "Most leverage in DeFi is
  synthetic."
- 280 characters a post, threads of 5–8, one poster per post (16:9), the poster says what
  the post says.
- Close with the campaign CTA ("Hungry for real margin?") and a question that invites a
  reply ("a hedge or a basis trade?").
- Tag a venue only when it has agreed. Reply to early replies.

## LinkedIn

- The institutional register: prime brokerage, net exposure, maintenance margin, first-loss
  reserve, underwriting — explained, not name-dropped.
- First person from a founder or the company, 120–220 words, short paragraphs, one
  concrete example, the source line under the number, one link at the end.
- Lead with the market gap ("Hedge funds borrow $7.95T against whole portfolios. On-chain,
  every venue sees only its own positions.") and end with what is live, honestly
  ("on a Solana test app today").
- No hashtags in the body; at most three at the end.

## Reddit

- Not marketing. Explain the mechanism and its limits as a builder would; disclose that you
  are on the team in the first lines.
- Lead with the question the subreddit has ("why is DeFi lending overcollateralized?") and
  answer it; Vanna is one paragraph, not the post.
- State the risks plainly (liquidation remains possible; test app; hedges still carry
  risk). No links in the first post unless the subreddit allows them; answer every comment.
- Respect each subreddit's rules (r/defi, r/solana, r/CryptoCurrency differ on promotion).

## Before / after (from Vanna's own posts)

| Before | After | Why |
|---|---|---|
| Advanced DEFI Prop Trading Protocol Powered By Composable Leverage & Chain Abstraction | Composable credit infrastructure for DeFi. | Old product generation; "chain abstraction" is vision, not today |
| Pay zero funding fees. | You pay a borrow rate, not a funding fee. | "Zero" reads as "free"; the founder's wording |
| Shared PDA custody | Both legs sit in one Vanna account. | Jargon, and "custody" is false |
| HF ≤ 1.1 · Whipsaw can liquidate short leg | Two exchanges can liquidate one side of your hedge. In one account, the legs offset. | Says what happens to the reader |
| 20% swing liquidates one leg | (illustration) a 20% move against the short can liquidate it on its own exchange | Unlabelled example |
| Idle holding: Zero liquidity | Your stock token sits idle. | Wrong: the token is liquid, it just earns nothing |
| 1.10x liquidation floor (Stellar) | One safety number covers every position. Above 1.1, the account is safe. | The figure explained, on its own deployment |
| Sub-second liquidation defense via Mercury (~320ms) | The guardian watches the account and acts before the liquidation line, under your rules. | Engineering detail is not the benefit; "defense" implied no liquidation |
| Fixed micro-gas 0.00014 XLM | (drop it, or) each transaction costs a fraction of a cent | Nobody chooses credit for gas |
