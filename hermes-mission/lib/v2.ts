/**
 * v2 data access — reads the pipeline's append-only journal directly.
 *
 * Two audit findings this replaces:
 *
 *  1. Every job-trigger route spawned a bare `python`, which does not exist on
 *     this machine, so every button failed. Nothing here spawns a process:
 *     triggering a run writes a JSON file into the queue, and a supervised
 *     worker picks it up.
 *  2. `lib/api.ts` promised "zero mock runs, zero static fixtures" and then
 *     returned `MISSION_DATA` fixtures from a catch-all. Here a read failure
 *     returns an explicit error the UI must render. There is no fixture to
 *     fall back to.
 */
import fs from 'fs';
import path from 'path';

export const REPO_ROOT = process.env.VANNA_REPO_ROOT ?? path.resolve(process.cwd(), '..');
const STATE = path.join(REPO_ROOT, 'state');
const RUNS_DIR = path.join(STATE, 'runs');
const QUEUE_DIR = path.join(STATE, 'queue');

export type StageKind = 'AGENT' | 'STAGE';

export interface ManifestStage {
  n: number;
  stage: string;
  kind: StageKind;
  purpose: string;
}

export interface StageView {
  stage: string;
  kind: StageKind | null;
  purpose: string;
  state: string;            // queued | running | succeeded | degraded | failed | not_reached
  status: string | null;    // ok | degraded | failed
  durationS: number | null;
  model: string | null;
  promptVersion: string | null;
  inputTokens: number;
  outputTokens: number;
  costUsd: number;
  costKnown: boolean;
  attempts: number;
  toolCalls: string[];
  degradedReason: string | null;
  error: string | null;
  /** True when this stage is declared an AGENT and actually called a model. */
  agentDidCallModel: boolean | null;
}

export interface RunView {
  runId: string;
  directive: string;
  status: string;
  startedAt: number | null;
  endedAt: number | null;
  durationS: number | null;
  stages: StageView[];
  degraded: string[];
  failed: string[];
  costUsd: number;
  costComplete: boolean;
  unpricedModels: string[];
  inputTokens: number;
  outputTokens: number;
  modelCalls: number;
  agentsDeclared: number;
  agentsThatCalledModel: number;
  decisions: { ts: number; actor: string; action: string; note: string }[];
  artifacts: { name: string; path: string; bytes: number }[];
}

function readJson<T>(p: string): T | null {
  try {
    return JSON.parse(fs.readFileSync(p, 'utf-8')) as T;
  } catch {
    return null;
  }
}

export function manifest(): ManifestStage[] {
  const m = readJson<{ stages: ManifestStage[] }>(path.join(STATE, 'manifest.json'));
  return m?.stages ?? [];
}

function readEvents(runId: string): any[] {
  const p = path.join(RUNS_DIR, runId, 'events.jsonl');
  let raw: string;
  try {
    raw = fs.readFileSync(p, 'utf-8');
  } catch {
    return [];
  }
  const out: any[] = [];
  for (const line of raw.split('\n')) {
    const t = line.trim();
    if (!t) continue;
    try {
      out.push(JSON.parse(t));
    } catch {
      // a torn final line never hides the events before it
    }
  }
  return out;
}

/** Build the run view from events. Nothing is stored pre-computed, so the view
 *  cannot drift from the journal. */
