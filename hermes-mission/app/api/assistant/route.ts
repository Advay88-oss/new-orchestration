import { NextResponse } from 'next/server';
import { companyAccess } from '@/lib/local-only';
import { clientTenant } from '@/lib/viewer';
import { ask } from '@/lib/assistant';

export const dynamic = 'force-dynamic';

/**
 * One assistant turn, streamed as server-sent events: the thread id, tool
 * activity, cards, the answer as it is written, and the grounding check.
 *
 * POST {tenant, text, thread_id?}
 *
 * The thread's history lives on the server (Cloud SQL / the tenant's brain),
 * so only the new message is sent. Closing the stream (Stop, or leaving the
 * page) cancels the turn. Owner-only.
 */
const TENANT = /^[a-z0-9][a-z0-9_-]{1,40}$/;
const THREAD = /^t_[A-Za-z0-9_-]{6,40}$/;

export async function POST(req: Request) {
  const body = await req.json().catch(() => ({}));
  // The owner talks about any company; a client only about their own.
  const access = companyAccess('the assistant', TENANT.test(String(body.tenant || '')) ? String(body.tenant) : null,
                               { write: true });
  if (access instanceof NextResponse) return access;
  const tenant = access.tenant || String(body.tenant || '');
  const client = Boolean(clientTenant());
  const text = String(body.text || '').slice(0, 8000);
  const thread_id = THREAD.test(String(body.thread_id || '')) ? String(body.thread_id) : null;
  if (!TENANT.test(tenant)) return Response.json({ ok: false, error: 'pick a company first' }, { status: 400 });
  if (!text.trim()) return Response.json({ ok: false, error: 'empty message' }, { status: 400 });

  const enc = new TextEncoder();
  let turn: ReturnType<typeof ask> | null = null;
  const stream = new ReadableStream({
    start(controller) {
      let open = true;
      const send = (ev: Record<string, unknown>) => {
        if (!open) return;
        try {
          const { id: _id, ...rest } = ev as any;
          controller.enqueue(enc.encode('data: ' + JSON.stringify(rest) + '\n\n'));
        } catch { open = false; }
      };
      turn = ask({ tenant, text, thread_id, base: new URL(req.url).origin, client }, send);
      req.signal.addEventListener('abort', () => turn?.cancel());
      turn.done.finally(() => { open = false; try { controller.close(); } catch { /* */ } });
    },
    cancel() { turn?.cancel(); },
  });
  return new Response(stream, {
    headers: { 'Content-Type': 'text/event-stream', 'Cache-Control': 'no-cache, no-transform', Connection: 'keep-alive' },
  });
}
