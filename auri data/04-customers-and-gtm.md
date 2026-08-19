# 04 — Customers & Go-To-Market

> **Status: proposal, not policy.** This file is analysis and recommendation. Nothing here
> has been ratified as company strategy. Use it to start the argument, not to end it.
> Market figures carry sources at the bottom.

---

## Who Auri is for

The mistake to avoid is defining the customer as "people who like gold." That's a
demographic, not a wedge. Auri's real customer is defined by a **grievance**:

> **Someone who has value — but the financial system won't give them credit, or charges
> them a fortune for it, or won't let them move their own money without permission.**

Gold is how they already store value. Auri is what finally makes that value *work*.

---

## Primary ICPs, ranked

### 1. 🥇 The gold-affinity diaspora across North America

**Why they're first:** cultural gold affinity is not something you have to create — it
already exists, at generational depth. Gold at weddings, gold as Diwali shagun, gold as the
family's real savings account. This is the same customer in Toronto, Jersey City, Fremont,
and Houston — which is precisely why a US + Canada launch works as *one* GTM rather than two.

**The two markets, sized:**

| | 🇨🇦 Canada | 🇺🇸 United States |
|---|---|---|
| Core community | **2.57M South Asians** (2021) — nearly quadrupled 1996–2021 | Far larger: South Asian, Latino, Chinese, Filipino, MENA communities, tens of millions combined |
| Remittance outflow | Meaningful | **The largest on earth** — ~$93B formal in 2024, up to ~$230B including informal channels |
| Top corridors | → India | → **India (~$137B received)**, → **Mexico (~$62.5B sent from the US)** |

**The Latino / Mexico corridor is the biggest single US opportunity and it is not in the
current product narrative at all.** $62.5B a year flows US → Mexico, and gold has deep
cultural weight in Mexican and Central American households. The gifting and remittance
mechanics Auri built for Diwali work identically for quinceañeras, weddings, and Día de las
Madres. **Someone should own researching this corridor.**

**Their jobs-to-be-done:**
- Buy gold regularly, in small amounts, without visiting a jeweller
- Send gold or money home to family
- Give gold as a gift for a wedding, birth, or festival — the *occasion* is the product
- Raise cash in an emergency without selling the family gold

**Why Auri wins here:** gifting with occasions built in, remittance at mid-market rates,
and — the killer — **borrow without selling**. In these cultures, selling family gold is a
last resort and carries real shame. *"Don't sell it, borrow against it"* is not a feature,
it's emotional relief.

**Where to find them:**
- 🇨🇦 Brampton, Surrey, Scarborough, Mississauga — grocery and jewellery districts, temples
  and gurdwaras, Punjabi/Hindi/Tamil/Urdu media
- 🇺🇸 Jersey City, Edison, Fremont, Sunnyvale, Houston, Chicago, Atlanta (South Asian);
  Los Angeles, Houston, Chicago, Phoenix (Latino); community radio, Spanish-language media,
  WhatsApp groups, festival events

### 2. 🥈 Immigrants with no local credit file

**Why they matter:** a newcomer can have $30,000 in gold and still be denied a $2,000 credit
card, because **neither the US nor Canada imports foreign credit history.** This is a
well-documented, deeply resented, universally shared pain on both sides of the border — and
it is *worse* in the US, where the credit score governs access to housing, insurance, and
employment, not just borrowing.

**Auri's answer:** *no credit check, no score, cash in minutes at 3.75%.* For this segment,
Auri isn't a better option. It's the **only** option that doesn't require years of local
credit history.

**Where to find them:** immigration consultants and settlement agencies, newcomer-focused
banking content, international student services, H-1B/PR/work-permit communities on Facebook,
Reddit, and WhatsApp, newcomer fintech partnerships.

### 3. 🥉 Inflation-anxious savers, 25–45

Distrust banks, watch purchasing power erode, own no gold because buying it is annoying and
holding it is useless. Auto-invest (SIP) is the product for them: CA$25 a week, automatic,
no fee, no market timing. India proves this behaviour converts at scale — **80M+ Indians**
already buy digital gold, and Jar built a business on rounding up spare change into it.

### 4. The self-employed, gig workers, and small business owners

Lumpy income, thin or damaged credit files, urgent working-capital needs. Traditional
lenders score them badly. They frequently hold gold. Same pitch as newcomers, different
channel: trade associations, accountants, small-business communities.

### 5. Crypto-adjacent users seeking real-world-asset exposure

Already comfortable with self-custody and DeFi mechanics. Want gold exposure with yield or
leverage. **Small segment, but the cheapest to acquire and the loudest.** They will find the
5× Boost and the API on their own. Useful for early liquidity and credibility; do **not**
let them define the product, because their preferences (complexity, leverage, tokens) are
the opposite of the mass market's.

