# 03 — Agentic Layer & AI Thesis

> This is the **current spearhead of Vanna's narrative** and the sharpest differentiation the company has. Roughly half the live homepage is dedicated to it.

---

## 1. The thesis in one paragraph

AI agents can already pay for APIs, control wallets, and call DeFi tools. What they **cannot** do yet is access disciplined credit and manage margin safely. Every agent infrastructure layer that exists today — wallets, payment rails, prompt frameworks, execution engines — **assumes the agent already has capital and already knows how to manage risk.** Vanna fills the missing layer: undercollateralized credit, unified risk, liquidation protection, and eventually portable credit history. **Vanna should not compete as another chatbot. Vanna should be the agent-native credit and risk layer.**

**The strategic framing, verbatim from the internal Delphi deck:**
> "Smart contracts can be forked, but high-quality credit history cannot be forked. This is one of Vanna's strongest possible data moats."

---

## 2. Why now — the market tailwind (verifiable, external)

This is the evidence base for the agentic bet. All of it is externally citable.

| Fact | Source | Why it matters to Vanna |
|---|---|---|
| **x402 and MPP are both live on Stellar mainnet** — the two leading agentic payment protocols | Stellar developer meeting, Apr 2026 | Vanna's chain is where agentic payments actually settle |
| x402 is from Coinbase Developer Platform; on Stellar it works via **Soroban authorization entries** (signed auth entries, not pre-signed transactions) | Stellar docs | Same authorization primitive Vanna's Sign Service uses — architecturally native |
| **MPP** (co-developed by Stripe and Tempo) introduces **sessions**: an agent pre-authorizes a spending limit, streams micro-payments within the session, settles in bulk. Launched with **100+ integrated services** including Stripe, Anthropic, OpenAI, Shopify, Visa. Core spec submitted to **IETF** as the official HTTP payment standard | Stellar developer meeting, Apr 2026 | The "pre-authorized spending limit" model is *exactly* Vanna's policy-bounded credit model |
| **SDF is a Premier member of the x402 Foundation**, the Linux Foundation body stewarding the standard | stellar.org/x402 | Vanna's ecosystem has governance standing in the standard |
| **~100M agentic payments processed on Base** via x402; transactions of $1+ went from 49% of volume in early 2025 to **95% by early 2026**; tester-to-payer conversion improved **4×** in six months | Chainalysis, Jun 2026 | Agent payments are moving from micro-experiments to real economic weight — i.e. agents are starting to need *credit*, not just cents |
| **Galaxy Research estimates agentic commerce could represent $3–5 trillion in B2C revenue by 2030** | Galaxy, Jan 2026 | The TAM slide |
| x402 settlement rails now live on Base, Solana, **Stellar**, Arbitrum, Polygon, Ethereum mainnet | RZLT, 2026 | Multi-chain settlement is solved; credit is not |
| Cloudflare uses x402 for pay-per-crawl; Nous Research uses it for per-inference billing of Hermes 4 | Stellar blog, Mar 2026 | Non-crypto-native adoption — "software paying for software, without a human in the loop" |
| Coinbase + Google: x402 became the **first stablecoin facilitator on Google's Agentic Payments Protocol (A2A)** | RZLT, 2026 | Big-tech distribution for the rail Vanna plugs into |

**The gap this exposes — Vanna's whole argument:**
The agent stack has matured across **identity** (Skyfire), **communication** (A2A), **wallets/signing** (Privy, Turnkey, Crossmint, Coinbase AgentKit), **orchestration** (Eco), and **settlement** (x402/MPP on six chains). There is **no credit layer.** Every one of those layers presupposes a funded agent.

---

## 3. The three front doors — "same rails, any interface"

The homepage's section 03. One `open_position` call, three entry points, **one unified account and risk engine behind all of them.**

### MCP (for agents)
> "For agents — Vanna becomes typed, policy-bounded tools they can call."

```json
// agent.mcp.json — register the server once
"vanna": { "url": "mcp.vanna.finance" }
```
```js
// the agent calls a typed tool
vanna.open_position({ strategy: "dn-carry", floor: 1.40 })
```

