> ## Documentation Index
> Fetch the complete documentation index at: https://docs.vanna.finance/llms.txt
> Use this file to discover all available pages before exploring further.

# Supply to Earn

> Using supply to earn in the current Stellar testnet application.

## Before supplying

Connect your wallet, select Pro mode, and obtain the exact token for the chosen Earn market. Retain XLM for fees and reserves.

## Steps

<Steps>
  <Step title="Choose the market">
    Open **Earn** and select XLM, BLUSDC, AqUSDC, or SoUSDC. Check that the selected market matches your wallet asset.
  </Step>

  <Step title="Enter and review the supply">
    Select **Supply Liquidity**, enter an amount, and review the pool, asset, and receipt preview.

    <Frame caption="Earlier supply form. Quoted returns, addresses, and legacy reward labels are not current protocol settings. Click the image to zoom.">
      <img src="https://mintcdn.com/vannafinance/UHj8oBBMt2jwIvZH/images/earn/SupplyLiquidity1.png?fit=max&auto=format&n=UHj8oBBMt2jwIvZH&q=85&s=9817d5ec0ff76361bfeda2e3fc9aa374" alt="Earn XLM supply form with an entered amount and receipt preview" width="1916" height="942" loading="lazy" decoding="async" data-path="images/earn/SupplyLiquidity1.png" />
    </Frame>
  </Step>

  <Step title="Confirm and check your receipts">
    Confirm and sign, wait for the transaction result, then check your vToken balance and position view.

    <Frame caption="Example receipt position after supply. The pictured balance and APY are illustrative. Click the image to zoom.">
      <img src="https://mintcdn.com/vannafinance/UHj8oBBMt2jwIvZH/images/earn/MyPositionTab.png?fit=max&auto=format&n=UHj8oBBMt2jwIvZH&q=85&s=f4794f037e237b0ed68ec556ba2d93c9" alt="Earn Current Position table showing receipt shares and underlying value" width="1021" height="815" loading="lazy" decoding="async" data-path="images/earn/MyPositionTab.png" />
    </Frame>
  </Step>
</Steps>

The deposited asset moves to the pool. The receipt quantity depends on the pool conversion rate and rounding; it is not always numerically identical to the underlying deposit. Your receipts remain in the wallet and do not automatically become margin collateral.

History can lag behind a confirmed transaction. Use its hash and refreshed balances to verify the result. Continue with [Withdraw](/guides/earn/withdraw).
