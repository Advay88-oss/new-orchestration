> ## Documentation Index
> Fetch the complete documentation index at: https://docs.vanna.finance/llms.txt
> Use this file to discover all available pages before exploring further.

# Repay a Loan

> Using repay a loan in the current Stellar testnet application.

Ordinary repayment uses tokens held **inside your SmartAccount**. It does not automatically draw missing funds from your connected wallet.

## Steps

1. Open **Repay Loan** and choose the debt asset.
2. Check the matching free margin balance and the live debt, including interest.
3. If needed, withdraw from Blend/remove LP liquidity or transfer more of the correct token into Margin first.
4. Enter the repayment amount and review the preview.
5. Confirm and sign, then check remaining debt and free collateral.

Partial repayment reduces shares and debt. Full repayment can require a small extra balance for accrued interest and rounding. The contract clamps the requested repayment to current debt and handles residual-share dust, but a UI showing a tiny amount as zero is not proof that every on-chain liability is cleared.

Repaying from collateral reduces both assets and debt; check the resulting account health rather than assuming every repayment increases the ratio in all account states.

Voluntary `settle_account` is a separate contract flow that unwinds recognized external positions and attempts debt clearance. It does not automatically close the account or refund remaining collateral to the wallet.

See [Transfer Collateral](/guides/margin/transfer-collateral) and [Liquidation](/guides/margin/liquidation).
