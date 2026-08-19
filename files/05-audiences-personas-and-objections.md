# 05 — Audiences, Personas & Objection Handling

---

## 1. The four-audience model (canonical — this is the live site's structure)

The homepage frames all four with a single elegant device: **"You plug in ___."**

| Audience | You plug in | The offer | Bullets shown |
|---|---|---|---|
| **Traders** | **collateral** | Deposit mixed assets, borrow up to 10×, run multi-leg strategies across every market from one account | Multi-collateral · Delta-neutral in one place · One health factor |
| **Businesses** | **a product** | Offer undercollateralized credit inside your own app. Vanna runs the risk engine; you keep the customer | API + SDK · No lending book to build · Your brand, front to back |
| **Institutions** | **liquidity** | Route firm liquidity into DeFi and trade on unified portfolio margin — cross-market leverage with account-level risk | Prime-broker experience · Capital efficiency · Segregated accounts |
| **Agents** | **autonomy** | Give agents their own credit account with hard limits and every Vanna action as a callable tool | MCP-native · Policy-bounded · On-chain track record |

**Plus the fifth, structurally essential audience the site under-serves:**

| Audience | The offer |
|---|---|
| **Liquidity Providers** | Supply XLM/USDC, receive vTokens, earn borrower interest. No positions to manage, no impermanent loss, no ponzinomics. Higher structural utilization than a standard money market because borrowers take 10× instead of overcollateralizing. |

> **GTM note:** LPs are the *supply side of the flywheel*. Without deposits there is no credit. The current site treats LPs almost as an afterthought (they appear only in docs). **This is a GTM gap the agent should flag and address with dedicated LP content.**

---

## 2. Personas

### P1 — "The Multi-Screen Trader" (primary near-term ICP)
- **Who:** Experienced DeFi trader, $10K–$500K book, already runs basis trades / funding harvests manually across Hyperliquid + a spot DEX + a lending market.
- **Day looks like:** three tabs, three health factors, manual rebalancing, a spreadsheet.
- **Pain:** gains stranded per venue; collateral can't be reused; babysitting separate liquidations; can't express a multi-leg position as one thing.
- **Trigger event:** a liquidation on one leg while another leg was profitable.
- **What lands:** the isolated-vs-unified comparison, one health factor, delta-neutral in one place.
- **What kills the deal:** no mainnet, no audit, low TVL.
- **Where they are:** Crypto Twitter, Farcaster, perp-DEX Discords, DeFi research substacks, Kaito/Cookie-style attention platforms.

### P2 — "The Yield Farmer Who Got Burned" (highest-volume ICP)
- **Who:** Runs leveraged yield / stablecoin carry; risk-averse about liquidation, not about complexity.
- **Pain:** leverage works until the 3am wick. Has been liquidated on a position that would have recovered by morning.
- **What lands:** Risk Guardian (the 03:14 SOL story), Lite Mode one-click leveraged yield, documented delta-neutral strategies with explicit risk ratings.
- **What kills the deal:** any hint of black-box autonomous trading. Emphasise **policy-based, human-approval thresholds.**
- **Where they are:** yield aggregator communities, Stellar/Blend ecosystem, DeFiLlama, r/defi, yield newsletters.

### P3 — "The Agent Builder" (highest-strategic ICP, lowest competition)
- **Who:** Developer building autonomous agents — trading bots, treasury agents, DeFi copilots. Works in Claude Code, Cursor, Codex. Already using x402/MPP, Privy or Turnkey, maybe AgentKit.
- **Pain:** their agent can pay for things but has no capital and no risk framework. They are hand-rolling position sizing and stop-losses.
- **What lands:** MCP-native from day one · typed policy-bounded tools · zero custody · scoped session keys · the working natural-language→auto-signed-multi-step demo.
- **What kills the deal:** vaporware. They will read the docs and check GitHub. **The empty public GitHub is a real problem for this persona.**
- **Where they are:** MCP directories and registries, Anthropic/OpenAI dev communities, agent framework Discords, X dev circles, Stellar developer meetings, hackathons, GitHub.

### P4 — "The DeFi Product Team" (B2B / Businesses)
- **Who:** Wallet, trading app, neobank or fintech that wants to offer leverage or credit without building a lending book and risk engine.
- **Pain:** building undercollateralized credit in-house means an oracle, a risk engine, a liquidation system, and audits. 12+ months and existential risk.
- **What lands:** "Vanna runs the risk engine; you keep the customer." API + SDK. White-label framing: your brand, front to back.
- **What kills the deal:** no audits, no SLA, no mainnet, no reference customer.
- **Where they are:** direct BD, ecosystem partnerships, conferences, warm intros through Stellar/Draper networks.

