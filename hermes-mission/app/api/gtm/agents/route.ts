import { NextResponse } from 'next/server';
import { gtmAgents } from '@/lib/gtm';

export const dynamic = 'force-dynamic';

/**
 * Status of the 13 GTM agents (ARCHITECTURE.md Agent 01-13).
 *
 * Distinct from `/api/agents/status`, which reports the `core/` pipeline. Every
 * field is read from the run journal that `autonomous_cycle.py` writes; an
 * agent that has not run says so.
 */
export async function GET(req: Request) {
  const runId = new URL(req.url).searchParams.get('run') || undefined;
  const { runId: rid, agents, summary } = await gtmAgents(runId);

  return NextResponse.json({
    runId: rid,
    agents,
    declared: agents.length,
    modelBacked: agents.filter((a) => a.kind === 'MODEL_BACKED').length,
    ranThisRun: agents.filter((a) => a.status === 'ok' || a.status === 'degraded').length,
    failed: agents.filter((a) => a.status === 'failed').map((a) => a.id),
    modelsUsed: summary?.models_used ?? [],
    status: summary?.status ?? null,
  });
}
