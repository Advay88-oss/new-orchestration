---
type: GTM Blueprint
title: Auri GTM Launch Blueprint — 2026
description: Complete, executable go-to-market blueprint for Auri, grounded in the internal docs and live competitor research.
tags: [gtm, launch, strategy, execution]
status: stable
verified:
  - by: human:advay
    at: 2026-08-12T00:00:00Z
sources:
  - id: internal
    resource: /auri data/
    title: Auri internal docs (product, competitors, GTM, business model, status)
  - id: competitors
    resource: /competitors/index.md
    title: 22 competitor dossiers + threat radar
---

# Auri GTM Launch Blueprint — 2026

**The one strategic decision this whole plan turns on.** Auri's money engine
(buy/sell/borrow/repay) is live and its developer API is live in private beta —
but **the fiat on-ramp is not built** (no ACH, no Interac). A user today can log
in and get a wallet, then hits a wall: there is no way to put money in. See
[/facts/tier-c.md](/facts/tier-c.md).

So a full public consumer launch is **not yet possible**, and any GTM plan that
assumes one is fiction. This blueprint is built around what is **actually live**:

- **Now (Phase 0):** launch the **developer/API product** (live, global, no fiat
  or KYC dependency) + build the **consumer waitlist, community and brand** ahead
  of rails — riding the tokenized-gold-goes-mainstream tailwind. Zero fiat needed.
- **At rails (Phase 1):** the **consumer launch** in the US and Canada, the day
  ACH/Interac + real KYC ship.

Leading with what is real, while seeding what is coming, is the honest and the
optimal sequence.

---

## 1. Business objective

| Horizon | Objective | Target (illustrative, set with the team) |
|---|---|---|
| Phase 0 (now → rails) | Developer signups + consumer waitlist + category authority | 25–50 API private-beta integrators; 5–10k consumer waitlist; own "tokenized gold you can use" |
| Phase 1 (rails live) | Funded consumer accounts | first-cohort activation (fund → buy → borrow) |
| North star | **Funded, active accounts** — not signups | activation rate (fund→first-action), not vanity signups |

Phase 0 is deliberately not measured in consumer revenue — it can't be, without
rails. It is measured in **pipeline**: integrators, waitlist, authority.

---

## 2. Market & audience

**Market:** tokenized gold surpassed **$5B** (PAXG + XAUT dominate); the category
is being legitimised top-down — the **UK FCA is drafting tokenized-gold
collateral rules**, central banks are accumulating gold (Bank of Korea, after 13
years). Tailwind is real and current. US is the largest outbound-remittance
market on earth (~$93B+); gold-affinity diaspora (India ~$137B received) spans
both launch markets.

**The gap Auri fills:** nobody combines *real allocated gold + self-custody +
credit + a developer API*. In Canada the missing leg is **credit** (Wealthsimple
owns buying, nobody lends against gold). In the US the missing leg is the
**asset** (credit is everywhere — Coinbase, Nexo — but only against crypto).

**Buying triggers:** inflation anxiety, distrust of banks, a cash need without
wanting to sell gold, remittance, diaspora gold affinity.
**Objections (rank order):** liquidation risk ("my gold could be sold"), "not a
bank / not FDIC-CDIC insured", no tax-sheltered accounts, brand-new trust.

---

## 3. Competitor intelligence (summary) + one launch teardown

Full set: **22 dossiers** in [/competitors/index.md](/competitors/index.md) +
[fresh threat radar](/competitors/threat-radar-2026-08-11.md). Headline:
*nobody competes with all of Auri; everybody competes with one slice.*

**Severe, time-boxed threats** (the launch clock):
- **Tether × Ledn XAUT loans** — Auri's exact product from the token issuer;
  **excludes Canada + EU at launch, not the US.** Not live yet.
- **Coinbase adds gold collateral** — they already lend on Morpho; a config change,
  not a rebuild. Not done yet. Auri's window is open **now**.

**Launch teardown — Wealthsimple Gold (the CA benchmark):** launched gold *inside
an app millions already trust*, $1 minimum, 1% fee, $0 storage, coin redemption,
TFSA/RRSP. Their playbook: **distribution-first** (existing user base), trust as
the product, dead-simple onboarding. **Lesson for Auri:** do not fight them on
trust or first-purchase ease — Auri has no distribution and no brand yet. Fight
on the leg they will never have at launch: **credit, spend, send, self-custody.**
"Wealthsimple lets you own gold. Auri lets you use it."

---

