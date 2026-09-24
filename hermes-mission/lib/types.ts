/**
 * Types for the captured fixture and the payloads embedded as JSON strings inside
 * message content. Shapes mirror the observed sources: Nostr kind-9 events,
 * spend-ledger.json, and vertex-calls.jsonl.
 */

/* ------------------------------------------------------------------ primitives */

export type ArcId = "capital-efficiency" | "risk-relief" | "agentic-credit";

export type StageId =
  | "kickoff"
  | "research"
  | "bucket"
  | "pitches"
  | "debate"
  | "ruling"
  | "visual"
  | "gate"
  | "review";

export type StageStatus = "done" | "active" | "failed" | "skipped" | "not_reached";

export type Outcome = "shipped" | "killed" | "died" | "running";

export type Tier = "A" | "B" | "C";

export type ModelId = "gemini-2.5-flash" | "gemini-2.5-pro";

export type AgentStatus = "connected" | "thinking" | "idle" | "errored";

export type Momentum = "rising" | "peaked" | "dead" | "evergreen";

export type Verdict = "ship" | "reject_all" | "revise";

export type ReviewStatus =
  | "awaiting_review"
  | "changes_requested"
  | "approved"
  | "rejected";

/** STEPPS — the six-axis virality self-score. */
export interface Stepps {
  social_currency: number;
  triggers: number;
  emotion: number;
  public: number;
  practical_value: number;
  stories: number;
}

/* ---------------------------------------------------------------- nostr events */

export interface NostrEvent {
  id: string;
  kind: number;
  created_at: number;
  pubkey: string;
  tags: string[][];
  content: string;
}

/* ------------------------------------------------------------------- vertex log */

export interface CallUsage {
  promptTokenCount: number;
  cachedContentTokenCount: number;
  candidatesTokenCount: number;
}

export interface VertexCall {
  seq: number;
  ts: string;
  stage: StageId;
  agent: string;
  model: ModelId;
  /** Set when the requested model did not exist and was silently rewritten. */
  rewritten_from: string | null;
  usage: CallUsage;
  cost_usd: number;
}

/* ---------------------------------------------------------------------- agents */

export interface Agent {
  id: string;
  role: string;
  distinct: string;
  pubkey: string;
  status: AgentStatus;
  working_on: string;
  log: string;
  arc?: ArcId;
  hue?: string;
  arcline?: string;
}

/* -------------------------------------------------------------------- payloads */

export interface SourceEngagement {
  likes: number;
  replies: number;
}

export interface TrendSource {
  platform: string;
  url: string;
  /** null when the tool was unavailable. Null is not zero. */
  engagement: SourceEngagement | null;
}

export interface WhyItWorks {
  hook_category: string;
  hook_text: string;
  format: string;
  virality_pattern: string;
  stepps: Stepps;
  engagement_shape: string;
}

export interface Trend {
  id: string;
  headline: string;
  type: string;
  momentum: Momentum;
  window_hours: number;
  sources: TrendSource[];
  why_it_works: WhyItWorks;
  vanna_hooks: string[];
  evidence: string;
}

export interface CompetitorContent {
  handle: string;
  posted: string;
  format: string;
  note: string;
}

export interface ResearchPayload {
  scanned_at: string;
  trends: Trend[];
  competitor_content: CompetitorContent[];
  keywords: string[];
  notes: string;
}

export interface Claim {
  text: string;
  tier: Tier;
  source: string;
}

export interface VisualBriefDatum {
  label: string;
  value: string;
  note: string;
}

export interface VisualBrief {
  type: string;
  headline: string;
  emphasis_phrase: string;
  subhead: string;
  data: VisualBriefDatum[];
  disclaimer: string;
}

export interface DraftPost {
  platform: string;
  template: string;
  hook: string;
  body: string;
  thread: string[];
  persona: string;
  claims: Claim[];
  stepps_self_score: Stepps;
  visual_brief: VisualBrief;
}

