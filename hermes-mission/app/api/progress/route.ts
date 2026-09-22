import { NextResponse } from 'next/server';
import { listRunIds, runView, manifest } from '@/lib/v2';

export const dynamic = 'force-dynamic';

/**
 * Live progress, derived from the newest run's journal.
 *
 * The previous source (`pipeline/state/execution_progress.json`) was written by
 * the retired orchestrator *before* each stage did its work, with hardcoded
 * prose for `detail` — a declaration of intent, not a record of outcome. It also
 * went stale silently: it still reported "Agent 13: Learning Engine" long after
 * that run ended.
 */
export async function GET() {
  const total = manifest().length || 13;
  const id = listRunIds(1)[0];
  const run = id ? runView(id) : null;

  if (!run) {
    return NextResponse.json({
      step: 0, total, run_id: null, state: 'idle',
      agent_name: '—', detail: 'No run recorded yet.', timestamp: Date.now() / 1000,
    });
  }

  const done = run.stages.filter((s) => s.state !== 'not_reached' && s.state !== 'running').length;
  const running = run.stages.find((s) => s.state === 'running');
  const current = running ?? [...run.stages].reverse().find((s) => s.state !== 'not_reached');

  return NextResponse.json({
    step: running ? done + 1 : done,
    total,
    run_id: run.runId,
    state: run.status === 'running' ? 'running' : run.status,
    agent_name: current ? `${current.stage} (${current.kind})` : '—',
    // Outcome, not intent: what this stage did, or why it degraded.
    detail: running
      ? `${running.purpose}…`
      : current?.degradedReason ?? current?.error ?? current?.purpose ?? '',
    model: current?.model ?? null,
    degraded: run.degraded,
    failed: run.failed,
    timestamp: run.endedAt ?? run.startedAt ?? Date.now() / 1000,
  });
}