export function runView(runId: string): RunView | null {
  const events = readEvents(runId);
  if (events.length === 0) return null;

  const man = manifest();
  const byStage = new Map<string, any>();
  const artifacts: RunView['artifacts'] = [];
  const decisions: RunView['decisions'] = [];
  const unpriced = new Set<string>();

  let directive = '';
  let status = 'running';
  let startedAt: number | null = null;
  let endedAt: number | null = null;
  let cost = 0;
  let inTok = 0;
  let outTok = 0;

  for (const e of events) {
    switch (e.kind) {
      case 'run_started':
        startedAt = e.ts;
        directive = e.directive ?? '';
        break;
      case 'stage_started':
        byStage.set(e.stage, { state: 'running', stage: e.stage });
        break;
      case 'stage_ended': {
        const prev = byStage.get(e.stage) ?? { stage: e.stage };
        byStage.set(e.stage, { ...prev, ...e, state: e.state });
        cost += e.cost_usd ?? 0;
        inTok += e.input_tokens ?? 0;
        outTok += e.output_tokens ?? 0;
        if (e.model && e.cost_known === false) unpriced.add(e.model);
        break;
      }
      case 'run_ended':
        endedAt = e.ts;
        status = e.status ?? 'unknown';
        break;
      case 'artifact':
        artifacts.push({ name: e.name, path: e.path, bytes: e.bytes ?? 0 });
        break;
      case 'decision':
        decisions.push({ ts: e.ts, actor: e.actor, action: e.action, note: e.note ?? '' });
        break;
    }
  }

  const stages: StageView[] = man.map((m) => {
    const e = byStage.get(m.stage);
    const calledModel = e?.model ? true : e ? false : null;
    return {
      stage: m.stage,
      kind: m.kind,
      purpose: m.purpose,
      state: e?.state ?? 'not_reached',
      status: e?.status ?? null,
      durationS: e?.duration_s ?? null,
      model: e?.model ?? null,
      promptVersion: e?.prompt_version ?? null,
      inputTokens: e?.input_tokens ?? 0,
      outputTokens: e?.output_tokens ?? 0,
      costUsd: e?.cost_usd ?? 0,
      costKnown: e?.cost_known ?? true,
      attempts: e?.attempts ?? 0,
      toolCalls: e?.tool_calls ?? [],
      degradedReason: e?.degraded_reason ?? null,
      error: e?.error ?? null,
      agentDidCallModel: m.kind === 'AGENT' ? calledModel : null,
    };
  });

  const agentsDeclared = stages.filter((s) => s.kind === 'AGENT').length;
  const agentsThatCalled = stages.filter((s) => s.agentDidCallModel === true).length;

  return {
    runId,
    directive,
    status,
    startedAt,
    endedAt,
    durationS: startedAt && endedAt ? Math.round((endedAt - startedAt) * 100) / 100 : null,
    stages,
    degraded: stages.filter((s) => s.status === 'degraded').map((s) => s.stage),
    failed: stages.filter((s) => s.status === 'failed').map((s) => s.stage),
    costUsd: Math.round(cost * 1e6) / 1e6,
    costComplete: unpriced.size === 0,
    unpricedModels: [...unpriced],
    inputTokens: inTok,
    outputTokens: outTok,
    modelCalls: stages.filter((s) => s.model).length,
    agentsDeclared,
    agentsThatCalledModel: agentsThatCalled,
    decisions,
    artifacts,
  };
}

export function listRunIds(limit = 50): string[] {
  try {
    return fs
      .readdirSync(RUNS_DIR, { withFileTypes: true })
      .filter((d) => d.isDirectory())
      .map((d) => d.name)
      .sort()
      .reverse()
      .slice(0, limit);
  } catch {
    return [];
  }
}

export function queueCounts(): Record<string, number> {
  const out: Record<string, number> = {};
  for (const s of ['pending', 'claimed', 'done', 'dead']) {
    try {
      out[s] = fs.readdirSync(path.join(QUEUE_DIR, s)).filter((f) => f.endsWith('.json')).length;
    } catch {
      out[s] = 0;
    }
  }
  return out;
}

/** Enqueue by writing a file. No child process, no awaited subprocess. */
export function enqueue(directive: string, requestedBy = 'dashboard'): { id: string } {
  const dir = path.join(QUEUE_DIR, 'pending');
  fs.mkdirSync(dir, { recursive: true });
  const stamp = new Date().toISOString().replace(/[-:T]/g, '').slice(0, 15);
  const id = `JOB-${stamp}-${Math.random().toString(16).slice(2, 8)}`;
  const job = {
    id,
    directive: directive.trim(),
    created_at: new Date().toISOString(),
    attempts: 0,
    idempotency_key: null,
    requested_by: requestedBy,
    run_id: null,
    last_error: null,
  };
  const tmp = path.join(dir, `${id}.tmp`);
  fs.writeFileSync(tmp, JSON.stringify(job, null, 2), 'utf-8');
  fs.renameSync(tmp, path.join(dir, `${id}.json`));
  return { id };
}

