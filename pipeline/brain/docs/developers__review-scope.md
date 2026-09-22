> ## Documentation Index
> Fetch the complete documentation index at: https://docs.vanna.finance/llms.txt
> Use this file to discover all available pages before exploring further.

# Documentation Review Scope

> Source versions, coverage, and limits of this documentation refresh.

Reviewed on **2026-09-12** against the local source trees:

| Source                        | Git HEAD at review                         |
| ----------------------------- | ------------------------------------------ |
| `Protocol_V1_Soroban_testnet` | `1d333fb816454ea9d0c3614508b53d9bd0bae577` |
| `mercury-stellar-backend`     | `c68077dec50ba58e11f6748dc00fd2d547581b20` |

The checked-out file contents are the basis for behavior descriptions. Commit IDs identify the baseline; local changes, if any, also form part of the reviewed working tree.

## Contract coverage

The reference covers AccountManager, SmartAccount, Registry, RiskEngine, Oracle, RateModel, lending-pool, v-token, TrackingToken, ControllerFacade, BlendController, SoroswapController, AquariusController, both deployers, and the shared vanna-common library. Public Rust signatures are copied from the implementation rather than reconstructed from old docs.

## Application coverage

The guides cover onboarding, Freighter/optional Privy, Pro/Lite modes, Margin, Earn, Spot, Farm, Portfolio, Analytics, and Copilot. The developer section covers transaction services, account/pool snapshots, Mercury proxies and RPC history, Hubble gates, and the external Copilot service boundary.

## Main corrections

Four distinct lending markets; conservative LP collateral valuation; live debt previews and rounding directions; partial receipt redemption and utilization caps; full-collateral liquidation with external exits and allowances; settlement/close separation; Registry bootstrap/finalization and timelocks; configurable post-exec/post-borrow checks; native/WAD controller differences; multi-transaction Lite fallback; and fixture-backed analytics limitations.

## Verification limits

This is a source-based documentation update. It does not verify deployed WASM, runtime permissions/fees, external pool availability, or production services. No deployment or financial transaction was performed. Selected historical screenshots are included as visual guides with captions; their rates, addresses, and labels are not proof of current UI behavior. Outdated implementation diagrams are excluded. Earlier review reports are archival, not current implementation references.

Address values are labeled configuration snapshots. Existing page routes are retained where practical; new contract and application pages are linked in navigation.
