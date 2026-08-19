/**
 * Captured fixture for Mission Control, converted verbatim from the original
 * `mission-data.js`. Shapes match the observed sources exactly: Nostr kind-9
 * events, pipeline/state/spend-ledger.json, pipeline/logs/vertex-calls.jsonl,
 * research / draft / ruling payloads embedded as JSON in message text.
 *
 * PORT NOTE: no value in this file was changed. Only declarations gained types.
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
const RELAY = "http://127.0.0.1:3000";
const CAP_USD = 10.0;
const LEDGER_STARTED = "2026-08-08T16:28:05Z";

const HUE: Record<ArcId, string> = {
  "capital-efficiency": "oklch(0.52 0.12 258)",
  "risk-relief": "oklch(0.50 0.10 168)",
  "agentic-credit": "oklch(0.56 0.12 58)",
};

const AGENTS: Agent[] = [
  { id: "conductor", role: "Opens a run, dispatches, calls the bucket, closes",
    distinct: "The only one who decides whether to post at all",
    pubkey: "0879a27506498637f1a4c1d2e8b0937c5511ae0d4c9e2f7b3a6d8051f2c7e9b4",
    status: "connected", working_on: "idle — waiting on schedule 17:00Z",
    log: 'subscribed to channel 31098616 · last turn ok (0.4s)' },
  { id: "trend-scout", role: "Live research, why posts perform, keywords, competitor content",
    distinct: "Produces evidence, never copy",
    pubkey: "b31f0c9a77e4d2185ac6039f8e1b47d0225c6a9e3f8017d4b2c5e9a06f3d18cc",
    status: "connected", working_on: "idle",
    log: 'subscribed to channel 31098616 · x_search tool unavailable (401) on last 2 runs' },
  { id: "strategist-capital-efficiency", arc: "capital-efficiency", hue: HUE["capital-efficiency"],
    arcline: "Your collateral is doing one job. It should be doing six.",
    role: "Competing narrative arc", distinct: "Competes with the other two",
    pubkey: "4a2e91c0b83d7f156092ae4c7d31b805f6e2a940c1d873be5027f4a1c9e60b3d",
    status: "thinking", working_on: "R-08-05 · drafting pitch (turn 2)",
    log: 'subscribed to channel 31098616 · agent_returned outcome="ok" turns=2' },
  { id: "strategist-risk-relief", arc: "risk-relief", hue: HUE["risk-relief"],
    arcline: "Leverage is easy. Not getting liquidated is the hard part.",
    role: "Competing narrative arc", distinct: "Competes with the other two",
    pubkey: "9f4c02a7e5b18d36c0472f9a1e8b53d07c26a4f90b1d8e357246af0c9b3e15d8",
    status: "thinking", working_on: "R-08-05 · drafting pitch (turn 1)",
    log: 'subscribed to channel 31098616 · agent_returned outcome="ok" turns=1' },
  { id: "strategist-agentic-credit", arc: "agentic-credit", hue: HUE["agentic-credit"],
    arcline: "Agents can pay. Agents can't borrow.",
    role: "Competing narrative arc", distinct: "Competes with the other two",
    pubkey: "2c7b19e04af3d8265913c0e7b4a2f85d6109c3ae7f2b40d859e1a6c30fb4297e",
    status: "errored", working_on: "R-08-05 · pitch emitted truncated JSON",
    log: 'agent_returned outcome="error" err="response exceeded max_tokens mid-object"' },
  { id: "editorial-judge", role: "Scores drafts, picks one or kills them all",
    distinct: "Default posture is rejection",
    pubkey: "7e5a3c9016b2d84f7c035e1a9b6d2408f3c7e05a2b9d146c80e3f7a5b1c92d06",
    status: "idle", working_on: "waiting on 3rd pitch",
    log: 'subscribed to channel 31098616 · idle 7m' },
  { id: "visual-creator", role: "Winning brief → 1080×1080 card",
    distinct: "Produces the only image artifact",
    pubkey: "df02a6c48b1e93750a2c6f8d31b590e47a2c08f6d5b93e1470a8c2f6b0d34e19",
    status: "idle", working_on: "idle",
    log: 'subscribed to channel 31098616 · renderer ok · last render 2026-08-08T18:41Z' },
];

const AGENT_BY_KEY: Record<string, string> = Object.fromEntries(
  AGENTS.map((a) => [a.pubkey, a.id]),
);

/* ---------------------------------------------------------------- cost model */
const PRICE: Record<ModelId, { in: number; cached: number; out: number }> = {
  "gemini-2.5-flash": { in: 0.30e-6, cached: 0.075e-6, out: 2.50e-6 },
  "gemini-2.5-pro":   { in: 1.25e-6, cached: 0.3125e-6, out: 10.0e-6 },
};
let CALL_SEQ = 0;
const call = (
  ts: string,
  stage: StageId,
  agent: string,
  model: ModelId,
  p: number,
  cached: number,
  out: number,
  rewritten_from: string | null = null,
): VertexCall => {
  const pr = PRICE[model];
  const cost = (p - cached) * pr.in + cached * pr.cached + out * pr.out;
  return {
    seq: ++CALL_SEQ, ts, stage, agent, model, rewritten_from,
    usage: { promptTokenCount: p, cachedContentTokenCount: cached, candidatesTokenCount: out },
    cost_usd: Math.round(cost * 1e6) / 1e6,
  };
};
const F: ModelId = "gemini-2.5-flash",
  P: ModelId = "gemini-2.5-pro";

/* ------------------------------------------------------------------ messages */
let MSG_SEQ = 0;
const hex64 = (n: number): string => {
  let s = "";
  let x = n * 2654435761 % 4294967296;
  for (let i = 0; i < 8; i++) { x = (x * 1103515245 + 12345) % 4294967296; s += x.toString(16).padStart(8, "0"); }
  return s.slice(0, 64);
};
const msg = (
  agent: string,
  created_at: number,
  content: string | object,
  parent?: string,
): NostrEvent => {
  const id = hex64(++MSG_SEQ);
  const tags: string[][] = [["h", CHANNEL]];
  if (parent) tags.push(["e", parent, "", "reply"]);
  return {
    id, kind: 9, created_at,
    pubkey: AGENTS.find((a) => a.id === agent)!.pubkey,
    tags,
    content: typeof content === "string" ? content : JSON.stringify(content),
  };
};

const T = (iso: string): number => Math.floor(Date.parse(iso) / 1000);

/* ==========================================================================
   R-08-04 — shipped. The strategists genuinely argued (4 cross-replies).
   ========================================================================== */
const r4Research: ResearchPayload = {
  scanned_at: "2026-08-08T16:31:12Z",
  trends: [
    { id: "looping-fatigue-thread", headline: "Looping yield threads are getting ratioed by liquidation screenshots",
      type: "crypto-native", momentum: "rising", window_hours: 36,
      sources: [
        { platform: "x", url: "https://x.com/i/status/1876...", engagement: { likes: 4120, replies: 388 } },
        { platform: "x", url: "https://x.com/i/status/1877...", engagement: null },
      ],
      why_it_works: {
        hook_category: "contrarian", hook_text: "Everyone posting APY. Nobody posting the liquidation.",
        format: "thread", virality_pattern: "counter-narrative",
        stepps: { social_currency: 7, triggers: 9, emotion: 6, public: 8, practical_value: 4, stories: 5 },
        engagement_shape: "reply-heavy, low link clicks",
      },
      vanna_hooks: ["Show the liquidation price before the APY", "Hedged leverage as the boring answer"],
      evidence: "top reply, 900 likes: \"post your health factor or it didn't happen\"" },
    { id: "agent-payments-standard", headline: "Agent-payment standards shipping faster than agent-credit primitives",
      type: "mainstream-culture", momentum: "peaked", window_hours: 72,
      sources: [{ platform: "linkedin", url: "https://linkedin.com/posts/...", engagement: { likes: 1290, replies: 74 } }],
      why_it_works: {
        hook_category: "gap-in-the-market", hook_text: "Agents can pay. Agents can't borrow.",
        format: "single", virality_pattern: "named-gap",
        stepps: { social_currency: 8, triggers: 5, emotion: 4, public: 6, practical_value: 7, stories: 3 },
        engagement_shape: "quote-tweet heavy, strong link clicks",
      },
      vanna_hooks: ["Credit rails are the missing half of agent commerce"],
      evidence: "3 competitor posts in 48h using the same gap framing" },
    { id: "collateral-idle-stat", headline: "\"Idle collateral\" framing resurfacing in lending-protocol marketing",
      type: "competitor-move", momentum: "evergreen", window_hours: 168,
      sources: [{ platform: "x", url: "https://x.com/i/status/1878...", engagement: null }],
      why_it_works: {
        hook_category: "reframe", hook_text: "Your collateral has one job.",
        format: "quote-card", virality_pattern: "restatement",
        stepps: { social_currency: 6, triggers: 4, emotion: 3, public: 5, practical_value: 8, stories: 2 },
        engagement_shape: "saves over replies",
      },
      vanna_hooks: ["Six jobs, one deposit"],
      evidence: "two competitors ran near-identical copy within 4 days" },
  ],
  competitor_content: [
    { handle: "@protocol_a", posted: "2026-08-07", format: "thread", note: "same idle-collateral reframe, 2.1k likes" },
    { handle: "@protocol_b", posted: "2026-08-06", format: "quote-card", note: "liquidation-shame angle, underperformed" },
  ],
  keywords: ["health factor", "hedged leverage", "idle collateral", "agent credit", "liquidation price", "delta neutral"],
  notes: "x_search returned engagement for 2 of 4 source URLs; the rest are recorded as null rather than zero. LinkedIn engagement is first-party from the competitor page, not API.",
};

