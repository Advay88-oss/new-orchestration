> ## Documentation Index
> Fetch the complete documentation index at: https://docs.vanna.finance/llms.txt
> Use this file to discover all available pages before exploring further.

# Liquidation

> Using liquidation in the current Stellar testnet application.

A priced account with debt becomes a liquidation candidate when its Health Factor is **at or below 1.1**. There is no grace-period mechanism in the contract. Any liquidator able to fund and authorize the operation can attempt it; your signature is not required.

## What happens

The liquidator repays full recognized debt using their own tokens. Blend positions are exited directly to them, AMM LP tokens are transferred to them, and remaining direct collateral is swept to them.

**The current path takes all remaining collateral.** It does not return a surplus above a fixed 10% bonus to you. Liquidation does not itself deactivate your SmartAccount. Successful execution depends on funding, allowances, oracle/configuration checks, pause state, and external positions.

## Settlement is different

Owner-authorized settlement unwinds assets into the SmartAccount and attempts repayment using its balances. It returns whether debt is cleared. Remaining assets stay in the account until you withdraw or explicitly close it. A failed or incomplete settlement is not proof that liquidation risk is gone.

## When data is unavailable

The manager refuses liquidation when its snapshot identifies unpriceable plain collateral. Other valuation failures have their own handling. A dashboard label is not a guarantee that a bot can execute at that moment.

See [Repay](/guides/margin/repay), [Health Factor](/guides/margin/health-factor), and the [technical liquidation reference](/learn/liquidation).
