> ## Documentation Index
> Fetch the complete documentation index at: https://docs.vanna.finance/llms.txt
> Use this file to discover all available pages before exploring further.

# Borrow

> Using borrow in the current Stellar testnet application.

Borrowing sends assets from a Vanna lending pool into your SmartAccount and creates interest-bearing debt. The proceeds are available for permitted account actions, not automatically sent to your wallet.

## Steps

1. Open **Leverage Assets** in Margin.
2. Select collateral and the intended debt market. Check the exact USDC variant.
3. Enter deposit/borrow amounts or use the available leverage controls.
4. Review post-action health, debt, pool liquidity, and fee information.
5. Confirm the operation and complete each required transaction.
6. Check actual credited funds and debt after confirmation.

## Limits and fees

Borrowing requires permitted assets, enough collateral headroom, available pool cash, and post-borrow utilization no greater than 95%. A displayed leverage target or debt limit is not guaranteed execution.

The pool records gross debt. A configured origination fee reduces spendable proceeds. Current frontend code records a zero-fee setup and still applies a small rounding buffer before deploying borrowed funds; the selected pool's getter is authoritative for its fee.

Account health changes with interest, prices, and external-position value. At or below 1.1, a priced debt-bearing account becomes a liquidation candidate. See [Repay](/guides/margin/repay) and [Health Factor](/guides/margin/health-factor).
