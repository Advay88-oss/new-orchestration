> ## Documentation Index
> Fetch the complete documentation index at: https://docs.vanna.finance/llms.txt
> Use this file to discover all available pages before exploring further.

# SmartAccount

> Current testnet implementation, behavior, authorization, and Rust signatures.

Each margin account is a separate contract holding real tokens and accounting state for its trader. It is controlled through AccountManager and registered controller callbacks; the owner does not have unrestricted arbitrary-call access.

## Ledger and snapshots

The V2 ledger uses token contract addresses for plain assets and tracking symbols for external positions. This prevents similarly named test tokens from sharing a balance. Debt is represented by lending-pool shares; `get_borrowed_token_debt` resolves the pool and reads its debt value.

Batched getters expose collateral lists, debt lists, ledger balances, and valuation snapshots. Blend underlying and LP USD caches reduce cross-contract calls on constrained execution paths. A cached valuation is not proof of a current market quote. Manager refresh methods update these caches; liquidation uses a separate valuation path.

## Custody and callbacks

`authorize_and_call` permits registered controller execution. `manager_authorize_and_call` is the manager-controlled counterpart. `update_tokens_in` and `update_tokens_out` apply controller deltas to the collateral ledger. Swap credits may be capped at oracle input value, so a raw token balance and accounted collateral need not match.

`sync_tracking_for_target` maintains external-position membership; Blend callbacks refresh underlying estimates. `repay_borrowed_token_to_pool` transfers account-held tokens and decrements collateral by the native amount actually paid, with a minimum native unit for positive dust repayment.

## Closing and sweeping

`sweep_to` moves held direct collateral. `transfer_held_token_to` permits LP seizure during liquidation. `sweep_to_split` exists, but the current AccountManager liquidation path calls `sweep_to`, not the split helper. `close_account` on AccountManager performs external unwind and deactivation; repayment and liquidation alone do not close the account.

## Function signatures

These signatures are copied from the reviewed Rust implementation. `env` is supplied by Soroban and is not a transaction argument. `Result` errors and panics must be handled by the caller; simulation does not guarantee later execution. Public methods include privileged and internal-contract callbacks, not just user entrypoints.

### \_\_constructor

```rust theme={null}
pub fn __constructor(
        env: Env,
        account_manager: Address,
        registry_contract: Address,
        user_address: Address,
    )
```

### deactivate\_account

```rust theme={null}
pub fn deactivate_account(env: &Env) -> Result<(), SmartAccountError>
```

### activate\_account

```rust theme={null}
pub fn activate_account(env: &Env) -> Result<(), SmartAccountError>
```

### remove\_borrowed\_token\_balance

```rust theme={null}
pub fn remove_borrowed_token_balance(
        env: Env,
        token_symbol: Symbol,
        amount_wad: u128,
    ) -> Result<(), SmartAccountError>
```

### remove\_collateral\_token\_balance

```rust theme={null}
pub fn remove_collateral_token_balance(
        env: &Env,
        user_address: Address,
        token_symbol: Symbol,
        amount_wad: u128,
    ) -> Result<(), SmartAccountError>
```

### sweep\_to

```rust theme={null}
pub fn sweep_to(env: &Env, to_address: Address) -> Result<(), SmartAccountError>
```

### transfer\_held\_token\_to

```rust theme={null}
pub fn transfer_held_token_to(
        env: &Env,
        to_address: Address,
        token_address: Address,
        amount: i128,
    ) -> Result<(), SmartAccountError>
```

### sweep\_to\_split

```rust theme={null}
pub fn sweep_to_split(
        env: &Env,
        to_first: Address,
        to_second: Address,
        to_first_bps: u32,
    ) -> Result<(), SmartAccountError>
```

### has\_debt

```rust theme={null}
pub fn has_debt(env: &Env) -> bool
```

### set\_has\_debt

```rust theme={null}
pub fn set_has_debt(env: &Env, has_debt: bool)
```

### get\_all\_borrowed\_tokens

```rust theme={null}
pub fn get_all_borrowed_tokens(env: &Env) -> Vec<Symbol>
```

### get\_asset\_lists

```rust theme={null}
pub fn get_asset_lists(env: &Env) -> (Vec<Symbol>, Vec<Symbol>)
```