## 4. Customer research → 5. ICP

**Primary ICP — "the credit-invisible saver."** Recent immigrants and
self-employed people in the US/Canada with gold affinity and **no local credit
file**, who fail credit checks. For them a no-credit-check 3.75% line against
gold is not a nicer product — it is the *only* product. Where they are: diaspora
communities, r/PersonalFinanceCanada, r/immigration, WhatsApp/Telegram diaspora
groups, gold-focused YouTube.

**Secondary ICP — "the gold holder who wants it to work."** Existing physical /
ETF gold owners frustrated their gold "does nothing." Where: r/Gold,
r/preciousmetals, gold-investing YouTube, FinTwit.

**Phase-0 ICP — "the fintech developer."** Builders who want to embed gold
buy/hold/borrow without building a vault, ramp or lending market. The API is live
and global; **this is the one segment Auri can fully serve today.** Where: X dev
community, Hacker News, r/fintech, developer Discords, Product Hunt.

---

## 6. Positioning + 7. Messaging framework

**Core positioning:** *Auri is the only place your gold is your savings, your
collateral, and your spending account at once — and it never leaves your wallet.*

**Lead with the credit line, not the gold** (everyone sells gold; almost nobody
sells "cash against your gold, no credit check, 3.75%"). Sequence:
1. **Hook:** "Need cash? Don't sell your gold. Don't get scored." → 3.75%, no check
2. **Trust:** "Auri holds $0. Your gold, your keys, checkable to the bar."
3. **Delight:** send it, gift it, stack it automatically
4. **Depth (devs):** "Gold your code can talk to."

**Per-market first sentence:**
| | Canada | United States |
|---|---|---|
| Lead | "Wealthsimple lets you own gold. Auri lets you use it." | "Coinbase will lend against your Bitcoin. Nobody will lend against your gold — until now." |
| Enemy | Buy-and-hold ceiling | The gold ETF + the warehouse model |
| Trust anchor | Self-custody vs a custodial brokerage | Swiss vaults + bar-level attestation vs a paper ETF |
| Don't fight on | Brand, TFSA/RRSP | Rate (Coinbase ~4%), spot price, IRA |

**White space** (where competitors are silent): *"gold you can borrow against,
non-custodially, without a credit check."* No incumbent says this because none
can do it. Own this sentence.

**Proof points (Tier A only):** XAUT allocated, Swiss vault, **BDO quarterly
attestation**, 22+ tonnes / 1,792 bars, Morpho ($10B+ deposits, 25+ audits),
**Auri holds $0**. **Never claim** fiat/Interac, the card, MCP/CLI, KYC as live
([/rules/not-built.md](/rules/not-built.md)).

---

## 8. GTM strategy + 9. Channel strategy (prioritised — NOT every channel)

**Strategy:** authority-led + developer-led now; distribution partnerships +
diaspora community for the consumer launch. Auri cannot out-spend or out-trust
incumbents, so it wins on **category ("gold you can use"), the credit wedge, and
diaspora distribution** — before a $50B competitor decides gold collateral is
worth a sprint.

**Channel priority** (which channel + audience + message + objective = highest
opportunity):

| Priority | Channel | Audience | Why | Phase |
|---|---|---|---|---|
| 1 | **X / FinTwit** | devs + gold/crypto-curious | founder voice, the credit wedge, tokenized-gold tailwind | 0 |
| 2 | **Developer channels** (HN, Product Hunt, dev Discords) | fintech builders | the one segment live today; API is the wedge | 0 |
| 3 | **YouTube + short-form** | gold holders, diaspora | explain "use your gold"; high-trust format for a trust-hard product | 0→1 |
| 4 | **Reddit + communities** | credit-invisible savers, gold holders | native value-first, where objections are voiced | 0→1 |
| 5 | **Diaspora community / WhatsApp-Telegram + partnerships** | credit-invisible ICP | distribution Auri otherwise lacks; gift/remittance loops | 1 |
| — | **Paid ads** | — | **deferred** until funnel converts organically and rails are live | 1+ |

Deliberately *not* prioritised now: broad paid, LinkedIn brand ads, TikTok
trends — no evidence they fit the ICP yet, and paid before rails burns money on a
funnel with no bottom.

---

## 10–13. Launch timeline (T-30 → post-launch)

Two-track: the **developer launch runs now**; the **consumer launch is staged and
gated on rails**.