### 6. 🏢 Developers and fintechs — the B2B2C wedge

**This is the most under-rated ICP in the deck.** Any fintech, neobank, remittance app, or
wallet that wants to offer gold buy/hold/borrow but doesn't want to build vaulting, ramps,
and a lending market. Auri's REST API + MCP + CLI make Auri the *infrastructure layer* for
gold, not just a consumer app.

**Why it's strategically strong:**
- Enterprise-shaped revenue (per-transaction, per-seat, or spread) with far lower CAC
- One integration can deliver more users than a year of consumer marketing
- No incumbent gold platform has a developer surface **at all** — this is genuinely open space
- The security property is a real selling point: *a leaked API key cannot exceed the caps,
  reach another account, or move funds to an external address*

**Where to find them:** developer conferences, MCP/agent ecosystem communities, fintech
infrastructure marketplaces, direct outbound to remittance and neobank product teams.

**And note: this ICP is borderless.** An API has no KYC problem, no fiat rail, and no
licensing footprint of its own — the integrator handles their own users. **The developer
business can go global on day one while the consumer product is still stuck behind US and
Canadian rails.** That asymmetry is under-appreciated and it may be the fastest path to
international revenue.

### 7. AI-agent power users

Small today, strategically interesting tomorrow. *"Give your agent a gold account"* is a
genuinely novel product statement, and the MCP ecosystem is where developer attention is
right now. Treat it as top-of-funnel brand differentiation and developer bait rather than a
revenue line.

---

## Personas (use these in design reviews and ad copy)

**🇨🇦 Priya, 29 — Software engineer, Brampton, PR since 2023**
Sends CA$800 home most months. Bought gold at Diwali because her mother told her to. Wants
to buy a condo in three years and has been rejected for a credit limit increase twice.
*Auri's hook:* "Your gold can be your credit line."

**🇨🇦 Ahmed, 41 — Owns two convenience stores, Scarborough**
Cash-flow gaps every few months. Has ~CA$40k in gold in a safety deposit box. Refuses to
sell it — it's the family's emergency fund. Currently uses a 22% credit card to bridge.
*Auri's hook:* "3.75% instead of 22%, and you keep the gold."

**🇺🇸 Raj, 32 — H-1B data scientist, Fremont CA, in the US four years**
Earns well, sends $1,500/month home, and still has a thin credit file because he arrived
without one. Bought a gold bar at Costco last year and it's sitting in a drawer. Follows
crypto but doesn't trade it.
*Auri's hook:* "Coinbase will lend against Bitcoin. We'll lend against the gold you already own."

**🇺🇸 Lucía, 38 — Runs a cleaning business, Phoenix AZ**
Sends money to family in Michoacán every two weeks and pays a fee every time. Buys gold
jewellery as savings because she doesn't trust banks and doesn't have a brokerage account.
No credit history to speak of.
*Auri's hook:* "Ahorra en oro. Envíalo a casa. Pide prestado sin venderlo."

**🇨🇦 Meera, 34 — Nurse, Surrey**
Watching prices rise, keeps meaning to "start investing," finds brokerages intimidating.
Wants something automatic she doesn't have to think about.
*Auri's hook:* "CA$25 every Friday, automatically. Pause anytime, no fee."

**🌍 Dev, 26 — Builds a remittance app, Toronto (users in six countries)**
Wants to offer his users gold savings but has no path to vaulting or lending.
*Auri's hook:* "One API. Your users get gold. You build nothing."

---

## Acquisition channels, ranked by expected efficiency

### Tier A — build these first

**1. Gifting as a viral loop 🔁 — the single best structural advantage**
A gift is sent as a link or QR, and **the recipient needs no Auri account to claim it.** So
every gift is: a new user, pre-loaded with a balance, arriving with a warm referral from
someone they trust, at an emotionally significant moment. This is Venmo's growth loop
applied to gold.

*Do this:* instrument gift-claim conversion as a top-3 company metric. Build occasion
templates per community. **The gold-buying calendar is fixed and knowable years in advance
— plan campaigns around it months ahead:**

| Moment | Community | Timing |
|---|---|---|
| **Diwali** | South Asian (US + Canada) | Oct–Nov |
| **Akshaya Tritiya** — the single biggest gold-buying day in the Indian calendar | South Asian | Apr–May |
| **Wedding season** | South Asian | Nov–Feb, Apr–Jun |
| **Eid al-Fitr / Eid al-Adha** | Muslim communities | Varies |
| **Lunar New Year** | Chinese, Vietnamese, Korean | Jan–Feb |
| **Quinceañeras, Día de las Madres, weddings** | Latino (primarily 🇺🇸) | Year-round, May peak |
| **Christmas, graduations, baby showers** | Everyone | Dec, May–Jun |

