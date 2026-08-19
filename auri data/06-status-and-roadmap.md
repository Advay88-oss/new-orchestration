# 06 — Status & Roadmap (The Honest Version)

*Verified against the repo on 2026-08-11, branch `feat/public-rest-api`. This is the file to
check before you promise anything to anyone.*

---

## Why this file exists

The landing site describes the **destination**. This file describes the **current position**.
Both are legitimate — every startup markets ahead of its build — but confusing them in front
of a partner, an investor, or a customer is how trust gets destroyed.

**Rule: never quote a landing-page capability without checking this table first.**

---

## The build state, feature by feature

### ✅ Live and working

| Feature | Evidence |
|---|---|
| **Passwordless login** (email, phone, Google, Apple, passkey) | Privy integration in `apps/web` |
| **Smart account creation** (ERC-4337 / ZeroDev Kernel v3) | `packages/aa` |
| **Session keys** — owner-signed, scoped, spend-capped, expiring | `apps/api/src/routes/sessions.ts` |
| **Gasless transactions** via paymaster | ZeroDev paymaster wired |
| **Buy gold** — USDC → XAUT via Enso/1inch | `POST /api/execute/buy` |
| **Sell gold** — XAUT → USDC | `POST /api/execute/sell` |
| **Borrow** — XAUT collateral on Morpho, cash out | `POST /api/execute/borrow` |
| **Repay / unlock collateral** | `POST /api/execute/repay` |
| **Withdraw** (crypto) | `POST /api/execute/withdraw` |
| **Live market pricing** — Chainlink settlement + CoinGecko display | `/api/market`, `/api/prices`; no hardcoded prices anywhere |
| **Balance, activity, audit log** | `/api/balance`, `/api/activity` |
| **Gift gold** | `apps/api/src/routes/gift.ts` — owner-signed transfer, server-side receipt verification |
| **Referral** | `/api/referral` with tests |
| **Auto-invest (SIP/DCA)** | `/api/auto-invest` + `workers/auto-invest-worker.ts` |
| **Notifications** | `/api/notifications` |
| **Public REST API + scoped API keys** | `/api/execute/*`, `/api/api-keys`; idempotency, hashed keys, `read`/`trade` scopes |
| **Developer portal** | `apps/developer` — standalone API-key management app |
| **Deployment pipeline** | GitHub Actions → Workload Identity Federation → Cloud Build → Cloud Run (`us-east4`) |

### 🟡 Partial — exists but not production-complete

| Feature | What's actually there | What's missing |
|---|---|---|
| **KYC** | `/api/kyc/status` + `/api/kyc/submit`, `User.kycStatus` drives feature gating in the app | **No real provider.** `KYC_AUTO_APPROVE` approves instantly outside production. The webhook seam is documented but a provider (Persona / Sumsub / Onfido) has not been chosen or integrated |
| **Boost (5× leverage)** | UI and local state only | The on-chain leverage leg — owned by another developer |
| **Arbitrum support** | Addresses partially verified in `packages/defi/src/addresses.ts` | Not the live path. **Ethereum mainnet (chain 1) is the only supported chain** |
| **Claim links** (gift without an account) | Gift transfer works to a username or wallet | The no-account claim flow |

### ⛔ Not built — described publicly, does not exist in code

| Feature | Reality |
|---|---|
| **Fiat on-ramp** | No `/api/fiat/*` routes exist. **Needed twice — 🇺🇸 ACH/wire/debit and 🇨🇦 Interac/EFT.** Candidates: 🇺🇸 Circle, Bridge, Stripe, Nuvei · 🇨🇦 Versapay, Nanopay, Flinks Pay, Moneris |
| **Fiat off-ramp (withdraw to bank)** | Same — nothing built, in either market |
| **Bank account linking** | No routes. Candidates: 🇺🇸 **Plaid** · 🇨🇦 **Flinks** (better Canadian coverage) or Plaid Canada |
| **Multi-currency / multi-market support** | The product is CAD-denominated in copy and docs. **USD display, US rails, and market-scoped configuration do not exist yet** |
| **The Auri card** | No issuer selected, no code |
| **Remittance corridors** (e.g. → INR) | Not built |
| **MCP server** | Documented; package names are explicitly placeholders |
| **CLI (`auri` binary)** | Documented; not published |
| **API sandbox** | On the roadmap, per the public docs |
| **Webhooks** | On the roadmap, per the public docs |
| **Auri Jewels rewards** | Described in docs; no ledger in code |
| **Tax export** | Planned in `STATUS.md` |
| **Mobile apps (iOS / Android)** | Planned — Expo/React Native in `apps/mobile/`, not started |

---

## 🔴 The critical path

**Everything downstream is blocked on two integrations:**

```
   FIAT ON-RAMP  +  REAL KYC          ← per market: 🇺🇸 ACH  ·  🇨🇦 Interac
          ↓
   users can actually fund an account
          ↓
   the money engine (already built and working) becomes usable
          ↓
   growth loops (gift, referral, SIP) have something to grow
```

A user today can log in, get a smart account, and grant a session — and then hit a wall,
because there is no way to put money in. **The money engine is the hard part and it is done.
The rails are the easy part and they are not.**

This should shape every planning conversation: Auri is not blocked on hard technology. It's
blocked on partner integrations and, most likely, on the compliance work that gates them.

**Now that scope is US + Canada, this gets more demanding, not less.** Two markets means two
ramp integrations, two banking relationships, and two regulatory regimes — but it does *not*
have to mean two products. **The single most valuable architectural decision available right
now is to build the fiat layer market-agnostic from the start:** a `market` on the user, a
provider interface behind the deposit/withdraw routes, and currency as data rather than a
hard-coded `CAD`. Doing this before the first ramp integration is cheap. Doing it after
costs months.

