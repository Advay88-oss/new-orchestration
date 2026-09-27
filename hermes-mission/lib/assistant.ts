/**
 * The assistant's Python process (pipeline/assistant/server.py), kept alive
 * across requests so its Brain MCP session and imports are paid for once.
 *
 * One request per stdin line; its events come back as stdout lines tagged
 * with the request id. Turns run one at a time (the process is sequential),
 * so a queue orders them. If the process dies it is started again on the
 * next request.
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
  chain: Promise<void>;
}

// On globalThis so Next's dev reloads do not start a second process.
const g = globalThis as unknown as { __vnAssistant?: State };
const st: State = (g.__vnAssistant ??= { child: null, buf: '', listeners: new Map(), chain: Promise.resolve() });

function start(): ChildProcessWithoutNullStreams {
  if (st.child && st.child.exitCode === null && !st.child.killed) return st.child;
  const py = pythonPath();
  if (!py) throw new Error('no python interpreter for the assistant');
  const child = spawn(py, ['-m', 'pipeline.assistant.server'], {
    cwd: REPO_ROOT,
    env: { ...process.env, PYTHONIOENCODING: 'utf-8', PYTHONUNBUFFERED: '1', PYTHONPATH: REPO_ROOT },
  });
  st.buf = '';
  child.stdout.on('data', (d) => {
    st.buf += d.toString();
    let i;
    while ((i = st.buf.indexOf('\n')) >= 0) {
      const line = st.buf.slice(0, i);
      st.buf = st.buf.slice(i + 1);
      try {
        const ev = JSON.parse(line);
        if (ev.id) st.listeners.get(String(ev.id))?.(ev);
      } catch {
        /* a stray print, not an event */
      }
    }
  });
  child.stderr.on('data', () => { /* logged by the child's own tools; kept off the stream */ });
  child.on('exit', () => {
    for (const l of st.listeners.values()) l({ type: 'error', error: 'the assistant stopped; ask again' });
    for (const l of st.listeners.values()) l({ type: 'done' });
    st.listeners.clear();
    st.child = null;
  });
  st.child = child;
  return child;
}

/** Run one turn; `onEvent` gets each event, ending with {type: 'done'}. */
export function ask(tenant: string, messages: unknown[], onEvent: Listener, base = ''): Promise<void> {
  const run = () =>
    new Promise<void>((resolve) => {
      const id = crypto.randomUUID();
      const timer = setTimeout(() => {
        onEvent({ type: 'error', error: 'the assistant took too long' });
        onEvent({ type: 'done' });
        st.listeners.delete(id);
        resolve();
      }, 240_000);
      st.listeners.set(id, (ev) => {
        onEvent(ev);
        if (ev.type === 'done') {
          clearTimeout(timer);
          st.listeners.delete(id);
          resolve();
        }
      });
      try {
        start().stdin.write(JSON.stringify({ id, tenant, messages, base }) + '\n');
      } catch (e: any) {
        onEvent({ type: 'error', error: String(e?.message || e) });
        onEvent({ type: 'done' });
        clearTimeout(timer);
        st.listeners.delete(id);
        resolve();
      }
    });
  const p = st.chain.then(run, run);
  st.chain = p.catch(() => undefined);
  return p;
}
