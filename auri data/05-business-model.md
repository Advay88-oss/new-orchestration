# 05 — Business Model & Risks

> **Status: proposal and analysis, not policy.** Auri has **no fee logic implemented in the
> codebase today** — a search across `apps/api` and `packages` for fee/spread logic returns
> nothing. Monetization is an open decision. This file lays out the options honestly so the
> decision can be made deliberately rather than by default.

---

## The current state of monetization

**There is none.** Every action a user takes today costs Auri money (RPC calls, paymaster
gas sponsorship, infrastructure) and earns nothing. The landing page says *"the exact price,
rate and any fee appear on the confirm screen before every action"* — which is the right
promise to make, and currently that fee is zero because the mechanism doesn't exist.

**This is fine for now** — pre-revenue while proving activation is a legitimate stage — but
it needs a decision before launch, because retrofitting fees onto users who onboarded for
free is one of the most reliable ways to lose them.

---

## Revenue lines, ranked by fit

### 1. 🥇 Net interest margin on borrowing — *the natural business*

Auri sources liquidity from Morpho at the market rate and lends to users at a retail rate.
The spread is the revenue.

- User-facing rate today: **3.75% APR**
- Auri's cost: whatever the XAUT/USDT Morpho market charges, which floats
- **Revenue = (retail rate − market rate) × outstanding loan book**

**Why this is the best line:**
- It scales with the metric that matters (loan book), not with transaction count
- It is recurring, not one-shot
- It is invisible to the user — nobody feels a spread the way they feel a fee
- It is exactly how banks make money, so it needs no explanation to an investor
- At 3.75% Auri is still **2–4× cheaper than Indian gold loans (8–15%)** and far below
  US/Canadian personal credit (9–14%) or credit cards (20%+). **There is headroom to take
  margin and still be among the cheapest credit the customer has ever been offered.**

**But the headroom is market-dependent, and this is important:**

| Market | The rate to beat | Auri's headroom |
|---|---|---|
| 🇨🇦 Canada | Nothing comparable exists. Credit cards at 20%+ | 🟢 **Very wide** — Auri could charge 6% and still be transformative |
| 🇺🇸 US | **Coinbase lends from ~4%**; the broader market is 5–14% | 🟡 **Narrower** — 3.75% is competitive, not remarkable. Raising it puts Auri above Coinbase |
| 🇮🇳 India (future) | 8–15% | 🟢 Very wide |

**Read this carefully before setting a global rate.** A single worldwide 3.75% leaves money
on the table in Canada and offers no advantage in the US. Rate should probably be a
market-level parameter, not a constant.

**The risk:** the Morpho rate floats. If the market rate rises above 3.75%, the spread
inverts and every loan loses money. A floating retail rate, a rate floor, or a hedging
policy is required before this can be the primary line. **This needs a decision.**

### 2. 🥈 Buy/sell spread — *the industry standard*

Every competitor charges this and users expect it:

| Platform | Market | Fee |
|---|---|---|
| Kinesis | 🌍 | 0.22% |
| **OneGold** | 🇺🇸 | **0% over spot** (Switzerland Gold) to **1.50%**, + 0.12%/yr storage, + 0.30% resell |
| Glint | 🌍 | 0.5% buy/sell, + 0.02%/mo storage |
| Goldmoney | 🌍 | 0.5% each way (1.0% round trip) |
| **Wealthsimple Gold** | 🇨🇦 | **1.0% trading fee**, $0 storage |
| **Vaulted** | 🇺🇸 | **1.8% all-in** (spread + premium + commission) |

**The two anchors that matter, and they are different in each country:**

- 🇨🇦 **Wealthsimple's 1%** sets the Canadian expectation. Auri at **0.5% is half the price
  of the most trusted brand in the country** — a genuinely strong marketing position.
- 🇺🇸 **OneGold's 0%-over-spot** is a much harder anchor. **Auri cannot win the US on price
  per gram, and should not try.** But note that OneGold's all-in cost is not really 0% —
  add 0.12%/yr storage and a 0.30% resell fee and a two-year round trip costs ~0.54%. And
  Vaulted charges a flat 1.8%. **The honest US comparison is closer than the headline
  suggests, and Auri's $0 storage is a real advantage in a market where everyone charges it.**