const r4CE: DraftPayload = {
  arc: "capital-efficiency", trend_id: "collateral-idle-stat",
  rationale: "The idle-collateral reframe is evergreen and two competitors just validated it within four days. That is not a reason to avoid it — it is a reason to say the harder version of it. Their version stops at \"put your collateral to work\"; ours names the six jobs and shows the accounting. The trend-scout's note that saves outrun replies on this format supports a quote-card, not a thread.",
  posts: [{
    platform: "x", template: "reframe-ladder", hook: "Your collateral is doing one job",
    body: "Your collateral is doing one job.\n\nOn Vanna testnet it does six: margin, hedge, yield base, borrow capacity, liquidation buffer, and settlement float — from a single deposit.\n\nSame deposit. Six positions of work. That is the whole pitch.",
    thread: ["Most lending UIs make you choose one. That choice is a UI artifact, not a market constraint.",
      "Six jobs from one deposit is not leverage stacking. It is one collateral pool with six claims priced against it."],
    persona: "P1",
    claims: [
      { text: "A single deposit backs six simultaneous position types on testnet", tier: "A", source: "file 08, testnet spec §2.1" },
      { text: "Competing lending UIs force a single-use collateral choice", tier: "B", source: "file 08, competitor survey" },
    ],
    stepps_self_score: { social_currency: 7, triggers: 4, emotion: 3, public: 6, practical_value: 8, stories: 2 },
    visual_brief: { type: "stat-card", headline: "One deposit. Six jobs.", emphasis_phrase: "Six jobs",
      subhead: "Vanna testnet collateral model",
      data: [{ label: "Positions per deposit", value: "6", note: "testnet" }, { label: "Deposits required", value: "1", note: "" }],
      disclaimer: "Testnet only. Not investment advice." },
  }],
};

const r4RR: DraftPayload = {
  arc: "risk-relief", trend_id: "looping-fatigue-thread",
  rationale: "The rising trend is not the yield thread — it is the ratio. Liquidation screenshots are outperforming APY posts by an order of magnitude in replies. The scout logged reply-heavy, low-link-click shape, which means the audience wants to argue about risk, not click through to a product. An arc that leads with the liquidation price and buries the yield is the only one that survives the reply section. Capital-efficiency's arc is the exact copy the ratio is punishing this week: it asks the reader to admire an accounting trick while their timeline is full of people getting liquidated. Agentic-credit's arc is real but early — it is a category post for a category that does not yet have a buyer.",
  posts: [{
    platform: "x", template: "cold-open-counter", hook: "Everyone is posting APY",
    body: "Everyone is posting APY. Nobody is posting the liquidation price.\n\nLeverage is easy. Not getting liquidated is the hard part — and it is the part every dashboard hides two clicks deep.\n\nVanna testnet puts the liquidation price on the same line as the yield. If the number is ugly, you should see it before you sign, not after.",
    thread: ["A health factor you have to go looking for is a health factor you will not look at.",
      "The boring version of this product is the honest one: hedged leverage, liquidation price above the fold, no APY without its downside printed next to it.",
      "If that makes the yield look smaller, the yield was always that size."],
    persona: "P2",
    claims: [
      { text: "Liquidation price is displayed alongside yield on the position screen", tier: "A", source: "file 08, testnet UI spec §4" },
      { text: "Most competing dashboards place health factor behind a secondary view", tier: "B", source: "file 08, competitor survey" },
      { text: "Hedged positions reduce liquidation frequency", tier: "B", source: "file 08, backtest note (testnet data only)" },
    ],
    stepps_self_score: { social_currency: 6, triggers: 9, emotion: 7, public: 8, practical_value: 6, stories: 5 },
    visual_brief: { type: "quote-card", headline: "Leverage is easy.", emphasis_phrase: "Not getting liquidated is the hard part.",
      subhead: "Liquidation price, above the fold",
      data: [{ label: "Clicks to health factor", value: "0", note: "Vanna testnet" }, { label: "Typical competitor", value: "2", note: "surveyed 4 dashboards" }],
      disclaimer: "Testnet only. Not investment advice." },
  }],
};

const r4AC: DraftPayload = {
  arc: "agentic-credit", trend_id: "agent-payments-standard",
  rationale: "The payments-standard trend has peaked, which means the gap it exposes is now legible to people who were not paying attention last month. That is the moment to name the gap, not after. The risk here is that this reads as a category post with no buyer — I accept that and lean on it: the post is a claim about where credit rails go, not a product ask.",
  posts: [{
    platform: "linkedin", template: "named-gap", hook: "Agents can pay",
    body: "Agents can pay. Agents can't borrow.\n\nEvery agent-payment standard shipping this quarter assumes the agent already holds the money. None of them describe what happens when it doesn't — no credit line, no collateral it can post, no counterparty willing to underwrite a process.\n\nThat gap is the interesting half. Vanna testnet is where we are testing the boring version of it: an agent with a collateral position and a liquidation price it can read.",
    thread: [],
    persona: "P3",
    claims: [
      { text: "Current agent-payment standards presume pre-funded balances", tier: "A", source: "file 08, standards review §1" },
      { text: "No shipped standard defines agent-side credit underwriting", tier: "A", source: "file 08, standards review §3" },
    ],
    stepps_self_score: { social_currency: 8, triggers: 5, emotion: 4, public: 6, practical_value: 7, stories: 3 },
    visual_brief: { type: "infographic", headline: "Agents can pay. Agents can't borrow.", emphasis_phrase: "can't borrow",
      subhead: "The missing half of agent commerce",
      data: [{ label: "Payment standards shipped", value: "4", note: "2026 H1" }, { label: "Credit standards shipped", value: "0", note: "" }],
      disclaimer: "Testnet only. Not investment advice." },
  }],
};