### CLI (for developers & power users — "script it, cron it, automate it")
```bash
# one command, policy-bound
$ vanna open-position \
    --strategy dn-carry \
    --collateral 1000usdc \
    --floor 1.40

→ tx 4f2a…c91 · settled ✓ · fee $0.004
```

### SDK (TypeScript)
```ts
import { Vanna } from "@vanna/sdk";
const v = new Vanna({ session });
await v.openPosition({ strategy: "dn-carry", floor: 1.40 });
```

### Identical response from all three
```json
{
  status: "open",
  health_factor: 1.43,
  collateral: "1,000 USDC",
  borrowed:   "$2,000 of ETH",
  tx: "0x9f4c…a3e2"
}
```
> "Same account, risk engine & guardrails — **whichever way you call it.**"

### The published tool taxonomy

| Class | Tools |
|---|---|
| **READ** | `get_account_state` · `estimate_capacity` · `simulate_position` |
| **WRITE** | `open_position` · `repay_debt` · `rebalance` |
| **RISK** | `protect_position` · `get_risk_alerts` |

*(The internal Delphi document lists a slightly longer target set: `get_account_state`, `estimate_borrow_capacity`, `simulate_position`, `open_position`, `repay_debt`, `rebalance_collateral`, `protect_position`. The internal MCP server build reportedly has **43 registered tools** — do not publish that number without confirmation.)*

### The non-negotiable trust line
> **"Scoped session keys · Vanna never holds custody · the guardian runs beneath all three."**

**Zero-custody is the architectural commitment:** the MCP server holds no keys. A separate Sign Service is the only signer, bound by scoped session keys and spend caps. This must appear in *every* piece of agent-facing content. It is the answer to "you're letting an AI trade my money?"

---

## 4. The Copilot — intent becomes positions

Homepage section 01. **"Every word becomes a parameter."**

> "Say what you want in plain language — the copilot compiles it into a guarded position and hands it back for approval. **Nothing signs without you.**"

**Worked example (canonical demo — memorise this):**

Input:
> *"Deposit 1,000 USDC, run a delta-neutral ETH carry, keep health above 1.40."*

Compilation — plain language → on-chain intent:

| Phrase | Becomes | Detail |
|---|---|---|
| "1,000 USDC" | **Collateral** | posted once · backs the whole strategy |
| "Δ-neutral ETH carry" | **Position** | borrow $2,000 of ETH · deploy to lending · Δ ≈ 0 |
| "health above 1.40" | **Guardrail** | floor 1.40 · guardian armed · auto-deleverage |

Compiled on-chain (live): Collateral 1,000 USDC · Borrowed $2,000 of ETH · Position Δ-neutral carry · **Health factor 1.43 — above your 1.40 floor** · tx confirmed.

**Why this demo works so well:** it makes three abstract things concrete simultaneously — natural-language intent, undercollateralized credit, and enforced guardrails. It is the single best 15-second explanation of Vanna. Reuse it constantly.

**Guardrails the copilot preserves (per internal doc):** max leverage, minimum health factor, max loss, allowed assets, user approval thresholds.

---

## 5. Strategy playbooks — templates + free-form

Homepage section 02: **"Flip through proven playbooks. Or write your own."**

> "Every card is a ready strategy from one unified margin account. The agent runs whichever you pick; the risk engine keeps it alive."

Cards: **LP + Lending Spread · Delta-Hedged Vol Carry · Funding-Rate Harvest · Compute Yield, Hedged**
Plus: **"Write your own instruction — plain words in, a defended position out."**

Each card shows: badge (`PLAYBOOK`, category e.g. `Δ-NEUTRAL · PERPS` or `OPTIONS`), headline yield/label (e.g. `≈12% funding capture`, `θ carry / premium capture`), a 3-step recipe, and a footer: `AGENT runs it end-to-end under your policy` + `HF 2.4`.

**Marketing note:** the template/free-form duality is the right story — templates lower the barrier for retail, free-form intent is what excites builders. Address both in content, never only one.

---

## 6. Agent Score — "we underwrite behavior, not promises"

Homepage section 04. This is Vanna's claimed **long-term data moat**.

