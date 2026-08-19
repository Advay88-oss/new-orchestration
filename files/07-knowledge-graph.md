# 07 — Knowledge Graph

> Machine-readable entity and relationship map. Designed for retrieval and reasoning: an agent asked "what values a Blend position?" or "who are Vanna's investors?" should resolve it from this file alone.

---

## 1. Node types

`Organization` · `Product` · `Surface` · `Contract` · `Concept` · `Metric` · `Strategy` · `Persona` · `Chain` · `Protocol` · `Standard` · `Person` · `Competitor` · `Channel` · `Asset` · `Claim`

---

## 2. Entities

### Organizations
```yaml
- id: vanna
  type: Organization
  name: Vanna Protocol / Vanna Finance
  category: Composable undercollateralized credit infrastructure for DeFi
  status: pre-mainnet (Stellar Testnet live)
  domains: [vanna.finance, docs.vanna.finance, test-stellar.vanna.finance, app.vanna.finance, mcp.vanna.finance]
  github: github.com/vannafinance   # 4 public repos, website only
  x: "@vannaprotocol"               # ~348 followers, ~76 posts
  discord: discord.gg/vanna
  funding_raised_usd: 350000+
  founded_signal: X account created Sept 2022

- id: zonymous_labs
  type: Organization
  relation_to_vanna: affiliated build studio / company entity
  evidence: "Zonymous" repo in Vanna GitHub org; internal calendar context

- id: pivot_ventures
  type: Organization
  role: Investor
- id: draper_university
  type: Organization
  role: Investor / accelerator
  note: runs Stellar × Draper University Founder Residency
- id: gitcoin
  type: Organization
  role: Investor / grants
- id: stellar_development_foundation
  type: Organization
  aliases: [SDF]
  role: Ecosystem backer; Premier member of x402 Foundation
- id: delphi
  type: Organization
  role: Target investor/research firm (pitch recipient)
  thesis_alignment: [trust infrastructure, agentic finance, real revenue, durable data moats]
```

### Chains
```yaml
- id: stellar
  type: Chain
  smart_contract_platform: Soroban
  role: PRIMARY — Vanna's live deployment (Testnet)
  agentic_status: x402 AND MPP both live on mainnet
- id: base
  type: Chain
  role: Roadmap / referenced in developer docs
- id: arbitrum
  type: Chain
  role: Roadmap (footer)
- id: optimism
  type: Chain
  role: Legacy deployment (EVM era) + roadmap; referenced "via Derive"
```

### Product surfaces
```yaml
- id: earn
  type: Surface
  audience: liquidity_providers
  function: supply XLM/USDC → receive vTokens → earn borrower interest
- id: margin
  type: Surface
  audience: traders
  function: open margin account, deposit collateral, borrow up to 10x, repay, monitor HF
- id: trade
  type: Surface
  function: spot swap using borrowed margin (via Soroswap)
- id: farm
  type: Surface
  function: deploy margin assets into external yield (single-asset Blend pools, AMM LP pools)
  modes: [Lite Mode (one-click leveraged yield, single transaction), Pro Mode (full control)]
- id: analytics
  type: Surface
  function: protocol risk dashboard — positions, HF distribution, leverage analytics, borrow rates, liquidations, Risk Explorer stress simulations
- id: mcp_server
  type: Surface
  endpoint: mcp.vanna.finance
  audience: agents
  built_on: FastMCP
  auth: WorkOS AuthKit OAuth (DCR-compatible)
  custody: zero — separate Sign Service is the only signer
  internal_tool_count: 43   # DO NOT PUBLISH unconfirmed
- id: cli
  type: Surface
  audience: developers / power users
  example: "vanna open-position --strategy dn-carry --collateral 1000usdc --floor 1.40"
- id: sdk
  type: Surface
  package: "@vanna/sdk"
  language: TypeScript
  wallet: Freighter
- id: copilot
  type: Surface
  function: natural language intent → compiled guarded position → user approval
- id: risk_guardian
  type: Surface
  function: 24/7 HF monitoring + policy-bounded defensive actions
  actions: [alert, add collateral, repay debt, reduce leverage, hedge exposure, partial close]
  design_principle: policy-based, NOT autonomous black-box
- id: agent_score
  type: Surface
  status: DESIGNED / MOCKED — not live
  scale: "0–850"
  access: x402 — GET /agent-score/{address}
```

