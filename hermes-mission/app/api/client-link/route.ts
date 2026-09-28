import { NextResponse } from 'next/server';
import { ownerOnly } from '@/lib/local-only';
import { signClient } from '@/lib/viewer';

export const dynamic = 'force-dynamic';

/**
 * A client link for one company: POST {tenant, days?} -> {url}. Owner only.
 *
 * Opening it makes that browser the company's client (lib/viewer.ts): its
 * runs, Assistant, Brand Brain, Notion, launches and decisions — nothing of
 * any other company. The link is signed and expires (30 days by default);
 * changing CLIENT_LINK_SECRET revokes every link at once.
 */
const TENANT = /^[a-z0-9][a-z0-9_-]{1,40}$/;

export async function POST(req: Request) {
  const blocked = ownerOnly('making client links');
  if (blocked) return blocked;
  const b = await req.json().catch(() => ({}));
  const tenant = String(b.tenant || '').toLowerCase();
  if (!TENANT.test(tenant)) return NextResponse.json({ ok: false, error: 'bad tenant' }, { status: 400 });
  const days = Math.max(1, Math.min(90, Number(b.days) || 30));
  try {
    const token = signClient(tenant, days);
    const url = new URL(req.url).origin + '/?client=' + encodeURIComponent(token);
    return NextResponse.json({ ok: true, tenant, days, url });
  } catch (e: any) {
    return NextResponse.json({ ok: false, error: String(e?.message || e) }, { status: 500 });
  }
}