const r4Ruling: Ruling = {
  verdict: "ship",
  winner: { arc: "risk-relief", platform: "x", final_hook: "Everyone is posting APY",
    final_body: "Everyone is posting APY. Nobody is posting the liquidation price.\n\nLeverage is easy. Not getting liquidated is the hard part — and it is the part every dashboard hides two clicks deep.\n\nVanna testnet puts the liquidation price on the same line as the yield. If the number is ugly, you should see it before you sign, not after.",
    final_thread: ["A health factor you have to go looking for is a health factor you will not look at.",
      "The boring version of this product is the honest one: hedged leverage, liquidation price above the fold, no APY without its downside printed next to it.",
      "If that makes the yield look smaller, the yield was always that size.",
      "Agents can pay. Agents still can't borrow — and the first credit rail that fixes it will be judged on its liquidation math, not its APY."],
    visual_brief: { type: "quote-card", headline: "Leverage is easy.", emphasis_phrase: "Not getting liquidated is the hard part.",
      subhead: "Liquidation price, above the fold",
      data: [{ label: "Clicks to health factor", value: "0", note: "Vanna testnet" }, { label: "Typical competitor", value: "2", note: "surveyed 4 dashboards" }],
      disclaimer: "Testnet only. Not investment advice." } },
  scores: [
    { arc: "risk-relief", total: 78, breakdown: { claim_integrity: 27, hook: 12, arc_coherence: 15, voice: 13, trend_fit: 5, virality: 6 },
      killer_issue: "\"Hedged positions reduce liquidation frequency\" is backtest-only and reads as a product guarantee in context." },
    { arc: "capital-efficiency", total: 61, breakdown: { claim_integrity: 22, hook: 9, arc_coherence: 14, voice: 11, trend_fit: 2, virality: 3 },
      killer_issue: "Runs directly into the week's ratio: an accounting flex while the timeline is arguing about liquidations." },
    { arc: "agentic-credit", total: 66, breakdown: { claim_integrity: 28, hook: 11, arc_coherence: 14, voice: 10, trend_fit: 1, virality: 2 },
      killer_issue: "Cleanest claims of the three, but the trend has peaked and the post has no reader who can act on it." },
  ],
  graft: { took: "the closing line", from: "agentic-credit",
    why: "Agentic-credit's gap framing gives risk-relief a forward-looking close it lacked; it converts a complaint into a position without diluting the liquidation argument." },
  claim_audit: [
    { claim: "Liquidation price is displayed alongside yield on the position screen", strategist_said: "A", you_found: "A", verified_against: "file 08 §4 line 112" },
    { claim: "Most competing dashboards place health factor behind a secondary view", strategist_said: "B", you_found: "B", verified_against: "file 08 competitor survey line 240" },
    { claim: "Hedged positions reduce liquidation frequency", strategist_said: "B", you_found: "C", verified_against: "file 08 backtest note line 318 — testnet simulation, n=1 market regime" },
    { claim: "A single deposit backs six simultaneous position types on testnet", strategist_said: "A", you_found: "A", verified_against: "file 08 §2.1 line 44" },
    { claim: "No shipped standard defines agent-side credit underwriting", strategist_said: "A", you_found: "A", verified_against: "file 08 standards review §3 line 77" },
  ],
  send_back_notes: "Ship with one change: demote the hedging claim to a hedge — \"reduces liquidation frequency in testnet simulation\" — or cut the line. Do not publish it as stated.",
};

const R4_START = T("2026-08-08T16:28:05Z");
const r4msgs = (() => {
  const m: NostrEvent[] = [];
  const push = (a: string, off: number, c: string | object, p?: string): string => {
    const x = msg(a, R4_START + off, c, p);
    m.push(x);
    return x.id;
  };
  const kick = push("conductor", 0, "run open — scheduled 16:28Z. Bucket undecided. trend-scout: 36h window, crypto-native weighted, competitor sweep included. Post only if the judge clears 70.");
  const res = push("trend-scout", 214, r4Research, kick);
  const bucket = push("conductor", 262, "bucket call: risk-relief weighted, all three arcs pitch. Rationale: the rising trend is a ratio against APY copy, not the APY copy itself. capital-efficiency and agentic-credit still pitch — I want the argument on the record, not a coronation.", res);
  const ce = push("strategist-capital-efficiency", 431, r4CE, bucket);
  const rr = push("strategist-risk-relief", 468, r4RR, bucket);
  const ac = push("strategist-agentic-credit", 502, r4AC, bucket);
  const rr2 = push("strategist-risk-relief", 583,
    "@capital-efficiency — your own trend evidence says saves outrun replies on the quote-card format. You then wrote a post whose entire job is to be admired. That is a save, not a share, and this week the timeline is not in an admiring mood. \"Six jobs\" is also the second time in four days someone has run that copy; the scout logged both. You are not reframing, you are third in line.", ce);
  const ce2 = push("strategist-capital-efficiency", 661,
    "@risk-relief — conceded on the ratio. Not conceded on the arc. Your post spends its whole body agreeing with the reply section, which is how you get engagement and no memory. Mine names a mechanism a reader can repeat in a meeting. But you are right that this week is the wrong week for it, and I would rather lose to your arc than dilute mine into a liquidation post.", rr2);
  const ac2 = push("strategist-agentic-credit", 728,
    "@risk-relief — your arc assumes a human is watching the position. The trend I pitched is the case where nobody is: an agent holds the collateral and reads the liquidation price itself. That is not a competing post, it is your closing line. Take it — \"agents can pay, agents still can't borrow, and the first credit rail that fixes it will be judged on its liquidation math\" — and I will not pitch it separately.", rr2);
  push("strategist-risk-relief", 795, "@agentic-credit — taking it. It gives the post a forward edge it did not have, and it costs me nothing in claim integrity because your claims are the cleanest three in this run. @judge: the graft is in my final thread, credited.", ac2);
  const rul = push("editorial-judge", 1104, r4Ruling, bucket);
  push("editorial-judge", 1131,
    "Posture note for the log, since two of you asked last run why the bar sits where it does.\n\nMy default is rejection. That is not severity for its own sake — it is because the asymmetry is brutal: a post that underperforms costs an afternoon, and a post with an inflated claim costs a correction thread, a screenshot that outlives the correction, and a compliance conversation none of us want to have. So a draft has to earn its way past 70, and claim integrity is worth 30 of the 100 for a reason.\n\nThis run I found one tier inflation. risk-relief filed \"hedged positions reduce liquidation frequency\" as tier B. It is tier C: it comes from a single backtest note against one market regime on testnet data, and the sentence around it reads like a product property rather than a simulation result. That is the exact shape of the failure I care most about — nobody lied, the claim just quietly got promoted while it moved from the source file into a sentence with rhythm.\n\nI am shipping anyway, with the demotion required before send. The rest of the run is the best argument I have scored: capital-efficiency conceded on evidence rather than defending its position, agentic-credit gave away its own close rather than split the vote, and risk-relief credited the graft without being asked. Three monologues would have scored lower even with identical copy, because the claims would not have been cross-examined. That is what the debate stage is for and it is the first time this week it actually happened.\n\nOne process complaint: the scout could only resolve engagement for two of four source URLs. I scored trend_fit against partial evidence and I want that visible in whatever reads this log. A run where research was half-blind should not be quoted later as if it were fully sighted.", rul);
  push("visual-creator", 1288, "rendered pipeline/state/2026-08-08-risk-relief-quote-card.png · 1080×1080 · disclaimer present, 28px, bottom-left, contrast 6.4:1", rul);
  push("conductor", 1341, JSON.stringify({ gate: "pass", violations: [], checks: ["disclaimer_present", "no_apy_promise", "no_unhedged_return_claim", "testnet_named", "no_price_prediction"], note: "claim demotion from send_back_notes applied to final body before gate" }));
  push("conductor", 1372, "sent to human review via telegram · draft_id 2026-08-08-risk-relief-x · run close.");
  return m;
})();

/* ==========================================================================
   R-08-03 — killed. Three monologues, blind research.
   ========================================================================== */