export interface DraftPayload {
  arc: ArcId;
  trend_id: string;
  rationale: string;
  posts: DraftPost[];
}

export interface ScoreBreakdown {
  claim_integrity: number;
  hook: number;
  arc_coherence: number;
  voice: number;
  trend_fit: number;
  virality: number;
}

export interface ArcScore {
  arc: ArcId;
  total: number;
  breakdown: ScoreBreakdown;
  killer_issue: string;
}

export interface RulingWinner {
  arc: ArcId;
  platform: string;
  final_hook: string;
  final_body: string;
  final_thread: string[];
  visual_brief: VisualBrief;
}

export interface Graft {
  took: string;
  from: ArcId;
  why: string;
}

export interface ClaimAuditRow {
  claim: string;
  strategist_said: Tier;
  you_found: Tier;
  verified_against: string;
}

export interface Ruling {
  verdict: Verdict;
  winner: RulingWinner | null;
  scores: ArcScore[];
  graft: Graft | null;
  claim_audit: ClaimAuditRow[];
  send_back_notes: string;
}

export interface GatePayload {
  gate: "pass" | "fail";
  violations: string[];
  checks: string[];
  note: string;
}

/* ------------------------------------------------------------------ run records */

export interface Stage {
  id: StageId;
  label: string;
  status: StageStatus;
  started: number | null;
  ended: number | null;
}

export interface Boundary {
  open_evidence: string;
  close_evidence: string | null;
  /** Anything other than "high" renders as a weak (rose) inference chip. */
  confidence: "high" | "open" | "low";
  note: string;
}

export interface Review {
  draft_id: string;
  status: ReviewStatus;
  channel: string;
  sent_at: number;
  reviewer_reply: string | null;
  replied_at?: number;
  path: string;
}

export interface Artifact {
  file: string;
  size: string;
  type: string;
  headline: string;
  emphasis: string;
  subhead: string;
  disclaimer: string;
  rendered_at: string;
}

export interface Died {
  stage: string;
  agent: string;
  error: string;
  log: string;
}

export interface Run {
  key: string;
  label: string;
  inferred: boolean;
  boundary: Boundary;
  started: number;
  ended: number | null;
  trigger: string;
  bucket: string;
  outcome: Outcome;
  quiet_since?: number;
  died?: Died;
  stages: Stage[];
  messages: NostrEvent[];
  research: ResearchPayload | null;
  ruling: Ruling | null;
  gate: GatePayload | null;
  review: Review | null;
  artifact: Artifact | null;
  calls: VertexCall[];
}

/* --------------------------------------------------------------- the fixture */

export interface MissionData {
  CHANNEL: string;
  RELAY: string;
  CAP_USD: number;
  SPENT_USD?: number | null; // null = no published rate for a model that ran
  POSTS_TOTAL?: number;      // real count of channel posts across runs
  LEDGER_STARTED: string;
  AGENTS: Agent[];
  AGENT_BY_KEY: Record<string, string>;
  RUNS: Run[];
  STAGE_ORDER: StageId[];
  HUE: Record<ArcId, string>;
}

/* ------------------------------------------------------- defensive parse union */

/** Result of parsing message content. `broken` is never dropped — it is rendered raw. */
export type ParseResult =
  | { kind: "prose"; value: null }
  | { kind: "json"; value: unknown }
  | { kind: "broken"; value: null; error: string };

/** Result of classifying a parsed message. */
export type Classified =
  | { type: "prose" }
  | { type: "error" }
  | { type: "broken"; error: string }
  | { type: "research"; value: ResearchPayload }
  | { type: "draft"; value: DraftPayload }
  | { type: "ruling"; value: Ruling }
  | { type: "gate"; value: GatePayload }
  | { type: "json"; value: unknown };

/* ------------------------------------------------------------- component props */

export type DebateEdges = "rail" | "matrix" | "both";

export interface MissionControlProps {
  debateEdges?: DebateEdges;
  capUsd?: number;
  arcPalette?: string[];
}
