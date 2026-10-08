import { NextResponse } from 'next/server';
import { companyAccess } from '@/lib/local-only';
import { runPython, lastJson } from '@/lib/python';
import { seesAll, seesSince, viewerKey, viewerSince } from '@/lib/viewer';

/** A visitor's Recents start empty: only chats started after their first visit. */
function scopeThreads(body: any): any {
  if (!viewerSince() || !body || !Array.isArray(body.threads)) return body;
  return { ...body, threads: body.threads.filter((t: any) => seesSince(t?.created_at)) };
}

export const dynamic = 'force-dynamic';

/**
 * The assistant's conversations, stored per company on the server.
 *
 *   GET    ?tenant=              the thread list, newest first
 *   GET    ?tenant=&id=t_...     one thread with its messages
 *   DELETE ?tenant=&id=t_...     delete a thread
 *
 * The owner and a company's client can read and delete. A visitor on the
 * public link can read this company's chats and cannot delete them.
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

function scoped(u: URL, opts: { publicRead?: boolean } = {}) {
  const asked = u.searchParams.get('tenant') || '';
  const access = companyAccess('the assistant', TENANT.test(asked) ? asked : null, opts);
  if (access instanceof NextResponse) return access;
  return access.tenant || asked;
}

// The list comes from a Python process that opens the brain: several seconds.
// Answer from the last copy at once and refresh it behind the answer, so the
// sidebar's Recents is there the moment the page opens.
const LISTS = new Map<string, { at: number; body: any }>();
const REFRESHING = new Set<string>();

// The owner's list is cached per company; anyone else's per company and viewer.
function listKey(tenant: string, by: string) { return by ? tenant + '|' + by : tenant; }

async function freshList(tenant: string, by = ''): Promise<any> {
  // A cold start against Cloud SQL can take longer than the old 30s limit,
  // and that timeout is what left Recents empty even though the chats were saved.
  const args = ['-m', 'pipeline.assistant.cli', 'threads', '--tenant', tenant, ...(by ? ['--by', by] : [])];
  const r = await runPython(args, 90_000);
  const line = r.stdout.trim().split('\n').filter(Boolean).pop() || '';
  const body = JSON.parse(line);
  if (body && body.ok && Array.isArray(body.threads)) LISTS.set(listKey(tenant, by), { at: Date.now(), body });
  return body;
}

export async function GET(req: Request) {
  const u = new URL(req.url);
  const s = scoped(u, { publicRead: true });
  if (s instanceof NextResponse) return s;
  const tenant = s;
  const id = u.searchParams.get('id') || '';
  if (!TENANT.test(tenant)) return NextResponse.json({ ok: false, error: 'bad tenant' }, { status: 400 });
  const by = seesAll() ? '' : viewerKey();
  if (id) {
    if (!THREAD.test(id)) return NextResponse.json({ ok: false, error: 'bad thread' }, { status: 400 });
    if (by) {
      // Only a chat this viewer started; for a visitor, also only since their first visit.
      const r = await runPython(['-m', 'pipeline.assistant.cli', 'thread', '--tenant', tenant, '--id', id, '--by', by], 30_000);
      const line = r.stdout.trim().split('\n').filter(Boolean).pop() || '';
      let body: any = null;
      try { body = JSON.parse(line); } catch { body = null; }
      const t = body?.thread || body;
      if (!body || !body.ok || !t || (viewerSince() && !seesSince(t?.created_at))) {
        return NextResponse.json({ ok: false, error: 'chat not found' }, { status: 404 });
      }
      return NextResponse.json(body);
    }
    return py(['thread', '--tenant', tenant, '--id', id]);
  }
  const cached = LISTS.get(listKey(tenant, by));
  // An empty copy is never reused. The first read often landed before any
  // chat existed, and every later open of Recents was handed that empty list.
  if (cached && cached.body?.threads?.length && u.searchParams.get('fresh') !== '1') {
    const k = listKey(tenant, by);
    if (Date.now() - cached.at > 3000 && !REFRESHING.has(k)) {
      REFRESHING.add(k);
      freshList(tenant, by).catch(() => {}).finally(() => REFRESHING.delete(k));
    }
    return NextResponse.json(scopeThreads({ ...cached.body, cached_at: new Date(cached.at).toISOString() }));
  }
  try {
    return NextResponse.json(scopeThreads(await freshList(tenant, by)));
  } catch (e: any) {
    return NextResponse.json({ ok: false, error: String(e?.message || e).slice(0, 300) }, { status: 500 });
  }
}

export async function DELETE(req: Request) {
  const u = new URL(req.url);
  const s = scoped(u);
  if (s instanceof NextResponse) return s;
  const tenant = s;
  const id = u.searchParams.get('id') || '';
  if (!TENANT.test(tenant) || !THREAD.test(id)) return NextResponse.json({ ok: false, error: 'bad request' }, { status: 400 });
  return py(['delete', '--tenant', tenant, '--id', id]);
}