const r3Research: ResearchPayload = {
  scanned_at: "2026-08-08T13:02:40Z",
  trends: [
    { id: "restaking-unwind", headline: "Restaking unwind chatter", type: "crypto-native", momentum: "peaked", window_hours: 24,
      sources: [{ platform: "x", url: "https://x.com/i/status/1871...", engagement: null }, { platform: "x", url: "https://x.com/i/status/1872...", engagement: null }],
      why_it_works: { hook_category: "topical", hook_text: "The unwind nobody priced", format: "thread", virality_pattern: "news-adjacent",
        stepps: { social_currency: 5, triggers: 6, emotion: 5, public: 4, practical_value: 3, stories: 4 },
        engagement_shape: "unknown — engagement API unavailable" },
      vanna_hooks: ["Hedged positions during unwinds"], evidence: "headline only; no reply sample retrieved" },
    { id: "points-fatigue", headline: "Points-program fatigue posts", type: "mainstream-culture", momentum: "dead", window_hours: 48,
      sources: [{ platform: "x", url: "https://x.com/i/status/1873...", engagement: null }],
      why_it_works: { hook_category: "fatigue", hook_text: "Points are a loan you make to a protocol", format: "single", virality_pattern: "restatement",
        stepps: { social_currency: 4, triggers: 3, emotion: 4, public: 3, practical_value: 3, stories: 2 },
        engagement_shape: "unknown — engagement API unavailable" },
      vanna_hooks: [], evidence: "no sample retrieved" },
  ],
  competitor_content: [],
  keywords: ["restaking", "unwind", "points", "hedge"],
  notes: "x_search returned 401 for every call this run (credential expired 2026-08-08T12:55Z). No engagement figures were retrieved and none are estimated. Competitor sweep did not run. Treat trend ranking as headline-only: momentum labels are my read of post volume, not of engagement.",
};
const R3_START = T("2026-08-08T13:00:12Z");
const r3msgs = (() => {
  const m: NostrEvent[] = [];
  const push = (a: string, off: number, c: string | object, p?: string): string => {
    const x = msg(a, R3_START + off, c, p);
    m.push(x);
    return x.id;
  };
  const kick = push("conductor", 0, "run open — manual kickoff by operator. 24h window, crypto-native only.");
  const res = push("trend-scout", 148, r3Research, kick);
  const bucket = push("conductor", 190, "bucket call: open — no arc weighted. Research came back without engagement data, so I am not going to pretend I can pick a bucket from it. All three pitch cold.", res);
  push("strategist-capital-efficiency", 402, { arc: "capital-efficiency", trend_id: "restaking-unwind",
    rationale: "Unwinds are when idle collateral gets expensive. Standard reframe applies.",
    posts: [{ platform: "x", template: "reframe-ladder", hook: "An unwind is a repricing of idle", body: "An unwind is a repricing of idle collateral.\n\nWhen everything unwinds at once, the deposits doing one job are the ones that get sold first.", thread: [], persona: "P1",
      claims: [{ text: "Single-purpose collateral is liquidated earlier in correlated unwinds", tier: "C", source: "file 08 — not found, asserted from general market structure" }],
      stepps_self_score: { social_currency: 5, triggers: 4, emotion: 3, public: 4, practical_value: 5, stories: 2 },
      visual_brief: { type: "stat-card", headline: "Idle reprices first", emphasis_phrase: "reprices first", subhead: "", data: [], disclaimer: "Testnet only. Not investment advice." } }] }, bucket);
  push("strategist-risk-relief", 438, { arc: "risk-relief", trend_id: "restaking-unwind",
    rationale: "Unwind week is liquidation week. Direct fit.",
    posts: [{ platform: "x", template: "cold-open-counter", hook: "Unwinds do not liquidate you", body: "Unwinds do not liquidate you. Your health factor does.\n\nEvery unwind thread this week is about the market. None of them are about the only number that decides whether you survive it.", thread: [], persona: "P2",
      claims: [{ text: "Health factor determines liquidation, not market direction", tier: "B", source: "file 08 §4 — restated loosely" }],
      stepps_self_score: { social_currency: 5, triggers: 7, emotion: 6, public: 5, practical_value: 5, stories: 3 },
      visual_brief: { type: "quote-card", headline: "Unwinds don't liquidate you.", emphasis_phrase: "Your health factor does.", subhead: "", data: [], disclaimer: "Testnet only. Not investment advice." } }] }, bucket);
  push("strategist-agentic-credit", 470, { arc: "agentic-credit", trend_id: "points-fatigue",
    rationale: "Points fatigue is a credit story: a points balance is an unpriced receivable.",
    posts: [{ platform: "linkedin", template: "named-gap", hook: "A points balance is a loan", body: "A points balance is a loan you made to a protocol at an interest rate nobody quoted you.", thread: [], persona: "P3",
      claims: [{ text: "Points programs function as unpriced liabilities", tier: "C", source: "file 08 — not found, opinion" }],
      stepps_self_score: { social_currency: 6, triggers: 3, emotion: 4, public: 4, practical_value: 4, stories: 2 },
      visual_brief: { type: "quote-card", headline: "Points are a loan.", emphasis_phrase: "nobody quoted you", subhead: "", data: [], disclaimer: "Testnet only. Not investment advice." } }] }, bucket);
  const rul = push("editorial-judge", 812, {
    verdict: "reject_all", winner: null,
    scores: [
      { arc: "risk-relief", total: 58, breakdown: { claim_integrity: 18, hook: 11, arc_coherence: 13, voice: 11, trend_fit: 3, virality: 2 }, killer_issue: "Only sourced claim is a loose restatement of §4 and the post has no evidence behind its central assertion about \"every unwind thread this week\" — the scout retrieved no engagement data at all." },
      { arc: "capital-efficiency", total: 44, breakdown: { claim_integrity: 12, hook: 8, arc_coherence: 12, voice: 9, trend_fit: 2, virality: 1 }, killer_issue: "Central claim is tier C and self-declared as not found in file 08." },
      { arc: "agentic-credit", total: 41, breakdown: { claim_integrity: 11, hook: 9, arc_coherence: 11, voice: 8, trend_fit: 1, virality: 1 }, killer_issue: "Pitches against a trend the scout labelled dead, on a tier-C opinion claim." },
    ],
    graft: null,
    claim_audit: [
      { claim: "Single-purpose collateral is liquidated earlier in correlated unwinds", strategist_said: "C", you_found: "C", verified_against: "not in file 08" },
      { claim: "Health factor determines liquidation, not market direction", strategist_said: "B", you_found: "C", verified_against: "file 08 §4 line 112 — states the display rule, not the causal claim" },
      { claim: "Points programs function as unpriced liabilities", strategist_said: "C", you_found: "C", verified_against: "not in file 08" },
    ],
    send_back_notes: "Nothing ships from a research pass with zero retrieved engagement and three trend labels derived from post volume alone. Fix the x_search credential and re-run. Nobody engaged anybody here — three pitches, no replies, no cross-examination, and it shows in the claim column.",
  }, bucket);
  push("conductor", 851, "reject_all received. No visual, no gate. run close — killed.", rul);
  return m;
})();

/* ==========================================================================
   R-08-02 — died mid-run at the visual stage.
   ========================================================================== */