```
PHASE 0 — NOW  (developer live + consumer seeding)
 Week 1-2   Founder thought leadership on X: tokenized gold goes mainstream
            (FCA, central banks) → "the rails were the missing piece"
 Week 2-3   Developer product: docs, "Gold your code can talk to", HN + PH prep
 Week 3-4   Consumer waitlist live: "cash against your gold, no credit check"
            landing page; educational content (the credit wedge, self-custody)
 Ongoing    Community: Reddit value-first, diaspora seeding, gift-loop teasers

CONSUMER LAUNCH  (T-0 = the day ACH/Interac + KYC ship — GATED, not dated)
 T-30→T-14  Teasers, founder content, waitlist push, problem-awareness content
 T-14→T-0   Product reveal, launch video (see VIDEO spec), demo, influencer/diaspora
 T-0        Launch: announcement, X thread, PH launch, email blast, community
 T+1→T+30   Testimonials, UGC, gift/referral loops, retargeting, feature content
```

**Do not date the consumer T-0.** Gate it on the critical path: **fiat on-ramp +
real KYC**, per market. Marketing a launch users cannot fund destroys trust.

---

## 14–19. Content calendar + scripts (Phase 0, ready now)

Every asset tagged **Audience · Funnel stage · Objective · CTA**. Cards render
in Auri's palette + logo (built). Scripts below are gate-passed drafts.

**X — founder authority (awareness, dev+consumer):**
- *"London is racing to build what you can use today."* (FCA tokenized-gold
  collateral → Auri already does it) — already produced, gated.
- *"Everyone sells gold. Nobody lets you use it."* (competitive wedge) — produced.
- *"Auri isn't just a gold app — it's an API."* (developer wedge) — produced.
- **Thread (new, dev):** "We put gold on rails your code can call. buy / borrow /
  send allocated gold through one scoped key — no vault, no lending market to
  build. Here's how the session-key security model means a leaked key can't move
  funds out. 🧵"

**LinkedIn — thought leadership (B2B/dev, consideration):**
- "Tokenized gold just went from crypto curiosity to FCA policy. Here's what the
  infrastructure actually needs to be — allocated, attested, non-custodial — and
  why the developer API is the part that's ready today."

**YouTube / short-form (gold holders, awareness→consideration):**
- Explainer: "Your gold is doing one job. Here's how to make it do six." (buy →
  hold → borrow → send → gift → auto-invest), risk disclosed. → VIDEO spec.

**Reddit (r/Gold, r/PersonalFinanceCanada — value-first, no promo):**
- Genuinely useful answer on "how do gold-backed loans actually work / what
  should they cost" — Auri mentioned only as one option, with the honest 3.75% vs
  8-15% (India) vs 20%+ (cards) comparison. Native, not an ad.

**Email (waitlist nurture):** 3-touch — (1) the credit wedge, (2) self-custody
proof, (3) "you're early; here's what launches first."

**Landing page (waitlist):** hero = "Need cash? Don't sell your gold. Don't get
scored." → 3.75%, no credit check, non-custodial → waitlist capture. Per-market
variant (CA/US copy from §6).

---

## 20. Paid strategy

**Deferred to Phase 1.** No paid spend until (a) rails are live so there's a funded
conversion, and (b) organic funnel shows a converting message. When on: retarget
waitlist + lookalikes of the credit-invisible ICP; test the credit-wedge hook
first. Budget in §27.

---

## 21. Incentive strategy (with impact estimate + compliance)

Every incentive gated by [/company/constraint.md](/company/constraint.md) — a
gold+borrowing product must never imply guaranteed reward or return.

| Incentive | Acq. impact | Conv. impact | Cost | Abuse risk | Verdict |
|---|---|---|---|---|---|
| **Waitlist priority / early access** | High | — | ~0 | Low | **Ship now** (Phase 0) |
| **Gift gold (real grams, occasion)** | High (viral loop) | Med | grams gifted | Med (self-gifting) | **Test** — built already; cap + verify |
| **Referral in real gold** | High | Med | per-referral grams | High (fraud) | **Phase 1**, capped, post-KYC only |
| **Founding-integrator API perks** (higher caps, support) | Med (dev) | High (dev) | ~0 | Low | **Ship now** (Phase 0) |
| Deposit/return-style bonus | — | — | — | — | **Never** — implies return; gate blocks |

**Recommended to test now:** waitlist priority + founding-integrator perks (zero
cost, on-brand). Gift/referral in gold only post-KYC (fraud + compliance).

---

## 22–26. Influencer / partnership / email / landing / funnel

