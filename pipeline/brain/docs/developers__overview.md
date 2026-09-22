> ## Documentation Index
> Fetch the complete documentation index at: https://docs.vanna.finance/llms.txt
> Use this file to discover all available pages before exploring further.

# Developer Overview

> Integrate with the reviewed Stellar testnet contracts and application.

This reference describes the local `Protocol_V1_Soroban_testnet` and `mercury-stellar-backend` code reviewed on **2026-09-12**. It does not describe the Solana, Solidity, or older Soroban directories.

Start with [Architecture](/developers/architecture), [Configured Contracts](/developers/deployed-contracts), and [Math Reference](/developers/math-reference). The [contract reference](/developers/contracts/account-manager) includes the current Rust signatures, including privileged callbacks. Env is implicit at the transaction boundary.

## Repository map

| Directory or file                             | Responsibility                                              |
| --------------------------------------------- | ----------------------------------------------------------- |
| `Protocol_V1_Soroban_testnet/contracts`       | Core contracts, controllers, deployers, shared library      |
| `Protocol_V1_Soroban_testnet/integrated_test` | Lifecycle, controller, risk, registry, and regression tests |
| `Protocol_V1_Soroban_testnet/deploy`          | Deployment and verification scripts                         |
| `mercury-stellar-backend/app`                 | Next.js pages and server API routes                         |
| `mercury-stellar-backend/lib/*-utils.ts`      | Stellar transaction and read services                       |
| `mercury-stellar-backend/hooks`               | Query, mutation, wallet, and snapshot hooks                 |
| `mercury-stellar-backend/lib/copilot`         | Copilot planning, authentication, approval, execution       |

## Current scope

Four lending markets, per-trader SmartAccounts, Blend supply, and Soroswap/Aquarius controller integrations are implemented. External availability remains pool/configuration dependent. Perpetuals and options are not enabled in this Stellar application. Read the [frontend reference](/developers/frontend) for routes and data limitations.

The TypeScript integration is application-local service code, not a published `@vanna/sdk` package. Use [Getting Started](/developers/sdk/getting-started) and [Transaction Flow](/developers/sdk/transaction-flow).
