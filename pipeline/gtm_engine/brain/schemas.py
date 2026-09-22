"""
GTM Intelligence Brain - Relational Schemas & Entity Models (Phase 18).
Defines machine-readable contracts for every level of the GTM intelligence hierarchy.
"""

from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone


# -----------------------------------------------------------------------------
# Level 1: Market Category
# -----------------------------------------------------------------------------
@dataclass
class MarketCategoryRecord:
    category_id: str                   # e.g. "LENDING", "SPOT_AMM_DEX"
    name: str                          # Display name
    raw_defillama_categories: List[str]# Underlying DefiLlama categories mapped
    definition: str                    # Mechanical definition
    active_protocols_count: int
    tvl_usd: float
    fees_30d_usd: Optional[float]
    volume_30d_usd: Optional[float]
    trajectory_30d: str                # GROWING, FLAT, DECLINING
    trajectory_basis: str
    dominant_chains: List[str]
    snapshot_date: str
    evidence_tier: str = "OBSERVED"
    source_url: str = "https://api.llama.fi/protocols"


# -----------------------------------------------------------------------------
# Level 2: Player Profile
# -----------------------------------------------------------------------------
@dataclass
class PlayerProfileRecord:
    player_id: str                     # e.g. "aave", "morpho"
    name: str
    market_category: str
    selection_bucket: str              # MARKET_LEADER, FAST_GROWING, GTM_LEADER, CATEGORY_INNOVATOR, LOW_TVL_OUTLIER
    selection_rationale: str
    tvl_usd: float
    tvl_percentile_in_category: float
    momentum_30d_pct: Optional[float]
    chains: List[str]
    target_audiences: List[str]
    business_model: str
    core_job_to_be_done: str
    current_positioning: str
    historical_origin_summary: str
    token_ticker: Optional[str]
    token_economics: Optional[str]
    major_integrations: List[str]
    major_partnerships: List[str]
    institutional_strategy: str
    gtm_sophistication_score: float    # 1.0 - 10.0
    gtm_velocity_posts_per_week: float
    website: Optional[str]
    twitter_handle: Optional[str]
    confirmed_blog_urls: List[str] = field(default_factory=list)
    confirmed_forum_urls: List[str] = field(default_factory=list)
    confirmed_rss_urls: List[str] = field(default_factory=list)
    evidence_tier: str = "OBSERVED"
    confidence: str = "HIGH"


# -----------------------------------------------------------------------------
# Level 3: Product Inventory
# -----------------------------------------------------------------------------
@dataclass
class ProductRecord:
    product_id: str                    # e.g. "morpho-blue", "aave-v4-hub"
    player_id: str                     # Parent player ID
    product_name: str
    product_category: str              # ISOLATED_PRIMITIVE, CURATED_VAULT, POOLED_LENDING, etc.
    what_it_does: str
    target_audience: List[str]
    core_problem_solved: str
    monetization_mechanism: str
    differentiators: List[str]
    integrations: List[str]
    lifecycle_status: str              # PRODUCTION_ACTIVE, EXPANDING, LEGACY_MAINTENANCE
    marketing_importance_share_pct: float
    source_url: str
    evidence_tier: str = "OBSERVED"


# -----------------------------------------------------------------------------
# Level 4 & 5: Social / Content Corpus Post
# -----------------------------------------------------------------------------
@dataclass
class ContentPostRecord:
    post_id: str                       # Native tweet ID or content hash
    player_id: str
    product_id: str                    # Specific product or "BRAND_LEVEL"
    date: str                          # YYYY-MM-DD
    timestamp_utc: Optional[str]
    platform: str                      # X, OWNED_BLOG, GOVERNANCE_FORUM, NEWSLETTER
    x_url: Optional[str]               # Exact X status URL or "X_URL_NOT_OBSERVED"
    primary_source_url: Optional[str]  # Blog or forum URL
    post_type: str                     # original, reply, quote, repost, thread
    exact_text: str
    media_present: bool
    media_type: str                    # VIDEO, IMAGE, NONE
    market_category: str
    content_category: str              # PRODUCT, METRICS, PARTNERSHIP, SECURITY, GOVERNANCE, etc.
    content_subcategory: str           # NEW_PRODUCT, TVL_MILESTONE, STRESS_REPORT, etc.
    pattern_id: Optional[str]
    series_id: Optional[str]
    campaign_id: Optional[str]
    trigger: str                       # PARTNER_LIVE, MARKET_EVENT, CALENDAR, MILESTONE, etc.
    audience: List[str]
    purpose: str                       # AUTHORITY, ACTIVATION, RETENTION, TRUST
    hook_type: str
    proof_type: str
    cta: str
    funnel_stage: str                  # AWARENESS, CONSIDERATION, ACTIVATION, RETENTION
    engagement_metrics: Dict[str, Any] # views, likes, retweets
    evidence_status: str               # X_OBSERVED, PRIMARY_SOURCE_OBSERVED, INFERRED, UNKNOWN