### Contracts (14, Soroban)
```yaml
- id: account_manager
  group: Entry
  role: single entry point for all margin operations
  functions: [create_account, borrow, repay, deposit_collateral_tokens, withdraw_collateral_balance, liquidate, close_account, settle_account, execute]
  testnet_address: CAK2IJIO2SKZWUODY4G7ZRIUUIIMJUUAIXE3I5YTQ5QYNSS2RYJ3P4CV
- id: lending_pool_xlm
  group: Entry
  testnet_address: CBA4E4ZMXUKCDTNT7LDKSO3LGNGKHRCE4GUVPSRCAKU3TKAONUY7SVOB
- id: lending_pool_usdc
  group: Entry
  testnet_address: CABLEI2ZPCWLO2FQRHJJYR7JW75BCCPN2ZIV5BX7CHPXZT4CZVTGUOBU
- id: smart_account
  group: Per-User State
  cardinality: one deployed contract per user, own storage
  property: RISK ISOLATION — a bug in one account cannot affect another
  deployed_by: deployer_contract (deterministic salt); closed accounts recycled
  template_hash: CDD7DEIRLFP36WCU7IHH3ACGBXM7QW3IBTYTRYXM3PV2NFGOKZI3XFWL
- id: risk_engine
  group: Risk
  property: STATELESS
  guards: [is_borrow_allowed, is_withdraw_allowed, is_account_healthy]
  testnet_address: CBL7RCG5H4VIZCNF7BRM2FQFXK7N5KRQKW7ZVEQZJKNXHA6FEU4OXK5I
- id: rate_model
  group: Risk
  curve: smooth polynomial, NO kink
  testnet_address: CCJAUPCU6EIFQK6GTAAYLW3Y4YETJAAUPAGBPFGQ2OUJPSW3WWHUCL2Z
- id: registry
  group: Infrastructure
  role: on-chain address book; every contract resolves peers at runtime
  property: enables safe upgrades — update registry entry, not business logic
  testnet_address: CC35XWCH7SCQROTNW7PA6HZKP4JMNSVV2K7CX3HY2PSI2MI2ZQQH73ID
- id: oracle
  group: Infrastructure
  implementation: thin passthrough to Reflector
  interface: get_price_latest(symbol) -> (price u128, decimals u32)
  cadence: ~5 minutes
  testnet_address: CB72D6SOUHUTCESXYOQOBMP6MRSH47NBYIBH73BBRH3ZRT53LPTB6R7V
- id: tracking_token
  group: Infrastructure
  role: tracks synthetic external position balances so RiskEngine can value them
  symbols: [BLEND_XLM, BLEND_USDC, AQ_XLM_USDC, SS_XLM_USDC]
  testnet_address: CA24GDWO63ZXNMW5FLWF2KMZ5DCF3DO7J3RYABFICDIDHH4A342RD2TR
- id: vxlm
  group: Infrastructure
  testnet_address: CCQAAPNBYF6I7PRM2NZ4NRDYZUVJJANMX3RZ4ZLMQH6Z5WAUL2MHU2RZ
- id: vusdc
  group: Infrastructure
  testnet_address: CDAJHQEJ26EBBGV2UYSR5S5LLA6F3A7KQISLPY5JMOL77RUDBEWG3T6Y
- id: deployer_contract
  group: Deployment
- id: deployer_lpool_contract
  group: Deployment
```

Additional pools/vTokens deployed: `Aquarius USDC Lending Pool` + `vAQUSDC`, `Soroswap USDC Lending Pool` + `vSOUSDC`.

### External protocols (integrated)
```yaml
- id: blend
  type: Protocol
  name: Blend Capital
  chain: stellar
  role: external lending/yield destination; b-tokens tracked as BLEND_XLM/BLEND_USDC
  relationship: integration partner AND ecosystem competitor (frenemy)
- id: aquarius
  type: Protocol
  chain: stellar
  role: AMM liquidity + LP positions
  pools: [XLM/USDC, XLM/AQUA, XLM/USDT]
- id: soroswap
  type: Protocol
  chain: stellar
  role: DEX spot swaps from margin accounts
- id: reflector
  type: Protocol
  role: price oracle
- id: privy
  type: Protocol
  role: wallet / embedded signing layer (frontend)
  caveat: Stellar support is EOA / raw Ed25519 only — NOT smart-contract-wallet tier
- id: freighter
  type: Protocol
  role: Stellar wallet used in SDK docs
- id: mercury
  type: Protocol
  role: Stellar event indexer for contract events
```

