> ## Documentation Index
> Fetch the complete documentation index at: https://docs.vanna.finance/llms.txt
> Use this file to discover all available pages before exploring further.

# Lending Pools

> Current testnet implementation, behavior, authorization, and Rust signatures.

One lending-pool implementation serves four configured frontend markets: XLM, Blend USDC, Aquarius USDC, and Soroswap USDC. Each deployment has its own underlying asset, liquidity, debt shares, and vToken.

## Supply and redeem

`deposit(lender, amount_wad)` authenticates the lender, accrues interest, transfers native underlying, and mints vTokens. The first deposit uses 1:1 WAD accounting and reserves 1,000 WAD share units for minimum liquidity before native vToken conversion. Later deposits use a virtual offset of **1 WAD integer unit** in both supply and assets. A zero-share accounting result is rejected.

`redeem_vtokens(lender, tokens_to_redeem_wad)` accepts **vToken quantity in WAD**, not underlying quantity or raw native receipt units. Payout is clamped to the minimum of requested value, **50% of total assets**, and available liquidity. A partial redemption burns the recomputed share amount; zero available payout fails. Read the event's `asset_amount` and remaining balance to determine what actually redeemed.

## Borrow and repay accounting

Only AccountManager may call `lend_to` and `collect_from`. `lend_to` returns `(is_first_borrow, net_amount_wad)` on success, records gross debt with upward-rounded shares, and distributes the fee to treasury and net proceeds to the SmartAccount. New borrowing cannot exceed **95% pool utilization**.

`collect_from` updates debt accounting; it does not itself pull tokens. AccountManager's regular repay path separately transfers account-held underlying, while liquidation transfers from the liquidator using an allowance. Do not call the pool accounting function as a standalone repayment flow.

`get_borrows` includes pending interest with floor rounding. `update_state` persists interest with ceiling rounding. Account debt getters use these live preview borrows, not just stored principal. See [Math Reference](/developers/math-reference).

## Pool administration

Pool pause blocks supply, redeem, and borrow, but not `collect_from`. Admin transfer is two-step. Origination fee and rate-model address are configurable. Read `get_origination_fee` rather than assuming a fixed deployment fee. The frontend's 0.9999 spend buffer is a rounding allowance, not the on-chain fee.

## Function signatures

These signatures are copied from the reviewed Rust implementation. `env` is supplied by Soroban and is not a transaction argument. `Result` errors and panics must be handled by the caller; simulation does not guarantee later execution. Public methods include privileged and internal-contract callbacks, not just user entrypoints.

### \_\_constructor

```rust theme={null}
pub fn __constructor(
        env: Env,
        admin: Address,
        asset_config: AssetConfig,
        registry_contract: Address,
        account_manager: Address,
        rate_model: Address,
        token_issuer: Address,
        treasury: Address,
        origination_fee: U256,
    )
```

### propose\_admin

```rust theme={null}
pub fn propose_admin(env: Env, proposed: Address) -> Result<(), LendingError>
```

### accept\_admin

```rust theme={null}
pub fn accept_admin(env: Env) -> Result<String, LendingError>
```

### get\_admin

```rust theme={null}
pub fn get_admin(env: &Env) -> Result<Address, LendingError>
```

### initialize\_pool

```rust theme={null}
pub fn initialize_pool(
        env: Env,
        vtoken_contract_address: Address,
    ) -> Result<String, LendingError>
```

### deposit

```rust theme={null}
pub fn deposit(env: Env, lender: Address, amount_wad: U256)
```

### redeem\_vtokens

```rust theme={null}
pub fn redeem_vtokens(env: &Env, lender: Address, tokens_to_redeem_wad: U256)
```

### lend\_to

```rust theme={null}
pub fn lend_to(
        env: &Env,
        smart_account: Address,
        amount_wad: U256,
    ) -> Result<(bool, U256), LendingError>
```

### collect\_from

```rust theme={null}
pub fn collect_from(
        env: &Env,
        amount_wad: U256,
        trader_smart_account: Address,
    ) -> Result<bool, LendingError>
```