Note that this calendar alone is an argument for the US market: it has *every* one of these
communities at scale, so the gifting engine never goes quiet.

**2. Referral paid in real gold**
Already in the product ("refer & earn — you both earn gold"). Rewarding in gold rather than
cash is on-brand, reinforces the habit, and keeps value inside the system. Track the k-factor
weekly.

**3. Community-led growth in diaspora networks**
Not ads — presence. Sponsor community events, partner with jewellers (a jeweller can
introduce digital gold to customers who already trust them), work with immigration
consultants and settlement agencies, seed WhatsApp community groups. **Trust in these
communities travels by referral, not by impression.**

**4. Comparison and intent SEO**
High-intent, low-cost, compounding, and it works in both markets with different keyword sets.
Auri already has a docs site — extend it into a genuine content asset.

| 🇨🇦 Canada | 🇺🇸 United States |
|---|---|
| "borrow against gold Canada" | "borrow against gold USA" · "gold backed loan no credit check" |
| "Wealthsimple gold alternative" | "OneGold alternative" · "Vaulted vs OneGold" |
| "gold loan Canada no credit check" | "loan without credit history immigrant" · "no SSN credit loan" |
| "how to buy gold in Canada" | "how to buy gold online" · "is Costco gold a good investment" |
| "send gold to India" | "send money to India without fees" · "enviar dinero a México sin comisión" |
| "Interac gold purchase" | "spend gold debit card" · "gold IRA alternative" |

The **"I bought a Costco gold bar, now what?"** search intent is a genuinely under-served US
niche and maps perfectly onto Auri's pitch.

**Bilingual from the start in the US.** Spanish-language content and support for the Latino
corridor is not a phase-two nicety — it's the difference between reaching the $62.5B
US→Mexico flow and not.

### Tier B — after fiat rails ship

**5. Developer-led (B2B)** — MCP directories, agent-ecosystem content, "gold API" SEO, a
public sandbox, direct outbound to remittance and neobank product teams.

**6. Paid social, tightly targeted** — the borrow message to newcomers and self-employed
audiences, not the gold message to everyone. Expensive and only worth it once the funnel
converts.

**7. Creator partnerships** — personal-finance creators in Punjabi, Hindi, Tamil, Urdu, and
**Spanish**. Under-served, high trust, and dramatically cheaper than English-language finance
creators. The Spanish-language personal-finance creator market in the US is large and
notably under-monetized by fintechs.

### Tier C — don't bother yet

Generic brand advertising, crypto-Twitter spend, conference booths, PR without a launch
hook. These burn money before there's a funnel to fill.

---

## The funnel, and where it currently breaks

```
Awareness  →  Signup  →  KYC  →  Fund  →  First buy  →  Borrow / SIP  →  Refer / Gift
                          ⛔ NOT BUILT   ⛔ NOT BUILT      ✅ works      🟡 partial
```

**The uncomfortable truth: today the funnel has no top.** A user can sign up and log in, but
cannot deposit any currency, because fiat rails and KYC are not built. Every growth idea in
this file is blocked behind those two integrations.

**Therefore the #1 GTM priority is not marketing. It is shipping deposits and KYC.**
Nothing else moves the number until then — and going bi-national means doing it twice.

### The rails needed, per market

| | 🇺🇸 United States | 🇨🇦 Canada |
|---|---|---|
| **Deposit** | ACH, wire, debit card, RTP/FedNow | **Interac e-Transfer** (the default), EFT, debit |
| **Withdraw** | ACH, wire | Interac, EFT |
| **Bank linking** | **Plaid** (the standard) | **Flinks** (better Canadian bank coverage) or Plaid Canada |
| **Acquiring** | Stripe, Adyen, Nuvei | Moneris, Stripe CAD, Nuvei |
| **Ramp candidates** | Circle, Bridge, MoonPay, Stripe Crypto | Versapay, Nanopay, Flinks Pay |
| **KYC** | Persona, Onfido, Sumsub — **all cover both**; pick one vendor for both markets | same |
| **Licensing burden** | 🔴 **Heavy** — potentially 49-state MTL, 12–18 months, $1M+ | 🟡 **Lighter** — FINTRAC MSB registration, provincial variation |

*(Planned candidates come from `STATUS.md`; nothing has been selected yet.)*

**Two practical recommendations:**

1. **Pick one KYC vendor that covers both countries** (Persona, Sumsub, and Onfido all do).
   Two KYC vendors means two integrations, two webhook contracts, and two sets of edge cases
   for zero benefit.
2. **Ship Canada first, but build the rails abstraction for two markets from day one.** The
   licensing path is materially lighter in Canada, the team already has the domain knowledge,
   and it lets you prove activation before taking on US legal costs. Hard-coding Interac
   assumptions into the data model now will cost months later.

---

## Metrics that matter

