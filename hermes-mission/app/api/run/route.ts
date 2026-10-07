import { NextResponse } from 'next/server';
import fs from 'fs';
import path from 'path';
import { pythonPath, spawnHidden } from '@/lib/python';
import { listGtmRunIds, gtmRunSummary } from '@/lib/gtm';
import { cloudMode, companyAccess } from '@/lib/local-only';
import { clientTenant } from '@/lib/viewer';
import { runPipelineJob } from '@/lib/cloudrun';
import { allow } from '@/lib/ratelimit';

export const dynamic = 'force-dynamic';

const REPO_ROOT = path.resolve(process.cwd(), '..');
const LOG_DIR = path.join(REPO_ROOT, 'pipeline', 'state', 'gtm_runs');

/**
 * Trigger one GTM cycle — all 13 agents.
 *
 * This used to enqueue a job for `core.worker`, a different pipeline from the
 * founder's agents, so pressing Launch Run in a dashboard headed "13 GTM
 * Agents" ran something else entirely.
 *
 * The cycle takes 2-4 minutes (Veo dominates), far longer than an HTTP request
 * should hold, so it is spawned detached and the client polls /api/runs. An
 * empty directive is the autonomous path: A02 picks the topic itself.
 */
const CLIENT_RUNS_PER_DAY = Number(process.env.CLIENT_RUNS_PER_DAY || 10);

export async function POST(req: Request) {
  let directive = '';
  let withVideo = true;
  let asked: string | null = null;
  try {
    const body = await req.json();
    directive = body?.directive ?? '';
    withVideo = body?.video !== false;
    asked = typeof body?.tenant === 'string' && body.tenant ? String(body.tenant) : null;
  } catch {
    /* empty body = fully autonomous */
  }

  // The owner runs any company (default: the dashboard's tenant); a client
  // only their own, and at most CLIENT_RUNS_PER_DAY a day, video included.
  const access = companyAccess('starting a run', asked, { write: true });
  if (access instanceof NextResponse) return access;
  const tenant = access.tenant || process.env.BRAIN_TENANT || 'vanna';
  if (clientTenant() && !allow('client-launch:' + tenant, CLIENT_RUNS_PER_DAY, 86_400_000)) {
    return NextResponse.json({ success: false,
      error: `the limit for ${tenant} is ${CLIENT_RUNS_PER_DAY} runs a day` }, { status: 429 });
  }
  // A cycle costs model calls and a Veo render: at most 6 launches an hour
  // (the pipeline also caps cycles per day, and the daily budget holds).
  if (!allow('launch', 6, 3_600_000)) {
    return NextResponse.json({ success: false, error: 'too many launches: the limit is 6 an hour' }, { status: 429 });
  }

  // On GCP the cycle is a Cloud Run Job execution, not a child process.
  if (cloudMode()) {
    const args = ['cycle'];
    if (directive.trim()) args.push('--directive', directive.trim().slice(0, 2000));
    if (!withVideo) args.push('--no-video');
    const r = await runPipelineJob(args, { BRAIN_TENANT: tenant });
    if (!r.ok) return NextResponse.json({ success: false, error: r.error }, { status: 502 });
    return NextResponse.json({
      success: true, execution: r.execution, tenant, directive: directive || null, autonomous: !directive.trim(),
      note: 'Cycle started on GCP. It appears under Posts as it runs.',
    });
  }

  const py = pythonPath();
  if (!py) {
    return NextResponse.json(
      { success: false, error: 'no python interpreter found for the pipeline' },
      { status: 503 },
    );
  }

  const args = ['-m', 'pipeline.gtm_os.autonomous_cycle'];
  if (directive.trim()) args.push('--directive', directive.trim());
  if (!withVideo) args.push('--no-video');

  fs.mkdirSync(LOG_DIR, { recursive: true });
  // One log per launch, written as it happens: a run that dies still says
  // how far it got. last_launch.log keeps pointing at the newest one's name.
  const stamp = new Date().toISOString().replace(/[-:]/g, '').replace(/\..*$/, '');
  const logFile = path.join(LOG_DIR, 'launch-' + stamp + '.log');
  fs.writeFileSync(path.join(LOG_DIR, 'last_launch.log'), 'see ' + path.basename(logFile) + '\n');
  const out = fs.openSync(logFile, 'a');

  const child = spawnHidden(args, {
    cwd: REPO_ROOT,
    env: { ...process.env, PYTHONPATH: REPO_ROOT, PYTHONIOENCODING: 'utf-8', PYTHONUNBUFFERED: '1', BRAIN_TENANT: tenant },
    detached: true,
    stdio: ['ignore', out, out],
  });
  child.unref();

  return NextResponse.json({
    success: true,
    pid: child.pid,
    directive: directive || null,
    autonomous: !directive.trim(),
    note:
      'Writing started. A post takes about 20 minutes and shows in Posts as it runs.',
    log: logFile,
  });
}

export async function GET() {
  const latest = (await listGtmRunIds(1))[0];
  const s = latest ? await gtmRunSummary(latest) : null;
  return NextResponse.json({
    latestRun: latest ?? null,
    status: s?.status ?? null,
    agentsRan: s?.agents_ran ?? null,
  });
}