### Standards
```yaml
- id: x402
  type: Standard
  origin: Coinbase Developer Platform; stewarded by x402 Foundation (Linux Foundation)
  mechanism_on_stellar: Soroban authorization entries (signed auth entries, not pre-signed txs)
  live_chains: [base, solana, stellar, arbitrum, polygon, ethereum]
  vanna_relation: planned monetization rail for the Financial Data API and Agent Score
- id: mpp
  type: Standard
  origin: Stripe + Tempo
  mechanism: sessions — pre-authorized spending limit, streamed micro-payments, bulk settlement
  status: live on Stellar mainnet; spec submitted to IETF; 100+ integrated services
- id: mcp
  type: Standard
  name: Model Context Protocol
  vanna_relation: primary agent interface — mcp.vanna.finance
```

### Core concepts
```yaml
- id: composable_credit
  definition: credit whose borrowed capital can move, redeploy and be reused across protocols while remaining under one risk framework
  properties: [portability, interoperability, programmability, reusability]
- id: unified_portfolio_margin
  definition: cross-margined account where every collateral and position across every market is marked by one oracle into one solvency ratio
  enables: [delta-neutral positions, multi-leg leverage, loss-in-one-venue-offset-by-gain-in-another]
- id: health_factor
  formula: "Σ(collateral_i × price_i) / Σ(debt_j × price_j)"
  threshold: 1.1
  storage: NEVER stored — derived on demand
  precision: WAD (1e18)
- id: self_collateralization
  definition: borrowed capital cannot leave the margin account, so the borrow guard counts it as both asset and debt — (C+B)/(D+B)
  consequence: max leverage = 10x  # from C >= 0.1B
- id: borrow_shares
  definition: debt tracked as proportional shares of pool total borrows
  tradeoff: health check uses raw shares (excludes interest since last pool interaction) because full conversion exceeds Soroban per-tx compute budget; 1.1x threshold absorbs the gap
- id: vanna_flywheel
  chain: "traders borrow 10x → utilization ↑ → lender APY ↑ → more lenders join → borrow rate ↓ → more borrowing → utilization ↑"
- id: bad_debt_mechanism
  definition: if liquidation surplus is insufficient, pool total_assets decreases, vToken exchange rate drops, shortfall distributed proportionally across LPs
- id: zero_custody
  definition: Vanna holds no keys; scoped session keys; separate Sign Service is the only signer, under spend caps
```

### Metrics
```yaml
- id: max_leverage
  value: 10x
  derivation: borrow guard (C+B)/(D+B) >= 1.1
  confidence: canonical
- id: liquidation_threshold
  value: 1.1
  confidence: canonical
- id: contract_count
  value: 14
  confidence: canonical
- id: rate_coefficients
  values: {C1: 0.1, C2: 0.3, C3: 3.5}
  confidence: canonical
- id: equilibrium_utilization
  value: "70–85%"
  confidence: canonical (docs)
- id: oracle_cadence
  value: "~5 minutes"
  confidence: canonical
- id: integrations_claimed
  value: "15+"
  confidence: marketing claim
- id: chains_claimed
  value: "6+"
  confidence: marketing claim
- id: users_claimed
  value: "1,000+"
  confidence: marketing claim
- id: email_subscribers
  value: "40,000+"
  confidence: internal
- id: reach_via_integrated_protocols
  value: "2M+"
  confidence: internal — NOT Vanna users
- id: funding_raised
  value: "$350,000+"
  confidence: internal
- id: breakeven_tvl_estimate
  value: "$100M+"
  confidence: internal modelling — DO NOT PUBLISH
```

