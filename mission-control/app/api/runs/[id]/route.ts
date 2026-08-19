import { NextResponse } from 'next/server';
import fs from 'fs';
import path from 'path';

// Full record of one run: its manifest + the complete event stream, so the run
// is fully replayable and traceable from start to finish.
const RUNS = path.resolve('D:/new orchestration/pipeline/state/runs');

export const dynamic = 'force-dynamic';

export async function GET(_req: Request, ctx: { params: Promise<{ id: string }> } | { params: { id: string } }) {
  try {
    // Next 15 passes params as a promise; support both shapes.
    const p: any = (ctx as any).params;
    const { id } = typeof p?.then === 'function' ? await p : p;
    // Guard against path traversal — only our timestamped run ids.
    if (!/^[a-z0-9._-]+$/i.test(id)) {
      return NextResponse.json({ error: 'bad id' }, { status: 400 });
    }
    const metaFile = path.join(RUNS, `${id}.meta.json`);
    const evFile = path.join(RUNS, `${id}.jsonl`);
    if (!fs.existsSync(metaFile)) return NextResponse.json({ error: 'not found' }, { status: 404 });
    const meta = JSON.parse(fs.readFileSync(metaFile, 'utf-8'));
    let events: any[] = [];
    if (fs.existsSync(evFile)) {
      events = fs
        .readFileSync(evFile, 'utf-8')
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
    }
    return NextResponse.json({ meta, events });
  } catch (e: any) {
    return NextResponse.json({ error: e.message }, { status: 500 });
  }
}
