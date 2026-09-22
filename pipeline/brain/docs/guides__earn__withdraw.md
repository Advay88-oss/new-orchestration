> ## Documentation Index
> Fetch the complete documentation index at: https://docs.vanna.finance/llms.txt
> Use this file to discover all available pages before exploring further.

# Withdraw from Earn

> Using withdraw from earn in the current Stellar testnet application.

Redeem your lending-pool receipts to receive underlying assets at the current conversion rate.

## Steps

1. Open the Earn market where you hold receipts.
2. Select **Withdraw Liquidity** and choose the quantity to redeem.
3. Review the underlying preview, receipt quantity, and available pool liquidity.
4. Confirm and sign the transaction.
5. Check the actual underlying received and the remaining receipt balance.

<Frame caption="Earlier redemption form. A 100% request can still partially fill under the current payout caps. Click the image to zoom.">
  <img src="https://mintcdn.com/vannafinance/UHj8oBBMt2jwIvZH/images/earn/WithdrawLiquidity.png?fit=max&auto=format&n=UHj8oBBMt2jwIvZH&q=85&s=e24808104b0a89fa51c2f2491d6046fb" alt="Earn withdrawal panel selecting vXLM receipts for redemption" width="1913" height="937" loading="lazy" decoding="async" data-path="images/earn/WithdrawLiquidity.png" />
</Frame>

## Partial fills

The pool limits one redemption to the smallest of the requested value, **50% of total assets**, and available cash. It burns the receipts corresponding to the completed redemption. A larger request can succeed partially; remaining receipts are not automatically queued for another payout.

If no payout is available, the transaction fails. Additional withdrawals require another request and sufficient liquidity. Pool pause can also block redemption. Displayed total assets include loans, so that number is not the available cash balance.

See [vTokens](/learn/vtokens) and [Pool Mechanics](/learn/lending-pool-mechanics).
