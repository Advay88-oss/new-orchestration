> ## Documentation Index
> Fetch the complete documentation index at: https://docs.vanna.finance/llms.txt
> Use this file to discover all available pages before exploring further.

# Deposit Collateral

> Using deposit collateral in the current Stellar testnet application.

Deposit moves tokens from your connected wallet into your SmartAccount. It is separate from supplying an Earn pool.

## Steps

1. Open Margin and select **Transfer Collateral** for a deposit without borrowing.
2. Choose the wallet-to-margin direction.
3. Select the exact asset and enter the amount.
4. Review the destination account, amount, and resulting balances.
5. Confirm, sign, and wait for the transaction result.

Only configured and permitted assets can be credited. BLUSDC, AqUSDC, and SoUSDC are separate. Amounts are converted to native units, so the accounted deposit reflects the actual transferable quantity.

Use **Leverage Assets** when you intend to combine a deposit with borrowing; the standalone transfer flow adds collateral without creating debt. Account and protocol pause/configuration checks can affect availability.

After confirmation, check the margin balance rather than the wallet balance alone. See [Transfer Collateral](/guides/margin/transfer-collateral).
