> ## Documentation Index
> Fetch the complete documentation index at: https://docs.vanna.finance/llms.txt
> Use this file to discover all available pages before exploring further.

# Registry

> Current testnet implementation, behavior, authorization, and Rust signatures.

Registry stores core addresses, trader-to-account membership, token aliases, asset metadata, token permissions, controller routes, controller TVL caps, and tracking metadata.

## Discovery

Use `get_protocol_config` for batched core/token/protocol configuration; `get_registered_assets`, `get_token_address_for`, and `get_lending_pool_for_symbol` for market resolution; and `get_tracking_meta` for external-position valuation/unwind configuration. USDC price-feed aliases do not make distinct token contracts interchangeable.

Account membership is written through AccountManager-authorized `add_account`, `close_account`, and `update_account`. There is no invented `get_user_smart_account` ABI: the frontend discovers account records using Registry storage and other supported fallbacks in `MarginAccountService`.

## Governance

After `finalize_registry_config`, controller registration has a **48-hour** queue delay. Token allowlist, asset metadata, and tracking metadata changes have a **24-hour** queue delay. Before finalization, these queue methods apply configuration immediately as a bootstrap path. The queue methods accept proposed data; the corresponding apply methods consume the queued change after its deadline. Cancellation and immediate deregistration methods are available. Finalizing Registry configuration restricts subsequent changes to sensitive configuration. Admin succession uses proposal and acceptance.

`AssetMeta` includes LTV and liquidation fields, but the current RiskEngine's operative health threshold is a global 1.1. Do not infer per-asset weighted risk calculations solely from metadata fields.

`get_exec_gate` batches target-to-controller lookup, probation TVL cap, and token permission checks. AccountManager's current typed execution uses it directly.

## Function signatures

These signatures are copied from the reviewed Rust implementation. `env` is supplied by Soroban and is not a transaction argument. `Result` errors and panics must be handled by the caller; simulation does not guarantee later execution. Public methods include privileged and internal-contract callbacks, not just user entrypoints.

### \_\_constructor

```rust theme={null}
pub fn __constructor(env: Env, admin: Address)
```

### set\_lendingpool\_xlm

```rust theme={null}
pub fn set_lendingpool_xlm(
        env: &Env,
        lendingpool_xlm: Address,
    ) -> Result<(), RegistryContractError>
```

### set\_smart\_account\_hash

```rust theme={null}
pub fn set_smart_account_hash(
        env: &Env,
        smart_account_hash: BytesN<32>,
    ) -> Result<(), RegistryContractError>
```

### set\_accountmanager\_contract

```rust theme={null}
pub fn set_accountmanager_contract(
        env: &Env,
        account_manager_address: Address,
    ) -> Result<(), RegistryContractError>
```

### set\_lendingpool\_usdc

```rust theme={null}
pub fn set_lendingpool_usdc(
        env: &Env,
        lendingpool_usdc_address: Address,
    ) -> Result<(), RegistryContractError>
```

### set\_risk\_engine\_address

```rust theme={null}
pub fn set_risk_engine_address(
        env: &Env,
        risk_engine_address: Address,
    ) -> Result<(), RegistryContractError>
```

### set\_rate\_model\_address

```rust theme={null}
pub fn set_rate_model_address(
        env: &Env,
        rate_model_address: Address,
    ) -> Result<(), RegistryContractError>
```

### set\_oracle\_contract\_address

```rust theme={null}
pub fn set_oracle_contract_address(
        env: &Env,
        oracle_contract_address: Address,
    ) -> Result<(), RegistryContractError>
```

### set\_native\_xlm\_contract\_address

```rust theme={null}
pub fn set_native_xlm_contract_address(
        env: &Env,
        xlm_contract_adddress: Address,
    ) -> Result<(), RegistryContractError>
```

### set\_native\_usdc\_contract\_address

```rust theme={null}
pub fn set_native_usdc_contract_address(
        env: &Env,
        usdc_contract_address: Address,
    ) -> Result<(), RegistryContractError>
```

### set\_blend\_pool\_address

```rust theme={null}
pub fn set_blend_pool_address(
        env: &Env,
        blend_pool_address: Address,
    ) -> Result<(), RegistryContractError>
```

### set\_tracking\_token\_contract\_addr

```rust theme={null}
pub fn set_tracking_token_contract_addr(
        env: &Env,
        tracking_token_contract_addr: Address,
    ) -> Result<(), RegistryContractError>
```

### set\_aquarius\_router\_address

```rust theme={null}
pub fn set_aquarius_router_address(
        env: &Env,
        aquarius_router_address: Address,
    ) -> Result<(), RegistryContractError>
```

### set\_aquarius\_pool\_index

```rust theme={null}
pub fn set_aquarius_pool_index(
        env: &Env,
        pool_index: BytesN<32>,
    ) -> Result<(), RegistryContractError>
```

### get\_lendingpool\_xlm

```rust theme={null}
pub fn get_lendingpool_xlm(env: &Env) -> Result<Address, RegistryContractError>
```

