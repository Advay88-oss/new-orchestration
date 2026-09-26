import crypto from 'crypto';
import { spawn } from 'child_process';
import { NextResponse } from 'next/server';
import { localOnly } from '@/lib/local-only';
import { pythonPath, runPython, lastJson } from '@/lib/python';
import { REPO_ROOT } from '@/lib/v2';

export const dynamic = 'force-dynamic';

/**
 * Connect a tenant's Notion (the OAuth public integration). Local-only.
 *
 *   GET  connect?tenant=     redirect to Notion's consent screen
 *   GET  callback?code&state Notion sends the founder back here; the code is
 *                            exchanged and the token stored encrypted
 *                            (pipeline/brand_brain/notion_oauth.py)
 *   POST disconnect {tenant} delete the token and stop the sync
 *
 * The client secret never reaches this process: the exchange runs in Python,
 * which reads it from pipeline/.env. `state` is bound to an httpOnly cookie so
 * a callback cannot be forged from another page.
 */
const TENANT = /^[a-z0-9][a-z0-9_-]{1,40}$/;
const COOKIE = 'vn_notion_state';

function back(req: Request, q: string) {
  return NextResponse.redirect(new URL('/?view=brain&' + q, req.url));
}

function exchange(tenant: string, code: string): Promise<{ ok: boolean; out: string }> {
  const py = pythonPath();
  if (!py) return Promise.resolve({ ok: false, out: 'no python interpreter' });
  return new Promise((resolve) => {
    const child = spawn(py, ['-m', 'pipeline.brand_brain.notion_oauth', 'exchange', '--tenant', tenant], {
      cwd: REPO_ROOT, env: { ...process.env, PYTHONIOENCODING: 'utf-8' },
    });
    let out = '';
    child.stdout.on('data', (d) => (out += d));
    child.stderr.on('data', (d) => (out += d));
    child.on('close', (c) => resolve({ ok: c === 0, out }));
    child.stdin.end(code);                     // the code on stdin, never in argv
  });
}

export async function GET(req: Request, { params }: { params: { action: string } }) {
  const blocked = localOnly('connecting Notion');
  if (blocked) return blocked;
  const url = new URL(req.url);

  if (params.action === 'connect') {
    const tenant = url.searchParams.get('tenant') || '';
    if (!TENANT.test(tenant)) return NextResponse.json({ ok: false, error: 'bad tenant' }, { status: 400 });
    const state = tenant + '.' + crypto.randomBytes(16).toString('hex');
    const r = await runPython(['-m', 'pipeline.brand_brain.notion_oauth', 'authorize-url', '--tenant', tenant, '--state', state], 30_000);
    const got = lastJson(r.stdout) as { url?: string } | null;
    if (!r.ok || !got?.url) return back(req, 'notion=not_configured');
    const res = NextResponse.redirect(got.url);
    res.cookies.set(COOKIE, state, { httpOnly: true, sameSite: 'lax', path: '/', maxAge: 600 });
    return res;
  }

  if (params.action === 'callback') {
    const state = url.searchParams.get('state') || '';
    const code = url.searchParams.get('code') || '';
    const want = req.headers.get('cookie')?.split(';').map((c) => c.trim())
      .find((c) => c.startsWith(COOKIE + '='))?.slice(COOKIE.length + 1) || '';
    if (url.searchParams.get('error')) return back(req, 'notion=denied');
    if (!state || state !== want || !code) return back(req, 'notion=bad_state');
    const tenant = state.split('.')[0];
    if (!TENANT.test(tenant)) return back(req, 'notion=bad_state');
    const r = await exchange(tenant, code);
    const res = back(req, r.ok ? 'notion=connected' : 'notion=failed');
    res.cookies.delete(COOKIE);
    return res;
  }

  return NextResponse.json({ ok: false, error: 'unknown action' }, { status: 404 });
}

export async function POST(req: Request, { params }: { params: { action: string } }) {
  const blocked = localOnly('disconnecting Notion');
  if (blocked) return blocked;
  if (params.action !== 'disconnect') return NextResponse.json({ ok: false, error: 'unknown action' }, { status: 404 });
  const body = await req.json().catch(() => ({}));
  const tenant = String(body.tenant || '');
  if (!TENANT.test(tenant)) return NextResponse.json({ ok: false, error: 'bad tenant' }, { status: 400 });
  const r = await runPython(['-m', 'pipeline.brand_brain.notion_oauth', 'disconnect', '--tenant', tenant], 30_000);
  return NextResponse.json(lastJson(r.stdout) ?? { ok: false, error: r.stderr.slice(0, 300) || r.error });
}