export interface WorkerHealth {
  state: string;
  pid: number | null;
  ts: number | null;
  ageS: number | null;
  alive: boolean;
}

/** Liveness that cannot go stale unnoticed — the old daemon_status.json
 *  reported RUNNING with a pid that had been dead for a day. */
export function workerHealth(): WorkerHealth {
  const h = readJson<{ state: string; pid: number; ts: number }>(path.join(STATE, 'worker.json'));
  if (!h) return { state: 'never_started', pid: null, ts: null, ageS: null, alive: false };
  const ageS = Math.round(Date.now() / 1000 - h.ts);
  return { state: h.state, pid: h.pid, ts: h.ts, ageS, alive: ageS < 120 };
}

export function artifactPath(runId: string, rel: string): string {
  return path.join(RUNS_DIR, runId, rel);
}

// --------------------------------------------------------------------------
// Spend, aggregated from the run journals
// --------------------------------------------------------------------------

export interface ModelSpend {
  model: string;
  roles: string[];
  calls: number;
  inputTokens: number;
  outputTokens: number;
  costUsd: number;
  costKnown: boolean;
}

export interface SpendView {
  capUsd: number;
  costUsd: number;
  costComplete: boolean;
  unpricedModels: string[];
  calls: number;
  inputTokens: number;
  outputTokens: number;
  runs: number;
  byModel: ModelSpend[];
  byStage: { stage: string; kind: string | null; calls: number; costUsd: number; inputTokens: number; outputTokens: number }[];
  windowFrom: number | null;
}

/**
 * Real spend, derived per model and per stage from what each run recorded.
 *
 * The Cost view previously invented its breakdown by multiplying the real
 * total by hardcoded shares (0.37 / 0.30 / 0.28 / 0.05). Those percentages
 * were not measured — they were typed. Every figure below is summed from
 * journal events, and a model with no published rate is reported as unpriced
 * rather than as costing nothing.
 */
export function spendView(capUsd = 10, limit = 500): SpendView {
  const ids = listRunIds(limit);
  const models = new Map<string, ModelSpend>();
  const stages = new Map<string, SpendView['byStage'][number]>();
  const unpriced = new Set<string>();
  const roleOf = new Map(manifest().map((m) => [m.stage, m.kind as string]));

  let cost = 0, inTok = 0, outTok = 0, calls = 0;
  let from: number | null = null;

  for (const id of ids) {
    const r = runView(id);
    if (!r) continue;
    if (r.startedAt && (from === null || r.startedAt < from)) from = r.startedAt;

    for (const s of r.stages) {
      if (!s.model) continue;
      calls += 1;
      cost += s.costUsd;
      inTok += s.inputTokens;
      outTok += s.outputTokens;
      if (!s.costKnown) unpriced.add(s.model);

      const m = models.get(s.model) ?? {
        model: s.model, roles: [], calls: 0, inputTokens: 0,
        outputTokens: 0, costUsd: 0, costKnown: true,
      };
      m.calls += 1;
      m.inputTokens += s.inputTokens;
      m.outputTokens += s.outputTokens;
      m.costUsd += s.costUsd;
      m.costKnown = m.costKnown && s.costKnown;
      if (!m.roles.includes(s.stage)) m.roles.push(s.stage);
      models.set(s.model, m);

      const st = stages.get(s.stage) ?? {
        stage: s.stage, kind: roleOf.get(s.stage) ?? null,
        calls: 0, costUsd: 0, inputTokens: 0, outputTokens: 0,
      };
      st.calls += 1;
      st.costUsd += s.costUsd;
      st.inputTokens += s.inputTokens;
      st.outputTokens += s.outputTokens;
      stages.set(s.stage, st);
    }
  }

  return {
    capUsd,
    costUsd: Math.round(cost * 1e6) / 1e6,
    costComplete: unpriced.size === 0,
    unpricedModels: [...unpriced],
    calls,
    inputTokens: inTok,
    outputTokens: outTok,
    runs: ids.length,
    byModel: [...models.values()].sort((a, b) => b.outputTokens - a.outputTokens),
    byStage: [...stages.values()].sort((a, b) => b.outputTokens - a.outputTokens),
    windowFrom: from,
  };
}

