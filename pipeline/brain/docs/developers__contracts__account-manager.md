> ## Documentation Index
> Fetch the complete documentation index at: https://docs.vanna.finance/llms.txt
> Use this file to discover all available pages before exploring further.

# AccountManager

> Current testnet implementation, behavior, authorization, and Rust signatures.

AccountManager authenticates margin owners, manages account lifecycle, coordinates lending and risk checks, and routes external actions through registered controllers. Earn deposits call lending pools directly.

## Account lifecycle

`create_account` deploys or reactivates a SmartAccount for the trader and updates Registry ownership records. `close_account` requires owner authorization, no outstanding debt, and a ledger later than activation. It unwinds external positions, sweeps direct tokens to the owner, deactivates the account, and records it for reuse.

## Collateral and borrowing

Deposits, withdrawals, and borrows use WAD amounts. Token transfers use each token's native decimals. Deposits credit the amount actually transferred after conversion. Borrow proceeds remain in the SmartAccount; gross debt includes any origination fee, while credited collateral is the net receipt.

`deposit_and_borrow` combines same-asset operations. `deposit_and_borrow_cross` supports distinct collateral and debt assets. `deposit_borrow_and_deploy_blend` accepts the legacy encoded Blend Deposit action and executes the combined operation atomically. The frontend may instead use multiple transactions.

The asset cap defaults to **5**, and can be changed by the admin. Token eligibility and pool resolution use Registry configuration. Borrow and withdrawal checks require health strictly above 1.1.

## Repayment, settlement, and liquidation

`repay` takes arguments in the order **amount, symbol, SmartAccount**. It clamps repayment to debt, updates pool shares, and transfers repayment tokens from the SmartAccount through `remove_borrowed_token_balance`. It does not automatically fund repayment from the owner's wallet.

`settle_account` unwinds external positions into the account, attempts repayment of recognized debt legs, and returns whether debt is cleared. It neither sweeps remaining collateral to the wallet nor deactivates the account. Use withdrawal or `close_account` afterward.

`liquidate` requires the liquidator's authorization and allowances for each underlying debt token to AccountManager. It takes a liquidation snapshot, rejects healthy accounts and unpriceable plain collateral, repays full recognized debt from the liquidator, exits Blend directly to the liquidator, transfers held AMM LP tokens, and sweeps remaining direct collateral to the liquidator. There is no partial-repayment input or enforced debt-plus-bonus seizure cap. The 10% bonus reported by `get_liquidation_config` is not a separate payment calculation in this path. Liquidation does not deactivate the account.

## External execution

`exec` uses the typed `ExternalAction` interface. It calls Registry's batched `get_exec_gate`, checks the controller's `can_call`, executes through the SmartAccount, applies signed WAD token deltas, and enforces asset and controller TVL caps. The current path checks Registry directly; it does not require a facade round-trip.

Live post-execution and post-borrow health validation is controlled by `get_exec_live_gate` (default **true**, admin configurable). Borrowing uses SmartAccount prechecks, then conditionally calls RiskEngine on the resulting state; the combined deposit/borrow path uses the same flag. Do not promise that every external action always runs a live health check. `execute` is the legacy XDR adapter; `exec_fn` is the function-name adapter. Use the typed path for new integrations.

## Administration

Admin methods cover two-step admin transfer, WASM upgrades, SmartAccount upgrades, pause state, asset cap, collateral eligibility, tracking minter authorization, valuation-cache refreshes, and the live execution gate. Manager pause blocks borrowing, combined deposit/borrow, collateral withdrawal, external execution, and liquidation. Standalone collateral deposit, repayment, settlement, and explicit close do not check this pause flag; their other authorization/configuration checks still apply. These controls are separate from pool and RiskEngine pause flags.

## Function signatures

These signatures are copied from the reviewed Rust implementation. `env` is supplied by Soroban and is not a transaction argument. `Result` errors and panics must be handled by the caller; simulation does not guarantee later execution. Public methods include privileged and internal-contract callbacks, not just user entrypoints.

### \_\_constructor

```rust theme={null}
pub fn __constructor(env: &Env, admin: Address, registry_contract: Address)
```

### get\_liquidation\_config

```rust theme={null}
pub fn get_liquidation_config(_env: &Env) -> (u128, u128, bool, bool)
```

### get\_admin

```rust theme={null}
pub fn get_admin(env: &Env) -> Address
```

### upgrade

```rust theme={null}
pub fn upgrade(env: &Env, new_wasm_hash: BytesN<32>)
```

### upgrade\_smart\_account

```rust theme={null}
pub fn upgrade_smart_account(env: &Env, smart_account: Address, new_wasm_hash: BytesN<32>)
```

### refresh\_blend\_underlying\_cache

```rust theme={null}
pub fn refresh_blend_underlying_cache(env: &Env, smart_account: Address)
```

### refresh\_lp\_usd\_cache

```rust theme={null}
pub fn refresh_lp_usd_cache(env: &Env, smart_account: Address)
```

