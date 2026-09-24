import { NextResponse } from 'next/server';
import { listGtmRunIds, gtmAgents, gtmRunSummary } from '@/lib/gtm';

export const dynamic = 'force-dynamic';

/**
 * Live progress of the newest GTM cycle, agent by agent.
 *
 * This read `lib/v2` — the `core/` pipeline — so the command console launched
 * the 13 agents and then displayed a different system's stages. That is why it
 * showed "STEP 13 / 13 · review (STAGE) · staged but BLOCKED for publication"
 * while A01 was still scraping: those are core's stage names and core's
 * claim-gate prose, from a run that had nothing to do with the directive just
 * submitted.
 *
 * Now it reads the same journal the rest of the dashboard does. A run is
 * visible here about a second after launch, because the cycle creates its
 * directory when it takes the lock — long before `summary.json` exists.
 */
export async function GET(req: Request) {
  const wanted = new URL(req.url).searchParams.get('runId') || undefined;
  const id = wanted || (await listGtmRunIds(1))[0];

  if (!id) {
    return NextResponse.json({
      step: 0, total: 13, run_id: null, state: 'idle',
      agent_name: '—', detail: 'No run recorded yet.', timestamp: Date.now() / 1000,
    });
  }

  const [{ agents }, summary] = await Promise.all([gtmAgents(id), gtmRunSummary(id)]);

  // `summary.json` is written only at the end, so its absence is what tells us
  // the cycle is still going.
  const finished = Boolean(summary);
  const done = agents.filter((a) => a.status !== 'never_ran');
  const current = done.length ? done[done.length - 1] : null;
  const failed = agents.filter((a) => a.status === 'failed').map((a) => a.id);

  return NextResponse.json({
    step: done.length,
    total: agents.length,
    run_id: id,
    state: finished ? summary.status : 'running',
    finished,
    agent_name: current ? `${current.id} · ${current.name}` : 'starting…',
    detail: current?.detail || (finished ? '' : 'waiting for the first agent to report…'),
    model: current?.model ?? null,
    failed,
    timestamp: Date.now() / 1000,
  });
}
