import crypto from 'crypto';
import { NextResponse } from 'next/server';
import { runPython, lastJson } from '@/lib/python';
import { allow, clientIp } from '@/lib/ratelimit';

export const dynamic = 'force-dynamic';

/**
 * A client connects their Notion through an invite (pipeline/brand_brain/
 * notion_oauth.py). Public on purpose: the signed invite is the authority,
 * not a login — it names one tenant, expires in 7 days and works once.
 *
 *   POST check          {invite}  who the invite is for, if it is still good
 *   GET  start?invite=            to Notion's consent screen
 *   GET  callback?code&state      Notion brings the client back; the code is
 *                                 exchanged and the token sealed for the tenant
 *
 * The invite and the code reach Python on stdin; the client secret never
 * leaves Python. `state` is bound to an httpOnly cookie, so a callback that
 * did not start here is refused.
 */
const STATE = 'vn_nstate';
const INVITE = 'vn_ninvite';
const COOKIE = { httpOnly: true, sameSite: 'lax' as const, path: '/', maxAge: 900 };

async function py(args: string[], input?: object) {
  const r = await runPython(['-m', 'pipeline.brand_brain.mcp_call', 'notion', ...args], 60_000,
                            input ? JSON.stringify(input) : undefined);
  return (lastJson(r.stdout) as any) ?? { ok: false, error: 'the connection service did not answer' };
}

function page(req: Request, q: Record<string, string>) {
  const u = new URL('/connect/notion', req.url);
  for (const [k, v] of Object.entries(q)) u.searchParams.set(k, v);
  return NextResponse.redirect(u);
}

function cookie(req: Request, name: string): string {
  return req.headers.get('cookie')?.split(';').map((c) => c.trim())
    .find((c) => c.startsWith(name + '='))?.slice(name.length + 1) || '';
}

export async function POST(req: Request, { params }: { params: { step: string } }) {
  if (params.step !== 'check') return NextResponse.json({ ok: false }, { status: 404 });
  // Public page: an invite cannot be guessed, but a loop could still cost us.
  if (!allow('notion-check:' + clientIp(req), 30, 600_000)) return NextResponse.json({ ok: false, error: 'too many tries; wait a few minutes' }, { status: 429 });
  const b = await req.json().catch(() => ({}));
  const r = await py(['check-invite'], { invite: String(b.invite || '').slice(0, 2000) });
  // Only what the page needs to show.
  return NextResponse.json(r.ok ? { ok: true, company: r.company, configured: r.configured }
                                : { ok: false, error: r.error });
}

export async function GET(req: Request, { params }: { params: { step: string } }) {
  const url = new URL(req.url);
  if (!allow('notion-flow:' + clientIp(req), 20, 600_000)) return page(req, { error: 'Too many tries; wait a few minutes.' });

  if (params.step === 'start') {
    const invite = String(url.searchParams.get('invite') || '').slice(0, 2000);
    const chk = await py(['check-invite'], { invite });
    if (!chk.ok) return page(req, { error: chk.error || 'invalid' });
    if (!chk.configured) return page(req, { error: 'Notion connections are not set up on this dashboard yet.' });
    const state = crypto.randomBytes(18).toString('hex');
    const auth = await py(['authorize-url', '--tenant', chk.tenant, '--state', state]);
    if (!auth.url) return page(req, { error: 'could not start the Notion connection' });
    const res = NextResponse.redirect(auth.url);
    res.cookies.set(STATE, state, COOKIE);
    res.cookies.set(INVITE, invite, COOKIE);
    return res;
  }

  if (params.step === 'callback') {
    if (url.searchParams.get('error')) return page(req, { error: 'Notion access was not granted.' });
    const state = url.searchParams.get('state') || '';
    const code = url.searchParams.get('code') || '';
    if (!state || state !== cookie(req, STATE) || !code) {
      return page(req, { error: 'This sign-in could not be verified. Open the invite link again.' });
    }
    const r = await py(['exchange-invite'], { invite: cookie(req, INVITE), code });
    const res = r.ok ? page(req, { done: '1', company: String(r.company || '') })
                     : page(req, { error: r.error || 'the connection failed' });
    res.cookies.delete(STATE);
    res.cookies.delete(INVITE);
    return res;
  }

  return NextResponse.json({ ok: false }, { status: 404 });
}
