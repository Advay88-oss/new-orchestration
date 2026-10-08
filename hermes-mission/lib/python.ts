/**
 * Resolve the interpreter that can actually run this project's Python.
 *
 * The 2026-09-21 audit found every dashboard trigger spawning a bare `python`
 * — which on this machine resolves to the Windows Store stub and fails with
 * "Python was not found". Seven routes shared that bug, so they share this fix.
 *
 * The venv is checked for existence rather than assumed: a route that cannot
 * find an interpreter must say so, not spawn something that will fail with a
 * message no one reads.
 */
import fs from 'fs';
import path from 'path';
import { spawn, type ChildProcessWithoutNullStreams, type SpawnOptions } from 'child_process';

import { REPO_ROOT } from './v2';

let cached: string | null | undefined;

export function pythonPath(): string | null {
  if (cached !== undefined) return cached;

  const candidates = [
    process.env.VANNA_PYTHON,
    path.join(REPO_ROOT, '.venv', 'Scripts', 'python.exe'), // Windows venv
    path.join(REPO_ROOT, '.venv', 'bin', 'python3'), // POSIX venv
    path.join(REPO_ROOT, '.venv', 'bin', 'python'),
  ].filter(Boolean) as string[];

  for (const c of candidates) {
    try {
      if (fs.existsSync(c)) {
        cached = c;
        return cached;
      }
    } catch {
      /* keep looking */
    }
  }
  cached = null;
  return cached;
}

/**
 * Start a pipeline process without a console window.
 *
 * On Windows, a console python.exe started from this app (which has no
 * console of its own) opens a PowerShell window. Every spawn uses pythonw
 * when the venv has it, and windowsHide, so a post, a visual, or a scrape
 * does not flash a window. pythonw still writes to the pipes we pass it.
 */
export function spawnHidden(args: string[], opts: SpawnOptions = {}): ChildProcessWithoutNullStreams {
  const py = pythonPath();
  if (!py) throw new Error('no python interpreter');
  let bin = py;
  if (process.platform === 'win32') {
    const windowless = py.replace(/python\.exe$/i, 'pythonw.exe');
    try { if (fs.existsSync(windowless)) bin = windowless; } catch { /* python.exe */ }
  }
  // Call sites read stdout and stderr. A detached job may set stdio to
  // 'ignore'; those callers never touch the streams.
  // detached:true on Windows sets DETACHED_PROCESS, and Windows then ignores
  // windowsHide and opens a PowerShell window. pythonw plus windowsHide is
  // enough; the Next server stays up, so the child does not need to detach.
  const hidden = process.platform === 'win32' ? { ...opts, detached: false } : opts;
  return spawn(bin, args, { ...hidden, windowsHide: true, shell: false }) as ChildProcessWithoutNullStreams;
}

export interface PyResult {
  ok: boolean;
  code: number | null;
  stdout: string;
  stderr: string;
  error?: string;
}

/**
 * Run a project script to completion and capture its output.
 *
 * Use only for short, read-shaped commands (status, list, a single panel
 * refresh). Anything that takes minutes belongs in the job queue — a pipeline
 * run tied to an HTTP request is the anti-pattern this codebase is removing.
 */
export function runPython(args: string[], timeoutMs = 120_000, input?: string,
                          env: Record<string, string> = {}): Promise<PyResult> {
  const py = pythonPath();
  if (!py) {
    return Promise.resolve({
      ok: false,
      code: null,
      stdout: '',
      stderr: '',
      error:
        `No interpreter found. Looked for .venv under ${REPO_ROOT}. ` +
        `Create it and install requirements.txt, or set VANNA_PYTHON.`,
    });
  }

  return new Promise<PyResult>((resolve) => {
    // No shell, no cmd.exe: arguments are passed as argv, so a directive
    // containing &, |, ^ or quotes cannot become a second command.
    const child = spawnHidden(args, {
      cwd: REPO_ROOT,
      // `env` carries the tenant a request is for (BRAIN_TENANT), e.g. a client's own company.
      env: { ...process.env, PYTHONIOENCODING: 'utf-8', PYTHONUNBUFFERED: '1', ...env },
    });

    let stdout = '';
    let stderr = '';
    let settled = false;

    const timer = setTimeout(() => {
      if (settled) return;
      settled = true;
      child.kill();
      resolve({
        ok: false, code: null, stdout, stderr,
        error: `timed out after ${timeoutMs}ms`,
      });
    }, timeoutMs);

    // Secrets and codes go on stdin, never in argv (argv is visible to other processes).
    if (input !== undefined) child.stdin.end(input);
    else child.stdin.end();

    child.stdout.on('data', (d) => { stdout += d.toString(); });
    child.stderr.on('data', (d) => { stderr += d.toString(); });

    child.on('error', (err) => {
      if (settled) return;
      settled = true;
      clearTimeout(timer);
      resolve({ ok: false, code: null, stdout, stderr, error: String(err) });
    });

    child.on('close', (code) => {
      if (settled) return;
      settled = true;
      clearTimeout(timer);
      resolve({ ok: code === 0, code, stdout, stderr });
    });
  });
}

/** Parse the last JSON object printed on stdout. */
export function lastJson<T = unknown>(stdout: string): T | null {
  const start = stdout.lastIndexOf('{');
  if (start === -1) return null;
  try {
    return JSON.parse(stdout.slice(start)) as T;
  } catch {
    // Some scripts print a JSON array, or JSON before trailing log lines.
    const m = stdout.match(/[[{][\s\S]*[\]}]/);
    if (!m) return null;
    try {
      return JSON.parse(m[0]) as T;
    } catch {
      return null;
    }
  }
}
