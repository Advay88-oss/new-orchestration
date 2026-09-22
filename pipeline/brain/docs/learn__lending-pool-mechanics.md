> ## Documentation Index
> Fetch the complete documentation index at: https://docs.vanna.finance/llms.txt
> Use this file to discover all available pages before exploring further.

# Pool Mechanics

> Current Stellar testnet pool mechanics.

## Deposits and receipts

Deposits convert underlying into share receipts. Later deposits use the ratio of total assets to receipt supply with a small virtual offset. The first deposit has special initial-share accounting. Token and receipt native decimals affect the final amounts.

## Debt shares

Debt uses shares so interest can accrue pool-wide without rewriting every borrower. New debt shares round up; regular repayment shares round down, with dust handling and clamps. Account debt reads include pending interest.

## Lazy interest accrual

Read previews floor the pending interest term. Mutations persist interest with ceiling rounding and advance the timestamp. A read-only simulation does not itself commit a pool update.

## Origination fee

The fee is computed from gross borrowing and sent to treasury. Gross borrowing becomes debt; the remainder becomes account-held collateral. The frontend records a zero-fee configuration, but the fee is changeable and should be read from the selected pool.

## Redemption limits

Requested receipt value is capped by 50% of total assets and available liquidity. Partial execution burns the corresponding receipt quantity. This is not a queued withdrawal request or an automatic promise to send the remainder later.

See [exact formulas](/developers/math-reference) and [pool signatures](/developers/contracts/lending-pools).
