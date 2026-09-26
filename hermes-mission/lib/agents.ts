/**
 * The agents, in the order a run reaches them — one list for every view.
 *
 * Ten specialists and two independent judges (2026-09-26). Seventeen ids
 * became twelve: four pairs were one job under two names. `aliases` are the
 * former ids — old run journals still carry them, and every view folds them
 * into the agent that owns the job now. The judges stay separate from what
 * they judge, so the maker never grades its own work.
 *
 * `learns` says what the agent learns from; `fixed` says why it deliberately
 * does not. Mirrors `pipeline/gtm_os/agent_runtime.py` (AGENT_ROLES, MERGED).
 * Client-safe: no fs, no server imports.
 */

export type GtmAgentRole = 'reasoning' | 'director' | 'image' | 'meme' | 'video' | 'none';

export type AgentTrack = 'intelligence' | 'creative' | 'delivery' | 'judges';

export interface AgentDef {
  id: string;
  code: string;
  name: string;
  role: GtmAgentRole;
  track: AgentTrack;
  judge?: boolean;
  aliases?: string[];
  absorbs?: string;
  learns?: string;
  fixed?: string;
}

export const AGENTS: AgentDef[] = [
  { id: 'A01_intelligence_scout', code: '01', name: 'Intelligence Scout', role: 'none',
    track: 'intelligence',
    learns: 'Which sources and news queries bring usable signals (analyst grades + founder); 30% kept for exploration' },
  { id: 'A02_market_analyst', code: '02', name: 'Market Analyst', role: 'reasoning',
    track: 'intelligence',
    learns: 'Its forecast accuracy, checked against later scrapes, never against approval' },
  { id: 'A02_opportunity_selector', code: '03', name: 'Opportunity Selector', role: 'reasoning',
    track: 'intelligence', learns: 'Topics the founder approved or killed' },
  { id: 'A03_gtm_strategist', code: '04', name: 'GTM Strategist & Planner', role: 'reasoning',
    track: 'intelligence', aliases: ['A04_machine_library', 'A05_campaign_engine'],
    absorbs: 'Machine library and campaign engine',
    learns: 'Winning pillars and GTM machines (Thompson sampling), approved hooks, founder corrections' },
  { id: 'A06_channel_adapter', code: '05', name: 'Copywriter', role: 'reasoning',
    track: 'creative', learns: 'Approved posts and founder corrections; writes only from sourced brand facts' },
  { id: 'A07_creative_director', code: '06', name: 'Creative Director', role: 'director',
    track: 'creative', aliases: ['A14_motion_director'], absorbs: 'Motion Director',
    learns: 'Layouts, motion styles and archetypes (Thompson, no repeats); approved posters and clips' },
  { id: 'A08_visual_synthesis', code: '07', name: 'Poster Designer', role: 'image',
    track: 'creative', learns: 'Founder-approved posters, retrieved by topic from the brand brain' },
  { id: 'A09_video_production', code: '08', name: 'Video Producer', role: 'video',
    track: 'creative', learns: 'Approved and rejected clips' },
  { id: 'A11_delivery', code: '09', name: 'Delivery', role: 'none',
    track: 'delivery', aliases: ['A11_dispatch_worker', 'A12_telegram_gateway'],
    absorbs: 'Dispatch worker and Telegram gateway',
    fixed: 'Never publishes on its own, and never learns to persuade the reviewer' },
  { id: 'A13_learning_engine', code: '10', name: 'Learning & Coach', role: 'director',
    track: 'delivery', aliases: ['A16_coach'], absorbs: 'Coach',
    learns: "Founder decisions into what every agent reads; its own rules' record decides which stay" },
  { id: 'A10_reviewer_firewall', code: 'J1', name: 'Reviewer & Fact Checker', role: 'reasoning',
    track: 'judges', judge: true,
    fixed: 'Checks every claim against the brand brain; never learns from approval' },
  { id: 'A15_creative_judge', code: 'J2', name: 'Creative Judge', role: 'reasoning',
    track: 'judges', judge: true,
    learns: "Judges against the rulebook and the Coach's learned rules" },
];

/** Former id -> the agent that owns the job now. */
export const ALIAS: Record<string, string> = Object.fromEntries(
  AGENTS.flatMap((a) => [[a.id, a.id], ...(a.aliases ?? []).map((x) => [x, a.id])]),
);

export const AGENT_COUNT = AGENTS.length;
export const SPECIALIST_COUNT = AGENTS.filter((a) => !a.judge).length;
export const JUDGE_COUNT = AGENTS.filter((a) => a.judge).length;
export const LEARNING_COUNT = AGENTS.filter((a) => a.learns).length;
