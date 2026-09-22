> ## Documentation Index
> Fetch the complete documentation index at: https://docs.vanna.finance/llms.txt
> Use this file to discover all available pages before exploring further.

# Earn Overview

> Using earn overview in the current Stellar testnet application.

Earn is Vanna's wallet-to-lending-pool supply interface. Deposits receive vTokens representing a claim on the selected pool's assets and borrower interest.

## Markets

| Display asset | Underlying market          |
| ------------- | -------------------------- |
| XLM           | Native Stellar asset       |
| BLUSDC        | Blend's USDC test asset    |
| AqUSDC        | Aquarius's USDC test asset |
| SoUSDC        | Soroswap's USDC test asset |

The three USDC variants have different addresses and independent lending markets. Use the matching wallet balance and receipt token.

<Frame caption="Earlier Earn market list. Rates and balances shown are historical examples. Click the image to zoom.">
  <img src="https://mintcdn.com/vannafinance/UHj8oBBMt2jwIvZH/images/earn/EarnSectionOverview.png?fit=max&auto=format&n=UHj8oBBMt2jwIvZH&q=85&s=a54c2042bf7ce1eda3b78aace4101ca4" alt="Earn market list showing XLM, BLUSDC, AqUSDC, and SoUSDC pools" width="1662" height="847" loading="lazy" decoding="async" data-path="images/earn/EarnSectionOverview.png" />
</Frame>

## Use Earn

In Pro mode, open Earn and select a pool. Its page provides supply, withdrawal, pool information, and position/history views. Supply uses wallet funds; no margin account is required. Earnings depend on actual borrower interest and utilization.

Withdrawal redeems receipts, with a per-call cap of 50% of pool total assets and available liquidity. A confirmed withdrawal may leave receipts behind. See [Supply](/guides/earn/supply) and [Withdraw](/guides/earn/withdraw).
