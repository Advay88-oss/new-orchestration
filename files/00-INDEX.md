# Vanna Protocol — GTM Knowledge Base

**Version:** 1.0
**Compiled:** 6 August 2026
**Purpose:** Single source of truth about Vanna Protocol for the GTM / sales / marketing agent. Every file in this directory is written to be read by an AI agent that will produce competitive analysis, positioning, content, and outbound on Vanna's behalf.

---

## How to use this knowledge base

**Read order for a cold agent:**

1. `08-facts-ledger-and-claim-safety.md` — **read this first, always.** It defines what is provable, what is aspirational, and what must never be claimed. Vanna is pre-mainnet; getting this wrong creates legal and reputational risk.
2. `01-company-identity-and-positioning.md` — who Vanna is and the one-sentence story.
3. `02-product-and-technical-architecture.md` — what actually exists and how it works.
4. `03-agentic-layer-and-ai-thesis.md` — the agent/AI strategy, which is the current spearhead of the narrative.
5. `04-brand-voice-and-message-library.md` — how Vanna sounds; approved copy blocks.
6. `05-audiences-personas-and-objections.md` — who we sell to and what they push back on.
7. `06-market-context-and-competitive-frame.md` — market tailwinds and the competitive frame. Superseded in part by `10`, but still the framing layer.
8. `07-knowledge-graph.md` — machine-readable entity/relationship map for reasoning and retrieval.
9. `10-competitor-battlecards.md` — eight battlecards and market sizing (research pass, 6 Aug 2026). **Read `11` immediately after — `10` establishes the facts, `11` says what to do about them.**
10. `11-competitive-strategy-and-repositioning.md` — **the current positioning.** Two claims were retired in Aug 2026: "MCP-native" (Morpho Agents shipped it on mainnet) and "nobody else is building agent credit scores" (Kojiru, ERC-8004, Visa TAP, WEF KYA, IETF). §7 is the messaging substitution table the content pipeline consumes; §10 is the standing rules. Sections marked Tier E must never be published.
11. `09-gtm-toolkit-and-agent-operating-guide.md` — the marketing skill library available and how to wire this KB into it.

---

## The one-paragraph version

Vanna Protocol is composable, undercollateralized credit infrastructure for DeFi. A user deposits collateral once into a per-user on-chain margin account, borrows up to **10×** against it, and deploys that borrowed capital across spot, perps, options, prediction markets, yield farming and AI-compute markets — all under **one** cross-margined health factor, so a loss in one venue is offset by a gain in another. Borrowed capital never leaves the protocol's control. On the other side, passive liquidity providers supply assets to lending pools and earn the interest borrowers pay. On top of that credit layer, Vanna is building an **agent-native** surface: MCP server, CLI, and TypeScript SDK hitting the same rails, plus a behavioural **Agent Score** that turns on-chain track record into a credit line, queryable by third parties over x402. Vanna is currently **live on Stellar Testnet, pre-mainnet.**

---

## Positioning statement (approved)

> **For** leveraged DeFi traders, DeFi-integrating businesses, institutional desks, and autonomous agents
> **who** need real leverage that works across markets instead of being trapped in a single venue,
> **Vanna is** composable undercollateralized credit infrastructure
> **that** gives one margin account up to 10× credit across every market under a single health factor, with an agent-native control surface.
> **Unlike** overcollateralized money markets (credit that moves but never exceeds your collateral) or isolated-margin venues (leverage that exceeds collateral but can't leave the venue),
> **Vanna does both at once.**

---

## Source provenance

Everything in this KB traces back to one of the following. When an agent generates a claim, it should be able to name the source class.

| Source | Trust level | Notes |
|---|---|---|
| `docs.vanna.finance` (live technical docs) | **Canonical** | Reflects the shipped Stellar Soroban implementation |
| `vanna.finance` (live marketing site, Aug 2026) | **Canonical for messaging** | Contains illustrative/demo numbers — see claim safety |
| Website UI screenshots + product video frames (Aug 2026) | **Canonical for messaging** | Visual and copy confirmation |
| `what_is_vanna.pdf` — "Vanna x AI Agents: Practical Product Ideas for Delphi" | **Internal strategy** | Investor-facing product roadmap; not all shipped |
| Internal research skills (`composable-credit-research`, `vanna-comparative-analysis`, failure post-mortems) | **Internal strategy** | Dated Feb 2026, partly reflects a *superseded* EVM-era design |
| `vanna-brand-guidelines` SKILL.md | **Canonical for design** | Design system in production use |
| Public web (Stellar docs, Chainalysis, Galaxy, ETHGlobal, GitHub, X) | **External, verifiable** | Cite when used for market claims |

---

## Critical version-reconciliation warning

There are **two generations** of Vanna in the available material. An agent that mixes them will produce false content.

| Dimension | Legacy / EVM-era design (internal research, ~2024–Feb 2026) | **Current canonical (Stellar Soroban, live now)** |
|---|---|---|
| Chain | Optimism, then multi-chain EVM ambition | **Stellar (Soroban) Testnet** first; Base/Arbitrum/Optimism referenced as ecosystem |
| Account abstraction | ERC-4337 smart accounts | **Per-user deployed Soroban `SmartAccount` contract** |
| Max leverage | 5× base / 7× blue-chip (asset-tiered) | **10×**, derived from the 1.1× health-factor borrow guard |
| Liquidation threshold | Varied | **Health factor 1.1×** |
| Contract count | ~828 contracts referenced for DeltaPrime comparison | **14 Soroban contracts** |
| Signature feature | "Greeks Dashboard", "Track Token" | **Risk Engine + TrackingToken + Agent layer (MCP/CLI/SDK) + Agent Score** |
| Oracle | Various | **Reflector** (via Oracle passthrough contract) |

**Rule for the agent:** when a technical claim conflicts, the **live docs (`docs.vanna.finance`) win**. Treat "Greeks Dashboard", "ERC-4337", "5x/7x tiered leverage", and "Prop Dashboard" as **legacy vocabulary — do not use in new content** unless a human confirms it has returned.
