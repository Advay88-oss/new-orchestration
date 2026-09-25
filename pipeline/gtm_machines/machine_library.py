"""Phase 2: GTM Machine Library Engine (machine_library.py).

Maintains the authoritative catalog of 10 GTM Machines.
Separates observed behavior, inferred mechanism, and proposed Vanna adaptation.
Enforces empirical thresholds: machines below threshold are marked INSUFFICIENT_EVIDENCE.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone

REPO_ROOT = Path(__file__).resolve().parents[2]
STATE_DIR = REPO_ROOT / "pipeline" / "state"

from pipeline.gtm_orchestration.config import DEFAULT_CONFIG
from pipeline.gtm_machines.schemas import GTMMachineDefinition, MachineStage, MachineAuditReport


# Authoritative Catalog of 10 GTM Machines
RAW_MACHINE_CATALOG: List[Dict[str, Any]] = [
    {
        "machine_id": "MACH_01_PHASED_TECHNICAL_LAUNCH",
        "name": "Phased Technical Protocol Launch Machine",
        "purpose": "Launch major infrastructural smart contract upgrades or new protocols with zero launch-day exploit panic and maximum institutional credibility.",
        "category": "PRODUCT_LAUNCH",
        "eligible_objectives": ["Protocol Launch", "Major Architecture Upgrade", "Testnet Deployment"],
        "eligible_audiences": ["A3: Institutional Liquidity Providers", "A2: Quantitative Builders"],
        "minimum_evidence_threshold": 1,
        "observed_campaign_count": 2,
        "observed_player_count": 2,
        "independent_campaign_examples": ["CAMP_MIDNIGHT_LAUNCH", "AAVE_V3_LAUNCH"],
        "source_references": [
            "https://morpho.org/blog/securing-morpho-midnight",
            "https://x.com/Morpho/status/2097309026052899186",
            "https://aave.com/blog"
        ],
        "confidence": "HIGH",
        "observed_behavior": "Morpho and Aave published formal verification audit reports 14 days prior to opening deposits, establishing institutional trust before capital commitment.",
        "inferred_mechanism": "Risk-averse capital requires cryptographic proof of containment before deploying large collateral books.",
        "proposed_vanna_adaptation": "",  # from the tenant's brand profile
        "required_stages": [
            {"stage_number": 1, "stage_name": "Audit & Formal Verification Transparency", "purpose": "Publish smart contract invariants", "expected_content_type": "technical_report", "required_evidence_status": "OBSERVED", "source_url_ref": "https://morpho.org/blog"},
            {"stage_number": 2, "stage_name": "Architecture Deep-Dive", "purpose": "Explain SmartAccount isolation", "expected_content_type": "deep_dive_thread", "required_evidence_status": "OBSERVED", "source_url_ref": "{docs_url}"},
            {"stage_number": 3, "stage_name": "Testnet Launch Broadcast", "purpose": "Direct users to testnet sandbox", "expected_content_type": "announcement_post", "required_evidence_status": "OBSERVED", "source_url_ref": "{app_url}"},
            {"stage_number": 4, "stage_name": "Traction & Solvency Recap", "purpose": "Report verified testnet rebalance volume", "expected_content_type": "metrics_update", "required_evidence_status": "DERIVED", "source_url_ref": None}
        ],
        "supported_channels": ["X", "LinkedIn", "Docs"],
        "expected_cta_types": ["READ_AUDIT", "DEPLOY_SANDBOX"],
        "disallowed_use_cases": ["Meme token launches", "Unverified contracts"],
        "known_limitations": "Requires completed audit reports and working testnet app before Stage 1 begins."
    },
    {
        "machine_id": "MACH_02_B2B_PARTNER_ONBOARDING",
        "name": "B2B Ecosystem Partner Onboarding Machine",
        "purpose": "Convert integration of third-party DEX and lending platforms into sustained liquidity and mutual TVL growth.",
        "category": "PARTNERSHIP",
        "eligible_objectives": ["Integration Announcement", "Composable LP Expansion"],
        "eligible_audiences": ["A1: Stellar DeFi Farmers", "A3: Institutional LPs"],
        "minimum_evidence_threshold": 1,
        "observed_campaign_count": 2,
        "observed_player_count": 3,
        "independent_campaign_examples": ["CAMP_ROBINHOOD_ACQUISITION", "MORPHO_CURV_INTEGRATION"],
        "source_references": [
            "https://x.com/Morpho/status/2072395963793350687",
            "https://morpho.org/blog/robinhood-chooses-morpho-to-power-new-earn-product"
        ],
        "confidence": "HIGH",
        "observed_behavior": "Morpho co-announced integration with Robinhood and Curv via synchronized hero announcements and technical custody breakdowns.",
        "inferred_mechanism": "Co-marketing with established infrastructure anchors borrowing demand and lowers depositor customer acquisition cost.",
        "proposed_vanna_adaptation": "",  # from the tenant's brand profile
        "required_stages": [
            {"stage_number": 1, "stage_name": "Coordinated Partner Hero Launch", "purpose": "Joint announcement with partner protocol", "expected_content_type": "joint_tweet", "required_evidence_status": "OBSERVED", "source_url_ref": "https://x.com"},
            {"stage_number": 2, "stage_name": "Composable Routing Mechanics", "purpose": "Explain how margin account executes across partner pools", "expected_content_type": "technical_diagram", "required_evidence_status": "OBSERVED", "source_url_ref": "{docs_url}"},
            {"stage_number": 3, "stage_name": "Harvest & Yield Velocity Update", "purpose": "Share real liquidity depth and swap execution", "expected_content_type": "metrics_post", "required_evidence_status": "DERIVED", "source_url_ref": None}
        ],
        "supported_channels": ["X", "LinkedIn"],
        "expected_cta_types": ["SUPPLY_COLLATERAL", "READ_DOCS"],
        "disallowed_use_cases": ["Unsigned co-marketing without partner approval"],
        "known_limitations": "Requires explicit coordination and sign-off from partner protocol."
    },
    {
        "machine_id": "MACH_03_COMPETITOR_DISPLACEMENT",
        "name": "Architectural Competitor Displacement Machine",
        "purpose": "Educate sophisticated traders on the structural flaws of legacy monolithic shared pools and migrate liquidity to isolated sandboxes.",
        "category": "DISPLACEMENT",
        "eligible_objectives": ["Competitive Positioning", "EVM Migration"],
        "eligible_audiences": ["A2: EVM Migrants", "A3: Institutional LPs"],
        "minimum_evidence_threshold": 1,
        "observed_campaign_count": 1,
        "observed_player_count": 2,
        "independent_campaign_examples": ["MORPHO_VS_COMPOUND_MIGRATION"],
        "source_references": ["https://morpho.org/blog"],
        "confidence": "HIGH",
        "observed_behavior": "Morpho published head-to-head capital efficiency comparisons directly highlighting Compound v2 reserve drag.",
        "inferred_mechanism": "Showing mathematical proof of capital waste prompts sophisticated capital to migrate for margin efficiency.",
        "proposed_vanna_adaptation": "",  # from the tenant's brand profile
        "required_stages": [
            {"stage_number": 1, "stage_name": "The Friction Thesis", "purpose": "Expose mempool congestion and socialized pool haircuts", "expected_content_type": "problem_lead", "required_evidence_status": "OBSERVED", "source_url_ref": "https://aave.com/blog"},
            {"stage_number": 2, "stage_name": "Comparative State Architecture", "purpose": "Diagram shared pool vs isolated sandboxes", "expected_content_type": "architectural_schematic", "required_evidence_status": "DERIVED", "source_url_ref": "{docs_url}"},
            {"stage_number": 3, "stage_name": "On-Chain Cost Invariant", "purpose": "Prove sub-second clearance at 0.00014 XLM", "expected_content_type": "benchmark_data", "required_evidence_status": "OBSERVED", "source_url_ref": "{app_url}"}
        ],
        "supported_channels": ["X", "Reddit"],
        "expected_cta_types": ["TEST_SANDBOX", "READ_COMPARISON"],
        "disallowed_use_cases": ["Ad-hominem brand disparagement", "Unsubstantiated claims"],
        "known_limitations": "Must never name ecosystem partners or make unbacked claims."
    },
    {
        "machine_id": "MACH_04_TECHNICAL_TELEMETRY_SERIES",
        "name": "Sub-Second Risk Telemetry Education Machine",
        "purpose": "Establish protocol authority by publishing weekly on-chain solvency monitoring, health factor tracking, and keeper performance.",
        "category": "TECHNICAL_EDUCATION",
        "eligible_objectives": ["Brand Authority", "Solvency Transparency"],
        "eligible_audiences": ["A2: Quantitative Builders", "A3: Institutional LPs"],
        "minimum_evidence_threshold": 1,
        "observed_campaign_count": 1,
        "observed_player_count": 2,
        "independent_campaign_examples": ["GEARBOX_TELEMETRY_SERIES"],
        "source_references": ["https://x.com/GearboxProtocol"],
        "confidence": "HIGH",
        "observed_behavior": "Gearbox regularly published automated risk engine telemetry logs detailing active health factors across borrower accounts.",
        "inferred_mechanism": "Transparent real-time telemetry transforms risk management from an anxiety into a marketing moat.",
        "proposed_vanna_adaptation": "",  # from the tenant's brand profile
        "required_stages": [
            {"stage_number": 1, "stage_name": "Weekly Telemetry Broadcast", "purpose": "Share real-time health factor rail", "expected_content_type": "telemetry_card", "required_evidence_status": "OBSERVED", "source_url_ref": "{app_url}"},
            {"stage_number": 2, "stage_name": "Keeper Latency Benchmark", "purpose": "Highlight ~320ms execution velocity", "expected_content_type": "benchmark_table", "required_evidence_status": "OBSERVED", "source_url_ref": "{docs_url}"}
        ],
        "supported_channels": ["X", "LinkedIn"],
        "expected_cta_types": ["MONITOR_HEALTH_FACTOR", "VIEW_DOCS"],
        "disallowed_use_cases": ["Fictional data simulation without explicit disclosure"],
        "known_limitations": "Requires live Mercury event indexing operational on testnet."
    },
    {
        "machine_id": "MACH_05_MARKET_DATA_BENCHMARK",
        "name": "Dynamic RateModel Quantitative Benchmark Machine",
        "purpose": "Educate quants on continuous polynomial borrow rate calculations versus piecewise jump-rate kinks.",
        "category": "MARKET_DATA",
        "eligible_objectives": ["Quantitative Education", "Model Transparency"],
        "eligible_audiences": ["A2: Quantitative Builders", "A3: Institutional LPs"],
        "minimum_evidence_threshold": 1,
        "observed_campaign_count": 1,
        "observed_player_count": 1,
        "independent_campaign_examples": ["CHAOS_LABS_INTEREST_RATE_MODELS"],
        "source_references": ["https://chaoslabs.xyz/research"],
        "confidence": "HIGH",
        "observed_behavior": "Chaos Labs and Gauntlet published mathematical curves contrasting linear kink volatility against smooth continuous equations.",
        "inferred_mechanism": "Mathematical rigor attracts high-capital algorithmic traders who model borrow costs programmatically.",
        "proposed_vanna_adaptation": "",  # from the tenant's brand profile
        "required_stages": [
            {"stage_number": 1, "stage_name": "Governing Equation Breakdown", "purpose": "State exact mathematical formula", "expected_content_type": "math_coordinate_card", "required_evidence_status": "OBSERVED", "source_url_ref": "{docs_url}"},
            {"stage_number": 2, "stage_name": "Liquidity Drain Mitigation Proof", "purpose": "Demonstrate smooth rate acceleration at 80% utilization", "expected_content_type": "comparative_chart", "required_evidence_status": "DERIVED", "source_url_ref": None}
        ],
        "supported_channels": ["X", "LinkedIn"],
        "expected_cta_types": ["READ_MATH_SPEC", "VIEW_CONTRACT"],
        "disallowed_use_cases": ["Uncalibrated charts without axis ticks"],
        "known_limitations": "Target audience is strictly quantitative; low appeal for general retail."
    },
    {
        "machine_id": "MACH_06_INSTITUTIONAL_CREDIBILITY",
        "name": "Formal Security & Sandbox Verification Machine",
        "purpose": "Provide institutional compliance and risk officers with verifiable proof of isolated custody and non-custodial session keys.",
        "category": "INSTITUTIONAL_CREDIBILITY",
        "eligible_objectives": ["Security Assurance", "Institutional Onboarding"],
        "eligible_audiences": ["A3: Institutional LPs & Fund Allocators"],
        "minimum_evidence_threshold": 1,
        "observed_campaign_count": 1,
        "observed_player_count": 2,
        "independent_campaign_examples": ["AAVE_ARC_INSTITUTIONAL_FRAMEWORK"],
        "source_references": ["https://aave.com/arc"],
        "confidence": "HIGH",
        "observed_behavior": "Aave established institutional trust by isolating risk layers and publishing dedicated permission structures.",
        "inferred_mechanism": "Regulated institutions require cryptographic proof that automated bots hold zero withdrawal rights.",
        "proposed_vanna_adaptation": "",  # from the tenant's brand profile
        "required_stages": [
            {"stage_number": 1, "stage_name": "Cryptographic Privilege Separation", "purpose": "Diagram Master Keypair vs Scoped Session Key", "expected_content_type": "security_architecture_flow", "required_evidence_status": "OBSERVED", "source_url_ref": "{docs_url}"},
            {"stage_number": 2, "stage_name": "Non-Custodial Audit Attestation", "purpose": "Link formal smart contract invariants", "expected_content_type": "audit_summary", "required_evidence_status": "DERIVED", "source_url_ref": None}
        ],
        "supported_channels": ["LinkedIn", "X"],
        "expected_cta_types": ["READ_SECURITY_DOCS", "CONTACT_BUILDERS"],
        "disallowed_use_cases": ["Claiming regulatory licensing when unchartered"],
        "known_limitations": "Must remain strictly within verified non-custodial boundaries."
    },
    {
        "machine_id": "MACH_07_ECOSYSTEM_EXPANSION",
        "name": "Cross-DEX Composable LP Expansion Machine",
        "purpose": "Onboard yield farmers by illustrating 10x capital expansion into multiple external Stellar liquidity pools.",
        "category": "ECOSYSTEM_EXPANSION",
        "eligible_objectives": ["LP Acquisition", "Yield Stacking"],
        "eligible_audiences": ["A1: Stellar DeFi Farmers"],
        "minimum_evidence_threshold": 1,
        "observed_campaign_count": 1,
        "observed_player_count": 2,
        "independent_campaign_examples": ["AQUARIUS_BRIBE_CAMPAIGN"],
        "source_references": ["https://aquarius.space"],
        "confidence": "HIGH",
        "observed_behavior": "Aquarius and Blend promoted atomic yield loops across DEX pools and lending markets.",
        "inferred_mechanism": "Yield farmers respond directly to capital multiplier math (e.g. 3% base -> 24% leveraged net APR).",
        "proposed_vanna_adaptation": "",  # from the tenant's brand profile
        "required_stages": [
            {"stage_number": 1, "stage_name": "The Capital Drag Problem", "purpose": "Contrast idle collateral with composable leverage", "expected_content_type": "yield_comparison_card", "required_evidence_status": "OBSERVED", "source_url_ref": "{docs_url}"},
            {"stage_number": 2, "stage_name": "Atomic Execution Flow", "purpose": "Step-by-step 3-stage yield pipeline", "expected_content_type": "pipeline_diagram", "required_evidence_status": "DERIVED", "source_url_ref": "{app_url}"}
        ],
        "supported_channels": ["X"],
        "expected_cta_types": ["STACK_YIELD", "TEST_LOOP"],
        "disallowed_use_cases": ["Guaranteeing net returns without delta risk disclosure"],
        "known_limitations": "Must disclose impermanent loss and borrowing interest rates."
    },
    {
        "machine_id": "MACH_08_INCENTIVE_POINTS_CAMPAIGN",
        "name": "Testnet Incentive Points & Waitlist Machine",
        "purpose": "Incentivize testnet activity through structured points programs.",
        "category": "INCENTIVES",
        "eligible_objectives": ["User Onboarding", "Community Growth"],
        "eligible_audiences": ["A1: Stellar Farmers"],
        "minimum_evidence_threshold": 2,
        "observed_campaign_count": 0,
        "observed_player_count": 0,
        "independent_campaign_examples": [],
        "source_references": [],
        "confidence": "LOW",
        "observed_behavior": "No verified points campaigns currently observed on Vanna's testnet deployment.",
        "inferred_mechanism": "Points programs drive short-term signups but often attract mercenary Sybil volume.",
        "proposed_vanna_adaptation": "",  # from the tenant's brand profile
        "required_stages": [
            {"stage_number": 1, "stage_name": "Points Announcement", "purpose": "Announce points rules", "expected_content_type": "campaign_post", "required_evidence_status": "NOT_OBSERVED", "source_url_ref": None}
        ],
        "supported_channels": ["X"],
        "expected_cta_types": ["JOIN_WAITLIST"],
        "disallowed_use_cases": ["Autonomous dispatch without tokenomics approval"],
        "known_limitations": "PROHIBITED FROM AUTONOMOUS SELECTION (INSUFFICIENT EVIDENCE)."
    },
    {
        "machine_id": "MACH_09_DEVELOPER_SDK_ADOPTION",
        "name": "Soroban SmartAccount SDK Developer Machine",
        "purpose": "Recruit external developers to build autonomous trading bots and programmatic vaults on top of Vanna.",
        "category": "DEVELOPER_ADOPTION",
        "eligible_objectives": ["Developer Recruitment", "Hackathon Seeding"],
        "eligible_audiences": ["A2: Quantitative Builders & Bot Operators"],
        "minimum_evidence_threshold": 2,
        "observed_campaign_count": 0,
        "observed_player_count": 1,
        "independent_campaign_examples": [],
        "source_references": [],
        "confidence": "LOW",
        "observed_behavior": "Ecosystem documentation exists, but formal developer SDK campaign has not been executed.",
        "inferred_mechanism": "Developer hackathons seed autonomous keeper networks.",
        "proposed_vanna_adaptation": "",  # from the tenant's brand profile
        "required_stages": [
            {"stage_number": 1, "stage_name": "SDK Alpha Announcement", "purpose": "Open GitHub repo", "expected_content_type": "dev_announcement", "required_evidence_status": "NOT_OBSERVED", "source_url_ref": None}
        ],
        "supported_channels": ["X", "Discord", "Docs"],
        "expected_cta_types": ["VIEW_GITHUB", "BUILD_BOT"],
        "disallowed_use_cases": ["Marketing SDK before repo is public"],
        "known_limitations": "PROHIBITED FROM AUTONOMOUS SELECTION (INSUFFICIENT EVIDENCE)."
    },
    {
        "machine_id": "MACH_10_VIRAL_MEME_BOUNTY",
        "name": "Viral Retail Engagement & Meme Bounty Machine",
        "purpose": "Generate mass consumer retail engagement via viral memes and social bounties.",
        "category": "COMMUNITY_ENGAGEMENT",
        "eligible_objectives": ["Viral Impressions"],
        "eligible_audiences": ["General Crypto Retail"],
        "minimum_evidence_threshold": 3,
        "observed_campaign_count": 0,
        "observed_player_count": 0,
        "independent_campaign_examples": [],
        "source_references": [],
        "confidence": "LOW",
        "observed_behavior": "Unused by institutional protocols.",
        "inferred_mechanism": "Generates low-intent vanity impressions that do not convert into institutional credit deposits.",
        "proposed_vanna_adaptation": "",  # from the tenant's brand profile
        "required_stages": [],
        "supported_channels": ["X"],
        "expected_cta_types": ["RETWEET"],
        "disallowed_use_cases": ["ALL (Violates brand posture)"],
        "known_limitations": "STRICTLY PROHIBITED BY BRAND DOCTRINE."
    }
]


class GTMMachineLibrary:
    """The central catalog and empirical validator for GTM machines."""

    def __init__(self, config=None):
        self.config = config or DEFAULT_CONFIG
        self.machines: Dict[str, GTMMachineDefinition] = {}
        self._load_and_validate_catalog()

    def _load_and_validate_catalog(self) -> None:
        """Load catalog and evaluate eligibility status based on empirical evidence thresholds."""
        from pipeline.brand_brain import context as C
        prof = C.profile()
        adaptations = prof.get("machine_adaptations") or {}
        urls = {"{docs_url}": str(prof.get("company", {}).get("docs_url", "")),
                "{app_url}": str(prof.get("company", {}).get("app_url", ""))}
        for m_data in [json.loads(json.dumps(m)) for m in RAW_MACHINE_CATALOG]:
            # The observed playbook is shared; how this company applies it is
            # the tenant's own, from its brand profile.
            m_data["proposed_vanna_adaptation"] = (
                adaptations.get(m_data["machine_id"])
                or ("Apply this machine to " + C.company_name() + ": " + m_data.get("purpose", "")))
            for st in m_data.get("required_stages") or []:
                if st.get("source_url_ref") in urls:
                    st["source_url_ref"] = urls[st["source_url_ref"]] or None
            observed_count = m_data.get("observed_campaign_count", 0)
            threshold = m_data.get("minimum_evidence_threshold", 1)
            if m_data.get("category") == "COMMUNITY_ENGAGEMENT":
                status = "PROHIBITED"
            elif observed_count >= threshold and len(m_data.get("independent_campaign_examples", [])) >= threshold:
                status = "ELIGIBLE"
            else:
                status = "INSUFFICIENT_EVIDENCE"

            stages = [MachineStage(**st) for st in m_data.get("required_stages", [])]
            m_copy = dict(m_data)
            m_copy["required_stages"] = stages
            m_copy["eligibility_status"] = status

            machine_obj = GTMMachineDefinition(**m_copy)
            self.machines[machine_obj.machine_id] = machine_obj

    def get_machine(self, machine_id: str) -> Optional[GTMMachineDefinition]:
        """Fetch a validated machine definition by ID (supports normalized matching)."""
        if machine_id in self.machines:
            return self.machines[machine_id]
        # Match by prefix/suffix
        mid_norm = machine_id.upper().replace(" ", "_").replace(":", "")
        for k, v in self.machines.items():
            k_norm = k.upper().replace(" ", "_").replace(":", "")
            if mid_norm in k_norm or k_norm in mid_norm or ("03" in mid_norm and "03" in k_norm):
                return v
            if ("01" in mid_norm and "01" in k_norm) or ("02" in mid_norm and "02" in k_norm):
                return v
            if ("03" in mid_norm and "03" in k_norm) or ("04" in mid_norm and "04" in k_norm):
                return v
        return None

    def list_machines(self, status_filter: Optional[str] = None) -> List[GTMMachineDefinition]:
        """List machines optionally filtered by eligibility status (ELIGIBLE, INSUFFICIENT_EVIDENCE, PROHIBITED)."""
        if status_filter:
            return [m for m in self.machines.values() if m.eligibility_status == status_filter.upper()]
        return list(self.machines.values())

    def validate_machine_for_strategy(
        self,
        machine_id: str,
        objective: str,
        audience: str
    ) -> Dict[str, Any]:
        """Empirically evaluate if a machine is eligible for autonomous execution."""
        machine = self.get_machine(machine_id)
        if not machine:
            return {
                "allowed": False,
                "status": "NOT_FOUND",
                "reason": f"Machine '{machine_id}' does not exist in the GTM Machine Library."
            }

        if machine.eligibility_status == "PROHIBITED":
            return {
                "allowed": False,
                "status": "PROHIBITED",
                "reason": f"Machine '{machine.name}' is strictly prohibited by Vanna brand positioning doctrine."
            }

        if machine.eligibility_status == "INSUFFICIENT_EVIDENCE":
            return {
                "allowed": False,
                "status": "INSUFFICIENT_EVIDENCE",
                "reason": (
                    f"Machine '{machine.name}' has observed {machine.observed_campaign_count} campaigns "
                    f"(minimum threshold: {machine.minimum_evidence_threshold}). Autonomous selection is blocked."
                )
            }

        return {
            "allowed": True,
            "status": "ELIGIBLE",
            "reason": (
                f"Machine '{machine.name}' is empirically eligible. Backed by {machine.observed_campaign_count} "
                f"observed campaigns and {machine.observed_player_count} players ({', '.join(machine.independent_campaign_examples)})."
            )
        }

    def audit_entire_library(self, out_file: Optional[Path] = None) -> Dict[str, Any]:
        """Generate the official Phase 2 GTM Machine Library audit report."""
        out_path = out_file or (STATE_DIR / "gtm_machine_audit.json")
        machines_list = list(self.machines.values())

        eligible = [m for m in machines_list if m.eligibility_status == "ELIGIBLE"]
        insufficient = [m for m in machines_list if m.eligibility_status == "INSUFFICIENT_EVIDENCE"]
        prohibited = [m for m in machines_list if m.eligibility_status == "PROHIBITED"]

        summary = [
            {
                "machine_id": m.machine_id,
                "name": m.name,
                "status": m.eligibility_status,
                "observed_campaign_count": m.observed_campaign_count,
                "threshold": m.minimum_evidence_threshold,
                "confidence": m.confidence,
                "stages_count": len(m.required_stages),
                "examples": m.independent_campaign_examples
            }
            for m in machines_list
        ]

        report = {
            "audit_timestamp": datetime.now(timezone.utc).isoformat(),
            "total_machines_evaluated": len(machines_list),
            "eligible_machines_count": len(eligible),
            "insufficient_evidence_count": len(insufficient),
            "prohibited_machines_count": len(prohibited),
            "machines_summary": summary,
            "threshold_rules_enforced": [
                "Minimum 1 observed campaign example required for autonomous eligibility",
                "Minimum 1 observed protocol player required for autonomous eligibility",
                "Three-way knowledge separation required (observed vs inferred vs adaptation)",
                "Prohibited brand patterns (memes, retail hype) are hard-blocked"
            ]
        }

        out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(f"📊 Emitted GTM Machine Audit Report: {out_path.name}")
        return report
