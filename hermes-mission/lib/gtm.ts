/**
 * Read model for the 13 GTM agents (`pipeline/gtm_*`).
 *
 * These are the agents described in ARCHITECTURE.md as Agent 01-13. Until now
 * the dashboard had no view of them at all: `/api/agents/status` reported the
 * `core/` pipeline's thirteen stages, which are a different system entirely, so
 * the founder's own agents were invisible while a second set was displayed
 * under their name.
 *
 * Everything here is read from `pipeline/state/gtm_runs/<run>/`, which
 * `pipeline/gtm_os/autonomous_cycle.py` writes as it runs:
 *
 *   calls.jsonl    one row per model call, including the failures
 *   stages.jsonl   one row per agent, including the ones that call no model
 *   summary.json   the finished run
 *
 * Nothing is synthesised. An agent that did not run reports `never_ran` rather
 * than a plausible-looking status.
 */
import fs from 'fs';
import path from 'path';
import { isDeployed, getText, getBytes, runIds as gcsRunIds } from '@/lib/gcs';
import { AGENTS as AGENT_DEFS, type GtmAgentRole } from '@/lib/agents';

export type { GtmAgentRole };

const REPO_ROOT = path.resolve(process.cwd(), '..');
const RUNS_DIR = path.join(REPO_ROOT, 'pipeline', 'state', 'gtm_runs');

export interface GtmAgent {
  n: number;
  id: string;
  code: string;
  name: string;
  role: GtmAgentRole;
  learns: string | null;
  fixed: string | null;
  model: string | null;
  kind: 'MODEL_BACKED' | 'DETERMINISTIC';
  status: string;
  detail: string;
  outputs: string[];
  at: string | null;
  modelCalls: number;
  modelCallsOk: number;
  inputTokens: number;
  outputTokens: number;
  durationS: number;
}

/**
 * Did this journal row actually call a model?
 *
 * `calls.jsonl` also carries deterministic work — A08 records the drawn
 * lockup there, with `model: null` and `transport: "deterministic"`, so the
 * journal shows every step it took. Those rows are real, but they are not
 * model calls: counting them showed A08 making calls it never made, and the
 * spend view grouped them under a model literally named "unknown".
 */
function isModelCall(c: any): boolean {
  return Boolean(c?.model) && c?.transport !== 'deterministic';
}

/** The routing table, mirrored from `pipeline/gtm_os/agent_runtime.py`. */
const MODELS: Record<string, string> = {
  reasoning: 'gemini-3.8-flash',
  director: 'gemini-3.8-flash',
  image: 'gemini-3-pro-image',
  meme: 'gemini-3-pro-image',
  video: 'veo-3.1-generate-001',
};

// The catalogue lives in lib/agents.ts, shared with the client views.
const AGENTS: Array<[string, string, GtmAgentRole]> = AGENT_DEFS.map(
  (a) => [a.id, a.name, a.role] as [string, string, GtmAgentRole]);
const DEF = new Map(AGENT_DEFS.map((a) => [a.id, a]));

/**
 * One run file, from whichever side of the seam this process is on.
 *
 * Locally the dashboard reads the pipeline's own directory; there is no reason
 * to make a developer round-trip through a bucket to see a run they just
 * produced. On Cloud Run that directory does not exist, so the same file comes
 * from GCS.
 */
async function runFile(runId: string, name: string): Promise<string | null> {
  if (isDeployed()) return getText(`gtm_runs/${runId}/${name}`);
  try {
    return fs.readFileSync(path.join(RUNS_DIR, runId, name), 'utf-8');
  } catch {
    return null;
  }
}

function parseJsonl(text: string | null): any[] {
  if (!text) return [];
  return text
    .split('\n')
    .filter((l) => l.trim())
    .map((l) => {
      try {
        return JSON.parse(l);
      } catch {
        return null;
      }
    })
    .filter(Boolean);
}