Recommendation: **0.4–0.5% on buy and sell in both markets**, with **$0 storage** as the
headline. In Canada that's "half of Wealthsimple." In the US that's "cheaper than Vaulted,
and no storage fee ever, unlike OneGold." Displayed transparently on the confirm screen, per
the existing promise.

### 3. FX and remittance margin

The mid-market conversion promise on remittance is a strong user pitch, but partner rails
cost money. A modest, disclosed margin on cross-border payouts is standard and expected —
Wise built a large business on being the *transparent* one, not the free one.

**This line is worth far more in the US than in Canada.** The US is the largest source of
outbound remittances on earth (~$93B formal in 2024, up to ~$230B including informal
channels), with India (~$137B received) and Mexico (~$62.5B from the US) as the dominant
corridors. Global flows exceeded $857B in 2025 and are projected past $900B in 2026.

⚠️ **But check the 1% US remittance excise levy first.** Whether a gold transfer between two
self-custodied wallets falls inside or outside it is unresolved. If outside, it's a 1%
structural price advantage over Western Union and Remitly and a strong marketing hook. If
inside, Auri needs collection and reporting machinery it does not have. **Get this answered
before pricing the product.**

### 4. Card interchange

Once the card ships, interchange (~0.5–1.5% depending on scheme and region) accrues on every
transaction. This is why card programs are strategically valuable well beyond retention:
it's revenue that grows with daily-life usage rather than investment behaviour.

### 5. 💡 API / B2B — *the most under-priced opportunity*

Per-call, per-seat, or revenue-share pricing for fintechs embedding gold. Enterprise gross
margins, far lower CAC than consumer, and **no incumbent gold platform offers a developer
API at all.** This could plausibly become the larger business, and it's the one with the
clearest path to defensible pricing.

### 6. Boost / leverage fees

A fee on leveraged positions is easy to justify and easy to collect. It is also the
riskiest revenue in the stack — leverage products generate liquidations, liquidations
generate angry users and regulatory attention, and the segment using them is small.
**Monetize it, but never let it become a headline revenue line.**

### 7. Explicitly *not* recommended: storage fees

Glint charges 0.02%/month, BullionVault has punitive minimums, OneGold charges ~$20/yr.
**Auri should charge zero storage, loudly**, and use it as a competitive weapon — matching
Wealthsimple's $0 storage while beating everyone else. It also fits the self-custody story:
*we can't charge you to store it, because we're not storing it.*

### 8. The Kinesis question — should Auri pay yield?

Kinesis redistributes **57.5% of platform transaction fees** back to holders as monthly
yields paid in gold. Ether.fi keeps collateral earning while you spend. Auri's gold earns
nothing.

Auri *does* have a natural source: gold sitting as idle collateral could earn lending yield.
This is worth a serious product conversation, with eyes open about the trade-off — paying
yield means taking on rehypothecation-shaped risk, which directly contradicts the
"we literally can't touch your gold" promise that is Auri's strongest asset.

**Recommendation: do not pursue yield until the core loops work.** The custody story is
worth more than the yield.

---

## Suggested opening structure

| Line | Rate | Notes |
|---|---|---|
| Buy / sell | **0.4–0.5%** | Half of Wealthsimple. Shown on the confirm screen |
| Borrow spread | **1.5–2.5% over the Morpho market rate** | With a floor to protect against rate inversion |
| Storage | **$0** | Permanent. Marketing weapon |
| Auto-invest (SIP) | **$0** | Already promised. Drives the habit that grows AUC |
| Send / gift | **$0** | These are the acquisition loops. Never tax them |
| Remittance FX | **0.5–1%** | Disclosed, mid-market-referenced |
| Card | **Interchange** | No annual fee |
| API | **Usage-based** | Price after the first three design partners |

**The design principle:** free where growth happens (gifting, referral, SIP), priced where
value is delivered (buying, borrowing, spending, integrating).

---

## Unit economics — the shape of it

The single most important number is **assets under custody (AUC) per user**, because almost
every revenue line is a percentage of it.

Illustrative only — these are worked examples to show the shape, **not forecasts**:

```
A user with CA$5,000 in gold who borrows CA$2,000:

  Buy fee        CA$5,000 × 0.45%              = CA$22.50   (one-time)
  Borrow spread  CA$2,000 × 2.0%               = CA$40.00   /year (recurring)
  Card spend     CA$500/mo × 12 × ~0.8%        = CA$48.00   /year (once shipped)
                                                 ─────────
  Year-1 revenue                               ≈ CA$110
```

