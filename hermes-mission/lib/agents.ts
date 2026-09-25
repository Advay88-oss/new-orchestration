/**
 * The agents, in the order a run reaches them — one list for every view.
 *
 * The count used to be the literal "13" in the sidebar, the page title and
 * the agents view. Since then the thirteen grew specialists with their own
 * journal rows (the market analyst, the Motion Director, the creative judge,
 * the Coach), and the dashboard kept saying 13. Everything that counts or
 * lists agents reads it from here, so adding one is one line.
 *
 * `learns` says what the agent learns from and how; `fixed` says why an agent
 * deliberately does not. Mirrors `pipeline/gtm_os/agent_runtime.py`.
 * Client-safe: no fs, no server imports.
 */

export type GtmAgentRole = 'reasoning' | 'director' | 'image' | 'meme' | 'video' | 'none';

export interface AgentDef {
  id: string;
  code: string;
  name: string;
  role: GtmAgentRole;
  track: 'intelligence' | 'creative' | 'governance' | 'learning';
  learns?: string;
  fixed?: string;
}

export const AGENTS: AgentDef[] = [
  { id: 'A01_intelligence_scout', code: 'A01', name: 'Intelligence Scout', role: 'none',
    track: 'intelligence',
    learns: 'Which sources and news queries bring usable signals (A02 grades + founder); 30% kept for exploration' },
  { id: 'A02_market_analyst', code: 'A02b', name: 'Market Analyst', role: 'reasoning',
    track: 'intelligence',
    learns: 'Its forecast accuracy, checked against later scrapes, never against approval' },
  { id: 'A02_opportunity_selector', code: 'A02', name: 'Opportunity Selector', role: 'reasoning',
    track: 'intelligence', learns: 'Topics the founder approved or killed' },
  { id: 'A03_gtm_strategist', code: 'A03', name: 'GTM Strategist', role: 'reasoning',
    track: 'intelligence', learns: 'Winning pillars, approved hooks, founder corrections' },
  { id: 'A04_machine_library', code: 'A04', name: 'GTM Machine Library', role: 'none',
    track: 'intelligence', learns: 'Which GTM machine wins (Thompson sampling)' },
  { id: 'A05_campaign_engine', code: 'A05', name: 'Campaign & Series Engine', role: 'none',
    track: 'intelligence', fixed: 'Deterministic series planning' },
  { id: 'A06_channel_adapter', code: 'A06', name: 'Content Creator & Channel Adapter', role: 'reasoning',
    track: 'creative', learns: 'Approved posts and founder corrections' },
  { id: 'A07_creative_director', code: 'A07', name: 'Creative Director System', role: 'reasoning',
    track: 'creative', learns: 'Visual archetypes (Thompson sampling, losers retire)' },
  { id: 'A14_motion_director', code: 'A14', name: 'Motion Director', role: 'director',
    track: 'creative',
    learns: 'Layouts and motion styles (Thompson, no repeats); approved posters and clips' },
  { id: 'A08_visual_synthesis', code: 'A08', name: 'Visual Synthesis Engine', role: 'image',
    track: 'creative', learns: 'Founder-approved posters, shown first as references' },
  { id: 'A09_video_production', code: 'A09', name: 'Video Production Engine', role: 'video',
    track: 'creative', learns: 'Approved and rejected clips' },
  { id: 'A15_creative_judge', code: 'A15', name: 'Creative Judge', role: 'reasoning',
    track: 'creative', learns: "Judges against the rulebook and the Coach's learned rules" },
  { id: 'A10_reviewer_firewall', code: 'A10', name: 'Pre-Delivery Reviewer Firewall', role: 'reasoning',
    track: 'governance', fixed: 'Checks every claim against the brand brain; never learns from approval' },
  { id: 'A11_dispatch_worker', code: 'A11', name: 'Approved Dispatch Worker', role: 'none',
    track: 'governance', fixed: 'Never publishes on its own' },
  { id: 'A12_telegram_gateway', code: 'A12', name: 'Telegram Gateway & Listener', role: 'none',
    track: 'governance', fixed: 'Must never learn to persuade the reviewer' },
  { id: 'A13_learning_engine', code: 'A13', name: 'Closed-Loop Learning Engine', role: 'reasoning',
    track: 'learning', learns: 'Founder decisions into the snapshot every agent reads' },
  { id: 'A16_coach', code: 'A16', name: 'Coach', role: 'director',
    track: 'learning',
    learns: "Writes rules from each run; its rules' record decides which stay (founder can veto)" },
];

export const AGENT_COUNT = AGENTS.length;
export const LEARNING_COUNT = AGENTS.filter((a) => a.learns).length;
