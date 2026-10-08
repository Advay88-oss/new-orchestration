import { NextResponse } from 'next/server';
import fs from 'fs';
import path from 'path';
import { gtmHarvest } from '@/lib/gtm';
import { isDeployed, getText } from '@/lib/gcs';
import { seesSince, viewerSince } from '@/lib/viewer';

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
function collectedAt(raw: string | null): number {
  if (!raw) return 0;
  try {
    const n = Date.parse(String(JSON.parse(raw).collected_at || ''));
    return Number.isFinite(n) ? n : 0;
  } catch {
    return 0;
  }
}

export async function GET(req: Request) {
  const runId = new URL(req.url).searchParams.get('runId') || undefined;
  let collected: unknown = null;
  try {
    const name = 'state/pipeline/state/research_latest.json';
    // On the laptop the scrape writes the file here. Asking gcloud for the
    // same object shells out to gcloud.cmd and opens a console on each refresh.
    const remote = isDeployed() ? await getText(name) : null;
    let disk: string | null = null;
    if (!isDeployed()) {
      try {
        disk = fs.readFileSync(path.join(process.cwd(), '..', 'pipeline', 'state', 'research_latest.json'), 'utf-8');
      } catch { disk = null; }
    }
    const raw = !disk ? remote : !remote ? disk : (collectedAt(remote) >= collectedAt(disk) ? remote : disk);
    collected = raw ? JSON.parse(raw) : null;
  } catch { collected = null; }
  if (collected && viewerSince()) {
    const c = collected as any;
    const items = (Array.isArray(c.items) ? c.items : []).filter((i: any) => seesSince(i?.at || c.collected_at));
    collected = items.length ? { ...c, items } : null;
  }
  const harvest = await gtmHarvest(runId);
  if (!harvest) {
    if (!collected) {
      return NextResponse.json(
        { success: false, error: 'no harvest recorded yet — run a cycle' },
        { status: 404 },
      );
    }
    return NextResponse.json({ success: true, signals: [], sources: {}, totalSignals: 0, collected });
  }
  return NextResponse.json({ success: true, ...harvest, collected });
}
