> ## Documentation Index
> Fetch the complete documentation index at: https://docs.vanna.finance/llms.txt
> Use this file to discover all available pages before exploring further.

# Risk Engine

> Current testnet implementation, behavior, authorization, and Rust signatures.

RiskEngine values collateral and debt in USD WAD and exposes borrow, withdrawal, execution, and liquidation checks.

## Health factor

`HF = collateral_usd / debt_usd`. Healthy means **strictly greater than 1.1**; a priced account with debt at or below 1.1 is liquidation eligible, subject to execution checks. `get_health_factor` returns a WAD `u128`, or `u128::MAX` for zero debt.

For a new gross borrow B, the standalone guard evaluates `(C + B) / (D + B)`. Existing borrowed proceeds already included in C are not added a second time. AccountManager/SmartAccount fast paths and net borrow credits must also be respected; this formula is not a transaction quote.

## Collateral valuation

Plain tokens use registered metadata, native decimal conversion, and canonical oracle feeds. Explicitly revoked collateral is excluded. Tracking positions use Registry `TrackingMeta`:

| Kind              | Valuation                                                            |
| ----------------- | -------------------------------------------------------------------- |
| `BlendUnderlying` | Receipt balance × Blend reserve b\_rate, converted to underlying USD |
| `LpSoroswap`      | User share of conservatively valued committed pair reserves          |
| `LpAquarius`      | User share of conservatively valued committed pool reserves          |
| `Unpriced`        | Zero                                                                 |

LP pool USD value is **2 × min(USD value of each reserve side)**, not the unrestricted sum of both sides. Freeze/revocation and missing data can remove collateral value. Borrow/withdraw snapshots may use cached Blend/LP values; liquidation reads its own snapshot and external positions. LP collateral is not categorically zero.

## Liquidation-safe reads

`liquidation_snapshot` returns `(collateral_usd_wad, debt_usd_wad, unpriceable_plain)`. AccountManager refuses liquidation when `unpriceable_plain` is true. Missing debt resolution or debt prices receive conservative maximum-value treatment. Some unavailable external collateral contributes zero. A displayed HF is therefore insufficient to guarantee liquidation execution.

AccountManager may use SmartAccount prechecks instead of calling these standalone guards. Its admin-configurable live gate also controls post-borrow RiskEngine checks.

Admin can pause guarded operations, change Registry, transfer administration in two steps, and upgrade WASM. Read deployment and liquidation configuration getters to inspect the selected contracts.

## Function signatures

These signatures are copied from the reviewed Rust implementation. `env` is supplied by Soroban and is not a transaction argument. `Result` errors and panics must be handled by the caller; simulation does not guarantee later execution. Public methods include privileged and internal-contract callbacks, not just user entrypoints.

### \_\_constructor

```rust theme={null}
pub fn __constructor(env: &Env, admin: Address, registry_contract: Address)
```

### get\_liquidation\_config

```rust theme={null}
pub fn get_liquidation_config(_env: &Env) -> (u128, u128, bool)
```

### get\_deployment\_config

```rust theme={null}
pub fn get_deployment_config(env: &Env) -> (Address, Address)
```

### is\_borrow\_allowed

```rust theme={null}
pub fn is_borrow_allowed(
        env: &Env,
        symbol: Symbol,
        borrow_amount_wad: U256,
        margin_account: Address,
    ) -> Result<bool, RiskEngineError>
```

### lp\_position\_usd\_wad

```rust theme={null}
pub fn lp_position_usd_wad(
        env: &Env,
        margin_account: Address,
        lp_symbol: Symbol,
    ) -> U256
```

### account\_usd\_totals

```rust theme={null}
pub fn account_usd_totals(
        env: &Env,
        margin_account: Address,
    ) -> Result<(U256, U256), RiskEngineError>
```

### account\_usd\_totals\_liq\_safe

```rust theme={null}
pub fn account_usd_totals_liq_safe(
        env: &Env,
        margin_account: Address,
    ) -> Result<(U256, U256), RiskEngineError>
```

