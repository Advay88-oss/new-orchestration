import fs from 'fs';
import path from 'path';
import { spawn } from 'child_process';
import { NextResponse } from 'next/server';
import { companyAccess } from '@/lib/local-only';
import { pythonPath } from '@/lib/python';
import { REPO_ROOT } from '@/lib/v2';

export const dynamic = 'force-dynamic';

/**
 * Onboarding: draft a brand profile from a website (the website analyzer).
 *
 * POST {url, tenant}  starts the analyzer in the background (1-3 minutes)
 * GET  ?tenant=       its status: running | done | failed, with a summary
 *
 * A tenant that already has a profile gets a report, not a new version —
 * the analyzer never replaces a profile the founder built. Local-only.
 */
const TENANT = /^[a-z0-9][a-z0-9_-]{1,40}$/;
const statusFile = (t: string) => path.join(REPO_ROOT, 'pipeline', 'state', 'analyzer', t + '.json');

export async function GET(req: Request) {
  const asked = new URL(req.url).searchParams.get('tenant') || '';
  if (!TENANT.test(asked)) return NextResponse.json({ ok: false, error: 'bad tenant' }, { status: 400 });
  const access = companyAccess('the website analysis', asked);
  if (access instanceof NextResponse) return access;
  const t = access.tenant || asked;
  const f = statusFile(t);
  if (!fs.existsSync(f)) return NextResponse.json({ ok: true, state: 'none' });
  try {
    return NextResponse.json({ ok: true, ...JSON.parse(fs.readFileSync(f, 'utf-8')) });
  } catch {
    return NextResponse.json({ ok: true, state: 'running' });
  }
}

export async function POST(req: Request) {
  const body = await req.json().catch(() => ({}));
  const asked = String(body.tenant || '').toLowerCase();
  // A client works on their own company only (a new company is the owner's call).
  const access = companyAccess('onboarding a website', asked || null, { write: true });
  if (access instanceof NextResponse) return access;
  const tenant = access.tenant || asked;
  let url = String(body.url || '').trim();
  if (!/^https?:\/\//i.test(url)) url = 'https://' + url;
  let host = '';
  try { host = new URL(url).hostname; } catch { /* invalid */ }
  if (!TENANT.test(tenant) || !host || !host.includes('.')) {
    return NextResponse.json({ ok: false, error: 'a website URL and a tenant id (a-z, 0-9, - or _) are needed' }, { status: 400 });
  }
  const py = pythonPath();
  if (!py) return NextResponse.json({ ok: false, error: 'no python interpreter for the pipeline' }, { status: 500 });
  const f = statusFile(tenant);
  fs.mkdirSync(path.dirname(f), { recursive: true });
  if (fs.existsSync(f) && JSON.parse(fs.readFileSync(f, 'utf-8')).state === 'running') {
    return NextResponse.json({ ok: false, error: 'an analysis for this tenant is already running' }, { status: 409 });
  }
  const child = spawn(py, ['-m', 'pipeline.brand_brain.analyzer', url, '--tenant', tenant, '--status-file', f], {
    cwd: REPO_ROOT, detached: true, stdio: 'ignore',
    env: { ...process.env, PYTHONIOENCODING: 'utf-8', PYTHONPATH: REPO_ROOT },
  });
  child.unref();
  fs.writeFileSync(f, JSON.stringify({ state: 'running', url, tenant, at: new Date().toISOString() }));
  return NextResponse.json({ ok: true, state: 'running', tenant, url });
}
