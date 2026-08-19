# 01 — What Auri Is

---

## The one-liner

> **Auri is a gold neobank.** You buy real, allocated gold, and then you can actually *use*
> it — borrow against it, spend it, send it, gift it, and auto-invest into it — while it
> stays in your own custody. Auri never holds your money.

Internal shorthand: **"programmable gold."**

---

## The problem Auri exists to solve

Gold is the oldest store of value humans have and roughly **$25 trillion** of it sits in
vaults, lockers, and jewellery boxes doing **nothing**. It has three chronic failures as a
financial asset:

1. **It's illiquid in practice.** To get cash out of gold you have to sell it — and once
   you sell, you lose the upside and you often trigger a taxable event.
2. **It can't be spent.** A bar in a vault cannot buy groceries, cross a border, or clear
   on a Sunday.
3. **It can't be borrowed against, easily.** In neither the US nor Canada does a mainstream
   product let a retail saver post gold as collateral for cash. In India — where gold-backed
   credit is a mature, mass-market product — it runs **8–15% APR** through pawn-style branch
   networks.

Meanwhile the alternatives each fail a different way:

- **Banks** lend you *their* money, gate it behind a credit score, and take days.
- **Gold apps** (Wealthsimple Gold, BullionVault, Goldmoney) park your metal and stop there
  — no credit, no spending, no transfer.
- **Crypto** solves the rails but demands seed phrases, gas tokens, and volatility most
  savers do not want.

**Auri's thesis:** *gold never needed rescuing — it needed rails.* Put real gold on
programmable rails and hide every trace of crypto from the user.

---

## What a user can actually do

| Action | What it means to the user | Under the hood |
|---|---|---|
| **Buy gold** | Cash in, real grams out, ~30 seconds, from $10 | Local currency → USDC → swap to XAUT via Enso/1inch |
| **Sell gold** | Grams back to cash balance | XAUT → USDC swap |
| **Borrow** | Cash against gold, no credit check, **3.75% APR**, repay whenever | XAUT supplied as Morpho collateral, USDT/USDC borrowed |
| **Repay / Unlock** | Pay down any amount anytime, free the collateral | Morpho repay + withdraw collateral |
| **Spend** | Auri card — tap/chip/online, 24/7/365 even when gold markets are shut | Card issuer partner (roadmap) |
| **Send** | Gold to a contact, `@username`, or wallet, in minutes | On-chain transfer / claim link |
| **Gift** | Real gold for a birthday, wedding, Diwali shagun — via link or QR, recipient needs no account | Claim-link flow |
| **Remit** | Send abroad, recipient gets local currency (e.g. India → INR) at mid-market | Partner payout rails (roadmap) |
| **Auto-invest (SIP/DCA)** | CA$25 weekly, or on payday, or monthly — automatic, no fee, pause anytime | Scheduled worker executes buys |
| **Boost** | Up to **5× leverage** on gold in one tap — advanced, high risk | Looped borrow-and-buy |
| **Automate** | Drive the account from an AI agent (MCP), a shell (CLI), or your own product (REST API) | Scoped API keys over `/api/execute/*` |
| **Earn** | Auri Jewels (rewards) + refer-a-friend paying out in real gold | Rewards ledger |

---

## The four things that actually differentiate Auri

Everything else on the list above exists somewhere. **The combination does not.**

### 1. Self-custody — "Auri holds $0"

Your gold and cash sit in a wallet **you** control, secured by passkeys. Auri is a software
platform, not a custodian. If Auri disappeared tonight, your gold would still be yours in
the morning, provable on a public ledger.

This is the strongest trust claim in the category and no mainstream gold app can make it.
Wealthsimple, Glint, Goldmoney, and BullionVault are all custodial — you are trusting a
company's balance sheet and their vault partner. Auri's answer is: *don't trust us, we
literally can't touch it.*

### 2. Borrow without being scored

No credit check, no credit score, nothing sold, cash in minutes at **3.75% APR**. For a
recent immigrant to the US or Canada with no local credit file, this is not a nicer product
— it is the *only* product.

Compare what the same person is otherwise offered:

| Alternative | Rate |
|---|---|
| **Auri** | **3.75% APR** |
| US crypto-backed lenders (Nexo, Milo, Figure) | ~5–14%, most 8–13% |
| US / Canadian personal loans | 9–14% |
| Indian gold loans (the mature market) | 8–15% |
| Credit cards, both countries | 20%+ |

The one rate that beats Auri's is **Coinbase's BTC-backed USDC loan from ~4%** — which is
built on Morpho, the same protocol Auri uses. That is not a coincidence, and it is a useful
sanity check: Auri's rate is achievable because the underlying rail is the same one a
public company already lends on at scale.

The trade-off is honest and stated everywhere: **liquidation risk.** If gold falls far
enough against the loan, part of the collateral gets sold to repay it. LTV and liquidation
price are shown live on screen.

### 3. Provable gold, not a price feed

Every balance is **Tether Gold (XAUT)** — allocated, London Good Delivery bars vaulted in
Switzerland, attested quarterly by BDO Italia. A user can trace their holding to an
individual numbered bar.

Landing-page proof figures (verify before reuse — these are point-in-time):
- 707,747 oz of fine gold · 22+ tonnes · 1,792 numbered bars
- Attestation as of 31 March 2026, quarterly, BDO Italia
- Loans run on **Morpho** — $10B+ deposits, 25+ independent security reviews

### 4. Gold your code can talk to