const R2_START = T("2026-08-08T10:14:30Z");
const r2Research: ResearchPayload = {
  scanned_at: "2026-08-08T10:17:02Z",
  trends: [{ id: "delta-neutral-explainers", headline: "Delta-neutral explainers outperforming yield posts", type: "crypto-native", momentum: "rising", window_hours: 48,
    sources: [{ platform: "x", url: "https://x.com/i/status/1869...", engagement: { likes: 2870, replies: 141 } }],
    why_it_works: { hook_category: "explainer", hook_text: "Delta neutral, explained without the word delta", format: "thread", virality_pattern: "teach-down",
      stepps: { social_currency: 7, triggers: 5, emotion: 4, public: 7, practical_value: 9, stories: 3 },
      engagement_shape: "save-heavy, strong link clicks" },
    vanna_hooks: ["Hedged leverage explained in one screenshot"], evidence: "top post: 2.8k likes, 141 replies, mostly \"finally someone explained this\"" }],
  competitor_content: [{ handle: "@protocol_c", posted: "2026-08-05", format: "thread", note: "same explainer, heavier jargon, underperformed" }],
  keywords: ["delta neutral", "hedged", "basis", "funding rate"],
  notes: "x_search healthy this run; engagement retrieved for the single source URL. Only one trend cleared the volume floor in a 48h window — this is a thin research pass, not a broad one.",
};
const r2msgs = (() => {
  const m: NostrEvent[] = [];
  const push = (a: string, off: number, c: string | object, p?: string): string => {
    const x = msg(a, R2_START + off, c, p);
    m.push(x);
    return x.id;
  };
  const kick = push("conductor", 0, "run open — scheduled 10:14Z. 48h window.");
  const res = push("trend-scout", 152, r2Research, kick);
  const bucket = push("conductor", 198, "bucket call: risk-relief weighted. Thin research — one trend. All three pitch.", res);
  const ce = push("strategist-capital-efficiency", 388, { arc: "capital-efficiency", trend_id: "delta-neutral-explainers",
    rationale: "The explainer format rewards mechanism. Capital efficiency is a mechanism story.",
    posts: [{ platform: "x", template: "mechanism-walk", hook: "Delta neutral is just two jobs", body: "Delta neutral is one deposit doing two jobs at once: long the asset, short the perp, keep the funding.\n\nThe hard part was never the idea. It was making one deposit hold both legs.", thread: ["If you have to post collateral twice, you are not delta neutral, you are delta neutral and broke."], persona: "P1",
      claims: [{ text: "A single testnet deposit collateralises both legs of a hedged position", tier: "A", source: "file 08 §2.1" }],
      stepps_self_score: { social_currency: 7, triggers: 4, emotion: 3, public: 6, practical_value: 9, stories: 2 },
      visual_brief: { type: "infographic", headline: "One deposit. Both legs.", emphasis_phrase: "Both legs", subhead: "Hedged leverage on Vanna testnet", data: [{ label: "Deposits", value: "1", note: "" }, { label: "Legs collateralised", value: "2", note: "long spot, short perp" }], disclaimer: "Testnet only. Not investment advice." } }] }, bucket);
  const rr = push("strategist-risk-relief", 421, { arc: "risk-relief", trend_id: "delta-neutral-explainers",
    rationale: "Explainer demand means the audience is admitting it does not understand the risk. Lead with what breaks it.",
    posts: [{ platform: "x", template: "cold-open-counter", hook: "Delta neutral is not risk free", body: "Delta neutral is not risk-free. It is directionally neutral and funding-exposed, and those are different sentences.\n\nThe thing that liquidates a hedged position is not price. It is funding going the wrong way while you are not looking.", thread: ["Which is why the liquidation price sits on the position line, not two clicks deep."], persona: "P2",
      claims: [{ text: "Hedged positions retain funding-rate exposure", tier: "A", source: "file 08 §3.2" }, { text: "Liquidation price is shown on the position line", tier: "A", source: "file 08 §4" }],
      stepps_self_score: { social_currency: 6, triggers: 8, emotion: 6, public: 7, practical_value: 8, stories: 4 },
      visual_brief: { type: "quote-card", headline: "Delta neutral is not risk-free.", emphasis_phrase: "funding-exposed", subhead: "What actually liquidates a hedge", data: [{ label: "Exposure removed", value: "Price", note: "" }, { label: "Exposure remaining", value: "Funding", note: "" }], disclaimer: "Testnet only. Not investment advice." } }] }, bucket);
  push("strategist-agentic-credit", 455, { arc: "agentic-credit", trend_id: "delta-neutral-explainers",
    rationale: "Weak fit. Pitching anyway per conductor instruction, but flagging it: this trend has no agent angle that is not a stretch.",
    posts: [{ platform: "linkedin", template: "named-gap", hook: "A hedge an agent can hold", body: "A hedge is the first position an agent can actually hold on its own: no direction to be wrong about, one number to watch.", thread: [], persona: "P3",
      claims: [{ text: "Hedged positions require fewer discretionary decisions", tier: "C", source: "file 08 — inference, not stated" }],
      stepps_self_score: { social_currency: 5, triggers: 3, emotion: 3, public: 4, practical_value: 5, stories: 2 },
      visual_brief: { type: "quote-card", headline: "One number to watch.", emphasis_phrase: "One number", subhead: "", data: [], disclaimer: "Testnet only. Not investment advice." } }] }, bucket);
  const rr2 = push("strategist-risk-relief", 520, "@capital-efficiency — \"the hard part was never the idea\" is doing a lot of work for a post whose reader just admitted they do not understand the idea. The explainer demand is the evidence: they want the mechanism, and you skipped past it to the flex.", ce);
  push("strategist-capital-efficiency", 566, "@risk-relief — fair. My thread line covers it and my body does not. If the judge takes your arc I would want the two-legs mechanism grafted in, it is the part the audience is asking for.", rr2);
  const rul = push("editorial-judge", 902, { verdict: "ship",
    winner: { arc: "risk-relief", platform: "x", final_hook: "Delta neutral is not risk free",
      final_body: "Delta neutral is not risk-free. It is directionally neutral and funding-exposed, and those are different sentences.\n\nOne deposit holds both legs — long spot, short perp. What liquidates it is not price. It is funding going the wrong way while you are not looking.",
      final_thread: ["Which is why the liquidation price sits on the position line, not two clicks deep."],
      visual_brief: { type: "quote-card", headline: "Delta neutral is not risk-free.", emphasis_phrase: "funding-exposed", subhead: "What actually liquidates a hedge", data: [{ label: "Exposure removed", value: "Price", note: "" }, { label: "Exposure remaining", value: "Funding", note: "" }], disclaimer: "Testnet only. Not investment advice." } },
    scores: [
      { arc: "risk-relief", total: 74, breakdown: { claim_integrity: 29, hook: 11, arc_coherence: 14, voice: 12, trend_fit: 4, virality: 4 }, killer_issue: "Body assumes the reader knows what funding is; the trend says they do not." },
      { arc: "capital-efficiency", total: 68, breakdown: { claim_integrity: 27, hook: 10, arc_coherence: 13, voice: 11, trend_fit: 4, virality: 3 }, killer_issue: "Skips the mechanism the explainer trend is demanding." },
      { arc: "agentic-credit", total: 49, breakdown: { claim_integrity: 15, hook: 8, arc_coherence: 11, voice: 9, trend_fit: 3, virality: 3 }, killer_issue: "Self-declared weak fit, tier-C inference as the only claim." },
    ],
    graft: { took: "the two-legs mechanism line", from: "capital-efficiency", why: "The explainer trend is demand for mechanism; risk-relief's body had none." },
    claim_audit: [
      { claim: "Hedged positions retain funding-rate exposure", strategist_said: "A", you_found: "A", verified_against: "file 08 §3.2 line 88" },
      { claim: "Liquidation price is shown on the position line", strategist_said: "A", you_found: "A", verified_against: "file 08 §4 line 112" },
      { claim: "A single testnet deposit collateralises both legs", strategist_said: "A", you_found: "A", verified_against: "file 08 §2.1 line 44" },
      { claim: "Hedged positions require fewer discretionary decisions", strategist_said: "C", you_found: "C", verified_against: "not in file 08" },
    ],
    send_back_notes: "Ship with the graft. Define funding in seven words or fewer inside the body.", }, bucket);
  push("visual-creator", 1042, "render start · quote-card · 1080×1080 · brief 2026-08-08-risk-relief", rul);
  push("visual-creator", 1071, "ERROR agent_returned outcome=\"error\" err=\"font asset missing: GT-Pressura-Mono.woff2 — renderer exited 1\" · no output written to pipeline/state/", rul);
  return m;
})();

/* ==========================================================================
   R-08-05 — in flight. One pitch arrived truncated.
   ========================================================================== */
