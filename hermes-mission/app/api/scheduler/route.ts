import { NextResponse } from 'next/server';
import { runPython, lastJson, pythonPath } from '@/lib/python';
import { exec, spawn } from 'child_process';
import path from 'path';
import fs from 'fs';

const REPO_ROOT = process.env.REPO_ROOT || (fs.existsSync('/app') ? '/app' : 'D:/new orchestration');
const SCHEDULER_SCRIPT = path.join(REPO_ROOT, 'pipeline/scheduler/configurable_scheduler_daemon.py');
const SCHEDULER_STATE_FILE = path.join(REPO_ROOT, 'pipeline/state/scheduler_state.json');
const CONFIG_FILE = path.join(REPO_ROOT, 'config/scheduler.yaml');

export const dynamic = 'force-dynamic';

export async function GET() {
  try {
    // 1. First try reading directly from state file & config for sub-millisecond response
    if (fs.existsSync(SCHEDULER_STATE_FILE) && fs.existsSync(CONFIG_FILE)) {
      try {
        const stateRaw = fs.readFileSync(SCHEDULER_STATE_FILE, 'utf-8');
        const stateData = JSON.parse(stateRaw);
        
        // Simple YAML parse for job intervals
        const yamlRaw = fs.readFileSync(CONFIG_FILE, 'utf-8');
        const jobsList: any[] = [];
        
        const jobDefs: Record<string, { desc: string; defaultInt: string; isModel: boolean }> = {
          research_collect: { desc: "Full research collection across all 8 sources via OpenCLI & on-chain RPC.", defaultInt: "12h", isModel: true },
          trend_scan: { desc: "Zero-cost real-time trend & news monitoring (Google News RSS + Curve/Stellar news).", defaultInt: "2m", isModel: false },
          ideas_panel: { desc: "Synthesizes 8-12 claim-gated actionable GTM ideas from newly scraped artefacts.", defaultInt: "6h", isModel: true },
          memes_panel: { desc: "Scans crypto culture for liquidation/gas humor with strict claim & risk gating.", defaultInt: "2h", isModel: true }
        };

        for (const [jKey, meta] of Object.entries(jobDefs)) {
          const st = stateData[jKey] || {};
          let currentInterval = meta.defaultInt;
          const matchInt = yamlRaw.match(new RegExp(`${jKey}:[\\s\\S]*?interval:\\s*["']?([^"'\n\r]+)["']?`));
          if (matchInt && matchInt[1]) {
            currentInterval = matchInt[1].trim();
          }

          jobsList.push({
            job: jKey,
            description: meta.desc,
            interval: currentInterval,
            enabled: st.status !== "DISABLED_AUTO_BACKOFF",
            status: st.status || "COMPLETED",
            last_run: st.last_run || "Never",
            next_run: st.last_run ? new Date(new Date(st.last_run).getTime() + (currentInterval.endsWith('m') ? parseInt(currentInterval)*60000 : parseInt(currentInterval)*3600000)).toISOString() : "Pending Tick",
            consecutive_failures: st.consecutive_failures || 0,
            total_runs: st.total_runs || 1,
            last_duration_s: st.last_duration_s || 0.5
          });
        }

        return NextResponse.json({
          success: true,
          jobs: jobsList,
          timestamp: new Date().toISOString()
        });
      } catch (err: any) {
        console.warn("[Scheduler API] File read notice, falling back to python CLI:", err);
      }
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
  try {
    const body = await req.json();
    const { action, job, interval } = body;

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
      if (!job) {
        return NextResponse.json({ success: false, error: 'job required' }, { status: 400 });
      }
            
      const rawArgs = ['pipeline/scheduler/configurable_scheduler_daemon.py', '--run-now', job];
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
          const jsonMatch = stdout.match(/\{[\s\S]*\}/);
          if (jsonMatch) {
            try {
              const data = JSON.parse(jsonMatch[0]);
              resolve(NextResponse.json({ success: true, result: data }));
              return;
            } catch {}
          }
          if (code === 0) {
            resolve(NextResponse.json({ success: true, output: stdout.trim() }));
          } else {
            resolve(NextResponse.json({ success: false, error: stderr || stdout || `Process exited with code ${code}` }, { status: 500 }));
          }
        });
      });
    }

    return NextResponse.json({ success: false, error: `Unknown action: ${action}` }, { status: 400 });
  } catch (err: any) {
    return NextResponse.json({ success: false, error: err.message }, { status: 500 });
  }
}
