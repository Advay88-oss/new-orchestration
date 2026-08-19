import { NextResponse } from 'next/server';
import fs from 'fs';
import path from 'path';

// The orchestrator appends one JSON line per debate step to this file as the run
// happens; we stream it so the dashboard can render the real debate live.
const FEED = path.resolve('D:/new orchestration/pipeline/state/live_run.jsonl');

export const dynamic = 'force-dynamic';

export async function GET() {
  try {
    if (!fs.existsSync(FEED)) {
      return NextResponse.json({ events: [], mtime: 0 });
    }
    const stat = fs.statSync(FEED);
    const raw = fs.readFileSync(FEED, 'utf-8');
    const events = raw
      .split('\n')
      .filter((l) => l.trim().length > 0)
      .map((l) => {
        try {
          return JSON.parse(l);
        } catch {
          return null;
        }
      })
      .filter(Boolean);
    return NextResponse.json({ events, mtime: stat.mtimeMs });
  } catch (e: any) {
    return NextResponse.json({ events: [], error: e.message }, { status: 500 });
  }
}