### get\_collateral\_ledger\_snapshot

```rust theme={null}
pub fn get_collateral_ledger_snapshot(env: &Env) -> (Vec<Symbol>, Vec<U256>)
```

### get\_debt\_snapshot

```rust theme={null}
pub fn get_debt_snapshot(env: &Env) -> (Vec<Symbol>, Vec<U256>)
```

### get\_health\_snapshot

```rust theme={null}
pub fn get_health_snapshot(
        env: &Env,
    ) -> (Vec<Symbol>, Vec<U256>, Vec<Symbol>, Vec<U256>)
```

### get\_valuation\_snapshot

```rust theme={null}
pub fn get_valuation_snapshot(
        env: &Env,
    ) -> (
        Vec<Symbol>,
        Vec<U256>,
        Vec<Symbol>,
        Vec<U256>,
        Vec<Symbol>,
        Vec<U256>,
        Vec<Symbol>,
        Vec<U256>,
    )
```

### set\_lp\_usd\_wad\_cache

```rust theme={null}
pub fn set_lp_usd_wad_cache(env: &Env, lp_symbol: Symbol, usd_wad: U256)
```

### refresh\_lp\_cache\_all

```rust theme={null}
pub fn refresh_lp_cache_all(env: &Env, lp_symbols: Vec<Symbol>, lp_usd_wads: Vec<U256>)
```

### debt\_usd\_wad\_cache

```rust theme={null}
pub fn debt_usd_wad_cache(env: &Env) -> U256
```

### refresh\_usd\_valuation\_cache

```rust theme={null}
pub fn refresh_usd_valuation_cache(env: &Env)
```

### refresh\_blend\_underlying\_wad

```rust theme={null}
pub fn refresh_blend_underlying_wad(env: &Env, tracking_symbol: Symbol)
```

### refresh\_blend\_cache\_all

```rust theme={null}
pub fn refresh_blend_cache_all(env: &Env)
```

### is\_deposit\_borrow\_precheck

```rust theme={null}
pub fn is_deposit_borrow_precheck(
        env: &Env,
        deposit_symbol: Symbol,
        deposit_amount_wad: U256,
        borrow_symbol: Symbol,
        borrow_amount_wad: U256,
        live_debt: bool,
    ) -> bool
```

### is\_borrow\_precheck

```rust theme={null}
pub fn is_borrow_precheck(env: &Env, borrow_symbol: Symbol, borrow_amount_wad: U256) -> bool
```

### refresh\_token\_directory

```rust theme={null}
pub fn refresh_token_directory(env: &Env)
```

### get\_assets

```rust theme={null}
pub fn get_assets(env: &Env) -> Vec<AssetKey>
```

### get\_collateral\_token\_addrs

```rust theme={null}
pub fn get_collateral_token_addrs(env: &Env) -> Vec<Address>
```

### get\_borrows

```rust theme={null}
pub fn get_borrows(env: &Env) -> Vec<Address>
```

### get\_collateral\_balance

```rust theme={null}
pub fn get_collateral_balance(env: &Env, token: Address) -> U256
```

### migrate\_ledger\_to\_v2

```rust theme={null}
pub fn migrate_ledger_to_v2(env: &Env) -> Result<(), SmartAccountError>
```

### authorize\_and\_call

```rust theme={null}
pub fn authorize_and_call(
        env: &Env,
        target: Address,
        func: Symbol,
        args: Vec<Val>,
        auth_entries: Vec<InvokerContractAuthEntry>,
    ) -> Val
```

### manager\_authorize\_and\_call

```rust theme={null}
pub fn manager_authorize_and_call(
        env: &Env,
        target: Address,
        func: Symbol,
        args: Vec<Val>,
        auth_entries: Vec<InvokerContractAuthEntry>,
    ) -> Val
```

### update\_tokens\_in

```rust theme={null}
pub fn update_tokens_in(
        env: &Env,
        tokens: Vec<Address>,
        amounts_wad: Vec<U256>,
        max_asset_cap_wad: U256,
    ) -> bool
```

### update\_tokens\_out

```rust theme={null}
pub fn update_tokens_out(env: &Env, tokens: Vec<Address>, amounts_wad: Vec<U256>)
```

### sync\_tracking\_for\_target

