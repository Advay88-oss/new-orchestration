import { NextResponse } from 'next/server';
import { gtmHarvest } from '@/lib/gtm';

export const dynamic = 'force-dynamic';

/**
 * Everything A01 scraped on a run: each signal with its source, the companies
 * named in it, and when it was pulled.
 *
 * Distinct from `/api/research`, which reports a different subsystem (the
 * research_runs / discovered_players registry). This one is the live scout's
 * own harvest, which had no endpoint at all — the run summary kept a headline
 * and a date per candidate and dropped the rest.
 */
export async function GET(req: Request) {
  const runId = new URL(req.url).searchParams.get('runId') || undefined;
  const harvest = await gtmHarvest(runId);
  if (!harvest) {
    return NextResponse.json(
      { success: false, error: 'no harvest recorded yet — run a cycle' },
      { status: 404 },
    );
  }
  return NextResponse.json({ success: true, ...harvest });
}