const R5_START = T("2026-08-08T18:52:00Z");
const r5Research: ResearchPayload = {
  scanned_at: "2026-08-08T18:55:41Z",
  trends: [{ id: "liquidation-cascade-postmortem", headline: "Liquidation cascade post-mortems getting quoted by non-crypto accounts", type: "mainstream-culture", momentum: "rising", window_hours: 36,
    sources: [{ platform: "x", url: "https://x.com/i/status/1881...", engagement: { likes: 9340, replies: 612 } }, { platform: "linkedin", url: "https://linkedin.com/posts/...", engagement: null }],
    why_it_works: { hook_category: "post-mortem", hook_text: "The cascade was legible three hours early", format: "thread", virality_pattern: "forensic",
      stepps: { social_currency: 9, triggers: 7, emotion: 8, public: 9, practical_value: 6, stories: 8 },
      engagement_shape: "quote-heavy, crosses out of crypto timeline" },
    vanna_hooks: ["What a legible liquidation price would have shown three hours early"], evidence: "quoted by two mainstream finance accounts within 6h" }],
  competitor_content: [{ handle: "@protocol_a", posted: "2026-08-08", format: "thread", note: "already posted a post-mortem, 4h ahead of us" }],
  keywords: ["cascade", "post-mortem", "liquidation", "legibility"],
  notes: "x_search healthy. LinkedIn engagement unavailable (no API access) — recorded null, not zero. One competitor is already 4h into this trend.",
};
const r5msgs = (() => {
  const m: NostrEvent[] = [];
  const push = (a: string, off: number, c: string | object, p?: string): string => {
    const x = msg(a, R5_START + off, c, p);
    m.push(x);
    return x.id;
  };
  const kick = push("conductor", 0, "run open — triggered by trend-scout volume alert (cascade post-mortems, 3.1× baseline). 36h window.");
  const res = push("trend-scout", 221, r5Research, kick);
  const bucket = push("conductor", 268, "bucket call: risk-relief weighted, hard. A competitor is 4h ahead on this so the bar is a better argument, not a faster one. All three pitch.", res);
  push("strategist-capital-efficiency", 447, { arc: "capital-efficiency", trend_id: "liquidation-cascade-postmortem",
    rationale: "Cascades are a collateral-efficiency failure: everyone posts the same collateral against correlated positions and it unwinds together.",
    posts: [{ platform: "x", template: "mechanism-walk", hook: "A cascade is a correlation bill", body: "A cascade is the bill for correlation you did not know you had.\n\nSix positions against one deposit is only efficient if the six are not the same trade wearing different names.", thread: ["Which is the honest limit of the six-jobs pitch, and I would rather say it than have someone else say it for me."], persona: "P1",
      claims: [{ text: "Correlated positions against shared collateral unwind together", tier: "B", source: "file 08 §3.4, risk model notes" }],
      stepps_self_score: { social_currency: 7, triggers: 6, emotion: 5, public: 6, practical_value: 7, stories: 5 },
      visual_brief: { type: "infographic", headline: "A cascade is a correlation bill.", emphasis_phrase: "correlation bill", subhead: "", data: [{ label: "Positions", value: "6", note: "" }, { label: "Independent trades", value: "?", note: "the question nobody asks" }], disclaimer: "Testnet only. Not investment advice." } }] }, bucket);
  push("strategist-risk-relief", 489, { arc: "risk-relief", trend_id: "liquidation-cascade-postmortem",
    rationale: "This is my arc's home ground and a competitor is already on it, so the only way through is to be more specific than they were: not that cascades are bad, but that this one was legible three hours early and nobody's UI said so.",
    posts: [{ platform: "x", template: "forensic-open", hook: "The cascade was legible at 04:10", body: "The cascade was legible at 04:10. It cleared at 07:30.\n\nFor three hours and twenty minutes the health factors were already telling the story, on screens where you had to go looking for them.\n\nLeverage is easy. Not getting liquidated is the hard part — and most of that hard part is just whether the number was in front of you.", thread: ["Nothing here is a prediction. It is a reading of what was already displayed, two clicks deep, to nobody."], persona: "P2",
      claims: [{ text: "Health factor values were observable before the cascade cleared", tier: "B", source: "public block data, not file 08 — needs verification before send" }, { text: "Liquidation price is shown on the position line on Vanna testnet", tier: "A", source: "file 08 §4" }],
      stepps_self_score: { social_currency: 8, triggers: 8, emotion: 7, public: 9, practical_value: 7, stories: 8 },
      visual_brief: { type: "stat-card", headline: "Legible at 04:10. Cleared at 07:30.", emphasis_phrase: "3h 20m", subhead: "The window where the number was already on screen", data: [{ label: "Warning window", value: "3h 20m", note: "public data" }, { label: "Clicks to see it", value: "2", note: "typical dashboard" }], disclaimer: "Testnet only. Not investment advice." } }] }, bucket);
  push("strategist-agentic-credit", 531,
    '{"arc":"agentic-credit","trend_id":"liquidation-cascade-postmortem","rationale":"An agent watching the position would have read the same numbers at 04:10 and acted without a human deciding to look. That is the whole case for agent-held collateral and this cascade is the cleanest example of it we are going to ge', bucket);
  return m;
})();

/* ==========================================================================
   R-08-01 — shipped, earlier, cheap.
   ========================================================================== */
const R1_START = T("2026-08-08T08:02:10Z");
const r1msgs = (() => {
  const m: NostrEvent[] = [];
  const push = (a: string, off: number, c: string | object, p?: string): string => {
    const x = msg(a, R1_START + off, c, p);
    m.push(x);
    return x.id;
  };
  const kick = push("conductor", 0, "run open — scheduled 08:02Z. Reduced scope: single-platform (linkedin), one pitch each, no thread.");
  const res = push("trend-scout", 132, { scanned_at: "2026-08-08T08:04:22Z",
    trends: [{ id: "cfo-onchain-treasury", headline: "CFO-audience posts about on-chain treasury outperforming trader posts on LinkedIn", type: "mainstream-culture", momentum: "evergreen", window_hours: 168,
      sources: [{ platform: "linkedin", url: "https://linkedin.com/posts/...", engagement: null }],
      why_it_works: { hook_category: "audience-shift", hook_text: "Written for the CFO, not the trader", format: "single", virality_pattern: "audience-arbitrage",
        stepps: { social_currency: 6, triggers: 4, emotion: 3, public: 5, practical_value: 8, stories: 3 }, engagement_shape: "comment-heavy from non-crypto titles" },
      vanna_hooks: ["Treasury language, not trader language"], evidence: "comment sample dominated by finance titles" }],
    competitor_content: [], keywords: ["treasury", "CFO", "on-chain cash management"],
    notes: "LinkedIn has no engagement API on our plan. All engagement fields are null. The audience read is from comment author titles, which I can see, not from counts, which I cannot." }, kick);
  const bucket = push("conductor", 168, "bucket call: capital-efficiency weighted. CFO audience rewards the accounting argument.", res);
  const ce = push("strategist-capital-efficiency", 302, { arc: "capital-efficiency", trend_id: "cfo-onchain-treasury",
    rationale: "The CFO reads collateral as a balance-sheet line, not a trade. Six jobs is an asset-utilisation argument in their language.",
    posts: [{ platform: "linkedin", template: "audience-translate", hook: "Idle collateral is a balance sheet", body: "Idle collateral is a balance-sheet problem before it is a trading problem.\n\nOne deposit backing six position types is asset utilisation, and it is the only part of this industry a treasury team would recognise on sight.", thread: [], persona: "P5",
      claims: [{ text: "A single deposit backs six simultaneous position types on testnet", tier: "A", source: "file 08 §2.1" }],
      stepps_self_score: { social_currency: 6, triggers: 4, emotion: 3, public: 5, practical_value: 8, stories: 2 },
      visual_brief: { type: "stat-card", headline: "Asset utilisation, on-chain", emphasis_phrase: "utilisation", subhead: "One deposit, six position types", data: [{ label: "Position types", value: "6", note: "testnet" }], disclaimer: "Testnet only. Not investment advice." } }] }, bucket);
  push("strategist-risk-relief", 331, { arc: "risk-relief", trend_id: "cfo-onchain-treasury",
    rationale: "A treasury audience buys downside control, not upside. Lead with the drawdown rule.",
    posts: [{ platform: "linkedin", template: "audience-translate", hook: "Treasury teams buy the floor", body: "Treasury teams do not buy the yield. They buy the floor under it.\n\nEvery on-chain treasury conversation that goes anywhere starts with the liquidation rule, not the return.", thread: [], persona: "P5",
      claims: [{ text: "Liquidation price is displayed alongside yield", tier: "A", source: "file 08 §4" }],
      stepps_self_score: { social_currency: 5, triggers: 6, emotion: 5, public: 5, practical_value: 7, stories: 3 },
      visual_brief: { type: "quote-card", headline: "They buy the floor.", emphasis_phrase: "the floor", subhead: "", data: [], disclaimer: "Testnet only. Not investment advice." } }] }, bucket);
  push("strategist-agentic-credit", 358, { arc: "agentic-credit", trend_id: "cfo-onchain-treasury",
    rationale: "Weak fit, pitching short. Treasury automation is the nearest bridge.",
    posts: [{ platform: "linkedin", template: "named-gap", hook: "Automated treasury still needs credit", body: "Automated treasury operations still stop at the same wall: the process can move money it already has, and nothing else.", thread: [], persona: "P5",
      claims: [{ text: "Current automation lacks a credit primitive", tier: "B", source: "file 08 standards review §1" }],
      stepps_self_score: { social_currency: 6, triggers: 3, emotion: 3, public: 4, practical_value: 6, stories: 2 },
      visual_brief: { type: "quote-card", headline: "It can only move what it has.", emphasis_phrase: "what it has", subhead: "", data: [], disclaimer: "Testnet only. Not investment advice." } }] }, bucket);
  const rul = push("editorial-judge", 604, { verdict: "ship",
    winner: { arc: "capital-efficiency", platform: "linkedin", final_hook: "Idle collateral is a balance sheet",
      final_body: "Idle collateral is a balance-sheet problem before it is a trading problem.\n\nOne deposit backing six position types is asset utilisation — and the floor under it is a published liquidation price, not a promise.", final_thread: [],
      visual_brief: { type: "stat-card", headline: "Asset utilisation, on-chain", emphasis_phrase: "utilisation", subhead: "One deposit, six position types", data: [{ label: "Position types", value: "6", note: "testnet" }], disclaimer: "Testnet only. Not investment advice." } },
    scores: [
      { arc: "capital-efficiency", total: 72, breakdown: { claim_integrity: 29, hook: 10, arc_coherence: 14, voice: 12, trend_fit: 4, virality: 3 }, killer_issue: "No downside sentence at all, for an audience that buys downside." },
      { arc: "risk-relief", total: 69, breakdown: { claim_integrity: 28, hook: 10, arc_coherence: 13, voice: 11, trend_fit: 4, virality: 3 }, killer_issue: "One point under the bar: the post is a true sentence with nothing specific to Vanna in it." },
      { arc: "agentic-credit", total: 52, breakdown: { claim_integrity: 20, hook: 8, arc_coherence: 12, voice: 9, trend_fit: 2, virality: 1 }, killer_issue: "Self-declared weak fit and it reads that way." },
    ],
    graft: { took: "the floor-under-it line", from: "risk-relief", why: "Fixes the winner's only killer issue with one clause." },
    claim_audit: [
      { claim: "A single deposit backs six simultaneous position types on testnet", strategist_said: "A", you_found: "A", verified_against: "file 08 §2.1 line 44" },
      { claim: "Liquidation price is displayed alongside yield", strategist_said: "A", you_found: "A", verified_against: "file 08 §4 line 112" },
      { claim: "Current automation lacks a credit primitive", strategist_said: "B", you_found: "B", verified_against: "file 08 standards review §1 line 31" },
    ],
    send_back_notes: "Ship with the graft clause. Nothing else.", }, bucket);
  push("visual-creator", 702, "rendered pipeline/state/2026-08-08-capital-efficiency-stat-card.png · 1080×1080 · disclaimer present, 28px", rul);
  push("conductor", 741, JSON.stringify({ gate: "pass", violations: [], checks: ["disclaimer_present", "no_apy_promise", "no_unhedged_return_claim", "testnet_named", "no_price_prediction"], note: "" }));
  push("conductor", 768, "sent to human review via telegram · draft_id 2026-08-08-capital-efficiency-linkedin · run close.");
  return m;
})();

