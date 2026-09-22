import { NextResponse } from 'next/server';
import { gtmLegacyRuns } from '@/lib/gtm';

export const dynamic = 'force-dynamic';

/**
 * Runs — the 13 GTM agents' cycles.
 *
 * This served the `core/` pipeline's journal until 2026-09-22. That is a
 * different system from the founder's agents, so the Runs Observatory was
 * showing one system's runs under the other's name. It now reads
 * `pipeline/state/gtm_runs`, which `autonomous_cycle.py` writes.
 */
export async function GET(req: Request) {
  const limit = Number(new URL(req.url).searchParams.get('limit') ?? 50);
  const runs = gtmLegacyRuns(Number.isFinite(limit) ? limit : 50);
  return NextResponse.json({
    runs,
    total_runs: runs.length,
    source: 'GTM_RUN_JOURNAL',
    updated_at: new Date().toISOString(),
  });
}
