> ## Documentation Index
> Fetch the complete documentation index at: https://docs.vanna.finance/llms.txt
> Use this file to discover all available pages before exploring further.

# Health Factor

> Current Stellar testnet health factor.

Health factor compares recognized collateral value with debt value:

```text theme={null}
Health factor = collateral USD / debt USD
```

A priced account with debt must be **strictly above 1.1** to be healthy. At or below 1.1 it is a liquidation candidate. Zero debt is healthy; the contract uses a maximum-integer sentinel for an unbounded ratio.

## What is collateral?

Direct token balances use oracle prices. Blend supply is valued using its b-token exchange rate and underlying price. Registered Soroswap and Aquarius LPs can contribute a conservative value based on the smaller USD-valued reserve side. Explicitly unpriced, frozen, revoked, or unavailable positions can contribute zero. Cached values on some paths can differ from current external position value.

## Debt and new borrowing

Debt reads include pending pool interest. Existing borrowed proceeds are already part of account assets when held or deployed; do not count the same debt twice as collateral. A standalone new-borrow check compares `(C+B)/(D+B)` with 1.1. Withdrawal compares the reduced collateral to existing debt. Net credits, fees, permissions, and pool limits can further constrain actual borrowing.

## Displayed account metrics

Equity is collateral minus debt. The UI labels a nonnegative equity value as Net Available Collateral; it is not a promise that this amount can be withdrawn. Liquidation collateral headroom is `max(0, C-1.1*D)`. Market prices, interest, LP reserve changes, and oracle/configuration changes can move these figures.

There is no universal guaranteed maximum leverage or time to liquidation. Read [Liquidation](/learn/liquidation) and [Math Reference](/developers/math-reference).
