> ## Documentation Index
> Fetch the complete documentation index at: https://docs.vanna.finance/llms.txt
> Use this file to discover all available pages before exploring further.

# Tracking Tokens

> Current testnet implementation, behavior, authorization, and Rust signatures.

TrackingToken stores per-account, per-symbol external-position receipts. It is an accounting registry, not a freely transferable wallet token or a lending-pool vToken.

## Metadata and balances

Initialization is per symbol. The contract has admin and deployer roles, with admin-authorized minters for controller operations. `mint_by` and `burn_by` require the specified authorized minter; `mint` and `burn` use the admin path. Freeze and supply/balance checks apply as implemented by each entrypoint.

Registry metadata, not a fixed list in RiskEngine, determines what a symbol represents. Blend receipts track b-token units. AMM position accounting also consults actual LP token balances and synchronizes tracking membership; do not assume every LP operation mints synthetic receipts by the legacy `execute()` return value.

| Configured symbol | Position               |
| ----------------- | ---------------------- |
| `BLEND_XLM`       | Blend XLM supply       |
| `BLEND_USDC`      | Blend's USDC supply    |
| `AQ_XLM_USDC`     | Aquarius XLM/AqUSDC LP |
| `SS_XLM_USDC`     | Soroswap XLM/SoUSDC LP |

Blend and registered AMM LP positions can contribute collateral value. `Unpriced` metadata and frozen/revoked positions are treated differently. See [Risk Engine](/developers/contracts/risk-engine).

## Function signatures

These signatures are copied from the reviewed Rust implementation. `env` is supplied by Soroban and is not a transaction argument. `Result` errors and panics must be handled by the caller; simulation does not guarantee later execution. Public methods include privileged and internal-contract callbacks, not just user entrypoints.

### \_\_constructor

```rust theme={null}
pub fn __constructor(env: Env, admin: Address, deployer: Address)
```

### rotate\_deployer

```rust theme={null}
pub fn rotate_deployer(env: Env, new_deployer: Address)
```

### initialize

```rust theme={null}
pub fn initialize(
        env: Env,
        admin: Address,
        token_symbol: Symbol,
        decimal: u32,
        name: String,
    ) -> Result<(), TokenError>
```

### admin

```rust theme={null}
pub fn admin(env: Env) -> Address
```

### set\_admin

```rust theme={null}
pub fn set_admin(env: Env, new_admin: Address) -> Result<(), TokenError>
```

### decimals

```rust theme={null}
pub fn decimals(env: Env, token_symbol: Symbol) -> u32
```

### name

```rust theme={null}
pub fn name(env: Env, token_symbol: Symbol) -> String
```

### symbol

```rust theme={null}
pub fn symbol(env: Env, token_symbol: Symbol) -> Symbol
```

### balance

```rust theme={null}
pub fn balance(env: Env, id: Address, token_symbol: Symbol) -> i128
```

### total\_supply

```rust theme={null}
pub fn total_supply(env: Env, token_symbol: Symbol) -> i128
```

### mint

```rust theme={null}
pub fn mint(
        env: Env,
        token_symbol: Symbol,
        to: Address,
        amount: i128,
    ) -> Result<(), TokenError>
```

### set\_authorized\_minter

```rust theme={null}
pub fn set_authorized_minter(
        env: Env,
        minter: Address,
        authorized: bool,
    ) -> Result<(), TokenError>
```

### is\_authorized\_minter

```rust theme={null}
pub fn is_authorized_minter(env: Env, minter: Address) -> bool
```

### mint\_by

```rust theme={null}
pub fn mint_by(
        env: Env,
        minter: Address,
        token_symbol: Symbol,
        to: Address,
        amount: i128,
    ) -> Result<(), TokenError>
```

### burn\_by

```rust theme={null}
pub fn burn_by(
        env: Env,
        minter: Address,
        token_symbol: Symbol,
        from: Address,
        amount: i128,
    ) -> Result<(), TokenError>
```

### burn

```rust theme={null}
pub fn burn(
        env: Env,
        token_symbol: Symbol,
        from: Address,
        amount: i128,
    ) -> Result<(), TokenError>
```

### burn\_from

```rust theme={null}
pub fn burn_from(
        env: Env,
        token_symbol: Symbol,
        from: Address,
        amount: i128,
    ) -> Result<(), TokenError>
```

### set\_frozen

```rust theme={null}
pub fn set_frozen(env: Env, id: Address, freeze: bool) -> Result<(), TokenError>
```

### frozen

```rust theme={null}
pub fn frozen(env: Env, id: Address) -> bool
```

### upgrade

```rust theme={null}
pub fn upgrade(env: Env, new_wasm_hash: BytesN<32>)
```

## Source reference

* `Protocol_V1_Soroban_testnet/contracts/TrackingTokenContract/src/tracking_token.rs`
