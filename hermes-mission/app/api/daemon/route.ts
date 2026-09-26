import { NextResponse } from 'next/server';
import { runPython, lastJson, pythonPath } from '@/lib/python';
import { spawnSync } from 'child_process';
import path from 'path';
import fs from 'fs';
import { localOnly } from '@/lib/local-only';

const REPO_ROOT = process.env.REPO_ROOT || (fs.existsSync('/app') ? '/app' : path.resolve(process.cwd(), '..'));
const SCRIPT_PATH = path.join(REPO_ROOT, 'pipeline/scripts/daemon_manager.py');
const PID_FILE = path.join(REPO_ROOT, 'pipeline/state/daemon.pid');
const STATUS_FILE = path.join(REPO_ROOT, 'pipeline/state/daemon_status.json');

export const dynamic = 'force-dynamic';

export async function GET() {
  const blocked = localOnly('the daemon');
  if (blocked) return blocked;

  try {
    let pid: number | null = null;
    let isRunning = false;

    if (fs.existsSync(PID_FILE)) {
      try {
        const raw = fs.readFileSync(PID_FILE, 'utf-8').trim();
        pid = parseInt(raw, 10);
      } catch {}
    }

    let statusInfo: any = {};
    if (fs.existsSync(STATUS_FILE)) {
      try {
        statusInfo = JSON.parse(fs.readFileSync(STATUS_FILE, 'utf-8'));
      } catch {}
    }

    // Call python daemon_manager.py status for accurate process check
        const pyBinary = pythonPath() as string;
    const pyArgs = ['pipeline/scripts/daemon_manager.py', 'status'];
    const py = spawnSync(pyBinary, pyArgs, { cwd: REPO_ROOT, encoding: 'utf-8', env: { ...process.env, PYTHONPATH: REPO_ROOT } });
    if (py.status === 0 && py.stdout) {
      try {
        const parsed = JSON.parse(py.stdout.trim());
        return NextResponse.json(parsed);
      } catch {}
    }

    return NextResponse.json({
      status: pid ? "UNKNOWN" : "STOPPED",
      pid,
      running: false,
      info: statusInfo
    });
  } catch (e: any) {
    return NextResponse.json({ error: e.message, status: "ERROR", running: false }, { status: 500 });
  }
}

export async function POST(req: Request) {
  const blocked = localOnly('the daemon');
  if (blocked) return blocked;

  try {
    const body = await req.json().catch(() => ({}));
    const action = (body.action || "status").toLowerCase(); // "start" | "stop" | "restart" | "status"
    const interval = body.interval_seconds || 1800;

        const pyBinary = pythonPath() as string;
    const rawArgs = ['pipeline/scripts/daemon_manager.py', action];
    if (action === "start" || action === "restart") {
      rawArgs.push('--interval', String(interval));
    }
    const pyArgs = rawArgs;

    const py = spawnSync(pyBinary, pyArgs, { cwd: REPO_ROOT, encoding: 'utf-8', env: { ...process.env, PYTHONPATH: REPO_ROOT } });
    if (py.status === 0 && py.stdout) {
      try {
        const parsed = JSON.parse(py.stdout.trim());
        return NextResponse.json(parsed);
      } catch {}
    }

    return NextResponse.json({
      success: py.status === 0,
      stdout: py.stdout,
      stderr: py.stderr
    });
  } catch (e: any) {
    return NextResponse.json({ error: e.message }, { status: 500 });
  }
}