// --------------------------------------------------------------------------
// Legacy-shape adapter
// --------------------------------------------------------------------------

/**
 * Present a v2 run in the shape the original views read.
 *
 * The older surfaces (Runs Observatory, Run Detail, Lifecycles, Posts) were
 * built against `pipeline/state/runs/*.meta.json`. Rather than leave them
 * pointed at a directory the current pipeline never writes — which is how they
 * came to show nothing while the system claimed to be running — they are fed
 * from the same journal everything else reads.
 *
 * Fields the v2 pipeline does not produce are omitted rather than invented.
 * In particular there are no receipts, no `published_channels`, and no
 * `delivered_to_telegram`.
 */
export function legacyRun(r: RunView): Record<string, unknown> {
  const stage = (name: string) => r.stages.find((s) => s.stage === name);
  const artifact = (suffix: string) =>
    r.artifacts.filter((a) => a.name.endsWith(suffix)).slice(-1)[0] ?? null;

  const png = artifact('.png');
  const mp4 = artifact('.mp4');

  const agent_outputs: Record<string, unknown> = {};
  for (const s of r.stages) {
    if (s.state === 'not_reached') continue;
    agent_outputs[s.stage] = {
      kind: s.kind,
      status: s.status,
      model: s.model,
      prompt_version: s.promptVersion,
      input_tokens: s.inputTokens,
      output_tokens: s.outputTokens,
      duration_s: s.durationS,
      tool_calls: s.toolCalls,
      degraded_reason: s.degradedReason,
      error: s.error,
    };
  }

  const reviewBlocked = stage('review')?.degradedReason ?? null;

  return {
    run_id: r.runId,
    title: r.directive || r.runId,
    trend: r.directive,
    directive: r.directive,
    started: r.startedAt,
    ended: r.endedAt,
    duration_s: r.durationS,
    status: r.status,
    brain: r.stages.find((s) => s.model)?.model ?? null,
    stages_total: r.stages.length,
    stages_succeeded: r.stages.filter((s) => s.status === 'ok').length,
    degraded: r.degraded,
    failed: r.failed,
    agents_declared: r.agentsDeclared,
    agents_that_reasoned: r.agentsThatCalledModel,
    agent_outputs,
    spend: {
      cost_usd: r.costUsd,
      cost_complete: r.costComplete,
      unpriced_models: r.unpricedModels,
      input_tokens: r.inputTokens,
      output_tokens: r.outputTokens,
      calls: r.modelCalls,
    },
    visual: png ? `/api/v2/artifact/${r.runId}?path=${encodeURIComponent(png.path)}` : null,
    video: mp4 ? `/api/v2/artifact/${r.runId}?path=${encodeURIComponent(mp4.path)}` : null,
    // Publication state, stated plainly. `blocked_reason` is present precisely
    // when the gate refused, so a surface cannot render it as shipped.
    publishable: reviewBlocked === null && stage('review')?.status === 'ok',
    blocked_reason: reviewBlocked,
    decisions: r.decisions,
  };
}

export function legacyRuns(limit = 50): Record<string, unknown>[] {
  // The list carries a compact slice of the reasoning too, so the runs table
  // can show the arc and playbook a run actually chose instead of falling back
  // to a constant when the old agent keys are absent.
  return listRunIds(limit)
    .map((id): Record<string, unknown> | null => {
      const r = runView(id);
      if (!r) return null;
      const reasoning = runReasoning(id);
      return {
        ...legacyRun(r),
        reasoning: {
          arc: reasoning.arc,
          audience: reasoning.audience,
          playbook: reasoning.playbook,
          hook: reasoning.hook,
          claims: reasoning.claims?.length ?? 0,
          verified: (reasoning.claims ?? []).filter((c: any) => c?.status === 'verified').length,
        },
      };
    })
    .filter((r): r is Record<string, unknown> => r !== null);
}

