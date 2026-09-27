import { NextResponse } from 'next/server';
import { localOnly } from '@/lib/local-only';
import { runPython } from '@/lib/python';

export const dynamic = 'force-dynamic';

/**
 * Today's spend against the caps, recent alerts and errors (pipeline/ops).
 *   GET               the status
 *   POST {test: true} send a test alert to the owner's Telegram
 * Owner-only.
 */
async function py(args: string[]) {
  const r = await runPython(['-m', 'pipeline.ops.cli', ...args], 30_000);
  try { return NextResponse.json(JSON.parse(r.stdout.trim().split('\n').pop() || '{}')); } catch {
    return NextResponse.json({ ok: false, error: r.stderr.slice(-300) || r.error }, { status: 500 });
  }
}

export async function GET() {
  const blocked = localOnly('the ops status');
  if (blocked) return blocked;
  return py(['status']);
}

export async function POST(req: Request) {
  const blocked = localOnly('the ops status');
  if (blocked) return blocked;
  const b = await req.json().catch(() => ({}));
  if (b.test) return py(['test-alert']);
  return NextResponse.json({ ok: false, error: 'nothing to do' }, { status: 400 });
}