At a CA$40 blended CAC, that's a healthy ratio **if** borrow attach rate is high. **The
entire model rests on borrow attach.** A user who only buys gold and holds it generates
CA$22.50, once, and is barely worth acquiring. A user who borrows is worth 5×.

**Which means: borrow attach rate is the company's north-star business metric**, and every
product and marketing decision should be judged against whether it increases the share of
gold holders who open a credit line.

---

## Cost base

| Cost | Nature | Note |
|---|---|---|
| **Paymaster gas sponsorship** | Per transaction | The most dangerous variable cost — a free-to-use, gas-sponsored product is a subsidy that scales with usage. `PAYMASTER_DAILY_LIMIT_USDC` exists as a cap, and **`checkDailyLimit()` is currently never called — this is a known P0 blocker** |
| KYC verifications | Per user | ~$1–3 per check, both markets |
| Fiat rails | Per transaction | 🇺🇸 ACH/wire/card fees · 🇨🇦 Interac/EFT partner fees |
| Card program | Fixed + per card | BIN sponsorship, issuance, processing — **separate programmes per country** |
| Infrastructure | Fixed-ish | Cloud Run, Cloud SQL, RPC providers |
| **US state licensing** | 🔴 **Large fixed, if required** | **$100k+ in application fees alone** across 49 states + DC; surety bonds, minimum net worth, and permissible-investment requirements per state; **12–18 months and six-to-seven figures all-in** |
| Compliance / legal | Fixed, growing | The largest hidden cost in fintech — **and going bi-national roughly doubles it** |

**Watch the paymaster.** It is the cost that most easily runs away — a gasless product on
Ethereum mainnet with no enforced daily cap is an open tap. Fixing `checkDailyLimit()` is
both a security fix and a P&L fix.

---

## Regulatory position

> **This is the section that changed most when scope went from Canada to North America.**
> The US is not "Canada but bigger." It is a structurally harder regulatory environment, and
> whether Auri can enter it cheaply hinges on a single unresolved legal question.

**What Auri says, and what is true:**
- Auri is a **non-custodial software platform**, not a bank or a deposit-taking institution
- Balances are **not deposits** and are **not CDIC-insured** (🇨🇦) / **not FDIC-insured** (🇺🇸)
- KYC and fiat on/off-ramps are performed by **licensed third-party partners**
- Auri provides no banking, brokerage, investment, legal, or tax advice

**Why the architecture is the compliance strategy:** because Auri never takes custody, it
avoids the heaviest category of financial licensing. The regulated steps — identity
verification, fiat movement — are deliberately pushed to regulated partners. This is a
sound and deliberate structure, and it is the reason "Auri holds $0" appears in the legal
disclaimers as well as the marketing.

---

### 🇺🇸 The United States — the $1M question

**The bad news.** As of 2026, crypto businesses that transmit, exchange, or store digital
assets **on behalf of customers** need money-transmitter licences in nearly every state.
**49 states require an MTL** — Montana is the only exception. All money transmitters must
also register as an MSB with FinCEN federally. Building a national footprint is a
**12–18 month, six-to-seven-figure programme**, with application fees alone exceeding
**$100,000** across 49 states plus DC, before surety bonds, minimum net worth, and
permissible-investment requirements.

**The good news, and it is potentially decisive.** FinCEN's threshold test is whether a
party **accepts and transmits value on behalf of others — i.e. exerts custody or control.**
Its 2019 CVC guidance holds that **unhosted wallet software is not money transmission**, and
— this is the striking part —

> *"if a multiple-signature wallet provider limits its role to creating un-hosted wallets
> that require the addition of a second authorization key to the wallet owner's private key
> in order to validate and complete transactions, the wallet provider is **not a money
> transmitter**, because it does not accept and transmit value."*

**That description is close to a literal specification of Auri's architecture.** The owner
key authorizes; Auri's session key is a second, scoped authorization key that cannot move
funds to an external address, cannot exceed its caps, and cannot reach another account.
Auri never accepts or transmits value on a user's behalf.

