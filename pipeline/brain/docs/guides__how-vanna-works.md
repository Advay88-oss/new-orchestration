> ## Documentation Index
> Fetch the complete documentation index at: https://docs.vanna.finance/llms.txt
> Use this file to discover all available pages before exploring further.

# How Vanna Works

> Using how vanna works in the current Stellar testnet application.

Vanna has two connected sides. Liquidity providers supply assets into lending pools and receive vTokens. Margin users deposit collateral, borrow from those pools, and use approved external protocols.

## Follow the assets

An Earn deposit moves wallet assets into a Vanna lending pool. A collateral deposit moves wallet assets into your SmartAccount. A borrow moves pool assets into that account and creates debt. A Farm action moves account-held assets into Blend or an AMM position.

These balances have different purposes. Earn receipts do not automatically back your margin debt, and external Farm value is not necessarily free balance available to repay.

## Account health

Health factor compares recognized collateral with debt. Debt-bearing accounts must remain above 1.1 to be healthy. External strategies, prices, interest, and configuration affect valuation. Liquidation repays recognized debt from a liquidator and transfers remaining collateral to that liquidator.

## Current product scope

The Stellar build includes Earn, Margin, Spot, Farm, Portfolio, Analytics, and Copilot, with Pro/Lite modes. Spot is the supported trading surface; perps/options routes redirect there. Some analytics are scenarios or fixture-backed views, rather than current protocol measurements.

See [Core Concepts](/learn/overview) for the accounting model.
