import { NextResponse } from 'next/server';
import { gtmLegacyRuns } from '@/lib/gtm';

export const dynamic = 'force-dynamic';

const MAX_RUNS = 1000;

/**
 * Runs — the GTM agents' cycles.
 *
 * This served the `core/` pipeline's journal until 2026-09-22. That is a
 * different system from the founder's agents, so the Runs Observatory was
 * showing one system's runs under the other's name. It now reads
 * `pipeline/state/gtm_runs`, which `autonomous_cycle.py` writes.
 */
export async function GET(req: Request) {
  // Every run, not the newest 50: the sidebar showed "50" as the history's
  // size while 95 runs were on disk. The cap only guards a runaway request.
  const limit = Number(new URL(req.url).searchParams.get('limit') ?? MAX_RUNS);
  const runs = await gtmLegacyRuns(Number.isFinite(limit) ? Math.min(limit, MAX_RUNS) : MAX_RUNS);
  return NextResponse.json({
    runs,
    total_runs: runs.length,
    source: 'GTM_RUN_JOURNAL',
    updated_at: new Date().toISOString(),
  });
}