### Strategies
```yaml
- id: cross_pool_rate_carry
  sections: [margin, farm]
  delta: none (XLM-neutral)
  risk: low-medium
  mechanism: borrow XLM from Vanna → deploy into Blend XLM pool → earn rate spread
- id: earn_borrow_hedge
  sections: [earn, margin, trade]
  delta: none (XLM-neutral)
  risk: medium
  mechanism: supply XLM to Earn → borrow equal XLM → swap to USDC → legs cancel
- id: parallel_rate_carry
  sections: [margin, farm]
  delta: none
  risk: medium-high
  mechanism: one USDC collateral base → borrow XLM → split across Blend + Aquarius → two rate spreads
- id: dual_yield_stack
  sections: [earn, margin, farm]
  delta: none
  risk: low-medium
  mechanism: supply USDC to Earn + run XLM carry in Margin → two independent yield streams

# Marketing playbooks (target product, not all live on testnet)
- id: funding_rate_harvest
  category: "Δ-neutral · perps"
  headline: "≈12% funding capture"
  steps: [buy BTC spot with credit line, short same size BTC perps, collect funding + rebalance drift]
  status: MARKETING — perps not live on Stellar testnet
- id: delta_hedged_vol_carry
  category: options
  headline: "θ carry · premium capture"
  steps: [sell 30-day ETH strangle, hedge delta with perps, roll or close at 21 days out]
  status: MARKETING — options not live on Stellar testnet
- id: lp_lending_spread
  status: MARKETING
- id: compute_yield_hedged
  status: MARKETING — maps to roadmap item DePIN/GPU financing
```

### Competitors
```yaml
- id: gearbox_v3
  ring: 1 (direct)
  status: ACTIVE — the surviving benchmark
  tvl: "$300M+"
  max_leverage: "up to 10x"
  has_sdk: true
  hacks: 0
  internal_score: 59/70
  positioning_rule: "never claim superiority — claim different job to be done (derivatives & hedging)"
- id: prime_protocol
  ring: 4 (graveyard)
  status: DEAD
  peak_tvl: "$13M"
  failure_mode: adoption
  root_cause: cross-chain fragmentation, wrong ecosystem, no integrations, founder attrition, underfunded
- id: primex_v1
  ring: 4 (graveyard)
  status: pivoted to V2
  peak_tvl: "~$3M"
  failure_mode: product-market fit
  root_cause: spot-margin-only credit (non-composable), missed perps, long beta, oracle limits, no SDK
- id: deltaprime
  ring: 4 (graveyard)
  status: severely diminished
  peak_tvl: "$42.9M"
  failure_mode: security
  root_cause: "$10.8M lost in two hacks in two months; single EOA admin; insufficient audits; 828 contracts"
- id: hyperliquid
  ring: 2 (substitute)
  note: "the real competitor for most traders — isolated margin, dominant perp DEX"
- id: aave
  ring: 2 (substitute)
  pole: "credit that moves but never exceeds collateral"
- id: morpho
  ring: 2 (substitute)
- id: blend_capital
  ring: 2 (substitute) AND integration partner
  note: frenemy — same chain
- id: base_mcp
  ring: 3 (agentic stack)
  note: "nearest analogue to Vanna's agent wedge — watch for credit features"
```

### Personas
```yaml
- id: multi_screen_trader        # P1 — primary near-term ICP
- id: burned_yield_farmer        # P2 — highest volume
- id: agent_builder             # P3 — highest strategic value, lowest competition
- id: defi_product_team         # P4 — B2B
- id: institutional_desk        # P5 — NOT near-term; nurture only
- id: passive_lp                # P6 — supply side of flywheel, currently under-served
```

---

## 3. Relationships

