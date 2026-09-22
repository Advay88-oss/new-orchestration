#!/usr/bin/env python3
"""Syncs Vanna Authoritative Campaigns and Recurring Series into Canonical Database.
Fixes Blocker 9 (Canonical DB Sync for Campaigns & Series).
Uses AtomicJsonlStore for concurrency protection.
"""

from __future__ import annotations

import json
from pathlib import Path
import sys

REPO_ROOT = Path("D:/new orchestration")
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

DB_SERIES_FILE = BRAIN_DB_DIR / "recurring_series.jsonl"
DB_CAMPAIGNS_FILE = BRAIN_DB_DIR / "campaigns.jsonl"

from pipeline.gtm_storage.atomic_store import AtomicJsonlStore
from pipeline.gtm_orchestration.config import BRAIN_DB_DIR, BRAIN_ROOT, CANONICAL_KNOWLEDGE_ROOT

# Authoritative Vanna Series
VANNA_SERIES = [
    {
        "series_id": "SERIES_VANNA_ARCHITECTURE",
        "player_id": "vanna-protocol",
        "name": "Vanna Architectural Deep-Dives",
        "cadence": "BI_WEEKLY",
        "first_observed": "2026-09-01",
        "last_observed": "2026-09-17",
        "occurrence_count": 3,
        "occurrence_record_ids": ["POST_ARCH_01", "POST_ARCH_02", "POST_ARCH_03"],
        "template_structure": [
            "1. Architectural Invariant / Problem Statement",
            "2. Isolated SmartAccount Sandbox Mechanics",
            "3. Stellar Soroban Smart Contract Implementation",
            "4. Verifiable Testnet Deployment Link"
        ],
        "audience": ["A2: Quantitative Builders", "A3: Institutional LPs"],
        "purpose": "TECHNICAL_AUTHORITY",
        "proof_type": "CONTRACT_INVARIANTS",
        "cta": "DEPLOY_SANDBOX",
        "confidence": "HIGH"
    },
    {
        "series_id": "SERIES_SOROBAN_COMPOSABLE_YIELD",
        "player_id": "vanna-protocol",
        "name": "The Soroban Composable Yield Series",
        "cadence": "WEEKLY",
        "first_observed": "2026-09-10",
        "last_observed": "2026-09-17",
        "occurrence_count": 2,
        "occurrence_record_ids": ["POST_YIELD_01", "POST_YIELD_02"],
        "template_structure": [
            "1. Single-Asset Lending vs Composable 10x Margin",
            "2. Blend v2 Vault & Aquarius AMM Routing",
            "3. Live Yield Multiplier & Health Factor Buffer",
            "4. Testnet Interactive Sandbox Callout"
        ],
        "audience": ["A1: Stellar DeFi Farmers", "A2: Quantitative Traders"],
        "purpose": "YIELD_EDUCATION",
        "proof_type": "ON_CHAIN_TVL_AND_RATES",
        "cta": "EXPLORE_VAULTS",
        "confidence": "HIGH"
    },
    {
        "series_id": "SERIES_SOLVENCY_WEEKLY",
        "player_id": "vanna-protocol",
        "name": "Vanna Weekly Solvency & Telemetry Report",
        "cadence": "WEEKLY",
        "first_observed": "2026-08-25",
        "last_observed": "2026-09-16",
        "occurrence_count": 4,
        "occurrence_record_ids": ["SOLV_W1", "SOLV_W2", "SOLV_W3", "SOLV_W4"],
        "template_structure": [
            "1. Average Network Health Factor (Target >= 1.45x)",
            "2. Sub-second Mercury Latency Distribution (~320ms)",
            "3. Proactive Rebalances Executed (1.25x trigger)",
            "4. Bad Debt Incurred ($0.00)"
        ],
        "audience": ["DeFi Allocators", "Risk Curators", "Institutional LPs"],
        "purpose": "SOLVENCY_AND_RISK_TRANSPARENCY",
        "proof_type": "MERCURY_INDEXER_LOGS",
        "cta": "INSPECT_TELEMETRY",
        "confidence": "HIGH"
    },
    {
        "series_id": "SERIES_MEV_DEFENSE_DISPATCH",
        "player_id": "vanna-protocol",
        "name": "Sub-Second Telemetry & Liquidation Deflection",
        "cadence": "BI_WEEKLY",
        "first_observed": "2026-09-05",
        "last_observed": "2026-09-17",
        "occurrence_count": 2,
        "occurrence_record_ids": ["MEV_01", "MEV_02"],
        "template_structure": [
            "1. Mempool Front-Running Vulnerability Analysis",
            "2. Soroban Fixed 0.00014 XLM Gas Economics",
            "3. Off-Chain Keeper Execution Invariant",
            "4. Documentation / Code Repository Reference"
        ],
        "audience": ["EVM Migrants", "DeFi Researchers"],
        "purpose": "COMPETITIVE_DIFFERENTIATION",
        "proof_type": "GAS_BENCHMARK_AND_TRACE",
        "cta": "READ_SPECS",
        "confidence": "HIGH"
    }
]

