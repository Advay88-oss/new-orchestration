"""Ingests complete Vanna multi-chain ground truth (Solana + Stellar + AI tokens + Tokenized Equities)
into Vanna Brand Brain (brain.db).
"""
import hashlib
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
BRAIN_DB = REPO_ROOT / "pipeline" / "brain" / "tenants" / "vanna" / "brain.db"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


KNOWLEDGE_PACKS = [
    {
        "title": "Vanna Solana Architecture & Surfpool Fork Deployment",
        "section": "Core Solana Infrastructure",
        "url": "https://github.com/vannafinance/Solana_Docs/blob/main/developers/overview.mdx",
        "page_id": "solana:overview",
        "text": """Vanna Protocol on Solana (Protocol_V1_Solana) is an Anchor-based cross-margin lending and leverage engine.
Program ID: BZ812nUv4Qhr2p1JVgmoJGjYTGk1brAXckyhFSCNH3Zg (Anchor Program: vanna_lending).
Live Demo: https://devnet.solana.vanna.finance/portfolio
Custom RPC: https://rpc-devnet.solana.vanna.finance (Hosted on a Surfpool mainnet fork cloning real mainnet state).
Local RPC: http://127.0.0.1:8899.
Key capabilities: Cross-margin user PDAs, Jupiter margin swaps, zero funding-rate perps, Kamino yield farming integration, and Pyth oracle price feeds.
Architecture boundaries: Single unified health factor per cross-margin account; collateral and debt positions are derived PDAs tied to user authority."""
    },
    {
        "title": "Vanna Solana Supported Assets: Tokenized Equities (xStocks) & Pre-IPO AI Shares (PreStocks)",
        "section": "Configured Reserves and Mints",
        "url": "https://github.com/vannafinance/Solana_Docs/blob/main/developers/deployed-contracts.mdx",
        "page_id": "solana:deployed_contracts",
        "text": """Vanna configures seven active on-chain reserves on Solana:
1. TSLAx (Tesla Tokenized Stock): Mint XsDoVfqeBukxuZHWhdvWHBhgEHjGNst4MLodqsJHzoB (Token-2022, 8 decimals).
2. OPENAI (OpenAI Pre-IPO Share Token from PreStocks): Mint PreweJYECqtQwBtpxHL171nL2K6umo692gTm7Q3rpgF (Token-2022, 9 decimals).
3. ANTHROPIC (Anthropic Pre-IPO Share Token from PreStocks): Mint Pren1FvFX6J3E4kXhJuCiAD5aDmGEb7qJRncwA8Lkhw (Token-2022, 9 decimals).
4. GOOGLx (Alphabet Tokenized Stock): Mint XsCPL9dNWBMvFtTmwcCA5v3xWPSMEBCszbQdiLLq6aN (Token-2022, 8 decimals).
5. AAPLx (Apple Tokenized Stock): Mint XsbEhLAtcf6HdfpFZ5xEMdqW8nfAvcsP5bdudRLJzJp (Token-2022, 8 decimals).
6. WSOL (Native Wrapped Solana): Mint So11111111111111111111111111111111111111112.
7. USDC (Native Settlement Asset): Mint EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v.
Pyth price oracles feed real-time pricing for both equity xStocks and crypto assets."""
    },
    {
        "title": "Vanna Solana: Up to 5x Long and Short Perps with ZERO Funding Rates",
        "section": "Perps and Trading Engine",
        "url": "https://github.com/vannafinance/Solana_Docs/blob/main/guides/why-vanna.mdx",
        "page_id": "solana:perps_mechanics",
        "text": """Vanna provides up to 5x leveraged long and short positions on tokenized equities and pre-IPO shares with ZERO funding rates.
Unlike virtual perpetual contracts (GMX, Drift, dYdX) which bleed 15%-40% annualized funding payments while holding positions, Vanna builds positions from borrowed spot tokens routed through Jupiter DEX in one atomic transaction.
Long Recipe: Trader deposits USDC -> Borrows additional USDC from Vanna pool -> Swaps total into TSLAx/OPENAI/ANTHROPIC via Jupiter swap.
Short Recipe: Trader deposits stock token -> Borrows additional stock token from Vanna pool -> Swaps total into USDC via Jupiter swap.
Both operations execute in a single signed Solana transaction. The trader pays standard fixed borrow APR rather than unpredictable hourly funding rate volatility."""
    },
    {
        "title": "Vanna Solana: Solving Kamino 0% Stock Yield & Dual-Market Integration",
        "section": "Kamino and Yield Mechanics",
        "url": "https://github.com/vannafinance/Solana_Docs/blob/main/learn/kamino-integration.mdx",
        "page_id": "solana:kamino_integration",
        "text": """Why Kamino stock supply APY was 0%: Kamino listed xStocks in market 5wJeMrUYECGq41fxRESKALVcHnNX26TAWy4W98yULsua, but borrower utilization was approximately 0%. Holding TSLAx or AAPLx in Kamino earned nothing.
How Vanna solves it:
1. Vanna creates active Credit LP pools for stock tokens. Margin traders and short-sellers actively borrow these stocks, driving utilization up and generating real APY for stock lenders.
2. Vanna Farm / Carry Trade: Vanna routes leveraged stock borrowing proceeds into Kamino's Main Market (7u3HeHxYDLhnCoErrtycNokbQYbWGzLs6JSDqGAv5PfF), where high-yield USDC (D6q6wuQSrifJKZYpR1M8R4YawnLDtDsMmWM1NbBmgJ59) and SOL (d4A2prbA2whesmvHaL88BH6Ewn5N4bTSU2Ze8P6Bc4Q) reserves pay real double-digit yield.
Lenders turn dead 0% equity holdings into productive cash flow."""
    },
    {
        "title": "Token-2022 TransferFeeConfig on AI PreStocks (ANTHROPIC and OPENAI)",
        "section": "Token Mechanics and Fees",
        "url": "https://github.com/vannafinance/Solana_Docs/blob/main/learn/tokenized-stocks.mdx",
        "page_id": "solana:token2022_transfer_fees",
        "text": """PreStocks (ANTHROPIC and OPENAI) originate from prestocks.com and utilize the Solana Token-2022 standard.
Crucial mechanism: ANTHROPIC and OPENAI carry an on-chain Token-2022 TransferFeeConfig extension of 100 bps (1.00%) per transfer.
Vanna's Solana smart contracts natively account for this 1% transfer haircut in deposit, withdrawal, and Jupiter swap calculations, ensuring that pool accounting and debt balances never mismatch actual on-chain token vault balances."""
    },
    {
        "title": "Vanna Solana: Unified Cross-Margin Solvency & Liquidation Bots",
        "section": "Risk and Liquidation Rules",
        "url": "https://github.com/vannafinance/Solana_Docs/blob/main/developers/guides/liquidation-bots.mdx",
        "page_id": "solana:liquidation_system",
        "text": """Health Factor Floor: Vanna enforces a strict 1.1x Health Factor (HF) threshold across all collateral and debt positions.
Unified Margin: Farm receipts, spot stock collateral, and Jupiter swaps share ONE single health factor.
Liquidation Process:
1. Public bots monitor margin PDAs.
2. Call public_refresh_reserve to accrue interest.
3. Fetch fresh Pyth price updates and Kamino exchange rates.
4. When HF <= 1.1, call public_liquidate with min_collateral_out.
5. Liquidator seizes collateral with a liquidation bonus, protecting lending pool solvency."""
    },
    {
        "title": "Vanna Stellar Architecture: Composable Prime Brokerage on Soroban",
        "section": "Stellar Soroban Engine",
        "url": "https://github.com/vannafinance/Vanna_docs/blob/main/developers/architecture.mdx",
        "page_id": "stellar:architecture",
        "text": """Vanna Protocol on Stellar Soroban is a 4-layer prime brokerage and composable credit system:
Layer 1: LendingPools issuing vTokens (vXLM, vUSDC) with dynamic polynomial RateModel and shared liquidation fees.
Layer 2: AccountManager contract managing trader accounts and enforcing WAD math.
Layer 3: Dedicated SmartAccount sandboxes per trader. Funds cannot be extracted directly to external wallets.
Layer 4: RiskEngine contract enforcing a strict 1.1x Health Factor floor with real-time Mercury indexer telemetry (~320ms).
Multi-Asset Markets: Ingests 4 distinct lending markets: native XLM, BLUSDC (Blend b-tokens), AqUSDC (Aquarius AMM), and SoUSDC (Soroswap DEX).
Enables up to 10x leverage natively routed into Blend, Soroswap, and Aquarius."""
    },
    {
        "title": "Zonymous Labs & The Vanna 18-Protocol Constellation",
        "section": "Ecosystem and Parent Studio",
        "url": "https://github.com/vannafinance/Zonymous/blob/main/lib/site.ts",
        "page_id": "ecosystem:zonymous_constellation",
        "text": """Zonymous Labs (zonymouslabs.com) is the senior engineering studio behind Vanna Finance, specializing in AI automation and autonomous on-chain finance ('Software that acts on its own, and money that runs on code').
The Vanna Constellation links credit across 18 major protocols in 5 categories:
- Perps: Hyperliquid, dYdX, GMX
- Spot: Uniswap, Curve, Angle
- Options: Derive, Lyra, Ribbon
- Yield: Pendle, Yearn, Convex, Notional
- Lending: Aave, Compound, MakerDAO, Morpho, Euler."""
    }
]

