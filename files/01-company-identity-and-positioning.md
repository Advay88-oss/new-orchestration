# 01 — Company Identity & Positioning

## 1. Identity

| Field | Value |
|---|---|
| Product name | **Vanna** / **Vanna Protocol** |
| Legal/company name used publicly | Vanna Finance |
| Category (self-described) | Composable, undercollateralized credit infrastructure for DeFi |
| GitHub org description | "Composable DeFi Credit Infrastructure for Institutions, Businesses & Agents" |
| Primary domain | `vanna.finance` |
| Docs | `docs.vanna.finance` |
| App (testnet) | `test-stellar.vanna.finance` |
| Gated app entry | `app.vanna.finance/access` (access-code gated) |
| MCP endpoint (as marketed) | `mcp.vanna.finance` |
| GitHub | `github.com/vannafinance` (4 public repos, all website-related; protocol contracts are **not** public) |
| X / Twitter | `@vannaprotocol` (joined Sept 2022; ~76 posts; ~348 followers as of last check) |
| Discord | `discord.gg/vanna` |
| LinkedIn | `linkedin.com/company/vannaprotocol` and `/vannafinance` |
| Deployment status | **Stellar Testnet only. Pre-mainnet.** Mainnet addresses "will be published at launch." |
| Related entity | **Zonymous Labs** — appears as a repo in the Vanna GitHub org and in internal calendar context; treat as the affiliated build studio / company entity |

### Name meaning (useful for brand storytelling)
"Vanna" is a **second-order options Greek** — the sensitivity of an option's vega to a change in spot price. It signals derivatives-native, risk-engineering DNA. This is a genuine differentiator in a market full of animal-mascot protocols, and it should be used deliberately: *the protocol is named after a risk sensitivity, not a meme.*

---

## 2. Mission, vision, why

**Mission (internal, approved):**
> Democratize access to capital and bring TradFi-grade risk management to DeFi. Every trader deserves professional tools, not casino gambling.

**Vision:**
> Build the composable credit layer that powers the next generation of DeFi capital markets.

**Why Vanna exists (problem narrative):**
DeFi promised financial freedom and delivered fragmented liquidity, forced overcollateralization, and constant liquidation anxiety. Vanna's answer:
- Give traders the leverage they actually need — and let it move.
- Give LPs sustainable yield from real borrower interest, not token emissions.
- Let protocols and businesses unlock deeper liquidity without building a lending book.
- Bring institutional risk tooling to everyone, including autonomous agents.

**Current strategic framing (2026, sharpest version):**
> Vanna is building **the credit and risk layer for agentic finance.** Most agent infrastructure today is wallets, payments, prompts, and execution — all of which assume the agent already *has* capital and already knows how to manage risk. Vanna supplies the missing layer: undercollateralized credit, unified risk, liquidation protection, and portable credit history.

---

## 3. The core positioning wedge

This is the single most important argument in the entire knowledge base. It is the live homepage's opening move and it should anchor almost every piece of content.

**The forced choice Vanna dissolves:**

| Model | Exceeds your collateral? | Moves across markets? |
|---|---|---|
| Overcollateralized lending (Aave, Morpho) | ❌ No | ✅ Yes |
| Isolated leverage (perp / options venues) | ✅ Yes | ❌ No |
| **Vanna — composable credit** | ✅ **Yes** | ✅ **Yes** |

> *"DeFi makes you choose: credit that moves but never exceeds your collateral, or leverage that exceeds it but stays trapped in one venue. Vanna does both — up to 10×, across every market at once."*

**One credit line across spot, perps, options, prediction and AI-compute markets — move it, recall it, it never leaves the protocol.**

### The second wedge: isolated margin vs unified portfolio margin

The website's second section makes the capital-efficiency argument concrete. Memorise the shape of it — it is the best sales asset Vanna has.

**Isolated margin, $10,000 split across venues:**
- Spot exchange (own login, ~$3,300 in) → a gain here is **stranded**; it can't back the perp
- Perp venue (own login, ~$3,300 in) → its **own** health factor; margin-call risk you top up yourself
- Options desk (own login, ~$3,400 in) → funded separately; borrowed assets can't move between venues
- Stocks / compute markets → **out of capital**
- Result: 3 screens, 3 logins, no combined view of risk or PnL
- Failure list: every position walled off · borrowed assets can't be reused · no delta-neutral, no multi-leg · babysit each liquidation · gains stranded per venue

**Unified portfolio margin, one account, one screen:**
- $10,000 collateral → ×3 credit → **$30,000 working book**
- Spot: BTC long · Perps: BTC short · Options: ETH short vol · Prediction: rates print hedge · T-Stocks: NVDAx basis · AI Compute: GPU-hours yield
- Whole book: **Δ ≈ 0**, net positive
- **One health factor for the whole book**
- Wins: one account every market · collateral reused, headroom to 10× · Δ-neutral & multi-leg · one health factor · a loss offset by a gain · managed from one screen

**The mechanism sentence (learn this verbatim-adjacent):**
> A unified portfolio margin account is cross-margined: every collateral and every position, across every market, marked by one oracle into one solvency ratio — the structure that makes delta-neutral, multi-leg leverage possible.

---

## 4. Approved positioning lines vs lines to avoid

From internal strategy analysis (Feb 2026), positioning was explicitly tested:

**USE:**
- "Derivatives credit infrastructure"
- "The DeFi prime brokerage for traders"
- "Leverage anything, hedge everything"
- "Composable undercollateralized credit for DeFi — humans and agents"
- "Leverage Anywhere, Without Getting Liquidated" (used in the product video and the homepage brand card)
- "Credit that composes. Leverage that holds." (current hero)
- "Stop gambling. Start strategizing." (closing CTA line, still live)