⚠️ **Do not treat this as a legal conclusion.** It is a strong, well-grounded hypothesis
that must be confirmed by US counsel, in writing, before any US launch. Three caveats:
- The guidance is from 2019; enforcement posture has evolved.
- **State regulators are not bound by FinCEN's federal analysis** and several take broader
  views of money transmission. New York's regime is the strictest — note that Nexo's 2026 US
  relaunch **excludes New York**.
- The moment Auri adds a **fiat ramp** or **remittance payouts**, it may be handling customer
  funds through those flows, which is a different analysis from the wallet architecture. The
  partner may absorb this, or may not.

**The GENIUS Act** (signed 18 July 2025) is the first federal framework for payment
stablecoins and **preempts state MTL for permitted stablecoin issuers**. Auri is not an
issuer, so this doesn't apply directly — but it signals the direction of federal preemption
and is worth tracking. Separately, **31 states have adopted the Money Transmission
Modernization Act** in whole or part as of February 2026, covering 99% of reported money
transmission activity — meaning a multi-state programme is more standardized than it used to
be.

**Bottom line:** if counsel confirms the non-custodial exemption, the US is cheap to enter
and Auri's architecture becomes a *regulatory* moat, not just a marketing one. If not, US
entry is a funded, multi-year, state-by-state programme. **The delta between those two
outcomes is roughly a million dollars and a year — which makes this the single highest-value
question in the company, and it can be answered with one legal engagement.**

---

### 🇨🇦 Canada — lighter, but not free

1. Does offering a credit line against tokenized gold constitute lending under **provincial**
   law? Ledn's constraints are instructive — **not available in Quebec, New Brunswick, Nova
   Scotia, or Saskatchewan** — and Canada currently lacks laws supporting collateral
   registration, perfection, and priority for crypto assets.
2. Is XAUT a security in Canada? Almost certainly not — it's a commodity claim — but this
   needs an opinion on file, not an assumption.
3. Does Boost (5× leverage) trigger derivatives or margin regulation?
4. MSB registration with **FINTRAC** for the remittance product — almost certainly required.
5. Tax reporting obligations on gold disposals for users.

**Note the asymmetry, and it now points both ways:**
- Ledn's XAUT-backed loan product launches **excluding Canada and the EU** — so in Canada,
  Auri is doing something a well-capitalized incumbent is avoiding. That may be an edge, or
  a warning.
- But the same product is **not excluded from the US**, where Auri would face it head-on,
  alongside Coinbase, Nexo, and Milo.

**Get both legal opinions before the marketing spend.**

---

## Risk register

| # | Risk | Severity | Mitigation |
|---|---|---|---|
| 1 | **Fiat rails and KYC not built** — the funnel has no top | 🔴 Critical | The #1 engineering priority. Nothing else matters until this ships |
| 2 | **Tether / XAUT concentration** — the product's entire foundation | 🔴 Critical | Monitor attestations. Evaluate PAXG as a second collateral asset |
| 3 | **Morpho market risk** — smart contract or oracle failure | 🔴 Critical | 25+ audits help; the PAXG oracle incident of Oct 2024 shows it's not theoretical |
| 4 | **Liquidation event PR** — a user loses gold and posts about it | 🟠 High | Conservative default LTV, aggressive warnings, live health indicators, proactive notifications well before liquidation |
| 5 | **Rate inversion** — Morpho cost exceeds the 3.75% retail rate | 🟠 High | Floating retail rate or a floor. **Needs a decision** |
| 6 | **🇺🇸 US state licensing deemed required** — 49-state MTL, 12–18 months, $1M+ | 🔴 Critical | **Get the FinCEN non-custodial opinion in writing first.** It is the cheapest way to de-risk the largest market |
| 6b | **Regulatory action** on tokenized-asset lending in Canada | 🟠 High | Legal opinion on file before launch; watch CSA/OSC |
| 7 | **Competitor moves** — Coinbase adds XAUT collateral (they already lend on Morpho); Tether/Ledn launch XAUT loans in the US; Wealthsimple adds credit in Canada | 🔴 Critical | Speed and brand. **Note the US threats are more likely and faster than the Canadian ones** |
| 7b | **US remittance excise levy** applies to gold transfers | 🟡 Medium | Get guidance before pricing or marketing remittance in the US |
| 8 | **Paymaster cost runaway** | 🟠 High | Fix `checkDailyLimit()`; per-user gas caps |
| 9 | **Partner dependency** — Privy, ZeroDev, Enso, KYC, ramp, card issuer | 🟡 Medium | Document failure modes; know the switching cost of each |
| 10 | **Thin XAUT liquidity** on large orders | 🟡 Medium | Slippage guards already enforced; cap single-order size |
| 11 | **Trust deficit vs. incumbents** | 🟡 Medium | Proof-of-reserve UX, attestation links, transparent security writing |
| 12 | **Known Sprint 0 P0 blockers** — Docker runs `NODE_ENV=development` in prod; CORS defaults open (`allowedOrigin = true`); missing `apps/web/Dockerfile` | 🔴 Critical | Tracked in the sprint plan. **Must be closed before any real-money launch** |

