/** Types mirror the real sources, not a convenient invention.
 *
 *  - messages are raw Nostr kind-9 events off the relay
 *  - calls come from pipeline/logs/vertex-calls.jsonl
 *  - research / draft / ruling arrive as JSON embedded in message text, which
 *    is why every one of them is optional and may fail to parse
 */

export type StageId =
  | 'kickoff'
  | 'research'
  | 'bucket'
  | 'pitches'
  | 'debate'
  | 'ruling'
  | 'visual'
  | 'gate'
  | 'review';

/** `skipped` and `not_reached` are deliberately distinct from `failed`. A stage
 *  the run never got to is not a stage that broke, and collapsing the two hides
 *  where a run actually stopped.
 *
 *  These strings match the source data exactly. Do not "tidy" them — the
 *  renderer looks up styles by this value, and a mismatch renders nothing. */
export type StageStatus = 'done' | 'active' | 'failed' | 'skipped' | 'not_reached';

export type ArcId =
  | 'capital-efficiency'
  | 'risk-relief'
  | 'agentic-credit';

export type Outcome = 'shipped' | 'killed' | 'died' | 'running';

export interface Stage {
  id: StageId;
  label: string;
  status: StageStatus;
  /** unix seconds; null while a stage has not started or not finished */
  started: number | null;
  ended: number | null;
}

export interface NostrMessage {
  id: string;
  kind: number;
  created_at: number;
  pubkey: string;
  tags: string[][];
  content: string;
}

export interface Usage {
  promptTokenCount: number;
  /** A large share of input is cached. Folding this into the total makes cost
   *  look far worse than it is, so it stays separate everywhere. */
  cachedContentTokenCount: number;
  candidatesTokenCount: number;
  thoughtsTokenCount?: number;
}

export interface VertexCall {
  seq: number;
  ts: string;
  stage: StageId;
  agent: string;
  model: string;
  /** Set when the proxy swapped an unavailable model id for one this project
   *  serves. Surfaced rather than hidden — a silent substitution is not
   *  auditable. */
  rewritten_from: string | null;
  usage: Usage;
  cost_usd: number;
}

export interface Agent {
  id: string;
  role: string;
  distinct: string;
  pubkey: string;
  status: 'connected' | 'thinking' | 'idle' | 'errored' | string;
  working_on: string;
  log?: string;
  arc?: ArcId;
  arcline?: string;
}

export interface Claim {
  text: string;
  tier: 'A' | 'B' | 'C';
  source: string;
}

export interface Score {
  arc: ArcId;
  total: number;
  breakdown: Record<string, number>;
  killer_issue: string;
}

export interface ClaimAuditRow {
  claim: string;
  strategist_said: string;
  you_found: string;
  verified_against: string;
}

export interface Ruling {
  verdict: 'ship' | 'revise' | 'reject_all';
  winner?: Record<string, unknown> | null;
  scores?: Score[];
  graft?: { took: string; from: string; why: string } | null;
  claim_audit?: ClaimAuditRow[];
  send_back_notes?: string;
}

export interface GateResult {
  pass: boolean;
  platform?: string;
  block_count?: number;
  warn_count?: number;
  violations?: { rule?: string; detail?: string }[];
}

export interface ReviewState {
  draft_id?: string;
  status?: 'awaiting_review' | 'changes_requested' | 'approved' | 'rejected' | string;
  reply?: string | null;
  sent_at?: string;
}

export interface Run {
  key: string;
  label: string;
  /** True when run boundaries were derived from message timestamps rather than
   *  recorded. The UI must say so — inference presented as fact is a lie the
   *  operator cannot check. */
  inferred: boolean;
  boundary?: string;
  started: number;
  ended: number | null;
  trigger: string;
  bucket: string | null;
  outcome: Outcome;
  quiet_since?: number | null;
  stages: Stage[];
  messages: NostrMessage[];
  research?: unknown | null;
  ruling?: Ruling | null;
  gate?: GateResult | null;
  review?: ReviewState | null;
  artifact?: { path?: string; disclaimer?: string } | null;
  calls: VertexCall[];
}

export interface MissionData {
  CHANNEL: string;
  RELAY: string;
  CAP_USD: number;
  LEDGER_STARTED: string;
  AGENTS: Agent[];
  AGENT_BY_KEY: Record<string, string>;
  RUNS: Run[];
  STAGE_ORDER: StageId[];
  HUE: Record<ArcId, string>;
}
