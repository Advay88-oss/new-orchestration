/** Next calls register() once when the server starts. The watchdog is Node-only. */
export async function register() {
  if (process.env.NEXT_RUNTIME === 'nodejs') {
    const { startWatchdog } = await import('./instrumentation-node');
    startWatchdog();
  }
}
