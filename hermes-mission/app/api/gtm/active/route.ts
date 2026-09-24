import { NextResponse } from 'next/server';
import { listGtmRunIds, gtmRunSummary, gtmAgents } from '@/lib/gtm';

export const dynamic = 'force-dynamic';

/**
 * Runs that have STARTED, including the one in flight.
 *
 * Every other listing (`/api/runs`, `/api/gtm/runs`, `/api/v2/runs`) drops a
 * run whose `summary.json` is missing — and that file is only written when the
 * cycle finishes, 2-5 minutes in. So a run that is actively executing is
 * invisible to all of them, and the command console polled for something that
 * could not appear inside its 90-second deadline.
 *
 * `autonomous_cycle` creates the run directory the moment it takes the lock,
 * so listing directories shows a run about a second after launch. `finished`
 * says which of them actually completed.
 */
export async function GET(req: Request) {
  const url = new URL(req.url);
  const limit = Number(url.searchParams.get('limit') ?? 8);
  const withProgress = url.searchParams.get('progress') === '1';

  const ids = await listGtmRunIds(Number.isFinite(limit) ? limit : 8);
  const runs = await Promise.all(
    ids.map(async (id) => {
      const s = await gtmRunSummary(id);
      return { runId: id, finished: Boolean(s), status: s?.status ?? 'running' };
    }),
  );

  // Stage-by-stage progress for the newest run, so the console can say which
  // agent is working rather than only that something is.
  let progress: unknown = null;
  if (withProgress && ids.length) {
    const { agents } = await gtmAgents(ids[0]);
    const done = agents.filter((a) => a.status !== 'never_ran');
    progress = {
      runId: ids[0],
      ran: done.length,
      total: agents.length,
      current: done.length ? done[done.length - 1].name : null,
      failed: agents.filter((a) => a.status === 'failed').map((a) => a.id),
    };
  }

  return NextResponse.json({ runs, progress });
}