Auri ships an **MCP server, a CLI, and a public REST API** on the same engine the app uses.
An AI agent, a cron job, or someone else's fintech can buy, borrow, send, and hold gold
through a scoped key. No incumbent gold platform has a developer surface at all.

This is also the seed of a **B2B2C business**: other fintechs embedding gold buy/hold/borrow
without building the vault, the ramp, or the lending market themselves.

---

## The user experience promise

Every crypto primitive is deliberately invisible:

- **No wallet, no seed phrase, no MetaMask.** Login is passwordless via Privy — email,
  phone, Google, Apple, or a passkey.
- **No gas.** Transactions are sponsored by a paymaster. The user never holds ETH and
  never sees a gas popup.
- **One signature, ever.** The user approves a scoped session key once. After that, actions
  are single taps.
- **Denominated in the user's own currency** (USD or CAD at launch), with g / oz / XAUT one
  tap away.
- **The confirm screen shows the exact price, rate, and fee before every action.**

---

## What is live today vs. what is a promise

This matters more than anything else in this document. Read
[06 — Status & roadmap](06-status-and-roadmap.md) in full, but the summary is:

| | State |
|---|---|
| **Buy / Sell / Borrow / Repay engine** | ✅ **Live and working** on testnet + mainnet contracts |
| Passwordless login, smart accounts, session keys, gasless UserOps | ✅ Live |
| Public REST API + developer portal + scoped API keys | ✅ Live (private beta, access-code gated) |
| Auto-invest (SIP), referral, notifications, activity | ✅ Built |
| Gift / send gold | ✅ Built (owner-signed transfer, server-verified receipt) |
| No-account claim links | 🟡 Not yet — recipient needs a wallet or username today |
| Fiat rails (US ACH/wire/debit · Canadian Interac/EFT) | ⛔ **Not built** — partner integrations pending in both markets |
| KYC | 🟡 Endpoints + gating exist, but **no real provider** — auto-approves outside production |
| The Auri card | ⛔ **Not built** — issuer not yet selected |
| Remittance corridors | ⛔ **Not built** |
| MCP server / CLI | ⛔ Described in docs, package names are placeholders |
| Boost (leverage) | 🟡 UI + local state only; the on-chain leverage leg is owned by another dev |

**Practical rule:** the landing site at auri.money describes the *destination*. The money
engine is real. The rails around it — fiat, KYC, card — are the current build.

---

## Where it runs

- **Web app (live, testnet):** [test.auri.money](https://test.auri.money)
- **Landing:** [auri.money](https://auri.money)
- **Developer portal:** standalone app for API-key management

### Market scope

**Auri is a global product with a North American launch.** The asset (XAUT), the vault
(Switzerland), the lending market (Morpho), and the rails (Ethereum) are all borderless from
day one — nothing in the architecture is country-specific. What *is* country-specific is
only the last mile: **fiat in/out, KYC, and licensing.**

| Phase | Markets | What gates it |
|---|---|---|
| **Launch** | 🇺🇸 **United States** + 🇨🇦 **Canada** | ACH/wire/debit and Interac/EFT partners; KYC provider with coverage in both; US state licensing analysis |
| **Near** | UK, EU, UAE, Australia | Partner coverage and local licensing |
| **Later** | India, SE Asia, LATAM, MENA — the highest gold-affinity markets on earth | Local regulation (India's digital-gold rules are actively in flux) |

**Why US + Canada together, and not Canada alone:** the US is roughly 10× the market, has
by far the largest remittance outflows in the world, and has a mature crypto-lending
industry that has already normalized "borrow against your assets" for consumers. Canada is
smaller but faster to enter and is where the team already has rails knowledge. Launching
both means one product, two rail integrations — not two products.

**The two markets are not symmetric.** See [05 — Business model](05-business-model.md) for
the regulatory difference, which is large: US state-by-state money-transmitter licensing is
a 12–18 month, six-to-seven-figure undertaking *if* Auri is deemed to need it. Whether it
does is the single most consequential open legal question in the company.

> ⚠️ **Known documentation inconsistency to fix:** the public docs and README say buys
> settle on **Arbitrum**. The code says otherwise — `packages/core/src/chains.ts` sets
> `SUPPORTED_CHAIN_IDS = [1]` (Ethereum mainnet), because XAUT liquidity and the gold Morpho
> market only exist there. Arbitrum addresses are *partially* verified in
> `packages/defi/src/addresses.ts`. **Ethereum mainnet is the live chain.** Do not repeat
> the Arbitrum claim to a partner until the docs are corrected.

> ⚠️ **Second inconsistency, now that scope is North America:** the public docs and landing
> site say **"Live in Canada · Interac"** and **"Canada (EN) · CAD"**, and the FAQ answers
> in Canadian terms ("fund by Interac, pay in Canadian dollars", "not CDIC-insured"). All of
> that needs a US equivalent — USD, ACH, and *"not FDIC-insured"* — before any US launch.

---

## The positioning statement

For **savers and newcomers who trust gold more than they trust banks**, Auri is a **gold
neobank** that turns gold from a dead asset into a working one — spendable, sendable, and
borrowable — without ever giving up custody.

Unlike **Wealthsimple Gold** and **OneGold** (custodial, buy-and-hold only), **Glint**
(custodial, spend only, no credit), and **Coinbase**, **Nexo**, and **Ledn** (credit, but
only against crypto), Auri is the only product where **real allocated gold is simultaneously
your savings, your collateral, and your spending account — and it never leaves your wallet.**

See [03 — Competitors](03-competitors.md) for the full defence of that claim.