```rust theme={null}
pub fn sync_tracking_for_target(
        env: &Env,
        target: Address,
        tracking_symbol: Symbol,
        keep_tracked: bool,
    )
```

### refresh\_blend\_cache\_for\_target

```rust theme={null}
pub fn refresh_blend_cache_for_target(env: &Env, target: Address, tracking_symbol: Symbol)
```

### add\_borrowed\_token

```rust theme={null}
pub fn add_borrowed_token(env: &Env, token_symbol: Symbol) -> Result<(), SmartAccountError>
```

### record\_new\_borrow

```rust theme={null}
pub fn record_new_borrow(env: &Env, borrowed_sym: Symbol, max_asset_cap_wad: U256) -> bool
```

### remove\_borrowed\_token

```rust theme={null}
pub fn remove_borrowed_token(env: &Env, token_symbol: Symbol) -> Result<(), SmartAccountError>
```

### get\_all\_collateral\_tokens

```rust theme={null}
pub fn get_all_collateral_tokens(env: &Env) -> Vec<Symbol>
```

### add\_collateral\_token

```rust theme={null}
pub fn add_collateral_token(env: &Env, token_symbol: Symbol) -> Result<(), SmartAccountError>
```

### remove\_collateral\_token

```rust theme={null}
pub fn remove_collateral_token(env: &Env, token_symbol: Symbol) -> Result<(), SmartAccountError>
```

### get\_collateral\_token\_balance

```rust theme={null}
pub fn get_collateral_token_balance(env: &Env, token_symbol: Symbol) -> U256
```

### set\_collateral\_token\_balance

```rust theme={null}
pub fn set_collateral_token_balance(
        env: &Env,
        token_symbol: Symbol,
        balance_wad: U256,
    ) -> Result<(), SmartAccountError>
```

### credit\_borrow\_collateral

```rust theme={null}
pub fn credit_borrow_collateral(
        env: &Env,
        token_symbol: Symbol,
        received_wad: U256,
        max_asset_cap_wad: U256,
    ) -> bool
```

### credit\_deposit\_collateral

```rust theme={null}
pub fn credit_deposit_collateral(
        env: &Env,
        token_symbol: Symbol,
        actual_deposited_wad: U256,
        max_asset_cap_wad: U256,
    ) -> bool
```

### record\_borrow\_and\_credit

```rust theme={null}
pub fn record_borrow_and_credit(
        env: &Env,
        borrowed_sym: Symbol,
        received_wad: U256,
        gross_borrow_wad: U256,
        max_asset_cap_wad: U256,
    ) -> bool
```

### apply\_deposit\_borrow\_ledger

```rust theme={null}
pub fn apply_deposit_borrow_ledger(
        env: &Env,
        deposit_token: Symbol,
        deposit_wad: U256,
        borrowed_sym: Symbol,
        borrow_received_wad: U256,
        gross_borrow_wad: U256,
        max_asset_cap_wad: U256,
        include_deposit: bool,
        include_borrow: bool,
    ) -> bool
```

### sync\_tracking\_collateral

```rust theme={null}
pub fn sync_tracking_collateral(
        env: &Env,
        tracking_symbol: Symbol,
        max_asset_cap_wad: U256,
        keep_tracked: bool,
    ) -> bool
```

### get\_borrowed\_token\_debt

```rust theme={null}
pub fn get_borrowed_token_debt(
        env: &Env,
        token_symbol: Symbol,
    ) -> Result<U256, SmartAccountError>
```

### clear\_account\_state

```rust theme={null}
pub fn clear_account_state(env: &Env) -> Result<(), SmartAccountError>
```

### repay\_borrowed\_token\_to\_pool

```rust theme={null}
pub fn repay_borrowed_token_to_pool(
        env: Env,
        token_symbol: Symbol,
        amount_wad: u128,
    ) -> Result<(), SmartAccountError>
```

### is\_account\_active

```rust theme={null}
pub fn is_account_active(env: &Env) -> bool
```

### upgrade

```rust theme={null}
pub fn upgrade(env: &Env, new_wasm_hash: BytesN<32>)
```

## Source reference

* `Protocol_V1_Soroban_testnet/contracts/SmartAccountContract/src/smart_account.rs`
