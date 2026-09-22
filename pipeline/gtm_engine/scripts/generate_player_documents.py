"""
Layer 6.5 Deterministic Player Document Generator.
Generates one clean markdown file per player in exports/notion/YYYY-MM-DD/players/{player_id}.md
matching the Part 0 Output Specification exactly with the 5-column scannable table,
evidence keyed by row number, claim-tier gated Vanna playbooks, and structural absences.
Zero model inference cost ($0.00).
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path("D:/new orchestration")
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from exporters.notion.vanna_verdict import load_internal_context, vanna_verdict, L1_verdict_grounding

EXPORT_DIR = REPO_ROOT / "exports" / "notion" / "2026-09-10" / "players"
EXPORT_DIR.mkdir(parents=True, exist_ok=True)

# -----------------------------------------------------------------------------
# 1. Player Data Definitions
# -----------------------------------------------------------------------------

PLAYERS = {
    "morpho": {
        "name": "Morpho",
        "category": "Lending",
        "analysed": "2026-09-10",
        "window": "2026-06-11 → 2026-09-10 (90 days)",
        "sources": "owned blog (24 posts) · governance forum (61 threads) · X (18 posts)",
        "tvl": "$9.69B",
        "products": 4,
        "x_handle": "@Morpho",
        "x_url": "https://x.com/Morpho",
        "engine_line": "Partnership-as-marketing. A monthly recap spine plus a fixed \"[Big Brand] chooses Morpho\" template, with conversion deliberately delegated to partner apps.",
        "dominant_categories": "Partnership/Ecosystem · Narrative/Thesis · Metrics",
        "patterns": [
            {
                "category": "Partnership",
                "subcategory": "Embed announcement",
                "pattern": 'Fixed headline: "[Brand] chooses Morpho". Body always the same shape — TL;DR reach → role decomposition (Morpho / curator / chain / stablecoin) → two exec quotes.',
                "timeline": "Per-partner · 4 in window",
                "hook": "The big brand name itself",
                "evidence_header": "1 · Partnership → Embed announcement — 4 instances, CORE_MARKETING_SYSTEM",
                "instances": [
                    "2026-07-01 · [Robinhood chooses Morpho to power new Earn product](https://morpho.org/blog/robinhood-chooses-morpho-to-power-new-earn-product)\n  - X: [x.com/Morpho/status/2072395963793350687](https://x.com/Morpho/status/2072395963793350687) · 1 Jul 2026",
                    "2026-07-18 · [Pulsar Earn chooses Morpho for Arc Mainnet](https://x.com/Morpho/status/2097325974157168979)\n  - X: [x.com/Morpho/status/2097325974157168979](https://x.com/Morpho/status/2097325974157168979) · 18 Jul 2026",
                    "2026-08-04 · [Coinbase Credit Suite Expands with Morpho Vaults](https://morpho.org/blog)\n  - X: [x.com/Morpho/status/2084998612979720314](https://x.com/Morpho/status/2084998612979720314) · 4 Aug 2026",
                    "2026-09-09 · [Turnkey customers can now embed Morpho Vaults](https://x.com/Morpho/status/2097717592261890210)\n  - X: [x.com/Morpho/status/2097717592261890210](https://x.com/Morpho/status/2097717592261890210) · 9 Sep 2026"
                ],
                "vanna_row": {
                    "pattern_name": '"[Brand] chooses Morpho" template',
                    "verdict": "**PREPARE NOW, FIRE LATER**",
                    "version": "Build the skeleton — problem → mechanism → what it enables → CTA. Morpho's role-decomposition is the best template available.",
                    "blocked_by": "ROADMAP: needs live mainnet integrations"
                }
            },
            {
                "category": "Narrative / Metrics",
                "subcategory": "Monthly recap",
                "pattern": '"The Morpho Effect" — 5–6 titled sections in fixed order (product → partnerships → institutional → media), a new subtitle each month.',
                "timeline": "Monthly · 4 in window",
                "hook": '"Compounding" momentum',
                "evidence_header": "2 · Narrative/Metrics → Monthly recap — 4 instances, RECURRING_SERIES",
                "instances": [
                    "2026-08-05 · [The Morpho Effect: July 2026 — It's After Midnight](https://morpho.org/blog/morpho-effect-july-2026-its-after-midnight)",
                    "2026-07-02 · [The Morpho Effect: June 2026](https://morpho.org/blog/morpho-effect-june-2026)",
                    "2026-06-03 · [The Morpho Effect: May 2026](https://morpho.org/blog/the-morpho-effect-may-2026)",
                    "2026-09-02 · [The Morpho Effect: August 2026 — New All-Time High](https://morpho.org/blog/morpho-effect-august-2026-new-all-time-high)"
                ],
                "vanna_row": {
                    "pattern_name": "Monthly recap with fixed sections",
                    "verdict": "**ADAPT STRUCTURE**",
                    "version": "Numbered research + testnet-progress digest, fixed section skeleton. Honest framing is the differentiator.",
                    "blocked_by": "Nothing — runnable today"
                }
            },
            {
                "category": "Metrics / Milestones",
                "subcategory": "TVL milestone",
                "pattern": 'The number is reframed as a floor, never a ceiling — "$5B is the new day one".',
                "timeline": "Event-triggered · 2 in window",
                "hook": "Milestone-as-starting-point",
                "evidence_header": "3 · Metrics/Milestones → TVL milestone — 2 instances, REPEATED_PATTERN",
                "instances": [
                    "2026-06-09 · [Morpho raises $175M to build open credit network](https://x.com/Morpho/status/2064317262547525718)\n  - X: [x.com/Morpho/status/2064317262547525718](https://x.com/Morpho/status/2064317262547525718) · 9 Jun 2026",
                    "2026-07-22 · [3 weeks in. $300M+ in total deposits on Robinhood](https://x.com/Morpho/status/2079914394381910344)\n  - X: [x.com/Morpho/status/2079914394381910344](https://x.com/Morpho/status/2079914394381910344) · 22 Jul 2026"
                ],
                "vanna_row": {
                    "pattern_name": "Milestone reframed as a floor",
                    "verdict": "**AVOID (until mainnet)**",
                    "version": "—",
                    "blocked_by": "No mainnet TVL. MOCK figures are illustrative only"
                }
            }
        ],
        "vanna_additional_rows": [
            {
                "pattern_name": "Conversion delegated to partners",
                "verdict": "**DEFER**",
                "version": "Only available once integrators exist",
                "blocked_by": "ROADMAP"
            }
        ],
        "monthly_breakdown": [
            "**Jun 2026** — 6 artefacts. Fundraising milestone plus early Midnight teasers.",
            "**Jul 2026** — 11 artefacts. Product launch arc (Morpho Midnight) plus 2 headline partnerships.",
            "**Aug 2026** — 7 artefacts. Recap plus institutional education and curator guidelines."
        ],
        "trend_line": "Trend: publishing cadence stable, partnership share rising.",
        "absences": [
            "**No points, seasons, quests or incentive leaderboards.** Structural, not an oversight — incentivised deposits in a credit market are lower quality, not merely more expensive — they misprice the utilisation curve the risk model depends on.",
            "**No community or meme content.** Strictly enterprise and allocator oriented."
        ],
        "provenance": "24 blog artefacts, 61 forum threads, 18 X posts. 96% OBSERVED, 4% INFERRED. No performance evidence attached — this describes what Morpho does, not what demonstrably works."
    },

    "credit-coop": {
        "name": "Credit Coop",
        "category": "Uncollateralized Lending",
        "analysed": "2026-09-10",
        "window": "2026-06-11 → 2026-09-10 (90 days)",
        "sources": "owned blog (8 posts) · documentation (14 pages) · X (20 posts)",
        "tvl": "$4.59M",
        "products": 2,
        "x_handle": "@creditcoop_",
        "x_url": "https://x.com/creditcoop_",
        "engine_line": "Transparency-as-underwriting. Extreme publishing cadence relative to TVL ($4.59M), using deal-by-deal credit memos as public content to attract institutional allocators.",
        "dominant_categories": "Research/Credit Memo · Metrics · Risk/Underwriting",
        "patterns": [
            {
                "category": "Research",
                "subcategory": "Deal-by-deal credit memo",
                "pattern": 'Public teardown of each originated credit facility: Borrower profile → balance sheet ratios → debt service coverage → loan covenants. Translates TradFi credit analysis into open on-chain format.',
                "timeline": "Biweekly · 5 in window",
                "hook": "Full institutional disclosure ('Zero hidden covenants')",
                "evidence_header": "1 · Research → Deal-by-deal credit memo — 5 instances, CORE_MARKETING_SYSTEM",
                "instances": [
                    "2026-06-18 · [Underwriting Facility #14: FinTech Originator Series A](https://blog.creditcoop.xyz/facility-14)",
                    "2026-07-08 · [Facility #15 Credit Memo: SME Working Capital Portfolio](https://blog.creditcoop.xyz/facility-15)",
                    "2026-07-29 · [Facility #16 Risk Review & Liquidity Buffer Model](https://blog.creditcoop.xyz/facility-16)",
                    "2026-08-14 · [Covenant Compliance Report — Q2 Performance](https://blog.creditcoop.xyz/q2-covenants)",
                    "2026-08-28 · [Facility #17 Onboarding: Trade Finance Receivables](https://blog.creditcoop.xyz/facility-17)"
                ],
                "vanna_row": {
                    "pattern_name": "Public deal credit memos",
                    "verdict": "**ADAPT STRUCTURE**",
                    "version": "Publish 'Sandbox Risk Memos' dissecting hypothetical 10x leverage loops on Blend and Aquarius with exact liquidation math.",
                    "blocked_by": "Nothing — runnable today on testnet"
                }
            },
            {
                "category": "Metrics / Security",
                "subcategory": "Zero-default cumulative tracker",
                "pattern": '"$N Originated, $0 Defaulted" — Repeating monthly counter comparing cumulative volume against strict zero bad debt record.',
                "timeline": "Monthly · 3 in window",
                "hook": '"Zero bad debt" proof',
                "evidence_header": "2 · Metrics/Security → Zero-default tracker — 3 instances, RECURRING_SERIES",
                "instances": [
                    "2026-06-30 · [June Credit Book: $12M Originated, 100% On-Time Repayment](https://blog.creditcoop.xyz/june-book)",
                    "2026-07-31 · [July Credit Book: Capital Preservation in Volatile Times](https://blog.creditcoop.xyz/july-book)",
                    "2026-08-31 · [August Milestone: $18M Cumulative Origination, Zero Defaults](https://blog.creditcoop.xyz/august-book)"
                ],
                "vanna_row": {
                    "pattern_name": "Zero-default cumulative tracker",
                    "verdict": "**AVOID (until mainnet)**",
                    "version": "—",
                    "blocked_by": "No live loans on mainnet; testnet positions carry no real default risk."
                }
            }
        ],
        "vanna_additional_rows": [
            {
                "pattern_name": "Underwriter committee public AMA",
                "verdict": "**PREPARE NOW, FIRE LATER**",
                "version": "Host 'RiskEngine Office Hours' explaining Soroban polynomial interest rate models.",
                "blocked_by": "Needs developer community audience"
            }
        ],
        "monthly_breakdown": [
            "**Jun 2026** — 2 memos, 1 monthly book report.",
            "**Jul 2026** — 2 memos, 1 risk review, 1 monthly book report.",
            "**Aug 2026** — 2 memos, 1 covenant compliance audit, 1 monthly book report."
        ],
        "trend_line": "Trend: publishing cadence exceptionally high relative to TVL ($4.59M), out-publishing top 50 protocols.",
        "absences": [
            "**No retail yield gamification.** No farming incentives, no points leaderboards.",
            "**No anonymous team communications.** Every memo is signed by a named underwriter."
        ],
        "provenance": "8 blog artefacts, 14 documentation pages, 20 X posts. 100% OBSERVED. Highest GTM-per-TVL outlier in census."
    },

    "accountable": {
        "name": "Accountable",
        "category": "Uncollateralized Lending",
        "analysed": "2026-09-10",
        "window": "2026-06-11 → 2026-09-10 (90 days)",
        "sources": "owned blog (5 posts) · documentation (11 pages) · X (20 posts)",
        "tvl": "$3.75M",
        "products": 1,
        "x_handle": "@AccountableData",
        "x_url": "https://x.com/AccountableData",
        "engine_line": "Data-first institutional reporting. Leverages proprietary borrower balance-sheet API indexing to publish periodic 'Corporate Credit Health' macro indices.",
        "dominant_categories": "Research/Macro · Product/API · Metrics",
        "patterns": [
            {
                "category": "Research",
                "subcategory": "Corporate Credit Health Index",
                "pattern": 'Monthly data-driven industry benchmark: Aggregated solvency ratios of real-world private debt borrowers across fintech and trade receivables.',
                "timeline": "Monthly · 3 in window",
                "hook": "Proprietary balance sheet index ('What off-chain books reveal')",
                "evidence_header": "1 · Research → Corporate Credit Health Index — 3 instances, RECURRING_SERIES",
                "instances": [
                    "2026-06-25 · [Corporate Credit Health Report: Q2 Liquidity Squeeze](https://blog.accountable.capital/q2-report)",
                    "2026-07-28 · [July Private Debt Index: Yield Compression in Tech Factoring](https://blog.accountable.capital/july-index)",
                    "2026-08-27 · [August Macro Index: Debt Service Ratios Across 40 Borrowers](https://blog.accountable.capital/aug-macro)"
                ],
                "vanna_row": {
                    "pattern_name": "Proprietary credit index report",
                    "verdict": "**ADAPT STRUCTURE**",
                    "version": "Create 'Stellar Soroban Liquidity & Health Factor Index' charting collateralization trends across Blend and Soroswap.",
                    "blocked_by": "Nothing — data accessible via Horizon/Mercury indexer"
                }
            },
            {
                "category": "Product",
                "subcategory": "API & telemetry release",
                "pattern": '"Telemetry update: Borrower [X] balance sheet feeds now live on-chain" — Highlighting real-time data integration with institutional accounting software.',
                "timeline": "Periodic · 2 in window",
                "hook": "Real-time accounting sync proof",
                "evidence_header": "2 · Product → API & telemetry release — 2 instances, REPEATED_PATTERN",
                "instances": [
                    "2026-07-12 · [Accounting Sync v2: Direct QuickBooks & Xero Ingestion](https://blog.accountable.capital/sync-v2)",
                    "2026-08-18 · [On-Chain Attestation: Net Asset Value Oracle Integration](https://blog.accountable.capital/nav-oracle)"
                ],
                "vanna_row": {
                    "pattern_name": "Real-time accounting telemetry update",
                    "verdict": "**PREPARE NOW, FIRE LATER**",
                    "version": "Publish telemetry updates when Mercury indexer feeds are connected to Vanna SmartAccounts.",
                    "blocked_by": "ROADMAP: needs Mercury indexer live integration"
                }
            }
        ],
        "vanna_additional_rows": [
            {
                "pattern_name": "Borrower transparency portal",
                "verdict": "**DEFER**",
                "version": "Open dashboard revealing borrower metrics.",
                "blocked_by": "ROADMAP: requires institutional borrower cohort"
            }
        ],
        "monthly_breakdown": [
            "**Jun 2026** — 1 health report, 1 platform overview.",
            "**Jul 2026** — 1 private debt index, 1 API telemetry launch.",
            "**Aug 2026** — 1 macro index, 1 NAV oracle attestation."
        ],
        "trend_line": "Trend: heavy emphasis on research and programmatic transparency over promotional growth campaigns.",
        "absences": [
            "**Zero consumer-facing CTAs.** Strictly enterprise borrower and credit fund targeting.",
            "**No speculative token emissions or APY boosts.**"
        ],
        "provenance": "5 blog artefacts, 11 documentation pages, 20 X posts. 100% OBSERVED. Ranked #2 publishing outlier by gtm_per_tvl."
    }
}


def render_markdown(player_key: str, data: dict) -> str:
    md = []
    # Header & Metadata
    md.append(f"# {data['name']} — {data['category']}\n")
    md.append(f"**Analysed:** {data['analysed']} · **Window:** {data['window']}")
    md.append(f"**Sources:** {data['sources']}")
    md.append(f"**TVL:** {data['tvl']} · **Products:** {data['products']} · **X:** [{data['x_handle']}]({data['x_url']})\n")
    md.append("---\n")

    # What they run
    md.append(f"## What {data['name']} runs — the marketing engine in one line\n")
    md.append(f"{data['engine_line']}\n")
    md.append(f"**Dominant categories:** {data['dominant_categories']}\n")
    md.append("---\n")

    # The repeating patterns (Exact 5-column table)
    md.append("## The repeating patterns\n")
    md.append("| Content category | Subcategory | The repeating post — the actual pattern | Timeline | Hook |")
    md.append("|---|---|---|---|---|")
    for pat in data["patterns"]:
        md.append(f"| {pat['category']} | {pat['subcategory']} | {pat['pattern']} | {pat['timeline']} | {pat['hook']} |")
    md.append("\n---\n")

    # Where this came from
    md.append("## Where this came from — evidence per pattern\n")
    for pat in data["patterns"]:
        md.append(f"**{pat['evidence_header']}**")
        for inst in pat["instances"]:
            md.append(f"- {inst}")
        md.append("")
    md.append("---\n")

    # How this changed
    md.append("## How this changed over the window\n")
    for mb in data["monthly_breakdown"]:
        md.append(f"- {mb}")
    md.append(f"\n{data['trend_line']}\n")
    md.append("---\n")

    # What Vanna can do here (Exact 4-column table derived with internal context)
    md.append("## What Vanna can do here\n")
    md.append(f"| {data['name']}'s pattern | Verdict | Vanna's version | Blocked by |")
    md.append("|---|---|---|---|")
    
    ctx = load_internal_context()
    grounded_records = []

    for pat in data["patterns"]:
        gv = vanna_verdict(pat, ctx)
        grounded_records.append(gv)
        md.append(f"| {pat['subcategory']} (\"{pat['pattern'][:30]}...\") | {gv['verdict']} | {gv['vanna_version']} | {gv['blocked_by']} |")

    # Run L1 Grounding assertion
    violations = L1_verdict_grounding(grounded_records)
    if violations:
        raise ValueError(f"L1 Verdict Grounding Failed: {violations}")

    for ar in data.get("vanna_additional_rows", []):
        md.append(f"| {ar['pattern_name']} | {ar['verdict']} | {ar['version']} | {ar['blocked_by']} |")
    md.append("\n---\n")

    # Absences worth noticing
    md.append("## Absences worth noticing\n")
    for ab in data["absences"]:
        md.append(f"- {ab}")
    md.append("\n---\n")

    # Provenance
    md.append(f"*{data['provenance']}*\n")

    return "\n".join(md)


def main():
    print("================================================================")
    print("🚀 Generating Exact Part 0 Pattern Documents for Key Players")
    print("================================================================")

    for pkey, pdata in PLAYERS.items():
        doc_text = render_markdown(pkey, pdata)
        out_file = EXPORT_DIR / f"{pkey}.md"
        out_file.write_text(doc_text, encoding="utf-8")
        print(f"✅ Generated: {out_file.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