| Stage | Metric | Why |
|---|---|---|
| Acquisition | Signup → KYC-complete rate | KYC is where fintech funnels die; expect 40–60% |
| Activation | **KYC → first buy within 24h** | The single best predictor of retention |
| Activation | Time-to-first-gold | Target: under 5 minutes end to end |
| Engagement | **Borrow attach rate** (% of gold holders who take a loan) | This is the revenue and differentiation metric |
| Engagement | SIP adoption rate | Recurring buys = predictable AUC growth + retention |
| Virality | **Gift-claim conversion** (claims → funded accounts) | The cheapest user Auri will ever get |
| Virality | Referral k-factor | >0.5 is good; >1.0 is a self-sustaining loop |
| Retention | 30/60/90-day balance retention | Are they leaving gold in, or cashing out? |
| Economics | AUC per user, and AUC growth rate | The base every revenue line multiplies against |
| Economics | CAC by channel, LTV:CAC | Kill channels below 3:1 |
| Risk | Loans near liquidation / liquidation events | One bad liquidation event on social media can undo a quarter of marketing |

**Segment every one of these by market from day one.** US and Canadian funnels will behave
differently — different KYC friction, different deposit rails, different competitive
alternatives — and a blended number will hide which market is actually working.

---

## Launch sequencing (recommendation)

Two tracks that run in parallel: a **consumer track** gated on fiat rails and licensing, and
a **developer track** that is gated on neither and can go global immediately.

### Consumer track

**Phase 0 — unblock (now).** Ship deposits, KYC, and withdrawals. Nothing else. Build the
rails layer so a second market is a configuration, not a rewrite.

**Phase 1 — 🇨🇦 Canada closed beta (~200–500 users).** Recruit by hand from one diaspora
community in one city. Goal is not growth — it's proving activation and getting the borrow
flow used by real people with real money. Fix the liquidation-anxiety UX here, where it's
cheap. **Run the US legal opinion in parallel with this phase**, so the answer is in hand
before the market is needed.

**Phase 2 — 🇨🇦 Canada community launch.** Referral + gifting loops on, timed to a festival.
One city, one community, done properly. Depth beats breadth.

**Phase 3 — 🇺🇸 US entry.** Sequenced by whatever the licensing opinion says. If Auri's
non-custodial architecture avoids state MTL requirements, this can move fast. If not, it
becomes a funded, staged, state-by-state programme — start with the largest diaspora states
(California, Texas, New Jersey, New York, Illinois) and accept that **New York is the
hardest and should be last**, as Nexo's US relaunch excluding NY demonstrates.

**Phase 4 — the card.** Converts Auri from a savings app into a daily-use account. Do not
launch before the loops work — it's expensive and it's the strongest retention lever, so
spend it when there are users to retain.

**Phase 5 — international.** UK, EU, UAE, Australia, then the high-gold-affinity markets
(India, SE Asia, LATAM, MENA). Each gated on partner coverage and local rules.

### Developer track — runs in parallel from Phase 1

Open the API beyond the access code, publish the sandbox, ship the MCP server and CLI
properly, sign three design partners. **This track has no fiat rail and no licensing
footprint of its own, so it is not blocked by any of the above and can serve integrators
worldwide immediately.** It targets a completely different buyer and may reach revenue first.

---

## Sources

🇨🇦 Canada — [StatCan: South Asian immigration to Canada](https://www150.statcan.gc.ca/n1/pub/11-627-m/11-627-m2024028-eng.htm) · [IMPRI: India–Canada South Asian diaspora](https://www.impriindia.com/insights/india-canada-south-asian-diaspora-as/)

🇺🇸 US & global remittances — [American Bazaar: US leads global remittance outflows, India tops recipients at $137B](https://americanbazaaronline.com/2026/05/27/us-leads-global-remittance-outflows-india-tops-recipient-with-137b-481665/) · [Niskanen Center: the 1% US remittance levy — impacts on Mexico & India](https://www.niskanencenter.org/the-1-u-s-remittance-levy-impacts-on-mexico-india/) · [Destatis: India largest recipient of remittances](https://www.destatis.de/EN/Themes/Countries-Regions/International-Statistics/Data-Topic/Economy-Finance/Remittances.html) · [MoneyTransferReviews: global remittance flows 2026](https://moneytransferreviews.com/data/remittance-flows) · [Fortune Business Insights: remittance market size](https://www.fortunebusinessinsights.com/remittance-market-115140) · [VIF: Indian diaspora and remittance flows](https://www.vifindia.org/article/2025/august/04/Indian-Diaspora-and-Remittance-Flows-Trends-Impacts-and-Perspectives)

🇮🇳 India — [Freo: digital gold investment apps India 2026](https://freo.money/guides/best-digital-gold-investment-apps/)
