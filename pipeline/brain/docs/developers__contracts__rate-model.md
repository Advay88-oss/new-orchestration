> ## Documentation Index
> Fetch the complete documentation index at: https://docs.vanna.finance/llms.txt
> Use this file to discover all available pages before exploring further.

# Rate Model

> Current testnet implementation, behavior, authorization, and Rust signatures.

The rate model uses a smooth utilization polynomial. It is not a two-slope kinked model.

```text theme={null}
u = borrows / (liquidity + borrows)
annual_rate = c3 × (c1×u + c1×u^32 + c2×u^64)
rate_per_second = annual_rate / 31,556,952
```

All contract values are WAD-scaled. Defaults are `c1 = 0.1`, `c2 = 0.3`, `c3 = 3.5`; these are configurable, not immutable market rates. `get_coefficients` returns current values. The admin setter rejects coefficients whose implied 100%-utilization APR exceeds **1000%**. Utilization is clamped to 100%, and inputs to the borrow-rate calculation are capped at 10^36.

The constructor accepts a Registry argument for deployment compatibility but does not persist or use it. The model's admin may change coefficients and upgrade WASM. See [Math Reference](/developers/math-reference) for integer scaling and interest rounding.

## Function signatures

These signatures are copied from the reviewed Rust implementation. `env` is supplied by Soroban and is not a transaction argument. `Result` errors and panics must be handled by the caller; simulation does not guarantee later execution. Public methods include privileged and internal-contract callbacks, not just user entrypoints.

### \_\_constructor

```rust theme={null}
pub fn __constructor(env: &Env, admin: Address, _registry_contract: Address)
```

### set\_coefficients

```rust theme={null}
pub fn set_coefficients(env: &Env, c1: u128, c2: u128, c3: u128)
```

### get\_coefficients

```rust theme={null}
pub fn get_coefficients(env: &Env) -> (u128, u128, u128)
```

### get\_admin

```rust theme={null}
pub fn get_admin(env: &Env) -> Address
```

### upgrade

```rust theme={null}
pub fn upgrade(env: &Env, new_wasm_hash: BytesN<32>)
```

### get\_borrow\_rate\_per\_sec

```rust theme={null}
pub fn get_borrow_rate_per_sec(
        env: &Env,
        liquidity_wad: U256,
        borrows_wad: U256,
    ) -> Result<U256, InterestRateError>
```

### get\_utilisation\_ratio

```rust theme={null}
pub fn get_utilisation_ratio(
        env: &Env,
        liquidity_wad: U256,
        borrows_wad: U256,
    ) -> Result<U256, InterestRateError>
```

## Source reference

* `Protocol_V1_Soroban_testnet/contracts/RateModelContract/src/rate_model.rs`
