> ## Documentation Index
> Fetch the complete documentation index at: https://docs.vanna.finance/llms.txt
> Use this file to discover all available pages before exploring further.

# Liquidation

> Current Stellar testnet liquidation.

Liquidation is a permissionless, liquidator-funded full-debt operation. AccountManager verifies the account's current valuation and rejects healthy accounts. Health at or below 1.1 is eligible subject to oracle, configuration, funding, and execution checks.

## What moves

The liquidator authorizes the operation and grants AccountManager token allowances. The manager accrues each recognized debt market and transfers repayment tokens from the liquidator to the lending pools. It exits Blend positions directly to the liquidator, transfers held AMM LP tokens to the liquidator, and sweeps remaining direct collateral.

**The current liquidation path takes all remaining collateral.** It does not cap proceeds at debt plus 10% or split excess back to the owner. A configuration getter reports a 10% bonus value, but the executable path does not use that number as a payout formula. LP tokens received by the liquidator still need an external exit to realize underlying assets.

## Account status

Liquidation does not deactivate or recycle the SmartAccount. Unknown debt symbols or residual debt require further inspection; an event alone is not proof that every liability disappeared.

## Oracle failure

If the snapshot reports unpriceable plain collateral, AccountManager withholds liquidation. Missing external-position data and debt-price failures have separate conservative handling. A low displayed health factor during a data failure does not guarantee a successful liquidation transaction.

## Voluntary settlement

Owner-authorized `settle_account` unwinds assets into the SmartAccount and attempts repayment from its balances. It returns whether debt is cleared. Remaining collateral stays in the account until withdrawn or swept by explicit `close_account`. Settlement is not an automatic wallet refund or a guaranteed debt-clearing operation.

See [Liquidation Bots](/developers/guides/liquidation-bots) for integration details.