> "Every guarded action leaves an on-chain trail. Vanna reads it, scores it, and turns it into an undercollateralized credit line."

**Anatomy of the demo score card:**
- Subject: `0x7a2f…c4e9` — *autonomous · treasury agent*
- Score: **742 / 850** — **Tier 4 · Established**
- On-chain behaviour record:
  - Repayment record — **100% on time**
  - Liquidations avoided — **47 saves**
  - Health-factor discipline — **1.8 avg · never < 1.4**
  - Account age · volume — **214d · $1.2M**
- Credit line: *"The steadier the record, the deeper the line — climbing toward 10×"* (shown ranging from 1.0× to 7.0×)
- Third-party access: *"Any business can pull the score over **x402** before it extends trust"* — `GET /agent-score/0x7a2f…c4e9`

**The scoring inputs (per internal doc):** repayment history, liquidation avoidance, leverage discipline, account longevity, drawdown control, position duration, collateral diversity, realized PnL discipline, historical behaviour inside Vanna margin accounts.

**Design intent:** starts off-chain, later becomes verifiable through signed attestations or on-chain proofs. Other protocols could query it before allowing an agent to borrow, route large trades, access premium data, or participate in strategy markets.

> ⚠️ **Claim safety:** the 742 score and all sub-metrics are a **UI mock**. There is no live Agent Score product and no live x402 endpoint. Describe it as designed/coming, never as operating.

---

## 7. Risk Guardian — "never get liquidated in your sleep"

Homepage section 05. The most emotionally resonant part of the site because it names the actual fear.

**The scenario:**
> "One night SOL dropped 12% at 03:14. The guardian's log on the left, your health factor on the right — it never touched the red."

Guardian log — *watching 24/7*:
- **03:14** — SOL dropped 12%. Health **2.4 → 1.3**
- **03:14** — Guardian stepped in. Trimmed leverage, topped up collateral.
- **03:15** — Position secured. **Back to 2.1 — you stayed in.**

Summary metrics: Lowest HF **1.3** · Liquidation at **1.10** · Recovered to **2.1**
Caption: *"It caught the dip you slept through."*

**Design principle (from internal doc, important):**
> The first version should be **policy-based, not fully autonomous black-box trading.** Users define rules: minimum health factor, max daily deleverage, allowed protective actions, and whether human approval is required above certain thresholds.

**Defensive actions in scope:** alert the user · add collateral · repay debt · reduce leverage · hedge exposure · close a portion of the position.

**Why it matters commercially:** *"Liquidation fear is one of the biggest blockers for leveraged DeFi usage."* A risk guardian directly improves user confidence, retention, and borrow demand. This is the highest-conversion story Vanna owns — it converts a fear into a feature.

---

## 8. The full product roadmap (from the internal Delphi document)

Eight shortlisted ideas with an explicit priority ordering. **This is the roadmap the GTM agent should assume.**

### Near term
1. **Agent-Native Margin Copilot** — chat-to-trade. User expresses intent ("open a conservative 3× long XLM position and avoid liquidation"); agent handles collateral selection, borrow amount, venue routing, execution, monitoring, risk controls. *Why: Vanna owns the trader relationship at the UX layer while increasing borrow demand and volume.*
2. **Vanna MCP + CLI Credit Rails** — expose Vanna through MCP, CLI, SDK so traders in Claude Code, Cursor, custom bots, or institutional agent frameworks can operate without the frontend. Built as an **agent-access layer, not just developer docs**. *Why: fastest path to being programmable by external agents.*
3. **Liquidation Protection + Risk Guardian Agent** — see §7.
4. **Vanna x402 Financial Data API** — paid per-request agent-readable financial data. Proposed endpoints:
   - `/account-state/{address}` — collateral, debt, health factor, available credit, positions
   - `/simulate-position` — expected health factor, liquidation price, borrow cost, slippage before execution
   - `/agent-score/{address}` — Vanna Agent Score and key risk factors
   - `/yield-rates` — available yield opportunities across supported venues
   - `/risk-alerts/{address}` — liquidation and deleverage risk signals
   *Why: real revenue from the data layer; turns Vanna into infrastructure others pay to use.*

