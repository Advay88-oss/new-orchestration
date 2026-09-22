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
import { spawn } from 'child_process';

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
export function runPython(args: string[], timeoutMs = 120_000): Promise<PyResult> {
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
    const child = spawn(py, args, {
      cwd: REPO_ROOT,
      env: { ...process.env, PYTHONIOENCODING: 'utf-8', PYTHONUNBUFFERED: '1' },
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