### P5 — "The Institutional Desk"
- **Who:** Crypto fund, prop desk, market maker wanting DeFi exposure with prime-broker ergonomics.
- **Pain:** DeFi has no portfolio margining. Every venue is a separate credit relationship and a separate margin call.
- **What lands:** unified portfolio margin, segregated accounts, cross-market leverage with account-level risk, Analytics/Risk Explorer stress simulations.
- **What kills the deal:** no audit, no compliance layer, no KYB option, no reporting tooling. Internal research names exactly these gaps.
- **Verdict:** **Not a near-term ICP.** Nurture only. Do not run institutional outbound until mainnet + audits.

### P6 — "The Passive LP"
- **Who:** Holds XLM or USDC, wants yield without managing anything. Often already in Blend.
- **Pain:** yields on plain money markets are thin because utilization is capped by overcollateralization.
- **What lands:** real yield from borrower interest, no IL, vToken exchange-rate growth, the flywheel argument.
- **What kills the deal:** bad-debt risk. **Be honest:** in extreme conditions bad debt dilutes the vToken exchange rate across LPs. Disclose it; it builds trust and it's already in the docs.

---

## 3. Objection handling

### 🔴 "You're not on mainnet. Why should I care?"
**This is the #1 objection and it is legitimate. Never dodge it.**

> You shouldn't put mainnet money in a testnet protocol, and we're not asking you to. What's on testnet is the full system — 14 contracts, the risk engine, the rate model, real integrations with Blend, Aquarius and Soroswap, and a working agent layer where a natural-language instruction becomes multiple auto-signed transactions that hold a health factor. What you can do today is read the maths, run the testnet, and tell us where the risk engine is wrong. When mainnet opens, you'll already know how it behaves.

**Never say:** "we're launching soon", "TVL is growing", or anything implying live capital.

### 🔴 "Where are the audits?"
> Security documentation is not published yet. That is the honest answer, and it's the reason we're not soliciting mainnet deposits. What we can point to today is the architecture: every user's margin account is a separately deployed contract with its own storage, so a bug in one account can't touch another; each lending pool is an isolated contract; every write routes through a stateless risk engine that gates on one invariant; all rounding floors against the protocol, not the user; and upgrades happen through a registry rather than by touching business logic.

**Internal note:** internal research lists ten launch blockers — multi-sig (3/5+), 24–48h timelock, 2+ independent audits, bug bounty with $500K+ max, formal verification of fund-handling functions, input validation on all external addresses, team identity verification, incident response plan, security monitoring partner, insurance fund. **Do not publish this list.** Do not claim any of them until confirmed.

### 🟠 "10× undercollateralized sounds like the thing that blew up DeltaPrime / Prime Protocol / PrimeX."
> Fair. Those failures are exactly what we studied. Three different deaths: Prime Protocol died of adoption after fragmenting across eight chains; PrimeX V1 died of product-market fit because its credit only worked for spot; DeltaPrime had genuine product-market fit and $42.9M TVL and was destroyed by two hacks in two months. The design answers: one chain deep before adding a second, credit that composes across every vertical rather than one, and a deliberately small contract surface — 14 contracts, not hundreds. And 10× isn't a dial we turned up; it's what falls out of a 1.1× solvency floor when borrowed capital never leaves the account.

### 🟠 "Why Stellar? DeFi liquidity is on EVM."
> Because agentic payments settle on Stellar. x402 and MPP are both live on Stellar mainnet, the Stellar Development Foundation is a Premier member of the x402 Foundation, and x402 on Stellar works through Soroban authorization entries — the same primitive our policy-bounded signing uses. If the thesis is that agents become economic actors that need credit, you want to be on the chain where agents already pay for things. Base, Arbitrum and Optimism are on the roadmap.

**Internal note:** internal research argued *against* Stellar. Never reveal that. The public rationale above is genuine and defensible.

### 🟠 "Isn't this just Gearbox?"
> Gearbox is the benchmark and it's a real protocol with real TVL. The difference is what the credit is *for*. Gearbox is universal leverage optimised largely for yield and spot. Vanna is built for **derivatives and hedging** — perps, options, prediction markets — where the whole point is that one leg loses while another wins and you need a single solvency ratio across both. That's why the risk engine values external positions as collateral rather than treating them as things you left the protocol to do. And Vanna is agent-native from the first commit rather than retrofitted.

**Rule:** never claim superiority to Gearbox. Claim **different job to be done**.

### 🟡 "You're letting an AI trade my money?"
> No. The copilot compiles your instruction into a position and hands it back for approval — nothing signs without you. The limits you set aren't suggestions to a model; they're on-chain guards enforced by the same risk engine that gates a human transaction. There's no path where a model bypasses the health-factor check. And Vanna never holds custody — scoped session keys, with a separate signing service as the only signer, under a spend cap.

