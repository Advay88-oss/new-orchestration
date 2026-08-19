# 02 — How Auri Works (Under the Hood)

*Written so a non-engineer can follow it, with enough precision that an engineer can trust
it. Verified against the repo on 2026-08-11.*

---

## The magic trick, in one paragraph

A user taps **"Buy gold."** Behind that single tap, Auri assembles a batch of on-chain
operations — convert cash to a stablecoin, swap the stablecoin for tokenized gold, optionally
post the gold as loan collateral — signs it with a **scoped session key** the user approved
once, and has a **paymaster** pay the network fees. The user signs **nothing** at that
moment, holds no gas token, and sees a normal fintech confirmation screen. That's the whole
product illusion, and it holds because of three separated authorities.

---

## The security model — the golden rule

> **The owner key authorizes · the session key executes · the paymaster pays gas.**

| Authority | Who holds it | What it can do |
|---|---|---|
| **Owner key** (sudo validator) | Privy, inside a TEE — never leaves | Full control of the account |
| **Session key** (permission validator) | Auri backend, AES-encrypted at rest in Postgres | Only what the policy allows: specific contracts, specific functions, a gas cap, a rate limit, an expiry |
| **Paymaster** | ZeroDev | Sponsors gas so the user never needs ETH |

**Why this matters commercially:** the backend can execute trades on a user's behalf *without
ever having unrestricted access to their funds*. A full backend compromise cannot drain
accounts — the session key can only call allowlisted functions on allowlisted contracts,
within a spend cap, until it expires. This is what makes the "Auri holds $0" claim
defensible rather than marketing.

A database test enforces the invariant that **no private-key column exists in the schema.**

---

## The flow, step by step

```
1. Login          User signs in with email / phone / Google / Apple / passkey
                  → Privy creates an embedded wallet; the owner key stays in a TEE
                  → A smart account (ERC-4337 / ZeroDev Kernel v3) address is derived

2. Session grant  User signs ONCE to approve a scoped session key
                  → The owner-signed approval is stored server-side
                  → The private key is never sent to the backend; it is generated and
                    encrypted server-side under KMS

3. Buy            App calls POST /api/execute/buy
                  → Backend builds a batched UserOperation
                  → Session key signs it · paymaster sponsors gas
                  → USDC swapped to XAUT (Enso primary, 1inch fallback)
                  → Optionally supplied as Morpho collateral
                  → txHash returned, position visible in the app

4. Borrow         Morpho borrow against the XAUT collateral, cash to the user's balance
5. Repay/Unlock   Repay, then withdraw collateral to free the gold
```

---

## The pieces and why each was chosen

| Layer | Choice | Why |
|---|---|---|
| **The gold** | **XAUT (Tether Gold)** | Largest tokenized gold token (~$3.3B cap, Q1 2026). Allocated London Good Delivery bars, Swiss vaults, quarterly BDO Italia attestation, bar-level traceability |
| **The cash** | **USDC** | Fully-reserved USD stablecoin; displayed to the user in their own currency (USD or CAD at launch) |
| **The chain** | **Ethereum mainnet (chain ID 1)** | XAUT liquidity and the gold Morpho market exist **only** here. Base has no Tether Gold token; Arbitrum support is partially wired but not the live path |
| **Smart accounts** | **ZeroDev Kernel v3 / EntryPoint 0.7** | Mature ERC-4337 stack with a first-class permission-validator (session key) system and a paymaster |
| **Auth + key custody** | **Privy** | Passwordless login *and* embedded wallet in one; owner key in a TEE means Auri never touches it |
| **Lending** | **Morpho Blue** | Immutable, open-source, permissionless markets. $10B+ deposits, 25+ audits (OpenZeppelin, Spearbit, ChainSecurity, Certora). The specific market is **XAUT collateral / USDT loan**, verified on-chain |
| **Swaps** | **Enso** (primary), **1inch** (fallback) | Aggregated routing; XAUT liquidity is thin so every swap must set `amountOutMinimum` |
| **Prices** | **Chainlink** for settlement, **CoinGecko** for display | Deliberately separated — a display feed must never be able to move money |

### One footgun worth knowing

**XAUT has 6 decimals, not 18.** The codebase guards this aggressively
(`packages/core/src/decimal-utils.ts` has a runtime invariant check). The reference is the
Morpho PAXG oracle incident of October 2024, where a decimals mismatch caused real losses.
Anyone touching amount math must read that file first.

