/**
 * Authoritative Mission Data & 13-Agent Registry for Vanna Protocol GTM Operating System.
 */
import type {
  Agent,
  ArcId,
  DraftPayload,
  MissionData,
  ModelId,
  NostrEvent,
  ResearchPayload,
  Ruling,
  Run,
  Stage,
  StageId,
  StageStatus,
  VertexCall,
} from "./types";

const CHANNEL = "31098616-3d0b-4202-86b4-96bfd36680cd";
// Empty means same origin. A hardcoded localhost made the deployed
// dashboard probe the viewer's own machine.
const RELAY = "";
const CAP_USD = 10.0;
const LEDGER_STARTED = "2026-08-08T16:28:05Z";

const HUE: Record<ArcId, string> = {
  "capital-efficiency": "#4ADE9B",
  "risk-relief": "#A98CFF",
  "agentic-credit": "#A98CFF",
};

/** All 13 Specialized Vanna GTM OS Agents */
const AGENTS: Agent[] = [
  {
    id: "agent-01-intelligence-scout",
    role: "Multi-Source Parallel Intelligence Scout (Twitter, Reddit, DeFiLlama, Stellar Horizon RPC, Telegram, Docs)",
    distinct: "Queries 6 live intelligence channels simultaneously in parallel; hash-deduplicates signals",
    pubkey: "pubkey-01-intelligence-scout",
    status: "connected",
    working_on: "Live streaming Stellar Protocol 20 ledger & Blend v2 pool state",
    log: "Parallel poll cycle complete · 4 fresh signals ingested · 0 duplicates"
  },
  {
    id: "agent-02-opportunity-selector",
    role: "Multi-Track Opportunity Selector & Portfolio Evaluator",
    distinct: "Evaluates candidates across 7 dimensions (0.0 - 1.0) with diversity filtering",
    pubkey: "pubkey-02-opportunity-selector",
    status: "connected",
    working_on: "Selected: Composable 10x Credit Layer on Blend v2 Pools (Score: 0.84/1.0)",
    log: "Diversity gate passed · 3-track portfolio selected across A1, A2, A3"
  },
  {
    id: "agent-03-gtm-strategist",
    role: "GTM Strategist (Reasoning Brain: Gemini 3.8 Flash)",
    distinct: "Formulates strategic narrative anchors with 4 decision-quality gates",
    pubkey: "pubkey-03-gtm-strategist",
    status: "thinking",
    working_on: "STRAT-SIG-OPP_BLEND_V2 · Audience: A2 Quantitative Traders & Yield Farmers",
    log: "Passed AudienceFitGate, ProductStageFitGate, ClaimConsistencyGate"
  },
  {
    id: "agent-04-machine-library",
    role: "GTM Machine Library Engine",
    distinct: "Authoritative catalog of 10 empirical GTM machines; enforces stage sequences",
    pubkey: "pubkey-04-machine-library",
    status: "connected",
    working_on: "Verified: Sub-Second Risk Telemetry Education Machine (MACH_04)",
    log: "Machine verified ELIGIBLE · Minimum evidence threshold satisfied"
  },
  {
    id: "agent-05-campaign-series",
    role: "Campaign & Series Engines",
    distinct: "Determines structural vehicle (RECURRING_SERIES) and recurrence tiering",
    pubkey: "pubkey-05-campaign-series",
    status: "connected",
    working_on: "The Soroban Composable Yield Series (Episode #1)",
    log: "Classified as RECURRING_SERIES · Recurrence tier: RECURRING_SYSTEM"
  },
  {
    id: "agent-06-channel-adapter",
    role: "Content Creator & Channel Adapter (Brain: Gemini 3.8 Flash)",
    distinct: "Genuinely platform-native copy for X, LinkedIn, Reddit with smart thread splitting",
    pubkey: "pubkey-06-channel-adapter",
    status: "connected",
    working_on: "Generated 3 X thread chunks (<280 chars) + LinkedIn Brief + Reddit Deep Dive",
    log: "Passed 34-point humanizer checklist · Zero em dashes · Claim citations intact"
  },
  {
    id: "agent-07-creative-director",
    role: "Creative Director System (Metaphor Diversity Manager)",
    distinct: "Compiles 9-point visual blueprints rotating across 5 physical concept families",
    pubkey: "pubkey-07-creative-director",
    status: "connected",
    working_on: "Physical Metaphor: OPTICAL_REFRACTION (Smoked glass optical prism)",
    log: "Rotated family from Hydrodynamic to Optical Refraction · Zero repetition"
  },
  {
    id: "agent-08-visual-synthesizer",
    role: "Visual Synthesizer Engine (Model Garden: Gemini 3.1 Flash Image)",
    distinct: "Synthesizes 100% textless geometric physical assets with Vanna tokens (#07020D)",
    pubkey: "pubkey-08-visual-synthesizer",
    status: "connected",
    working_on: "vanna_visual_blend_v2_composable.png (1.36 MB, Textless)",
    log: "Render verified · 78% negative space · Dual blooms (#471485, #5E0D46)"
  },
  {
    id: "agent-09-video-engine",
    role: "Video Production Engine (Remotion + Veo 3.1 + EBU R128 Audio)",
    distinct: "Asynchronous 5-act product film render queue with dynamic voiceover ducking",
    pubkey: "pubkey-09-video-engine",
    status: "connected",
    working_on: "VannaProductFilm41s (41.00s / 1,230 frames / 1080p Full HD)",
    log: "Async job completed in queue · Dialogue normalized to -14 LUFS · -12dB sidechain"
  },
  {
    id: "agent-10-reviewer-firewall",
    role: "Pre-Delivery Reviewer (Brain: Gemini 3.8 Flash Adversarial Gate)",
    distinct: "Senior CMO, Risk Officer, and Art Director firewall; halts at WAITING_FOR_HUMAN",
    pubkey: "pubkey-10-reviewer-firewall",
    status: "connected",
    working_on: "",
    log: ""
  },
  {
    id: "agent-11-dispatch-worker",
    role: "Approved Dispatch Worker (Multi-Channel Publisher)",
    distinct: "Dispatches approved packages to X, LinkedIn, Reddit with persistent retry queue",
    pubkey: "pubkey-11-dispatch-worker",
    status: "connected",
    working_on: "Dispatched to X, LinkedIn, Reddit · Status: ALL_PUBLISHED",
    log: "Canonical URLs verified · Seeded performance records with NULL != 0"
  },
  {
    id: "agent-12-telegram-gateway",
    role: "Telegram Gateway & Mobile Callback Listener",
    distinct: "Interactive phone approval card handler; authenticates Advay Anand (5501720892)",
    pubkey: "pubkey-12-telegram-gateway",
    status: "connected",
    working_on: "Approved by Founder (TG: 5501720892)",
    log: "Callback query 'act:approve' captured · Auto-dispatched batch"
  },
  {
    id: "agent-13-learning-engine",
    role: "Closed-Loop Learning Engine & Bayesian RL Bandit",
    distinct: "Ingests post-distribution conversions; Bayesian UCB prior for low sample sizes",
    pubkey: "pubkey-13-learning-engine",
    status: "connected",
    working_on: "Ingested 8 sandbox deployments · Weight updated: 1.00 -> 1.15",
    log: "Sample size N >= 3 satisfied · Synced updated weight to patterns.jsonl"
  }
];

