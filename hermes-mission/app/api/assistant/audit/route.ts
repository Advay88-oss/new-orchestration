import { NextResponse } from 'next/server';
import { companyAccess } from '@/lib/local-only';
import { runPython } from '@/lib/python';

export const dynamic = 'force-dynamic';

/**
 * The audit log: what the assistant started and which buttons the owner
 * pressed in the chat.
 *
 *   GET  ?tenant=                                  the latest entries
 *   POST {tenant, action, run_id?, directive?, result?, thread_id?, asked?}
 *                                                  record an owner action
 * Owner-only.
 */
const TENANT = /^[a-z0-9][a-z0-9_-]{1,40}$/;

export async function GET(req: Request) {
  const asked = new URL(req.url).searchParams.get('tenant') || '';
  if (!TENANT.test(asked)) return NextResponse.json({ ok: false, error: 'bad tenant' }, { status: 400 });
  const access = companyAccess('the audit log', asked);
  if (access instanceof NextResponse) return access;
  const tenant = access.tenant || asked;
  const r = await runPython(['-m', 'pipeline.assistant.cli', 'audit', '--tenant', tenant], 30_000);
  try { return NextResponse.json(JSON.parse(r.stdout.trim().split('\n').pop() || '{}')); } catch {
    return NextResponse.json({ ok: false, error: r.stderr.slice(-300) }, { status: 500 });
  }
}

export async function POST(req: Request) {
  const b = await req.json().catch(() => ({}));
  const asked = String(b.tenant || '');
  if (!TENANT.test(asked)) return NextResponse.json({ ok: false, error: 'bad tenant' }, { status: 400 });
  const access = companyAccess('the audit log', asked, { write: true });
  if (access instanceof NextResponse) return access;
  const tenant = access.tenant || asked;
  const entry = { action: String(b.action || ''), run_id: b.run_id ?? null, directive: b.directive ?? null,
                  result: String(b.result || '').slice(0, 300), thread_id: b.thread_id ?? null,
                  asked: String(b.asked || '').slice(0, 300) };
  const r = await runPython(['-m', 'pipeline.assistant.cli', 'record', '--tenant', tenant], 30_000, JSON.stringify(entry));
  return NextResponse.json({ ok: r.ok });
}
