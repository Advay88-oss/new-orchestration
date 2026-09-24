import { NextResponse } from 'next/server';
import { manifest, listRunIds, runView } from '@/lib/v2';
import { localOnly } from '@/lib/local-only';

export const dynamic = 'force-dynamic';

/**
 * Agent status, derived from the manifest and the most recent run journal.
 *
 * This file previously returned 133 lines of hardcoded JSON — all thirteen
 * agents permanently `"connected"` with invented `working_on` and `log`
 * strings — while importing `fs` and never using it. Nothing below is
 * synthesised: `status` reflects what the last run actually recorded.
 */
export async function GET() {
  // This reports the `core/` pipeline, whose manifest is read from disk. In
  // the container that file does not exist, and a bare 503 reads as a server
  // fault rather than a system that was never deployed. The founder's own 13
  // agents are at /api/gtm/agents, which is sourced from GCS.
  const blocked = localOnly('core/ stage status');
  if (blocked) return blocked;

  const stages = manifest();
  if (stages.length === 0) {
    return NextResponse.json(
      { error: 'manifest unavailable; cannot report agent status' },
      { status: 503 },
    );
  }

  const latestId = listRunIds(1)[0];
  const run = latestId ? runView(latestId) : null;
  const byStage = new Map((run?.stages ?? []).map((s) => [s.stage, s]));

  const agents = stages.map((m) => {
    const s = byStage.get(m.stage);
    return {
      id: m.stage,
      n: m.n,
      role: m.purpose,
      kind: m.kind,
      // "connected" is not a thing a stage can be. These are the states a run
      // can actually leave behind.
      status: s?.state ?? 'never_run',
      last_run: run?.runId ?? null,
      model: s?.model ?? null,
      prompt_version: s?.promptVersion ?? null,
      input_tokens: s?.inputTokens ?? 0,
      output_tokens: s?.outputTokens ?? 0,
      duration_s: s?.durationS ?? null,
      tool_calls: s?.toolCalls ?? [],
      degraded_reason: s?.degradedReason ?? null,
      error: s?.error ?? null,
      // The audit's key metric: an AGENT that recorded no model call.
      reasoned: m.kind === 'AGENT' ? s?.agentDidCallModel ?? null : null,
    };
  });

  return NextResponse.json({
    agents,
    declared_agents: stages.filter((s) => s.kind === 'AGENT').length,
    agents_that_reasoned: agents.filter((a) => a.reasoned === true).length,
    source_run: run?.runId ?? null,
  });
}
