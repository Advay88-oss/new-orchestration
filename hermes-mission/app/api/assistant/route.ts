import { localOnly } from '@/lib/local-only';
import { ask } from '@/lib/assistant';

export const dynamic = 'force-dynamic';

/**
 * One assistant turn, streamed as server-sent events: tool activity, cards
 * (an analysis, a Notion button, an action to confirm, a run) and the answer.
 *
 * POST {tenant, messages: [{role: 'user'|'assistant', text}]}
 *
 * Owner-only (lib/local-only.ts): the assistant can start the analyzer and
 * make Notion links, and it reads everything in the brain.
 */
const TENANT = /^[a-z0-9][a-z0-9_-]{1,40}$/;

export async function POST(req: Request) {
  const blocked = localOnly('the assistant');
  if (blocked) return blocked;
  const body = await req.json().catch(() => ({}));
  const tenant = String(body.tenant || '');
  const messages = Array.isArray(body.messages) ? body.messages.slice(-30) : [];
  if (!TENANT.test(tenant)) return Response.json({ ok: false, error: 'pick a company first' }, { status: 400 });

  // Tools that build links (Notion invites) need to know where the dashboard lives.
  const base = new URL(req.url).origin;

  const enc = new TextEncoder();
  const stream = new ReadableStream({
    start(controller) {
      const send = (ev: Record<string, unknown>) => {
        try {
          controller.enqueue(enc.encode('data: ' + JSON.stringify(ev) + '\n\n'));
        } catch {
          /* the browser went away */
        }
      };
      ask(tenant, messages, (ev) => {
        const { id: _id, ...rest } = ev as any;
        send(rest);
      }, base).finally(() => {
        try { controller.close(); } catch { /* already closed */ }
      });
    },
  });
  return new Response(stream, {
    headers: { 'Content-Type': 'text/event-stream', 'Cache-Control': 'no-cache, no-transform', Connection: 'keep-alive' },
  });
}