### has\_unpriceable\_plain\_collateral

```rust theme={null}
pub fn has_unpriceable_plain_collateral(env: &Env, margin_account: Address) -> bool
```

### is\_deposit\_borrow\_allowed

```rust theme={null}
pub fn is_deposit_borrow_allowed(
        env: &Env,
        deposit_symbol: Symbol,
        deposit_amount_wad: U256,
        borrow_symbol: Symbol,
        borrow_amount_wad: U256,
        margin_account: Address,
    ) -> Result<bool, RiskEngineError>
```

### is\_withdraw\_allowed

```rust theme={null}
pub fn is_withdraw_allowed(
        env: &Env,
        symbol: Symbol,
        withdraw_amount_wad: U256,
        margin_account: Address,
    ) -> Result<bool, RiskEngineError>
```

### is\_account\_healthy

```rust theme={null}
pub fn is_account_healthy(
        env: &Env,
        total_account_balance_wad: U256,
        total_account_debt_wad: U256,
    ) -> Result<bool, RiskEngineError>
```

### get\_health\_factor

```rust theme={null}
pub fn get_health_factor(env: &Env, margin_account: Address) -> u128
```

### get\_health\_factor\_threshold

```rust theme={null}
pub fn get_health_factor_threshold(_env: &Env) -> u128
```

### get\_current\_total\_balance

```rust theme={null}
pub fn get_current_total_balance(
        env: &Env,
        margin_account: Address,
    ) -> Result<U256, RiskEngineError>
```

### get\_total\_balance\_liq\_safe

```rust theme={null}
pub fn get_total_balance_liq_safe(
        env: &Env,
        margin_account: Address,
    ) -> Result<U256, RiskEngineError>
```

### get\_current\_total\_borrows

```rust theme={null}
pub fn get_current_total_borrows(
        env: &Env,
        margin_account: Address,
    ) -> Result<U256, RiskEngineError>
```

### get\_total\_borrows\_liq\_safe

```rust theme={null}
pub fn get_total_borrows_liq_safe(
        env: &Env,
        margin_account: Address,
    ) -> Result<U256, RiskEngineError>
```

### debt\_usd\_wad

```rust theme={null}
pub fn debt_usd_wad(env: &Env, margin_account: Address) -> Result<U256, RiskEngineError>
```

### is\_still\_healthy\_after\_execute

```rust theme={null}
pub fn is_still_healthy_after_execute(
        env: &Env,
        margin_account: Address,
        known_debt_usd: U256,
    ) -> Result<bool, RiskEngineError>
```

### is\_currently\_healthy

```rust theme={null}
pub fn is_currently_healthy(env: &Env, margin_account: Address) -> Result<bool, RiskEngineError>
```

### liquidation\_snapshot

```rust theme={null}
pub fn liquidation_snapshot(env: &Env, margin_account: Address) -> (U256, U256, bool)
```

### is\_account\_healthy\_liq\_safe

```rust theme={null}
pub fn is_account_healthy_liq_safe(env: &Env, margin_account: Address) -> Result<bool, RiskEngineError>
```

### mul\_wad\_down

```rust theme={null}
pub fn mul_wad_down(env: &Env, a: U256, b: U256) -> U256
```

### upgrade

```rust theme={null}
pub fn upgrade(env: &Env, new_wasm_hash: BytesN<32>)
```

### set\_registry

```rust theme={null}
pub fn set_registry(env: &Env, new_registry: Address)
```

### propose\_admin

```rust theme={null}
pub fn propose_admin(env: &Env, proposed: Address)
```

### accept\_admin

```rust theme={null}
pub fn accept_admin(env: &Env)
```

### set\_paused

```rust theme={null}
pub fn set_paused(env: &Env, paused: bool)
```

### is\_paused

```rust theme={null}
pub fn is_paused(env: &Env) -> bool
```

## Source reference

* `Protocol_V1_Soroban_testnet/contracts/RiskEngineContract/src/risk_engine.rs`