---

## P0 blockers (Sprint 0 — must close before any real-money launch)

From the sprint plan:

1. **Docker runs `NODE_ENV=development` in production** — disables production hardening
2. **`checkDailyLimit()` is never called** — the paymaster spend cap is dead code, so gas
   sponsorship is effectively uncapped (a security *and* a cost problem)
3. **CORS defaults open** — `allowedOrigin = true`
4. **Missing `apps/web/Dockerfile`**

These are small fixes with large consequences. They are the cheapest risk reduction
available.

---

## Known documentation inconsistencies to fix

| Claim | Where | Reality |
|---|---|---|
| "Settles on **Arbitrum**" | `README.md`, public docs, landing site | `SUPPORTED_CHAIN_IDS = [1]` — **Ethereum mainnet**. XAUT liquidity and the gold Morpho market only exist there |
| "MCP · CLI — **live**" | Landing `#developers` section | Neither is published; package names are placeholders |
| "$248.6M originated to date" | Public docs, borrowing section | Verify the provenance of this figure before reusing it |
| "Backend in `asia-south1`" | `ONBOARDING.md` | Infra moved to GCP `us-east4`; `ONBOARDING.md` is stale relative to `AURI_INFRA_GCP.md` |
| Frontends on Vercel | `ONBOARDING.md` | Migrated to Cloud Run |
| **"Live in Canada · Interac" · "Canada (EN) · CAD" · "not CDIC-insured"** | Landing site, public docs, footer legal | **Scope is now US + Canada.** Every Canada-only string needs a US counterpart: USD, ACH, *"not FDIC-insured"*, and US-appropriate legal disclaimers. **This is a launch blocker for the US, not a cleanup task** |
| "Auri is live at **auri.finance**" / "app at **app.auri.ca**" | Public docs | Live properties are `auri.money` and `test.auri.money`. A `.ca` domain also reads as Canada-only to a US audience |

**None of these are dishonest** — they're the normal drift of a fast-moving repo. But they
should be corrected before external parties read the docs, especially the Arbitrum claim
(a technical partner will check it) and the Canada-only framing (a US user or investor will
read the site and conclude the product isn't for them).

---

## Suggested priority order

**P0 — Unblock the funnel**
1. Close the four Sprint 0 P0 blockers
2. **Make the fiat/market layer multi-market before writing any of it** — `market` on the
   user, a provider interface behind deposit/withdraw, currency as data not a hard-coded
   `CAD`. Cheap now, expensive later
3. Select one KYC provider that covers **both** the US and Canada (Persona, Sumsub, and
   Onfido all do — don't run two)
4. 🇨🇦 Integrate an Interac / EFT on-ramp partner and the matching off-ramp
5. 🇨🇦 Bank account linking (Flinks)
6. **In parallel, non-engineering: commission the US legal opinion** on whether Auri's
   non-custodial architecture requires state money-transmitter licensing. It gates the
   entire US roadmap and takes calendar time, so start it now — see [05](05-business-model.md)

**P1 — Make the product complete**
7. Claim links (unlocks the gifting viral loop — the cheapest acquisition Auri has)
8. Correct the documentation inconsistencies above, **including the Canada-only framing**
9. Ship the MCP server and CLI for real, or remove the "live" labels from the landing page
10. Complete the Boost on-chain leg, or hide the UI until it works

**P2 — 🇺🇸 US market entry** *(sequenced by the legal answer from step 6)*
11. USD display, US legal copy (`not FDIC-insured`), US-facing marketing site
12. ACH / wire / debit on-ramp + off-ramp; Plaid bank linking
13. State-by-state rollout if licensing is required — largest diaspora states first
    (CA, TX, NJ, NY, IL); **New York last, it's the hardest**

**P3 — Scale**
14. Card programme (issuer selection, BIN sponsorship — **separate per country**)
15. Remittance corridors (US→India and US→Mexico are the largest in the world)
16. API sandbox + webhooks — note the **developer business is not blocked by any of the
    above and can serve integrators globally today**
17. Mobile apps
14. Jewels rewards ledger, tax export

---

## Where the real documentation lives

| Topic | File |
|---|---|
| Repo wiring, local dev, ops cheat-sheet | `ONBOARDING.md` |
| Security model and key invariants | `SECURITY.md` |
| Local development setup | `LOCAL_DEV_GUIDE.md` |
| Current GCP architecture | `AURI_INFRA_GCP.md` |
| Backend deploy runbook | `DEPLOY_BACKEND_USEAST4.md` |
| Frontend deploy runbook | `DEPLOY_FRONTEND_GCP.md` |
| Observability | `OBSERVABILITY.md` |
| Contract addresses | `CONTRACTS_REFERENCE.md`, `packages/defi/src/addresses.ts` |
| Full build backlog | `STATUS.md` |
| Team conventions, branching, commit rules | `CLAUDE.md` |
| **Sprint scope — the source of truth** | Notion: *"Auri — Production Sprint Plan"* |

---

## Local dev quick start

```bash
docker-compose up postgres -d                  # Postgres on :5432
pnpm install
pnpm --filter @decisionlab/db db:generate
```

Then start each service individually — the root `pnpm dev` does not reliably start the API:

| Service | Port |
|---|---|
| web | 3000 |
| api | 3001 |
| landing | 3002 |
| developer portal | 3003 |

Full setup: `LOCAL_DEV_GUIDE.md`.