# Authoritative Vanna Campaigns
VANNA_CAMPAIGNS = [
    {
        "campaign_id": "CAMP_TESTNET_SANDBOX_ALPHA",
        "player_id": "vanna-protocol",
        "name": "Vanna Testnet SmartAccount Alpha Launch",
        "narrative_goal": "Establish Vanna as the premier composable credit infrastructure on Stellar Soroban.",
        "start_date": "2026-09-01",
        "end_date": "2026-10-15",
        "stages": [
            {"stage_num": 1, "stage_name": "Audit & Security Invariants", "source_url": "https://docs.vanna.finance/security", "evidence_status": "OBSERVED"},
            {"stage_num": 2, "stage_name": "SmartAccount Isolation Deep Dive", "source_url": "https://docs.vanna.finance/smartaccounts", "evidence_status": "OBSERVED"},
            {"stage_num": 3, "stage_name": "Testnet Deployment Broadcast", "source_url": "https://test.stellar.vanna.finance", "evidence_status": "OBSERVED"},
            {"stage_num": 4, "stage_name": "Risk Guardian Solvency Traction", "source_url": "https://vanna.finance", "evidence_status": "DERIVED"}
        ],
        "confidence": "HIGH"
    },
    {
        "campaign_id": "CAMP_BLEND_V2_INTEGRATION",
        "player_id": "vanna-protocol",
        "name": "Blend v2 Composable Credit Partnership Campaign",
        "narrative_goal": "Unlock 10x leveraged borrowing and yield on top of Blend v2 $149M TVL pools.",
        "start_date": "2026-09-10",
        "end_date": "2026-10-30",
        "stages": [
            {"stage_num": 1, "stage_name": "Hero Integration Co-Announcement", "source_url": "https://docs.blend.capital", "evidence_status": "OBSERVED"},
            {"stage_num": 2, "stage_name": "Composable Margin Routing Mechanics", "source_url": "https://docs.vanna.finance", "evidence_status": "OBSERVED"},
            {"stage_num": 3, "stage_name": "Harvest & Yield Velocity Update", "source_url": "https://test.stellar.vanna.finance", "evidence_status": "DERIVED"}
        ],
        "confidence": "HIGH"
    }
]

def sync_series_and_campaigns():
    print("▶ Syncing Vanna Series and Campaigns into Canonical DB...")
    
    # Series
    series_store = AtomicJsonlStore(DB_SERIES_FILE)
    existing_series = {r["series_id"]: r for r in series_store.read_all()}
    for s in VANNA_SERIES:
        existing_series[s["series_id"]] = s
    series_store.atomic_overwrite(list(existing_series.values()))
    print(f"✅ Synchronized {len(existing_series)} series to {DB_SERIES_FILE}")

    # Campaigns
    campaign_store = AtomicJsonlStore(DB_CAMPAIGNS_FILE)
    existing_camps = {r["campaign_id"]: r for r in campaign_store.read_all()}
    for c in VANNA_CAMPAIGNS:
        existing_camps[c["campaign_id"]] = c
    campaign_store.atomic_overwrite(list(existing_camps.values()))
    print(f"✅ Synchronized {len(existing_camps)} campaigns to {DB_CAMPAIGNS_FILE}")

if __name__ == "__main__":
    sync_series_and_campaigns()
