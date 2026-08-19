import { NextResponse } from 'next/server';
import fs from 'fs';
import path from 'path';

// Persistent audit trail: one meta.json per pipeline run. This lists them all,
// newest first, so no execution disappears after it finishes.
const RUNS = path.resolve('D:/new orchestration/pipeline/state/runs');

export const dynamic = 'force-dynamic';

export async function GET() {
  try {
    if (!fs.existsSync(RUNS)) return NextResponse.json({ runs: [] });
    const runs = fs
      .readdirSync(RUNS)
      .filter((f) => f.endsWith('.meta.json'))
      .map((f) => {
        try {
          const meta = JSON.parse(fs.readFileSync(path.join(RUNS, f), 'utf-8'));
          // Derive a short title: the winning hook if present, else the trend.
          const title = meta.winner_hook || (meta.trend ? `trend: ${meta.trend}` : meta.pipeline);
          return { ...meta, title };
        } catch {
          return null;
        }
      })
      .filter(Boolean)
      .sort((a: any, b: any) => (b.started ?? 0) - (a.started ?? 0));
    return NextResponse.json({ runs });
  } catch (e: any) {
    return NextResponse.json({ runs: [], error: e.message }, { status: 500 });
  }
}