export async function listGtmRunIds(limit = 25): Promise<string[]> {
  if (isDeployed()) return gcsRunIds(limit);
  try {
    return fs
      .readdirSync(RUNS_DIR)
      .filter((d) => d.startsWith('GTM-'))
      .sort()
      .reverse()
      .slice(0, limit);
  } catch {
    return [];
  }
}

/** The founder's decision on a run (approve / revise / kill), if one was given. */
export async function gtmFeedback(runId: string): Promise<any | null> {
  const raw = await runFile(runId, 'feedback.json');
  if (!raw) return null;
  try {
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

export async function gtmRunSummary(runId: string): Promise<any | null> {
  const raw = await runFile(runId, 'summary.json');
  if (!raw) return null;
  try {
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

/**
 * What a run in flight has produced so far.
 *
 * The cycle writes `partial.json` each time the copy, the poster or the video
 * is ready. `summary.json` stays the "finished" marker other routes rely on,
 * so this is a separate file, always read as status "running".
 */
async function gtmRunPartial(runId: string): Promise<any | null> {
  const raw = await runFile(runId, 'partial.json');
  if (!raw) return null;
  try {
    return { ...JSON.parse(raw), status: 'running' };
  } catch {
    return null;
  }
}

/**
 * Per-agent status for one run, or for the latest run when none is given.
 *
 * `status` comes from stages.jsonl; the token and call counts come from
 * calls.jsonl. An agent with `kind: DETERMINISTIC` is expected to show zero
 * model calls — that is correct, not a fault, and the UI should not flag it.
 */
export async function gtmAgents(runId?: string): Promise<{
  runId: string | null;
  agents: GtmAgent[];
  summary: any | null;
}> {
  const rid = runId || (await listGtmRunIds(1))[0];
  const blank = (): GtmAgent[] =>
    AGENTS.map(([id, name, role], i) => ({
      n: i + 1, id, name, role, code: DEF.get(id)!.code,
      learns: DEF.get(id)!.learns ?? null, fixed: DEF.get(id)!.fixed ?? null,
      model: role === 'none' ? null : MODELS[role],
      kind: role === 'none' ? 'DETERMINISTIC' : 'MODEL_BACKED',
      status: 'never_ran', detail: '', outputs: [], at: null,
      modelCalls: 0, modelCallsOk: 0, inputTokens: 0, outputTokens: 0, durationS: 0,
    }));

  if (!rid) return { runId: null, agents: blank(), summary: null };

  const stages = parseJsonl(await runFile(rid, 'stages.jsonl'));
  const calls = parseJsonl(await runFile(rid, 'calls.jsonl'));

  // The cycle's stage wrapper writes a second row after an agent has already
  // recorded its own with artifact paths on it. Taking the last row alone
  // dropped those paths, so a rendered PNG existed with no link to it.
  const lastStage = new Map<string, any>();
  for (const s of stages) {
    const prior = lastStage.get(s.agent);
    const outputs = Array.from(new Set([...(prior?.outputs ?? []), ...(s.outputs ?? [])]));
    lastStage.set(s.agent, { ...s, outputs });
  }

  const byAgentCalls = new Map<string, any[]>();
  for (const c of calls) {
    if (!isModelCall(c)) continue;
    const arr = byAgentCalls.get(c.agent) || [];
    arr.push(c);
    byAgentCalls.set(c.agent, arr);
  }

  const agents: GtmAgent[] = AGENTS.map(([id, name, role], i) => {
    const s = lastStage.get(id);
    const cs = byAgentCalls.get(id) || [];
    return {
      n: i + 1, id, name, role, code: DEF.get(id)!.code,
      learns: DEF.get(id)!.learns ?? null, fixed: DEF.get(id)!.fixed ?? null,
      model: role === 'none' ? null : MODELS[role],
      kind: role === 'none' ? 'DETERMINISTIC' : 'MODEL_BACKED',
      status: s?.status ?? 'never_ran',
      detail: s?.detail ?? '',
      outputs: s?.outputs ?? [],
      at: s?.at ?? null,
      modelCalls: cs.length,
      modelCallsOk: cs.filter((c) => c.ok).length,
      inputTokens: cs.reduce((a, c) => a + (c.input_tokens || 0), 0),
      outputTokens: cs.reduce((a, c) => a + (c.output_tokens || 0), 0),
      durationS: Number(cs.reduce((a, c) => a + (c.duration_s || 0), 0).toFixed(2)),
    };
  });

  return { runId: rid, agents, summary: await gtmRunSummary(rid) };
}

/** Everything one run produced, for the detail and per-section views. */
export async function gtmRunDetail(runId?: string) {
  const rid = runId || (await listGtmRunIds(1))[0];
  if (!rid) return null;

  // A run in flight has a journal but no summary.json yet — it is written when
  // the cycle finishes. Returning null 404'd the whole view for the two-to-four
  // minutes a cycle takes, which is exactly when someone is watching it.
  // A run in flight shows what it has made so far — the copy, the poster,
  // the video — as each one lands, not only once the cycle closes.
  const s = (await gtmRunSummary(rid)) ?? (await gtmRunPartial(rid)) ?? { status: 'running' };
  const { agents } = await gtmAgents(rid);

  return {
    runId: rid,
    status: s.status,
    reason: s.reason ?? null,
    signal: s.signal ?? null,
    actionStatus: s.action_status ?? null,
    machine: s.machine ?? null,
    pillar: s.pillar ?? null,
    visualConcept: s.visual_concept ?? null,
    visualArchetype: s.visual_archetype ?? null,
    visualWhy: s.visual_why ?? null,
    posterBrief: s.poster_brief ?? null,
    motionPlan: s.motion_plan ?? null,
    videoMode: s.video_mode ?? null,
    videoReview: s.video_review ?? null,
    visualReview: s.visual_review ?? null,
    source: s.source ?? null,
    visualRenderer: s.visual_renderer ?? null,
    posts: s.posts ?? {},
    spendByModel: s.spend_by_model ?? null,
    reviewPassed: s.review_passed ?? null,
    reviewNotes: s.review_notes ?? null,
    creativeReview: s.creative_review ?? null,
    startedAt: s.started_at ?? null,
    durationS: s.duration_s ?? 0,
    inFlight: !s.ended_at,
    inputTokens: s.input_tokens ?? 0,
    outputTokens: s.output_tokens ?? 0,
    modelCalls: s.model_calls ?? 0,
    modelCallsOk: s.model_calls_ok ?? 0,
    modelsUsed: s.models_used ?? [],
    selection: s.selection ?? null,
    candidateSignals: s.candidate_signals ?? [],
    signalSourceType: s.signal_source_type ?? null,
    signalObservedAt: s.signal_observed_at ?? null,
    strategyReasoning: s.strategy_reasoning ?? [],
    problem: s.problem ?? null,
    opportunity: s.opportunity ?? null,
    audience: s.audience ?? null,
    proofClaims: s.proof_claims ?? [],
    agents,
    artifacts: {
      visual: s.visual_path ? '/api/gtm/artifact/' + rid + '/visual' : null,
      meme: s.meme_path ? '/api/gtm/artifact/' + rid + '/meme' : null,
      video: s.video_path ? '/api/gtm/artifact/' + rid + '/video' : null,
    },
  };
}

/** Recent runs, newest first, for the Runs view. */
export async function gtmRuns(limit = 15) {
  const ids = await listGtmRunIds(limit);
  const out = await Promise.all(
    ids.map(async (id) => {
      const s = await gtmRunSummary(id);
      if (!s) return null;
      return {
        runId: id,
        status: s.status,
        signal: s.signal ?? null,
        machine: s.machine ?? null,
        agentsRan: s.agents_ran ?? 0,
        modelCalls: s.model_calls ?? 0,
        modelCallsOk: s.model_calls_ok ?? 0,
        modelsUsed: s.models_used ?? [],
        inputTokens: s.input_tokens ?? 0,
        outputTokens: s.output_tokens ?? 0,
        durationS: s.duration_s ?? 0,
        startedAt: s.started_at ?? null,
        hasVisual: Boolean(s.visual_path),
        hasVideo: Boolean(s.video_path),
        hasMeme: Boolean(s.meme_path),
        reviewPassed: s.review_passed ?? null,
      };
    }),
  );
  return out.filter(Boolean);
}

/**
 * A run artifact, from whichever side of the seam this process is on.
 *
 * Locally this is a file path; deployed it is a GCS object key. The route
 * needs bytes either way, so both resolve to bytes here rather than leaking
 * the difference into the route handler.
 */
export async function gtmArtifact(
  runId: string,
  kind: 'visual' | 'meme' | 'video',
): Promise<{ body: Buffer; contentType: string } | null> {
  const type = kind === 'video' ? 'video/mp4' : 'image/png';

  if (isDeployed()) {
    const ext = kind === 'video' ? 'mp4' : 'png';
    const got = await getBytes('assets/' + runId + '/' + kind + '.' + ext);
    return got ? { body: Buffer.from(got.body), contentType: type } : null;
  }

  const s = (await gtmRunSummary(runId)) ?? (await gtmRunPartial(runId));
  if (!s) return null;
  const raw = kind === 'visual' ? s.visual_path : kind === 'meme' ? s.meme_path : s.video_path;
  if (!raw) return null;

  // Guard against traversal: whatever the summary holds must resolve inside
  // the pipeline's own state directory.
  const resolved = path.resolve(String(raw));
  const stateRoot = path.resolve(path.join(REPO_ROOT, 'pipeline', 'state'));
  if (!resolved.startsWith(stateRoot) || !fs.existsSync(resolved)) return null;
  return { body: fs.readFileSync(resolved), contentType: type };
}

/**
 * A GTM run in the shape the existing views already consume.
 *
 * The Runs Observatory, Run Detail, Posts and Memes views were built against
 * `legacyRun()` from lib/v2.ts, which reads the `core/` pipeline — a different
 * system from the founder's 13 agents. This emits the same keys from GTM data
 * so `core/` stops being a data source for any surface.
 */
export async function gtmLegacyRun(runId: string): Promise<Record<string, unknown> | null> {
  const d = await gtmRunDetail(runId);
  if (!d) return null;

  const agent_outputs: Record<string, unknown> = {};
  for (const a of d.agents) {
    if (a.status === 'never_ran') continue;
    agent_outputs[a.id] = {
      kind: a.kind, name: a.name, status: a.status, model: a.model, role: a.role,
      input_tokens: a.inputTokens, output_tokens: a.outputTokens,
      duration_s: a.durationS, detail: a.detail, outputs: a.outputs,
      tool_calls: a.modelCalls > 0 ? [a.model + ' x' + a.modelCalls] : [],
      degraded_reason: a.status === 'degraded' ? a.detail : null,
      error: a.status === 'failed' ? a.detail : null,
    };
  }

  const blocked =
    d.reviewPassed === false
      ? ('pre-delivery firewall blocked this run: ' +
          JSON.stringify(d.reviewNotes ?? {})).slice(0, 400)
      : null;

  const startedUnix = d.startedAt ? Math.floor(Date.parse(d.startedAt) / 1000) : null;

  // Priced from the per-model tally the cycle writes at finish. A run
  // recorded before that field existed has no tally, so it stays unpriced
  // rather than being priced from a total that omits the media calls.
  const rates = await modelRates();
  const tally: Record<string, { calls: number; input_tokens: number; output_tokens: number }> =
    (d.spendByModel && typeof d.spendByModel === 'object') ? d.spendByModel : {};
  const tallied = Object.keys(tally);
  const unpricedForRun = tallied.length
    ? tallied.filter((m) => rateCost(rates[m], 1, 0, 0) === null)
    : d.modelsUsed;
  let runCostUsd: number | null = null;
  if (tallied.length) {
    let acc = 0;
    let any = false;
    for (const [m, v] of Object.entries(tally)) {
      const c = rateCost(rates[m], v.calls, v.input_tokens, v.output_tokens);
      if (c === null) continue;
      acc += c;
      any = true;
    }
    runCostUsd = any ? acc : null;
  }

  return {
    run_id: d.runId,
    title: d.signal || d.runId,
    trend: d.signal,
    directive: d.signal,
    // These views do `new Date(started * 1000)` — they want unix seconds, not
    // an ISO string. Passing the string through produced NaN and the whole
    // dashboard died on `Invalid time value`.
    started: startedUnix,
    ended: startedUnix && d.durationS ? startedUnix + Math.round(d.durationS) : null,
    duration_s: d.durationS,
    status: d.status,
    brain: d.modelsUsed[0] ?? null,
    stages_total: d.agents.length,
    stages_succeeded: d.agents.filter((a) => a.status === 'ok').length,
    degraded: d.agents.filter((a) => a.status === 'degraded').map((a) => a.id),
    failed: d.agents.filter((a) => a.status === 'failed').map((a) => a.id),
    agents_declared: d.agents.length,
    agents_that_reasoned: d.agents.filter((a) => a.modelCallsOk > 0).length,
    agent_outputs,
    spend: {
      // Cost is real now. `pipeline/state/model_rates.json` holds the
      // published Google rates and the summary holds a per-model tally, so
      // the media calls — which are billed per call and report no tokens, and
      // which are most of a full run's cost — are priced rather than skipped.
      // Still null, never 0, for any run whose models are not all in the
      // table: a 0 reads as free, and "not priced" is a different fact.
      cost_usd: runCostUsd,
      cost_complete: runCostUsd !== null && unpricedForRun.length === 0,
      unpriced_models: unpricedForRun,
      input_tokens: d.inputTokens,
      output_tokens: d.outputTokens,
      calls: d.modelCalls,
    },
    visual: d.artifacts.visual,
    video: d.artifacts.video,
    meme: d.artifacts.meme,
    machine: d.machine,
    pillar: d.pillar,
    visual_concept: d.visualConcept,
    visual_archetype: d.visualArchetype,
    visual_why: d.visualWhy,
    poster_brief: d.posterBrief,
    motion_plan: d.motionPlan,
    video_mode: d.videoMode,
    video_review: d.videoReview,
    visual_review: d.visualReview,
    source: d.source,
    visual_renderer: d.visualRenderer,
    posts: d.posts,
    models_used: d.modelsUsed,
    publishable: d.reviewPassed === true,
    blocked_reason: blocked,
    // The judge's real per-asset verdicts and the firewall's findings. These
    // were parsed and then dropped here, so the Gates view had no data to
    // render and showed four hardcoded PASS cards instead — over a run the
    // judge had actually rejected.
    creative_review: d.creativeReview,
    review_passed: d.reviewPassed,
    review_notes: d.reviewNotes,
    // A11 never dispatches unprompted, so "published" is a claim only the
    // dispatch stage can support.
    dispatched:
      d.agents.find((a) => a.id.startsWith('A11'))?.status === 'ok',
    dispatch_detail:
      d.agents.find((a) => a.id.startsWith('A11'))?.detail ?? null,
    decisions: [],
    reasoning: {
      arc: d.pillar,
      audience: d.audience,
      playbook: d.machine,
      hook: (d.posts as any)?.x?.hook ?? null,
      claims: 0,
      verified: 0,
    },
  };
}

export async function gtmLegacyRuns(limit = 50): Promise<Record<string, unknown>[]> {
  const ids = await listGtmRunIds(limit);
  const out = await Promise.all(ids.map((id) => gtmLegacyRun(id)));
  return out.filter((r): r is Record<string, unknown> => r !== null);
}

/**
 * Published rates per model, if the operator has supplied them.
 *
 * `pipeline/state/model_rates.json` (pushed to the bucket as
 * `config/model_rates.json`) maps a model id to its billing rate. Nothing is
 * assumed: a model absent from the file stays unpriced rather than being
 * guessed at, because a made-up rate would produce a made-up invoice.
 *
 *   {
 *     "gemini-3.8-flash":       {"input_per_1m": 0.0, "output_per_1m": 0.0},
 *     "gemini-3.1-flash-image": {"per_call": 0.0},
 *     "veo-3.1-generate-001":   {"per_call": 0.0}
 *   }
 */
export interface ModelRate {
  input_per_1m?: number;
  output_per_1m?: number;
  per_call?: number;
}

async function modelRates(): Promise<Record<string, ModelRate>> {
  try {
    const raw = isDeployed()
      ? await getText('config/model_rates.json')
      : (() => {
          const p = path.join(REPO_ROOT, 'pipeline', 'state', 'model_rates.json');
          return fs.existsSync(p) ? fs.readFileSync(p, 'utf-8') : null;
        })();
    if (!raw) return {};
    const parsed = JSON.parse(raw) as Record<string, ModelRate>;
    return parsed && typeof parsed === 'object' ? parsed : {};
  } catch {
    return {};
  }
}

/** Cost of one model's usage, or null when no rate is published for it. */
function rateCost(
  rate: ModelRate | undefined,
  calls: number,
  inputTokens: number,
  outputTokens: number,
): number | null {
  if (!rate) return null;
  const hasToken = rate.input_per_1m != null || rate.output_per_1m != null;
  const hasCall = rate.per_call != null;
  if (!hasToken && !hasCall) return null;
  return (
    (inputTokens / 1_000_000) * (rate.input_per_1m ?? 0) +
    (outputTokens / 1_000_000) * (rate.output_per_1m ?? 0) +
    calls * (rate.per_call ?? 0)
  );
}

/** Aggregate spend across GTM runs, in the shape the Cost view consumes. */
export async function gtmSpend(capUsd = 10) {
  const ids = await listGtmRunIds(200);
  const rates = await modelRates();
  const byModel = new Map<
    string,
    { model: string; roles: Set<string>; calls: number; inputTokens: number; outputTokens: number }
  >();
  let calls = 0;
  let inputTokens = 0;
  let outputTokens = 0;

  for (const id of ids) {
    for (const c of parseJsonl(await runFile(id, 'calls.jsonl'))) {
      if (!isModelCall(c)) continue;
      const m = String(c.model);
      const row =
        byModel.get(m) ??
        { model: m, roles: new Set<string>(), calls: 0, inputTokens: 0, outputTokens: 0 };
      row.roles.add(String(c.role ?? '?'));
      row.calls += 1;
      row.inputTokens += c.input_tokens || 0;
      row.outputTokens += c.output_tokens || 0;
      byModel.set(m, row);
      calls += 1;
      inputTokens += c.input_tokens || 0;
      outputTokens += c.output_tokens || 0;
    }
  }

  const rows = [...byModel.values()].map((r) => {
    const cost = rateCost(rates[r.model], r.calls, r.inputTokens, r.outputTokens);
    return {
      model: r.model,
      roles: [...r.roles],
      calls: r.calls,
      inputTokens: r.inputTokens,
      outputTokens: r.outputTokens,
      costUsd: cost,
      costKnown: cost !== null,
    };
  });

  const unpricedModels = rows.filter((r) => !r.costKnown).map((r) => r.model);
  const priced = rows.filter((r) => r.costKnown);

  return {
    capUsd,
    // Null, never 0, while any model is unpriced. A 0 reads as "this cost
    // nothing", which is a stronger and more wrong claim than "unknown".
    costUsd: priced.length ? priced.reduce((a, r) => a + (r.costUsd ?? 0), 0) : null,
    costComplete: unpricedModels.length === 0 && rows.length > 0,
    unpricedModels,
    calls,
    inputTokens,
    outputTokens,
    runs: ids.length,
    byModel: rows,
  };
}

/**
 * What A01 actually brought back on a run, and from where.
 *
 * The summary keeps only a headline, a type and a date per candidate, so
 * everything answering "which source, whose news, pulled when" was discarded
 * once A02 picked a winner. `harvest.json` is the full record; this reads it
 * for the Scraped Intelligence view.
 */
export async function gtmHarvest(runId?: string) {
  const rid = runId || (await listGtmRunIds(1))[0];
  if (!rid) return null;

  // The newest run may have aborted before A01 wrote anything, so fall back
  // through recent runs rather than showing an empty page.
  const ids = runId ? [runId] : await listGtmRunIds(8);
  for (const id of ids) {
    const raw = await runFile(id, 'harvest.json');
    if (!raw) continue;
    try {
      const h = JSON.parse(raw);
      const signals = Array.isArray(h.signals) ? h.signals : [];

      // Group by publisher and by company so the view can show both without
      // recomputing them per render.
      const bySource = new Map<string, number>();
      const byCompany = new Map<string, number>();
      const companyCase = new Map<string, string>();
      for (const s of signals) {
        const src = String(s.source_root || s.source_type || 'unknown');
        bySource.set(src, (bySource.get(src) ?? 0) + 1);
        for (const e of s.entities ?? []) {
          if (e === '(unattributed)') continue;
          // Archive signals carry lowercase entities and the live extractor
          // capitalises, so "aave" and "Aave" were counted as two companies.
          // Key on the lowered form, display the best-cased spelling seen.
          const key = String(e).toLowerCase();
          const prior = companyCase.get(key);
          if (!prior || (prior === prior.toLowerCase() && e !== key)) {
            companyCase.set(key, String(e));
          }
          byCompany.set(key, (byCompany.get(key) ?? 0) + 1);
        }
      }
      const rank = (m: Map<string, number>, display?: Map<string, string>) =>
        [...m.entries()]
          .sort((a, b) => b[1] - a[1])
          .map(([name, count]) => ({ name: display?.get(name) ?? name, count }));

      return {
        runId: id,
        scrapedAt: h.scraped_at ?? null,
        sources: h.sources ?? {},
        totalSignals: signals.length,
        signals,
        bySource: rank(bySource),
        byCompany: rank(byCompany, companyCase),
      };
    } catch {
      continue;
    }
  }
  return null;
}

/* -------------------------------------------------------------------------
 * Vanna References — each scraped item with its source, and what it is for.
 *
 * `harvest.json` holds the references and `analysis.json` holds A02's reading
 * of them: a grade, a move per relevant signal, and strategies that cite
 * signal ids. Neither file was shown next to the other, so the dashboard
 * listed links and never said what Vanna could do with any of them. This
 * joins them per signal, and resolves every strategy's citations back to the
 * items it rests on.
 * ---------------------------------------------------------------------- */

export type RefKind = 'post' | 'docs' | 'news' | 'data';

/** What kind of reference a signal is, from the id prefix the collector set. */
function refKind(s: any): { kind: RefKind; channel: string } | null {
  const id = String(s.signal_id || '');
  const tag = id.split('-')[1]?.toUpperCase() ?? '';
  if (String(s.source_type) === 'ARCHIVE' || tag === 'OPP') return null;
  if (tag === 'TWITTER') return { kind: 'post', channel: 'X' };
  if (tag === 'REDDIT') return { kind: 'post', channel: 'Reddit' };
  if (tag === 'TG') return { kind: 'post', channel: 'Telegram' };
  if (tag === 'DOCS') return { kind: 'docs', channel: 'Docs & blogs' };
  if (tag === 'NEWS') return { kind: 'news', channel: 'News' };
  if (tag === 'LLAMA') return { kind: 'data', channel: 'DefiLlama' };
  // An unknown collector is still a live reference; call it news rather than
  // dropping it, and keep the raw source type visible.
  return { kind: 'news', channel: String(s.source_root || s.source_type || 'Other') };
}

export async function gtmReferences(runId?: string) {
  const ids = runId ? [runId] : await listGtmRunIds(10);

  // Which recent runs have a harvest, and which were read by A02 — the view
  // offers these as a selector, because the newest run is not always the one
  // with a reading (A02 degrades on a bad model reply and the run goes on).
  const recent: { runId: string; hasAnalysis: boolean }[] = [];
  let chosen: { id: string; harvest: any; analysis: any } | null = null;
  for (const id of ids) {
    const h = await runFile(id, 'harvest.json');
    if (!h) continue;
    const a = await runFile(id, 'analysis.json');
    recent.push({ runId: id, hasAnalysis: Boolean(a) });
    if (!chosen) {
      try {
        chosen = { id, harvest: JSON.parse(h), analysis: a ? JSON.parse(a) : null };
      } catch {
        /* a half-written file; try the next run */
      }
    }
  }
  if (!chosen) return null;

  // When the chosen run was not read, say why, from A02's own journal line.
  let analysisNote: string | null = null;
  if (!chosen.analysis) {
    const stages = await runFile(chosen.id, 'stages.jsonl');
    const line = (stages ?? '')
      .split('\n')
      .map((l) => { try { return JSON.parse(l); } catch { return null; } })
      .filter((r) => r && r.agent === 'A02_market_analyst')
      .pop();
    analysisNote = line
      ? `A02 ${line.status}: ${String(line.detail ?? '').slice(0, 200)}`
      : 'A02 did not run on this cycle.';
  }

  const readings = new Map<string, any>();
  for (const r of chosen.analysis?.signals ?? []) readings.set(String(r.signal_id), r);

  const items: any[] = (chosen.harvest.signals ?? [])
    .map((s: any) => {
      const k = refKind(s);
      if (!k) return null;
      const r = readings.get(String(s.signal_id));
      const url = String(s.source || '');
      return {
        id: String(s.signal_id),
        kind: k.kind,
        channel: k.channel,
        headline: String(s.headline || ''),
        url: /^https?:\/\//.test(url) ? url : null,
        publisher: String(s.source_root || ''),
        observedAt: s.observed_at ?? null,
        entities: (s.entities ?? []).filter((e: string) => e !== '(unattributed)'),
        whatItIs: r?.what_it_is ?? null,
        relevance: (r?.relevance ?? null) as 'DIRECT' | 'ADJACENT' | 'NONE' | null,
        why: r?.why ?? null,
        vannaMove: r?.vanna_move || null,
      };
    })
    .filter(Boolean);

  const byId = new Map<string, any>(items.map((i) => [i.id, i] as [string, any]));
  const land = chosen.analysis?.landscape ?? null;
  const cite = (sids: any) =>
    (Array.isArray(sids) ? sids : [])
      .map((sid: any) => byId.get(String(sid)))
      .filter(Boolean)
      .map((i: any) => ({ id: i.id, headline: i.headline, url: i.url, channel: i.channel }));

  const counts: Record<RefKind, number> = { post: 0, docs: 0, news: 0, data: 0 };
  for (const i of items) counts[i.kind as RefKind] += 1;

  return {
    runId: chosen.id,
    scrapedAt: chosen.harvest.scraped_at ?? null,
    recent,
    analysisNote,
    counts,
    items,
    landscape: land
      ? {
          summary: land.summary ?? '',
          forVanna: land.for_vanna ?? '',
          quietOn: land.quiet_on ?? [],
          themes: (land.themes ?? []).map((t: any) => ({
            theme: t.theme, whatIsHappening: t.what_is_happening,
            mattersToVanna: Boolean(t.matters_to_vanna), cites: cite(t.signal_ids),
          })),
          strategies: (land.strategies ?? []).map((st: any) => ({
            title: st.title, move: st.move, rationale: st.rationale,
            horizon: st.horizon ?? null, cites: cite(st.signal_ids),
          })),
        }
      : null,
  };
}

/** The agents as a manifest, in the shape the pipeline views consume. */
export function gtmManifest() {
  return AGENTS.map(([id, name, role], i) => ({
    n: i + 1,
    stage: id,
    kind: role === 'none' ? 'DETERMINISTIC' : 'MODEL_BACKED',
    purpose: name,
    model: role === 'none' ? null : MODELS[role],
  }));
}