# -----------------------------------------------------------------------------
# Level 6: Repeatable Pattern
# -----------------------------------------------------------------------------
@dataclass
class PatternRecord:
    pattern_id: str
    name: str
    market_categories: List[str]
    content_categories: List[str]
    trigger: str
    structure: List[str]               # Ordered sequential beats
    narrative_hook: str
    proof_mechanism: str
    cta_type: str
    target_audience: List[str]
    funnel_stage: str
    expected_objective: str
    observed_frequency: int
    players_using: List[str]
    sample_urls: List[str]
    evidence_status: str = "OBSERVED"
    confidence: str = "HIGH"


# -----------------------------------------------------------------------------
# Level 7: Recurring Series
# -----------------------------------------------------------------------------
@dataclass
class RecurringSeriesRecord:
    series_id: str
    series_name: str
    player_id: str
    market_category: str
    content_category: str
    content_subcategory: str
    cadence: str                       # WEEKLY, MONTHLY, BIWEEKLY
    first_observed: str
    latest_observed: str
    occurrence_count: int              # >= 4 required for series
    section_order: List[str]
    visual_template_type: str
    standard_cta: str
    target_audience: List[str]
    strategic_purpose: str
    source_urls: List[str]
    confidence: str = "HIGH"


# -----------------------------------------------------------------------------
# Level 8: Campaign & Stages
# -----------------------------------------------------------------------------
@dataclass
class CampaignStageRecord:
    stage_number: int
    stage_name: str                    # THESIS, TEASER, EDUCATION, TECH_PROOF, LAUNCH, PARTNER, RESULTS
    date: str
    x_url: Optional[str]
    primary_source_url: Optional[str]
    exact_hook: str
    functional_purpose: str
    evidence_status: str               # X_OBSERVED, PRIMARY_SOURCE_OBSERVED, NOT_OBSERVED


@dataclass
class CampaignRecord:
    campaign_id: str
    player_id: str
    product_id: str
    campaign_name: str
    market_category: str
    strategic_objective: str
    target_audience: List[str]
    core_narrative: str
    duration_days: int
    start_date: str
    end_date: Optional[str]
    status: str                        # COMPLETED, ACTIVE, PROPOSAL
    stages: List[CampaignStageRecord]
    confidence: str = "HIGH"


# -----------------------------------------------------------------------------
# Level 9: Reusable GTM Machine
# -----------------------------------------------------------------------------
@dataclass
class GTMMachineRecord:
    machine_id: str
    name: str
    objective: str
    trigger: str
    audience: List[str]
    stages: List[str]                  # Step-by-step structural machine
    content_types: List[str]
    channels: List[str]
    cta: str
    proof_requirements: str
    typical_cadence: str
    observed_players: List[str]
    observed_categories: List[str]
    sample_source_urls: List[str]
    working_conditions: str
    failure_modes: str
    confidence: str = "HIGH"


# -----------------------------------------------------------------------------
# Level 10: Market Whitespace & Strategic Opportunities
# -----------------------------------------------------------------------------
@dataclass
class MarketWhitespaceRecord:
    whitespace_id: str
    market_category: str
    saturated_mechanisms: List[str]
    underused_mechanisms: List[str]
    emerging_mechanisms: List[str]
    structural_void_description: str
    incumbent_failure_point: str
    unlocked_opportunity: str
    evidence_basis: List[str]


@dataclass
class GTMOpportunityRecord:
    opportunity_id: str
    market_signal: str
    target_audience: List[str]
    competitor_behavior_observed: str
    evidence_urls: List[str]
    market_gap: str
    vanna_relevance_and_moat: str
    recommended_gtm_machine_id: str
    campaign_concept_name: str
    expected_business_objective: str
    recommended_cta: str
    success_metric: str
    priority: str                      # P0, P1, P2
    claim_tier_safety_gate: str        # TESTNET_COMPLIANT, PROHIBITED_MAINNET


# -----------------------------------------------------------------------------
# Level 11: Evidence Graph & Audit
# -----------------------------------------------------------------------------
@dataclass
class EvidenceNode:
    claim_id: str
    claim_statement: str
    evidence_type: str                 # OBSERVED, INFERRED, UNKNOWN
    evidence_count: int
    source_urls: List[str]
    underlying_observed_facts: List[str]
    analytical_inference: Optional[str]
    verifying_tool_or_code: str
    confidence_level: str              # HIGH, MEDIUM, LOW


# -----------------------------------------------------------------------------
# Level 12: Execution & Outcome Feedback Loop
# -----------------------------------------------------------------------------
@dataclass
class ExecutionOutcomeRecord:
    execution_id: str
    opportunity_id: str
    campaign_name: str
    content_text: str
    channel: str
    published_date: str
    impressions: int
    engagements: int
    clicks: int
    conversions: int
    actual_vs_expected_variance: str
    strategic_learning_lesson: str
    updated_intelligence_signal: str
