> ## Documentation Index
> Fetch the complete documentation index at: https://docs.vanna.finance/llms.txt
> Use this file to discover all available pages before exploring further.

# Frontend and Server APIs

> Current routes, wallet flows, state, and feature availability.

Despite its directory name, `mercury-stellar-backend` contains the complete Next.js frontend and its API routes.

## Screens

| Route                                                                          | Implemented behavior                                              |
| ------------------------------------------------------------------------------ | ----------------------------------------------------------------- |
| `/`                                                                            | Margin interface in Pro; Lite strategy home in Lite mode          |
| `/margin`                                                                      | Margin account detail, balances, collateral, borrowing, repayment |
| `/portfolio`                                                                   | Aggregated wallet/account/Earn/Farm portfolio views               |
| `/earn`, `/earn/[id]`                                                          | Four lending markets, supply, receipt redemption                  |
| `/trade/spot`                                                                  | Soroswap/Aquarius spot UI and wallet or margin service paths      |
| `/trade/perps`, `/trade/options`                                               | Redirect to `/trade/spot`                                         |
| `/farm`, `/farm/[id]`                                                          | Blend single-asset and AMM LP interfaces                          |
| `/analytics/overview2`                                                         | Protocol/account risk overview                                    |
| `/analytics/positions`, `/analytics/positions/[address]`                       | Position discovery and detail                                     |
| `/analytics/liquidations`                                                      | Liquidation history and candidate accounts                        |
| `/analytics/risk-explorer`                                                     | Scenario hub; individual scenarios vary in data source            |
| `/analytics/oracles`, `/analytics/alerts`                                      | Live/fixture fallback views                                       |
| `/analytics/whales`, `/analytics/stress-test`, `/analytics/positions-advanced` | Additional monitoring and stress views                            |
| `/copilot`                                                                     | Conversation, planning, approval, and execution UI                |
| `/stats`                                                                       | Separately gated Hubble/mainnet stats                             |

Pro is the default persisted application mode. Lite guards hide or redirect advanced screens such as Earn. A visible pool card is not proof of an enabled controller route: Aquarius configuration also contains an XLM/USDT pool for display, whereas configured lending markets remain the four documented assets.

## Wallets and state

Freighter is supported directly. Privy email/Google embedded-wallet login is conditional on `NEXT_PUBLIC_PRIVY_APP_ID` and provider readiness. LOBSTR and xBull do not have implemented adapters in this build.

Zustand stores hold wallet, UI mode, selections, and transaction progress. TanStack Query and ledger-driven hooks refresh data. Lite positions are reconstructed from chain through `lib/lite-positions.ts`; original leverage, opening time, and cost basis cannot always be recovered and should not be represented as exact history.

## APIs

| Route family                                                | Purpose                                       |
| ----------------------------------------------------------- | --------------------------------------------- |
| `/api/pools`                                                | Cached shared pool reads; 502 on read failure |
| `/api/account/[addr]`                                       | Cached account snapshot                       |
| `/api/mercury`, `/api/mercury/events`                       | Server-side indexed-history proxies           |
| `/api/faucet/blend`                                         | Configured Blend faucet integration           |
| `/api/copilot`, `/api/copilot/guardian`, `/api/copilot/log` | Copilot request, guard, and logging routes    |
| `/api/auth/*`                                               | Optional user login/session/logout flow       |
| `/api/analytics/*`                                          | Server-gated Hubble queries                   |

## Data limitations

Do not label every Analytics chart live. Single-asset, multi-asset crash, and leverage-concentration scenario pages import fixture datasets; oracle and alert pages have fallback/mock paths. The Margin summary currently initializes realized P\&L to zero until cost-basis accounting is wired. Derived equity is not realized profit.

## Copilot integration

`lib/copilot` includes intent routing, planning, asset readiness, plan sanitization, approval checks, wallet binding, conditional guards, write deduplication, and execution receipts. Configured MCP and signing services live outside this repository. Browser user consent is required to add a Vanna signer to a Privy wallet; the user's ownership is retained. Presence of these code paths does not prove the external services are configured or available.

## Source reference

* `mercury-stellar-backend/app`
* `mercury-stellar-backend/lib/constants.ts`
* `mercury-stellar-backend/lib/lite-positions.ts`
* `mercury-stellar-backend/lib/wallet-adapter.ts`
* `mercury-stellar-backend/lib/copilot/config.ts`