### get\_smart\_account\_hash

```rust theme={null}
pub fn get_smart_account_hash(env: &Env) -> Result<BytesN<32>, RegistryContractError>
```

### get\_accountmanager\_contract

```rust theme={null}
pub fn get_accountmanager_contract(env: &Env) -> Result<Address, RegistryContractError>
```

### get\_lendingpool\_usdc

```rust theme={null}
pub fn get_lendingpool_usdc(env: &Env) -> Result<Address, RegistryContractError>
```

### get\_risk\_engine\_address

```rust theme={null}
pub fn get_risk_engine_address(env: &Env) -> Result<Address, RegistryContractError>
```

### get\_rate\_model\_address

```rust theme={null}
pub fn get_rate_model_address(env: &Env) -> Result<Address, RegistryContractError>
```

### get\_oracle\_contract\_address

```rust theme={null}
pub fn get_oracle_contract_address(env: &Env) -> Result<Address, RegistryContractError>
```

### get\_xlm\_contract\_address

```rust theme={null}
pub fn get_xlm_contract_address(env: &Env) -> Result<Address, RegistryContractError>
```

### get\_usdc\_contract\_address

```rust theme={null}
pub fn get_usdc_contract_address(env: &Env) -> Result<Address, RegistryContractError>
```

### get\_blend\_pool\_address

```rust theme={null}
pub fn get_blend_pool_address(env: &Env) -> Result<Address, RegistryContractError>
```

### get\_aquarius\_router\_address

```rust theme={null}
pub fn get_aquarius_router_address(env: &Env) -> Result<Address, RegistryContractError>
```

### set\_soroswap\_router\_address

```rust theme={null}
pub fn set_soroswap_router_address(
        env: &Env,
        soroswap_router_address: Address,
    ) -> Result<(), RegistryContractError>
```

### get\_soroswap\_router\_address

```rust theme={null}
pub fn get_soroswap_router_address(env: &Env) -> Result<Address, RegistryContractError>
```

### get\_aquarius\_pool\_index

```rust theme={null}
pub fn get_aquarius_pool_index(env: &Env) -> Result<BytesN<32>, RegistryContractError>
```

### has\_tracking\_token\_contract\_addr

```rust theme={null}
pub fn has_tracking_token_contract_addr(env: &Env) -> bool
```

### get\_tracking\_token\_contract\_addr

```rust theme={null}
pub fn get_tracking_token_contract_addr(env: &Env) -> Result<Address, RegistryContractError>
```

### get\_admin

```rust theme={null}
pub fn get_admin(env: &Env) -> Result<Address, RegistryContractError>
```

### propose\_admin

```rust theme={null}
pub fn propose_admin(env: &Env, proposed: Address) -> Result<(), RegistryContractError>
```

### accept\_admin

```rust theme={null}
pub fn accept_admin(env: &Env) -> Result<(), RegistryContractError>
```

### get\_proposed\_admin

```rust theme={null}
pub fn get_proposed_admin(env: &Env) -> Option<Address>
```

### get\_timelock\_durations

```rust theme={null}
pub fn get_timelock_durations(_env: &Env) -> (u64, u64)
```

### upgrade

```rust theme={null}
pub fn upgrade(env: &Env, new_wasm_hash: BytesN<32>)
```

### add\_account

```rust theme={null}
pub fn add_account(
        env: &Env,
        trader: Address,
        smart_account: Address,
    ) -> Result<bool, RegistryContractError>
```

### close\_account

```rust theme={null}
pub fn close_account(
        env: &Env,
        trader: Address,
        smart_account: Address,
    ) -> Result<bool, RegistryContractError>
```

### update\_account

```rust theme={null}
pub fn update_account(
        env: &Env,
        trader: Address,
        smart_account: Address,
    ) -> Result<bool, RegistryContractError>
```

### set\_iscollateral\_allowed

```rust theme={null}
pub fn set_iscollateral_allowed(env: &Env, token_symbol: Symbol, allowed: bool)
```

### get\_iscollateral\_allowed

```rust theme={null}
pub fn get_iscollateral_allowed(env: &Env, token_symbol: Symbol) -> bool
```

### is\_collateral\_explicitly\_revoked

```rust theme={null}
pub fn is_collateral_explicitly_revoked(env: &Env, token_symbol: Symbol) -> bool
```

### set\_controller\_facade

```rust theme={null}
pub fn set_controller_facade(env: &Env, facade: Address)
```

### get\_controller\_facade

```rust theme={null}
pub fn get_controller_facade(env: &Env) -> Address
```

### has\_controller\_facade

```rust theme={null}
pub fn has_controller_facade(env: &Env) -> bool
```

### is\_registry\_config\_finalized

```rust theme={null}
pub fn is_registry_config_finalized(env: &Env) -> bool
```

### finalize\_registry\_config

```rust theme={null}
pub fn finalize_registry_config(env: &Env)
```

### queue\_register\_controller