WHATS_NEW_ITEMS = [
    {
        "id": "wn:solana:prestocks_and_xstocks",
        "kind": "feature_launch",
        "title": "Solana Deployment: Tokenized Stocks (TSLAx) & AI PreStocks (OPENAI, ANTHROPIC)",
        "detail": "Vanna launches Protocol_V1_Solana on Surfpool fork RPC with 7 reserves: TSLAx, GOOGLx, AAPLx, OPENAI, ANTHROPIC, WSOL, USDC. Provides 5x long/short leverage with zero funding rates and solves Kamino 0% stock yield.",
        "url": "https://github.com/vannafinance/Solana_Docs"
    },
    {
        "id": "wn:solana:zero_funding_perps",
        "kind": "mechanism_update",
        "title": "Zero Funding-Rate Equity Perps via Jupiter Atomic Swaps",
        "detail": "Long and short stock positions are constructed using spot borrowed tokens routed through Jupiter in one signed transaction, eliminating the 20-40% annual funding rate bleed of traditional perps.",
        "url": "https://github.com/vannafinance/Solana_Docs/blob/main/guides/why-vanna.mdx"
    },
    {
        "id": "wn:stellar:multi_asset_markets",
        "kind": "architecture_update",
        "title": "Stellar Soroban: 4 Lending Markets & Blend/Soroswap/Aquarius Routing",
        "detail": "Configured 4 independent lending pools for XLM, BLUSDC (Blend), AqUSDC (Aquarius), and SoUSDC (Soroswap) inside dedicated SmartAccount sandboxes with 1.1x RiskEngine protection.",
        "url": "https://github.com/vannafinance/Vanna_docs"
    }
]


