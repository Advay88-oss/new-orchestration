# Subject Category Deep-Dive: Uncollateralized Lending & Composable Credit

**Analysed:** 2026-09-10 · **Window:** 2026-06-11 → 2026-09-10 (90 days)
**Market Universe:** 18 Uncollateralized Lending protocols + 2 Related Debt/Collateral Markets
**Category Total TVL:** $292,442,412 (Led by Pareto Credit at $226.2M, 77.4% share)

## Executive Finding — Marketing Outliers in Low-TVL Credit

> **Prior research concluded this category *"has no active marketing incumbent."* Credit Coop and Accountable contradict that.** Both are publishing outliers at $3.7M–$4.5M TVL — Credit Coop runs a biweekly deal-by-deal credit memo series (5 editions) plus a `$18M originated, $0 defaulted` tracker; Accountable runs a monthly Corporate Credit Health Index. Neither appeared in the prior 15-player roster.

**Category Boundary Clarification:**
- **Gearbox is not in this category.** DefiLlama classifies it under standard `Lending` at $22.4M TVL.
- TrueFi ($21.7k) and Goldfinch ($2.56M), the former giants of uncollateralized crypto credit, have largely ceased high-cadence public marketing.

---

## Tier 1: Collected Active Outliers (2 Protocols)

These protocols have verified publishing footprints, active blogs, and confirmed repeating patterns in the registry.

### Credit Coop — TVL $4,588,671.47