```rust theme={null}
pub fn queue_register_controller(
        env: &Env,
        target: Address,
        controller: Address,
        tvl_cap_usd_wad: u128,
    )
```

### register\_controller

```rust theme={null}
pub fn register_controller(env: &Env, target: Address)
```

### cancel\_register\_controller

```rust theme={null}
pub fn cancel_register_controller(env: &Env, target: Address)
```

### deregister\_controller

```rust theme={null}
pub fn deregister_controller(env: &Env, target: Address)
```

### get\_controller\_for

```rust theme={null}
pub fn get_controller_for(env: &Env, target: Address) -> Option<Address>
```

### get\_controller\_tvl\_cap

```rust theme={null}
pub fn get_controller_tvl_cap(env: &Env, controller: Address) -> Option<u128>
```

### get\_protocol\_config

```rust theme={null}
pub fn get_protocol_config(env: &Env) -> vanna_common::types::ProtocolConfig
```

### get\_revoked\_flags

```rust theme={null}
pub fn get_revoked_flags(env: &Env, symbols: Vec<Symbol>) -> Vec<bool>
```

### get\_exec\_gate

```rust theme={null}
pub fn get_exec_gate(
        env: &Env,
        target: Address,
        tokens: Vec<Address>,
    ) -> vanna_common::types::ExecGate
```

### queue\_set\_token\_allowed

```rust theme={null}
pub fn queue_set_token_allowed(env: &Env, token_addr: Address, allowed: bool)
```

### set\_token\_allowed

```rust theme={null}
pub fn set_token_allowed(env: &Env, token_addr: Address)
```

### cancel\_set\_token\_allowed

```rust theme={null}
pub fn cancel_set_token_allowed(env: &Env, token_addr: Address)
```

### deregister\_token

```rust theme={null}
pub fn deregister_token(env: &Env, token_addr: Address)
```

### is\_token\_allowed

```rust theme={null}
pub fn is_token_allowed(env: &Env, token_addr: Address) -> bool
```

### queue\_set\_asset\_meta

```rust theme={null}
pub fn queue_set_asset_meta(env: &Env, token_addr: Address, meta: AssetMeta)
```

### set\_asset\_meta

```rust theme={null}
pub fn set_asset_meta(env: &Env, token_addr: Address)
```

### cancel\_set\_asset\_meta

```rust theme={null}
pub fn cancel_set_asset_meta(env: &Env, token_addr: Address)
```

### get\_asset\_meta

```rust theme={null}
pub fn get_asset_meta(env: &Env, token_addr: Address) -> Option<AssetMeta>
```

### get\_registered\_assets

```rust theme={null}
pub fn get_registered_assets(env: &Env) -> Vec<RegisteredAsset>
```

### backfill\_asset\_list

```rust theme={null}
pub fn backfill_asset_list(env: &Env, tokens: Vec<Address>)
```

### get\_token\_address\_for

```rust theme={null}
pub fn get_token_address_for(env: &Env, symbol: Symbol) -> Option<Address>
```

### get\_price\_feed\_for

```rust theme={null}
pub fn get_price_feed_for(env: &Env, symbol: Symbol) -> Option<Symbol>
```

### register\_token\_alias

```rust theme={null}
pub fn register_token_alias(env: &Env, symbol: Symbol, address: Address)
```

### get\_lending\_pool\_for

```rust theme={null}
pub fn get_lending_pool_for(env: &Env, token_addr: Address) -> Option<Address>
```

### get\_lending\_pool\_for\_symbol

```rust theme={null}
pub fn get_lending_pool_for_symbol(env: &Env, symbol: Symbol) -> Option<Address>
```

### queue\_set\_tracking\_meta

```rust theme={null}
pub fn queue_set_tracking_meta(env: &Env, symbol: Symbol, meta: TrackingMeta)
```

### set\_tracking\_meta

```rust theme={null}
pub fn set_tracking_meta(env: &Env, symbol: Symbol)
```

### cancel\_set\_tracking\_meta

```rust theme={null}
pub fn cancel_set_tracking_meta(env: &Env, symbol: Symbol)
```

### deregister\_tracking\_meta

```rust theme={null}
pub fn deregister_tracking_meta(env: &Env, symbol: Symbol)
```

### get\_tracking\_meta

```rust theme={null}
pub fn get_tracking_meta(env: &Env, symbol: Symbol) -> Option<TrackingMeta>
```

### get\_blend\_tracking\_symbol\_for

```rust theme={null}
pub fn get_blend_tracking_symbol_for(env: &Env, token_addr: Address) -> Option<Symbol>
```

### is\_tracking\_symbol

```rust theme={null}
pub fn is_tracking_symbol(env: &Env, symbol: Symbol) -> bool
```

### get\_all\_tracking\_symbols

```rust theme={null}
pub fn get_all_tracking_symbols(env: &Env) -> Vec<Symbol>
```

## Source reference

* `Protocol_V1_Soroban_testnet/contracts/RegistryContract/src/registry.rs`
