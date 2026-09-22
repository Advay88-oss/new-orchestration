> ## Documentation Index
> Fetch the complete documentation index at: https://docs.vanna.finance/llms.txt
> Use this file to discover all available pages before exploring further.

# Transfer Collateral

> Using transfer collateral in the current Stellar testnet application.

The **Transfer Collateral** tab moves supported tokens between your wallet and SmartAccount.

## Wallet to Margin

Choose the wallet-to-margin direction, select the exact token variant, enter an amount, review the destination and available balance, and confirm/sign. This increases account-held funds without creating debt.

## Margin to Wallet

Choose the margin-to-wallet direction, select a free account-held token balance, and enter the amount. Review the post-withdrawal health preview, then confirm/sign.

A withdrawal with outstanding debt must leave the account strictly above the 1.1 health threshold. The contract also checks available balances and configuration. Recognized external-position value is not a withdrawable plain-token balance; exit Blend or remove LP liquidity first if those assets are needed.

Net Available Collateral is displayed equity, not a maximum withdrawal amount. Prices, interest, and cached valuations can change between the preview and execution.

Verify both wallet and margin balances after confirmation. See [Deposit Collateral](/guides/margin/deposit-collateral) and [Health Factor](/guides/margin/health-factor).