---

## The system map

```
                                    Google Cloud (us-east4)
   Browser                    ┌──────────────────────────────────────────┐
 ┌──────────────┐   REST      │  Cloud Run: auri-api (Fastify 5)         │
 │ apps/web     │ ─ Bearer ─► │    ├─► Cloud SQL (Postgres) users,       │
 │ Next.js 16   │   JWT       │    │   sessions, audit log               │
 │ test.auri.   │             │    ├─► Secret Manager (all secrets)      │
 │ money        │             │    └─► RPC ─► ZeroDev ─► Morpho / Enso   │
 └──────┬───────┘             └──────────────────────────────────────────┘
        │
     Privy (login + embedded wallet, owner key in a TEE)
```

**Apps**
- `apps/web` — Next.js 16, the product (buy/sell/borrow/spend/send, auto-invest)
- `apps/api` — Fastify 5, session management, Kernel orchestration, market data, audit log
- `apps/landing` — the marketing site (auri.money)
- `apps/developer` — standalone developer portal for API-key management

**Shared packages** (`@decisionlab/*`)
- `core` — chain config, token registry, decimal-safe math, shared types
- `aa` — Kernel account, ZeroDev client, permission-validator wrappers
- `defi` — swap router (Enso / 1inch) + Morpho market interfaces
- `oracle` — Chainlink (settlement) and CoinGecko (display), kept strictly separate
- `db` — Prisma schema; a CI test enforces "no private-key columns"

**Infrastructure:** Google Cloud Run in `us-east4`, deployed by GitHub Actions via Workload
Identity Federation → Cloud Build. Merging to `dev` auto-deploys the changed app.

---

## The public API (this is a product, not plumbing)

Auri exposes the same engine the app uses over HTTP with a scoped key. This is what makes
the developer and agent story real.

```http
POST /api/execute/buy
Authorization: Bearer auri_sk_live_…
Idempotency-Key: buy-2026-07-29-001

{ "usdcAmountIn": "1000000" }        // 1.00 USDC — 6-decimal base units

200 OK
{ "txHash": "0x…", "explorerLink": "…" }
```

**Endpoints:** `/api/execute/` → `buy` · `sell` · `borrow` · `repay` · `lend` · `withdraw`.
Credentials are managed at `/api/api-keys` (create · list · revoke).

**Why the API is the one part of Auri that is already global:** it has no fiat rail, no KYC
burden, and no licensing footprint of its own — the integrator serves their own users under
their own compliance. So while the consumer product waits on US and Canadian rails, the
developer product can serve integrators anywhere today.

**Properties that matter to an integrator:**
- **Scoped keys** — `read` and `trade` scopes, hashed at rest, shown once, rotate anytime
- **Idempotent writes** — send an `Idempotency-Key` and a retry can never double-execute
- **Session-secured** — every trade still runs through the owner-approved, spend-capped
  session key. **A leaked API key cannot exceed the caps, reach another account, or move
  funds to an external address.** That is a genuinely unusual security property for a
  financial API and it should be a headline in developer marketing.
- **Private beta** — key creation requires an access code today.

Other surfaces live under `/api/`: `account`, `sessions`, `balance`, `market`, `activity`,
`prices`, `kyc`, `wallets`, `referral`, `auto-invest`, `notifications`, `gift`, `api-keys`.

---

## How to explain this to a non-technical person

Use this analogy; it lands every time.

> Think of a **safety deposit box** that only you have the key to. You give the bank a
> *limited pass* that says: *"you may take gold out of my box only to buy more gold, or to
> pledge it for a loan — nothing else, up to this amount, until this date."* The bank can
> act fast on your behalf, but it can never empty the box, and it can never hand your gold
> to anyone else. That limited pass is the session key. Auri holds the pass. **You keep
> the key.**

---

## What an engineer should read next

1. `SECURITY.md` — the full threat model and key invariants
2. `ONBOARDING.md` — how the repo is wired, local dev, ops cheat-sheet
3. `packages/defi/src/addresses.ts` — on-chain-verified contract set (do not edit without
   re-verifying; a wrong address loses funds)
4. `packages/core/src/decimal-utils.ts` — the decimal invariants
5. `CLAUDE.md` — team conventions, branching, commit rules