### 🟡 "What if the oracle is wrong or lags?"
> Reflector updates on roughly a five-minute cadence, and we treat that lag as a design input, not an edge case. It's one of the two reasons the liquidation threshold is 1.1× rather than 1.0× — the other is slippage. That 10% surplus is what covers a stale price and market impact at the moment of liquidation. In extreme conditions where collateral collapses faster than liquidations clear, bad debt can arise, and it dilutes the vToken exchange rate proportionally across LPs. That's documented, not hidden.

### 🟡 "Only XLM and USDC? That's a tiny market."
> On testnet today, yes — XLM and USDC pools, with Blend, Aquarius and Soroswap as venues. That's deliberate: internal analysis says protocols die from too many integrations at launch, not too few. Deep and audited beats broad and unauditable. The architecture is asset-agnostic — the registry maps assets to pools, the tracking token generalises to any external position type — so adding a market is a configuration and an audit, not a rewrite.

### 🟡 "Is there a token / airdrop / points programme?"
> No token. No points. No airdrop.

**Hard rule: never hint otherwise, in any channel, ever.** Internal prerequisites before any token is even considered: 6–12 months of clean mainnet, $50M+ organic TVL without incentives, $500K+/yr revenue, and 3+ third-party protocols building on the SDK.

### 🟡 "Liquidation isn't permissionless — doesn't that break the model?"
> The current implementation requires the account owner's authorization on `liquidate()` because collateral is swept back to the owner rather than to an external liquidator. It's an emergency exit for the account, not a bounty for a bot. **Do not extend this answer further without engineering confirmation** — the docs contain a known inconsistency on this point.

### 🟡 "Your GitHub is empty."
> The protocol contracts aren't open-sourced yet; what's public is the website. That's a fair criticism for anyone evaluating us as infrastructure, and it's on the list to fix. In the meantime the full contract reference, math reference, event schemas and deployed testnet addresses are all published in the docs.

---

## 4. Discovery questions by persona

**Traders:** How many venues is your book split across right now? · Where does collateral sit idle? · When did a liquidation cost you money on a position that recovered? · Have you ever wanted to run one leg long and one short and had to fund them separately?

**Yield farmers:** What's your current leveraged-yield setup? · What health factor do you hold and who watches it overnight? · What's your rebalance cadence and what does it cost you in gas and attention?

**Agent builders:** What does your agent do when it needs capital it doesn't have? · How do you enforce position limits today — in the prompt or in code? · Where do the keys live? · What happens if the model returns something wrong?

**Businesses:** Have you scoped building a lending book in-house? · What would it take to offer leverage in your app in a quarter instead of a year? · Who owns the liquidation logic in that plan?

---

## 5. Channel priorities (recommendation, pre-mainnet)

**Tier 1 — invest now**
1. **Developer / agent-builder channels.** MCP registries and directories, GitHub, agent-framework communities, Stellar developer meetings, hackathons. Highest strategic value, lowest competition, and does not require mainnet to be credible.
2. **Technical content / education.** The architecture is genuinely interesting and mostly unexplained in the market. Ownable topics: self-collateralization maths, why kinked rate curves are worse than smooth polynomials, valuing external positions as collateral, why 1.1× and not 1.0×, what a credit layer for agents actually needs.
3. **X / Crypto Twitter.** Current footprint is near-zero (~348 followers, ~76 posts). This is a build-from-scratch problem, not an optimisation problem. Founder-led, thread-driven, mechanism-first.

**Tier 2 — build in parallel**
4. **Stellar ecosystem.** Underserved DeFi ecosystem, SDF distribution, Blend/Aquarius/Soroswap co-marketing, x402 Foundation adjacency. Vanna can be a *big fish in a small pond* here rather than invisible on Base.
5. **SEO.** Own the agentic-credit and Stellar-DeFi keyword clusters now, before anyone else does.
6. **LP-side content.** Fix the flywheel's supply side.

**Tier 3 — hold until mainnet + audits**
7. Institutional outbound
8. Paid acquisition
9. Aggressive competitor-comparison content

---

## 6. What the agent must never do in GTM

1. Imply mainnet, live TVL, or user funds at risk.
2. Claim audits, bug bounty, multi-sig, or insurance.
3. Hint at a token, airdrop, points, or rewards programme.
4. Present video/website demo numbers (26% ROI, 742 score, HF 2.4, +$302) as realised results.
5. Claim live perps, options, prediction-market or AI-compute integrations. Blend, Aquarius and Soroswap are what exists.
6. Claim superiority over a named competitor. Compare jobs-to-be-done instead.
7. Use "2M+ users" as a Vanna user count. It is aggregate reach of integrated protocols.
8. Publish the internal launch-blocker list, the funding-gap analysis, or the Stellar disagreement.
9. Give financial, investment or tax advice, or promise returns.
10. Use legacy vocabulary: Greeks Dashboard, Prop Dashboard, ERC-4337, 5x/7x tiered leverage, 1000× leverage.
