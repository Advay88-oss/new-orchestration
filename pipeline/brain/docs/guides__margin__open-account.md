> ## Documentation Index
> Fetch the complete documentation index at: https://docs.vanna.finance/llms.txt
> Use this file to discover all available pages before exploring further.

# Open a Margin Account

> Using open a margin account in the current Stellar testnet application.

You need a SmartAccount before holding margin collateral or deploying account-based strategies. Earn supply does not require one.

## Steps

1. Connect the wallet that will own the account.
2. Open Margin in Pro mode and use the account creation control if no account is discovered.
3. Review the displayed terms and liquidation acknowledgment.
4. Confirm and authorize the creation transaction.
5. Wait for confirmation and check the discovered SmartAccount address.

The owner wallet starts with G; the deployed SmartAccount starts with C. They hold different balances. Creation may reuse a previously closed contract. Existing accounts are rediscovered on reconnect; a missing local browser record does not mean you need to deploy another account.

An account cannot be closed in the same ledger in which it was activated. Closing later requires debt clearance and external-position unwind. Liquidation does not automatically close it.

Continue with [Deposit Collateral](/guides/margin/deposit-collateral).