// --------------------------------------------------------------------------
// Stage artifacts
// --------------------------------------------------------------------------

/**
 * The JSON a stage actually produced.
 *
 * Surfaces that want to show reasoning — which arc was chosen, which claims
 * were checked, what the gate decided — read it from here. The Live Debate view
 * previously invented three competing arcs with verdicts of WINNER / GRAFTED /
 * REJECTED and scores derived by subtracting 4 and 8 from a single number.
 * None of that happened.
 */
export function stageArtifact<T = unknown>(runId: string, stage: string): T | null {
  const dir = path.join(RUNS_DIR, runId, 'artifacts');
  let names: string[];
  try {
    names = fs.readdirSync(dir);
  } catch {
    return null;
  }
  // Artifacts are content-addressed: `<stage>.<hash>.json`.
  const match = names.filter((n) => n.startsWith(`${stage}.`) && n.endsWith('.json')).sort().pop();
  if (!match) return null;
  try {
    return JSON.parse(fs.readFileSync(path.join(dir, match), 'utf-8')) as T;
  } catch {
    return null;
  }
}

export function runReasoning(runId: string) {
  // Stage 3 is a debate: three strategists argue competing arcs and a judge
  // rules. `strategy` is kept as a fallback for runs recorded before that.
  const debate = stageArtifact<any>(runId, 'debate');
  const strategy = debate?.strategy ?? stageArtifact<any>(runId, 'strategy');
  const plan = stageArtifact<any>(runId, 'plan');
  const copy = stageArtifact<any>(runId, 'copy');
  const verify = stageArtifact<any>(runId, 'verify');
  const concept = stageArtifact<any>(runId, 'concept');
  const gate = stageArtifact<any>(runId, 'gate');
  const review = stageArtifact<any>(runId, 'review');

  return {
    // What the strategist actually decided. One arc, chosen — not three debated.
    arc: strategy?.narrative_arc ?? null,
    audience: strategy?.audience ?? null,
    problem: strategy?.problem_statement ?? null,
    angle: strategy?.angle ?? null,
    playbook: plan?.playbook ?? null,
    vehicle: plan?.vehicle ?? null,
    hook: copy?.hook ?? null,
    body: copy?.body ?? null,
    thread: copy?.thread ?? [],
    claims: Array.isArray(verify) ? verify : [],
    concepts: concept?.all ?? [],
    chosenConcept: concept?.chosen ?? null,
    noveltyNote: concept?.novelty_note ?? null,
    gate: gate ?? null,
    review: review ?? null,
    // The real debate: every brief that was argued, and how it was ruled on.
    debate: debate
      ? {
          winner: debate.winner ?? null,
          briefs: debate.briefs ?? [],
          ruling: debate.ruling ?? null,
          judgeNote: debate.judge_note ?? null,
          failedStrategists: debate.failed_strategists ?? [],
        }
      : null,
  };
}

/**
 * Record a human decision by APPENDING to the run journal.
 *
 * The previous implementation did `fs.writeFileSync(targetFile, ...)` on the
 * run's meta file, so APPROVE / REVISE / KILL overwrote the record of what the
 * run had actually produced, with no prior version kept. History is not a
 * mutable field: the decision is a new event, and the run's own account of
 * itself stays exactly as it was written.
 */
export function appendDecision(
  runId: string,
  actor: string,
  action: string,
  note = '',
): { ok: boolean; error?: string } {
  const p = path.join(RUNS_DIR, runId, 'events.jsonl');
  if (!fs.existsSync(p)) return { ok: false, error: `no journal for ${runId}` };
  const line = JSON.stringify({
    ts: Date.now() / 1000,
    kind: 'decision',
    actor,
    action,
    note,
  });
  try {
    fs.appendFileSync(p, line + '\n', 'utf-8');
    return { ok: true };
  } catch (e) {
    return { ok: false, error: String(e) };
  }
}
