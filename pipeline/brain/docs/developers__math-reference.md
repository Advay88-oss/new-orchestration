> ## Documentation Index
> Fetch the complete documentation index at: https://docs.vanna.finance/llms.txt
> Use this file to discover all available pages before exploring further.

# Math Reference

> Exact scaling, debt rounding, share conversion, health, and collateral valuation.

## WAD arithmetic

`WAD = 10^18`. A WAD integer unit is 10^-18 tokens or ratio units, not one whole token. Plain token and receipt transfers use their own native decimals.

```text theme={null}
mul_wad_down(a,b) = floor(a*b/WAD)
mul_wad_up(a,b) = ceil(a*b/WAD)
native_to_wad(n,d) = floor(n*WAD/10^d)
wad_to_native(w,d) = floor(w*10^d/WAD)
```

The frontend's configured SAC amounts commonly use 7 decimals, including USDC test variants. Do not import an EVM USDC 6-decimal assumption. Read each asset and receipt's `decimals()`.

## Interest rate model

In real-number notation, with integer operations rescaled to WAD:

```text theme={null}
u = min(1, borrows / (liquidity + borrows))
annual_rate = c3 * (u*c1 + u^32*c1 + u^64*c2)
rate_per_second = annual_rate / 31,556,952
```

Empty-pool utilization is zero. Default coefficients are 0.1, 0.3, and 3.5. Admin can change them subject to `c3*(2*c1+c2) <= 10` (1000% APR). Rates shown as APR are annualized rates, not guaranteed realized APY.

## Interest accrual

```text theme={null}
factor_wad = elapsed_seconds * rate_per_second_wad
preview_borrows = stored_borrows + floor(stored_borrows*factor_wad/WAD)
persisted_borrows = stored_borrows + ceil(stored_borrows*factor_wad/WAD)
```

`get_borrows` returns the preview. `update_state` persists accrual and advances time; it does not accrue again if the current timestamp is no later than the last update. `get_borrow_balance` converts shares using preview borrows, so user debt includes pending interest.

## Borrow share accounting

```text theme={null}
new_shares = ceil(gross_borrow * total_shares / current_borrows)
repay_shares = floor(repay_amount * total_shares / current_borrows)
user_debt = floor(user_shares * current_borrows / total_shares)
```

When no total shares exist, conversion is 1:1. Repayment has explicit dust and clamping rules: a nonzero repayment rounding to zero shares becomes one share, and reductions are bounded by user/pool shares and debt. A UI dust threshold is not global on-chain debt forgiveness.

### Origination fee

```text theme={null}
fee = floor(gross_borrow * fee_rate_wad / WAD)
net_credit = gross_borrow - fee
```

Debt is the gross amount, and native transfers split it between treasury and borrower. The frontend documents a zero-fee configuration and applies a 0.9999 spend buffer, floored to 7 decimals. Verify `get_origination_fee` for the actual deployment.

## vToken exchange rate

Let A be liquidity plus preview borrows and S the receipt supply converted to WAD. The virtual offset v is **1**, in WAD integer units.

```text theme={null}
minted_shares_wad = floor(deposit_wad * (S+v) / (A+v))
redeemed_assets_wad = floor(receipts_wad * (A+v) / (S+v))
```

First-deposit execution instead starts 1:1 and subtracts 1,000 WAD share units before minting the user's receipts. Mint/burn then convert to the receipt's native decimals; this small accounting constant must not be described as 1,000 whole tokens.

Redemption payout is capped at `min(requested_value, floor(A/2), available_liquidity)`. For partial fills the burn amount is recomputed from the payout. Borrow execution separately enforces post-borrow utilization at or below 95%.

## Health factor

```text theme={null}
HF_wad = floor(collateral_usd_wad * WAD / debt_usd_wad)
healthy = HF_wad > 1.1 * WAD
borrow_guard = (C+B)/(D+B) > 1.1
withdraw_guard = (C-W)/D > 1.1
```

C includes accounted borrowed proceeds and recognized external positions; do not add existing debt into C again. Zero debt is healthy. Oracle and configuration failures can reject operations independently of the ratio. Post-exec and post-borrow live health checks depend on the manager's admin-configurable execution gate.

The frontend derives equity as `max(0, C-D)`, liquidation collateral headroom as `max(0, C-1.1*D)`, and debt limit as `C/1.1`. Equity and displayed debt limit are not spendable-token or new-borrow guarantees. Frontend dust handling may differ from exact contract values.

## Blend b-token valuation

```text theme={null}
underlying_native = floor(b_tokens_native * b_rate / 10^12)
underlying_wad = native_to_wad(underlying_native, underlying_decimals)
USD_wad = floor(underlying_wad * oracle_price_wad / WAD)
```

## LP valuation

For both registered Soroswap and Aquarius LP kinds:

```text theme={null}
side_a_usd = floor(reserve_a_wad * price_a_wad / WAD)
side_b_usd = floor(reserve_b_wad * price_b_wad / WAD)
conservative_pool_usd = 2 * min(side_a_usd, side_b_usd)
position_usd = floor(user_lp_native * conservative_pool_usd / total_lp_native)
```

Read committed pool reserves and map token ordering correctly. Do not use raw donated balances, an uncapped reserve sum, or the older 2x-skew piecewise formula. `Unpriced`, revoked, frozen, missing, or stale-cache positions can have lower or zero recognized value.

## Oracle price conversion

For supported oracle precision d no greater than 18, `price_wad = price * (10^18 / 10^d)`. The service prefers an available fresh five-record TWAP, then fresh spot, then a bounded admin fallback. Upstream freshness is 600 seconds; fallback lifetime is 86,400 seconds; the production memo window is 30 seconds.

## Storage TTL

Shared constants are 6,307,200 and 63,072,000 ledgers for refresh threshold and extension target. These are code-requested TTL values, not guarantees that every entry lives for a calendar year or ten years. Storage class, reads/writes, and network limits determine actual lifetime.

## Source reference

* `Protocol_V1_Soroban_testnet/contracts/lending-pool/src/pool.rs`
* `Protocol_V1_Soroban_testnet/contracts/RiskEngineContract/src/risk_engine.rs`
* `Protocol_V1_Soroban_testnet/contracts/RateModelContract/src/rate_model.rs`
* `Protocol_V1_Soroban_testnet/contracts/vanna-common/src/math.rs`
* `mercury-stellar-backend/lib/margin-health.ts`
