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

const REPO_ROOT = path.resolve(process.cwd(), '..');
const RUNS_DIR = path.join(REPO_ROOT, 'pipeline', 'state', 'gtm_runs');

export type GtmAgentRole = 'reasoning' | 'image' | 'meme' | 'video' | 'none';

export interface GtmAgent {
  n: number;
  id: string;
  name: string;
  role: GtmAgentRole;
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

/** The routing table, mirrored from `pipeline/gtm_os/agent_runtime.py`. */
const MODELS: Record<string, string> = {
  reasoning: 'gemini-3.8-flash',
  image: 'gemini-3.1-flash-image',
  meme: 'nano-banana-pro-preview',
  video: 'veo-3.1-generate-001',
};

const AGENTS: Array<[string, string, GtmAgentRole]> = [
  ['A01_intelligence_scout', 'Intelligence Scout', 'none'],
  ['A02_opportunity_selector', 'Opportunity Selector', 'reasoning'],
  ['A03_gtm_strategist', 'GTM Strategist', 'reasoning'],
  ['A04_machine_library', 'GTM Machine Library', 'none'],
  ['A05_campaign_engine', 'Campaign & Series Engine', 'none'],
  ['A06_channel_adapter', 'Content Creator & Channel Adapter', 'reasoning'],
  ['A07_creative_director', 'Creative Director System', 'reasoning'],
  ['A08_visual_synthesis', 'Visual Synthesis Engine', 'image'],
  ['A09_video_production', 'Video Production Engine', 'video'],
  ['A10_reviewer_firewall', 'Pre-Delivery Reviewer Firewall', 'none'],
  ['A11_dispatch_worker', 'Approved Dispatch Worker', 'none'],
  ['A12_telegram_gateway', 'Telegram Gateway & Listener', 'none'],
  ['A13_learning_engine', 'Closed-Loop Learning Engine', 'reasoning'],
];

function readJsonl(file: string): any[] {
  try {
    return fs
      .readFileSync(file, 'utf-8')
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
  } catch {
    return [];
  }
}

export function listGtmRunIds(limit = 25): string[] {
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

export function gtmRunSummary(runId: string): any | null {
  try {
    return JSON.parse(
      fs.readFileSync(path.join(RUNS_DIR, runId, 'summary.json'), 'utf-8'),
    );
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
export function gtmAgents(runId?: string): {
  runId: string | null;
  agents: GtmAgent[];
  summary: any | null;
} {
  const rid = runId || listGtmRunIds(1)[0];
  if (!rid) {
    return {
      runId: null,
      agents: AGENTS.map(([id, name, role], i) => ({
        n: i + 1,
        id,
        name,
        role,
        model: role === 'none' ? null : MODELS[role],
        kind: role === 'none' ? 'DETERMINISTIC' : 'MODEL_BACKED',
        status: 'never_ran',
        detail: '',
        outputs: [],
        at: null,
        modelCalls: 0,
        modelCallsOk: 0,
        inputTokens: 0,
        outputTokens: 0,
        durationS: 0,
      })),
      summary: null,
    };
  }

  const dir = path.join(RUNS_DIR, rid);
  const stages = readJsonl(path.join(dir, 'stages.jsonl'));
  const calls = readJsonl(path.join(dir, 'calls.jsonl'));

  // Last stage row per agent wins: an agent that degraded and then recovered
  // should not be reported by its first attempt.
  const lastStage = new Map<string, any>();
  for (const s of stages) {
    const prior = lastStage.get(s.agent);
    // The cycle's stage wrapper writes a second row after an agent has already
    // recorded its own with artifact paths on it. Taking the last row alone
    // dropped those paths, so a rendered PNG existed with no link to it.
    const outputs = Array.from(
      new Set([...(prior?.outputs ?? []), ...(s.outputs ?? [])]),
    );
    lastStage.set(s.agent, { ...s, outputs });
  }

  const byAgentCalls = new Map<string, any[]>();
  for (const c of calls) {
    const arr = byAgentCalls.get(c.agent) || [];
    arr.push(c);
    byAgentCalls.set(c.agent, arr);
  }

  const agents: GtmAgent[] = AGENTS.map(([id, name, role], i) => {
    const s = lastStage.get(id);
    const cs = byAgentCalls.get(id) || [];
    return {
      n: i + 1,
      id,
      name,
      role,
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
      durationS: Number(
        cs.reduce((a, c) => a + (c.duration_s || 0), 0).toFixed(2),
      ),
    };
  });

  return { runId: rid, agents, summary: gtmRunSummary(rid) };
}

/** Recent runs, newest first, for the Runs view. */
export function gtmRuns(limit = 15) {
  return listGtmRunIds(limit)
    .map((id) => {
      const s = gtmRunSummary(id);
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
    selection: s.selection ?? null,
    candidateSignals: s.candidate_signals ?? [],
    signalSourceType: s.signal_source_type ?? null,
    signalObservedAt: s.signal_observed_at ?? null,
    strategyReasoning: s.strategy_reasoning ?? [],
    problem: s.problem ?? null,
    opportunity: s.opportunity ?? null,
    audience: s.audience ?? null,
    proofClaims: s.proof_claims ?? [],
      };
    })
    .filter(Boolean);
}

/**
 * Absolute path to a run artifact, guarded against traversal.
 *
 * The artifact route serves whatever this returns, so it must never resolve
 * outside the state directory no matter what the caller passes.
 */
export function gtmArtifactPath(
  runId: string,
  kind: 'visual' | 'video' | 'meme',
): string | null {
  const s = gtmRunSummary(runId);
  if (!s) return null;
  const p =
    kind === 'visual' ? s.visual_path : kind === 'meme' ? s.meme_path : s.video_path;
  if (!p) return null;
  const resolved = path.resolve(String(p));
  const stateRoot = path.resolve(path.join(REPO_ROOT, 'pipeline', 'state'));
  if (!resolved.startsWith(stateRoot)) return null;
  return fs.existsSync(resolved) ? resolved : null;
}


/** Everything one run produced, for the detail and per-section views. */
export function gtmRunDetail(runId?: string) {
  const rid = runId || listGtmRunIds(1)[0];
  if (!rid) return null;
  const s = gtmRunSummary(rid);
  if (!s) return null;
  const { agents } = gtmAgents(rid);

  return {
    runId: rid,
    status: s.status,
    reason: s.reason ?? null,
    signal: s.signal ?? null,
    actionStatus: s.action_status ?? null,
    machine: s.machine ?? null,
    pillar: s.pillar ?? null,
    visualConcept: s.visual_concept ?? null,
    posts: s.posts ?? {},
    reviewPassed: s.review_passed ?? null,
    reviewNotes: s.review_notes ?? null,
    startedAt: s.started_at ?? null,
    durationS: s.duration_s ?? 0,
    inputTokens: s.input_tokens ?? 0,
    outputTokens: s.output_tokens ?? 0,
    modelCalls: s.model_calls ?? 0,
    modelCallsOk: s.model_calls_ok ?? 0,
    modelsUsed: s.models_used ?? [],
    agents,
    artifacts: {
      visual: s.visual_path ? `/api/gtm/artifact/${rid}/visual` : null,
      meme: s.meme_path ? `/api/gtm/artifact/${rid}/meme` : null,
      video: s.video_path ? `/api/gtm/artifact/${rid}/video` : null,
    },
  };
}

/**
 * A GTM run in the shape the existing views already consume.
 *
 * The Runs Observatory, Run Detail, Posts and Memes views were all built
 * against `legacyRun()` from lib/v2.ts, which reads the `core/` pipeline's
 * journal — a different system from the founder's 13 agents. Rather than
 * rewrite four large views, this emits the same keys from GTM data, so the
 * dashboard shows the 13 agents everywhere and `core/` stops being a data
 * source for any surface.
 */
export function gtmLegacyRun(runId: string): Record<string, unknown> | null {
  const d = gtmRunDetail(runId);
  if (!d) return null;

  const agent_outputs: Record<string, unknown> = {};
  for (const a of d.agents) {
    if (a.status === 'never_ran') continue;
    agent_outputs[a.id] = {
      kind: a.kind,
      name: a.name,
      status: a.status,
      model: a.model,
      role: a.role,
      input_tokens: a.inputTokens,
      output_tokens: a.outputTokens,
      duration_s: a.durationS,
      detail: a.detail,
      outputs: a.outputs,
      // Kept for view compatibility: these surfaces render `tool_calls`.
      tool_calls: a.modelCalls > 0 ? [`${a.model} x${a.modelCalls}`] : [],
      degraded_reason: a.status === 'degraded' ? a.detail : null,
      error: a.status === 'failed' ? a.detail : null,
    };
  }

  const blocked =
    d.reviewPassed === false
      ? `pre-delivery firewall blocked this run: ${JSON.stringify(d.reviewNotes ?? {})}`.slice(0, 400)
      : null;

  return {
    run_id: d.runId,
    title: d.signal || d.runId,
    trend: d.signal,
    directive: d.signal,
    // These views do `new Date(started * 1000)` — they want unix seconds, not
    // an ISO string. Passing the ISO string through produced NaN and the whole
    // dashboard died on `Invalid time value`.
    started: d.startedAt ? Math.floor(Date.parse(d.startedAt) / 1000) : null,
    ended:
      d.startedAt && d.durationS
        ? Math.floor(Date.parse(d.startedAt) / 1000) + Math.round(d.durationS)
        : null,
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
      // Token counts are measured. Cost is not: the GTM agents call through
      // Model Garden and the API key, and no per-model rate table is wired, so
      // reporting a dollar figure here would be inventing one.
      cost_usd: null,
      cost_complete: false,
      unpriced_models: d.modelsUsed,
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
    posts: d.posts,
    models_used: d.modelsUsed,
    publishable: d.reviewPassed === true,
    blocked_reason: blocked,
    decisions: [],
    reasoning: {
      arc: d.pillar,
      audience: null,
      playbook: d.machine,
      hook: (d.posts as any)?.x?.hook ?? null,
      claims: 0,
      verified: 0,
    },
  };
}

export function gtmLegacyRuns(limit = 50): Record<string, unknown>[] {
  return listGtmRunIds(limit)
    .map((id) => gtmLegacyRun(id))
    .filter((r): r is Record<string, unknown> => r !== null);
}

/** Aggregate spend across GTM runs, in the shape the Cost view consumes. */
export function gtmSpend(capUsd = 10) {
  const ids = listGtmRunIds(200);
  const byModel = new Map<
    string,
    { model: string; roles: Set<string>; calls: number; inputTokens: number; outputTokens: number }
  >();
  let calls = 0;
  let inputTokens = 0;
  let outputTokens = 0;

  for (const id of ids) {
    for (const c of readJsonl(path.join(RUNS_DIR, id, 'calls.jsonl'))) {
      const m = String(c.model ?? 'unknown');
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

  return {
    capUsd,
    // Deliberately null, not 0. No rate table is wired for Model Garden or the
    // API key, so any dollar figure here would be invented — and a 0 reads as
    // "this cost nothing", which is worse than "unpriced".
    costUsd: null,
    costComplete: false,
    unpricedModels: [...byModel.keys()],
    calls,
    inputTokens,
    outputTokens,
    runs: ids.length,
    byModel: [...byModel.values()].map((r) => ({
      model: r.model,
      roles: [...r.roles],
      calls: r.calls,
      inputTokens: r.inputTokens,
      outputTokens: r.outputTokens,
      costUsd: null,
      costKnown: false,
    })),
  };
}

/** The 13 agents as a manifest, in the shape the pipeline views consume. */
export function gtmManifest() {
  return AGENTS.map(([id, name, role], i) => ({
    n: i + 1,
    stage: id,
    kind: role === 'none' ? 'DETERMINISTIC' : 'MODEL_BACKED',
    purpose: name,
    model: role === 'none' ? null : MODELS[role],
  }));
}
