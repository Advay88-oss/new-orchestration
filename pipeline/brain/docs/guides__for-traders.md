> ## Documentation Index
> Fetch the complete documentation index at: https://docs.vanna.finance/llms.txt
> Use this file to discover all available pages before exploring further.

# For Traders and Borrowers

> Using for traders and borrowers in the current Stellar testnet application.

Use a **Margin Account** to hold collateral, borrow, swap, and deploy approved strategies. Each account is a Stellar contract controlled through your wallet's authorization.

1. Create or reconnect to your margin account.
2. Deposit the correct test assets through Transfer Collateral or the deposit-and-borrow panel.
3. Review debt, health factor, pool liquidity, and the transaction preview before borrowing.
4. Use free account-held balances in Spot or Farm.
5. Unwind assets and repay debt when reducing exposure.

The account shares risk across its positions. Health factor at or below 1.1 makes a priced account with debt a liquidation candidate. Borrow availability depends on more than health, including asset permissions, available cash, the pool's 95% utilization ceiling, and execution resources.

BLUSDC, AqUSDC, and SoUSDC are different tokens. Borrowing one does not fund another protocol's USDC leg.

See [Margin](/guides/margin/overview), [Spot](/guides/trade/spot-swap), and [Farm](/guides/farm/overview).