- **Influencers:** gold-YouTube + diaspora finance creators (not crypto-bro); brief
  = "use your gold," honest liquidation-risk disclosure. Phase 1 for consumer.
- **Partnerships:** the highest-leverage consumer channel Auri otherwise lacks —
  diaspora orgs, remittance-adjacent communities. Also **fintechs embedding the
  API** (B2B2C) — live now.
- **Funnel:** Awareness (X/YT/Reddit) → Interest (waitlist/landing) → Consideration
  (email nurture, proof) → **[rails gate]** → Signup → Fund → Activate (first
  buy/borrow) → Refer. The **fund step is the current dead-end** until rails ship.

---

## 27. Budget allocation (illustrative — set with the team)

Phase 0 is deliberately cheap; the expensive channels wait for rails.

| Bucket | Phase 0 (now) | Phase 1 (rails live) |
|---|---|---|
| Content + creative (mostly in-house engine) | Low | Med |
| Launch video production (VIDEO spec) | — | Med (tens of $ per film) |
| Community + diaspora partnerships | Low | Med-High |
| Paid ads | **$0** | Test budget, gated on converting funnel |
| Influencer | — | Med |
| Tooling (APIs: video, publishing) | Low | Low |

The engine keeps content/creative cost near-zero; spend concentrates on
**distribution Auri can't manufacture** (partnerships, diaspora), and only after
the funnel converts.

---

## 28. KPI framework

| Funnel stage | Phase 0 KPI | Phase 1 KPI |
|---|---|---|
| Awareness | reach, X follower growth, share of "gold you can use" voice | + paid CPM/reach |
| Interest | waitlist signups, landing conversion, API signups | + ad CTR |
| Consideration | email open/click, dev docs engagement | demo completion |
| Activation | (n/a — no rails) | **fund→first-action rate** ← north star |
| Referral | gift-loop shares | k-factor |
| Business | integrators signed, authority (mentions/PR) | CAC, activation, retention, LTV |

**North star stays "funded active accounts."** Phase 0 explicitly does not chase
it (impossible without rails) — it builds the pipeline that converts the day
rails ship.

---

## 29. Experimentation plan

Controlled tests, holdout where possible, one variable at a time (feeds the
[learning loop](/../pipeline/scripts/learn.py)):
- **Hook:** credit-wedge ("don't get scored") vs use-it ("gold that works") vs
  trust ("Auri holds $0"). *Learned signal so far: statement + comparison hooks
  lead; security theme hot.*
- **Market copy:** CA "own vs use" vs US "Bitcoin vs gold".
- **Format:** stat-card vs thread vs short video (once video ships).
- **Waitlist offer:** priority-only vs priority + founder-note.
- **Dev message:** "gold API" vs "session-key security" as the headline.

---

## 30. Measurement & attribution

Tag every asset with campaign_id + audience + funnel + objective + CTA (the
`run_id` instrumentation, the top gap in [OKRS.md](/../OKRS.md)). Pull platform
metrics → join to outcomes → `learn.py` aggregates cross-company, feature-level.
**Blocked until:** (a) working publishing, (b) `run_id`, (c) analytics
connectors. Until then, attribution is manual and directional.

---

## 31–33. Analysis → optimisation → learnings

The closed loop, on the substrate already built: measure → `learn.py` →
`INSIGHTS.md` → injected into next generation. Each cycle sharpens "which hook /
format / market / theme works for which audience." Cross-company: patterns
transfer (Vanna ↔ Auri) at the feature level; tenant facts never cross (V6).

---

## Execution status — what is done vs blocked

**Executed / ready now (Phase 0):**
- Positioning, messaging, per-market copy — done (this doc).
- Competitor intel + launch teardown + threat radar — done (22 dossiers).
- ICP, channel priority, timeline, budget frame, KPIs, experiments — done.
- 5 gate-passed content assets + Auri-branded cards — produced this session.
- Trend scout (live gold/fintech signals) + learning loop — running.

**Blocked (be honest):**
- **Consumer launch** — gated on **fiat rails + KYC** (not built). Do not date it.
- **Publishing** — X browser-automation blocked; needs platform APIs or manual.
  Everything is *produced*; going *live* is the pending last mile.
- **Live attribution** — needs publishing + `run_id` + analytics connectors.

**The single most valuable next move to make this executable end-to-end:** a
working publish path (X + LinkedIn + YouTube APIs). Everything upstream is built;
this is the wall between "great plan + assets" and "live, measured, self-improving
GTM."
