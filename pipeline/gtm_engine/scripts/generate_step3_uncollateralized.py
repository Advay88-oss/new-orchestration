"""
Generate Step 3: Subject Category Deep-Dive (doc_10_uncollateralized_lending.md).
Zero model calls ($0.00).
"""

from pathlib import Path

EXPORT_FILE = Path("D:/new orchestration/exports/notion/2026-09-10/doc_10_uncollateralized_lending.md")
EXPORT_FILE.parent.mkdir(parents=True, exist_ok=True)

COLLECTED_PLAYERS = [
    {
        "name": "Credit Coop",
        "slug": "credit-coop",
        "tvl": "$4,588,671.47",
        "x_handle": "@creditcoop_xyz",
        "blog_url": "https://blog.creditcoop.xyz",
        "artefacts_90d": 8,
        "engine": "Transparency-as-underwriting. Extreme publishing cadence relative to TVL ($4.59M), using deal-by-deal credit memos as public content to attract institutional allocators.",
        "patterns": [
            ("Research", "Deal-by-deal credit memo", "Underwriting Facility #[N]: Borrower balance sheet review & debt covenants.", "Biweekly · 5 in window", "Full institutional disclosure"),
            ("Metrics / Security", "Zero-default tracker", '"$18M Originated, $0 Defaulted" — Repeating monthly volume vs bad debt counter.', "Monthly · 3 in window", '"Zero bad debt" proof')
        ],
        "vanna_verdict": [
            ("Public deal credit memos", "**ADAPT STRUCTURE**", "Publish 'Sandbox Risk Memos' dissecting hypothetical 10x leverage loops on Blend and Aquarius with exact liquidation math.", "Nothing — runnable today on testnet"),
            ("Zero-default cumulative tracker", "**AVOID (until mainnet)**", "—", "No live loans on mainnet; testnet positions carry no real default risk.")
        ]
    },
    {
        "name": "Accountable",
        "slug": "accountable",
        "tvl": "$3,746,493.19",
        "x_handle": "@AccountableData",
        "blog_url": "https://blog.accountable.capital",
        "artefacts_90d": 5,
        "engine": "Data-first institutional reporting. Leverages proprietary borrower balance-sheet API indexing to publish periodic 'Corporate Credit Health' macro indices.",
        "patterns": [
            ("Research", "Corporate Credit Health Index", "Monthly industry benchmark charting solvency ratios of real-world private debt borrowers.", "Monthly · 3 in window", "Proprietary balance sheet index"),
            ("Product", "API & telemetry release", "Telemetry Update: Direct QuickBooks/Xero and NAV oracle on-chain sync feeds.", "Periodic · 2 in window", "Real-time accounting sync proof")
        ],
        "vanna_verdict": [
            ("Proprietary credit index report", "**ADAPT STRUCTURE**", "Create 'Stellar Soroban Liquidity & Health Factor Index' charting collateralization trends across Blend and Soroswap.", "Nothing — data accessible via Horizon/Mercury indexer"),
            ("Real-time accounting telemetry update", "**PREPARE NOW, FIRE LATER**", "Publish telemetry updates when Mercury indexer feeds are connected to Vanna SmartAccounts.", "ROADMAP: needs Mercury indexer live integration")
        ]
    }
]

PENDING_MEMBERS = [
    ("Pareto Credit", "pareto-credit", "$226,216,675.04", "@paretocredit", "https://paretocredit.com", 0, "FLAGSHIP_INSTITUTIONAL"),
    ("cSigma Finance", "csigma-finance", "$21,591,638.53", "@csigmafinance", "https://csigma.finance", 0, "PENDING"),
    ("Kasu", "kasu", "$12,518,044.95", "@kasuFinance", "https://kasu.finance", 0, "PENDING"),
    ("3Jane Lending", "3jane-lending", "$12,404,917.09", "@3janexyz", "https://3jane.xyz", 0, "PENDING"),
    ("Wildcat Protocol", "wildcat-protocol", "$8,202,229.86", "@WildcatFi", "https://wildcat.finance", 0, "PENDING"),
    ("Goldfinch", "goldfinch", "$2,558,595.29", "@goldfinch_fi", "https://goldfinch.finance", 0, "LEGACY_CREDIT"),
    ("Union Protocol", "union-protocol", "$266,042.28", "@unionprotocol", "https://union.finance", 0, "PENDING"),
    ("Clearpool Lending", "clearpool-lending", "$234,066.93", "@ClearpoolFin", "https://clearpool.finance", 0, "PENDING"),
    ("Ribbon Lend", "ribbon-lend", "$52,335.20", "@ribbonfinance", "https://ribbon.finance", 0, "LEGACY_DEBT"),
    ("dAMM Finance", "damm-finance", "$23,074.53", "@dammfinance", "https://damm.finance", 0, "PENDING"),
    ("TrueFi", "truefi", "$21,735.48", "@TrueFiDAO", "https://truefi.io", 0, "LEGACY_CREDIT"),
    ("Atlendis V1", "atlendis-v1", "$16,806.57", "@AtlendisLabs", "https://atlendis.io", 0, "DEPRECATED"),
    ("Atlendis V2", "atlendis-v2", "$1,013.16", "@AtlendisLabs", "https://atlendis.io", 0, "PENDING"),
    ("Avocado Fund", "avocado-fund", "$46.97", "@_avocadofund", "—", 0, "INACTIVE"),
    ("Clawloan", "clawloan", "$15.16", "@Clawloan", "—", 0, "INACTIVE"),
    ("Micro Credit Project", "micro-credit-project", "$11.00", "@microcredittoken", "—", 0, "INACTIVE"),
]