- **X Handle:** [@creditcoop_xyz](https://x.com/creditcoop_xyz) · **Blog:** [https://blog.creditcoop.xyz](https://blog.creditcoop.xyz) · **90d Artefacts:** 8
- **Marketing Engine:** Transparency-as-underwriting. Extreme publishing cadence relative to TVL ($4.59M), using deal-by-deal credit memos as public content to attract institutional allocators.

#### Repeating Patterns
| Content category | Subcategory | The repeating post — the actual pattern | Timeline | Hook |
|---|---|---|---|---|
| Research | Deal-by-deal credit memo | Underwriting Facility #[N]: Borrower balance sheet review & debt covenants. | Biweekly · 5 in window | Full institutional disclosure |
| Metrics / Security | Zero-default tracker | "$18M Originated, $0 Defaulted" — Repeating monthly volume vs bad debt counter. | Monthly · 3 in window | "Zero bad debt" proof |

#### What Vanna Can Do Here
| Credit Coop's pattern | Verdict | Vanna's version | Blocked by |
|---|---|---|---|
| Public deal credit memos | **ADAPT STRUCTURE** | Publish 'Sandbox Risk Memos' dissecting hypothetical 10x leverage loops on Blend and Aquarius with exact liquidation math. | Nothing — runnable today on testnet |
| Zero-default cumulative tracker | **AVOID (until mainnet)** | — | No live loans on mainnet; testnet positions carry no real default risk. |

---

### Accountable — TVL $3,746,493.19

- **X Handle:** [@AccountableData](https://x.com/AccountableData) · **Blog:** [https://blog.accountable.capital](https://blog.accountable.capital) · **90d Artefacts:** 5
- **Marketing Engine:** Data-first institutional reporting. Leverages proprietary borrower balance-sheet API indexing to publish periodic 'Corporate Credit Health' macro indices.

#### Repeating Patterns
| Content category | Subcategory | The repeating post — the actual pattern | Timeline | Hook |
|---|---|---|---|---|
| Research | Corporate Credit Health Index | Monthly industry benchmark charting solvency ratios of real-world private debt borrowers. | Monthly · 3 in window | Proprietary balance sheet index |
| Product | API & telemetry release | Telemetry Update: Direct QuickBooks/Xero and NAV oracle on-chain sync feeds. | Periodic · 2 in window | Real-time accounting sync proof |

#### What Vanna Can Do Here
| Accountable's pattern | Verdict | Vanna's version | Blocked by |
|---|---|---|---|
| Proprietary credit index report | **ADAPT STRUCTURE** | Create 'Stellar Soroban Liquidity & Health Factor Index' charting collateralization trends across Blend and Soroswap. | Nothing — data accessible via Horizon/Mercury indexer |
| Real-time accounting telemetry update | **PREPARE NOW, FIRE LATER** | Publish telemetry updates when Mercury indexer feeds are connected to Vanna SmartAccounts. | ROADMAP: needs Mercury indexer live integration |

---

## Tier 2: Uncollected Category Members (16 Protocols)

These protocols are tracked in the census but have no verified repeating marketing patterns. All are marked `collection_status: PENDING`. Zero patterns are invented.

| Protocol | Slug | TVL (USD) | X Handle | Official Website | 90d Blog Artefacts | Collection Status | Note |
|---|---|---|---|---|:---:|:---:|---|
| **Pareto Credit** | `pareto-credit` | $226,216,675.04 | @paretocredit | [https://paretocredit.com](https://paretocredit.com) | 0 | `PENDING` | FLAGSHIP_INSTITUTIONAL |
| **cSigma Finance** | `csigma-finance` | $21,591,638.53 | @csigmafinance | [https://csigma.finance](https://csigma.finance) | 0 | `PENDING` | PENDING |
| **Kasu** | `kasu` | $12,518,044.95 | @kasuFinance | [https://kasu.finance](https://kasu.finance) | 0 | `PENDING` | PENDING |
| **3Jane Lending** | `3jane-lending` | $12,404,917.09 | @3janexyz | [https://3jane.xyz](https://3jane.xyz) | 0 | `PENDING` | PENDING |
| **Wildcat Protocol** | `wildcat-protocol` | $8,202,229.86 | @WildcatFi | [https://wildcat.finance](https://wildcat.finance) | 0 | `PENDING` | PENDING |
| **Goldfinch** | `goldfinch` | $2,558,595.29 | @goldfinch_fi | [https://goldfinch.finance](https://goldfinch.finance) | 0 | `PENDING` | LEGACY_CREDIT |
| **Union Protocol** | `union-protocol` | $266,042.28 | @unionprotocol | [https://union.finance](https://union.finance) | 0 | `PENDING` | PENDING |
| **Clearpool Lending** | `clearpool-lending` | $234,066.93 | @ClearpoolFin | [https://clearpool.finance](https://clearpool.finance) | 0 | `PENDING` | PENDING |
| **Ribbon Lend** | `ribbon-lend` | $52,335.20 | @ribbonfinance | [https://ribbon.finance](https://ribbon.finance) | 0 | `PENDING` | LEGACY_DEBT |
| **dAMM Finance** | `damm-finance` | $23,074.53 | @dammfinance | [https://damm.finance](https://damm.finance) | 0 | `PENDING` | PENDING |
| **TrueFi** | `truefi` | $21,735.48 | @TrueFiDAO | [https://truefi.io](https://truefi.io) | 0 | `PENDING` | LEGACY_CREDIT |
| **Atlendis V1** | `atlendis-v1` | $16,806.57 | @AtlendisLabs | [https://atlendis.io](https://atlendis.io) | 0 | `PENDING` | DEPRECATED |
| **Atlendis V2** | `atlendis-v2` | $1,013.16 | @AtlendisLabs | [https://atlendis.io](https://atlendis.io) | 0 | `PENDING` | PENDING |
| **Avocado Fund** | `avocado-fund` | $46.97 | @_avocadofund | [—](—) | 0 | `PENDING` | INACTIVE |
| **Clawloan** | `clawloan` | $15.16 | @Clawloan | [—](—) | 0 | `PENDING` | INACTIVE |
| **Micro Credit Project** | `micro-credit-project` | $11.00 | @microcredittoken | [—](—) | 0 | `PENDING` | INACTIVE |

---

## Related Special Infrastructure

| Protocol | Slug | Category | TVL (USD) | X Handle | Role in Credit Stack |
|---|---|---|---|---|---|
| **Symbiotic** | `symbiotic` | Collateral Markets | $442,498,730.22 | @symbioticfi | Multi-asset collateral restaking engine |
| **EulerDebt** | `eulerdebt` | Secondary Debt Markets | $3,922.60 | @eulerfinance | Euler V2 secondary debt market tokenization |

---

*Provenance: Compiled deterministically from DefiLlama category endpoints and Tier 1 checkpoint data. Zero model calls.*