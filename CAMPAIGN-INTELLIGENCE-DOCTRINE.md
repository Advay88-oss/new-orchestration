# Campaign Intelligence Doctrine

How the engine researches, reverse-engineers, and learns from **real-world**
campaigns — the operating rules every research/strategy agent follows. This is
fed into the pipeline (see "How it's wired" below); it is not a document that
gets forgotten.

**The one objective:** not "generate marketing ideas." It is —
> *Research what the market is actually doing → understand WHY it worked → design
> an original strategy → execute → measure real business outcomes → learn →
> improve the next one.*

---

## The five rules that outrank everything

These are the non-negotiables distilled from the 17-part spec. Every agent obeys
them; the rest of this doc is detail.

1. **Executed, not opined.** Only learn from campaigns someone *actually ran*.
   Distinguish "someone says this is a good strategy" from "someone did this and
   here is what happened." First-hand founder/marketer/community breakdowns
   outrank theory. Weight a source by evidence of execution.

2. **Causal, not correlational.** Never stop at "this campaign was successful."
   Break down the *mechanism*: Audience → Problem → Hook → Message → Creative →
   Distribution → Social proof → Offer → CTA → Funnel → Activation → Conversion →
   Retention. Identify *why* it worked, not that views were high.

3. **Business results, not vanity.** Likes/views/impressions/followers are vanity.
   Signups/activation/CAC/revenue/retention/LTV are business. A viral campaign is
   **not** classified as successful unless attention turned into user behaviour.
   Always ask: *"Did attention become meaningful action?"*

4. **Label inferences as inferences.** Where conversion/CAC/revenue data is not
   public, say so — *"inferred, not measured."* Never pretend to know numbers.
   This is the same honesty discipline the claim gate enforces on product claims,
   applied to campaign analysis.

5. **Every asset carries its coordinates.** No content is generated without
   **Audience + Funnel Stage + Objective + CTA** attached. This prevents random
   content and lets measurement (§O) and learning (§Q) group by those dimensions.

---

## What to research (sources, in priority order)

