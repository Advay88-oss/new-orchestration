> ## Documentation Index
> Fetch the complete documentation index at: https://docs.vanna.finance/llms.txt
> Use this file to discover all available pages before exploring further.

# Health Factor

> Using health factor in the current Stellar testnet application.

Health Factor is recognized collateral value divided by debt value. For accounts with debt, **above 1.1 is healthy; at or below 1.1 is liquidation eligible subject to execution checks**.

## What changes it

Collateral/debt prices, borrow interest, deposits, withdrawals, swaps, external strategy values, and asset permissions all affect the account. Borrowed funds already held or deployed are included in collateral where recognized. LP valuation is conservative and can differ from the amount shown by a DEX.

Borrow and withdrawal checks restrict new risk. Live health checks after external actions depend on the configured execution gate, so do not assume that every action guarantees the ratio remains above the threshold. Market moves can also make a previously healthy account unhealthy.

## Interpret the display

No-debt accounts can display an infinity sentinel. UI snapshots are cached and apply display dust rules, so use exact balances and transaction simulation when acting on very small debt or tight health headroom.

The displayed collateral headroom is `max(0, collateral USD - 1.1 × debt USD)`. Net Available Collateral represents nonnegative equity; it is not the same as immediately withdrawable funds.

If you need to reduce debt, obtain the correct free repayment asset in the SmartAccount and use Repay Loan. Deposits can add collateral, while external assets may need to be unwound before repayment. See [Repay](/guides/margin/repay) and [Liquidation](/guides/margin/liquidation).
