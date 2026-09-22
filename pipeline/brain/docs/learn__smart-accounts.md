> ## Documentation Index
> Fetch the complete documentation index at: https://docs.vanna.finance/llms.txt
> Use this file to discover all available pages before exploring further.

# Margin Accounts

> Current Stellar testnet margin accounts.

A margin account is a separately deployed Stellar contract holding a trader's collateral and strategy assets. Your wallet authorizes its use through AccountManager.

## One account, multiple positions

The same account can hold direct tokens, Blend supply, and AMM LP positions while owing debt in multiple Vanna lending markets. Health is assessed across the account. Farm cards are views of positions within that shared account, not independent liquidation compartments.

Plain-token balances are keyed by token contract address. Tracking symbols identify external positions. BLUSDC, AqUSDC, and SoUSDC remain separate even though their price feeds may all resolve to USDC.

## Lifecycle

Creating an account deploys or reactivates a contract. Closing requires no debt and a later ledger than activation; the manager unwinds external assets, sweeps remaining tokens to the owner, and deactivates the account for reuse. Repayment, settlement, and liquidation do not automatically close it.

## Spendable versus valued

Collateral value includes recognized external positions, but those positions must be withdrawn or converted before their underlying is spendable. The account's risk ledger can also conservatively credit less than its raw token balance after swaps. Use the UI's current free balance and transaction simulation for actions.

See [AccountManager](/developers/contracts/account-manager) and [SmartAccount](/developers/contracts/smart-account).
