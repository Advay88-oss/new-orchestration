import { NextResponse } from 'next/server';
import { localOnly } from '@/lib/local-only';
import { runPython, lastJson } from '@/lib/python';

export const dynamic = 'force-dynamic';

/**
 * The assistant's conversations, stored per company on the server.
 *
 *   GET    ?tenant=              the thread list, newest first
 *   GET    ?tenant=&id=t_...     one thread with its messages
 *   DELETE ?tenant=&id=t_...     delete a thread
 *
 * Owner-only.
 */
const TENANT = /^[a-z0-9][a-z0-9_-]{1,40}$/;
const THREAD = /^t_[A-Za-z0-9_-]{6,40}$/;

async function py(args: string[]) {
  const r = await runPython(['-m', 'pipeline.assistant.cli', ...args], 30_000);
  // The thread JSON nests objects, so parse the whole last line.
  const line = r.stdout.trim().split('\n').filter(Boolean).pop() || '';
  try { return NextResponse.json(JSON.parse(line)); } catch {
    return NextResponse.json(lastJson(r.stdout) ?? { ok: false, error: r.stderr.slice(-300) || r.error }, { status: 500 });
  }
}

export async function GET(req: Request) {
  const blocked = localOnly('the assistant');
  if (blocked) return blocked;
  const u = new URL(req.url);
  const tenant = u.searchParams.get('tenant') || '';
  const id = u.searchParams.get('id') || '';
  if (!TENANT.test(tenant)) return NextResponse.json({ ok: false, error: 'bad tenant' }, { status: 400 });
  if (id) {
    if (!THREAD.test(id)) return NextResponse.json({ ok: false, error: 'bad thread' }, { status: 400 });
    return py(['thread', '--tenant', tenant, '--id', id]);
  }
  return py(['threads', '--tenant', tenant]);
}

export async function DELETE(req: Request) {
  const blocked = localOnly('the assistant');
  if (blocked) return blocked;
  const u = new URL(req.url);
  const tenant = u.searchParams.get('tenant') || '';
  const id = u.searchParams.get('id') || '';
  if (!TENANT.test(tenant) || !THREAD.test(id)) return NextResponse.json({ ok: false, error: 'bad request' }, { status: 400 });
  return py(['delete', '--tenant', tenant, '--id', id]);
}
