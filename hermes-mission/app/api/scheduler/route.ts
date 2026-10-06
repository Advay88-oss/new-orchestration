import { NextResponse } from 'next/server';
import { runPython, lastJson, pythonPath } from '@/lib/python';
import { spawn } from 'child_process';
import path from 'path';
import fs from 'fs';
import { cloudMode, localOnly } from '@/lib/local-only';
import { isDeployed, getText } from '@/lib/gcs';
import { runPipelineJob } from '@/lib/cloudrun';

const REPO_ROOT = process.env.REPO_ROOT || (fs.existsSync('/app') ? '/app' : path.resolve(process.cwd(), '..'));
const SCHEDULER_SCRIPT = path.join(REPO_ROOT, 'pipeline/scheduler/configurable_scheduler_daemon.py');
const SCHEDULER_STATE_FILE = path.join(REPO_ROOT, 'pipeline/state/scheduler_state.json');
const CONFIG_FILE = path.join(REPO_ROOT, 'config/scheduler.yaml');

export const dynamic = 'force-dynamic';

/** The jobs as the pipeline config and its state file describe them. */
function jobsFromPipeline(): { success: true; jobs: any[]; timestamp: string } | null {
  if (!fs.existsSync(CONFIG_FILE)) return null;
  const yamlRaw = fs.readFileSync(CONFIG_FILE, 'utf-8').replace(/\r\n/g, '\n');
  const body = yamlRaw.split(/^jobs:\s*$/m)[1];
  if (!body) return null;
  let stateData: Record<string, any> = {};
  if (fs.existsSync(SCHEDULER_STATE_FILE)) {
    try { stateData = JSON.parse(fs.readFileSync(SCHEDULER_STATE_FILE, 'utf-8')); } catch { stateData = {}; }
  }
  const jobs = body.split(/\n(?=  [a-z0-9_]+:\s*$)/m).flatMap((chunk) => {
    const name = chunk.match(/^  ([a-z0-9_]+):/m)?.[1];
    if (!name) return [];
    const interval = (chunk.match(/interval:\s*["']?([^"'\n]+)/)?.[1] || '24h').trim();
    const description = chunk.match(/description:\s*"([^"]*)"/)?.[1]
      || chunk.match(/description:\s*'([^']*)'/)?.[1]
      || '';
    const modelHeavy = /model_heavy:\s*true/.test(chunk);
    const enabled = !/enabled:\s*false/.test(chunk);
    const st = stateData[name] || {};
    const last = st.last_run || null;
    let next = 'Overdue / Pending';
    if (last) {
      const sec = interval.endsWith('m') ? parseInt(interval, 10) * 60 : parseInt(interval, 10) * 3600;
      const t = new Date(last).getTime();
      if (!Number.isNaN(t) && sec) next = new Date(t + sec * 1000).toISOString();
    }
    return [{
      job: name,
      description,
      interval,
      model_heavy: modelHeavy,
      enabled: enabled && st.status !== 'DISABLED_AUTO_BACKOFF',
      status: st.status || 'IDLE',
      last_run: last || 'Never',
      next_run: next,
      consecutive_failures: st.consecutive_failures || 0,
      total_runs: st.total_runs || 0,
      last_duration_s: st.last_duration_s || 0,
    }];
  });
  return { success: true, jobs, timestamp: new Date().toISOString() };
}

export async function GET() {
  const blocked = localOnly('the scheduler');
  if (blocked) return blocked;

  try {
    const listed = jobsFromPipeline();
    if (listed) {
      let raw: string | null = null;
      if (isDeployed()) raw = await getText('state/pipeline/state/scheduler_intervals.json');
      else {
        const p = path.join(REPO_ROOT, 'pipeline', 'state', 'scheduler_intervals.json');
        try { raw = fs.readFileSync(p, 'utf-8'); } catch { raw = null; }
      }
      if (raw) {
        try {
          const chosen = JSON.parse(raw) as Record<string, unknown>;
          const paused = new Set((Array.isArray(chosen._paused) ? chosen._paused : []).map(String));
          const on = new Set((Array.isArray(chosen._on) ? chosen._on : []).map(String));
          for (const job of listed.jobs) {
            if (typeof chosen[job.job] === 'string') job.interval = chosen[job.job];
            if (on.has(job.job)) job.enabled = true;
            if (paused.has(job.job)) {
              job.paused = true;
              job.enabled = false;
              if (job.status !== 'RUNNING') job.status = 'STOPPED';
            }
          }
          const cronState = (chosen._cron_state && typeof chosen._cron_state === 'object')
            ? chosen._cron_state as Record<string, any> : {};
          for (const job of listed.jobs) {
            const st = cronState[job.job] || {};
            job.cron = typeof st.cron === 'string' ? st.cron : '';
            job.cron_id = typeof st.id === 'string' ? st.id : '';
            job.cron_state = typeof st.state === 'string' ? st.state : '';
            job.lands = typeof st.lands === 'string' ? st.lands : '';
          }
          (listed as any).posts = paused.has('gtm_cycle') ? 'stopped' : 'on';
          (listed as any).until = typeof chosen._until === 'string' ? chosen._until : '';
          (listed as any).posts_left = typeof chosen._posts_left === 'number' ? chosen._posts_left : null;
          (listed as any).chain = chosen._post_chain && typeof chosen._post_chain === 'object' ? chosen._post_chain : null;
        } catch { /* the yaml interval stands */ }
      }
      return NextResponse.json(listed);
    }

    // 2. Fallback to executing python CLI
    return new Promise<Response>((resolve) => {
      runPython([SCHEDULER_SCRIPT, '--status'], 60_000).then((r) => {
        if (!r.ok) {
          resolve(NextResponse.json(
            { success: false, error: r.error || r.stderr.trim().slice(-500) || `exit ${r.code}` },
            { status: 500 },
          ));
          return;
        }
        resolve(NextResponse.json(lastJson(r.stdout) ?? { success: true, jobs: [] }));
      });
    });
  } catch (err: any) {
    return NextResponse.json({ success: false, error: err.message }, { status: 500 });
  }
}

export async function POST(req: Request) {
  const blocked = localOnly('the scheduler');
  if (blocked) return blocked;

  try {
    const body = await req.json();
    const { action, job, interval } = body;

    if (action === 'tell') {
      const text = String(body.text || '').trim().slice(0, 240);
      if (!text) return NextResponse.json({ success: false, error: 'say what you want' }, { status: 400 });
      const py = pythonPath();
      if (!py) return NextResponse.json({ success: false, error: 'no python interpreter' }, { status: 503 });
      return new Promise<Response>((resolve) => {
        const child = spawn(py, [SCHEDULER_SCRIPT, '--tell', text], {
          cwd: REPO_ROOT,
          env: { ...process.env, PYTHONPATH: REPO_ROOT, PYTHONUNBUFFERED: '1', PYTHONIOENCODING: 'utf-8' },
        });
        let stdout = '';
        let stderr = '';
        child.stdout.on('data', (d) => { stdout += d.toString(); });
        child.stderr.on('data', (d) => { stderr += d.toString(); });
        child.on('close', (code) => {
          if (code === 0) {
            try {
              const last = stdout.trim().split('\n').filter(Boolean).pop() || '{}';
              resolve(NextResponse.json({ success: true, ...JSON.parse(last) }));
            } catch {
              resolve(NextResponse.json({ success: true, message: stdout.trim() }));
            }
          } else {
            resolve(NextResponse.json({ success: false, error: (stderr || stdout).trim().slice(-300) || 'that did not stick' }, { status: 400 }));
          }
        });
      });
    }

    if (action === 'set_interval') {
      if (!job || !interval) {
        return NextResponse.json({ success: false, error: 'job and interval required' }, { status: 400 });
      }
            
      const rawArgs = ['pipeline/scheduler/configurable_scheduler_daemon.py', '--set-interval', job, interval];
      const spawnArgs = rawArgs;

      return new Promise<Response>((resolve) => {
        const py = spawn(pythonPath() as string, spawnArgs, {
          cwd: REPO_ROOT,
          env: { ...process.env, PYTHONPATH: REPO_ROOT, PYTHONUNBUFFERED: '1' }
        });
        let stdout = '';
        let stderr = '';
        py.stdout.on('data', (d) => { stdout += d.toString(); });
        py.stderr.on('data', (d) => { stderr += d.toString(); });
        py.on('close', (code) => {
          if (code === 0) {
            resolve(NextResponse.json({ success: true, message: stdout.trim() }));
          } else {
            resolve(NextResponse.json({ success: false, error: stderr || stdout || `Exited with code ${code}` }, { status: 400 }));
          }
        });
      });
    }

    if (action === 'run_now') {
      if (!job || !/^[a-z0-9_]+$/.test(job)) {
        return NextResponse.json({ success: false, error: 'job required' }, { status: 400 });
      }
      const known = jobsFromPipeline();
      if (known && !known.jobs.some((j) => j.job === job)) {
        return NextResponse.json({ success: false, error: 'unknown job: ' + job }, { status: 400 });
      }
      const running = known?.jobs.find((j) => j.job === job && j.status === 'RUNNING');
      if (running) {
        return NextResponse.json({ success: false, error: job + ' is already running on the pipeline' }, { status: 409 });
      }
      // The page only asks. The job runs on the pipeline and reports back
      // through the scheduler state file, which this view already polls.
      if (cloudMode()) {
        const args = job === 'gtm_cycle' ? ['cycle'] : ['sched', '--job', job];
        const r = await runPipelineJob(args);
        return NextResponse.json(r.ok
          ? { success: true, started: true, job, execution: r.execution }
          : { success: false, error: r.error }, { status: r.ok ? 200 : 502 });
      }
      const py = pythonPath();
      if (!py) {
        return NextResponse.json({ success: false, error: 'no python interpreter for the pipeline' }, { status: 503 });
      }
      const logFile = path.join(REPO_ROOT, 'pipeline', 'state', 'scheduler_run_now.log');
      fs.mkdirSync(path.dirname(logFile), { recursive: true });
      const out = fs.openSync(logFile, 'a');
      const child = spawn(py, [SCHEDULER_SCRIPT, '--run-now', job], {
        cwd: REPO_ROOT,
        env: { ...process.env, PYTHONPATH: REPO_ROOT, PYTHONIOENCODING: 'utf-8' },
        detached: true,
        stdio: ['ignore', out, out],
      });
      child.unref();
      return NextResponse.json({ success: true, started: true, job, pid: child.pid });
    }

    return NextResponse.json({ success: false, error: `Unknown action: ${action}` }, { status: 400 });
  } catch (err: any) {
    return NextResponse.json({ success: false, error: err.message }, { status: 500 });
  }
}
