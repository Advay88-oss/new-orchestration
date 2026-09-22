> ## Documentation Index
> Fetch the complete documentation index at: https://docs.vanna.finance/llms.txt
> Use this file to discover all available pages before exploring further.

# Oracle System

> Current Stellar testnet oracle system.

Vanna's Oracle service supplies prices to collateral and debt valuation. It reads a configured Reflector-compatible contract and returns an integer price with its decimal scale.

## Price selection

The production service may use a 30-second memo. On a fresh lookup, it prefers an available positive five-record TWAP, then a positive spot price. The most recent upstream timestamp must be within 600 seconds. If those fail, an admin fallback can be used for up to 86,400 seconds after it was set.

The fallback is not a permanent peg or a live external feed. If no usable price remains, the lookup fails. Repeated calls do not imply new market updates every ledger.

## Position prices

Blend receipts are converted to underlying using the reserve b\_rate. AMM LP valuation uses committed reserves and a conservative smaller-side USD calculation. USDC feed aliases can value BLUSDC, AqUSDC, and SoUSDC without making those tokens interchangeable.

RiskEngine has distinct handling for operational checks and liquidation snapshots. AccountManager refuses liquidation when plain collateral cannot be priced. Read [Oracle Service](/developers/contracts/oracle) and [Risk Engine](/developers/contracts/risk-engine).
