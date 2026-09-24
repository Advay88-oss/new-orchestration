import { NextResponse } from 'next/server';
import { listGtmRunIds, gtmRunSummary } from '@/lib/gtm';
import { isDeployed, getText } from '@/lib/gcs';
import fs from 'fs';
import path from 'path';

export const dynamic = 'force-dynamic';

const REPO_ROOT = path.resolve(process.cwd(), '..');
const RUNS_DIR = path.join(REPO_ROOT, 'pipeline', 'state', 'gtm_runs');

/**
 * One time-ordered event stream for a run, tailed with a cursor.
 *
 * The three journals are append-only and written as the cycle goes, so a
 * reader can poll for what is new rather than waiting for `summary.json` —
 * which lands only at the very end, and was the reason nothing about a run
 * was visible until it had finished.
 *
 *   stages.jsonl     an agent started or finished
 *   calls.jsonl      a model call, with tokens and duration
 *   decisions.jsonl  what A02 chose and turned down, A03's verdict,
 *                    A07's direction, A10's firewall result
 *
 * `?after=N` returns only events past that index, so the client polls cheaply
 * and never re-renders what it already has.
 */
async function readFile(runId: string, name: string): Promise<string | null> {
  if (isDeployed()) return getText(`gtm_runs/${runId}/${name}`);
  try {
    return fs.readFileSync(path.join(RUNS_DIR, runId, name), 'utf-8');
  } catch {
    return null;
  }
}

function lines(text: string | null): any[] {
  if (!text) return [];
  return text
    .split('\n')
    .filter((l) => l.trim())
    .map((l) => {
      try {
        return JSON.parse(l);
      } catch {
        return null;
      }
    })
    .filter(Boolean);
}

export async function GET(req: Request) {
  const url = new URL(req.url);
  const after = Number(url.searchParams.get('after') ?? -1);
  const runId = url.searchParams.get('runId') || (await listGtmRunIds(1))[0];

  if (!runId) {
    return NextResponse.json({ runId: null, events: [], cursor: -1, finished: false });
  }

  const [stagesRaw, callsRaw, decisionsRaw, summary] = await Promise.all([
    readFile(runId, 'stages.jsonl'),
    readFile(runId, 'calls.jsonl'),
    readFile(runId, 'decisions.jsonl'),
    gtmRunSummary(runId),
  ]);

  const events = [
    ...lines(stagesRaw).map((s) => ({
      type: 'stage' as const,
      at: s.at,
      agent: s.agent,
      name: s.name,
      status: s.status,
      detail: s.detail,
    })),
    ...lines(callsRaw)
      // Deterministic rows are real work but not model calls, and showing
      // them as calls overstates what the models did.
      .filter((c) => c.model && c.transport !== 'deterministic')
      .map((c) => ({
        type: 'call' as const,
        at: c.at,
        agent: c.agent,
        model: c.model,
        ok: c.ok,
        durationS: c.duration_s,
        inputTokens: c.input_tokens,
        outputTokens: c.output_tokens,
      })),
    ...lines(decisionsRaw).map((d) => ({
      type: 'decision' as const,
      at: d.at,
      agent: d.agent,
      name: d.name,
      kind: d.kind,
      payload: d.payload,
    })),
  ].sort((a, b) => String(a.at ?? '').localeCompare(String(b.at ?? '')));

  // `summary.json` exists only once the cycle has finished, so its presence
  // is what ends the client's polling.
  const finished = Boolean(summary);

  return NextResponse.json({
    runId,
    finished,
    status: summary?.status ?? 'running',
    cursor: events.length - 1,
    events: after >= 0 ? events.slice(after + 1) : events,
  });
}