---

## The questions to resolve before launch

**In priority order. Question 1 is worth more than the rest combined.**

1. 🔴 **Does Auri's non-custodial, second-authorization-key architecture exempt it from US
   state money-transmitter licensing?** FinCEN's 2019 multi-signature carve-out reads almost
   like a description of Auri's session-key model — but state regulators aren't bound by it,
   and adding a fiat ramp changes the analysis. **The answer is the difference between
   entering the US for legal fees and entering it for ~$1M and 12–18 months.** One legal
   engagement resolves it. Do this before anything else.
2. 🔴 **What is the legal opinion on lending against tokenized gold, per province and per
   state?** Ledn's provincial exclusions (QC, NB, NS, SK) and Nexo's New York exclusion both
   show this is not uniform, and it determines the real addressable market in each country.
3. 🟠 **Is the borrow rate fixed, floating, or per-market?** 3.75% is currently a marketing
   promise with no hedge behind it. If the Morpho rate moves, that promise becomes a loss —
   and a single global rate leaves margin on the table in Canada while offering no advantage
   against Coinbase's ~4% in the US.
4. 🟠 **What is the fee structure, and when is it turned on?** Retrofitting fees onto free
   users is expensive. Decide now; consider launching with fees visible from day one. Note
   the US and Canadian price anchors are different (OneGold at 0% over spot vs. Wealthsimple
   at 1%).
5. 🟡 **Does the 1% US remittance excise levy apply to gold transfers between self-custodied
   wallets?** Affects both pricing and required reporting machinery.
6. 🟡 **Which market ships first, and is the rails layer built for two from day one?** The
   recommendation in [04](04-customers-and-gtm.md) is Canada first for speed and lighter
   licensing — but with a rails abstraction that makes the US a configuration, not a rewrite.

---

## Sources

🇺🇸 US licensing & stablecoin regulation — [Astraea Counsel: state-by-state crypto licensing map](https://astraea.law/insights/state-by-state-crypto-licensing-map-2025) · [InnReg: money transmitter licence steps & requirements 2026](https://www.innreg.com/blog/money-transmitter-license-steps-and-requirements) · [Global Law Experts: obtaining an MSB licence in the US 2026](https://globallawexperts.com/obtaining-an-msb-licence-in-the-us-2026-a-complete-guide-for-crypto-payment-businesses/) · [eco.com: stablecoin regulation, US federal and state rules 2026](https://eco.com/support/en/articles/14814631-stablecoin-regulation-us-federal-and-state-rules-2026) · [v-comply: money transmitter compliance guide 2026](https://www.v-comply.com/blog/money-transmitter-compliance-guide/)

🇺🇸 FinCEN non-custodial guidance — [FinCEN Guidance FIN-2019-G001 (PDF)](https://www.fincen.gov/system/files/2019-05/FinCEN%20CVC%20Guidance%20FINAL.pdf) · [Jones Day: FinCEN consolidates guidance on virtual currencies](https://www.jonesday.com/en/insights/2019/06/fincen-consolidates-guidance) · [Covington analysis (PDF)](https://www.cov.com/-/media/files/corporate/publications/2019/11/fincen-issues-guidance-to-synthesize-regulatory-framework-for-virtual-currency.pdf) · [U. Chicago Business Law Review: regulating non-custodial service providers under the BSA](https://businesslawreview.uchicago.edu/print-archive/regulating-cryptocurrency-non-custodial-service-providers-through-bank-secrecy-act)

🇺🇸 Remittance levy — [Niskanen Center: the 1% US remittance levy](https://www.niskanencenter.org/the-1-u-s-remittance-levy-impacts-on-mexico-india/)

Competitor pricing — see the sources section of [03 — Competitors](03-competitors.md).
