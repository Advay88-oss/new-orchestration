> ## Documentation Index
> Fetch the complete documentation index at: https://docs.vanna.finance/llms.txt
> Use this file to discover all available pages before exploring further.

# Margin Account

> Using margin account in the current Stellar testnet application.

Your Margin Account is a SmartAccount contract holding collateral, borrowed funds, and external strategy positions.

The Pro interface provides **Leverage Assets**, **Repay Loan**, and **Transfer Collateral** tabs, alongside balances, positions, history, and account metrics. The root page and Margin detail page draw on shared account snapshots.

<Frame caption="Earlier Margin layout showing where to find account metrics and action tabs. Values and contract addresses are historical. Click the image to zoom.">
  <img src="https://mintcdn.com/vannafinance/UHj8oBBMt2jwIvZH/images/margin/MarginOverview.png?fit=max&auto=format&n=UHj8oBBMt2jwIvZH&q=85&s=5a2343e966d1e19a8c94ccb232568c08" alt="Margin overview showing health, collateral headroom, borrowing, and action tabs" width="1645" height="849" loading="lazy" decoding="async" data-path="images/margin/MarginOverview.png" />
</Frame>

## Read the metrics

| Metric                             | Meaning                                                                   |
| ---------------------------------- | ------------------------------------------------------------------------- |
| Health Factor                      | Recognized collateral USD divided by debt USD                             |
| Borrowed value                     | Outstanding debt, including interest                                      |
| Net Available Collateral           | Nonnegative displayed equity; not a withdrawal quote                      |
| Collateral Left Before Liquidation | `max(0, collateral - 1.1 × debt)`                                         |
| Debt limit                         | Derived from collateral and threshold; not guaranteed new borrow capacity |

Health must be strictly above 1.1 for an account with debt to be healthy. A zero or placeholder P\&L figure is not proof of realized performance; the current Margin summary lacks complete cost-basis accounting.

Start with [Open Account](/guides/margin/open-account), [Deposit](/guides/margin/deposit-collateral), and [Borrow](/guides/margin/borrow).
