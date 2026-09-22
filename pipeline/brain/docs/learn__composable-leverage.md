> ## Documentation Index
> Fetch the complete documentation index at: https://docs.vanna.finance/llms.txt
> Use this file to discover all available pages before exploring further.

# Composable Leverage

> Current Stellar testnet composable leverage.

A SmartAccount can deploy deposited and borrowed assets into approved external protocols while the account retains its debt to Vanna's lending pools.

Blend supply creates a receipt-backed external position. Soroswap and Aquarius liquidity provision creates an AMM LP position. Spot swaps change the tokens held by the account. Controllers mediate these actions and update recognized collateral.

## Shared account risk

All positions in an account share its health factor and debt. A single profitable Farm card does not isolate it from another position's losses. External assets need to be unwound before their underlying can fund ordinary repayment.

## Execution boundaries

Some same-asset Blend openings have an atomic contract path. Lite Mode can fall back to multiple transactions, and LP/cross-asset strategies generally involve multiple steps. Earlier confirmed actions survive a later failure.

Controller support does not establish external pool availability. The configured Aquarius gauge-enabled pool has a documented smart-contract trustline limitation. See [Farm](/guides/farm/overview), [Lite Mode](/guides/farm/leveraged-yield), and [Controllers](/developers/contracts/controller-facade).
