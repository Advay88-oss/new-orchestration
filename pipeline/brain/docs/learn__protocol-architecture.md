> ## Documentation Index
> Fetch the complete documentation index at: https://docs.vanna.finance/llms.txt
> Use this file to discover all available pages before exploring further.

# Protocol Architecture

> Current Stellar testnet protocol architecture.

The protocol has core accounting contracts, per-trader custody contracts, and external-protocol controllers.

| Component                               | Role                                                                       |
| --------------------------------------- | -------------------------------------------------------------------------- |
| AccountManager                          | Owner authorization, lifecycle, collateral, borrow/repay, strategy routing |
| SmartAccount                            | Custody, address-based collateral ledger, debt and position snapshots      |
| LendingPool / vToken                    | Per-market cash, borrow shares, supplier receipts                          |
| RiskEngine / Oracle                     | USD valuation, solvency checks, feed resolution                            |
| Registry                                | Core addresses, asset metadata, controller permissions, account membership |
| Blend / Soroswap / Aquarius controllers | Approved external actions and ledger updates                               |
| TrackingToken                           | Per-symbol external receipt accounting                                     |
| Deployers                               | Core and lending-market deployment helpers                                 |

Earn deposits enter the pool directly. Margin operations enter AccountManager. External actions route through a Registry-approved controller and execute from SmartAccount custody. ControllerFacade exposes policy checks, while the current typed execution path reads Registry directly to reduce cost.

Risk is checked at several points, with an admin-configurable live check after external execution. Valuation snapshots can include caches. See the [developer architecture diagram](/developers/architecture) and [contract reference](/developers/contracts/account-manager).