**AVOID:**
- "Better than Gearbox" — do not pick a direct fight with a $300M+ TVL incumbent
- "The Composable Credit Layer" as a bare claim — too generic, indistinguishable from Gearbox
- Crypto hype register: moon, wen token, WAGMI, ape, degen
- Fear-of-missing-out framing
- Guaranteed returns of any kind

---

## 5. Traction, funding & ecosystem

### Funding (per internal content guide)
- **$350,000+ raised**
- Investors / backers named: **Pivot Ventures, Draper University, Gitcoin**
- Ecosystem support referenced: **Stellar Development Foundation, Optimism, Base**
- Draper University connection is real and notable — Draper runs a **Stellar × Draper University Founder Residency**, which is the likely path in.

> ⚠️ **Claim discipline:** $350K is a pre-seed-scale number. Internal analysis flags a **funding gap**: for the ambition (multi-integration + SDK + security budget), the assessed minimum is **$5M+**. Do not lead with funding as a credibility signal. Lead with architecture and design.

### Traction figures shown on the live site
- **15+** integrations
- **6+** chains
- **1,000+** users
- **40,000+** email subscribers (from campaigns, per internal guide)
- **2M+ users via integrated protocols** (internal guide — this is a *reach* figure, not Vanna users; see claim safety)

### Ecosystem logos displayed on the live homepage
Grouped as "Integrated with the venues that matter, backed by the investors building on-chain finance."

**Row 1:** Stellar · Hyperliquid · Uniswap · Optimism *(via Derive)* · Soroswap · ZeroDev · Katana · Avantis · Draper University
**Row 2:** Morpho · Privy · Blend · Aerodrome · Derive · Gitcoin · Aquarius · Aster · Pivot Ventures

**Footer chains:** *Built on Stellar · Base · Arbitrum · Optimism*

**Integrations actually wired in the shipped Soroban contracts (verifiable):**
- **Blend Capital** — external lending/yield destination (b-tokens)
- **Aquarius** — AMM liquidity + LP positions (XLM/USDC, XLM/AQUA, XLM/USDT pools)
- **Soroswap** — DEX spot swaps from margin accounts
- **Reflector** — price oracle
- **Privy** — wallet / embedded signing layer (frontend)
- **Freighter** — Stellar wallet used in SDK docs

Everything else on the logo wall should be treated as **ecosystem / roadmap / partner-adjacent**, not as live protocol integration.

### Legal line used on the site
> "Positions held at outside venues remain subject to those venues' own margin and liquidation rules."

Keep this or an equivalent in any content that implies cross-venue protection.

---

## 6. Company history (as far as it is publicly traceable)

| Period | Event |
|---|---|
| Sept 2022 | `@vannaprotocol` X account created |
| ~2023–2024 | ETHGlobal showcase entry: "DeFi derivative proprietary trading protocol", **live on Optimism**, integrated Perp Protocol + Uniswap, EIP-4337 account abstraction, internal liquidation bot |
| 2024 | First docs generation (`docs.vannafinance.xyz`, `docs.vanna.finance/docs1`): "Margin Account", "Prop Dashboard", two-sided protocol |
| Feb 2026 | Internal comparative + failure-analysis research produced; brand guidelines v1.0 dated Feb 2026 |
| 2025–2026 | Rebuild on **Stellar / Soroban**: 14 contracts, Reflector oracle, Blend/Aquarius/Soroswap integrations, testnet deployment |
| 2026 | Agent layer: MCP server (43 registered tools internally), CLI, TypeScript SDK, WorkOS-based OAuth, zero-custody Sign Service, Agent Score concept |
| Aug 2026 | Current marketing site live with agent-first narrative; still **pre-mainnet** |

**Narrative value:** Vanna has *already survived one pivot* (EVM derivatives protocol → Stellar-native composable credit + agent layer). That is a maturity signal if framed as focus, and a liability if framed as drift. **Frame it as focus.**

---

## 7. Known internal strategic tensions (agent should know, never publish)

These are real, documented disagreements inside Vanna's own research. The GTM agent must know them so it doesn't produce content that walks into them.

1. **Stellar choice.** The Feb 2026 internal analysis explicitly recommended *removing Stellar* ("non-EVM, low DeFi activity, splits engineering resources") and launching on one high-activity L2 (Arbitrum or Base). The company went **Stellar-first anyway**. The counter-case — which the current strategy implicitly bets on — is that Stellar became the strongest agentic-payments chain (x402 + MPP both live on mainnet, SDF is a Premier member of the x402 Foundation). **Public line: Stellar was chosen because it is where agentic payments actually settle.** Never publicly acknowledge the internal disagreement.
2. **Multi-chain too early.** Internal research flags the Prime Protocol death pattern: 8 chains → fragmented liquidity → death. The homepage footer says "Built on Stellar · Base · Arbitrum · Optimism." Content should emphasise **Stellar depth first**, chains as roadmap.
3. **Integration count over-promise.** Internal research warns against launching with 16 integrations (attack surface, audit cost) and recommends 5–7 deep ones. The site says "15+". Prefer **naming the real, deep ones** over quoting the count.
4. **No mainnet track record = trust deficit.** This is the single biggest objection and it is legitimate. See `05-audiences-personas-and-objections.md`.
5. **Token strategy undefined.** No token. Internal research sets prerequisites before any token (6–12 months clean mainnet, $50M+ organic TVL, $500K+/yr revenue, 3+ third-party SDK integrations). **Never hint at a token, airdrop, or points programme.**