SPECIAL_INFRA = [
    ("Symbiotic", "symbiotic", "Collateral Markets", "$442,498,730.22", "@symbioticfi", "https://symbiotic.fi", "Multi-asset collateral restaking engine"),
    ("EulerDebt", "eulerdebt", "Secondary Debt Markets", "$3,922.60", "@eulerfinance", "https://euler.finance", "Euler V2 secondary debt market tokenization")
]


def render_deep_dive():
    md = []
    md.append("# Subject Category Deep-Dive: Uncollateralized Lending & Composable Credit\n")
    md.append("**Analysed:** 2026-09-10 · **Window:** 2026-06-11 → 2026-09-10 (90 days)")
    md.append("**Market Universe:** 18 Uncollateralized Lending protocols + 2 Related Debt/Collateral Markets")
    md.append("**Category Total TVL:** $292,442,412 (Led by Pareto Credit at $226.2M, 77.4% share)\n")

    # Critical Finding
    md.append("## Executive Finding — Marketing Outliers in Low-TVL Credit\n")
    md.append("> **Prior research concluded this category *\"has no active marketing incumbent.\"* Credit Coop and Accountable contradict that.** Both are publishing outliers at $3.7M–$4.5M TVL — Credit Coop runs a biweekly deal-by-deal credit memo series (5 editions) plus a `$18M originated, $0 defaulted` tracker; Accountable runs a monthly Corporate Credit Health Index. Neither appeared in the prior 15-player roster.\n")
    md.append("**Category Boundary Clarification:**")
    md.append("- **Gearbox is not in this category.** DefiLlama classifies it under standard `Lending` at $22.4M TVL.")
    md.append("- TrueFi ($21.7k) and Goldfinch ($2.56M), the former giants of uncollateralized crypto credit, have largely ceased high-cadence public marketing.\n")
    md.append("---\n")

    # Tier 1: Collected Members (2)
    md.append("## Tier 1: Collected Active Outliers (2 Protocols)\n")
    md.append("These protocols have verified publishing footprints, active blogs, and confirmed repeating patterns in the registry.\n")

    for cp in COLLECTED_PLAYERS:
        md.append(f"### {cp['name']} — TVL {cp['tvl']}\n")
        md.append(f"- **X Handle:** [{cp['x_handle']}](https://x.com/{cp['x_handle'][1:]}) · **Blog:** [{cp['blog_url']}]({cp['blog_url']}) · **90d Artefacts:** {cp['artefacts_90d']}")
        md.append(f"- **Marketing Engine:** {cp['engine']}\n")
        
        md.append("#### Repeating Patterns")
        md.append("| Content category | Subcategory | The repeating post — the actual pattern | Timeline | Hook |")
        md.append("|---|---|---|---|---|")
        for pat in cp["patterns"]:
            md.append(f"| {pat[0]} | {pat[1]} | {pat[2]} | {pat[3]} | {pat[4]} |")
        
        md.append("\n#### What Vanna Can Do Here")
        md.append(f"| {cp['name']}'s pattern | Verdict | Vanna's version | Blocked by |")
        md.append("|---|---|---|---|")
        for vr in cp["vanna_verdict"]:
            md.append(f"| {vr[0]} | {vr[1]} | {vr[2]} | {vr[3]} |")
        md.append("\n---\n")

    # Tier 2: Uncollected Members (16)
    md.append("## Tier 2: Uncollected Category Members (16 Protocols)\n")
    md.append("These protocols are tracked in the census but have no verified repeating marketing patterns. All are marked `collection_status: PENDING`. Zero patterns are invented.\n")
    
    md.append("| Protocol | Slug | TVL (USD) | X Handle | Official Website | 90d Blog Artefacts | Collection Status | Note |")
    md.append("|---|---|---|---|---|:---:|:---:|---|")
    for pm in PENDING_MEMBERS:
        md.append(f"| **{pm[0]}** | `{pm[1]}` | {pm[2]} | {pm[3]} | [{pm[4]}]({pm[4]}) | {pm[5]} | `PENDING` | {pm[6]} |")
    
    md.append("\n---\n")

    # Special Infrastructure
    md.append("## Related Special Infrastructure\n")
    md.append("| Protocol | Slug | Category | TVL (USD) | X Handle | Role in Credit Stack |")
    md.append("|---|---|---|---|---|---|")
    for sp in SPECIAL_INFRA:
        md.append(f"| **{sp[0]}** | `{sp[1]}` | {sp[2]} | {sp[3]} | {sp[4]} | {sp[6]} |")

    md.append("\n---\n")
    md.append("*Provenance: Compiled deterministically from DefiLlama category endpoints and Tier 1 checkpoint data. Zero model calls.*")

    return "\n".join(md)


def main():
    doc_text = render_deep_dive()
    EXPORT_FILE.write_text(doc_text, encoding="utf-8")
    print(f"✅ Generated: {EXPORT_FILE.relative_to(Path('D:/new orchestration'))}")


if __name__ == "__main__":
    main()
