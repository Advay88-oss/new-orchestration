import { NextResponse } from 'next/server';
import { isDeployed } from '@/lib/gcs';
import { allow, clientIp } from '@/lib/ratelimit';
import { OWNER_COOKIE, OWNER_SESSION_DAYS, PREVIEW_COOKIE, isOwner, isOwnerKey, signOwner } from '@/lib/viewer';

export const dynamic = 'force-dynamic';

/**
 * The owner signs in here, from the /login form: the key travels in a POST
 * body, never in a URL, and what the browser keeps is a signed session that
 * expires (lib/viewer.ts), not the key or a fixed hash of it.
 *
 *   GET   {owner}            is this browser signed in
 *   POST  {key}              sign in; 10 tries per 15 minutes per address
 */
export async function GET() {
  return NextResponse.json({ ok: true, owner: isOwner(), deployed: isDeployed() });
}

export async function POST(req: Request) {
  if (!allow('login:' + clientIp(req), 10, 15 * 60_000)) {
    return NextResponse.json({ ok: false, error: 'too many tries; wait 15 minutes' }, { status: 429 });
  }
  const body = await req.json().catch(() => ({}));
  const key = typeof body?.key === 'string' ? body.key.slice(0, 400) : '';
  if (!process.env.OWNER_KEY) {
    return NextResponse.json({ ok: false, error: 'OWNER_KEY is not set on this server' }, { status: 503 });
  }
  if (!isOwnerKey(key)) {
    return NextResponse.json({ ok: false, error: 'that key is not right' }, { status: 401 });
  }
  const res = NextResponse.json({ ok: true, owner: true });
  res.cookies.set(OWNER_COOKIE, signOwner(), {
    httpOnly: true, sameSite: 'lax', secure: isDeployed() || new URL(req.url).protocol === 'https:',
    path: '/', maxAge: OWNER_SESSION_DAYS * 86400,
  });
  res.cookies.delete(PREVIEW_COOKIE);
  return res;
}
