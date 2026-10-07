import fs from 'fs';
import path from 'path';
import { NextResponse } from 'next/server';
import { localOnly } from '@/lib/local-only';
import { pythonPath, spawnHidden } from '@/lib/python';
import { REPO_ROOT } from '@/lib/v2';

export const dynamic = 'force-dynamic';

/**
 * The assistant's checks (pipeline/assistant/evals.py): real questions
 * through the real model and brain, judged on correctness, invented numbers,
 * planted instructions, actions without a button, Notion links, language,
 * memory, Stop and latency.
 *
 *   GET   the last report and whether a run is in progress
 *   POST  run the checks now (3-5 minutes, in the background)
 *
 * Owner-only.
 */
const REPORT = path.join(REPO_ROOT, 'pipeline', 'state', 'assistant_eval.json');
const STATUS = path.join(REPO_ROOT, 'pipeline', 'state', 'assistant_eval.status.json');

function read(f: string): any | null {
  try { return JSON.parse(fs.readFileSync(f, 'utf-8')); } catch { return null; }
}

export async function GET() {
  const blocked = localOnly('the assistant checks');
  if (blocked) return blocked;
  return NextResponse.json({ ok: true, report: read(REPORT), status: read(STATUS) });
}

export async function POST() {
  const blocked = localOnly('the assistant checks');
  if (blocked) return blocked;
  if (read(STATUS)?.state === 'running') return NextResponse.json({ ok: false, error: 'checks are already running' }, { status: 409 });
  const py = pythonPath();
  if (!py) return NextResponse.json({ ok: false, error: 'no python interpreter' }, { status: 500 });
  fs.mkdirSync(path.dirname(STATUS), { recursive: true });
  fs.writeFileSync(STATUS, JSON.stringify({ state: 'running', at: new Date().toISOString() }));
  const child = spawnHidden(['-m', 'pipeline.assistant.evals', '--status-file', STATUS], {
    cwd: REPO_ROOT, detached: true, stdio: 'ignore',
    env: { ...process.env, PYTHONIOENCODING: 'utf-8', PYTHONPATH: REPO_ROOT },
  });
  child.unref();
  return NextResponse.json({ ok: true, state: 'running' });
}
