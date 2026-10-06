import { NextResponse } from 'next/server';
import { companyAccess } from '@/lib/local-only';
import { runPython, lastJson } from '@/lib/python';

export const dynamic = 'force-dynamic';

/**
 * The owner's side of Notion connections (the client's side is
 * /api/connect/notion, reached through an invite).
 *
 *   POST invite     {tenant}  a signed, single-use link for that tenant's
 *                             Notion: send it to the client, or open it
 *                             yourself to connect your own workspace
 *   POST disconnect {tenant}  delete the token and stop the sync
 *
 * Owner-only (lib/local-only.ts).
 */
const TENANT = /^[a-z0-9][a-z0-9_-]{1,40}$/;

export async function POST(req: Request, { params }: { params: { action: string } }) {
  const body = await req.json().catch(() => ({}));
  const asked = String(body.tenant || '');
  if (!TENANT.test(asked)) return NextResponse.json({ ok: false, error: 'bad tenant' }, { status: 400 });
  // A client connects (or disconnects) their own company's Notion.
  const access = companyAccess('managing Notion connections', asked, { write: true });
  if (access instanceof NextResponse) return access;
  const tenant = access.tenant || asked;
  let args: string[];
  if (params.action === 'invite') {
    args = ['invite', '--tenant', tenant, '--base', new URL(req.url).origin];
  } else if (params.action === 'disconnect') {
    args = ['disconnect', '--tenant', tenant];
  } else {
    return NextResponse.json({ ok: false, error: 'unknown action' }, { status: 404 });
  }
  const r = await runPython(['-m', 'pipeline.brand_brain.mcp_call', 'notion', ...args], 30_000);
  return NextResponse.json(lastJson(r.stdout) ?? { ok: false, error: r.stderr.slice(-300) || r.error });
}