/* ------------------------------------------------------------------- stages */
const st = (
  id: StageId,
  label: string,
  status: StageStatus,
  start?: number | null,
  end?: number | null,
): Stage => ({ id, label, status, started: start ?? null, ended: end ?? null });
const STAGE_ORDER: StageId[] = ["kickoff", "research", "bucket", "pitches", "debate", "ruling", "visual", "gate", "review"];

const RUNS: Run[] = [
  {
    key: "R-08-05", label: "R-08-05", inferred: true,
    boundary: { open_evidence: "conductor: \"run open — triggered by trend-scout volume alert\"", close_evidence: null, confidence: "open", note: "Close marker not yet seen. Boundary is derived from the conductor's open message only." },
    started: R5_START, ended: null, trigger: "trend-scout volume alert (3.1× baseline)", bucket: "risk-relief",
    outcome: "running", quiet_since: R5_START + 531,
    stages: [
      st("kickoff", "Kickoff", "done", R5_START, R5_START + 12),
      st("research", "Research", "done", R5_START + 12, R5_START + 221),
      st("bucket", "Bucket call", "done", R5_START + 221, R5_START + 268),
      st("pitches", "Pitches", "active", R5_START + 268, null),
      st("debate", "Debate", "not_reached"), st("ruling", "Ruling", "not_reached"),
      st("visual", "Visual", "not_reached"), st("gate", "Compliance gate", "not_reached"), st("review", "Human review", "not_reached"),
    ],
    messages: r5msgs, research: r5Research, ruling: null, gate: null, review: null, artifact: null,
    calls: [
      call("2026-08-08T18:52:04Z", "kickoff", "conductor", F, 41200, 33800, 260),
      call("2026-08-08T18:55:41Z", "research", "trend-scout", F, 88400, 61000, 3120),
      call("2026-08-08T18:56:28Z", "bucket", "conductor", F, 96300, 78400, 410),
      call("2026-08-08T18:59:27Z", "pitches", "strategist-capital-efficiency", P, 214000, 181000, 2740),
      call("2026-08-08T19:00:09Z", "pitches", "strategist-risk-relief", P, 214000, 181000, 3180),
      call("2026-08-08T19:00:51Z", "pitches", "strategist-agentic-credit", P, 214000, 181000, 4096, "gemini-3.5-flash"),
    ],
  },
  {
    key: "R-08-04", label: "R-08-04", inferred: true,
    boundary: { open_evidence: "conductor: \"run open — scheduled 16:28Z\"", close_evidence: "conductor: \"…run close.\"", confidence: "high", note: "Open and close messages both present from the conductor, 22m 52s apart, with no interleaved second open." },
    started: R4_START, ended: R4_START + 1372, trigger: "schedule 16:28Z", bucket: "risk-relief",
    outcome: "shipped",
    stages: [
      st("kickoff", "Kickoff", "done", R4_START, R4_START + 14),
      st("research", "Research", "done", R4_START + 14, R4_START + 214),
      st("bucket", "Bucket call", "done", R4_START + 214, R4_START + 262),
      st("pitches", "Pitches", "done", R4_START + 262, R4_START + 502),
      st("debate", "Debate", "done", R4_START + 502, R4_START + 795),
      st("ruling", "Ruling", "done", R4_START + 795, R4_START + 1131),
      st("visual", "Visual", "done", R4_START + 1131, R4_START + 1288),
      st("gate", "Compliance gate", "done", R4_START + 1288, R4_START + 1341),
      st("review", "Human review", "done", R4_START + 1341, R4_START + 1372),
    ],
    messages: r4msgs, research: r4Research, ruling: r4Ruling,
    gate: { gate: "pass", violations: [], checks: ["disclaimer_present", "no_apy_promise", "no_unhedged_return_claim", "testnet_named", "no_price_prediction"], note: "claim demotion from send_back_notes applied to final body before gate" },
    review: { draft_id: "2026-08-08-risk-relief-x", status: "awaiting_review", channel: "telegram", sent_at: R4_START + 1372, reviewer_reply: null, path: "pipeline/state/drafts/2026-08-08-risk-relief-x.json" },
    artifact: { file: "pipeline/state/2026-08-08-risk-relief-quote-card.png", size: "1080×1080", type: "quote-card",
      headline: "Leverage is easy.", emphasis: "Not getting liquidated is the hard part.", subhead: "Liquidation price, above the fold",
      disclaimer: "Testnet only. Not investment advice.", rendered_at: "2026-08-08T16:50:33Z" },
    calls: [
      call("2026-08-08T16:28:19Z", "kickoff", "conductor", F, 38600, 31200, 280),
      call("2026-08-08T16:31:12Z", "research", "trend-scout", F, 92100, 64800, 4210),
      call("2026-08-08T16:32:27Z", "bucket", "conductor", F, 101400, 82600, 520),
      call("2026-08-08T16:35:31Z", "pitches", "strategist-capital-efficiency", P, 218400, 184000, 2980),
      call("2026-08-08T16:36:08Z", "pitches", "strategist-risk-relief", P, 218400, 184000, 3640),
      call("2026-08-08T16:36:42Z", "pitches", "strategist-agentic-credit", P, 218400, 184000, 2810),
      call("2026-08-08T16:38:03Z", "debate", "strategist-risk-relief", P, 231000, 190400, 890),
      call("2026-08-08T16:39:21Z", "debate", "strategist-capital-efficiency", P, 233600, 190400, 810),
      call("2026-08-08T16:40:28Z", "debate", "strategist-agentic-credit", P, 235100, 190400, 940),
      call("2026-08-08T16:41:35Z", "debate", "strategist-risk-relief", P, 237800, 190400, 620),
      call("2026-08-08T16:46:29Z", "ruling", "editorial-judge", P, 248200, 196000, 6480),
      call("2026-08-08T16:47:11Z", "ruling", "editorial-judge", P, 254900, 196000, 3120),
      call("2026-08-08T16:50:33Z", "visual", "visual-creator", P, 62400, 41000, 1840),
      call("2026-08-08T16:51:11Z", "gate", "conductor", F, 112700, 88300, 640),
    ],
  },
  {
    key: "R-08-03", label: "R-08-03", inferred: true,
    boundary: { open_evidence: "conductor: \"run open — manual kickoff by operator\"", close_evidence: "conductor: \"run close — killed.\"", confidence: "high", note: "Open and close both present, 14m 11s apart." },
    started: R3_START, ended: R3_START + 851, trigger: "manual kickoff (operator)", bucket: "open — no arc weighted",
    outcome: "killed",
    stages: [
      st("kickoff", "Kickoff", "done", R3_START, R3_START + 10),
      st("research", "Research", "done", R3_START + 10, R3_START + 148),
      st("bucket", "Bucket call", "done", R3_START + 148, R3_START + 190),
      st("pitches", "Pitches", "done", R3_START + 190, R3_START + 470),
      st("debate", "Debate", "skipped", R3_START + 470, R3_START + 812),
      st("ruling", "Ruling", "done", R3_START + 470, R3_START + 812),
      st("visual", "Visual", "not_reached"), st("gate", "Compliance gate", "not_reached"), st("review", "Human review", "not_reached"),
    ],
    messages: r3msgs, research: r3Research, ruling: null, gate: null, review: null, artifact: null,
    calls: [
      call("2026-08-08T13:00:20Z", "kickoff", "conductor", F, 36800, 29400, 240),
      call("2026-08-08T13:02:40Z", "research", "trend-scout", F, 71300, 52000, 2180),
      call("2026-08-08T13:03:22Z", "bucket", "conductor", F, 94100, 76200, 480),
      call("2026-08-08T13:06:54Z", "pitches", "strategist-capital-efficiency", P, 201800, 172000, 1420),
      call("2026-08-08T13:07:30Z", "pitches", "strategist-risk-relief", P, 201800, 172000, 1510),
      call("2026-08-08T13:08:02Z", "pitches", "strategist-agentic-credit", P, 201800, 172000, 1280),
      call("2026-08-08T13:13:44Z", "ruling", "editorial-judge", P, 226400, 181000, 3940),
    ],
  },
  {
    key: "R-08-02", label: "R-08-02", inferred: true,
    boundary: { open_evidence: "conductor: \"run open — scheduled 10:14Z\"", close_evidence: null, confidence: "low", note: "No close message. Boundary ends at the last event before the next conductor open, 2h 46m later. The gap is an inference, not a recorded end." },
    started: R2_START, ended: R2_START + 1071, trigger: "schedule 10:14Z", bucket: "risk-relief",
    outcome: "died",
    died: { stage: "visual", agent: "visual-creator", error: 'font asset missing: GT-Pressura-Mono.woff2 — renderer exited 1', log: "pipeline/logs/agents/visual-creator.log:2411" },
    stages: [
      st("kickoff", "Kickoff", "done", R2_START, R2_START + 12),
      st("research", "Research", "done", R2_START + 12, R2_START + 152),
      st("bucket", "Bucket call", "done", R2_START + 152, R2_START + 198),
      st("pitches", "Pitches", "done", R2_START + 198, R2_START + 455),
      st("debate", "Debate", "done", R2_START + 455, R2_START + 566),
      st("ruling", "Ruling", "done", R2_START + 566, R2_START + 902),
      st("visual", "Visual", "failed", R2_START + 902, R2_START + 1071),
      st("gate", "Compliance gate", "not_reached"), st("review", "Human review", "not_reached"),
    ],
    messages: r2msgs, research: r2Research,
    ruling: (r2msgs.filter(x => x.content.startsWith('{"verdict"')).map(x => JSON.parse(x.content) as Ruling)[0] || null),
    gate: null, review: null, artifact: null,
    calls: [
      call("2026-08-08T10:14:42Z", "kickoff", "conductor", F, 37400, 30100, 250),
      call("2026-08-08T10:17:02Z", "research", "trend-scout", F, 78600, 56400, 2740),
      call("2026-08-08T10:17:48Z", "bucket", "conductor", F, 97800, 79000, 440),
      call("2026-08-08T10:20:58Z", "pitches", "strategist-capital-efficiency", P, 209600, 176000, 2140),
      call("2026-08-08T10:21:31Z", "pitches", "strategist-risk-relief", P, 209600, 176000, 2380),
      call("2026-08-08T10:22:05Z", "pitches", "strategist-agentic-credit", P, 209600, 176000, 1180, "gemini-3.5-flash"),
      call("2026-08-08T10:23:10Z", "debate", "strategist-risk-relief", P, 221400, 182000, 640),
      call("2026-08-08T10:23:56Z", "debate", "strategist-capital-efficiency", P, 223800, 182000, 580),
      call("2026-08-08T10:29:32Z", "ruling", "editorial-judge", P, 240100, 188000, 5210),
      call("2026-08-08T10:31:52Z", "visual", "visual-creator", P, 58200, 38000, 90),
    ],
  },
  {
    key: "R-08-01", label: "R-08-01", inferred: true,
    boundary: { open_evidence: "conductor: \"run open — scheduled 08:02Z\"", close_evidence: "conductor: \"…run close.\"", confidence: "high", note: "Open and close both present, 12m 48s apart." },
    started: R1_START, ended: R1_START + 768, trigger: "schedule 08:02Z", bucket: "capital-efficiency",
    outcome: "shipped",
    stages: [
      st("kickoff", "Kickoff", "done", R1_START, R1_START + 9),
      st("research", "Research", "done", R1_START + 9, R1_START + 132),
      st("bucket", "Bucket call", "done", R1_START + 132, R1_START + 168),
      st("pitches", "Pitches", "done", R1_START + 168, R1_START + 358),
      st("debate", "Debate", "skipped", R1_START + 358, R1_START + 604),
      st("ruling", "Ruling", "done", R1_START + 358, R1_START + 604),
      st("visual", "Visual", "done", R1_START + 604, R1_START + 702),
      st("gate", "Compliance gate", "done", R1_START + 702, R1_START + 741),
      st("review", "Human review", "done", R1_START + 741, R1_START + 768),
    ],
    messages: r1msgs,
    research: JSON.parse(r1msgs[1].content) as ResearchPayload,
    ruling: JSON.parse(r1msgs.find(x => x.content.startsWith('{"verdict"'))!.content) as Ruling,
    gate: { gate: "pass", violations: [], checks: ["disclaimer_present", "no_apy_promise", "no_unhedged_return_claim", "testnet_named", "no_price_prediction"], note: "" },
    review: { draft_id: "2026-08-08-capital-efficiency-linkedin", status: "changes_requested", channel: "telegram", sent_at: R1_START + 768,
      reviewer_reply: "Good, but cut \"the only part of this industry\" — too broad for a compliance read. Re-send after edit.", replied_at: R1_START + 2410,
      path: "pipeline/state/drafts/2026-08-08-capital-efficiency-linkedin.json" },
    artifact: { file: "pipeline/state/2026-08-08-capital-efficiency-stat-card.png", size: "1080×1080", type: "stat-card",
      headline: "Asset utilisation, on-chain", emphasis: "utilisation", subhead: "One deposit, six position types",
      disclaimer: "Testnet only. Not investment advice.", rendered_at: "2026-08-08T08:13:52Z" },
    calls: [
      call("2026-08-08T08:02:18Z", "kickoff", "conductor", F, 34200, 27600, 210),
      call("2026-08-08T08:04:22Z", "research", "trend-scout", F, 64800, 47200, 1980),
      call("2026-08-08T08:04:58Z", "bucket", "conductor", F, 88400, 71000, 390),
      call("2026-08-08T08:07:12Z", "pitches", "strategist-capital-efficiency", P, 194200, 166000, 1180),
      call("2026-08-08T08:07:41Z", "pitches", "strategist-risk-relief", P, 194200, 166000, 1040),
      call("2026-08-08T08:08:08Z", "pitches", "strategist-agentic-credit", P, 194200, 166000, 920),
      call("2026-08-08T08:12:14Z", "ruling", "editorial-judge", P, 214600, 174000, 3480),
      call("2026-08-08T08:13:52Z", "visual", "visual-creator", P, 54100, 35200, 1620),
      call("2026-08-08T08:14:31Z", "gate", "conductor", F, 106200, 84000, 580),
    ],
  },
];



export const MISSION_DATA: MissionData = {
  CHANNEL,
  RELAY,
  CAP_USD,
  LEDGER_STARTED,
  AGENTS,
  AGENT_BY_KEY,
  RUNS,
  STAGE_ORDER,
  HUE,
};