```
# Ownership / structure
vanna                 --BUILT_ON-->            stellar (Soroban)
vanna                 --ROADMAP_CHAIN-->       base, arbitrum, optimism
vanna                 --AFFILIATED_WITH-->     zonymous_labs
vanna                 --FUNDED_BY-->           pivot_ventures, draper_university, gitcoin
vanna                 --ECOSYSTEM_BACKED_BY--> stellar_development_foundation, optimism, base
vanna                 --PITCHING-->            delphi

# Product composition
vanna                 --EXPOSES-->             earn, margin, trade, farm, analytics
vanna                 --EXPOSES-->             mcp_server, cli, sdk   # "three front doors, same rails"
mcp_server            --CONVERGES_ON-->        account_manager
cli                   --CONVERGES_ON-->        account_manager
sdk                   --CONVERGES_ON-->        account_manager
copilot               --COMPILES_TO-->         guarded position (requires user approval)
risk_guardian         --MONITORS-->            health_factor
agent_score           --DERIVED_FROM-->        on-chain behaviour of margin accounts
agent_score           --SERVED_OVER-->         x402

# Contract call graph
user                  --CALLS-->               account_manager, lending_pool_xlm, lending_pool_usdc
account_manager       --GATES_VIA-->           risk_engine
account_manager       --ISSUES_DEBT_VIA-->     lending_pool_xlm, lending_pool_usdc   # lend_to / collect_from
account_manager       --MUTATES-->             smart_account
account_manager       --MINTS-->               tracking_token
smart_account         --ROUTES_TO-->           blend, aquarius, soroswap
smart_account         --REJECTS-->             any caller that is not its registered account_manager
risk_engine           --READS-->               smart_account, lending_pools, tracking_token
risk_engine           --PRICES_VIA-->          oracle
oracle                --PASSES_THROUGH_TO-->   reflector
rate_model            --CALLED_BY-->           lending_pools (during update_state)
all_contracts         --RESOLVE_PEERS_VIA-->   registry
lending_pools         --MINT-->                vxlm, vusdc
deployer_contract     --DEPLOYS-->             smart_account

# Economic relationships
liquidity_providers   --SUPPLY_TO-->           lending_pools
lending_pools         --LEND_TO-->             smart_account (via account_manager)
traders               --PAY_INTEREST_TO-->     liquidity_providers (via vToken exchange rate growth)
utilization           --DETERMINES-->          borrow_rate (via rate_model)
max_leverage          --DERIVES_FROM-->        self_collateralization + liquidation_threshold
bad_debt_mechanism    --DILUTES-->             vToken exchange rate

# Valuation relationships
tracking_token        --ENABLES-->             external positions counted as collateral
blend b-tokens        --CONVERTED_VIA b_rate-->underlying amount --PRICED_BY--> oracle
health_factor         --GATES-->               borrow, withdraw, liquidation

# Market relationships
x402                  --LIVE_ON-->             stellar (mainnet)
mpp                   --LIVE_ON-->             stellar (mainnet)
stellar_development_foundation --PREMIER_MEMBER_OF--> x402_foundation
agentic_stack         --MISSING-->             credit layer   # ← Vanna's core claim
vanna                 --FILLS-->               that gap

# Competitive relationships
vanna                 --BENCHMARKED_AGAINST--> gearbox_v3
vanna                 --LEARNED_FROM-->        prime_protocol, primex_v1, deltaprime
prime_protocol        --DIED_OF-->             adoption failure
primex_v1             --DIED_OF-->             pmf failure
deltaprime            --DIED_OF-->             security failure
gearbox_v3            --SURVIVED_BECAUSE-->    had an SDK → became infrastructure
blend_capital         --IS_BOTH-->             integration partner AND substitute
```

---

## 4. Causal chains worth reasoning over

**Chain A — why 10× exists**
`borrowed capital cannot leave the account` → `borrow guard counts B on both sides: (C+B)/(D+B)` → `with D=0: C ≥ 0.1B` → `B ≤ 10C` → **10× max leverage**

**Chain B — why LP yield is structurally higher**
`undercollateralized borrowing removes the utilization ceiling` → `utilization runs structurally higher than a standard money market` → `polynomial rate curve raises borrow APR with utilization` → `interest accrues into vToken exchange rate` → **higher LP yield**

**Chain C — why the threshold is 1.1 not 1.0**
`liquidation incurs slippage` + `Reflector lags ~5 min` → `zero surplus at 1.0 cannot cover either` → `10% surplus floor` → **1.1× threshold** → *side effect:* also absorbs the borrow-shares interest-accrual understatement

**Chain D — why agents need Vanna**
`agents got identity, comms, wallets, orchestration, settlement` → `all of it presupposes a funded agent` → `no layer extends credit` → `credit requires underwriting` → `underwriting requires behavioural history` → `history accumulates in margin accounts` → **Agent Score → deeper credit line → unforkable moat**

**Chain E — why the SDK is existential**
`Prime Protocol, PrimeX V1, DeltaPrime all had no SDK` → `zero third-party building` → `all remained applications` → `applications die when attention moves` → `Gearbox had an SDK → became infrastructure → survived` → **MCP + CLI + SDK is the survival requirement, not a feature**

**Chain F — the trust bottleneck (the thing blocking everything)**
`pre-mainnet` + `no published audits` + `security docs "coming soon"` + `contracts not open-source` → `institutions and businesses cannot transact` → `only developers and testnet users are addressable` → **all GTM effort must go to developer/agent-builder and education channels until mainnet + audits**