### convert\_asset\_borrow\_shares

```rust theme={null}
pub fn convert_asset_borrow_shares(env: &Env, amount_wad: U256, round_up: bool) -> U256
```

### convert\_borrow\_shares\_asset

```rust theme={null}
pub fn convert_borrow_shares_asset(env: &Env, debt_wad: U256) -> U256
```

### update\_state

```rust theme={null}
pub fn update_state(env: &Env)
```

### set\_paused

```rust theme={null}
pub fn set_paused(env: Env, paused: bool)
```

### is\_paused

```rust theme={null}
pub fn is_paused(env: &Env) -> bool
```

### before\_deposit

```rust theme={null}
pub fn before_deposit(env: &Env)
```

### before\_withdraw

```rust theme={null}
pub fn before_withdraw(env: &Env)
```

### get\_user\_borrow\_shares

```rust theme={null}
pub fn get_user_borrow_shares(env: &Env, trader: Address) -> U256
```

### get\_borrow\_balance

```rust theme={null}
pub fn get_borrow_balance(env: &Env, trader: Address) -> U256
```

### get\_total\_borrow\_shares

```rust theme={null}
pub fn get_total_borrow_shares(env: &Env) -> U256
```

### total\_assets

```rust theme={null}
pub fn total_assets(env: &Env) -> U256
```

### get\_borrows

```rust theme={null}
pub fn get_borrows(env: &Env) -> U256
```

### get\_rate\_factor

```rust theme={null}
pub fn get_rate_factor(env: &Env) -> Result<U256, InterestRateError>
```

### get\_total\_liquidity\_in\_pool

```rust theme={null}
pub fn get_total_liquidity_in_pool(env: &Env) -> U256
```

### get\_last\_updated\_time

```rust theme={null}
pub fn get_last_updated_time(env: &Env) -> u64
```

### get\_current\_total\_vtoken\_balance

```rust theme={null}
pub fn get_current_total_vtoken_balance(env: &Env) -> U256
```

### get\_total\_vtokens\_minted

```rust theme={null}
pub fn get_total_vtokens_minted(env: &Env) -> U256
```

### get\_total\_vtokens\_burnt

```rust theme={null}
pub fn get_total_vtokens_burnt(env: &Env) -> U256
```

### get\_lenders

```rust theme={null}
pub fn get_lenders(env: Env) -> Vec<Address>
```

### is\_pool\_initialised

```rust theme={null}
pub fn is_pool_initialised(env: &Env) -> bool
```

### get\_native\_asset\_address

```rust theme={null}
pub fn get_native_asset_address(env: &Env) -> Address
```

### get\_asset\_config

```rust theme={null}
pub fn get_asset_config(env: &Env) -> AssetConfig
```

### convert\_asset\_to\_vtoken

```rust theme={null}
pub fn convert_asset_to_vtoken(env: &Env, amount_wad: U256) -> U256
```

### convert\_vtoken\_to\_asset

```rust theme={null}
pub fn convert_vtoken_to_asset(env: &Env, vtokens_to_be_burnt_wad: U256) -> U256
```

### update\_origination\_fee

```rust theme={null}
pub fn update_origination_fee(env: &Env, origination_fee: U256)
```

### update\_rate\_model

```rust theme={null}
pub fn update_rate_model(env: &Env, new_rate_model: Address)
```

### get\_origination\_fee

```rust theme={null}
pub fn get_origination_fee(env: &Env) -> U256
```

### get\_treasury

```rust theme={null}
pub fn get_treasury(env: &Env) -> Address
```

### get\_max\_utilization\_wad

```rust theme={null}
pub fn get_max_utilization_wad(_env: &Env) -> u128
```

### upgrade

```rust theme={null}
pub fn upgrade(env: &Env, new_wasm_hash: BytesN<32>)
```

## Source reference

* `Protocol_V1_Soroban_testnet/contracts/lending-pool/src/pool.rs`