First-hand execution breakdowns first: **Reddit** (candid "what actually
worked/failed, how much budget, how users were acquired, why they converted or
didn't"), founder interviews, growth reports, public teardowns, build-in-public
threads. Then **X** (launches, founder campaigns, "alternative to X" and
buying-intent conversations), **Product Hunt / Hacker News** (launch mechanics),
YouTube/LinkedIn/communities, and competitor sites/launch pages/observable ads.

Reddit is dual-use: a customer-intent research source *and* a channel the engine
should evaluate for execution (Community/Interest/Keyword/Retargeting audiences).

Classify every conversation by intent: **awareness · problem-aware ·
solution-seeking · comparison · purchase-intent · post-purchase.** That intent
maps directly to which funnel stage a campaign should target.

---

## Reconstruct launches as timelines, not post collections

For every relevant launch, rebuild the campaign as a timeline across three
phases — and answer the specific questions in each:

- **Before:** how far ahead did they start? audience/waitlist? anticipation?
  founder posting? educational content? teasers? community seeding? influencers?
  partnerships? early users?
- **Launch:** launch-day announcement, creative, launch video, demo, offer,
  scarcity, social proof, influencer participation, founder promotion, platforms,
  CTA, where traffic went.
- **After (7/14/30 days):** retargeting, testimonials, case studies, referral,
  incentives, continued content, paid, email sequences, new features, community
  loops.

Output is a **campaign timeline**, e.g. `T-30 teaser → waitlist → founder content
→ reveal → launch video → influencer push → offer → retargeting → community`.

---

## The knowledge bases this builds

Three durable stores, feature-level and cross-company (V6-safe — patterns
transfer between tenants; a tenant's proprietary facts never do):

1. **Campaign type library** — the ~35 types (product-launch, waitlist, PLG,
   founder-led, community-led, content-led, referral, comparison,
   competitor-switching, freemium, LTO, challenge, ABM, reactivation…). For each:
   when it works, for which product/audience/funnel-stage/budget. The engine
   *selects* the fitting mechanism — it does **not** assume all apply.

2. **Campaign pattern KB** — recurring cause→effect: which hooks repeatedly grab
   attention, which offers cut conversion friction, which channels fit B2B vs
   B2C, which incentives lift signups but *hurt* retention, which content creates
   demand vs captures existing demand, which campaigns bring high- vs low-quality
   users.

3. **"What NOT to do" KB** — failed launches/ads/products/influencer/community
   campaigns, founder post-mortems, Reddit failure threads. **Learn from failure
   patterns as much as success patterns.**

---

## From research to campaign (the output contract)

After research, produce a strategy (objective, audience, ICP, problem, market
opportunity, competitive context, campaign type + *why this one*, core idea,
positioning, message, hook, offer, incentive, funnel, channels, content/creative/
influencer/community/paid/retargeting/landing/email/referral strategy, timeline,
budget, KPIs, experiments, expected outcomes) — then generate the actual assets
(names, calendar, platform-native posts, scripts, launch-video script, ad
creatives/copy, landing copy, email sequence, threads, community strategy,
influencer/UGC briefs, referral + incentive campaigns, retargeting, CTAs,
storyboards). Every asset tagged with its coordinates (rule 5).

**Multi-touch by default.** Not `Ad → Signup`. Design the touchpoint sequence the
buying cycle actually needs: `Problem → Education → Founder story → Product intro
→ Demo → Social proof → Offer → Landing → Signup → Activation → Retargeting →
Conversion → Referral`. Choose the number/type of touches from the product and
cycle.

**Psychology, honestly.** Use legitimate conversion mechanisms — curiosity,
trust, authority, social proof, demonstration, specificity, risk reduction,
reciprocity, community validation, clear ROI, pain reduction, belonging, and
urgency/scarcity/FOMO *only where genuine*. **Avoid manipulative or deceptive
tactics** — the same line the brand-voice and claim rules already draw.

---

## Optimise for real conversion (diagnose the drop, prescribe the fix)

Track the full funnel — Impression → Click → Landing → Signup → Activation →
Trial/Usage → Paid → Retention → Referral → Revenue — and **diagnose where users
drop, then recommend the next intervention** (not just report numbers):

| Symptom | Likely problem | Fix |
|---|---|---|
| High impressions, low CTR | creative / hook / targeting | new hook, tighter audience |
| High CTR, low signup | landing / message mismatch / offer | align landing to ad; reduce friction |
| High signup, low activation | onboarding / product value / UX | fix first-run experience |
| High activation, low payment | pricing / value perception / paywall | reprice, re-frame value |
| High conversion, low retention | PMF / expectation mismatch / experience | fix the product, not the ad |

Build **experiments** into every campaign: `Hypothesis → Variant A → Variant B →
KPI → Result → Decision`, one variable at a time.

---

## How this is wired into the engine

- **Doctrine injected:** the concise operating rules live in
  `pipeline/buzz-pack/campaign-doctrine.md` and are appended to every agent's
  shared instructions (alongside the learned-signal brief), so the scout and
  strategists reason under these rules by construction.
- **Research:** `trend_scout.py` already pulls X/Reddit/News signals with
  engagement; the campaign layer adds intent-classification and
  executed-vs-opined weighting, and stores teardowns under
  `okf-{tenant}/campaign-intel/`.
- **Learning:** `learn.py`'s feature-level KB extends to campaign features (type,
  funnel stage, hook, offer, touch count) — cross-company, isolation-safe.
- **Honesty:** rules 3 and 4 are enforced the way product claims are — vanity
  metrics never stand in for business results, and every un-sourced number is
  labelled inferred.

## Honest current limits

- **Business-metric data is mostly non-public.** Most teardowns will end at
  *inferred* conversion — that is correct behaviour (rule 4), not a gap to paper
  over.
- **Reddit/X depth needs the browser bridge up.** News/RSS always works; candid
  Reddit threads need OpenCLI connected.
- **The pattern KB gets predictive only with volume.** Early teardowns are
  intelligence; the KB sharpens as it fills.