### Mid term
5. **Agent Credit Layer** — Vanna becomes the credit primitive for capital-constrained agents. If an agent has a strong behavioural record, it accesses undercollateralized credit and deploys it into approved strategies. *Why: platform-level, not a feature. If agents become economic actors, they will need credit.*
6. **Portable Agent Identity + Credit Score** — see §6.

### Long term
7. **Intent-Based Prime Brokerage** — agents submit financial goals; Vanna resolves them with credit, collateral, risk controls and execution routing. Example: *"Get $500K ETH exposure, keep health factor above 1.4, use the cheapest borrow route, and park idle collateral in yield."* *Why: intent systems route capital; Vanna can **create** capital through undercollateralized credit — the deeper primitive.*
8. **DePIN / GPU Financing Credit Agent** — finance GPU operators / DePIN compute providers using agent-assisted underwriting (hardware value, uptime, revenue history, compute market rates, repayment behaviour, collateral quality). **Explicitly flagged as NOT a near-term build** unless there is a clear oracle and legal/collateral path. *Why: extends credit rails into AI infrastructure debt — differentiated yield.*

**Note the connection to the homepage:** "AI-compute markets" and the "Compute Yield, Hedged" playbook are the marketing surface of idea #8. Be careful not to imply it ships soon.

---

## 9. The Delphi pitch (the approved investor/partner script)

> "AI agents can already pay for APIs, control wallets, and call DeFi tools. What they cannot do yet is access disciplined credit and manage margin safely. Vanna is building that layer. Our near-term products are an agent-native margin copilot, MCP/CLI credit rails, and a liquidation protection agent. The long-term moat is behavioural credit data: every agent and trader using Vanna builds a credit history that cannot be forked."

**Why this maps to Delphi's stated AI×crypto thesis:** trust infrastructure · agentic finance · real revenue · durable data moats. Vanna's claim: it already holds the hard primitive most agent systems lack — **credit**.

---

## 10. Supporting internal infrastructure (context for the GTM agent, mostly not public)

Useful for developer-audience content, technical blog posts and dev-rel outreach. Confirm before publishing specifics.

- **`vanna-mcp-server`** — zero-custody MCP server enabling AI agents to autonomously execute leveraged yield and margin strategies. Built on **FastMCP**. Reported **43 registered tools**.
- **Auth:** OAuth via **WorkOS AuthKit**, chosen over Auth0 and Stytch for a 1M MAU free tier and full MCP spec compliance. Dynamic Client Registration supported; `OAUTH_AUDIENCE` set to the resource URL.
- **Security posture:** Origin header validation for DNS-rebinding/CSRF protection per MCP spec. Phased identity enforcement (identity binding, session-takeover prevention, closed signup). Oracle-priced **USD spend cap** system.
- **Auto-sign / signing layer:** `EnableAutoSign` component on the website's `/agent` route using `useSigners` from `@privy-io/react-auth`. Sign Service enforces caps (e.g. a $1,000 clamp). **Privy's Stellar support is EOA / raw Ed25519 signing only — not smart-contract-wallet tier.** Do not claim smart-wallet-grade signing on Stellar.
- **Demonstrated end-to-end flow:** natural language → agent computes constraints → multiple auto-signed transactions → health factor maintained. This is a **real, working demo** and a strong proof point for developer audiences.
- **Indexer:** `mercury-stellar-backend` / Mercury for event indexing.

---

## 11. How to talk about agents without triggering alarm

Three recurring anxieties and the approved answers.

| Anxiety | Answer |
|---|---|
| "An AI will trade my money and blow it up." | Nothing signs without you. Policies are hard limits enforced by the on-chain risk engine, not by the model. The copilot **compiles** intent and hands it back for approval. |
| "Where are the keys?" | Vanna never holds custody. Scoped session keys. A separate Sign Service is the only signer, with spend caps. |
| "What if the model hallucinates?" | The model can only call **typed, policy-bounded tools**. Every write passes through the same RiskEngine guard as a human transaction. There is no path where a model bypasses the health-factor check. |

**Framing rule:** the agent is a *front door*, not a decision-maker with discretion. Guardrails are on-chain. Say this often.
