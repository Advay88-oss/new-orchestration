import fs from 'fs';
import path from 'path';
import { spawn } from 'child_process';
import { NextResponse } from 'next/server';
import { companyAccess } from '@/lib/local-only';
import { pythonPath } from '@/lib/python';
import { REPO_ROOT } from '@/lib/v2';

export const dynamic = 'force-dynamic';

/**
 * Competitor analysis (the website analyzer's rivals step).
 *
 * POST {tenant, suggest?}  analyse every competitor in the profile: its website
 *                          and recent X posts, into pattern summaries; with
 *                          `suggest`, also web-search for new ones to confirm
 * GET  ?tenant=            the job's status, and the last report
 *
 * Only summaries reach the brain; competitors' text never does. Local-only.
 */
const TENANT = /^[a-z0-9][a-z0-9_-]{1,40}$/;
const statusFile = (t: string) => path.join(REPO_ROOT, 'pipeline', 'state', 'analyzer', t + '.competitors.json');
const reportFile = (t: string) => path.join(REPO_ROOT, 'pipeline', 'brain', 'tenants', t, 'competitors.json');

function readJson(f: string): any | null {
  try {
    return JSON.parse(fs.readFileSync(f, 'utf-8'));
  } catch {
    return null;
  }
}

export async function GET(req: Request) {
  const asked = new URL(req.url).searchParams.get('tenant') || '';
  if (!TENANT.test(asked)) return NextResponse.json({ ok: false, error: 'bad tenant' }, { status: 400 });
  const access = companyAccess('the competitor analysis', asked);
  if (access instanceof NextResponse) return access;
  const t = access.tenant || asked;
  const job = readJson(statusFile(t));
  const report = readJson(reportFile(t));
  return NextResponse.json({ ok: true, state: job?.state ?? 'none', job, report });
}

export async function POST(req: Request) {
  const body = await req.json().catch(() => ({}));
  const asked = String(body.tenant || '').toLowerCase();
  // A client works on their own company only (a new company is the owner's call).
  const access = companyAccess('analysing competitors', asked || null, { write: true });
  if (access instanceof NextResponse) return access;
  const tenant = access.tenant || asked;
  if (!TENANT.test(tenant)) return NextResponse.json({ ok: false, error: 'bad tenant' }, { status: 400 });
  const py = pythonPath();
  if (!py) return NextResponse.json({ ok: false, error: 'no python interpreter for the pipeline' }, { status: 500 });
  const f = statusFile(tenant);
  fs.mkdirSync(path.dirname(f), { recursive: true });
  if (readJson(f)?.state === 'running') {
    return NextResponse.json({ ok: false, error: 'a competitor analysis is already running' }, { status: 409 });
  }
  const args = ['-m', 'pipeline.brand_brain.mcp_call', 'competitors', '--tenant', tenant, '--status-file', f];
  if (body.suggest) args.push('--suggest');
  const child = spawn(py, args, {
    cwd: REPO_ROOT, detached: true, stdio: 'ignore',
    env: { ...process.env, PYTHONIOENCODING: 'utf-8', PYTHONPATH: REPO_ROOT },
  });
  child.unref();
  fs.writeFileSync(f, JSON.stringify({ state: 'running', mode: 'competitors', tenant, at: new Date().toISOString() }));
  return NextResponse.json({ ok: true, state: 'running', tenant });
}