### refresh\_usd\_valuation\_cache

```rust theme={null}
pub fn refresh_usd_valuation_cache(env: &Env, smart_account: Address)
```

### create\_account

```rust theme={null}
pub fn create_account(
        env: &Env,
        trader_address: Address,
    ) -> Result<Address, AccountManagerError>
```

### close\_account

```rust theme={null}
pub fn close_account(
        env: &Env,
        smart_account_address: Address,
    ) -> Result<bool, AccountManagerError>
```

### deposit\_collateral\_tokens

```rust theme={null}
pub fn deposit_collateral_tokens(
        env: Env,
        smart_account: Address,
        token_symbol: Symbol,
        token_amount_wad: U256,
    ) -> Result<(), AccountManagerError>
```

### withdraw\_collateral\_balance

```rust theme={null}
pub fn withdraw_collateral_balance(
        env: Env,
        smart_account: Address,
        token_symbol: Symbol,
        token_amount_wad: U256,
    ) -> Result<(), AccountManagerError>
```

### borrow

```rust theme={null}
pub fn borrow(
        env: &Env,
        smart_account: Address,
        borrow_amount_wad: U256,
        token_symbol: Symbol,
    ) -> Result<(), AccountManagerError>
```

### deposit\_and\_borrow

```rust theme={null}
pub fn deposit_and_borrow(
        env: Env,
        smart_account: Address,
        deposit_amount_wad: U256,
        borrow_amount_wad: U256,
        token_symbol: Symbol,
    ) -> Result<(), AccountManagerError>
```

### deposit\_and\_borrow\_cross

```rust theme={null}
pub fn deposit_and_borrow_cross(
        env: Env,
        smart_account: Address,
        deposit_amount_wad: U256,
        deposit_token_symbol: Symbol,
        borrow_amount_wad: U256,
        borrow_token_symbol: Symbol,
    ) -> Result<(), AccountManagerError>
```

### deposit\_borrow\_and\_deploy\_blend

```rust theme={null}
pub fn deposit_borrow_and_deploy_blend(
        env: Env,
        smart_account: Address,
        deposit_amount_wad: U256,
        borrow_amount_wad: U256,
        token_symbol: Symbol,
        blend_call_bytes: Bytes,
    ) -> Result<(), AccountManagerError>
```

### repay

```rust theme={null}
pub fn repay(
        env: Env,
        repay_amount_wad: U256,
        token_symbol: Symbol,
        smart_account: Address,
    ) -> Result<(), AccountManagerError>
```

### liquidate

```rust theme={null}
pub fn liquidate(
        env: Env,
        liquidator: Address,
        smart_account: Address,
    ) -> Result<(), AccountManagerError>
```

### settle\_account

```rust theme={null}
pub fn settle_account(env: Env, smart_account: Address) -> Result<bool, AccountManagerError>
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

### set\_max\_asset\_cap

```rust theme={null}
pub fn set_max_asset_cap(env: &Env, cap: U256)
```

### get\_max\_asset\_cap

```rust theme={null}
pub fn get_max_asset_cap(env: &Env) -> U256
```

### get\_iscollateral\_allowed

```rust theme={null}
pub fn get_iscollateral_allowed(env: &Env, token_symbol: Symbol) -> bool
```

### set\_iscollateral\_allowed

```rust theme={null}
pub fn set_iscollateral_allowed(env: &Env, token_symbol: Symbol, allowed: bool)
```

### generate\_salt

```rust theme={null}
pub fn generate_salt(
        env: &Env,
        trader_address: Address,
        account_manager: Address,
        smart_account_num: u32,
    ) -> BytesN<32>
```

### get\_inactive\_accounts

```rust theme={null}
pub fn get_inactive_accounts(env: &Env, trader_address: Address) -> Vec<Address>
```

### exec

```rust theme={null}
pub fn exec(
        env: &Env,
        smart_account: Address,
        target: Address,
        action: ExternalAction,
        tokens: Vec<Address>,
        amounts_wad: Vec<u128>,
        min_out: u128,
    )
```

### set\_exec\_live\_gate

```rust theme={null}
pub fn set_exec_live_gate(env: &Env, enabled: bool)
```

### get\_exec\_live\_gate

```rust theme={null}
pub fn get_exec_live_gate(env: &Env) -> bool
```

### authorize\_tracking\_minter

```rust theme={null}
pub fn authorize_tracking_minter(env: &Env, minter: Address, authorized: bool)
```

### execute

```rust theme={null}
pub fn execute(env_x: &Env, smart_account: Address, extern_proto_call_bytes: Bytes)
```

### exec\_fn

```rust theme={null}
pub fn exec_fn(
        env: &Env,
        smart_account: Address,
        target: Address,
        func: Symbol,
        args: Vec<Val>,
        auth_entries: Vec<InvokerContractAuthEntry>,
        tokens: Vec<Address>,
    )
```

## Source reference

* `Protocol_V1_Soroban_testnet/contracts/AccountManagerContract/src/account_manager.rs`
