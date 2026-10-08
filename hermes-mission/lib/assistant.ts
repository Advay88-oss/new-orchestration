/**
 * The assistant's Python process (pipeline/assistant/server.py), kept alive
 * across requests so its Brain MCP sessions and imports are paid for once.
 *
 * Requests go down stdin as JSON lines; events come back on stdout tagged
 * with the request id. Turns run in parallel on the Python side. A turn can
 * be cancelled (the Stop button, or the browser going away). If the process
 * dies it is restarted on the next request; if it stops answering pings it
 * is killed and restarted.
 */
import type { ChildProcessWithoutNullStreams } from 'child_process';
import crypto from 'crypto';
import { spawnHidden } from '@/lib/python';
import { REPO_ROOT } from '@/lib/v2';

type Listener = (ev: Record<string, unknown>) => void;

interface State {
  child: ChildProcessWithoutNullStreams | null;
  buf: string;
  listeners: Map<string, Listener>;
  lastSeen: number;
  watchdog: NodeJS.Timeout | null;
  spawnedAt?: number;              // on the global too: a dev reload must not forget it
}

// On globalThis so Next's dev reloads do not start a second process.
const g = globalThis as unknown as { __vnAssistant2?: State };
const st: State = (g.__vnAssistant2 ??= { child: null, buf: '', listeners: new Map(), lastSeen: 0, watchdog: null });

const TURN_TIMEOUT_MS = 240_000;

function failAll(msg: string) {
  for (const l of st.listeners.values()) { l({ type: 'error', error: msg }); l({ type: 'done' }); }
  st.listeners.clear();
}

function write(obj: object) {
  start().stdin.write(JSON.stringify(obj) + '\n');
}

// The Python code the assistant runs. The process imports it once, so when a
// file here changes it is restarted at the next idle moment; otherwise a fix
// would not reach the chat until the dashboard itself was restarted.
const CODE_DIRS = ['pipeline/assistant', 'pipeline/scheduler', 'pipeline/brand_brain', 'pipeline/intelligence_stream', 'pipeline/ops'];

function codeChangedSince(t: number): boolean {
  const fs = require('fs') as typeof import('fs');
  const path = require('path') as typeof import('path');
  for (const d of CODE_DIRS) {
    const dir = path.join(REPO_ROOT, d);
    let names: string[] = [];
    try { names = fs.readdirSync(dir); } catch { continue; }
    for (const n of names) {
      if (!n.endsWith('.py')) continue;
      try { if (fs.statSync(path.join(dir, n)).mtimeMs > t) return true; } catch { /* gone */ }
    }
  }
  return false;
}

/** Called before a new turn registers: restarts the process when its code
 * changed and no other turn is open. */
function restartIfStale(): void {
  // Turns still open block a restart; one older than the turn timeout is a
  // leftover (a stream that never ended) and does not.
  const now = Date.now();
  for (const [k, fn] of Array.from(st.listeners)) {
    if (now - (((fn as any).at as number) || 0) > TURN_TIMEOUT_MS + 30_000) st.listeners.delete(k);
  }
  if (st.child && st.child.exitCode === null && !st.child.killed && st.listeners.size === 0
      && codeChangedSince(st.spawnedAt || 0)) {
    killTree(st.child);
    st.child = null;
  }
}

/** The venv's pythonw.exe is a launcher with python.exe under it: on
 * Windows the whole tree goes, or the old interpreter lives on. */
function killTree(child: ChildProcessWithoutNullStreams): void {
  try {
    if (process.platform === 'win32' && child.pid) {
      require('child_process').spawnSync('taskkill', ['/PID', String(child.pid), '/T', '/F'], { windowsHide: true });
    } else {
      child.kill();
    }
  } catch { /* already gone */ }
}

function start(): ChildProcessWithoutNullStreams {
  if (st.child && st.child.exitCode === null && !st.child.killed) return st.child;
  const child = spawnHidden(['-m', 'pipeline.assistant.server'], {
    cwd: REPO_ROOT,
    env: { ...process.env, PYTHONIOENCODING: 'utf-8', PYTHONUNBUFFERED: '1', PYTHONPATH: REPO_ROOT },
  });
  st.buf = '';
  st.lastSeen = Date.now();
  child.stdout.on('data', (d) => {
    st.lastSeen = Date.now();
    st.buf += d.toString();
    let i;
    while ((i = st.buf.indexOf('\n')) >= 0) {
      const line = st.buf.slice(0, i);
      st.buf = st.buf.slice(i + 1);
      try {
        const ev = JSON.parse(line);
        if (ev.id) st.listeners.get(String(ev.id))?.(ev);
      } catch { /* a stray print, not an event */ }
    }
  });
  child.stderr.on('data', () => { /* the child's own log noise */ });
  child.on('exit', () => {
    if (st.child !== child) return;      // an old process replaced on purpose
    failAll('the assistant restarted; ask again');
    st.child = null;
  });
  st.child = child;
  st.spawnedAt = Date.now();
  // Health: a ping every 30 s; no sign of life for 90 s while idle-or-busy
  // and the process is replaced.
  if (!st.watchdog) {
    st.watchdog = setInterval(() => {
      if (!st.child) return;
      if (Date.now() - st.lastSeen > 90_000) {
        killTree(st.child);
        return;
      }
      try { st.child.stdin.write(JSON.stringify({ op: 'ping', id: 'ping-' + Date.now() }) + '\n'); } catch { /* */ }
    }, 30_000);
    st.watchdog.unref?.();
  }
  return child;
}

export interface Turn { id: string; done: Promise<void>; cancel: () => void }

/** Start one turn; `onEvent` gets each event, ending with {type: 'done'}. */
export function ask(req: { tenant: string; text: string; thread_id?: string | null; base?: string; client?: boolean;
                           role: 'owner' | 'client' | 'visitor' },
                    onEvent: Listener): Turn {
  restartIfStale();
  const id = crypto.randomUUID();
  let finish!: () => void;
  const done = new Promise<void>((r) => (finish = r));
  const timer = setTimeout(() => {
    cancel();
    onEvent({ type: 'error', error: 'the assistant took too long' });
    onEvent({ type: 'done' });
    stop();                              // a turn that timed out must not stay registered
  }, TURN_TIMEOUT_MS);
  const stop = () => { clearTimeout(timer); st.listeners.delete(id); finish(); };
  st.listeners.set(id, Object.assign((ev: any) => { onEvent(ev); if (ev.type === 'done') stop(); }, { at: Date.now() }));
  function cancel() {
    try { write({ op: 'cancel', id }); } catch { /* process gone: nothing to stop */ }
  }
  try {
    write({ op: 'turn', id, ...req });
  } catch (e: any) {
    onEvent({ type: 'error', error: String(e?.message || e) });
    onEvent({ type: 'done' });
    stop();
  }
  return { id, done, cancel };
}
