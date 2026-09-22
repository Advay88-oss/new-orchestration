> ## Documentation Index
> Fetch the complete documentation index at: https://docs.vanna.finance/llms.txt
> Use this file to discover all available pages before exploring further.

# Lending Pools

> Current Stellar testnet lending pools.

Liquidity providers deposit wallet assets into Vanna pools and receive vTokens. Margin accounts borrow from those pools and accrue interest. Each of the four configured markets—XLM, BLUSDC, AqUSDC, and SoUSDC—has separate liquidity, debt, and receipts.

## Cash and total assets

Available liquidity is the underlying held by the pool. Total assets add outstanding debt, including previewed interest. A pool can therefore have substantial total assets but little immediately withdrawable cash.

## Interest and borrowing

Rates respond to utilization under an admin-configurable polynomial curve. New borrows cannot push pool utilization above 95%. Borrowers owe the gross amount; an origination fee, if configured, reduces what reaches the SmartAccount.

## Withdrawals

Redemption burns receipts at their current conversion rate. A single call pays at most 50% of total assets and the available cash, so a withdrawal can partially fill. The remaining receipts continue to represent a claim on the pool. No cash available means the redemption fails.

Pools have pause controls. Pool pause stops deposit, redemption, and new borrow; repayment accounting remains available. See [Pool Mechanics](/learn/lending-pool-mechanics).
