> ## Documentation Index
> Fetch the complete documentation index at: https://docs.vanna.finance/llms.txt
> Use this file to discover all available pages before exploring further.

# vTokens

> Current testnet implementation, behavior, authorization, and Rust signatures.

Each lending pool controls a separate receipt-token deployment. The frontend configures four receipts: vXLM, vBLEND\_USDC, vAQUARIUS\_USDC, and vSOROSWAP\_USDC. Use [configured addresses](/developers/deployed-contracts) and token metadata for exact tickers and decimals.

## Pool shares

A receipt represents a claim on pool assets, including outstanding borrow interest. The exact conversion includes a virtual offset and native decimal rounding; use pool conversion getters rather than assuming one receipt always equals one underlying token.

Pool methods take WAD quantities; token `balance`, `transfer`, `mint`, and `burn` use native `i128` quantities. Underlying and receipt decimals must each be read independently.

## Authorization and controls

Construction sets an admin; initialization supplies metadata and authenticates the configured admin. The lending pool normally controls mint/burn. Holder transfers and allowance-based transfers require their respective authorizations. Admin controls include maximum supply and account authorization/freeze state. Transfers can be blocked by freeze state; unconditional transferability is not guaranteed. Pool-directed burn is permitted for exit even when receipt receiving/transfers are frozen.

Holding vTokens does not itself add collateral to a margin account. Earn positions and margin custody are separate.

## Function signatures

These signatures are copied from the reviewed Rust implementation. `env` is supplied by Soroban and is not a transaction argument. `Result` errors and panics must be handled by the caller; simulation does not guarantee later execution. Public methods include privileged and internal-contract callbacks, not just user entrypoints.

### \_\_constructor

```rust theme={null}
pub fn __constructor(env: Env, admin: Address)
```

### initialize

```rust theme={null}
pub fn initialize(
        env: Env,
        admin: Address,
        decimal: u32,
        name: String,
        symbol: String,
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

### set\_max\_supply

```rust theme={null}
pub fn set_max_supply(env: Env, max_supply: i128) -> Result<(), TokenError>
```

### max\_supply

```rust theme={null}
pub fn max_supply(env: Env) -> Option<i128>
```

### decimals

```rust theme={null}
pub fn decimals(env: Env) -> u32
```

### name

```rust theme={null}
pub fn name(env: Env) -> String
```

### symbol

```rust theme={null}
pub fn symbol(env: Env) -> String
```

### balance

```rust theme={null}
pub fn balance(env: Env, id: Address) -> i128
```

### total\_supply

```rust theme={null}
pub fn total_supply(env: Env) -> i128
```

### allowance

```rust theme={null}
pub fn allowance(env: Env, from: Address, spender: Address) -> i128
```

### approve

```rust theme={null}
pub fn approve(
        env: Env,
        from: Address,
        spender: Address,
        amount: i128,
        expiration_ledger: u32,
    ) -> Result<(), TokenError>
```

### transfer

```rust theme={null}
pub fn transfer(env: Env, from: Address, to: Address, amount: i128) -> Result<(), TokenError>
```

### transfer\_from

```rust theme={null}
pub fn transfer_from(
        env: Env,
        spender: Address,
        from: Address,
        to: Address,
        amount: i128,
    ) -> Result<(), TokenError>
```

### mint

```rust theme={null}
pub fn mint(env: Env, to: Address, amount: i128) -> Result<(), TokenError>
```

### burn

```rust theme={null}
pub fn burn(env: Env, from: Address, amount: i128) -> Result<(), TokenError>
```

### burn\_from

```rust theme={null}
pub fn burn_from(
        env: Env,
        spender: Address,
        from: Address,
        amount: i128,
    ) -> Result<(), TokenError>
```

### set\_authorized

```rust theme={null}
pub fn set_authorized(env: Env, id: Address, authorize: bool) -> Result<(), TokenError>
```

### authorized

```rust theme={null}
pub fn authorized(env: Env, id: Address) -> bool
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
pub fn upgrade(env: &Env, new_wasm_hash: BytesN<32>)
```

## Source reference

* `Protocol_V1_Soroban_testnet/contracts/v-token/src/token.rs`
