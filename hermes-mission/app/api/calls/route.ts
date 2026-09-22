import { NextResponse } from 'next/server';
import { listRunIds, runView } from '@/lib/v2';

export const dynamic = 'force-dynamic';

/**
 * Model calls, from the run journal.
 *
 * The previous source was the retired spend proxy's log, whose entries carry
 * `"rewritten_from": "gemini-3.8-flash"` next to `"model": "gemini-2.5-flash"` —
 * the silent downgrade the audit documented. Journal entries record the model
 * the provider itself reported, so no rewrite can hide in them.
 */
export async function GET(req: Request) {
  const limit = Number(new URL(req.url).searchParams.get('limit') ?? 200);
  const calls: Record<string, unknown>[] = [];
  let seq = 0;

  for (const id of listRunIds(50)) {
    const run = runView(id);
    if (!run) continue;
    for (const s of run.stages) {
      if (!s.model) continue;
      calls.push({
        seq: ++seq,
        run_id: run.runId,
        stage: s.stage,
        kind: s.kind,
        model: s.model,
        prompt_version: s.promptVersion,
        usage: { promptTokenCount: s.inputTokens, candidatesTokenCount: s.outputTokens },
        cost_usd: s.costUsd,
        cost_known: s.costKnown,
        attempts: s.attempts,
        duration_s: s.durationS,
        tools: s.toolCalls,
        status: s.status,
      });
      if (calls.length >= limit) return NextResponse.json(calls);
    }
  }
  return NextResponse.json(calls);
}
