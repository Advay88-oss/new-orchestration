> ## Documentation Index
> Fetch the complete documentation index at: https://docs.vanna.finance/llms.txt
> Use this file to discover all available pages before exploring further.

# Registry

> Current Stellar testnet registry.

Registry is the protocol's configurable directory. It maps core contracts, trader accounts, asset addresses and aliases, lending markets, controller routes, and external tracking metadata.

## Why token identity matters

BLUSDC, AqUSDC, and SoUSDC are different test tokens. Registry associates each address with its lending pool and price feed. A shared USD price does not permit spending one variant in another protocol's pool.

## Controller permissions

External actions require a registered controller and allowed tokens. After configuration finalization, controller registration is queued for 48 hours; asset, token, and tracking metadata updates have 24-hour queues. Before finalization, the queue methods apply immediately for bootstrap. Admin can cancel proposals and remove permissions. Finalization and admin transfer are explicit contract operations.

Metadata includes asset risk fields, but the currently enforced RiskEngine health threshold remains the global 1.1. Do not infer a different liquidation formula from metadata alone.

Use the [Registry Reference](/developers/contracts/registry) and [configured address list](/developers/deployed-contracts) for integration.