def ingest_into_brain():
    raise SystemExit(
        "This script is not the brain. It writes unverified packs into the laptop "
        "file and skips Cloud SQL. The live path is "
        "python -m pipeline.brand_brain.github_sync sync"
    )
    print(f"Connecting to Brand Brain SQLite: {BRAIN_DB}")
    conn = sqlite3.connect(BRAIN_DB)
    cursor = conn.cursor()

    now = _now()
    chunks_inserted = 0
    whats_new_inserted = 0

    # 1. Insert Chunks
    for kp in KNOWLEDGE_PACKS:
        cid = "chunk:github:" + _hash(kp["page_id"] + kp["text"])
        h = _hash(kp["text"])
        prefix = f"# {kp['title']}\n## {kp['section']}"

        # Delete existing chunk with same page_id to keep clean
        cursor.execute("DELETE FROM chunks WHERE page_id=?", (kp["page_id"],))

        cursor.execute(
            """
            INSERT INTO chunks (
                id, source, authority, url, page_id, title, section,
                parent_id, content_type, prefix, text, hash, updated_at, deleted, embedding
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                cid,
                "github",
                1,  # Authority 1 = Core Ground Truth
                kp["url"],
                kp["page_id"],
                kp["title"],
                kp["section"],
                None,
                "guide",
                prefix,
                kp["text"],
                h,
                now,
                0,
                None  # Embedding populated by sync_embeddings
            )
        )
        chunks_inserted += 1

    # 2. Insert What's New
    for wn in WHATS_NEW_ITEMS:
        cursor.execute("DELETE FROM whats_new WHERE id=?", (wn["id"],))
        cursor.execute(
            """
            INSERT INTO whats_new (
                id, at, kind, title, detail, source, url, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                wn["id"],
                now,
                wn["kind"],
                wn["title"],
                wn["detail"],
                "github_source_truth",
                wn["url"],
                now
            )
        )
        whats_new_inserted += 1

    conn.commit()
    conn.close()

    print(f"Successfully ingested {chunks_inserted} authoritative chunks and {whats_new_inserted} updates into Vanna Brand Brain!")


if __name__ == "__main__":
    ingest_into_brain()
