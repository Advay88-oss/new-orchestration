import { spawn } from 'child_process';
import { NextResponse } from 'next/server';
import { companyAccess } from '@/lib/local-only';
import { lastJson, pythonPath, runPython } from '@/lib/python';
import { REPO_ROOT } from '@/lib/v2';

export const dynamic = 'force-dynamic';

const TENANT = /^[a-z0-9][a-z0-9_-]{1,40}$/;

/** The latest Campaigns scrape for this company. */
export async function GET(req: Request) {
  const asked = (new URL(req.url).searchParams.get('tenant') || '').toLowerCase();
  if (asked && !TENANT.test(asked)) return NextResponse.json({ ok: false, error: 'bad tenant' }, { status: 400 });
  const access = companyAccess('campaign research', asked || null);
  if (access instanceof NextResponse) return access;
  const tenant = access.tenant || asked || 'vanna';
  const r = await runPython(['-m', 'pipeline.gtm_os.campaigns', 'list', tenant], 60_000);
  return NextResponse.json(lastJson(r.stdout) ?? { ok: false, error: r.stderr.slice(-300) || r.error || 'unavailable' });
}

/** Start a scrape. Query is what kind of campaign. Source is where, Galxe today. */
export async function POST(req: Request) {
  const body = await req.json().catch(() => ({}));
  const asked = String(body.tenant || '').toLowerCase();
  const access = companyAccess('campaign research', asked || null, { write: true });
  if (access instanceof NextResponse) return access;
  const tenant = access.tenant || asked || 'vanna';
  if (!TENANT.test(tenant)) return NextResponse.json({ ok: false, error: 'bad tenant' }, { status: 400 });
  const query = String(body.query || '').trim().slice(0, 400);
  const source = String(body.source || 'galxe').trim().slice(0, 300) || 'galxe';
  if (!query) return NextResponse.json({ ok: false, error: 'write what kind of campaign you want' }, { status: 400 });
  const py = pythonPath();
  if (!py) return NextResponse.json({ ok: false, error: 'no python interpreter for the pipeline' }, { status: 500 });
  const child = spawn(py, ['-m', 'pipeline.gtm_os.campaigns', 'run', tenant, query, source], {
    cwd: REPO_ROOT, detached: true, stdio: 'ignore',
    env: { ...process.env, PYTHONIOENCODING: 'utf-8', PYTHONPATH: REPO_ROOT },
  });
  child.unref();
  return NextResponse.json({ ok: true, state: 'running' });
}
