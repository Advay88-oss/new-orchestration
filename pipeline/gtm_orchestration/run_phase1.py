#!/usr/bin/env python3
"""CLI Entry point for Phase 1 Vanna GTM Orchestration Operating System.

Usage:
  python pipeline/gtm_orchestration/run_phase1.py [--category LENDING] [--test-no-action]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

STATE_DIR = REPO_ROOT / "pipeline" / "state"

from pipeline.gtm_orchestration.gtm_orchestrator import GTMOrchestrator
from pipeline.gtm_orchestration.intelligence_provider import IntelligenceProvider


def main() -> int:
    parser = argparse.ArgumentParser(description="Vanna GTM Orchestration Operating System (Phase 1)")
    parser.add_argument("--category", default="LENDING", help="Market category to query from Brain DB")
    parser.add_argument("--test-no-action", action="store_true", help="Demonstrate NO_ACTION suppression on irrelevant signals")
    args = parser.parse_args()

    orchestrator = GTMOrchestrator()

    if args.test_no_action:
        print("▶ Running in NO_ACTION test mode (irrelevant signal)...")
        from pipeline.gtm_orchestration.schemas import MarketSignal
        irrelevant_sig = MarketSignal(
            signal_id="SIG-NOACTION-DEMO",
            headline="Celebrity Meme Coin Surges on Solana DEX",
            description="A viral speculative token with zero utility or lending mechanics gained social volume.",
            market_category="MEME_COINS",
            source="https://x.com/crypto_memes",
            source_type="SOCIAL_CORPUS",
            record_id="rec_meme_999",
            observed_at="2026-09-16T12:00:00Z",
            confidence="LOW",
            evidence_status="UNKNOWN"
        )
        trace = orchestrator.run_lifecycle(signal_override=irrelevant_sig, force_no_action=True)
    else:
        # Pull real signal from Brain DB
        intel = IntelligenceProvider()
        signals = intel.get_market_signals(category=args.category, limit=1)
        if not signals:
            print("❌ No signals found in Brain DB.")
            return 1
        signal = signals[0]
        print(f"▶ Selected Market Signal: {signal.headline} (Source: {signal.source_type} | Record: {signal.record_id})")
        trace = orchestrator.run_lifecycle(signal_override=signal)

    print("\n" + "=" * 75)
    print("📋 SUMMARY OF GENERATED CONTRACT ARTIFACTS")
    print("=" * 75)
    print(f"• Trace ID:           {trace.trace_id}")
    print(f"• Overall Status:     {trace.overall_status}")
    print(f"• Total Stages Run:   {len(trace.stages)}")
    print(f"• Provenance Entries: {len(trace.provenance_chain)}")
    print(f"• Trace File:         {STATE_DIR / 'execution_trace.json'}")

    if trace.overall_status == "WAITING_FOR_HUMAN":
        strat_file = STATE_DIR / "gtm_strategy.json"
        pkg_file = STATE_DIR / "content_package.json"
        cr_file = STATE_DIR / "creative_brief.json"
        print(f"• Strategy Contract:  {strat_file} ({strat_file.stat().st_size:,} bytes)")
        print(f"• Content Package:    {pkg_file} ({pkg_file.stat().st_size:,} bytes)")
        print(f"• Creative Brief:     {cr_file} ({cr_file.stat().st_size:,} bytes)")
        print(f"• Human Review Pkt:   Ready for Telegram Gateway approval")

    return 0


if __name__ == "__main__":
    sys.exit(main())
