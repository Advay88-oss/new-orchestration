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
import { spawn, type ChildProcessWithoutNullStreams } from 'child_process';
import crypto from 'crypto';
import { pythonPath } from '@/lib/python';
import { REPO_ROOT } from '@/lib/v2';

type Listener = (ev: Record<string, unknown>) => void;

interface State {
  child: ChildProcessWithoutNullStreams | null;
  buf: string;
  listeners: Map<string, Listener>;
  lastSeen: number;
  watchdog: NodeJS.Timeout | null;
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

function start(): ChildProcessWithoutNullStreams {
  if (st.child && st.child.exitCode === null && !st.child.killed) return st.child;
  const py = pythonPath();
  if (!py) throw new Error('no python interpreter for the assistant');
  const child = spawn(py, ['-m', 'pipeline.assistant.server'], {
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
    failAll('the assistant restarted; ask again');
    st.child = null;
  });
  st.child = child;
  // Health: a ping every 30 s; no sign of life for 90 s while idle-or-busy
  // and the process is replaced.
  if (!st.watchdog) {
    st.watchdog = setInterval(() => {
      if (!st.child) return;
      if (Date.now() - st.lastSeen > 90_000) {
        try { st.child.kill(); } catch { /* already gone */ }
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
export function ask(req: { tenant: string; text: string; thread_id?: string | null; base?: string },
                    onEvent: Listener): Turn {
  const id = crypto.randomUUID();
  let finish!: () => void;
  const done = new Promise<void>((r) => (finish = r));
  const timer = setTimeout(() => {
    cancel();
    onEvent({ type: 'error', error: 'the assistant took too long' });
    onEvent({ type: 'done' });
  }, TURN_TIMEOUT_MS);
  const stop = () => { clearTimeout(timer); st.listeners.delete(id); finish(); };
  st.listeners.set(id, (ev) => { onEvent(ev); if (ev.type === 'done') stop(); });
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
