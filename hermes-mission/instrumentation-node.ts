/**
 * Node-only half of instrumentation.ts. Keeps the local scheduler alive while this dashboard runs.
 *
 * On 2026-10-05 the scheduler process died with the laptop and nothing
 * restarted it, so every "Active" job on the page sat a day overdue. Next
 * calls register() once when the server starts; from then on the server asks
 * `daemon_manager.py ensure` every minute, which starts the scheduler only if
 * it is not running and the owner has not stopped it.
 *
 * Local only. On GCP the clock is Cloud Scheduler (see /api/daemon).
 */
import path from 'path';
import { pythonPath, spawnHidden } from './lib/python';

export function startWatchdog() {
  if (process.env.K_SERVICE || process.env.VANNA_CLOUD === '1' || process.env.VANNA_NO_WATCHDOG === '1') return;
  const root = process.env.REPO_ROOT || path.resolve(process.cwd(), '..');
  const py = pythonPath();
  if (!py) return;

  const g = globalThis as unknown as { __vnWatchdog?: NodeJS.Timeout };
  if (g.__vnWatchdog) return; // dev reloads call register() again

  const ensure = () => {
    const child = spawnHidden(['pipeline/scripts/daemon_manager.py', 'ensure'], {
      cwd: root,
      env: { ...process.env, PYTHONPATH: root, PYTHONIOENCODING: 'utf-8' },
      stdio: ['ignore', 'pipe', 'ignore'],
    });
    let out = '';
    child.stdout?.on('data', (d) => { out += d.toString(); });
    child.on('close', () => {
      try {
        const res = JSON.parse(out);
        if (res.ensured === 'restarted') console.log(`[watchdog] scheduler restarted (pid ${res.pid})`);
        else if (res.ensured === 'could not start') console.log(`[watchdog] scheduler could not start: ${res.message || ''}`);
      } catch { /* the next check tries again */ }
    });
  };
  ensure();
  g.__vnWatchdog = setInterval(ensure, 60_000);
}
