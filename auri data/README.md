# Auri — Team Brief

**A shareable, non-technical-first explainer of what Auri is, who it's for, who we compete
with, and how we win.**

Written for: new teammates, advisors, design/marketing collaborators, and anyone who asks
*"okay but what does Auri actually do?"*

> **This folder is gitignored on purpose.** It is a briefing pack, not product code. Share
> it as a folder, a zip, or export it to PDF (see below). Nothing in here is a legal,
> financial, or regulatory document.

**Last updated:** 2026-08-11 · **Status of product facts:** verified against the repo on
this date (`feat/public-rest-api`).

**Market scope: 🇺🇸 United States + 🇨🇦 Canada at launch, global thereafter.** The gold, the
Swiss vault, the lending market, and the rails are borderless — only funding, KYC, and
licensing are country-specific. The two markets have almost entirely different competitors
and *very* different regulatory burdens, so files 03, 04, and 05 treat them separately.

---

## Quick explainer (Hinglish — 60 seconds)

Auri ek **gold neobank** hai.

- User email se login karta hai (no wallet, no seed phrase, no MetaMask).
- Cash daalta hai → **asli allocated gold** kharidta hai (Tether Gold / XAUT — Switzerland
  ke vault me numbered bars, quarterly attested).
- Gold **bechna nahi padta** — uske against cash **borrow** kar sakta hai (~3.75% APR,
  no credit check), spend kar sakta hai (card), kisi ko **bhej** sakta hai ya **gift** kar
  sakta hai, aur **auto-invest** (SIP) bhi laga sakta hai.
- Gold **Auri ke paas nahi hota** — user ke apne wallet me hota hai. Auri ke paas **$0**
  user funds hote hain. Yehi sabse bada differentiator hai.
- Andar sab kuch on-chain hai (smart accounts + session keys + gasless), lekin user ko
  bilkul ek normal fintech app dikhta hai.
- **Market: pehle USA + Canada, phir poori duniya.** Gold, vault, lending market — sab
  borderless hai. Sirf paisa daalne/nikaalne ka rasta (fiat rails), KYC, aur licence har
  desh me alag hote hain. Isliye launch North America se, aur baaki markets uske baad.

**Ek line me:** *Gold ab sirf locker me pada rehne wali cheez nahi — usse kharcho, bhejo,
gift karo, aur uske against udhaar lo, bina bechhe, aur bina custody chhode.*

Business ka core insight: duniya me ~$25T gold pada hai jo **kaam nahi karta**. Banks
aapko unka paisa udhaar dete hain aur credit score maangte hain. Gold apps sirf metal
park karte hain. Auri dono ka gap bharta hai.

---

## How to read this pack

| # | File | What's in it | Read if you are |
|---|---|---|---|
| 01 | [What Auri is](01-what-is-auri.md) | Product, features, the pitch, what's live vs. not | Everyone — start here |
| 02 | [How it works](02-how-it-works.md) | Architecture and security in plain English | Eng, technical partners |
| 03 | [Competitors](03-competitors.md) | 🇺🇸 and 🇨🇦 landscapes separately, feature matrix, threat radar | Founders, GTM, investors |
| 04 | [Customers & go-to-market](04-customers-and-gtm.md) | ICPs, personas, channels, funnel, metrics, per-market rails | Growth, marketing, sales |
| 05 | [Business model & risks](05-business-model.md) | Revenue lines, unit economics, **US vs. Canada regulatory**, risk register | Founders, finance, legal |
| 06 | [Status & roadmap](06-status-and-roadmap.md) | Honest build state — shipped vs. mocked vs. planned | Everyone, especially new eng |
| 07 | [FAQ & objections](07-faq-objections.md) | Hard questions with straight answers | Anyone talking to a customer |

**Fastest path for a new joiner:** 01 → 06 → 03. That's ~25 minutes and you'll be able to
hold a conversation about Auri with anyone.

---

## Export to PDF

There is no PDF checked in (it would go stale in a week). Generate one when you need it:

**Option A — VS Code (easiest)**
1. Install the *Markdown PDF* extension.
2. Right-click any `.md` file → **Markdown PDF: Export (pdf)**.

**Option B — Pandoc (one PDF for the whole pack)**
```bash
cd auri-brief
pandoc README.md 01-*.md 02-*.md 03-*.md 04-*.md 05-*.md 06-*.md 07-*.md \
  -o Auri-Team-Brief.pdf --toc --pdf-engine=xelatex -V geometry:margin=1in
```

**Option C — Notion**
Drag the folder into Notion (*Import → Markdown*). It preserves headings and tables, and
gives you a shareable link. This is the recommended route for non-technical teammates.

---

## Ground rules for this pack

1. **Product facts** (what's built, what chain, what the API does) are verified against the
   repo. If something contradicts the code, the code wins — file a fix.
2. **Market and competitor facts** carry sources. They were correct as of August 2026 and
   will drift; re-check before putting any number in a deck.
3. **Strategy sections** (GTM, business model, positioning) are *analysis and proposals*,
   not decisions that have been made. They are explicitly marked. Treat them as a starting
   point for a discussion, not as company policy.
4. **Marketing copy ≠ shipped feature.** The landing site describes the full product
   vision. [06 — Status & roadmap](06-status-and-roadmap.md) tells you what actually runs
   today. Never quote a landing-page number to a partner without checking file 06 first.
5. **The public site is still Canada-only in its copy** ("Live in Canada · Interac",
   "Canada (EN) · CAD", "not CDIC-insured", `app.auri.ca`). That contradicts the North
   American scope and reads as *"not for you"* to a US visitor. Tracked as a launch blocker
   in [06](06-status-and-roadmap.md), not a cleanup task.

---

## The three things worth knowing before any other conversation

1. 🔴 **The funnel has no top.** No fiat rails, no real KYC — in either market. The money
   engine (buy/sell/borrow/repay) is built and works; the rails around it are not. Every GTM
   idea is blocked behind this.
2. 🔴 **One legal question is worth ~$1M.** FinCEN's 2019 guidance says a provider whose role
   is limited to adding a second authorization key alongside the owner's key is *not* a money
   transmitter — which reads almost like a spec of Auri's session-key model. If US counsel
   confirms it, the US is cheap to enter. If not, it's a 12–18 month, seven-figure,
   49-state licensing programme. **Commission that opinion now.**
3. 🟠 **Coinbase is the competitor nobody has named.** They lend USDC against BTC from ~4%,
   built on Morpho — the same protocol Auri uses. Adding gold collateral is closer to a
   config change than a rebuild. Auri's defence is brand, distribution, and network effects,
   never technology.