const AGENT_BY_KEY: Record<string, string> = Object.fromEntries(
  AGENTS.map((a) => [a.pubkey, a.id]),
);

// Published rates, from ai.google.dev/gemini-api/docs/pricing (paid tier,
// read 2026-09-24). The previous values here were gemini-2.5-flash's rates
// wearing gemini-3.8-flash's name — 0.30/2.50 against a real 0.75/3.75 — so
// every figure this produced was under-reported by 2.5x. The image entry was
// worse: it priced an image model per *token*, and image calls return no
// token counts, so it always evaluated to zero.
//
// pipeline/state/model_rates.json is the same table for the server side and
// carries the per-call media rates, including Veo, which dominates a full
// run's cost and has no representation here at all.
const PRICE: Record<string, { in: number; cached: number; out: number }> = {
  "gemini-3.8-flash": { in: 0.75e-6, cached: 0.1875e-6, out: 3.75e-6 },
};

const STAGE_ORDER: StageId[] = [
  "kickoff",
  "research",
  "bucket",
  "pitches",
  "debate",
  "ruling",
  "visual",
  "gate",
  "review",
];

const DEFAULT_VISUAL_BRIEF = {
  type: "editorial_hero" as const,
  headline: "The Optical Refraction of Capital",
  emphasis: "10x Margin",
  emphasis_phrase: "10x Margin",
  subhead: "Isolated SmartAccount Sandboxes on Stellar Soroban",
  layout_archetype: "editorial_hero",
  visual_metaphor: "Precision-cut smoked glass optical prism",
  color_palette: ["#07020D", "#471485", "#5E0D46"],
  focal_object: "Prism and Refracted Filaments",
  composition_family: "asymmetric_split",
  spatial_hierarchy: "hero center",
  disclaimer: "Stellar Testnet Only",
  data: []
};

export const MISSION_DATA: MissionData = {
  CHANNEL,
  RELAY,
  CAP_USD,
  LEDGER_STARTED,
  HUE,
  AGENTS,
  AGENT_BY_KEY,
  STAGE_ORDER,
  RUNS: []
};
