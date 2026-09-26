import { NextResponse } from 'next/server';
import { execFile } from 'child_process';
import fs from 'fs';
import os from 'os';
import path from 'path';
import { gtmFeedback } from '@/lib/gtm';
import { localOnly } from '@/lib/local-only';
import { pythonPath } from '@/lib/python';

export const dynamic = 'force-dynamic';

const REPO_ROOT = path.resolve(process.cwd(), '..');
const VERDICTS = new Set(['approve', 'edit', 'revise', 'kill']);

/**
 * The founder's decision on a run — the reward the learning loop records.
 *
 * GET  ?runId=   the run's feedback.json (works deployed, via GCS)
 * POST {runId, verdict, note}  records a decision through
 *      `pipeline.gtm_learning.feedback`, the same writer the Telegram
 *      listener uses, so both surfaces produce one ledger. Recording never
 *      publishes: approve means "this was good", not "send it".
 */
export async function GET(req: Request) {
  const runId = new URL(req.url).searchParams.get('runId');
  if (!runId) {
    return NextResponse.json({ success: false, error: 'runId required' }, { status: 400 });
  }
  return NextResponse.json({ success: true, feedback: await gtmFeedback(runId) });
}

export async function POST(req: Request) {
  const blocked = localOnly('recording feedback');
  if (blocked) return blocked;

  const body = await req.json().catch(() => ({}));
  const runId = String(body.runId ?? '');
  const verdict = String(body.verdict ?? '').toLowerCase();
  const note = String(body.note ?? '').slice(0, 2000);
  if (!/^GTM-\d{8}-\d{6}$/.test(runId) || !VERDICTS.has(verdict)) {
    return NextResponse.json(
      { success: false, error: 'runId (GTM-YYYYMMDD-HHMMSS) and verdict approve|edit|revise|kill required' },
      { status: 400 },
    );
  }
  const py = pythonPath();
  if (!py) {
    return NextResponse.json(
      { success: false, error: 'no python interpreter found for the pipeline' },
      { status: 500 },
    );
  }

  // execFile, not a shell: the note is the founder's free text and is passed
  // as one argument, never interpolated into a command line.
  const args = ['-m', 'pipeline.gtm_learning.feedback', 'record', runId, verdict,
                '--note', note, '--source', 'dashboard'];
  // An edited approval carries the founder's version: written to a temp file
  // and passed by path, never on the command line.
  let editDir: string | null = null;
  if (verdict === 'edit') {
    const edited = String(body.edited ?? '').slice(0, 8000);
    if (!edited.trim()) {
      return NextResponse.json({ success: false, error: 'an edit needs the edited text' }, { status: 400 });
    }
    editDir = fs.mkdtempSync(path.join(os.tmpdir(), 'edit-'));
    fs.writeFileSync(path.join(editDir, 'edited.txt'), edited, 'utf-8');
    args.push('--edited-file', path.join(editDir, 'edited.txt'));
  }
  const result = await new Promise<{ code: number; out: string; err: string }>((resolve) => {
    execFile(py, args, {
      cwd: REPO_ROOT,
      env: { ...process.env, PYTHONPATH: REPO_ROOT, PYTHONIOENCODING: 'utf-8' },
      timeout: 60_000,
    }, (error, stdout, stderr) => {
      resolve({ code: error ? (typeof (error as any).code === 'number' ? (error as any).code : 1) : 0,
                out: String(stdout), err: String(stderr) });
    });
  });

  if (editDir) fs.rmSync(editDir, { recursive: true, force: true });
  const line = result.out.trim().split('\n').filter(Boolean).pop() ?? '';
  try {
    const parsed = JSON.parse(line);
    return NextResponse.json(parsed, { status: parsed.success ? 200 : 400 });
  } catch {
    return NextResponse.json(
      { success: false, error: (result.err || result.out || 'feedback recorder failed').slice(-400) },
      { status: 500 },
    );
  }
}
