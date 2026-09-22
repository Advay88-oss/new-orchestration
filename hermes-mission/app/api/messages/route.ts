import { NextResponse } from 'next/server';
import { listRunIds, runView, runReasoning } from '@/lib/v2';

export const dynamic = 'force-dynamic';

/**
 * Stage messages, from the run journal.
 *
 * This route previously replayed a relay log of drafts from August 2026, whose
 * entries carry `"pubkey": "strategist-undefined"` — a bug the audit recorded.
 * There is no relay in this pipeline: stages pass typed values inside one
 * process. What follows is the sequence of things stages actually produced.
 */
export async function GET(req: Request) {
  const limit = Number(new URL(req.url).searchParams.get('limit') ?? 200);
  const out: Record<string, unknown>[] = [];

  for (const id of listRunIds(20)) {
    const run = runView(id);
    if (!run) continue;
    const reasoning = runReasoning(id);

    for (const s of run.stages) {
      if (s.state === 'not_reached') continue;
      let content = s.purpose;
      if (s.stage === 'strategy' && reasoning.angle) content = reasoning.angle;
      else if (s.stage === 'copy' && reasoning.hook) content = reasoning.hook;
      else if (s.stage === 'verify') {
        const v = reasoning.claims.filter((c: any) => c.status === 'verified').length;
        content = `${v} of ${reasoning.claims.length} claims verified against evidence`;
      } else if (s.stage === 'concept' && reasoning.chosenConcept) {
        content = `Selected "${reasoning.chosenConcept.title}" (${reasoning.chosenConcept.layout})`;
      } else if (s.degradedReason) content = s.degradedReason;
      else if (s.error) content = s.error;

      out.push({
        id: `${run.runId}:${s.stage}`,
        run_id: run.runId,
        stage: s.stage,
        kind: s.kind,
        status: s.status,
        model: s.model,
        content,
        created_at: run.startedAt,
      });
      if (out.length >= limit) return NextResponse.json(out);
    }
  }
  return NextResponse.json(out);
}
