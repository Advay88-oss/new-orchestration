> ## Documentation Index
> Fetch the complete documentation index at: https://docs.vanna.finance/llms.txt
> Use this file to discover all available pages before exploring further.

# vTokens

> Current Stellar testnet vtokens.

vTokens are the receipts issued by Vanna lending pools. Each of the four markets has a separate receipt contract. Your receipt balance measures shares; its underlying redemption value changes with pool assets and debt interest.

## How yield appears

You do not need to claim a separate reward to realize lending interest. The value represented by a receipt can grow as interest accrues. Actual redemption still depends on available pool liquidity and the per-call payout cap.

The exchange rate is approximately total assets divided by receipt supply; exact execution includes virtual-offset and native-rounding rules. Do not assume deposits always mint an equal number of whole receipts.

<Frame caption="Conceptual interest-accrual example. Higher redemption value is not guaranteed; actual payouts depend on pool assets, liquidity, and caps. Click the image to zoom.">
  <img src="https://mintcdn.com/vannafinance/UHj8oBBMt2jwIvZH/images/learn/vToken.png?fit=max&auto=format&n=UHj8oBBMt2jwIvZH&q=85&s=da733aa2e34b3d410b6dd45abe3bcfeb" alt="Diagram showing a deposit receiving vTokens, borrower interest, and receipt redemption" width="1536" height="1024" loading="lazy" decoding="async" data-path="images/learn/vToken.png" />
</Frame>

## Transfers and controls

Receipts support holder and allowance-based transfers, subject to authorization/freeze controls. Pool-controlled mint/burn and configurable maximum supply are part of the implementation. A receipt's existence does not imply acceptance as collateral by another protocol.

Earn receipts in your wallet are separate from margin collateral and external Blend/LP tracking positions. See [Supply](/guides/earn/supply), [Withdraw](/guides/earn/withdraw), and [vToken Reference](/developers/contracts/vtokens).
